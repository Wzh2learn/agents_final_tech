"""
文本分割工具
支持递归分割和 Markdown 结构分割
"""
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from langchain_core.documents import Document


def __dynamic_import():
    """动态导入文本分割器，避免静态类型检查错误"""
    # 递归字符分割器
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        _recursive_splitter = RecursiveCharacterTextSplitter
    except ImportError:
        _recursive_splitter = None

    # Markdown 标题分割器
    try:
        from langchain_text_splitters import MarkdownHeaderTextSplitter
        _markdown_splitter = MarkdownHeaderTextSplitter
    except ImportError:
        _markdown_splitter = None

    return _recursive_splitter, _markdown_splitter


_RecursiveSplitter, _MarkdownSplitter = __dynamic_import()


@tool
def split_text_recursive(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
) -> str:
    """
    使用递归字符分割器分割文本（推荐用于通用文本）

    Args:
        text: 要分割的文本
        chunk_size: 每个块的最大字符数（默认 1000）
        chunk_overlap: 块之间的重叠字符数（默认 200）
        separators: 分隔符列表，默认为 ["\n\n", "\n", " ", ""]

    Returns:
        分割后的文本块列表（带索引）

    Raises:
        ValueError: 如果分割器未安装或文本为空
    """
    if _RecursiveSplitter is None:
        raise ValueError(
            "文本分割器未安装，请运行: "
            "pip install langchain-text-splitters"
        )

    if not text or not text.strip():
        raise ValueError("文本不能为空")

    if separators is None:
        separators = ["\n\n", "\n", " ", ""]

    try:
        splitter = _RecursiveSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )

        # 将文本转换为 Document 对象
        document = Document(page_content=text)

        # 分割文档
        chunks = splitter.split_documents([document])

        # 格式化输出
        result = f"📝 文本分割结果\n"
        result += f"总块数: {len(chunks)}\n"
        result += f"块大小: {chunk_size} 字符\n"
        result += f"重叠: {chunk_overlap} 字符\n"
        result += "=" * 50 + "\n\n"

        for i, chunk in enumerate(chunks, 1):
            result += f"--- 块 {i} ({len(chunk.page_content)} 字符) ---\n"
            result += f"{chunk.page_content}\n\n"

        return result

    except Exception as e:
        raise ValueError(f"文本分割失败: {str(e)}")


@tool
def split_text_by_markdown_structure(
    text: str,
    headers_to_split_on: Optional[List[tuple]] = None,
    return_each_line: Optional[bool] = False
) -> str:
    """
    基于 Markdown 标题结构分割文本

    Args:
        text: Markdown 文本
        headers_to_split_on: 要分割的标题列表
            格式: [("标题名", "标题级别")]
            例如: [("#", "Header 1"), ("##", "Header 2")]
            如果为 None，默认使用常见标题
        return_each_line: 是否返回每行内容（仅用于调试）

    Returns:
        分割后的文本块（带标题和元数据）

    Raises:
        ValueError: 如果分割器未安装或文本为空
    """
    if _MarkdownSplitter is None:
        raise ValueError(
            "Markdown 分割器未安装，请运行: "
            "pip install langchain-text-splitters"
        )

    if not text or not text.strip():
        raise ValueError("文本不能为空")

    if headers_to_split_on is None:
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

    try:
        splitter = _MarkdownSplitter(
            headers_to_split_on=headers_to_split_on
        )

        # 分割文档（使用split_text方法）
        chunks = splitter.split_text(text)

        # 格式化输出
        result = f"📝 Markdown 结构分割结果\n"
        result += f"总块数: {len(chunks)}\n"
        result += f"分割规则: {[h[0] for h in headers_to_split_on]}\n"
        result += "=" * 50 + "\n\n"

        for i, chunk in enumerate(chunks, 1):
            result += f"--- 块 {i} ({len(chunk)} 字符) ---\n"
            result += f"{chunk}\n\n"

        return result

    except Exception as e:
        raise ValueError(f"Markdown 分割失败: {str(e)}")


@tool
def split_document_optimized(
    text: str,
    file_type: str = "text"
) -> str:
    """
    根据文件类型自动选择最优分割策略

    Args:
        text: 要分割的文本
        file_type: 文件类型
            - "text": 通用文本（使用递归分割）
            - "markdown": Markdown 文档（使用标题结构分割）
            - "code": 代码文件（使用递归分割，小块）

    Returns:
        分割后的文本块

    Raises:
        ValueError: 如果文件类型不支持
    """
    # 根据文件类型选择分割策略
    if file_type == "markdown":
        return split_text_by_markdown_structure(text)
    elif file_type == "code":
        # 代码使用较小的块
        return split_text_recursive(
            text,
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "  ", ". ", " "]
        )
    else:
        # 默认使用通用文本分割
        return split_text_recursive(text)


@tool
def split_text_with_summary(
    text: str,
    max_chunks: Optional[int] = None
) -> str:
    """
    分割文本并生成摘要统计

    Args:
        text: 要分割的文本
        max_chunks: 最大分割块数（None 表示不限制）

    Returns:
        分割结果 + 统计摘要

    Raises:
        ValueError: 如果文本为空
    """
    if not text or not text.strip():
        raise ValueError("文本不能为空")

    # 使用递归分割
    result = split_text_recursive(text)

    # 添加统计摘要
    total_chars = len(text)
    total_words = len(text.split())
    total_lines = len(text.split('\n'))

    summary = f"\n📊 统计摘要\n"
    summary += "=" * 30 + "\n"
    summary += f"总字符数: {total_chars}\n"
    summary += f"总词数: {total_words}\n"
    summary += f"总行数: {total_lines}\n"
    summary += f"平均块大小: {total_chars // max(len(result.split('---')) - 1, 1)} 字符\n"

    return result + summary


def hierarchical_split(
    text: str,
    parent_chunk_size: int = 2000,
    child_chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[Dict[str, any]]:
    """
    父子分段模式：两级分割，父块用于概览，子块用于详细检索
    
    Args:
        text: 要分割的文本
        parent_chunk_size: 父块大小（默认2000字符）
        child_chunk_size: 子块大小（默认500字符）
        chunk_overlap: 块之间重叠（默认100字符）
    
    Returns:
        包含父子关系的Document列表
        每个父Document包含metadata: {"parent_id": str, "is_parent": True}
        每个子Document包含metadata: {"parent_id": str, "is_parent": False, "child_index": int}
    """
    if _RecursiveSplitter is None:
        raise ValueError("文本分割器未安装")
    
    if not text or not text.strip():
        return []
    
    # 第一步：创建父块
    parent_splitter = _RecursiveSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    parent_docs = parent_splitter.split_documents([Document(page_content=text)])
    
    # 第二步：为每个父块创建子块
    all_chunks = []
    
    for parent_idx, parent_doc in enumerate(parent_docs):
        parent_id = f"parent_{parent_idx}"
        
        # 添加父块（用于概览）
        parent_doc.metadata.update({
            "parent_id": parent_id,
            "is_parent": True,
            "chunk_index": parent_idx
        })
        all_chunks.append(parent_doc)
        
        # 创建子块分割器
        child_splitter = _RecursiveSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=chunk_overlap // 2,
            separators=["\n\n", "\n", "。", "；", " ", ""]
        )
        
        # 从父块内容创建子块
        child_docs = child_splitter.split_documents([parent_doc])
        
        # 为子块添加元数据
        for child_idx, child_doc in enumerate(child_docs):
            child_doc.metadata.update({
                "parent_id": parent_id,
                "is_parent": False,
                "child_index": child_idx,
                "chunk_index": f"{parent_idx}_{child_idx}"
            })
            all_chunks.append(child_doc)
    
    return all_chunks


@tool
def split_text_hierarchical(
    text: str,
    parent_chunk_size: int = 2000,
    child_chunk_size: int = 500
) -> str:
    """
    使用父子分段模式分割文本（工具包装）
    
    Args:
        text: 要分割的文本
        parent_chunk_size: 父块大小
        child_chunk_size: 子块大小
    
    Returns:
        格式化的分割结果
    """
    try:
        chunks = hierarchical_split(text, parent_chunk_size, child_chunk_size)
        
        result = f"📝 父子分段结果\n"
        result += f"父块大小: {parent_chunk_size} | 子块大小: {child_chunk_size}\n"
        result += f"总块数: {len(chunks)}\n"
        result += "=" * 50 + "\n\n"
        
        for chunk in chunks:
            is_parent = chunk.metadata.get("is_parent", False)
            chunk_type = "【父块】" if is_parent else "  【子块】"
            chunk_id = chunk.metadata.get("chunk_index", "")
            
            result += f"{chunk_type} ID: {chunk_id} ({len(chunk.page_content)} 字符)\n"
            result += f"{chunk.page_content[:100]}...\n\n"
        
        return result
    except Exception as e:
        raise ValueError(f"父子分段失败: {str(e)}")
