#!/usr/bin/env python3
"""
RAG功能集成测试脚本
测试文档加载、分割、向量化、检索和问答完整流程
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# 添加src到路径
workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
src_path = os.path.join(workspace_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 导入RAG工具（使用动态导入）
try:
    from tools.document_loader import document_loader_tool
    from tools.text_splitter import text_splitter_tool
    from tools.vector_store import vector_store_tool
    from tools.reranker_tool import reranker_tool
    from tools.rag_retriever import rag_retrieve_with_rerank
except ImportError as e:
    print(f"导入工具失败: {e}")
    print("将使用创建函数方式导入工具...")
    from tools.document_loader import create_document_loader_tool
    from tools.text_splitter import create_text_splitter_tool
    from tools.vector_store import create_vector_store_tool
    from tools.reranker_tool import create_reranker_tool

    document_loader_tool = create_document_loader_tool()
    text_splitter_tool = create_text_splitter_tool()
    vector_store_tool = create_vector_store_tool()
    reranker_tool = create_reranker_tool()


def test_document_loader():
    """测试文档加载功能"""
    print("\n" + "="*50)
    print("测试1: 文档加载功能")
    print("="*50)

    try:
        # 使用已导入的工具
        loader_tool = document_loader_tool

        # 测试加载Markdown文档（创建测试文档）
        test_md_content = """# 建账规则说明

## 1. 基本原则
建账是企业财务管理的基础工作，需要遵循以下原则：
- 真实性原则：确保所有数据真实准确
- 完整性原则：确保账目完整无遗漏
- 及时性原则：及时记录和更新账目

## 2. 建账流程
1. 收集初始凭证
2. 开设会计科目
3. 录入期初余额
4. 试算平衡
5. 建立账簿体系

## 3. 注意事项
在建账过程中，需要特别注意：
- 核对期初余额的准确性
- 选择合适的会计政策
- 确保科目设置的合理性
"""
        test_md_path = "/tmp/test_document.md"
        with open(test_md_path, "w", encoding="utf-8") as f:
            f.write(test_md_content)

        # 调用工具加载文档
        result = loader_tool.invoke({"file_path": test_md_path})
        print(f"✓ 文档加载成功")
        print(f"  内容长度: {len(result)} 字符")
        print(f"  内容预览: {result[:100]}...")

        # 清理测试文件
        os.remove(test_md_path)
        return True

    except Exception as e:
        print(f"✗ 文档加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_splitter():
    """测试文本分割功能"""
    print("\n" + "="*50)
    print("测试2: 文本分割功能")
    print("="*50)

    try:
        # 使用已导入的工具
        splitter_tool = text_splitter_tool

        # 测试文本
        test_text = """
这是第一段文字，介绍建账的基本概念。建账是指根据会计准则和企业实际情况，建立会计账簿体系的过程。

这是第二段文字，说明建账的重要性。一个完善的会计账簿体系是企业财务管理的基础，能够为企业决策提供准确的数据支持。

这是第三段文字，讲解建账的步骤。建账通常包括以下几个步骤：收集原始凭证、设置会计科目、录入期初余额、试算平衡等。

这是第四段文字，强调建账的注意事项。在建账过程中，需要确保会计科目的设置符合企业实际情况，期初余额的录入准确无误。
        """ * 3  # 重复多次以测试分割

        # 调用工具分割文本
        result = splitter_tool.invoke({
            "text": test_text,
            "chunk_size": 200,
            "chunk_overlap": 50
        })
        chunks = json.loads(result)

        print(f"✓ 文本分割成功")
        print(f"  原始文本长度: {len(test_text)} 字符")
        print(f"  分割后块数: {len(chunks)}")
        print(f"  第一块长度: {len(chunks[0])} 字符")
        print(f"  第一块内容: {chunks[0][:80]}...")

        return True

    except Exception as e:
        print(f"✗ 文本分割测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store():
    """测试向量存储功能"""
    print("\n" + "="*50)
    print("测试3: 向量存储功能")
    print("="*50)

    try:
        # 使用已导入的工具
        vector_store_tool_instance = vector_store_tool

        # 测试文档块
        test_docs = [
            {"text": "建账是财务管理的基础工作", "metadata": {"source": "test", "page": 1}},
            {"text": "会计科目设置需要符合企业实际情况", "metadata": {"source": "test", "page": 2}},
            {"text": "期初余额的录入必须准确无误", "metadata": {"source": "test", "page": 3}},
        ]

        # 调用工具添加文档
        result = vector_store_tool_instance.invoke({
            "action": "add",
            "collection_name": "test_collection",
            "documents": json.dumps(test_docs)
        })

        print(f"✓ 向量存储成功")
        print(f"  {result}")

        return True

    except Exception as e:
        print(f"✗ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reranker():
    """测试Rerank重排序功能"""
    print("\n" + "="*50)
    print("测试4: Rerank重排序功能")
    print("="*50)

    try:
        # 使用已导入的工具
        reranker_tool_instance = reranker_tool

        # 测试查询和文档
        test_query = "如何进行建账工作？"

        test_documents = [
            {"text": "建账是企业财务管理的基础工作", "id": "1"},
            {"text": "今天的天气很好", "id": "2"},
            {"text": "建账包括收集原始凭证、设置科目、录入期初余额等步骤", "id": "3"},
            {"text": "股票市场分析", "id": "4"},
            {"text": "在建账过程中需要确保数据的真实性和完整性", "id": "5"},
        ]

        # 调用工具进行重排序
        result = reranker_tool_instance.invoke({
            "query": test_query,
            "documents": json.dumps(test_documents),
            "top_k": 3
        })

        reranked_docs = json.loads(result)

        print(f"✓ Rerank重排序成功")
        print(f"  查询: {test_query}")
        print(f"  重排序后Top {len(reranked_docs)}:")
        for i, doc in enumerate(reranked_docs, 1):
            print(f"    {i}. [{doc.get('relevance_score', 0):.3f}] {doc['text'][:60]}...")

        return True

    except Exception as e:
        print(f"✗ Rerank重排序测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_qa():
    """测试RAG问答功能"""
    print("\n" + "="*50)
    print("测试5: RAG问答功能")
    print("="*50)

    try:
        # 使用已导入的工具
        rag_tool = rag_retrieve_with_rerank

        # 测试问题
        test_questions = [
            "建账的基本原则是什么？",
            "建账的流程包括哪些步骤？",
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n--- 问题 {i}: {question} ---")

            # 调用RAG工具
            result = rag_tool.invoke({
                "query": question,
                "collection_name": "knowledge_base",
                "top_n": 3,
                "use_rerank": True
            })

            print(f"  检索结果预览: {result[:200]}...")

        print(f"\n✓ RAG问答功能测试完成")

        return True

    except Exception as e:
        print(f"✗ RAG问答测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("RAG功能集成测试")
    print("="*60)

    results = {
        "文档加载": test_document_loader(),
        "文本分割": test_text_splitter(),
        "向量存储": test_vector_store(),
        "Rerank重排序": test_reranker(),
        "RAG问答": test_rag_qa(),
    }

    # 输出测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！RAG系统运行正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
