"""
向量存储配置
支持 PGVector 向量数据库
"""
import os
from typing import Optional, Union
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# 全局变量
_vector_store = None
_embeddings = None


def __get_connection_string() -> str:
    """获取 PostgreSQL 连接字符串"""
    # 从环境变量读取数据库配置
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "vector_db")

    # 使用 psycopg3 连接字符串
    connection_string = (
        f"postgresql+psycopg://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    return connection_string


def __dynamic_import():
    """动态导入 PGVector 和 embeddings"""
    global _vector_store, _embeddings

    # 尝试导入 PGVector
    try:
        from langchain_postgres import PGVector
        _vector_store = PGVector
    except ImportError:
        _vector_store = None

    # 尝试导入 embeddings（使用 HuggingFace）
    try:
        from sentence_transformers import SentenceTransformer
        _embeddings = SentenceTransformer
    except ImportError:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            _embeddings = HuggingFaceEmbeddings
        except ImportError:
            _embeddings = None

    return _vector_store, _embeddings


_VectorStoreClass, _EmbeddingsClass = __dynamic_import()


def get_embeddings(model_name: str = "BAAI/bge-small-zh-v1.5"):
    """
    获取 embeddings 实例

    Args:
        model_name: embedding 模型名称
            默认使用 BGE 中文小模型

    Returns:
        Embeddings 实例
    """
    global _embeddings

    # 如果已经实例化，直接返回
    if hasattr(_embeddings, 'embed_documents'):
        # 如果是 SentenceTransformer 实例
        if _embeddings.__class__.__name__ == 'SentenceTransformer':
            return _embeddings
        # 如果是 HuggingFaceEmbeddings 实例
        elif hasattr(_embeddings, 'model'):
            return _embeddings

    # 创建新的 embeddings 实例
    if _embeddings is None:
        raise RuntimeError(
            "Embeddings 库未安装，请运行: "
            "pip install sentence-transformers 或 pip install langchain-huggingface"
        )

    try:
        # 使用 HuggingFaceEmbeddings 包装
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # 可根据环境改为 'cuda'
            encode_kwargs={'normalize_embeddings': True}
        )
        return embeddings
    except Exception as e:
        raise RuntimeError(f"创建 embeddings 失败: {str(e)}")


def get_vector_store(
    collection_name: str = "knowledge_base",
    embeddings: Optional[Embeddings] = None,
    connection_string: Optional[str] = None
):
    """
    获取 PGVector 向量存储实例

    Args:
        collection_name: 集合名称
        embeddings: Embeddings 实例（如果为 None，使用默认）
        connection_string: 数据库连接字符串（如果为 None，使用默认）

    Returns:
        PGVector 实例

    Raises:
        RuntimeError: 如果 PGVector 未安装
    """
    global _vector_store

    if _vector_store is None:
        raise RuntimeError(
            "PGVector 库未安装，请运行: "
            "pip install langchain-postgres"
        )

    if connection_string is None:
        connection_string = __get_connection_string()

    try:
        vector_store = _vector_store(
            collection_name=collection_name,
            connection=connection_string,
            embeddings=embeddings or get_embeddings(),
            use_jsonb=True,  # 使用 JSONB 提高性能
        )

        return vector_store

    except Exception as e:
        raise RuntimeError(f"创建向量存储失败: {str(e)}")


def check_vector_store_setup() -> str:
    """
    检查向量存储设置状态

    Returns:
        设置状态信息
    """
    status = {
        "PGVector": "已安装" if _vector_store else "未安装",
        "Embeddings": "已安装" if _embeddings else "未安装",
        "数据库配置": __get_connection_string().replace(os.getenv("POSTGRES_PASSWORD", ""), "****"),
        "安装命令": [
            "pip install langchain-postgres",
            "pip install sentence-transformers"
        ]
    }

    result = "📊 向量存储状态检查\n"
    result += "=" * 40 + "\n"
    for key, value in status.items():
        if isinstance(value, list):
            result += f"{key}:\n"
            for v in value:
                result += f"  - {v}\n"
        else:
            result += f"{key}: {value}\n"

    return result
