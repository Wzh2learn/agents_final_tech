"""
文档处理工具：解析文档 → 提取规则 → 生成结构化表格
对应 Dify 工作流：WF_DocumentProcessor_v1 + 文档处理.yml
"""
import os
from typing import Optional
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from coze_coding_utils.runtime_ctx.context import Context, default_headers


def _read_document(file_path: str) -> str:
    """
    读取文档内容
    支持: .txt, .md, .csv, .json
    """
    if not os.path.exists(file_path):
        return f"错误：文件不存在 - {file_path}"

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in ['.txt', '.md', '.csv', '.json', '.yaml', '.yml']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            # 简单处理：提示需要安装PyPDF2或pypdf
            try:
                import pypdf
                with open(file_path, 'rb') as f:
                    pdf_reader = pypdf.PdfReader(f)
                    content = []
                    for page in pdf_reader.pages:
                        content.append(page.extract_text())
                    return '\n'.join(content)
            except ImportError:
                return "错误：PDF 解析需要安装 pypdf 库。请运行: pip install pypdf"
        elif ext in ['.docx']:
            # 简单处理：提示需要安装python-docx
            try:
                doc_module = __import__('docx')
                Document = doc_module.Document
                doc = Document(file_path)
                content = []
                for para in doc.paragraphs:
                    content.append(para.text)
                return '\n'.join(content)
            except ImportError:
                return "错误：DOCX 解析需要安装 python-docx 库。请运行: pip install python-docx"
            except Exception as e:
                return f"读取DOCX文件失败：{str(e)}"
        else:
            return f"错误：不支持的文件格式 - {ext}"
    except Exception as e:
        return f"读取文件失败：{str(e)}"


def _call_llm_with_thinking(ctx: Context, messages: list, config: dict) -> str:
    """
    调用大语言模型（支持深度思考）
    """
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=config.get("model", "deepseek-v3-2-251201"),
        api_key=api_key,
        base_url=base_url,
        streaming=True,
        temperature=config.get("temperature", 0.1),
        max_completion_tokens=config.get("max_completion_tokens", 65501),
        extra_body={
            "thinking": {
                "type": config.get("thinking", "disabled")
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

    system_prompt = f"""# 角色定义
你是专注于金融建账业务规则处理的"建账规则转换专家"。
当前处理角色：{role_context}

# 核心任务
将提供的非结构化金融建账业务规则描述文本，转化为特定的标准化规则字典表格形式。

# 能力
- 精准理解金融建账领域知识
- 提炼规则ID、名称、触发条件、执行动作、配置参数等关键要素
- 生成规范的Markdown表格

# 输出格式要求（强制）
你的唯一输出必须是以下格式的Markdown表格，严禁在表格前后添加任何额外的解释、问候或说明文字。

| 字段 | 说明 | 提取内容 |
|------|------|----------|
| 规则ID | 唯一标识 | [待补充] |
| 规则名称 | 业务描述 | [从文本中精准提炼出最核心的建账业务名称] |
| 最后更新 | 生效日期 | [待补充] |
| 触发条件 | 规则触发的前提条件 | [从文本中提取] |
| 执行动作 | 规则执行的具体操作 | [从文本中提取] |
| 配置参数 | 规则相关的配置项 | [从文本中提取] |
| 业务场景 | 适用场景描述 | [从文本中提取] |
| 注意事项 | 需要特别关注的点 | [从文本中提取] |

# 约束
- 尽最大努力把文本中的每一条有效信息，合理归纳到表格中最合适的字段里
- 对于源文本中确实不存在的字段，可以留空或使用占位符 [待补充]
- 严格遵守表格格式，不添加任何额外文字
"""

    # 3. 调用 LLM 进行转换
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请将以下金融建账业务规则文本转换为标准化规则表格：\n\n{content}")
    ]

    config = {
        "model": "deepseek-v3-2-251201",  # 使用支持长上下文的模型
        "temperature": 0.1,
        "thinking": "disabled",
        "max_completion_tokens": 65501
    }

    try:
        result = _call_llm_with_thinking(ctx, messages, config)
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

    config = {
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.2,
        "thinking": "disabled"
    }

    try:
        result = _call_llm_with_thinking(ctx, messages, config)
        return result
    except Exception as e:
        return f"规则校验失败：{str(e)}"
