"""
知识库 API 路由
"""
import os
import logging
import tempfile
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from biz.rag_service import get_rag_service
from utils.cache import cached, get_cache
from utils.file_validator import validate_upload

router = APIRouter()
logger = logging.getLogger(__name__)


class TraceabilityRequest(BaseModel):
    query: str


class CompareRequest(BaseModel):
    query: str
    methods: dict = {}


@router.get("/stats")
@cached(ttl=60, key_prefix="kb_stats")
async def get_knowledge_stats():
    """获取知识库统计信息（带60秒缓存）"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            stats_data = doc_mgr.get_statistics(db)
            return {"status": "success", "stats": stats_data}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/documents")
async def get_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    limit: Optional[int] = None,
    search: str = ""
):
    """获取文档列表（支持分页和搜索）"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        if limit is not None and limit > 0:
            page_size = limit
            page = 1
        skip = (page - 1) * page_size

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            documents = doc_mgr.get_documents(db=db, skip=skip, limit=page_size, search=search)
            total = len(doc_mgr.get_documents(db=db, skip=0, limit=10000, search=search))

            return {
                "status": "success",
                "documents": documents,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    use_hierarchical: bool = Form(False)
):
    """上传文档"""
    try:
        rag_service = get_rag_service()
        if not file.filename:
            return {"status": "error", "message": "未选择文件"}

        # 读取文件内容
        content = await file.read()

        # 安全验证
        valid, error_msg = validate_upload(file.filename, content)
        if not valid:
            return {"status": "error", "message": error_msg}

        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            ingest_result = await rag_service.ingest_file(
                file_path=tmp_path,
                metadata={"original_name": file.filename},
                use_hierarchical=use_hierarchical
            )
            cache = get_cache()
            cache.delete("kb_stats:get_knowledge_stats:():{}")
            return {
                "status": "success",
                "message": f"成功上传: {file.filename}",
                "object_key": ingest_result["object_key"],
                "chunks_count": ingest_result["chunks"]
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session
        from storage.document_storage import get_document_storage

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            doc_storage = get_document_storage()
            document = doc_mgr.get_document_by_name(db, doc_id)
            if not document:
                return {"status": "error", "message": "文档不存在"}

            chunks = doc_mgr.get_document_chunks(db, doc_id, limit=1)
            if chunks:
                obj_key = chunks[0].get("metadata", {}).get("object_key")
                if obj_key:
                    doc_storage.delete_document(obj_key)

            success = doc_mgr.delete_document(db, doc_id)
            if success:
                get_cache().delete("kb_stats:get_knowledge_stats:():{}")
                return {"status": "success", "message": f"文档 {doc_id} 删除成功"}
            return {"status": "error", "message": "删除失败"}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str):
    """下载文档"""
    import io
    try:
        from storage.provider import get_storage_provider
        provider = get_storage_provider()
        file_content = provider.query_document(doc_id)
        if not file_content:
            return {"status": "error", "message": "文档不存在"}
        content_type = provider.doc_storage._guess_content_type(doc_id)
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={doc_id}"}
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/traceability")
async def traceability_query(request: TraceabilityRequest):
    """答案溯源查询"""
    try:
        rag_service = get_rag_service()
        results = rag_service.get_traceability(request.query)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/compare")
async def compare_methods(request: CompareRequest):
    """对比检索方法"""
    try:
        rag_service = get_rag_service()
        results = rag_service.compare_methods(request.query, request.methods)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/heatmap")
async def get_heatmap():
    """获取知识热力图"""
    try:
        rag_service = get_rag_service()
        data = rag_service.get_heatmap(topic_level=3, min_frequency=1)
        return {"status": "success", "heatmap": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/hierarchy/{doc_id}")
async def get_hierarchy(doc_id: str):
    """获取文档层级结构"""
    try:
        rag_service = get_rag_service()
        data = rag_service.get_hierarchy(doc_id)
        return {"status": "success", "hierarchy": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
