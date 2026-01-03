"""
文档加载工具
支持 Markdown 和 Word (DOCX) 文档加载
"""
import os
from typing import List, Optional
from langchain.tools import tool
from langchain_core.documents import Document


def __dynamic_import():
    """动态导入文档加载器，避免静态类型检查错误"""
    _has_unstructured = False
    _has_docx = False

    try:
        # 尝试导入 unstructured
        from unstructured.partition.md import partition_md
        _has_unstructured = True
    except ImportError:
        pass

    try:
        # 尝试导入 python-docx
        from docx import Document
        _has_docx = True
    except ImportError:
        pass

    return _has_unstructured, _has_docx


_has_unstructured, _has_docx = __dynamic_import()


def _get_file_extension(file_path: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(file_path)[1].lower()


from pydantic import BaseModel, Field, validator
import os

class DocumentLoadInput(BaseModel):
    file_path: str = Field(..., description="文档路径（支持 .txt, .md, .pdf, .docx, .csv, .json, .yaml, .yml 格式；.doc 需额外依赖或转换）")

    @validator('file_path')
    def validate_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"文件不存在: {v}")
        allowed_exts = ['.txt', '.md', '.markdown', '.pdf', '.docx', '.doc', '.csv', '.json', '.yaml', '.yml']
        ext = os.path.splitext(v)[1].lower()
        if ext not in allowed_exts:
            raise ValueError(f"不支持的文件格式: {ext}。支持的格式: {allowed_exts}")
        return v

@tool
def load_document(file_path: str) -> str:
    """
    加载文档内容（支持 Markdown 和 Word）

    Args:
        file_path: 文档路径（支持 .md, .markdown, .docx 格式）

    Returns:
        文档的文本内容
    """
    # I/O Guard 校验
    validated = DocumentLoadInput(file_path=file_path)
    file_path = validated.file_path

    ext = _get_file_extension(file_path)

    # 通用纯文本类（.txt/.csv/.json/.yaml/.yml）
    if ext in ['.txt', '.csv', '.json', '.yaml', '.yml']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Windows 环境常见的编码兜底
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                return f.read()

    # 加载 PDF 文档
    if ext == '.pdf':
        # 优先使用 unstructured（如果已安装）
        try:
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(filename=file_path)
            content = "\n\n".join([str(el) for el in elements])
            return content
        except ImportError:
            pass
        # 兜底：pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n\n".join(pages).strip()
        except ImportError:
            raise ValueError("PDF 解析依赖缺失：请安装 unstructured 或 pypdf（pip install unstructured pypdf）")

    # 加载 Markdown 文档
    if ext in ['.md', '.markdown']:
        try:
            from unstructured.partition.md import partition_md
            elements = partition_md(filename=file_path)
            content = "\n\n".join([str(el) for el in elements])
            return content
        except ImportError:
            # 降级方案：直接读取文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                raise ValueError(f"加载 Markdown 文件失败: {str(e)}")

    # 加载 Word 文档
    elif ext == '.docx':
        if not _has_docx:
            raise ValueError("python-docx 库未安装，请运行: pip install python-docx")

        try:
            from docx import Document
            doc = Document(file_path)
            content = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return content
        except Exception as e:
            raise ValueError(f"加载 Word 文件失败: {str(e)}")

    # 加载旧 Word 文档（.doc） - 尽力支持（需要 textract）
    elif ext == '.doc':
        try:
            import textract
            text_bytes = textract.process(file_path)
            return text_bytes.decode('utf-8', errors='ignore')
        except ImportError:
            raise ValueError(".doc 解析需要额外依赖 textract，或请将文件转换为 .docx")
        except Exception as e:
            raise ValueError(f"加载 .doc 文件失败: {str(e)}")

    else:
        raise ValueError(
            f"不支持的文件格式: {ext}。"
            f"支持的格式: .txt, .md, .markdown, .pdf, .docx, .doc, .csv, .json, .yaml, .yml"
        )


@tool
def load_documents_with_metadata(
    file_path: str,
    mode: Optional[str] = None
) -> str:
    """
    加载文档并保留元数据（支持 Markdown）

    Args:
        file_path: 文档路径
        mode: 加载模式
            - None: 默认模式，合并所有内容
            - "elements": 保留文档元素（标题、段落等）的元数据（仅支持 Markdown）

    Returns:
        格式化的文档内容和元数据

    Raises:
        ValueError: 如果文件格式不支持或参数无效
    """
    if not os.path.exists(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    ext = _get_file_extension(file_path)

    # 加载 Markdown 文档
    if ext in ['.md', '.markdown']:
        try:
            from unstructured.partition.md import partition_md
            elements = partition_md(filename=file_path)

            if mode == "elements":
                # 返回带元数据的格式化内容
                result = []
                for i, el in enumerate(elements, 1):
                    category = getattr(el, 'category', 'text')
                    result.append(f"[{i}] 类型: {category}")
                    result.append(f"内容: {str(el)}")
                    result.append("---")
                return "\n".join(result)
            else:
                # 默认模式，返回合并内容
                content = "\n\n".join([str(el) for el in elements])
                return content
        except Exception as e:
            # 降级方案：使用 load_document
            return load_document(file_path)

    # Word 文档暂不支持 mode 参数
    elif ext == '.docx':
        return load_document(file_path)

    else:
        raise ValueError(
            f"不支持的文件格式: {ext}。"
            f"支持的格式: .md, .markdown, .docx"
        )


@tool
def get_document_info(file_path: str) -> str:
    """
    获取文档基本信息

    Args:
        file_path: 文档路径

    Returns:
        文档信息（文件名、大小、格式、行数、字符数）
    """
    if not os.path.exists(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    ext = _get_file_extension(file_path)
    file_size = os.path.getsize(file_path)

    info = {
        "文件名": os.path.basename(file_path),
        "文件格式": ext,
        "文件大小": f"{file_size} bytes ({file_size / 1024:.2f} KB)",
    }

    # 如果是支持的格式，加载内容并统计
    try:
        content = load_document(file_path)
        lines = content.count('\n') + 1 if content else 0
        chars = len(content)
        words = len(content.split())

        info["行数"] = lines
        info["字符数"] = chars
        info["单词数"] = words
    except:
        pass

    # 格式化输出
    result = "📄 文档信息\n"
    result += "=" * 40 + "\n"
    for key, value in info.items():
        result += f"{key}: {value}\n"

    return result
