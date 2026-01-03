"""
简单测试BM25检索功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.bm25_retriever import _bm25_retrieve_internal, clear_bm25_cache

def test_bm25_with_sample_documents():
    """测试BM25检索功能"""
    print("=" * 60)
    print("测试 BM25 全文检索功能")
    print("=" * 60)

    # 准备测试文档
    test_documents = [
        {
            "text": "建账的基本原则包括：真实性原则、完整性原则、及时性原则、一致性原则和重要性原则。",
            "metadata": {"source": "建账规则.md", "category": "基础规则"}
        },
        {
            "text": "凭证审核的主要流程包括：审核原始凭证的真实性和合法性、审核记账凭证的正确性和完整性、审核凭证的合规性和合理性。",
            "metadata": {"source": "审核流程.md", "category": "流程规范"}
        },
        {
            "text": "日记账分为现金日记账、银行存款日记账和其他货币资金日记账。现金日记账用于记录现金的收付业务。",
            "metadata": {"source": "日记账规范.md", "category": "账簿管理"}
        },
        {
            "text": "总分类账是根据会计科目设置，用来汇总全部经济业务的账簿。它是对明细分类账的汇总和控制。",
            "metadata": {"source": "总账规范.md", "category": "账簿管理"}
        },
        {
            "text": "会计凭证分为原始凭证和记账凭证。原始凭证是在经济业务发生或完成时取得或填制的凭证。",
            "metadata": {"source": "凭证管理.md", "category": "凭证管理"}
        }
    ]

    print("\n1. 测试文档列表:")
    for i, doc in enumerate(test_documents, 1):
        print(f"   {i}. {doc['metadata']['source']}: {doc['text'][:50]}...")

    # 测试查询
    test_queries = [
        "建账的基本原则",
        "如何进行凭证审核",
        "日记账的分类"
    ]

    print(f"\n2. 准备测试 {len(test_queries)} 个查询...")

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")

        try:
            # 调用BM25检索
            result_str = _bm25_retrieve_internal(
                query=query,
                documents=str(test_documents).replace("'", '"'),  # 转换为JSON字符串
                top_k=3
            )

            # 解析结果
            import json
            result = json.loads(result_str)

            print(f"\n检索结果 ({result['count']} 条):")
            for i, item in enumerate(result.get('results', []), 1):
                print(f"\n  结果 {i}:")
                print(f"    BM25分数: {item.get('bm25_score', 0):.4f}")
                print(f"    来源: {item.get('metadata', {}).get('source', 'unknown')}")
                print(f"    内容: {item.get('document', '')[:100]}...")

            if 'error' in result:
                print(f"\n  错误: {result['error']}")

        except Exception as e:
            print(f"\n  ✗ 检索失败: {e}")
            import traceback
            traceback.print_exc()

    # 清理缓存（跳过，因为clear_bm25_cache是工具函数）
    # print(f"\n{'='*60}")
    # print("清理BM25缓存...")
    # print(f"{'='*60}")

    # try:
    #     clear_cache_result = clear_bm25_cache.invoke({"collection_name": None})
    #     print(f"✓ 缓存已清理: {clear_cache_result}")
    # except Exception as e:
    #     print(f"✗ 清理缓存失败: {e}")

    print(f"\n{'='*60}")
    print("✓ 测试完成！")
    print(f"{'='*60}")


if __name__ == '__main__':
    test_bm25_with_sample_documents()
