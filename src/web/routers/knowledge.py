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

from biz.rag_service import get_rag_service, get_runtime_rag_settings, set_runtime_rag_settings
from utils.cache import cached, get_cache
from utils.file_validator import validate_upload

router = APIRouter()
logger = logging.getLogger(__name__)


class TraceabilityRequest(BaseModel):
    query: str
    collection_name: Optional[str] = None


class CompareRequest(BaseModel):
    query: str
    methods: dict = {}
    collection_name: Optional[str] = None


class RagSettingsRequest(BaseModel):
    top_k: Optional[int] = None
    max_results: Optional[int] = None
    use_rerank: Optional[bool] = None
    rerank_top_n: Optional[int] = None


@router.get("/stats")
@cached(ttl=60, key_prefix="kb_stats")
async def get_knowledge_stats(collection_name: str = "knowledge_base"):
    """获取知识库统计信息（带60秒缓存）"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            stats_data = doc_mgr.get_statistics(db, collection_name=collection_name)
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
    search: str = "",
    collection_name: str = "knowledge_base",
    file_type: Optional[str] = None
):
    """获取文档列表（支持分页、搜索和集合切换）"""
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
            documents = doc_mgr.get_documents(
                db=db,
                skip=skip,
                limit=page_size,
                search=search,
                collection_name=collection_name,
                file_type=file_type
            )
            # 使用 count_documents 获取总数，避免查询全部数据
            total = doc_mgr.count_documents(
                db=db,
                search=search,
                collection_name=collection_name,
                file_type=file_type
            )

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


@router.get("/collections")
async def list_collections():
    """获取所有知识库集合列表"""
    try:
        from biz.rag_service import get_rag_service
        rag_service = await get_rag_service()
        collections = rag_service.get_collection_names()
        return {"status": "success", "collections": collections}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/rag-settings")
async def get_rag_settings():
    """获取运行时 RAG 设置（用于 UI 控制 top_k/rerank 等）"""
    try:
        return {"status": "success", "settings": get_runtime_rag_settings()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/rag-settings")
async def update_rag_settings(payload: RagSettingsRequest):
    """更新运行时 RAG 设置（内存/Redis 缓存，重启会丢失）"""
    try:
        settings = set_runtime_rag_settings(payload.model_dump(exclude_none=True))
        return {"status": "success", "settings": settings}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    use_hierarchical: bool = Form(False),
    collection_name: str = Form("knowledge_base")
):
    """上传文档"""
    try:
        rag_service = await get_rag_service()
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
                use_hierarchical=use_hierarchical,
                collection_name=collection_name
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
async def delete_document(doc_id: str, collection_name: str = Query("knowledge_base")):
    """删除文档"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session
        from storage.document_storage import get_document_storage

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            doc_storage = get_document_storage()
            document = doc_mgr.get_document_by_name(db, doc_id, collection_name=collection_name)
            if not document:
                return {"status": "error", "message": "文档不存在"}

            chunks = doc_mgr.get_document_chunks(db, doc_id, collection_name=collection_name, limit=1)
            if chunks:
                obj_key = chunks[0].get("metadata", {}).get("object_key")
                if obj_key:
                    doc_storage.delete_document(obj_key)

            success = doc_mgr.delete_document(db, doc_id, collection_name=collection_name)
            if success:
                get_cache().delete("kb_stats:get_knowledge_stats:():{}")
                return {"status": "success", "message": f"文档 {doc_id} 删除成功"}
            return {"status": "error", "message": "删除失败"}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, collection_name: str = Query("knowledge_base")):
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


@router.get("/documents/{doc_id}/export-docx")
async def export_document_docx(doc_id: str, collection_name: str = Query("knowledge_base")):
    """导出文档为 DOCX（基于分段内容生成）"""
    import io
    try:
        from docx import Document
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            chunks = doc_mgr.get_document_chunks(db, doc_id, collection_name=collection_name, limit=10000)
            if not chunks:
                return {"status": "error", "message": "文档不存在"}

            document = Document()
            document.add_heading(doc_id, level=1)
            for chunk in chunks:
                content = chunk.get("content") or ""
                if content:
                    document.add_paragraph(content)

            buffer = io.BytesIO()
            document.save(buffer)
            buffer.seek(0)

            file_name = f"{os.path.splitext(doc_id)[0]}.docx"
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={file_name}"}
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Export docx failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/traceability")
async def traceability_query(request: TraceabilityRequest):
    """答案溯源查询"""
    try:
        rag_service = await get_rag_service()
        results = rag_service.get_traceability(request.query, request.collection_name)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/compare")
async def compare_methods(request: CompareRequest):
    """对比检索方法"""
    try:
        rag_service = await get_rag_service()
        results = rag_service.compare_methods(request.query, request.methods, request.collection_name)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/heatmap")
async def get_heatmap():
    """获取知识热力图"""
    try:
        rag_service = await get_rag_service()
        data = rag_service.get_heatmap(topic_level=3, min_frequency=1)
        return {"status": "success", "heatmap": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/hierarchy/{doc_id}")
async def get_hierarchy(doc_id: str, collection_name: str = Query("knowledge_base")):
    """获取文档层级结构"""
    try:
        rag_service = await get_rag_service()
        data = rag_service.get_hierarchy(doc_id, collection_name=collection_name)
        return {"status": "success", "hierarchy": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
