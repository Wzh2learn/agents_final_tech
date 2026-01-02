#!/usr/bin/env python3
"""
测试RAG策略功能
"""
import os
import sys
import json

# 添加src到路径
workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
src_path = os.path.join(workspace_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def test_question_classifier():
    """测试问题分类器"""
    print("\n" + "="*60)
    print("测试1: 问题分类器")
    print("="*60)

    test_queries = [
        "什么是建账？",
        "如何进行凭证审核？",
        "现金日记账和银行存款日记账的区别是什么？",
        "固定资产折旧率是多少？",
        "建账有哪些规定？",
        "建账时出现余额不平衡怎么办？"
    ]

    from tools.question_classifier import classify_question_type, get_retrieval_strategy

    for query in test_queries:
        print(f"\n问题: {query}")

        # 分类
        result_str = classify_question_type.func(query)
        result = json.loads(result_str)
        print(f"  类型: {result['type']}, 置信度: {result['confidence']:.2f}, 原因: {result['reason']}")

        # 获取策略
        strategy_str = get_retrieval_strategy.func(result['type'])
        strategy = json.loads(strategy_str)
        print(f"  推荐策略: {strategy['strategy']['method']}, 原因: {strategy['strategy']['reason']}")

    print("\n✓ 问题分类器测试完成")


def test_bm25_retriever():
    """测试BM25检索"""
    print("\n" + "="*60)
    print("测试2: BM25检索")
    print("="*60)

    from tools.bm25_retriever import bm25_retrieve

    query = "建账的基本原则"
    test_docs = [
        {"text": "建账是企业财务管理的基础工作", "id": "1"},
        {"text": "建账需要遵循真实性、完整性、及时性原则", "id": "2"},
        {"text": "如何进行凭证审核的步骤说明", "id": "3"},
        {"text": "固定资产折旧的计算方法", "id": "4"},
    ]

    result_str = bm25_retrieve.func(
        query=query,
        documents=json.dumps(test_docs),
        top_k=3
    )

    result = json.loads(result_str)
    print(f"\n查询: {query}")
    print(f"返回文档数: {result['count']}")

    for i, doc in enumerate(result.get("results", []), 1):
        print(f"\n结果 {i}:")
        print(f"  文档: {doc['document'][:50]}...")
        print(f"  BM25分数: {doc['bm25_score']:.4f}")

    print("\n✓ BM25检索测试完成")


def test_hybrid_retriever():
    """测试混合检索"""
    print("\n" + "="*60)
    print("测试3: 混合检索")
    print("="*60)

    from tools.hybrid_retriever import hybrid_retrieve

    query = "建账的基本原则和要求"

    result_str = hybrid_retrieve.func(
        query=query,
        collection_name="knowledge_base",
        top_k=5,
        vector_weight=0.5,
        bm25_weight=0.5,
        use_rerank=False
    )

    result = json.loads(result_str)
    print(f"\n查询: {query}")
    print(f"返回文档数: {result.get('final_count', 0)}")

    if 'summary' in result:
        print(f"\n摘要:\n{result['summary'][:500]}...")

    print("\n✓ 混合检索测试完成")


def test_smart_retrieve():
    """测试智能检索路由"""
    print("\n" + "="*60)
    print("测试4: 智能检索路由")
    print("="*60)

    from tools.rag_router import smart_retrieve

    test_queries = [
        "什么是建账？",
        "如何进行凭证审核？",
        "现金日记账和银行存款日记账的区别是什么？"
    ]

    for query in test_queries:
        print(f"\n问题: {query}")

        result_str = smart_retrieve.func(
            query=query,
            collection_name="knowledge_base",
            top_k=5,
            verbose=True
        )

        result = json.loads(result_str)

        print(f"  问题类型: {result.get('question_type', 'N/A')}")
        print(f"  选择策略: {result.get('strategy_selected', 'N/A')}")
        print(f"  使用方法: {result.get('method', 'N/A')}")
        print(f"  检索文档数: {result.get('count', 0)}")

        if 'summary' in result:
            print(f"  摘要: {result['summary'][:200]}...")

    print("\n✓ 智能检索路由测试完成")


def test_compare_methods():
    """测试检索方法对比"""
    print("\n" + "="*60)
    print("测试5: 检索方法对比")
    print("="*60)

    from tools.hybrid_retriever import compare_retrieval_methods

    query = "建账的基本原则"

    result_str = compare_retrieval_methods.func(
        query=query,
        collection_name="knowledge_base",
        top_k=5
    )

    result = json.loads(result_str)
    print(f"\n查询: {query}")

    if 'summary' in result:
        print(f"\n{result['summary']}")

    print("\n✓ 检索方法对比测试完成")


def test_batch_retrieve():
    """测试批量检索"""
    print("\n" + "="*60)
    print("测试6: 批量检索")
    print("="*60)

    from tools.rag_router import batch_retrieve

    queries = [
        "什么是建账？",
        "如何进行凭证审核？",
        "建账的基本原则是什么？"
    ]

    result_str = batch_retrieve.func(
        queries=json.dumps(queries),
        collection_name="knowledge_base",
        top_k=5,
        strategy="auto"
    )

    result = json.loads(result_str)

    print(f"\n总查询数: {result['total_queries']}")
    print(f"使用策略: {result['strategy']}")

    if 'summary' in result:
        print(f"\n{result['summary']}")

    print("\n✓ 批量检索测试完成")


def test_statistics():
    """测试检索统计"""
    print("\n" + "="*60)
    print("测试7: 检索统计")
    print("="*60)

    from tools.rag_router import get_retrieval_statistics

    queries = [
        "什么是建账？",
        "如何进行凭证审核？",
        "建账的基本原则是什么？",
        "现金日记账和银行存款日记账的区别是什么？",
        "固定资产折旧率是多少？"
    ]

    result_str = get_retrieval_statistics.func(
        queries=json.dumps(queries),
        collection_name="knowledge_base",
        top_k=5
    )

    result = json.loads(result_str)

    print(f"\n总查询数: {result['total_queries']}")

    if 'summary' in result:
        print(f"\n{result['summary']}")

    print("\n✓ 检索统计测试完成")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("RAG 策略功能测试")
    print("="*60)

    try:
        # 依次执行所有测试
        test_question_classifier()
        test_bm25_retriever()
        test_hybrid_retriever()
        test_smart_retrieve()
        test_compare_methods()
        test_batch_retrieve()
        test_statistics()

        print("\n" + "="*60)
        print("✓ 所有测试完成！")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
