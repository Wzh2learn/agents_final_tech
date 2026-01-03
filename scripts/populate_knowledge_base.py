"""
添加示例文档到知识库
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.mock_embedding import get_mock_embeddings
from tools.vector_store import get_vector_store
from langchain_core.documents import Document

# 导入分割器
from langchain_text_splitters import RecursiveCharacterTextSplitter


def populate_knowledge_base():
    """添加示例文档到知识库"""
    print("=" * 60)
    print("添加示例文档到知识库")
    print("=" * 60)

    # 获取模拟Embedding
    print("\n初始化模拟Embedding...")
    embeddings = get_mock_embeddings()
    print("✓ Embedding初始化成功")

    # 获取向量存储实例
    print("\n初始化向量存储...")
    vector_store = get_vector_store(
        collection_name="knowledge_base",
        embeddings=embeddings
    )
    print("✓ 向量存储初始化成功")

    # 创建文本分割器
    print("\n初始化文本分割器...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    print("✓ 文本分割器初始化成功")

    # 查找示例文档
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
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

    for i, file_path in enumerate(markdown_files, 1):
        print(f"\n[{i}/{len(markdown_files)}] 处理: {os.path.basename(file_path)}")

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"  ✓ 文件读取成功，共 {len(content)} 字符")

            # 分割文本
            chunks = text_splitter.split_text(content)
            print(f"  ✓ 文本分割成功，共 {len(chunks)} 个chunk")

            # 创建Document对象
            documents = []
            for idx, chunk in enumerate(chunks, 1):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'source': os.path.basename(file_path),
                        'chunk_index': idx,
                        'total_chunks': len(chunks),
                        'file_path': file_path
                    }
                )
                documents.append(doc)

            # 添加到向量存储
            vector_store.add_documents(documents)
            total_chunks += len(documents)
            print(f"  ✓ 已添加到知识库")

        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()

    # 测试检索
    print(f"\n{'='*60}")
    print("测试检索功能")
    print(f"{'='*60}")

    try:
        test_queries = [
            "建账的基本原则",
            "如何进行凭证审核",
            "日记账的分类"
        ]

        for query in test_queries:
            print(f"\n查询: {query}")
            results = vector_store.similarity_search(query, k=2)

            for i, doc in enumerate(results, 1):
                print(f"  {i}. {doc.page_content[:80]}...")
                print(f"     来源: {doc.metadata.get('source', 'unknown')}")

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
