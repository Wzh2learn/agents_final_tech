"""
配置加载器
统一管理配置文件的加载和访问
"""
import os
import json
from typing import Any, Optional, Dict
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Find project root (3 levels up from src/utils/config_loader.py)
    base_dir = Path(__file__).resolve().parent.parent.parent
    env_path = base_dir / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv() # Fallback to default search
except ImportError:
    pass


class AppConfig:
    """应用配置类"""

    _instance = None
    _config_data: Dict[str, Any] = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置加载器"""
        if self._config_data is None:
            self.load_config()

    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径（可选，默认使用 app_config.json）
        """
        if config_path is None:
            # 优先尝试相对于 src/utils/config_loader.py 的路径
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "config" / "app_config.json"
            
            if not config_path.exists():
                # 降级尝试环境变量或默认路径
                workspace_path = os.getenv("WORKSPACE_PATH", "/workspace/projects")
                config_path = Path(workspace_path) / "config" / "app_config.json"

        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            self._config_data = json.load(f)

        print(f"✓ 配置文件加载成功: {config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（优先从环境变量获取，然后从配置文件获取）
        支持嵌套key，使用点号分隔
        """
        # 1. 尝试从环境变量获取 (将点号替换为下划线并转大写)
        env_key = key.replace('.', '_').upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        if self._config_data is None:
            return default

        # 2. 从配置文件获取
        keys = key.split('.')
        value = self._config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置节

        Args:
            section: 配置节名称（如 "database", "llm"）

        Returns:
            配置节字典

        Examples:
            >>> config = AppConfig()
            >>> db_config = config.get_section("database")
            >>> print(db_config["host"])
            "localhost"
        """
        return self.get(section, {})

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get_section("database")

    def get_vector_store_config(self) -> Dict[str, Any]:
        """获取向量存储配置"""
        return self.get_section("vector_store")

    def get_embedding_config(self) -> Dict[str, Any]:
        """获取Embedding配置"""
        return self.get_section("embedding")

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.get_section("llm")

    def get_rerank_config(self) -> Dict[str, Any]:
        """获取Rerank配置"""
        return self.get_section("rerank")

    def get_rag_config(self) -> Dict[str, Any]:
        """获取RAG配置"""
        return self.get_section("rag")

    def get_bm25_config(self) -> Dict[str, Any]:
        """获取BM25配置"""
        return self.get_section("bm25")

    def get_document_processing_config(self) -> Dict[str, Any]:
        """获取文档处理配置"""
        return self.get_section("document_processing")

    def get_web_config(self) -> Dict[str, Any]:
        """获取Web服务配置"""
        return self.get_section("web")

    def get_websocket_config(self) -> Dict[str, Any]:
        """获取WebSocket配置"""
        return self.get_section("websocket")

    def get_collaboration_config(self) -> Dict[str, Any]:
        """获取协作会话配置"""
        return self.get_section("collaboration")

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get_section("storage")

    def get_memory_config(self) -> Dict[str, Any]:
        """获取记忆配置"""
        return self.get_section("memory")

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get_section("logging")

    def get_features_config(self) -> Dict[str, Any]:
        """获取功能开关配置"""
        return self.get_section("features")

    def is_enabled(self, feature: str) -> bool:
        """
        检查功能是否启用

        Args:
            feature: 功能名称（如 "role_selection", "smart_routing"）

        Returns:
            是否启用

        Examples:
            >>> config = AppConfig()
            >>> config.is_enabled("rerank")
            True
        """
        features = self.get_section("features")
        return features.get(feature, False)

    def reload(self) -> None:
        """重新加载配置文件"""
        self.load_config()

    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径（可选，默认使用原路径）
        """
        if config_path is None:
            workspace_path = os.getenv("WORKSPACE_PATH", "/workspace/projects")
            config_path = os.path.join(workspace_path, "config/app_config.json")

        config_file = Path(config_path)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config_data, f, indent=2, ensure_ascii=False)

        print(f"✓ 配置文件保存成功: {config_path}")

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值（支持嵌套key）

        Args:
            key: 配置键（支持嵌套，如 "database.port"）
            value: 配置值

        Examples:
            >>> config = AppConfig()
            >>> config.set("database.port", 5433)
            >>> config.get("database.port")
            5433
        """
        keys = key.split('.')
        config = self._config_data

        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        返回完整配置字典

        Returns:
            配置字典
        """
        return self._config_data.copy() if self._config_data else {}


# 全局配置实例
_app_config = None


def get_config() -> AppConfig:
    """
    获取全局配置实例

    Returns:
        AppConfig 实例
    """
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config


# 便捷函数
def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return get_config().get_database_config()


def get_vector_store_config() -> Dict[str, Any]:
    """获取向量存储配置"""
    return get_config().get_vector_store_config()


def get_embedding_config() -> Dict[str, Any]:
    """获取Embedding配置"""
    return get_config().get_embedding_config()


def get_llm_config() -> Dict[str, Any]:
    """获取LLM配置"""
    return get_config().get_llm_config()


def get_rerank_config() -> Dict[str, Any]:
    """获取Rerank配置"""
    return get_config().get_rerank_config()


def get_rag_config() -> Dict[str, Any]:
    """获取RAG配置"""
    return get_config().get_rag_config()


def get_bm25_config() -> Dict[str, Any]:
    """获取BM25配置"""
    return get_config().get_bm25_config()


def get_document_processing_config() -> Dict[str, Any]:
    """获取文档处理配置"""
    return get_config().get_document_processing_config()


def get_web_config() -> Dict[str, Any]:
    """获取Web服务配置"""
    return get_config().get_web_config()


def get_websocket_config() -> Dict[str, Any]:
    """获取WebSocket配置"""
    return get_config().get_websocket_config()


def get_collaboration_config() -> Dict[str, Any]:
    """获取协作会话配置"""
    return get_config().get_collaboration_config()


def get_storage_config() -> Dict[str, Any]:
    """获取存储配置"""
    return get_config().get_storage_config()


def get_memory_config() -> Dict[str, Any]:
    """获取记忆配置"""
    return get_config().get_memory_config()


def is_feature_enabled(feature: str) -> bool:
    """
    检查功能是否启用

    Args:
        feature: 功能名称

    Returns:
        是否启用
    """
    return get_config().is_enabled(feature)


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()

    print("=" * 60)
    print("配置加载测试")
    print("=" * 60)

    print("\n数据库配置:")
    print(json.dumps(config.get_database_config(), indent=2, ensure_ascii=False))

    print("\nLLM配置:")
    print(json.dumps(config.get_llm_config(), indent=2, ensure_ascii=False))

    print("\nRAG配置:")
    print(json.dumps(config.get_rag_config(), indent=2, ensure_ascii=False))

    print("\n功能状态:")
    features = config.get_features_config()
    for feature, enabled in features.items():
        status = "✓ 启用" if enabled else "✗ 禁用"
        print(f"  {feature}: {status}")

    print("\n配置获取测试:")
    print(f"  database.host: {config.get('database.host')}")
    print(f"  database.port: {config.get('database.port')}")
    print(f"  llm.model: {config.get('llm.model')}")
    print(f"  rag.default_top_k: {config.get('rag.default_top_k')}")

    print("\n" + "=" * 60)
