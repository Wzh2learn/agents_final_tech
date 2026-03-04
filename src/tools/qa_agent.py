"""
QA问答工具：知识检索 → 理解用户问题 → 生成答案
对应 Dify 工作流：WF_QA_Main

固定流程：多路检索（规则库 + 标准答案库）→ 生成 → 质检 → 反思
"""
import json
import logging
import os
import glob
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from utils.runtime_ctx import Context, default_headers
from utils.openai_network import get_chat_openai_network_kwargs, get_thinking_kwargs

logger = logging.getLogger(__name__)


def _multi_path_retrieval(query: str, top_k: int = 4) -> Tuple[List[dict], List[dict]]:
    """
    多路检索：规则库 + 标准答案库（对应 Dify 的两个知识检索节点）

    Args:
        query: 用户查询
        top_k: 每个检索路径返回的文档数

    Returns:
        (规则库检索结果, 标准答案库检索结果)
    """
    try:
        from biz.rag_service import get_rag_service_sync
        rag_service = get_rag_service_sync()

        # 路径1：规则库检索（主要知识来源）
        # 对应 Dify 的 "知识检索 - 多路召回" 节点
        rule_results = rag_service.smart_retrieve(query=query, top_k=top_k)

        # 路径2：标准答案库检索（质检用）
        # 对应 Dify 的 "答案搜寻" 节点
        # 注意：标准答案库目前可能为空，但预留接口
        # TODO: 当标准答案库有数据后，可以通过 collection_name 参数指定
        # standard_answer_results = rag_service.smart_retrieve(
        #     query=query,
        #     top_k=1,
        #     collection_name="standard_answers"
        # )
        standard_answer_results = []  # 目前标准答案库为空

        logger.info(f"多路检索完成：规则库 {len(rule_results)} 条，标准答案库 {len(standard_answer_results)} 条")
        return rule_results, standard_answer_results

    except Exception as e:
        logger.warning(f"多路检索失败: {e}")
        return [], []


def _call_llm(ctx: Context, messages: list, config: dict) -> str:
    """调用大语言模型"""
    from utils.config_loader import get_config
    app_cfg = get_config()
    llm_cfg = app_cfg.get_llm_config()

    api_key = os.getenv(llm_cfg.get("api_key_env", "SILICONFLOW_API_KEY"))
    base_url = os.getenv(llm_cfg.get("base_url_env", "SILICONFLOW_BASE_URL"))

    llm_kwargs = {
        "model": llm_cfg.get("model", "deepseek-ai/DeepSeek-V3.2"),
        "api_key": api_key,
        "base_url": base_url,
        "streaming": True,
        "temperature": config.get("temperature", llm_cfg.get("temperature", 0.7)),
        "max_completion_tokens": config.get("max_completion_tokens", llm_cfg.get("max_tokens", 4096)),
        "default_headers": default_headers(ctx) if ctx else {},
    }
    thinking_type = config.get("thinking", llm_cfg.get("thinking", "disabled"))
    llm_kwargs.update(get_thinking_kwargs(thinking_type))
    llm_kwargs.update(get_chat_openai_network_kwargs())
    llm = ChatOpenAI(**llm_kwargs)

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


def _extract_json_block(text: str) -> Optional[dict]:
    """从文本中提取 JSON 结构"""
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            return json.loads(text[start_idx:end_idx])
    except Exception:
        return None
    return None


def _generate_answer(ctx: Context, query: str, rule_context: str) -> str:
    """
    生成回答（对应 Dify 的 "生成回答" LLM 节点）
    【Dify 原始提示词 - 原封不动保留】
    """
    # 完整保留 Dify WF_QA_Main.yml 第323-330行的提示词
    system_prompt = """你是一位金融建账自动化规则工程师，只回答与"托管估值辅助建账业务规则"相关的问题。
回答时必须优先依据"规则字典库"的片段，原文档片段只作为补充信息，如两者冲突，以规则字典库为准。
严禁编造知识库中不存在的规则、比例、科目编码或接口名称。


【检索上下文说明】
- 知识检索结果中包含两类信息：
  1）规则库片段：是经过整理的结构化规则说明（规则名称、规则逻辑、业务示例等）；
  2）原产品文档片段：来自 Word 文档的原始自然语言描述，可能包含背景说明或旧版本内容。

【使用优先级】
- 当回答涉及具体规则（触发条件、IF/THEN/ELSE逻辑、字段赋值、科目编码等）时：
  - 必须优先依据"规则库片段"的内容；
  - 如规则库与原文档描述不一致，一律以规则库为准。
- 原文档片段仅作为背景补充，不得单独凭一句原文就推翻规则库中的明确规则。

【回答要求】
1. 严禁编造不存在于上下文中的比例、科目编码、条件等具体规则。
2. 如果上下文中没有查询到相关规则，请明确回答"当前知识库中没有查到明确规则描述"，不要猜。
3.在回答时，优先从上下文中识别该规则的"规则名称"和"规则逻辑"段落，用自己的话总结，但请在文中引用规则名称，例如："根据《辅助建账通用宏定义与基础默认规则》，……"。


【检索结果】
{context}

【用户问题】
{query}

请据此给出最终回答：
"""
    messages = [
        SystemMessage(content=system_prompt.format(context=rule_context, query=query))
    ]
    return _call_llm(ctx, messages, {"temperature": 0.7, "max_completion_tokens": 65501})


def _quality_check(ctx: Context, query: str, answer: str, standard_answer_context: str) -> Optional[dict]:
    """
    智检智能体：评估回答质量（对应 Dify 的 "智检智能体" LLM 节点）
    【Dify 原始提示词 - 原封不动保留】
    """
    # 完整保留 Dify WF_QA_Main.yml 第367-402行的提示词
    system_prompt = """你是回答质检官。

【用户问题】
{query}

【当前回答】
{answer}

【标准答案检索结果】
{context}

如有标准答案，请对比当前回答与标准答案的一致性；如无标准答案，只做自检。

严格按照系统定义的 JSON 结构输出，不要输出任何多余内容。

字段含义：
- has_standard_answer: 是否命中标准答案
- similarity_to_gold: 与标准答案的相似度（0~1）
- score: 整体得分（0~100）
- critical_error: 是否存在严重事实错误或规则错误
- suggestion: 对回答优化的简要建议
"""
    messages = [
        SystemMessage(content=system_prompt.format(
            query=query,
            answer=answer,
            context=standard_answer_context or "无标准答案"
        ))
    ]
    result = _call_llm(ctx, messages, {"temperature": 0.1, "max_completion_tokens": 65501})
    return _extract_json_block(result)


def _reflect_and_improve(ctx: Context, query: str, answer: str, suggestion: str, rule_context: str) -> str:
    """
    反思智能体：根据质检建议优化回答（对应 Dify 的 "反思智能体" LLM 节点）
    【Dify 原始提示词 - 原封不动保留】
    """
    # 完整保留 Dify WF_QA_Main.yml 第488-530行的提示词
    system_prompt = """你是一位金融建账自动化规则工程师，只回答与"托管估值辅助建账业务规则"相关的问题。
回答时必须优先依据"规则字典库"的片段，原文档片段只作为补充信息，如两者冲突，以规则字典库为准。
严禁编造知识库中不存在的规则、比例、科目编码或接口名称。

你是回答优化助手。请根据质检建议，对回答进行结构化改写。

【用户问题】
{query}

【原回答】
{answer}

【质检建议】
{suggestion}

如果当前问题能够对应到某条标准规则（比如上下文中有显式的规则名称或"规则条件/执行动作/业务示例"结构），请尽量按下面结构输出回答：

1. 简要结论（1~2 句话）
2. 规则条件（IF 部分）
3. 执行动作（THEN / ELSE 部分）
4. 业务示例（结合典型场景说明）
5. 异常处理（有则说明，没有可以省略）

如果无法匹配到规则场景，就保留普通自然语言回答，但仍要保证准确、不编造。
"""
    messages = [
        SystemMessage(content=system_prompt.format(
            query=query,
            answer=answer,
            suggestion=suggestion or "无"
        ))
    ]
    return _call_llm(ctx, messages, {"temperature": 0.2, "max_completion_tokens": 65501})


def _structured_rule_interpretation(ctx: Context, query: str, rule_context: str) -> str:
    """
    结构化规则解读（对应 Dify 的 "结构化规则解读回答" LLM 节点）
    【Dify 原始提示词 - 原封不动保留】
    """
    # 完整保留 Dify WF_QA_Main.yml 第831-858行的提示词
    system_prompt = """# 角色 你是一位顶尖的**金融建账自动化规则工程师**，也是团队内部"辅助建账"功能的**首席架构师**。你深知"辅助建账"的核心价值在于**替代估值会计在恒生（Hundsun）等系统中的繁琐手动操作**，是"一键估值"前最关键的数据准备环节。你对通过**直接数据库交互**与外部系统同步数据的技术方案了如指掌，并且你的主要服务对象是**估值会计**与**运维人员**。 你的使命，是将产品经理编写的、面向"人"的业务需求文档，精准地提炼、转化为结构化、无歧义、机器可读的"规则字典"。你不仅能理解文档的字面意思，更能**主动关联上下文，理解概念的多种表述，并追溯信息的完整链路**，为不同角色的同事提供清晰、可执行的解读。
明确说明：所有信息从 {{context}}来；

## 技能
### 技能 1: 构建并增强规则字典（具备联想与追溯能力） 1. 当用户提出关于建账规则的问题时，**首先**，在本地知识库中进行**宽泛而精准**的检索。你要理解，不同的人可能会用不同的词语描述同一个概念（例如，"前端"、"Web界面"、"客户端"都可能指用户操作界面）。
2. **其次**，你必须将规则信息严格按照以下`规则字典`的格式进行呈现。这是所有回答的**第一步和基础**。 :规则ID、规则名称、最后更新、来源位置、用户问题、规则逻辑、数据来源、业务示例。
### 技能 2:
向产品经理/业务人员阐述规则 (讲清完整"业务流")
1. 在`规则字典`下方，以"**面向业务/产品人员的解析**"为标题，提供详细说明。
2. 回答必须完整串联起一个业务故事，清晰展示规则在**包含人工干预的多阶段流程**中的作用。
3. 说明内容应包含： * **【规则背景与目的】:** 这条规则要解决估值会计/运维的哪个具体痛点？（例如：避免手动维护文件路径的繁琐和易错性）。 * **【完整业务流程拆解】:** 分步描述整个业务流的发生过程。 1. **触发点：** 什么业务事件的发生会启动这个流程？（例如：系统监测到某产品发生了第一笔资金划转）。 2. **系统自动响应：** 流程启动后，系统做的第一件事是什么？（例如：给运维人员创建一个待办任务）。 3. **人工处理环节：** 哪个角色（估值会计/运维）需要做什么操作？（例如：运维人员在待办页面确认或修改默认的文件路径）。 4. **最终系统闭环：** 人工操作完成后，系统如何完成最后的自动化步骤？（例如：将路径信息同步到恒生估值数据库）。
### 技能 3: 协助技术人员开发 (讲清"技术实现链路") 1. 在业务解析下方，以"**面向技术/开发人员的解析**"为标题，提供技术实现层面的解读。
2. 回答必须清晰描绘出实现该规则所需的技术组件和它们之间的调用关系，**特别要强调与恒生系统的数据库交互**。
3. 说明内容应包含： * **【技术触发与入口】:** 规则链路的入口是什么？是定时任务（Cron Job）、还是某个前端页面的API调用？ * **【核心实现链路详解】:** 详细拆解实现这个多阶段规则的技术链路。 1. **监听/扫描组件：** 例如，一个 `Scheduled Task` 在特定时间（如每日6点）扫描 `clearing_instruction_table`。
2. **人机交互接口：** 当触发条件满足时，调用 `todo_service` 创建待办事项。运维人员处理待办时，前端会调用哪个 `API`（如 `/api/v1/paths/confirm`）。
3. **后端处理核心：** 上述API的后端实现逻辑是什么？**重点说明与恒生系统【直接的数据库交互】逻辑**，例如：`通过JDBC连接恒生数据库，向'hs_file_path_table'中INSERT或UPDATE数据`。要明确指出操作的表名和关键字段。 * **【关键配置与硬编码】:** 指出规则中需要注意的配置项，特别是像`接口ID列表`这样的硬编码常量集合，以及文件路径的`动态模板`。
### 技能 4: (可选) 向新手讲解规则
1. 如果需要，在最后增加一个"**给新手的极简解释**"部分。 2. 用一两句话概括整个流程。 * *示例："简单说，就是系统发现有新账户在做交易了，就喊运维来看一眼文件路径对不对，运维一点头，系统就自动把这个路径写到恒生系统里去，省得会计自己去登录恒生客户端手动输一遍。"*

## 限制与原则: * **概念归一化原则：** 在你的内部理解和外部解释中，必须能识别并统一概念的多种说法。例如，当你看到"前端"、"Web端"、"界面"时，要能理解它们都指向用户交互的图形界面，并在解释时选择最合适的、一致的术语。
* **主动追溯原则：** 当`规则逻辑`中出现一个抽象的业务术语（如"首笔划款指令"）时，你**有责任在整个知识库中去寻找它的具体定义和数据来源**，并在`数据来源`字段和后续的解析中明确揭示这种关联。如果找不到，需明确指出"文档中未找到'XXX'的具体定义，需要人工补充"。
 * **结构至上：** 严格遵循"先表格，后解析"的输出结构。
* **忠于原文，主动推理：** 所有回答的依据是本地知识库，但你必须主动进行关联和推理，让信息形成闭环。 * **视角分离：** "业务流"和"技术链路"的解析必须侧重点分明。
* **明确溯源：** `规则字典`中的`来源位置`字段必须准确填写。
* **专注领域：** 只回答与"辅助建账"及相关业务规则的问题。


输出markdown形式！！！"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"【检索结果】\n{rule_context}\n\n【用户问题】\n{query}")
    ]
    return _call_llm(ctx, messages, {"temperature": 0, "max_completion_tokens": 65501})


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

    【固定流程 - 对应 Dify 设计】：
    1. 多路检索（规则库 + 标准答案库）
    2. 生成回答
    3. 质检（智检智能体）
    4. 反思优化（反思智能体）

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

    # 检测是否为高级查看模式（结构化规则解读）
    # 对应 Dify 的条件分支：包含"规则字典"、"面向业务"、"给新手"
    advanced_keywords = ["规则字典", "面向业务", "给新手", "结构化解读", "详细解析"]
    is_advanced_mode = any(keyword in query for keyword in advanced_keywords)

    try:
        # ========== 步骤1：多路检索 ==========
        # 对应 Dify 的两个知识检索节点：
        # - 知识检索（规则库）
        # - 答案搜寻（标准答案库）
        rule_results, standard_answer_results = _multi_path_retrieval(query, top_k=4)

        # 构建规则库上下文
        rule_context = ""
        if rule_results:
            for i, doc in enumerate(rule_results, 1):
                source = doc.get("metadata", {}).get("source", "未知文档")
                content = doc.get("content", "")
                rule_context += f"\n【文档{i} - {source}】\n{content}\n"

        # 构建标准答案库上下文
        standard_answer_context = ""
        if standard_answer_results:
            for i, doc in enumerate(standard_answer_results, 1):
                content = doc.get("content", "")
                standard_answer_context += f"\n【标准答案{i}】\n{content}\n"

        # ========== 步骤2：生成回答 ==========
        if is_advanced_mode:
            # 高级模式：结构化规则解读
            # 对应 Dify 的 "结构化规则解读回答" LLM 节点
            answer = _structured_rule_interpretation(ctx, query, rule_context)
        else:
            # 标准模式：生成回答
            # 对应 Dify 的 "生成回答" LLM 节点
            answer = _generate_answer(ctx, query, rule_context)

        # ========== 步骤3：质检 ==========
        # 对应 Dify 的 "智检智能体" LLM 节点
        quality_result = _quality_check(ctx, query, answer, standard_answer_context)

        # ========== 步骤4：反思优化 ==========
        # 【去掉评分阈值判断，直接执行反思】
        # 对应 Dify 的 "反思智能体" LLM 节点
        if quality_result:
            suggestion = quality_result.get("suggestion", "")
            improved_answer = _reflect_and_improve(ctx, query, answer, suggestion, rule_context)
            if improved_answer:
                return improved_answer

        # 如果反思失败，返回原始答案
        return answer

    except Exception as e:
        logger.error(f"QA问答失败: {e}")
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
