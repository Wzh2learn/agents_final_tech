"""
文档管理 Manager
处理文档的增删改查，支持分页和统计
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json

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
        collection_name: str = "knowledge_base"
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

        # 查询文档块（避免对JSONB使用max函数）
        query = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid
        )

        # 获取所有结果
        all_results = query.all()

        # 在Python中进行分组和聚合
        from collections import defaultdict
        doc_groups = defaultdict(lambda: {
            'chunks': [],
            'total_size': 0
        })

        for result in all_results:
            source = result.cmetadata.get('source', 'unknown')
            doc_groups[source]['chunks'].append(result)
            doc_groups[source]['total_size'] += len(result.document) if result.document else 0

        # 转换为文档列表
        documents = []
        for source, data in doc_groups.items():
            chunks = data['chunks']
            # 获取创建时间（从第一个块的metadata）
            created_at = None
            if chunks and chunks[0].cmetadata:
                created_at = chunks[0].cmetadata.get('created_at')

            doc_info = {
                'id': str(source),
                'name': source,
                'size': data['total_size'],
                'chunks': len(chunks),
                'created_at': created_at
            }
            documents.append(doc_info)

        # 搜索过滤（在Python中执行）
        if search:
            search_lower = search.lower()
            documents = [doc for doc in documents if search_lower in doc['name'].lower()]

        # 按创建时间排序（降序）
        documents.sort(key=lambda x: x['created_at'] or '', reverse=True)

        # 分页
        total = len(documents)
        documents = documents[skip:skip + limit]

        return documents

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
            LangchainPgEmbedding.cmetadata['source'] == document_name
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
            LangchainPgEmbedding.cmetadata['source'] == document_name
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

        # 搜索文档内容
        results = db.query(LangchainPgEmbedding).filter(
            LangchainPgEmbedding.collection_id == collection.uuid,
            LangchainPgEmbedding.document.ilike(f'%{query}%')
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
