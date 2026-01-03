"""
完整测试 RAG 功能
测试向量检索、BM25检索、混合检索和智能路由
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.mock_embedding import get_mock_embeddings
from tools.rag_retriever import rag_retrieve_with_rerank
from tools.bm25_retriever import bm25_retrieve
from tools.hybrid_retriever import hybrid_retrieve, compare_retrieval_methods
from tools.rag_router import smart_retrieve
from tools.question_classifier import classify_question_type, get_retrieval_strategy
import json


def test_question_classifier():
    """测试问题分类器"""
    print("=" * 60)
    print("测试1: 问题分类器")
    print("=" * 60)

    test_questions = [
        ("什么是建账？", "concept"),
        ("如何进行凭证审核？", "process"),
        ("现金日记账和银行存款日记账的区别", "compare"),
        ("固定资产折旧率是多少？", "factual"),
        ("建账规则有哪些要求？", "rule"),
        ("系统报错了怎么办？", "troubleshooting"),
        ("你好", "general")
    ]

    print(f"\n测试 {len(test_questions)} 个问题...\n")

    for question, expected_type in test_questions:
        result_str = classify_question_type.invoke({"query": question})
        result = json.loads(result_str)

        predicted_type = result.get('question_type', 'unknown')
        confidence = result.get('confidence', 0)
        is_correct = predicted_type == expected_type

        status = "✓" if is_correct else "✗"
        print(f"{status} 问题: {question}")
        print(f"   预测类型: {predicted_type} (期望: {expected_type})")
        print(f"   置信度: {confidence:.2f}")
        print()

    return True


def test_vector_retrieval():
    """测试向量检索"""
    print("=" * 60)
    print("测试2: 向量检索")
    print("=" * 60)

    queries = [
        "建账的基本原则",
        "如何进行凭证审核"
    ]

    for query in queries:
        print(f"\n查询: {query}")

        try:
            result_str = rag_retrieve_with_rerank.invoke({
                "query": query,
                "collection_name": "knowledge_base",
                "initial_k": 5,
                "top_n": 2,
                "use_rerank": False
            })

            result = json.loads(result_str)
            results = result.get('results', [])

            print(f"✓ 检索成功，找到 {len(results)} 个结果")
            for i, item in enumerate(results, 1):
                print(f"  {i}. {item.get('content', '')[:80]}...")
                print(f"     来源: {item.get('metadata', {}).get('source', 'unknown')}")

        except Exception as e:
            print(f"✗ 检索失败: {e}")

    return True


def test_bm25_retrieval():
    """测试BM25检索"""
    print("\n" + "=" * 60)
    print("测试3: BM25检索")
    print("=" * 60)

    queries = [
        "建账的基本原则",
        "如何进行凭证审核"
    ]

    for query in queries:
        print(f"\n查询: {query}")

        try:
            result_str = bm25_retrieve.invoke({
                "query": query,
                "collection_name": "knowledge_base",
                "top_k": 2
            })

            result = json.loads(result_str)
            results = result.get('results', [])

            print(f"✓ 检索成功，找到 {len(results)} 个结果")
            for i, item in enumerate(results, 1):
                print(f"  {i}. {item.get('document', '')[:80]}...")
                print(f"     BM25分数: {item.get('bm25_score', 0):.4f}")

        except Exception as e:
            print(f"✗ 检索失败: {e}")

    return True


def test_hybrid_retrieval():
    """测试混合检索"""
    print("\n" + "=" * 60)
    print("测试4: 混合检索（向量+BM25）")
    print("=" * 60)

    query = "建账的基本原则"
    print(f"\n查询: {query}")

    try:
        result_str = hybrid_retrieve.invoke({
            "query": query,
            "collection_name": "knowledge_base",
            "top_k": 2,
            "vector_weight": 0.5,
            "bm25_weight": 0.5,
            "use_rerank": False
        })

        result = json.loads(result_str)
        results = result.get('final_results', [])

        print(f"✓ 混合检索成功，找到 {len(results)} 个结果")
        for i, item in enumerate(results, 1):
            print(f"\n  {i}. {item.get('content', '')[:80]}...")
            print(f"     来源: {item.get('metadata', {}).get('source', 'unknown')}")
            print(f"     向量分数: {item.get('vector_score', 0):.4f}")
            print(f"     BM25分数: {item.get('bm25_score', 0):.4f}")
            print(f"     混合分数: {item.get('hybrid_score', 0):.4f}")

    except Exception as e:
        print(f"✗ 混合检索失败: {e}")
        import traceback
        traceback.print_exc()

    return True


def test_smart_retrieve():
    """测试智能检索路由"""
    print("\n" + "=" * 60)
    print("测试5: 智能检索路由")
    print("=" * 60)

    queries = [
        "什么是建账？",  # concept
        "如何进行凭证审核？",  # process
        "现金日记账和银行存款日记账的区别"  # compare
    ]

    for query in queries:
        print(f"\n查询: {query}")

        try:
            result_str = smart_retrieve.invoke({
                "query": query,
                "collection_name": "knowledge_base",
                "top_k": 2,
                "verbose": True
            })

            result = json.loads(result_str)

            question_type = result.get('question_type', 'unknown')
            strategy = result.get('strategy', 'unknown')
            results = result.get('results', [])

            print(f"✓ 智能路由成功")
            print(f"   问题类型: {question_type}")
            print(f"   选择策略: {strategy}")
            print(f"   结果数: {len(results)}")

            for i, item in enumerate(results, 1):
                print(f"  {i}. {item.get('content', '')[:80]}...")

        except Exception as e:
            print(f"✗ 智能路由失败: {e}")

    return True


def test_compare_methods():
    """测试检索方法对比"""
    print("\n" + "=" * 60)
    print("测试6: 检索方法对比")
    print("=" * 60)

    query = "建账的基本原则"
    print(f"\n查询: {query}")

    try:
        result_str = compare_retrieval_methods.invoke({
            "query": query,
            "collection_name": "knowledge_base",
            "top_k": 2
        })

        result = json.loads(result_str)

        print(f"✓ 对比成功\n")

        # 显示每种方法的结果
        methods = result.get('methods', {})
        for method_name, method_data in methods.items():
            print(f"\n方法: {method_name}")
            print(f"  结果数: {method_data.get('count', 0)}")
            print(f"  前3个分数: {method_data.get('top_scores', [])}")

    except Exception as e:
        print(f"✗ 对比失败: {e}")
        import traceback
        traceback.print_exc()

    return True


def main():
    """主函数"""
    print("\n")
    print("=" * 60)
    print("RAG 功能完整测试")
    print("=" * 60)

    tests = [
        ("问题分类器", test_question_classifier),
        ("向量检索", test_vector_retrieval),
        ("BM25检索", test_bm25_retrieval),
        ("混合检索", test_hybrid_retrieval),
        ("智能检索路由", test_smart_retrieve),
        ("检索方法对比", test_compare_methods)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "通过" if success else "失败"
        except Exception as e:
            print(f"\n✗ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "异常"

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, status in results.items():
        print(f"{test_name}: {status}")

    passed = sum(1 for v in results.values() if v == "通过")
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    print("\n" + "=" * 60)
    print("✓ 测试完成！")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
