"""
RAG 动态策略路由
根据问题类型自动选择最优的检索策略
"""
import json
from typing import Optional
from langchain.tools import tool

# 导入相关工具
from tools.question_classifier import classify_question_type, get_retrieval_strategy
from tools.rag_retriever import rag_retrieve_with_rerank
from tools.bm25_retriever import bm25_retrieve
from tools.hybrid_retriever import hybrid_retrieve


@tool
def smart_retrieve(
    query: str,
    documents: str = "[]",
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5,
    override_strategy: Optional[str] = None,
    verbose: Optional[bool] = True
) -> str:
    """
    智能检索路由 - 根据问题类型自动选择最优检索策略

    工作流程：
    1. 对问题进行分类（concept/process/compare/factual/rule/troubleshooting/general）
    2. 根据问题类型选择检索策略
    3. 执行检索
    4. 返回结果

    支持的检索策略：
    - vector: 向量检索（适合语义匹配）
    - bm25: BM25全文检索（适合精确关键词匹配）
    - hybrid: 混合检索（向量+BM25，综合两者优势）
    - hybrid_rerank: 混合检索+Rerank（最精确，但耗时最长）

    Args:
        query: 用户查询
        documents: 文档列表（JSON字符串，用于BM25和混合检索）
        collection_name: 向量集合名称
        top_k: 返回的文档数量
        override_strategy: 强制使用指定策略（跳过自动分类）
        verbose: 是否输出详细过程信息

    Returns:
        JSON 格式的检索结果
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    result = {
        "query": query,
        "strategy_selected": None,
        "question_type": None,
        "confidence": 0.0,
        "reasoning": "",
        "results": [],
        "count": 0
    }

    try:
        # 步骤1: 问题分类
        if override_strategy:
            # 使用用户指定的策略
            result["strategy_selected"] = override_strategy
            result["question_type"] = "manual_override"
            result["confidence"] = 1.0
            result["reasoning"] = f"用户手动指定策略: {override_strategy}"
        else:
            # 自动分类问题
            from tools.question_classifier import classify_question_type
            classification_str = classify_question_type.func(query)
            classification = json.loads(classification_str)

            question_type = classification.get("type", "general")
            confidence = classification.get("confidence", 0.5)
            reason = classification.get("reason", "")

            result["question_type"] = question_type
            result["confidence"] = confidence
            result["classification_reason"] = reason

            # 步骤2: 获取推荐的检索策略
            from tools.question_classifier import get_retrieval_strategy
            strategy_str = get_retrieval_strategy.func(question_type)
            strategy_data = json.loads(strategy_str)

            strategy = strategy_data["strategy"]
            result["strategy_selected"] = strategy["method"]
            if strategy.get("use_rerank"):
                result["strategy_selected"] += "_rerank"

            result["strategy_details"] = strategy
            result["reasoning"] = strategy.get("reason", "根据问题类型自动选择")

        # 步骤3: 执行检索
        strategy = result["strategy_selected"]

        retrieval_result = None

        if strategy == "vector":
            # 向量检索
            from tools.rag_retriever import rag_retrieve_with_rerank
            retrieval_result_str = rag_retrieve_with_rerank.func(
                query=query,
                collection_name=collection_name,
                initial_k=top_k * 2,
                top_n=top_k,
                use_rerank=False
            )
            result["method"] = "向量检索"
            retrieval_result = {"raw": retrieval_result_str}

        elif strategy == "bm25":
            # BM25检索
            from tools.bm25_retriever import bm25_retrieve
            retrieval_result_str = bm25_retrieve.func(
                query=query,
                documents=documents,
                collection_name=collection_name,
                top_k=top_k
            )
            retrieval_result = json.loads(retrieval_result_str)
            result["method"] = "BM25全文检索"
            result["results"] = retrieval_result.get("results", [])
            result["count"] = retrieval_result.get("count", 0)

        elif strategy == "hybrid":
            # 混合检索（不使用Rerank）
            vector_weight = result["strategy_details"].get("vector_weight", 0.5)
            bm25_weight = result["strategy_details"].get("bm25_weight", 0.5)

            from tools.hybrid_retriever import hybrid_retrieve
            retrieval_result_str = hybrid_retrieve.func(
                query=query,
                documents=documents,
                collection_name=collection_name,
                top_k=top_k,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                use_rerank=False
            )
            retrieval_result = json.loads(retrieval_result_str)
            result["method"] = "混合检索（向量+BM25）"
            result["results"] = retrieval_result.get("final_results", [])
            result["count"] = retrieval_result.get("final_count", 0)

        elif strategy == "hybrid_rerank":
            # 混合检索 + Rerank
            vector_weight = result["strategy_details"].get("vector_weight", 0.5)
            bm25_weight = result["strategy_details"].get("bm25_weight", 0.5)

            from tools.hybrid_retriever import hybrid_retrieve
            retrieval_result_str = hybrid_retrieve.func(
                query=query,
                documents=documents,
                collection_name=collection_name,
                top_k=top_k,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                use_rerank=True
            )
            retrieval_result = json.loads(retrieval_result_str)
            result["method"] = "混合检索+Rerank（向量+BM25+重排）"
            result["results"] = retrieval_result.get("final_results", [])
            result["count"] = retrieval_result.get("final_count", 0)

        else:
            # 默认使用向量检索
            from tools.rag_retriever import rag_retrieve_with_rerank
            retrieval_result_str = rag_retrieve_with_rerank.func(
                query=query,
                collection_name=collection_name,
                initial_k=top_k * 2,
                top_n=top_k,
                use_rerank=False
            )
            result["method"] = "向量检索（默认）"
            retrieval_result = {"raw": retrieval_result_str}

        # 如果有summary字段，使用它
        if "summary" in retrieval_result:
            result["summary"] = retrieval_result["summary"]
        elif "raw" in retrieval_result:
            result["summary"] = retrieval_result["raw"]

        # 添加详细过程信息
        if verbose:
            result["verbose"] = {
                "question_type": result["question_type"],
                "classification_confidence": result["confidence"],
                "strategy_selected": result["strategy_selected"],
                "strategy_reasoning": result["reasoning"],
                "method_used": result["method"],
                "documents_retrieved": result["count"]
            }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        result["error"] = f"智能检索失败: {str(e)}"
        result["summary"] = f"❌ 智能检索失败: {str(e)}"
        return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def batch_retrieve(
    queries: str,
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5,
    strategy: Optional[str] = "auto"
) -> str:
    """
    批量检索 - 对多个查询执行智能检索
    """
    try:
        query_list = json.loads(queries)
    except json.JSONDecodeError:
        return json.dumps({
            "error": "queries参数必须是有效的JSON数组",
            "queries": queries
        }, ensure_ascii=False, indent=2)

    results = {
        "total_queries": len(query_list),
        "strategy": strategy,
        "results": []
    }

    for i, query in enumerate(query_list, 1):
        try:
            from tools.rag_router import smart_retrieve
            retrieval_result_str = smart_retrieve.func(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                override_strategy=strategy if strategy != "auto" else None,
                verbose=False
            )

            retrieval_result = json.loads(retrieval_result_str)

            results["results"].append({
                "index": i,
                "query": query,
                "question_type": retrieval_result.get("question_type"),
                "strategy": retrieval_result.get("strategy_selected"),
                "count": retrieval_result.get("count", 0),
                "summary": retrieval_result.get("summary", "")[:200],
                "error": retrieval_result.get("error")
            })

        except Exception as e:
            results["results"].append({
                "index": i,
                "query": query,
                "error": f"检索失败: {str(e)}"
            })

    # 生成摘要
    successful = sum(1 for r in results["results"] if "error" not in r)
    failed = len(results["results"]) - successful

    summary = f"📦 批量检索完成\n"
    summary += f"总查询数: {results['total_queries']}\n"
    summary += f"成功: {successful}\n"
    summary += f"失败: {failed}\n"
    summary += f"策略: {strategy}\n"
    summary += "=" * 60 + "\n\n"

    for r in results["results"]:
        if "error" not in r:
            summary += f"[{r['index']}] {r['query'][:50]}...\n"
            summary += f"  类型: {r.get('question_type', 'N/A')}\n"
            summary += f"  策略: {r.get('strategy', 'N/A')}\n"
            summary += f"  文档数: {r.get('count', 0)}\n\n"
        else:
            summary += f"[{r['index']}] {r['query'][:50]}...\n"
            summary += f"  ❌ {r['error']}\n\n"

    results["summary"] = summary

    return json.dumps(results, ensure_ascii=False, indent=2)


@tool
def get_retrieval_statistics(
    queries: str,
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5
) -> str:
    """
    获取检索统计信息 - 分析不同策略的效果对比
    """
    try:
        query_list = json.loads(queries)
    except json.JSONDecodeError:
        return json.dumps({
            "error": "queries参数必须是有效的JSON数组"
        }, ensure_ascii=False, indent=2)

    stats = {
        "total_queries": len(query_list),
        "strategies": {
            "vector": {"count": 0, "avg_docs": 0, "avg_top_score": 0},
            "bm25": {"count": 0, "avg_docs": 0, "avg_top_score": 0},
            "hybrid": {"count": 0, "avg_docs": 0, "avg_top_score": 0},
            "hybrid_rerank": {"count": 0, "avg_docs": 0, "avg_top_score": 0}
        },
        "question_types": {}
    }

    for query in query_list:
        try:
            from tools.rag_router import smart_retrieve
            result_str = smart_retrieve.func(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                verbose=True
            )
            result = json.loads(result_str)

            # 统计策略使用
            strategy = result.get("strategy_selected", "vector")
            if strategy in stats["strategies"]:
                stats["strategies"][strategy]["count"] += 1
                stats["strategies"][strategy]["avg_docs"] += result.get("count", 0)

                # 提取top分数
                results_list = result.get("results", [])
                if results_list:
                    top_score = 0.0
                    if strategy == "bm25":
                        top_score = results_list[0].get("bm25_score", 0)
                    elif "hybrid" in strategy:
                        top_score = results_list[0].get("hybrid_score", results_list[0].get("rerank_score", 0))
                    else:
                        top_score = results_list[0].get("vector_score", 0)
                    stats["strategies"][strategy]["avg_top_score"] += top_score

            # 统计问题类型
            question_type = result.get("question_type", "general")
            if question_type not in stats["question_types"]:
                stats["question_types"][question_type] = 0
            stats["question_types"][question_type] += 1

        except Exception as e:
            print(f"统计查询失败: {query[:50]}... 错误: {e}")

    # 计算平均值
    for strategy, data in stats["strategies"].items():
        count = data["count"]
        if count > 0:
            data["avg_docs"] = round(data["avg_docs"] / count, 2)
            data["avg_top_score"] = round(data["avg_top_score"] / count, 4)

    # 生成摘要
    summary = f"📊 检索统计报告\n"
    summary += f"总查询数: {stats['total_queries']}\n"
    summary += "=" * 60 + "\n\n"

    summary += "【策略使用统计】\n"
    for strategy, data in stats["strategies"].items():
        if data["count"] > 0:
            summary += f"{strategy}: {data['count']}次, "
            summary += f"平均文档数: {data['avg_docs']}, "
            summary += f"平均Top分数: {data['avg_top_score']}\n"

    summary += "\n【问题类型分布】\n"
    for qtype, count in stats["question_types"].items():
        summary += f"{qtype}: {count} ({count/stats['total_queries']*100:.1f}%)\n"

    stats["summary"] = summary

    return json.dumps(stats, ensure_ascii=False, indent=2)
