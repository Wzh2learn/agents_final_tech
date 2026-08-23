"""
向量存储配置
支持 PGVector 向量数据库 + 硅基流动 (SiliconFlow) Embedding API
"""
import os
import re
import threading
from pathlib import Path
from typing import Optional, Union, List
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from utils.config_loader import get_config
from utils.openai_network import get_openai_sync_network_kwargs

# 全局变量
_vector_store = None
_embeddings_client = None

# [PG 池泄漏修复 2026-08-23 菜单 a] 实例缓存: 此前每次调用构造新 PGVector 实例
# (各带独立 SQLAlchemy engine + 池), 实例随请求丢弃 → idle 连接泄漏打满
# (归因: docs/experiments/2026-08-23_pg_pool_leak_attribution.md)。
# 现按 (collection_name, connection_string) 缓存实例, Lock 护竞态。
_STORE_INSTANCE_CACHE: dict = {}
_STORE_INSTANCE_CACHE_LOCK = threading.Lock()


def __get_connection_string() -> str:
    """获取 PostgreSQL 连接字符串"""
    # 优先使用 PGDATABASE_URL 环境变量
    pg_url = os.getenv("PGDATABASE_URL")
    if pg_url:
        # Ensure it uses psycopg (v3) driver
        if pg_url.startswith("postgresql://"):
            pg_url = pg_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return pg_url

    # 否则使用单独的环境变量
    db_user = os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres"))
    db_password = os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", ""))
    db_host = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost"))
    db_port = os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))
    db_name = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "vector_db"))

    # 使用 psycopg3 连接字符串
    connection_string = (
        f"postgresql+psycopg://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    return connection_string


class SiliconFlowEmbeddings(Embeddings):
    """硅基流动 Embedding API 封装（兼容 LangChain Embeddings 接口）"""

    def __init__(
        self,
        model: str = "BAAI/bge-m3",
        api_key: Optional[str] = None,
        base_url: Optional[str] = "https://api.siliconflow.cn/v1"
    ):
        """
        初始化硅基流动 Embedding

        Args:
            model: 模型名称
            api_key: API Key（默认从环境变量读取）
            base_url: Base URL（默认从环境变量读取）
        """
        self.model = model
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self.base_url = base_url or os.getenv("SILICONFLOW_BASE_URL") or "https://api.siliconflow.cn/v1"

        if not self.api_key:
            raise ValueError("未找到 API Key 环境变量 (SILICONFLOW_API_KEY)")

        # 动态导入 OpenAI 客户端
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                **get_openai_sync_network_kwargs()
            )
        except ImportError:
            raise RuntimeError(
                "未安装 openai 库，请运行: pip install openai"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入多个文本
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            raise RuntimeError(f"调用硅基流动 Embedding API 失败: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单个查询
        """
        return self.embed_documents([text])[0]


class LocalSentenceTransformerEmbeddings(Embeddings):
    """Sentence Transformers adapter for an explicitly configured local model."""

    def __init__(self, model_path: str, device: str = "cuda"):
        path = Path(model_path).expanduser()
        if not path.is_dir():
            raise ValueError(f"本地 Embedding 模型目录不存在: {path}")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("本地 Embedding 需要 sentence-transformers") from exc
        self.model_path = str(path)
        self.device = device
        self.model = SentenceTransformer(
            self.model_path,
            trust_remote_code=True,
            device=device,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


def __dynamic_import():
    """动态导入 PGVector"""
    global _vector_store

    # 尝试导入 PGVector
    try:
        from langchain_postgres import PGVector
        _vector_store = PGVector
    except ImportError:
        _vector_store = None

    return _vector_store


_VectorStoreClass = __dynamic_import()


def get_embeddings(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> Embeddings:
    """
    获取硅基流动 Embeddings 实例
    """
    global _embeddings_client

    # 单例模式，避免重复创建
    if _embeddings_client is not None:
        return _embeddings_client

    try:
        local_model_path = os.getenv("LOCAL_EMBEDDING_MODEL_PATH")
        if local_model_path:
            _embeddings_client = LocalSentenceTransformerEmbeddings(
                model_path=local_model_path,
                device=os.getenv("LOCAL_EMBEDDING_DEVICE", "cpu"),  # GB10 ARM64: CUDA Triton JIT 不可用，缺省必须 cpu
            )
            return _embeddings_client

        config = get_config()
        embedding_model = model or config.get("embedding.model", "Qwen/Qwen3-Embedding-0.6B")
        api_key_env = config.get("embedding.api_key_env", "SILICONFLOW_API_KEY")
        base_url_env = config.get("embedding.base_url_env", "SILICONFLOW_BASE_URL")
        embedding_api_key = api_key or os.getenv(api_key_env)
        embedding_base_url = base_url or os.getenv(base_url_env) or "https://api.siliconflow.cn/v1"

        _embeddings_client = SiliconFlowEmbeddings(
            model=embedding_model,
            api_key=embedding_api_key,
            base_url=embedding_base_url
        )
        return _embeddings_client
    except Exception as e:
        raise RuntimeError(f"创建 Embeddings 失败: {str(e)}")


def get_vector_store(
    collection_name: str = "knowledge_base",
    embeddings: Optional[Embeddings] = None,
    connection_string: Optional[str] = None
):
    """
    获取 PGVector 向量存储实例

    Args:
        collection_name: 集合名称
        embeddings: Embeddings 实例（如果为 None，使用豆包 Embedding）
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

    # [PG 池泄漏修复] 调用方显式传 embeddings 时不走缓存, 避免实例误用
    use_cache = embeddings is None
    cache_key = (collection_name, connection_string)
    if use_cache:
        with _STORE_INSTANCE_CACHE_LOCK:
            cached = _STORE_INSTANCE_CACHE.get(cache_key)
        if cached is not None:
            return cached

    # 使用豆包 Embedding 或用户提供的 embeddings
    embeddings = embeddings or get_embeddings()

    try:
        vector_store = _vector_store(
            collection_name=collection_name,
            connection=connection_string,
            embeddings=embeddings,
            use_jsonb=True,  # 使用 JSONB 提高性能
        )
        if use_cache:
            with _STORE_INSTANCE_CACHE_LOCK:
                # setdefault: 竞态时以先构造的实例为准, 避免重复 engine
                vector_store = _STORE_INSTANCE_CACHE.setdefault(cache_key, vector_store)
        return vector_store

    except Exception as e:
        raise RuntimeError(f"创建向量存储失败: {str(e)}")


def check_vector_store_setup() -> str:
    """
    检查向量存储设置状态
    """
    connection_string = __get_connection_string()
    password = (
        os.getenv("POSTGRES_PASSWORD")
        or os.getenv("PGPASSWORD")
        or ""
    )
    if password:
        masked_connection = connection_string.replace(password, "****")
    else:
        # Fallback: mask password-like segment in URL
        masked_connection = re.sub(r":([^:@/]+)@", ":****@", connection_string, count=1)

    status = {
        "PGVector": "已安装" if _vector_store else "未安装",
        "SiliconFlow Embedding": "已配置" if _embeddings_client else "未配置",
        "数据库配置": masked_connection,
        "模型": "Qwen/Qwen3-Embedding-0.6B",
        "安装命令": [
            "pip install langchain-postgres",
            "pip install openai"
        ]
    }

    result = "向量存储状态检查\n"
    result += "=" * 40 + "\n"
    for key, value in status.items():
        if isinstance(value, list):
            result += f"{key}:\n"
            for v in value:
                result += f"  - {v}\n"
        else:
            result += f"{key}: {value}\n"

    return result
