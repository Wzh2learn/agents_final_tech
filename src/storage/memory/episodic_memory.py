"""
情景记忆存储层 (Episodic Memory)
负责将历史对话片段向量化并存入 PGVector，支持基于相似度的召回。
类比推荐系统中的长期兴趣特征存储。
"""
import logging
import json
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from tools.vector_store import get_vector_store

logger = logging.getLogger(__name__)

class EpisodicMemoryProvider:
    def __init__(self, collection_name: str = "episodic_memory"):
        self.collection_name = collection_name
        self._vector_store = None

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_vector_store(collection_name=self.collection_name)
        return self._vector_store

    async def add_memory(self, session_id: str, content: str, metadata: Dict[str, Any] = None):
        """添加一条记忆片段"""
        try:
            doc_metadata = {
                "session_id": session_id,
                "type": "episodic",
                **(metadata or {})
            }
            doc = Document(page_content=content, metadata=doc_metadata)
            self.vector_store.add_documents([doc])
            logger.info(f"Added episodic memory for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to add episodic memory: {e}")

    async def search_memory(self, query: str, session_id: str, top_k: int = 5) -> List[Document]:
        """检索相关记忆片段 (Target Attention 召回)"""
        try:
            # 基础召回：基于向量相似度
            # 在论文中，这里可以进一步实现更复杂的 Attention 计算
            filter_dict = {"session_id": session_id}
            results = self.vector_store.similarity_search(query, k=top_k, filter=filter_dict)
            
            # 兼容性回退：如果 PGVector filter 不生效，手动过滤
            if results and any(m.get("session_id") != session_id for m in [r.metadata for r in results]):
                results = [r for r in results if r.metadata.get("session_id") == session_id]
                results = results[:top_k]
                
            return results
        except Exception as e:
            logger.error(f"Failed to search episodic memory: {e}")
            return []

_episodic_provider = None

def get_episodic_memory_provider() -> EpisodicMemoryProvider:
    global _episodic_provider
    if _episodic_provider is None:
        _episodic_provider = EpisodicMemoryProvider()
    return _episodic_provider
