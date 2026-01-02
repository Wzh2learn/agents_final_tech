"""
RAG 检索工具
整合向量检索和 LLM Rerank 重排
"""
import json
from typing import Optional, List
from langchain.tools import tool
from langchain_core.documents import Document

# 导入相关工具
from tools.vector_store import get_vector_store
from tools.reranker_tool import rerank_documents


@tool
def rag_retrieve_with_rerank(
    query: str,
    collection_name: Optional[str] = "knowledge_base",
    initial_k: Optional[int] = 20,
    top_n: Optional[int] = 5,
    use_rerank: Optional[bool] = True
) -> str:
    """
    RAG 检索（向量检索 + LLM Rerank 重排）

    Args:
        query: 查询文本
        collection_name: 向量集合名称
        initial_k: 初始检索文档数（用于 rerank，默认 20）
        top_n: 最终返回的文档数（rerank 后，默认 5）
        use_rerank: 是否使用 rerank（默认 True）

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

        # 第二步：LLM Rerank 重排（如果启用）
        if use_rerank:
            # 准备 rerank 输入
            rerank_docs = []
            for i, (doc, score) in enumerate(vector_results):
                rerank_docs.append({
                    "content": doc.page_content,
                    "id": str(i),
                    "vector_score": float(score)
                })

            # 调用 rerank 工具
            from tools.reranker_tool import rerank_documents as rerank_func
            rerank_json = rerank_func(
                query=query,
                documents=json.dumps(rerank_docs),
                top_n=top_n
            )

            # 解析 rerank 结果
            rerank_results = json.loads(rerank_json)

            # 组合结果
            final_results = []
            for ranked_doc in rerank_results:
                doc_id = int(ranked_doc.get("id", "0"))
                # 找到原始文档
                for doc, vec_score in vector_results:
                    if str(vector_results.index((doc, vec_score))) == str(doc_id):
                        final_results.append({
                            "document": doc,
                            "vector_score": vec_score,
                            "rerank_score": ranked_doc.get("relevance_score", 0.5),
                            "reason": ranked_doc.get("reason", "")
                        })
                        break
        else:
            # 不使用 rerank，直接返回向量检索结果
            final_results = []
            for doc, score in vector_results[:top_n]:
                final_results.append({
                    "document": doc,
                    "vector_score": float(score),
                    "rerank_score": None,
                    "reason": ""
                })

        # 格式化输出
        result = f"🔍 RAG 检索结果\n"
        result += f"查询: {query}\n"
        result += f"使用 Rerank: {'是' if use_rerank else '否'}\n"
        result += f"初始检索: {initial_k} 文档\n"
        result += f"返回结果: {len(final_results)} 文档\n"
        result += "=" * 50 + "\n\n"

        for i, item in enumerate(final_results, 1):
            doc = item["document"]
            result += f"【结果 {i}】\n"
            result += f"向量相似度: {item['vector_score']:.4f}\n"
            if item["rerank_score"] is not None:
                result += f"Rerank 分数: {item['rerank_score']:.4f}\n"
                if item.get("reason"):
                    result += f"相关原因: {item['reason']}\n"
            result += f"内容: {doc.page_content[:400]}...\n"
            if doc.metadata:
                result += f"来源: {doc.metadata.get('source', '未知')}\n"
            result += "\n"

        return result

    except Exception as e:
        raise RuntimeError(f"RAG 检索失败: {str(e)}")
