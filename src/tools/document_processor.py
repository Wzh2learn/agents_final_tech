"""
文档处理工具：解析文档 → 提取规则 → 生成结构化表格
对应 Dify 工作流：WF_DocumentProcessor_v1 + 文档处理.yml
"""
from pydantic import BaseModel, Field, validator
import os

from typing import Optional
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from utils.runtime_ctx import Context, default_headers


from tools.document_loader import load_document

def _read_document(file_path: str) -> str:
    """
    读取文档内容 (通过统一的 load_document 工具)
    """
    try:
        return load_document.invoke({"file_path": file_path})
    except Exception as e:
        return f"读取文件失败：{str(e)}"


def _call_llm_with_thinking(ctx: Context, messages: list, config: dict) -> str:
    """
    调用大语言模型（支持深度思考）
    """
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
        temperature=config.get("temperature", llm_cfg.get("temperature", 0.1)),
        max_completion_tokens=config.get("max_completion_tokens", llm_cfg.get("max_tokens", 65501)),
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


class DocumentProcessorInput(BaseModel):
    file_path: str = Field(..., description="文档文件路径（支持 .txt, .md, .pdf, .docx, .csv, .json）")
    role: str = Field("default", description="处理角色（product_manager/tech_developer/sales_engineer/default）")

    @validator('file_path')
    def validate_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"文件不存在: {v}")
        allowed_exts = ['.txt', '.md', '.pdf', '.docx', '.csv', '.json', '.yaml', '.yml']
        ext = os.path.splitext(v)[1].lower()
        if ext not in allowed_exts:
            raise ValueError(f"不支持的文件格式: {ext}")
        return v

@tool
def document_processor(
    file_path: str,
    role: str = "default",
    runtime = None
) -> str:
    """
    文档处理工具：解析文档并提取建账规则为结构化表格

    Args:
        file_path: 文档文件路径（支持 .txt, .md, .pdf, .docx, .csv, .json）
        role: 处理角色（product_manager/tech_developer/sales_engineer/default）

    Returns:
        结构化的规则表格（Markdown格式）
    """
    # I/O Guard 校验
    validated = DocumentProcessorInput(file_path=file_path, role=role)
    file_path = validated.file_path
    role = validated.role

    ctx = runtime.context if runtime else None

    # 1. 读取文档内容
    content = _read_document(file_path)
    if content.startswith("错误"):
        return content

    # 2. 根据角色定制提示词
    role_prompts = {
        "product_manager": "产品经理视角 - 关注业务流程和用户体验",
        "tech_developer": "技术开发视角 - 关注技术实现和系统架构",
        "sales_engineer": "销售运营视角 - 关注客户价值和市场竞争",
        "default": "金融建账自动化规则工程师 - 负责根据结构化规则字典回答用户问题"
    }

    role_context = role_prompts.get(role, role_prompts["default"])

    system_prompt = f"""# 角色定义 (Role)

你是一个专注于金融建账业务规则处理的"建账规则转换专家"。
当前处理角色：{role_context}

# 核心任务 (Task)

你的核心任务是精准地将一段非结构化的金融建账业务规则描述文本，转化为特定的标准化规则字典表格形式。

你犹如一位经验丰富的金融业务分析师，对金融建账领域知识了如指掌，能够迅速且准确地从文档中提炼出规则的ID、名称、触发条件、执行动作、配置参数等关键要素，并合理归类到相应表格位置。

# 能力

- 精准理解金融建账领域知识
- 从非结构化文本中提炼关键规则要素
- 生成规范的Markdown表格

# 输入处理

我会提供一段关于金融建账业务规则的文本描述。你需要完成以下任务：

1. 仔细、全面地阅读并透彻理解文本中的所有信息，不放过任何细节。
2. 严格依据我给定的规则字典输出格式，生成一个规范的Markdown表格。
3. 尽最大努力把文本中的每一条有效信息，合理归纳到表格中最合适的字段里。对于源文本中确实不存在的字段（如规则ID、更新日期等），可以留空或使用占位符 [待补充]。

# 背景 (Context)

我正在搭建一个结构化的金融建账规则知识库。原始的业务文档采用自然语言撰写，格式缺乏统一规范，这给系统化的管理和查询带来了极大困难。我需要你助力完成从"非结构化文本"到"结构化数据"的关键转变，为后续的规则引擎、RAG系统或团队知识库奠定坚实基础。

# 输出格式 (Output Format) - 【强制】

你的唯一输出必须是以下格式的Markdown表格。严禁在表格前后添加任何额外的解释、问候或说明文字。

| 字段 | 说明 | 提取内容 |
|------|------|----------|
| 规则ID | 唯一标识 | [待补充] |
| 规则名称 | 业务描述 | [从文本中精准提炼出最核心的建账业务名称，需简洁明了且能准确反映业务本质，例如："建账账号信息更新规则"] |
| 最后更新 | 生效日期 | [待补充] |
| 来源位置 | 文档位置 | [待补充] |
| 触发条件 | 规则触发的前提条件 | [从文本中提取] |
| 执行动作 | 规则执行的具体操作 | [从文本中提取] |
| 配置参数 | 规则相关的配置项 | [从文本中提取] |
| 业务场景 | 适用场景描述 | [从文本中提取] |
| 注意事项 | 需要特别关注的点 | [从文本中提取] |

# 约束

- 尽最大努力把文本中的每一条有效信息，合理归纳到表格中最合适的字段里
- 对于源文本中确实不存在的字段，可以留空或使用占位符 [待补充]
- 严格遵守表格格式，不添加任何额外文字
- 保持规则的准确性和完整性
"""

    # 3. 调用 LLM 进行转换
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请将以下金融建账业务规则文本转换为标准化规则表格：\n\n{content}")
    ]

    try:
        result = _call_llm_with_thinking(ctx, messages, {})
        return result
    except Exception as e:
        return f"文档处理失败：{str(e)}"


@tool
def validate_rules(
    rules_table: str,
    runtime = None
) -> str:
    """
    规则校验工具：审核提取的规则是否合理

    Args:
        rules_table: 规则表格（Markdown格式）

    Returns:
        校验结果和建议
    """
    ctx = runtime.context if runtime else None

    system_prompt = """# 角色定义
你是金融建账规则审核专家，负责审核提取的规则表格。

# 审核要点
1. 完整性：关键字段是否填写完整
2. 准确性：规则描述是否准确反映原文意图
3. 逻辑性：触发条件和执行动作是否逻辑一致
4. 可操作性：规则是否具备可执行性

# 输出格式
提供以下结构化的审核结果：

## 审核结果
- 总体评分：[0-10分]
- 通过审核：[是/否]

## 详细建议
[列出需要改进的地方]

## 优化建议（可选）
[提供优化建议]
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请审核以下规则表格：\n\n{rules_table}")
    ]

    try:
        result = _call_llm_with_thinking(ctx, messages, {"temperature": 0.2})
        return result
    except Exception as e:
        return f"规则校验失败：{str(e)}"
