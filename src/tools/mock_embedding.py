"""
模拟 Embedding 实现（仅用于测试）
生产环境需要配置真实的 Embedding API
"""
import os
from typing import List
from langchain_core.embeddings import Embeddings
import hashlib


class MockEmbeddings(Embeddings):
    """
    模拟 Embeddings 实现

    使用文本哈希生成固定向量，用于测试向量存储功能
    生产环境应替换为真实的 Embedding API（如豆包Embedding）
    """

    def __init__(self, model: str = "mock-embedding", dimension: int = 1536):
        """
        初始化模拟Embedding

        Args:
            model: 模型名称（仅用于标识）
            dimension: 向量维度
        """
        self.model = model
        self.dimension = dimension

    def _text_to_vector(self, text: str) -> List[float]:
        """
        将文本转换为模拟向量

        使用文本哈希生成固定向量，确保相同文本产生相同向量

        Args:
            text: 输入文本

        Returns:
            模拟向量
        """
        # 计算文本的MD5哈希
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        # 将哈希转换为数字
        hash_int = int(text_hash, 16)

        # 生成固定维度的向量
        vector = []
        for i in range(self.dimension):
            # 使用伪随机算法生成向量值
            seed = (hash_int + i) % (2 ** 32)
            value = ((seed % 10000) - 5000) / 10000.0  # 归一化到[-0.5, 0.5]
            vector.append(value)

        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入多个文本

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return [self._text_to_vector(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单个查询

        Args:
            text: 查询文本

        Returns:
            向量
        """
        return self._text_to_vector(text)


def get_mock_embeddings(dimension: int = 1536) -> MockEmbeddings:
    """
    获取模拟Embeddings实例

    Args:
        dimension: 向量维度（默认1536，与OpenAI兼容）

    Returns:
        MockEmbeddings 实例
    """
    return MockEmbeddings(dimension=dimension)


# 检查是否使用真实Embedding
USE_REAL_EMBEDDING = os.getenv("USE_REAL_EMBEDDING", "false").lower() == "true"


def get_embeddings():
    """
    获取Embeddings实例

    根据环境变量决定使用真实Embedding还是模拟Embedding

    Returns:
        Embeddings 实例
    """
    if USE_REAL_EMBEDDING:
        # 尝试使用真实Embedding（豆包）
        try:
            from .vector_store import get_embeddings as get_real_embeddings
            return get_real_embeddings()
        except Exception as e:
            print(f"警告: 无法加载真实Embedding ({e})，使用模拟Embedding")
            return get_mock_embeddings()
    else:
        # 默认使用模拟Embedding
        print("注意: 使用模拟Embedding（仅用于测试）")
        print("      生产环境请设置 USE_REAL_EMBEDDING=true 并配置真实的Embedding API")
        return get_mock_embeddings()
