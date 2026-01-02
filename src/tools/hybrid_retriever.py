"""
混合检索策略工具
结合向量检索和BM25全文检索，实现更精确的检索
"""
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from langchain.tools import tool

# 导入相关工具
from tools.rag_retriever import rag_retrieve_with_rerank
from tools.bm25_retriever import bm25_retrieve
from tools.reranker_tool import rerank_documents


def _normalize_scores(scores: List[float], method: str = "minmax") -> List[float]:
    """
    归一化分数到[0, 1]区间

    Args:
        scores: 原始分数列表
        method: 归一化方法（minmax=最小-最大归一化，sigmoid=Sigmoid归一化）

    Returns:
        归一化后的分数列表
    """
    if not scores:
        return []

    scores = np.array(scores)

    if method == "minmax":
        # 最小-最大归一化
        min_score = scores.min()
        max_score = scores.max()
        if max_score - min_score > 0:
            normalized = (scores - min_score) / (max_score - min_score)
        else:
            normalized = np.ones_like(scores) * 0.5
    elif method == "sigmoid":
        # Sigmoid归一化（适合分数范围较大的情况）
        normalized = 1 / (1 + np.exp(-scores))
    else:
        # 默认使用minmax
        return _normalize_scores(scores, "minmax")

    return normalized.tolist()


def _merge_results(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    vector_weight: float,
    bm25_weight: float
) -> List[Dict[str, Any]]:
    """
    融合向量检索和BM25检索的结果

    Args:
        vector_results: 向量检索结果
        bm25_results: BM25检索结果
        vector_weight: 向量检索权重
        bm25_weight: BM25检索权重

    Returns:
        融合后的结果列表
    """
    # 创建文档ID到结果的映射
    vector_map = {}
    for i, result in enumerate(vector_results):
        # 使用文档内容或索引作为唯一标识
        doc_id = result.get("document", "").strip()[:50]  # 使用前50个字符作为ID
        vector_map[doc_id] = {
            "result": result,
            "vector_score": result.get("vector_score", result.get("score", 0)),
            "bm25_score": 0.0,
            "index": i
        }

    bm25_map = {}
    for i, result in enumerate(bm25_results):
        doc_id = result.get("document", "").strip()[:50]
        bm25_map[doc_id] = {
            "result": result,
            "bm25_score": result.get("bm25_score", result.get("score", 0)),
            "vector_score": 0.0,
            "index": i
        }

    # 合并两个映射
    all_doc_ids = set(vector_map.keys()) | set(bm25_map.keys())

    merged_results = []

    for doc_id in all_doc_ids:
        if doc_id in vector_map and doc_id in bm25_map:
            # 文档在两个检索结果中都存在
            vector_data = vector_map[doc_id]
            bm25_data = bm25_map[doc_id]

            merged_results.append({
                "document": vector_data["result"].get("document", ""),
                "metadata": vector_data["result"].get("metadata", {}),
                "vector_score": float(vector_data["vector_score"]),
                "bm25_score": float(bm25_data["bm25_score"]),
                "vector_rank": vector_data["index"],
                "bm25_rank": bm25_data["index"]
            })

        elif doc_id in vector_map:
            # 文档只在向量检索结果中
            vector_data = vector_map[doc_id]
            merged_results.append({
                "document": vector_data["result"].get("document", ""),
                "metadata": vector_data["result"].get("metadata", {}),
                "vector_score": float(vector_data["vector_score"]),
                "bm25_score": 0.0,
                "vector_rank": vector_data["index"],
                "bm25_rank": -1
            })

        else:
            # 文档只在BM25检索结果中
            bm25_data = bm25_map[doc_id]
            merged_results.append({
                "document": bm25_data["result"].get("document", ""),
                "metadata": bm25_data["result"].get("metadata", {}),
                "vector_score": 0.0,
                "bm25_score": float(bm25_data["bm25_score"]),
                "vector_rank": -1,
                "bm25_rank": bm25_data["index"]
            })

    return merged_results


def _calculate_hybrid_score(
    merged_results: List[Dict[str, Any]],
    vector_weight: float,
    bm25_weight: float,
    score_method: str = "weighted"
) -> List[Tuple[int, float]]:
    """
    计算混合检索分数

    Args:
        merged_results: 融合后的结果列表
        vector_weight: 向量检索权重
        bm25_weight: BM25检索权重
        score_method: 分数计算方法

    Returns:
        (索引, 分数)的排序列表
    """
    vector_scores = [r.get("vector_score", 0) for r in merged_results]
    bm25_scores = [r.get("bm25_score", 0) for r in merged_results]

    # 归一化分数
    vector_normalized = _normalize_scores(vector_scores)
    bm25_normalized = _normalize_scores(bm25_scores)

    hybrid_scores = []

    for i, result in enumerate(merged_results):
        vec_score = vector_normalized[i]
        bm25_score = bm25_normalized[i]

        if score_method == "weighted":
            # 加权平均
            hybrid_score = vec_score * vector_weight + bm25_score * bm25_weight

        elif score_method == "rrf":
            # Reciprocal Rank Fusion（倒数排名融合）
            k = 60  # RRF常数
            vec_rank = result.get("vector_rank", -1)
            bm25_rank = result.get("bm25_rank", -1)

            vec_rrf = 1 / (k + vec_rank + 1) if vec_rank >= 0 else 0
            bm25_rrf = 1 / (k + bm25_rank + 1) if bm25_rank >= 0 else 0

            hybrid_score = vec_rrf * vector_weight + bm25_rrf * bm25_weight

        else:
            # 默认使用加权平均
            hybrid_score = vec_score * vector_weight + bm25_score * bm25_weight

        result["hybrid_score"] = float(hybrid_score)
        hybrid_scores.append((i, hybrid_score))

    # 按分数降序排序
    hybrid_scores.sort(key=lambda x: x[1], reverse=True)

    return hybrid_scores


def _parse_vector_retrieval_result(result_str: str) -> List[Dict[str, Any]]:
    """
    解析向量检索结果字符串

    Args:
        result_str: 向量检索工具返回的字符串

    Returns:
        解析后的文档列表
    """
    # 这里需要根据实际返回的字符串格式进行解析
    # 由于rag_retrieve_with_rerank返回的是格式化文本，这里做简化处理
    # 实际应该改进向量检索工具，使其返回结构化的JSON

    # 简化处理：返回空列表，实际需要解析
    return []


def _get_vector_retrieval_documents(
    query: str,
    collection_name: str,
    initial_k: int
) -> List[Dict[str, Any]]:
    """
    获取向量检索的文档

    Args:
        query: 查询文本
        collection_name: 集合名称
        initial_k: 初始检索数量

    Returns:
        文档列表
    """
    try:
        # 获取向量存储
        from tools.vector_store import get_vector_store
        vector_store = get_vector_store(collection_name=collection_name)

        # 执行相似度搜索
        results = vector_store.similarity_search_with_score(
            query=query,
            k=initial_k
        )

        # 转换为字典格式
        documents = []
        for doc, score in results:
            documents.append({
                "text": doc.page_content,
                "document": doc.page_content,
                "metadata": doc.metadata,
                "vector_score": float(score),
                "score": float(score)
            })

        return documents

    except Exception as e:
        print(f"向量检索失败: {e}")
        return []


@tool
def hybrid_retrieve(
    query: str,
    documents: str = "[]",
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5,
    vector_weight: Optional[float] = 0.5,
    bm25_weight: Optional[float] = 0.5,
    score_method: Optional[str] = "weighted",
    use_rerank: Optional[bool] = False
) -> str:
    """
    混合检索（向量检索 + BM25全文检索 + 可选Rerank）

    Args:
        query: 查询文本
        documents: 文档列表（JSON字符串），用于BM25检索
        collection_name: 向量集合名称，用于向量检索
        top_k: 返回的文档数量
        vector_weight: 向量检索权重（0-1，默认0.5）
        bm25_weight: BM25检索权重（0-1，默认0.5）
        score_method: 融合方法（weighted=加权平均，rrf=倒数排名融合）
        use_rerank: 是否使用Rerank重排序

    Returns:
        JSON 格式的混合检索结果
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    # 归一化权重
    total_weight = vector_weight + bm25_weight
    if total_weight > 0:
        vector_weight = vector_weight / total_weight
        bm25_weight = bm25_weight / total_weight

    # 初始化结果
    results = {
        "query": query,
        "method": "hybrid",
        "parameters": {
            "vector_weight": vector_weight,
            "bm25_weight": bm25_weight,
            "top_k": top_k,
            "score_method": score_method,
            "use_rerank": use_rerank
        },
        "vector_count": 0,
        "bm25_count": 0,
        "final_count": 0,
        "results": []
    }

    try:
        # 1. 向量检索（获取更多文档以便融合）
        initial_k = min(top_k * 3, 50)  # 获取3倍的文档用于融合
        vector_docs = _get_vector_retrieval_documents(query, collection_name, initial_k)
        results["vector_count"] = len(vector_docs)

        # 2. BM25检索
        from tools.bm25_retriever import bm25_retrieve as bm25_retrieve_func
        bm25_result_str = bm25_retrieve_func(
            query=query,
            documents=documents,
            collection_name=collection_name,
            top_k=initial_k
        )
        bm25_result = json.loads(bm25_result_str)
        bm25_docs = bm25_result.get("results", [])
        results["bm25_count"] = len(bm25_docs)

        # 3. 融合结果
        merged_results = _merge_results(vector_docs, bm25_docs, vector_weight, bm25_weight)

        # 4. 计算混合分数
        if merged_results:
            hybrid_scores = _calculate_hybrid_score(
                merged_results,
                vector_weight,
                bm25_weight,
                score_method
            )

            # 取top_k结果
            final_results = []
            for idx, score in hybrid_scores[:top_k]:
                result = merged_results[idx].copy()
                result["hybrid_rank"] = len(final_results) + 1
                final_results.append(result)

            # 5. 可选的Rerank重排
            if use_rerank and final_results:
                # 准备rerank输入
                rerank_docs = []
                for i, r in enumerate(final_results):
                    rerank_docs.append({
                        "content": r.get("document", ""),
                        "id": str(i),
                        "hybrid_score": r.get("hybrid_score", 0)
                    })

                # 调用rerank
                from tools.reranker_tool import rerank_documents as rerank_func
                rerank_json = rerank_func(
                    query=query,
                    documents=json.dumps(rerank_docs),
                    top_n=top_k
                )
                rerank_results = json.loads(rerank_json)

                # 更新最终结果
                for ranked_doc in rerank_results:
                    doc_id = int(ranked_doc.get("id", "0"))
                    if doc_id < len(final_results):
                        final_results[doc_id]["rerank_score"] = ranked_doc.get("relevance_score", 0.5)
                        final_results[doc_id]["rerank_reason"] = ranked_doc.get("reason", "")

                # 按rerank分数重新排序
                final_results.sort(
                    key=lambda x: x.get("rerank_score", x.get("hybrid_score", 0)),
                    reverse=True
                )

            results["final_results"] = final_results
            results["final_count"] = len(final_results)

        # 格式化输出用于展示
        output_text = f"🔍 混合检索结果\n"
        output_text += f"查询: {query}\n"
        output_text += f"向量检索权重: {vector_weight:.2f}\n"
        output_text += f"BM25检索权重: {bm25_weight:.2f}\n"
        output_text += f"融合方法: {score_method}\n"
        output_text += f"使用Rerank: {'是' if use_rerank else '否'}\n"
        output_text += f"向量检索: {results['vector_count']} 文档\n"
        output_text += f"BM25检索: {results['bm25_count']} 文档\n"
        output_text += f"最终返回: {results['final_count']} 文档\n"
        output_text += "=" * 60 + "\n\n"

        for i, result in enumerate(final_results, 1):
            output_text += f"【结果 {i}】\n"
            output_text += f"向量分数: {result.get('vector_score', 0):.4f}\n"
            output_text += f"BM25分数: {result.get('bm25_score', 0):.4f}\n"
            output_text += f"混合分数: {result.get('hybrid_score', 0):.4f}\n"
            if "rerank_score" in result:
                output_text += f"Rerank分数: {result['rerank_score']:.4f}\n"
                if "rerank_reason" in result and result["rerank_reason"]:
                    output_text += f"Rerank原因: {result['rerank_reason']}\n"
            output_text += f"内容: {result.get('document', '')[:300]}...\n"
            if result.get("metadata"):
                output_text += f"来源: {result['metadata'].get('source', '未知')}\n"
            output_text += "\n"

        results["summary"] = output_text

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        results["error"] = f"混合检索失败: {str(e)}"
        results["summary"] = f"❌ 混合检索失败: {str(e)}"
        return json.dumps(results, ensure_ascii=False, indent=2)


@tool
def compare_retrieval_methods(
    query: str,
    documents: str = "[]",
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5
) -> str:
    """
    对比不同检索方法的结果

    对比以下方法：
    1. 向量检索
    2. BM25检索
    3. 混合检索（向量+BM25）
    4. 混合检索+Rerank

    Args:
        query: 查询文本
        documents: 文档列表（JSON字符串）
        collection_name: 向量集合名称
        top_k: 返回的文档数量

    Returns:
        JSON 格式的对比结果
    """
    comparison = {
        "query": query,
        "methods": {}
    }

    try:
        # 1. 向量检索
        vector_result = _get_vector_retrieval_documents(query, collection_name, top_k)
        comparison["methods"]["vector"] = {
            "count": len(vector_result),
            "top_scores": [r.get("vector_score", 0) for r in vector_result[:3]]
        }

        # 2. BM25检索
        from tools.bm25_retriever import bm25_retrieve as bm25_func
        bm25_result_str = bm25_func(
            query=query,
            documents=documents,
            collection_name=collection_name,
            top_k=top_k
        )
        bm25_result = json.loads(bm25_result_str)
        bm25_docs = bm25_result.get("results", [])
        comparison["methods"]["bm25"] = {
            "count": len(bm25_docs),
            "top_scores": [r.get("bm25_score", 0) for r in bm25_docs[:3]]
        }

        # 3. 混合检索（不使用Rerank）
        hybrid_result_str = hybrid_retrieve(
            query=query,
            documents=documents,
            collection_name=collection_name,
            top_k=top_k,
            vector_weight=0.5,
            bm25_weight=0.5,
            use_rerank=False
        )
        hybrid_result = json.loads(hybrid_result_str)
        hybrid_docs = hybrid_result.get("final_results", [])
        comparison["methods"]["hybrid"] = {
            "count": len(hybrid_docs),
            "top_scores": [r.get("hybrid_score", 0) for r in hybrid_docs[:3]]
        }

        # 4. 混合检索+Rerank
        hybrid_rerank_str = hybrid_retrieve(
            query=query,
            documents=documents,
            collection_name=collection_name,
            top_k=top_k,
            vector_weight=0.5,
            bm25_weight=0.5,
            use_rerank=True
        )
        hybrid_rerank_result = json.loads(hybrid_rerank_str)
        hybrid_rerank_docs = hybrid_rerank_result.get("final_results", [])
        comparison["methods"]["hybrid_rerank"] = {
            "count": len(hybrid_rerank_docs),
            "top_scores": [r.get("rerank_score", r.get("hybrid_score", 0)) for r in hybrid_rerank_docs[:3]]
        }

        # 生成对比摘要
        summary = f"📊 检索方法对比\n"
        summary += f"查询: {query}\n"
        summary += f"返回数量: {top_k}\n"
        summary += "=" * 60 + "\n\n"

        for method_name, method_data in comparison["methods"].items():
            summary += f"【{method_name.upper()}】\n"
            summary += f"  文档数: {method_data['count']}\n"
            summary += f"  Top-3 分数: {', '.join([f'{s:.4f}' for s in method_data['top_scores']])}\n"
            summary += "\n"

        comparison["summary"] = summary

        return json.dumps(comparison, ensure_ascii=False, indent=2)

    except Exception as e:
        comparison["error"] = f"对比失败: {str(e)}"
        comparison["summary"] = f"❌ 对比失败: {str(e)}"
        return json.dumps(comparison, ensure_ascii=False, indent=2)
