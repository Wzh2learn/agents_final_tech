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
    try:
        # 尝试导入 UnstructuredMarkdownLoader
        _md_loader = None
        _word_loader = None
        return _md_loader, _word_loader
    except Exception as e:
        print(f"导入文档加载器时出错: {e}")
        return None, None


_MarkdownLoader, _WordLoader = __dynamic_import()


def _get_file_extension(file_path: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(file_path)[1].lower()


@tool
def load_document(file_path: str) -> str:
    """
    加载文档内容（支持 Markdown 和 Word）

    Args:
        file_path: 文档路径（支持 .md, .markdown, .docx 格式）

    Returns:
        文档的文本内容

    Raises:
        ValueError: 如果文件格式不支持或文件不存在
    """
    if not os.path.exists(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    ext = _get_file_extension(file_path)

    # 加载 Markdown 文档
    if ext in ['.md', '.markdown']:
        if _MarkdownLoader is None:
            raise ValueError("Markdown 加载器未安装，请运行: pip install 'unstructured[md]'")

        try:
            loader = _MarkdownLoader(file_path)
            documents = loader.load()

            if not documents:
                raise ValueError(f"无法从 Markdown 文件加载内容: {file_path}")

            # 合并所有文档内容
            content = "\n\n".join([doc.page_content for doc in documents])
            return content

        except Exception as e:
            raise ValueError(f"加载 Markdown 文件失败: {str(e)}")

    # 加载 Word 文档
    elif ext == '.docx':
        if _WordLoader is None:
            raise ValueError("Word 加载器未安装，请运行: pip install docx2txt")

        try:
            loader = _WordLoader(file_path)
            documents = loader.load()

            if not documents:
                raise ValueError(f"无法从 Word 文件加载内容: {file_path}")

            # 合并所有文档内容
            content = "\n\n".join([doc.page_content for doc in documents])
            return content

        except Exception as e:
            raise ValueError(f"加载 Word 文件失败: {str(e)}")

    else:
        raise ValueError(
            f"不支持的文件格式: {ext}。"
            f"支持的格式: .md, .markdown, .docx"
        )


@tool
def load_documents_with_metadata(
    file_path: str,
    mode: Optional[str] = None
) -> str:
    """
    加载文档并保留元数据（支持 Markdown 和 Word）

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
        if _MarkdownLoader is None:
            raise ValueError("Markdown 加载器未安装，请运行: pip install 'unstructured[md]'")

        try:
            loader_kwargs = {}
            if mode == "elements":
                loader_kwargs["mode"] = "elements"

            loader = _MarkdownLoader(file_path, **loader_kwargs)
            documents = loader.load()

            if not documents:
                raise ValueError(f"无法从 Markdown 文件加载内容: {file_path}")

            if mode == "elements":
                # 返回带元数据的格式化内容
                result = []
                for i, doc in enumerate(documents, 1):
                    metadata = doc.metadata or {}
                    category = metadata.get('category', 'text')
                    result.append(f"[{i}] 类型: {category}")
                    result.append(f"内容: {doc.page_content}")
                    result.append("---")
                return "\n".join(result)
            else:
                # 默认模式，返回合并内容
                content = "\n\n".join([doc.page_content for doc in documents])
                return content

        except Exception as e:
            raise ValueError(f"加载 Markdown 文件失败: {str(e)}")

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
        lines = content.split('\n')
        info["行数"] = len(lines)
        info["字符数"] = len(content)
        info["非空行数"] = len([line for line in lines if line.strip()])
    except Exception as e:
        info["说明"] = f"无法读取文件内容: {str(e)}"

    # 格式化输出
    result = "📄 文档信息\n"
    result += "=" * 40 + "\n"
    for key, value in info.items():
        result += f"{key}: {value}\n"

    return result
