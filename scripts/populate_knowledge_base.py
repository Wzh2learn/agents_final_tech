"""
添加示例文档到知识库
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from biz.rag_service import get_rag_service
from langchain_core.documents import Document

# 导入分割器
from langchain_text_splitters import RecursiveCharacterTextSplitter


def populate_knowledge_base():
    """添加示例文档到知识库"""
    print("=" * 60)
    print("添加示例文档到知识库 (通过 RAGService)")
    print("=" * 60)

    rag_service = get_rag_service()

    # 查找示例文档
    workspace_path = os.getenv("WORKSPACE_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_dir = os.path.join(workspace_path, "assets")

    print(f"\n搜索示例文档...")
    markdown_files = []
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            if file.endswith('.md') or file.endswith('.docx'):
                full_path = os.path.join(root, file)
                markdown_files.append(full_path)

    if not markdown_files:
        print("✗ 未找到示例文档")
        return False

    print(f"✓ 找到 {len(markdown_files)} 个文档:")
    for i, file in enumerate(markdown_files, 1):
        print(f"  {i}. {os.path.relpath(file, assets_dir)}")

    # 添加文档到知识库
    print(f"\n添加文档到知识库...")
    total_chunks = 0

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for i, file_path in enumerate(markdown_files, 1):
        print(f"\n[{i}/{len(markdown_files)}] 处理: {os.path.basename(file_path)}")

        try:
            # 使用 RAGService 统一全流程处理
            res = loop.run_until_complete(rag_service.ingest_file(file_path))
            total_chunks += res["chunks"]
            print(f"  ✓ 处理完成: {res['chunks']} 个chunk, Key: {res['object_key']}")

        except Exception as e:
            print(f"  ✗ 处理失败: {e}")

    # 测试检索
    print(f"\n{'='*60}")
    print("测试检索功能 (Smart Retrieve)")
    print(f"{'='*60}")

    try:
        test_queries = [
            "建账的基本原则",
            "如何进行凭证审核",
            "日记账的分类"
        ]

        for query in test_queries:
            print(f"\n查询: {query}")
            results = rag_service.smart_retrieve(query, top_k=2)

            for i, item in enumerate(results, 1):
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                print(f"  {i}. {content[:80]}...")
                print(f"     来源: {metadata.get('source', 'unknown')}")

    except Exception as e:
        print(f"\n检索测试失败: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"✓ 知识库初始化完成！")
    print(f"{'='*60}")
    print(f"\n总计添加 {len(markdown_files)} 个文档，{total_chunks} 个chunk")

    return True


if __name__ == '__main__':
    success = populate_knowledge_base()
    sys.exit(0 if success else 1)
