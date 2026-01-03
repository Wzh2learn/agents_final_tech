"""
QA问答工具：知识检索 → 理解用户问题 → 生成答案
对应 Dify 工作流：WF_QA_Main
"""
from pydantic import BaseModel, Field
import os
import glob
from typing import List, Optional
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from utils.runtime_ctx import Context, default_headers
def _search_knowledge(query: str) -> List[dict]:
    """
    通过 RAGService 检索知识库 (取代原有的本地 glob搜索)
    """
    try:
        from biz.rag_service import get_rag_service
        rag_service = get_rag_service()
        results = rag_service.smart_retrieve(query=query, top_k=3)
        return results
    except Exception as e:
        print(f"知识检索失败: {e}")
        return []


def _call_llm(ctx: Context, messages: list, config: dict) -> str:
    """调用大语言模型"""
    from utils.config_loader import get_config
    app_cfg = get_config()
    llm_cfg = app_cfg.get_llm_config()
    
    api_key = os.getenv(llm_cfg.get("api_key_env", "SILICONFLOW_API_KEY"))
    base_url = os.getenv(llm_cfg.get("base_url_env", "SILICONFLOW_BASE_URL"))

    llm = ChatOpenAI(
        model=llm_cfg.get("model", "deepseek-ai/DeepSeek-V3.2"),
        api_key=api_key,
        base_url=base_url,
        streaming=True,
        temperature=config.get("temperature", llm_cfg.get("temperature", 0.7)),
        max_completion_tokens=config.get("max_completion_tokens", llm_cfg.get("max_tokens", 4096)),
        extra_body={
            "thinking": {
                "type": config.get("thinking", llm_cfg.get("thinking", "disabled"))
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    full_response = ""
    for chunk in llm.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            # 处理 chunk.content 可能是字符串或列表的情况
            if isinstance(chunk.content, str):
                full_response += chunk.content
            elif isinstance(chunk.content, list):
                for item in chunk.content:
                    if isinstance(item, str):
                        full_response += item

    return full_response


class QAInput(BaseModel):
    query: str = Field(..., description="用户的问题")
    role: str = Field("default", description="回答角色（product_manager/tech_developer/sales_engineer/default）")
    use_knowledge: bool = Field(True, description="是否使用知识库检索")

@tool
def qa_agent(
    query: str,
    role: str = "default",
    use_knowledge: bool = True,
    runtime = None
) -> str:
    """
    QA问答工具：基于知识库回答用户关于建账规则的问题

    Args:
        query: 用户的问题
        role: 回答角色（product_manager/tech_developer/sales_engineer/default）
        use_knowledge: 是否使用知识库检索

    Returns:
        答案内容
    """
    # I/O Guard 校验
    validated = QAInput(query=query, role=role, use_knowledge=use_knowledge)
    query = validated.query
    role = validated.role
    use_knowledge = validated.use_knowledge

    ctx = runtime.context if runtime else None

    # 角色定义
    role_contexts = {
        "product_manager": {
            "name": "产品经理",
            "focus": "业务流程、用户体验、需求分析",
            "tone": "从产品角度解释，关注业务价值和用户痛点"
        },
        "tech_developer": {
            "name": "技术开发",
            "focus": "技术实现、系统架构、数据库交互",
            "tone": "从技术角度解释，关注技术链路和实现细节"
        },
        "sales_engineer": {
            "name": "销售运营",
            "focus": "客户价值、市场竞争、商业应用",
            "tone": "从商业角度解释，关注客户价值和竞争优势"
        },
        "default": {
            "name": "金融建账规则工程师",
            "focus": "规则解析、准确答案、技术细节",
            "tone": "标准技术解释，提供准确、详细的答案"
        }
    }

    role_info = role_contexts.get(role, role_contexts["default"])

    # 1. 如果需要，先检索知识库
    knowledge_context = ""
    if use_knowledge:
        relevant_docs = _search_knowledge(query)
        if relevant_docs:
            knowledge_context = "\n\n--- 相关知识库内容 ---\n"
            for i, doc in enumerate(relevant_docs, 1):
                source = doc.get("metadata", {}).get("source", "未知文档")
                content = doc.get("content", "")
                knowledge_context += f"\n【文档{i} - {source}】\n{content}\n"

    # 2. 构建系统提示词（迁移自Dify WF_QA_Main）
    system_prompt = f"""# 角色定义

你是一位金融建账自动化规则工程师，专注于{role_info['focus']}。
{role_info['tone']}

# 核心能力

- 精准理解金融建账规则
- 基于知识库内容提供准确答案
- {role_info['focus']}

# 知识库使用原则

1. 只回答与"托管估值辅助建账业务规则"相关的问题
2. 回答时必须优先依据"规则字典库"的片段，原文档片段只作为补充信息
3. 如两者冲突，以规则字典库为准
4. 严禁编造知识库中不存在的规则、比例、科目编码或接口名称

# 检索上下文说明

知识检索结果中包含两类信息：
1) 规则库片段：是经过整理的结构化规则说明（规则名称、规则逻辑、业务示例等）
2) 原产品文档片段：来自 Word 文档的原始自然语言描述，可能包含背景说明或旧版本内容

# 使用优先级

- 当回答涉及具体规则（触发条件、IF/THEN/ELSE逻辑、字段赋值、科目编码等）时：
  - 必须优先依据"规则库片段"的内容
  - 如规则库与原文档描述不一致，一律以规则库为准
- 原文档片段仅作为背景补充，不得单独凭一句原文就推翻规则库中的明确规则

# 回答要求

1. 严禁编造不存在于上下文中的比例、科目编码、条件等具体规则
2. 如果上下文中没有查询到相关规则，请明确回答"当前知识库中没有查到明确规则描述"，不要猜
3. 在回答时，优先从上下文中识别该规则的"规则名称"和"规则逻辑"段落，用自己的话总结
4. 请在文中引用规则名称，例如："根据《辅助建账通用宏定义与基础默认规则》，……"

# 输出格式

直接给出答案，结构清晰，不添加额外的前言或问候。
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"用户问题：{query}\n{knowledge_context}")
    ]

    try:
        result = _call_llm(ctx, messages, {})
        return result
    except Exception as e:
        return f"问答失败：{str(e)}"


@tool
def classify_query(
    query: str,
    runtime = None
) -> str:
    """
    查询分类工具：判断用户查询的类型

    Args:
        query: 用户查询内容

    Returns:
        查询类型（rule_query/general_qa/document_analysis）
    """
    ctx = runtime.context if runtime else None

    system_prompt = """# 任务
判断用户查询的类型，返回以下类型之一：

1. **rule_query** - 用户询问具体的建账规则
   例如：账户创建规则是什么？转账流程有哪些要求？

2. **general_qa** - 一般性问答或概念解释
   例如：什么是建账？为什么要这样设计？

3. **document_analysis** - 用户提到文档或文件
   例如：请分析这个文档、处理上传的文件

# 输出格式
仅返回查询类型，不要添加任何解释。
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"用户查询：{query}")
    ]

    try:
        result = _call_llm(ctx, messages, {"temperature": 0.3})
        return result.strip()
    except Exception as e:
        return "general_qa"  # 默认返回通用问答
