"""
文档管理 Manager
处理文档的增删改查，支持分页和统计
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json
import uuid as uuid_module

from storage.database.shared.model import LangchainPgCollection, LangchainPgEmbedding
from storage.database.db import get_session


# ==================== Pydantic Models ====================

class DocumentInfo(BaseModel):
    """文档信息"""
    id: str
    name: str
    source: str
    size: int
    chunks: int
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(BaseModel):
    """创建文档"""
    name: str = Field(..., description="文档名称")
    source: str = Field(..., description="来源文件路径")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")


class DocumentUpdate(BaseModel):
    """更新文档"""
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentStats(BaseModel):
    """文档统计"""
    total_documents: int
    total_chunks: int
    total_size: int
    collection_count: int


# ==================== Manager Class ====================

class DocumentManager:
    """文档管理 Manager，负责文档的CRUD和统计"""

    def get_documents(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        collection_name: str = "knowledge_base",
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取文档列表（支持分页和搜索）

        Args:
            db: 数据库会话
            skip: 跳过数量（分页偏移）
            limit: 返回数量
            search: 搜索关键词
            collection_name: 集合名称

        Returns:
            文档列表
        """
        # 查询向量集合
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()

        if not collection:
            return []

        # 使用子查询获取文档级别的数据，避免加载所有块到内存
        from sqlalchemy import distinct

        # 统一获取所有唯一 source，再在 Python 中过滤（兼容 search 与 file_type）
        sources = db.query(
            distinct(LangchainPgEmbedding.cmetadata['source'].astext)
        ).filter(
            LangchainPgEmbedding.collection_id == collection.uuid
        ).all()

        # 搜索过滤
        if search:
            search_lower = search.lower()
            sources = [
                (s[0],) for s in sources
                if s[0] and search_lower in s[0].lower()
            ]

        # 文件类型过滤
        if file_type and file_type.lower() != "all":
            normalized = file_type.lower().lstrip(".")
            extensions_map = {
                "doc": [".doc", ".docx"],
                "word": [".doc", ".docx"],
                "md": [".md", ".markdown"],
                "markdown": [".md", ".markdown"],
            }
            extensions = extensions_map.get(normalized, [f".{normalized}"])
            sources = [
                (s[0],) for s in sources
                if s[0] and any(s[0].lower().endswith(ext) for ext in extensions)
            ]

        total = len(sources)
        paginated_sources = sources[skip:skip + limit]

        # 获取每个文档的详细信息
        documents = []
        for (source,) in paginated_sources:
            if not source:
                continue
            
            # 获取该文档的块信息
            chunks_query = db.query(LangchainPgEmbedding).filter(
                LangchainPgEmbedding.collection_id == collection.uuid,
                LangchainPgEmbedding.cmetadata['source'].astext == source
            ).all()
            
            if not chunks_query:
                continue
            
            # 计算总大小
            total_size = sum(len(c.document) if c.document else 0 for c in chunks_query)
            
            # 获取创建时间（从第一个块的metadata）
            created_at = None
            original_filename = None
            if chunks_query[0].cmetadata:
                created_at = chunks_query[0].cmetadata.get('created_at')
                original_filename = chunks_query[0].cmetadata.get('original_name') or chunks_query[0].cmetadata.get('filename')
            
            display_name = original_filename if original_filename else source
            
            doc_info = {
                'id': str(source),
                'name': display_name,
                'original_name': source,
                'size': total_size,
                'chunks': len(chunks_query),
                'created_at': created_at
            }
            documents.append(doc_info)

        return documents

    def count_documents(
        self,
        db: Session,
        search: Optional[str] = None,
        collection_name: str = "knowledge_base",
        file_type: Optional[str] = None
    ) -> int:
        """
        获取文档总数（用于分页）

        Args:
            db: 数据库会话
            search: 搜索关键词
            collection_name: 集合名称

        Returns:
            文档总数
        """
        # 查询向量集合
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()

        if not collection:
            return 0

        # 使用 DISTINCT 统计不同的 source 数量
        from sqlalchemy import distinct
        sources = db.query(distinct(LangchainPgEmbedding.cmetadata['source'].astext)).filter(
            LangchainPgEmbedding.collection_id == collection.uuid
        ).all()

        if search:
            search_lower = search.lower()
            sources = [s for s in sources if s[0] and search_lower in s[0].lower()]

        if file_type and file_type.lower() != "all":
            normalized = file_type.lower().lstrip(".")
            extensions_map = {
                "doc": [".doc", ".docx"],
                "word": [".doc", ".docx"],
                "md": [".md", ".markdown"],
                "markdown": [".md", ".markdown"],
            }
            extensions = extensions_map.get(normalized, [f".{normalized}"])
            sources = [
                s for s in sources
                if s[0] and any(s[0].lower().endswith(ext) for ext in extensions)
            ]

        return len(sources)

    def get_document_by_name(
        self,
        db: Session,
        document_name: str,
        collection_name: str = "knowledge_base"
    ) -> Optional[Dict[str, Any]]:
        """
        根据文档名称获取文档详情

        Args:
            db: 数据库会话
            document_name: 文档名称
            collection_name: 集合名称

        Returns:
            文档详情或None
        """
        documents = self.get_documents(
            db=db,
            skip=0,
            limit=1,
            search=document_name,
            collection_name=collection_name
        )

        return documents[0] if documents else None

    def delete_document(
        self,
        db: Session,
        document_name: str,
        collection_name: str = "knowledge_base"
    ) -> bool:
        """
        删除文档及其所有块

        Args:
            db: 数据库会话
            document_name: 文档名称
            collection_name: 集合名称

        Returns:
            是否删除成功
        """
        # 查询向量集合
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()

        if not collection:
            return False

        # 删除指定文档的所有块
        deleted_count = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid,
            LangchainPgEmbedding.cmetadata['source'].astext == document_name
        ).delete(synchronize_session='fetch')

        db.commit()

        return deleted_count > 0

    def get_document_chunks(
        self,
        db: Session,
        document_name: str,
        collection_name: str = "knowledge_base",
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取文档的所有块

        Args:
            db: 数据库会话
            document_name: 文档名称
            collection_name: 集合名称
            skip: 跳过数量
            limit: 返回数量

        Returns:
            文档块列表
        """
        # 查询向量集合
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()

        if not collection:
            return []

        # 查询文档块
        chunks = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid,
            LangchainPgEmbedding.cmetadata['source'].astext == document_name
        ).order_by(LangchainPgEmbedding.id).offset(skip).limit(limit).all()

        # 转换为字典列表
        chunk_list = []
        for chunk in chunks:
            chunk_info = {
                'id': chunk.id,
                'content': chunk.document,
                'metadata': chunk.cmetadata
            }
            chunk_list.append(chunk_info)

        return chunk_list

    def get_statistics(
        self,
        db: Session,
        collection_name: str = "knowledge_base"
    ) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Args:
            db: 数据库会话
            collection_name: 集合名称

        Returns:
            统计信息
        """
        # 查询向量集合
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()

        if not collection:
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'total_size': 0,
                'average_chunk_size': 0
            }

        # 统计文档数、块数、总大小
        stats = db.query(
            func.count(func.distinct(LangchainPgEmbedding.cmetadata['source'])).label('doc_count'),
            func.count(LangchainPgEmbedding.id).label('chunk_count'),
            func.sum(func.length(LangchainPgEmbedding.document)).label('total_size')
        ).filter(
            LangchainPgEmbedding.collection_id == collection.uuid
        ).first()

        total_documents = stats.doc_count or 0
        total_chunks = stats.chunk_count or 0
        total_size = stats.total_size or 0
        avg_chunk_size = total_size / total_chunks if total_chunks > 0 else 0

        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'total_size': total_size,
            'average_chunk_size': avg_chunk_size
        }

    def search_content(
        self,
        db: Session,
        query: str,
        collection_name: str = "knowledge_base",
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        在文档内容中搜索关键词

        Args:
            db: 数据库会话
            query: 搜索关键词
            collection_name: 集合名称
            skip: 跳过数量
            limit: 返回数量

        Returns:
            匹配的文档块列表
        """
        # 查询向量集合
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()

        if not collection:
            return []

        # 转义 SQL LIKE 特殊字符，避免用户输入的 % 和 _ 被当作通配符
        escaped_query = query.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')

        # 搜索文档内容
        results = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid,
            LangchainPgEmbedding.document.ilike(f'%{escaped_query}%', escape='\\')
        ).order_by(LangchainPgEmbedding.id).offset(skip).limit(limit).all()

        # 转换为字典列表
        chunk_list = []
        for chunk in results:
            chunk_info = {
                'id': chunk.id,
                'content': chunk.document,
                'metadata': chunk.cmetadata
            }
            chunk_list.append(chunk_info)

        return chunk_list

    def collection_exists(self, db: Session, collection_name: str) -> bool:
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()
        return collection is not None

    def create_collection(
        self,
        db: Session,
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.collection_exists(db, collection_name):
            raise ValueError(f"集合已存在: {collection_name}")

        collection = LangchainPgCollection(
            uuid=uuid_module.uuid4(),
            name=collection_name,
            cmetadata=metadata or {}
        )
        db.add(collection)
        db.commit()
        return {"name": collection.name, "uuid": str(collection.uuid)}

    def rename_collection(
        self,
        db: Session,
        old_name: str,
        new_name: str
    ) -> bool:
        if old_name == new_name:
            return True

        old_collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == old_name
        ).first()
        if not old_collection:
            return False

        new_collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == new_name
        ).first()
        if new_collection:
            raise ValueError(f"集合已存在: {new_name}")

        old_collection.name = new_name
        db.commit()
        return True

    def delete_collection(self, db: Session, collection_name: str) -> bool:
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()
        if not collection:
            return False

        db.delete(collection)
        db.commit()
        return True

    def rename_document(
        self,
        db: Session,
        old_name: str,
        new_name: str,
        collection_name: str = "knowledge_base"
    ) -> int:
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()
        if not collection:
            return 0

        chunks = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid,
            LangchainPgEmbedding.cmetadata['source'].astext == old_name
        ).all()

        if not chunks:
            return 0

        for chunk in chunks:
            metadata = dict(chunk.cmetadata or {})
            metadata["source"] = new_name
            metadata["original_name"] = new_name
            metadata["filename"] = new_name
            chunk.cmetadata = metadata

        db.commit()
        return len(chunks)

    def update_chunk_content(
        self,
        db: Session,
        chunk_id: str,
        document_name: str,
        new_content: str,
        collection_name: str = "knowledge_base",
        embedding_vector: Optional[List[float]] = None,
    ) -> Optional[Dict[str, Any]]:
        collection = db.query(LangchainPgCollection).filter(
            LangchainPgCollection.name == collection_name
        ).first()
        if not collection:
            return None

        chunk = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid,
            LangchainPgEmbedding.id == chunk_id,
            LangchainPgEmbedding.cmetadata['source'].astext == document_name
        ).first()
        if not chunk:
            return None

        chunk.document = new_content
        metadata = dict(chunk.cmetadata or {})
        metadata["edited_manually"] = True
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        chunk.cmetadata = metadata

        if embedding_vector is not None:
            chunk.embedding = embedding_vector

        db.commit()
        return {
            "id": chunk.id,
            "document_name": document_name,
            "collection_name": collection_name,
            "content_length": len(new_content),
            "updated_at": metadata["updated_at"],
            "embedding_updated": embedding_vector is not None,
            "metadata": metadata,
        }
