"""
初始化 PGVector 向量数据库
创建PGVector扩展并测试向量存储功能
"""
import sys
import os
import builtins

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from storage.database.db import get_engine
from tools.vector_store import get_embeddings, get_vector_store, check_vector_store_setup
from tools.document_loader import load_document
from langchain_core.documents import Document


def _setup_console_output() -> None:
    """Normalize status symbols for Windows GBK consoles."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass


def _safe_print(*args, **kwargs) -> None:
    normalized = []
    for arg in args:
        text = str(arg)
        text = text.replace("✓", "[OK]")
        text = text.replace("✗", "[ERROR]")
        text = text.replace("⚠️", "[WARN]")
        text = text.replace("📊", "[INFO]")
        normalized.append(text)
    builtins.print(*normalized, **kwargs)


_setup_console_output()
print = _safe_print


def create_pgvector_extension():
    """创建PGVector扩展"""
    print("=" * 50)
    print("步骤 1: 创建 PGVector 扩展")
    print("=" * 50)

    engine = get_engine()

    try:
        with engine.connect() as conn:
            # 检查扩展是否已存在
            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            ))
            exists = result.scalar()

            if exists:
                print("✓ PGVector 扩展已存在")
            else:
                # 创建扩展
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("✓ PGVector 扩展创建成功")

    except Exception as e:
        print(f"✗ 创建 PGVector 扩展失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_embedding_api():
    """测试Embedding API"""
    print("\n" + "=" * 50)
    print("步骤 2: 测试 Embedding API")
    print("=" * 50)

    try:
        print("\n尝试使用硅基流动 Embedding API...")
        embeddings = get_embeddings()
        print(f"✓ Embeddings 实例创建成功")
        print(f"  模型: {embeddings.model}")

        # 测试嵌入单个文本
        test_text = "建账的基本原则"
        print(f"\n测试文本: {test_text}")

        vector = embeddings.embed_query(test_text)
        print(f"✓ 嵌入成功")
        print(f"  向量维度: {len(vector)}")
        print(f"  前5个值: {vector[:5]}")

        # 测试批量嵌入
        test_texts = ["什么是建账", "如何进行凭证审核", "日记账的分类"]
        print(f"\n测试批量嵌入 ({len(test_texts)} 个文本)...")

        vectors = embeddings.embed_documents(test_texts)
        print(f"✓ 批量嵌入成功")
        print(f"  返回向量数量: {len(vectors)}")
        print(f"  每个向量维度: {len(vectors[0])}")

        return True

    except Exception as e:
        print(f"✗ 测试 Embedding API 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store():
    """测试向量存储功能"""
    print("\n" + "=" * 50)
    print("步骤 3: 测试向量存储功能")
    print("=" * 50)

    try:
        print("使用真实 Embedding (硅基流动)...")
        embeddings = get_embeddings()

        # 获取向量存储实例
        vector_store = get_vector_store(
            collection_name="test_collection",
            embeddings=embeddings
        )
        print("✓ 向量存储实例创建成功")

        # 创建测试文档
        test_docs = [
            Document(
                page_content="建账的基本原则包括：真实性原则、完整性原则、及时性原则、一致性原则和重要性原则。",
                metadata={"source": "建账规则.md", "category": "基础规则"}
            ),
            Document(
                page_content="凭证审核的主要流程包括：审核原始凭证的真实性和合法性、审核记账凭证的正确性和完整性、审核凭证的合规性和合理性。",
                metadata={"source": "审核流程.md", "category": "流程规范"}
            ),
            Document(
                page_content="日记账分为现金日记账、银行存款日记账和其他货币资金日记账。现金日记账用于记录现金的收付业务。",
                metadata={"source": "日记账规范.md", "category": "账簿管理"}
            )
        ]

        print(f"\n准备添加 {len(test_docs)} 个测试文档...")
        for i, doc in enumerate(test_docs, 1):
            print(f"  {i}. {doc.metadata['source']}")

        # 添加文档到向量存储
        vector_store.add_documents(test_docs)
        print("✓ 文档添加成功")

        # 测试相似度搜索
        query = "建账的基本原则有哪些"
        print(f"\n测试搜索: {query}")

        results = vector_store.similarity_search(query, k=3)
        print(f"✓ 搜索成功，找到 {len(results)} 个结果\n")

        for i, doc in enumerate(results, 1):
            print(f"  结果 {i}:")
            print(f"    来源: {doc.metadata.get('source', 'unknown')}")
            print(f"    内容: {doc.page_content[:100]}...")
            print()

        # 测试带分数的搜索
        print("测试带分数的搜索...")
        results_with_scores = vector_store.similarity_search_with_score(query, k=3)
        print(f"✓ 搜索成功\n")

        for i, (doc, score) in enumerate(results_with_scores, 1):
            print(f"  结果 {i}:")
            print(f"    相似度: {score:.4f}")
            print(f"    来源: {doc.metadata.get('source', 'unknown')}")
            print(f"    内容: {doc.page_content[:100]}...")
            print()

        # 清理测试数据
        print("清理测试数据...")
        vector_store.delete_collection()
        print("✓ 测试数据已清理")

        return True

    except Exception as e:
        print(f"✗ 测试向量存储失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_document():
    """使用真实文档测试"""
    print("\n" + "=" * 50)
    print("步骤 4: 使用真实文档测试")
    print("=" * 50)

    # 查找assets目录下的测试文档
    workspace_path = os.getenv("WORKSPACE_PATH", "/workspace/projects")
    test_docs_dir = os.path.join(workspace_path, "assets")

    # 查找Markdown文档
    markdown_files = []
    for root, dirs, files in os.walk(test_docs_dir):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))

    if not markdown_files:
        print("✗ 未找到测试文档")
        print("  请在 assets/ 目录下放置 .md 文档")
        return False

    print(f"找到 {len(markdown_files)} 个文档:")
    for file in markdown_files:
        print(f"  - {os.path.relpath(file, test_docs_dir)}")

    # 选择第一个文档进行测试
    test_file = markdown_files[0]
    print(f"\n使用文档: {os.path.basename(test_file)}")

    try:
        # 加载文档
        docs = load_document(file_path=test_file)
        print(f"✓ 文档加载成功，共 {len(docs)} 个chunk")

        # 添加到知识库
        vector_store = get_vector_store(collection_name="knowledge_base")
        print("正在添加到知识库...")

        # 批量添加（每次10个）
        batch_size = 10
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            vector_store.add_documents(batch)
            print(f"  进度: {min(i+batch_size, len(docs))}/{len(docs)}")

        print("✓ 文档已添加到知识库")

        # 测试检索
        print("\n测试检索功能...")
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

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n")
    print("=" * 60)
    print("PGVector 向量数据库初始化")
    print("=" * 60)

    # 步骤 1: 显示配置状态
    print("\n📊 向量存储配置状态:")
    print("=" * 60)
    print(check_vector_store_setup())

    # 步骤 2: 创建PGVector扩展
    if not create_pgvector_extension():
        print("\n✗ 初始化失败：无法创建 PGVector 扩展")
        return False

    # 步骤 3: 测试Embedding API
    if not test_embedding_api():
        print("\n⚠️ Embedding API 测试失败，无法继续向量存储测试")
        print("提示: 可以使用模拟Embedding进行功能测试")
        return False

    # 步骤 4: 测试向量存储
    if not test_vector_store():
        print("\n✗ 初始化失败：无法测试向量存储")
        return False

    # 步骤 5: 使用真实文档测试（可选）
    test_real = input("\n是否使用真实文档测试？(y/n): ").strip().lower()
    if test_real == 'y':
        test_with_real_document()

    # 完成
    print("\n" + "=" * 60)
    print("✓ 初始化完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 运行测试脚本验证功能: python tests/test_rag_strategy.py")
    print("  2. 启动Web服务: python src/web/app.py")
    print("  3. 访问 http://localhost:5000/rag-config 测试RAG配置")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
