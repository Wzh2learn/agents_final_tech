"""
存储提供者 - 防腐层 (ACL)
封装文档存储与数据库操作，支持迁移逻辑与 Schema 校验。
"""
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import os
from storage.document_storage import get_document_storage
from storage.database.document_manager import DocumentManager
from storage.database.db import get_session

logger = logging.getLogger(__name__)

class DocumentMetadata(BaseModel):
    source: str
    object_key: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    size: int = 0
    version: str = "v1"

    @validator('source')
    def validate_source(cls, v):
        allowed_exts = ['.md', '.markdown', '.docx', '.pdf', '.txt']
        ext = os.path.splitext(v)[1].lower()
        if ext not in allowed_exts:
            raise ValueError(f"Unsupported file extension: {ext}. Allowed: {allowed_exts}")
        return v

class StorageProvider:
    """ACL 层：业务模块应调用此 Provider 而非直接操作 S3 或 DB"""
    
    def __init__(self):
        self.doc_storage = get_document_storage()
        self.doc_mgr = DocumentManager()

    def ingest_document(self, file_content: bytes, file_name: str, metadata: Dict[str, Any]) -> str:
        """上传并同步到 DB"""
        # 1. Schema 校验
        meta = DocumentMetadata(source=file_name, size=len(file_content), **metadata)
        
        # 2. 上传对象存储
        object_key = self.doc_storage.upload_document(
            file_content=file_content, 
            file_name=file_name,
            metadata=meta.dict()
        )
        
        # 3. 同步元数据到数据库 (如果需要)
        # 这里可以调用 doc_mgr 的相关方法将元数据持久化
        logger.info(f"Successfully ingested {file_name} with key {object_key}")
        
        return object_key

    def query_document(self, object_key: str) -> Optional[bytes]:
        """优先从新路径读取，支持降级"""
        try:
            # 统一通过 object_key 读取
            return self.doc_storage.download_document(object_key)
        except Exception as e:
            logger.warning(f"Failed to read document for {object_key}: {e}")
            # 降级逻辑：如果是老系统的路径，可以尝试转换路径再次读取
            if not object_key.startswith("documents/"):
                fallback_key = f"documents/{object_key}"
                try:
                    return self.doc_storage.download_document(fallback_key)
                except:
                    pass
            return None

_provider_instance = None

def get_storage_provider() -> StorageProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = StorageProvider()
    return _provider_instance
