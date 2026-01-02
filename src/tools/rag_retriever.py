"""
RAG 检索工具
整合向量检索和 Rerank 重排
"""
import json
from typing import Optional, List
from langchain.tools import tool
from langchain_core.documents import Document

# 导入相关工具
from tools.vector_store import get_vector_store
from tools.reranker_tool import _init_reranker, _reranker_model


@tool
def rag_retrieve_with_rerank(
    query: str,
    collection_name: Optional[str] = "knowledge_base",
    initial_k: Optional[int] = 20,
    top_n: Optional[int] = 5,
    use_rerank: Optional[bool] = True,
    rerank_model: Optional[str] = "BAAI/bge-reranker-large"
) -> str:
    """
    RAG 检索（向量检索 + Rerank 重排）

    Args:
        query: 查询文本
        collection_name: 向量集合名称
        initial_k: 初始检索文档数（用于 rerank，默认 20）
        top_n: 最终返回的文档数（rerank 后，默认 5）
        use_rerank: 是否使用 rerank（默认 True）
        rerank_model: reranker 模型名称
            - "BAAI/bge-reranker-large": 大模型（默认）
            - "BAAI/bge-reranker-base": 基础模型（更快）

    Returns:
        检索结果（带相似度分数和 rerank 分数）

    Raises:
        ValueError: 如果查询为空
        RuntimeError: 如果检索失败
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    try:
        # 第一步：向量检索
        vector_store = get_vector_store(collection_name=collection_name)

        # 执行相似度搜索
        vector_results = vector_store.similarity_search_with_score(
            query=query,
            k=initial_k
        )

        if not vector_results:
            return f"🔍 RAG 检索结果\n\n未找到相关文档\n"

        # 第二步：Rerank 重排（如果启用）
        if use_rerank:
            # 初始化 reranker
            reranker = _init_reranker(rerank_model)

            # 准备 rerank 输入
            rerank_inputs = []
            for doc, score in vector_results:
                rerank_inputs.append([query, doc.page_content])

            # 执行 rerank
            rerank_scores = reranker.predict(rerank_inputs)

            # 组合结果
            ranked_results = []
            for (doc, vec_score), rerank_score in zip(vector_results, rerank_scores):
                ranked_results.append({
                    "document": doc,
                    "vector_score": float(vec_score),
                    "rerank_score": float(rerank_score)
                })

            # 按 rerank 分数降序排序
            ranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)

            # 返回 top-n 结果
            top_results = ranked_results[:top_n]
        else:
            # 不使用 rerank，直接返回向量检索结果
            top_results = []
            for doc, score in vector_results[:top_n]:
                top_results.append({
                    "document": doc,
                    "vector_score": float(score),
                    "rerank_score": None
                })

        # 格式化输出
        result = f"🔍 RAG 检索结果\n"
        result += f"查询: {query}\n"
        result += f"使用 Rerank: {'是' if use_rerank else '否'}\n"
        if use_rerank:
            result += f"Rerank 模型: {rerank_model}\n"
        result += f"初始检索: {initial_k} 文档\n"
        result += f"返回结果: {len(top_results)} 文档\n"
        result += "=" * 50 + "\n\n"

        for i, item in enumerate(top_results, 1):
            doc = item["document"]
            result += f"【结果 {i}】\n"
            result += f"向量相似度: {item['vector_score']:.4f}\n"
            if item["rerank_score"] is not None:
                result += f"Rerank 分数: {item['rerank_score']:.4f}\n"
            result += f"内容: {doc.page_content[:400]}...\n"
            if doc.metadata:
                result += f"来源: {doc.metadata.get('source', '未知')}\n"
                result += f"元数据: {json.dumps(doc.metadata, ensure_ascii=False)}\n"
            result += "\n"

        return result

    except Exception as e:
        raise RuntimeError(f"RAG 检索失败: {str(e)}")


@tool
def hybrid_search(
    query: str,
    collection_name: Optional[str] = "knowledge_base",
    k: Optional[int] = 5
) -> str:
    """
    混合搜索（同时返回向量检索和 Rerank 结果对比）

    Args:
        query: 查询文本
        collection_name: 向量集合名称
        k: 返回的文档数

    Returns:
        混合搜索结果（对比向量检索和 Rerank 结果）
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    try:
        # 向量检索
        vector_result = rag_retrieve_with_rerank(
            query=query,
            collection_name=collection_name,
            initial_k=k,
            top_n=k,
            use_rerank=False
        )

        # Rerank 检索
        rerank_result = rag_retrieve_with_rerank(
            query=query,
            collection_name=collection_name,
            initial_k=k * 2,  # Rerank 需要更多候选
            top_n=k,
            use_rerank=True
        )

        # 对比结果
        result = f"🔄 混合搜索对比\n"
        result += f"查询: {query}\n"
        result += "=" * 50 + "\n\n"
        result += "【向量检索结果】\n"
        result += vector_result + "\n\n"
        result += "【Rerank 检索结果】\n"
        result += rerank_result

        return result

    except Exception as e:
        raise RuntimeError(f"混合搜索失败: {str(e)}")


@tool
def format_docs_for_rag(
    docs: str,
    max_length: Optional[int] = 2000
) -> str:
    """
    格式化检索到的文档用于 RAG 生成

    Args:
        docs: 文档列表（JSON 字符串格式）
            格式示例:
            [
                {"content": "文档1内容", "metadata": {"source": "doc1"}},
                {"content": "文档2内容", "metadata": {"source": "doc2"}}
            ]
        max_length: 总内容最大长度（字符数）

    Returns:
        格式化的文档字符串（用于 LLM 上下文）
    """
    try:
        # 解析文档
        doc_list = json.loads(docs)

        # 构建格式化内容
        formatted = "以下是相关的知识库内容：\n\n"

        total_length = 0
        for i, doc in enumerate(doc_list, 1):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            source = metadata.get('source', f'文档 {i}')

            formatted_content = f"[来源: {source}]\n{content}\n\n"
            formatted_content_length = len(formatted_content)

            # 检查是否超出最大长度
            if max_length and total_length + formatted_content_length > max_length:
                formatted += f"... (已省略部分内容以保持上下文在 {max_length} 字符以内)\n"
                break

            formatted += formatted_content
            total_length += formatted_content_length

        return formatted

    except json.JSONDecodeError:
        raise ValueError("docs 应该是有效的 JSON 数组格式")
    except Exception as e:
        raise RuntimeError(f"格式化文档失败: {str(e)}")
