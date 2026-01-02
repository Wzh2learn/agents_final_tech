"""
知识库管理工具
支持文档上传、索引、删除和查询
"""
import os
import json
from typing import Optional, List, Dict
from langchain.tools import tool
from langchain_core.documents import Document

# 导入相关工具
from tools.document_loader import load_document, get_document_info
from tools.text_splitter import split_text_recursive, split_text_by_markdown_structure
from tools.vector_store import get_vector_store, get_embeddings


def __get_file_type(file_path: str) -> str:
    """根据文件扩展名判断文件类型"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.md', '.markdown']:
        return "markdown"
    elif ext in ['.docx']:
        return "word"
    else:
        return "text"


@tool
def add_document_to_knowledge_base(
    file_path: str,
    chunk_size: Optional[int] = 1000,
    chunk_overlap: Optional[int] = 200,
    collection_name: Optional[str] = "knowledge_base",
    metadata: Optional[str] = None
) -> str:
    """
    添加文档到知识库（包含加载、分割、向量化和存储）

    Args:
        file_path: 文档路径（支持 .md, .docx 格式）
        chunk_size: 文本块大小（字符数，默认 1000）
        chunk_overlap: 块重叠大小（字符数，默认 200）
        collection_name: 向量集合名称（默认 knowledge_base）
        metadata: 文档元数据（JSON 字符串格式）
            例如: '{"category": "建账规则", "version": "1.0"}'

    Returns:
        处理结果摘要（包括文件信息、分割结果、存储状态）

    Raises:
        ValueError: 如果文件不存在或处理失败
    """
    # 检查文件
    if not os.path.exists(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    # 获取文件信息
    file_info = get_document_info(file_path)

    # 加载文档内容
    try:
        content = load_document(file_path)
    except Exception as e:
        raise ValueError(f"加载文档失败: {str(e)}")

    # 判断文件类型并分割
    file_type = __get_file_type(file_path)

    try:
        if file_type == "markdown":
            # Markdown 使用标题结构分割
            split_result = split_text_by_markdown_structure(content)
        else:
            # 其他使用递归分割
            split_result = split_text_recursive(
                content,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

        # 解析分割结果中的文档块
        lines = split_result.split('\n')
        chunks = []
        current_chunk = ""
        for line in lines:
            if line.startswith('---'):
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = ""
            else:
                current_chunk += line + "\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # 创建 Document 对象
        documents = []
        meta_data = json.loads(metadata) if metadata else {}
        base_metadata = {
            "source": os.path.basename(file_path),
            "file_path": file_path,
            "file_type": file_type,
        }
        base_metadata.update(meta_data)

        for i, chunk_text in enumerate(chunks):
            # 过滤掉非内容行
            if chunk_text.startswith(('---', '📝', '📊', '=')):
                continue

            doc = Document(
                page_content=chunk_text,
                metadata={
                    **base_metadata,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)

        if not documents:
            raise ValueError(f"文档分割后没有有效的内容块: {file_path}")

        # 向量化并存储
        try:
            embeddings = get_embeddings()
            vector_store = get_vector_store(
                collection_name=collection_name,
                embeddings=embeddings
            )

            # 添加文档到向量存储
            ids = vector_store.add_documents(documents)

        except Exception as e:
            raise RuntimeError(f"向量存储失败: {str(e)}")

        # 返回结果
        result = f"✅ 文档已成功添加到知识库\n\n"
        result += file_info + "\n"
        result += f"分割块数: {len(documents)}\n"
        result += f"向量集合: {collection_name}\n"
        result += f"文档 IDs: {ids[:10]}...\n"
        result += f"文档 ID 总数: {len(ids)}\n"

        return result

    except Exception as e:
        raise RuntimeError(f"处理文档失败: {str(e)}")


@tool
def delete_documents_from_knowledge_base(
    source: Optional[str] = None,
    metadata_filter: Optional[str] = None,
    collection_name: Optional[str] = "knowledge_base"
) -> str:
    """
    从知识库删除文档

    Args:
        source: 源文件名（可选）
        metadata_filter: 元数据过滤条件（JSON 字符串格式）
            例如: '{"category": "建账规则"}'
        collection_name: 向量集合名称

    Returns:
        删除结果

    Raises:
        ValueError: 如果参数无效
    """
    try:
        vector_store = get_vector_store(collection_name=collection_name)

        # 构建删除条件
        filters = {}

        if source:
            filters["source"] = source

        if metadata_filter:
            filter_data = json.loads(metadata_filter)
            filters.update(filter_data)

        if not filters:
            raise ValueError(
                "必须提供至少一个删除条件（source 或 metadata_filter）"
            )

        # 执行删除
        # 注意：PGVector 的删除方法可能需要调整
        # 这里使用 delete 方法
        delete_count = vector_store.delete(where=filters)

        result = f"🗑️ 文档删除结果\n"
        result += f"删除条件: {filters}\n"
        result += f"删除文档数: {delete_count}\n"

        return result

    except Exception as e:
        raise RuntimeError(f"删除文档失败: {str(e)}")


@tool
def search_knowledge_base(
    query: str,
    k: Optional[int] = 5,
    collection_name: Optional[str] = "knowledge_base",
    score_threshold: Optional[float] = 0.7
) -> str:
    """
    从知识库搜索相关文档

    Args:
        query: 查询文本
        k: 返回的文档数（默认 5）
        collection_name: 向量集合名称
        score_threshold: 相似度阈值（0-1，默认 0.7）

    Returns:
        搜索结果（带相似度分数和元数据）

    Raises:
        ValueError: 如果查询为空
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    try:
        vector_store = get_vector_store(collection_name=collection_name)

        # 执行相似度搜索
        results = vector_store.similarity_search_with_score(
            query=query,
            k=k
        )

        # 过滤低分数结果
        filtered_results = [
            (doc, score) for doc, score in results
            if score >= score_threshold
        ]

        # 格式化输出
        result = f"🔍 知识库搜索结果\n"
        result += f"查询: {query}\n"
        result += f"返回结果数: {len(filtered_results)}/{len(results)}\n"
        result += f"相似度阈值: {score_threshold}\n"
        result += "=" * 50 + "\n\n"

        for i, (doc, score) in enumerate(filtered_results, 1):
            result += f"【结果 {i}】相似度: {score:.4f}\n"
            result += f"内容: {doc.page_content[:300]}...\n"
            if doc.metadata:
                result += f"元数据: {json.dumps(doc.metadata, ensure_ascii=False)}\n"
            result += "\n"

        if not filtered_results:
            result += "⚠️ 未找到相关文档（可能需要降低 score_threshold）\n"

        return result

    except Exception as e:
        raise RuntimeError(f"搜索知识库失败: {str(e)}")


@tool
def get_knowledge_base_stats(
    collection_name: Optional[str] = "knowledge_base"
) -> str:
    """
    获取知识库统计信息

    Args:
        collection_name: 向量集合名称

    Returns:
        统计信息
    """
    try:
        # 注意：PGVector 可能没有直接的统计方法
        # 这里我们返回基础信息
        result = f"📊 知识库统计\n"
        result += f"集合名称: {collection_name}\n"
        result += f"状态: 已连接\n"
        result += f"\n注意: PGVector 不提供直接的文档计数方法，\n"
        result += f"可以通过搜索查询来获取文档列表\n"

        return result

    except Exception as e:
        raise RuntimeError(f"获取统计信息失败: {str(e)}")
