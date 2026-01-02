#!/usr/bin/env python3
"""
RAG功能简单测试脚本
"""

import os
import sys
import json

# 添加src到路径
workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
src_path = os.path.join(workspace_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def test_all():
    """测试所有RAG相关工具"""
    print("\n" + "="*60)
    print("RAG功能测试")
    print("="*60)

    # 测试1: 导入检查
    print("\n[测试1] 检查RAG相关工具导入...")
    try:
        from tools.document_loader import load_document
        from tools.text_splitter import split_text_recursive
        from tools.knowledge_base import add_document_to_knowledge_base
        from tools.reranker_tool import rerank_documents
        from tools.rag_retriever import rag_retrieve_with_rerank
        print("✓ 所有工具导入成功")
    except ImportError as e:
        print(f"✗ 工具导入失败: {e}")
        return False

    # 测试2: 文档加载
    print("\n[测试2] 测试文档加载功能...")
    try:
        # 创建测试Markdown文件
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
        test_md_path = "/tmp/test_rag_doc.md"
        with open(test_md_path, "w", encoding="utf-8") as f:
            f.write(test_md_content)

        # 调用加载工具
        result = load_document.invoke({"file_path": test_md_path})
        print(f"✓ 文档加载成功，内容长度: {len(result)} 字符")

        # 清理测试文件
        os.remove(test_md_path)

    except Exception as e:
        print(f"✗ 文档加载测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试3: 文本分割
    print("\n[测试3] 测试文本分割功能...")
    try:
        test_text = test_md_content

        result = split_text_recursive.invoke({
            "text": test_text,
            "chunk_size": 200,
            "chunk_overlap": 50
        })

        chunks = json.loads(result)
        print(f"✓ 文本分割成功")
        print(f"  原始文本: {len(test_text)} 字符")
        print(f"  分割后: {len(chunks)} 个块")

    except Exception as e:
        print(f"✗ 文本分割测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试4: 知识库管理
    print("\n[测试4] 测试知识库管理功能...")
    try:
        # 准备测试文档
        test_docs = [
            {
                "text": "建账是财务管理的基础工作",
                "metadata": {"source": "test", "type": "principle"}
            },
            {
                "text": "会计科目设置需要符合企业实际情况",
                "metadata": {"source": "test", "type": "rule"}
            },
            {
                "text": "期初余额的录入必须准确无误",
                "metadata": {"source": "test", "type": "rule"}
            },
        ]

        result = add_document_to_knowledge_base.invoke({
            "documents": json.dumps(test_docs),
            "collection_name": "test_kb",
            "batch_size": 10
        })

        print(f"✓ 知识库管理测试完成")
        print(f"  结果: {result}")

    except Exception as e:
        print(f"✗ 知识库管理测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试5: Rerank重排序
    print("\n[测试5] 测试Rerank重排序功能...")
    try:
        test_query = "如何进行建账工作？"
        test_documents = [
            {"text": "建账是企业财务管理的基础工作", "id": "1"},
            {"text": "今天的天气很好", "id": "2"},
            {"text": "建账包括收集原始凭证、设置科目、录入期初余额等步骤", "id": "3"},
            {"text": "股票市场分析", "id": "4"},
        ]

        result = rerank_documents.invoke({
            "query": test_query,
            "documents": json.dumps(test_documents),
            "top_k": 3
        })

        reranked = json.loads(result)
        print(f"✓ Rerank重排序成功")
        print(f"  查询: {test_query}")
        for i, doc in enumerate(reranked, 1):
            score = doc.get('relevance_score', 0)
            print(f"  {i}. [{score:.3f}] {doc['text'][:50]}...")

    except Exception as e:
        print(f"✗ Rerank测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试6: RAG检索
    print("\n[测试6] 测试RAG检索功能...")
    try:
        test_query = "建账的原则是什么？"

        result = rag_retrieve_with_rerank.invoke({
            "query": test_query,
            "collection_name": "knowledge_base",
            "top_n": 3,
            "use_rerank": True
        })

        print(f"✓ RAG检索成功")
        print(f"  查询: {test_query}")
        print(f"  结果预览: {result[:200]}...")

    except Exception as e:
        print(f"✗ RAG检索测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    return True


if __name__ == "__main__":
    test_all()
