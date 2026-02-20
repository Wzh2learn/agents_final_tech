"""
Knowledge base API routes.
"""

import logging
import os
import re
import tempfile
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from biz.rag_service import get_rag_service, get_runtime_rag_settings, set_runtime_rag_settings
from utils.cache import cached, get_cache
from utils.file_validator import validate_upload

router = APIRouter()
logger = logging.getLogger(__name__)
_COLLECTION_NAME_PATTERN = re.compile(r"^[\w\-\u4e00-\u9fff]{1,64}$")


class TraceabilityRequest(BaseModel):
    query: str
    collection_name: Optional[str] = None


class CompareRequest(BaseModel):
    query: str
    methods: Dict[str, bool] = {}
    collection_name: Optional[str] = None


class RagSettingsRequest(BaseModel):
    top_k: Optional[int] = None
    max_results: Optional[int] = None
    use_rerank: Optional[bool] = None
    rerank_top_n: Optional[int] = None


class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class CollectionRenameRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=64)


class DocumentRenameRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=255)


class ChunkUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    update_embedding: bool = True


class CollectionSettings(BaseModel):
    collection_name: str
    chunk_mode: str = "parent_child"
    index_mode: str = "high_quality"
    retrieval_mode: str = "hybrid"
    top_k: int = 5
    use_rerank: bool = True
    rerank_top_n: int = 5
    chunk_settings: dict = {}
    updated_at: Optional[str] = None


_collection_settings_cache: Dict[str, Dict[str, Any]] = {}


def _default_collection_settings(collection_name: str) -> Dict[str, Any]:
    return {
        "collection_name": collection_name,
        "chunk_mode": "parent_child",
        "index_mode": "high_quality",
        "retrieval_mode": "hybrid",
        "top_k": 5,
        "use_rerank": True,
        "rerank_top_n": 5,
        "chunk_settings": {
            "parent_chunk_size": 2000,
            "child_chunk_size": 500,
            "chunk_overlap": 100,
        },
    }


def _validate_collection_name(name: str, strict: bool = True) -> str:
    normalized = (name or "").strip()
    if not normalized:
        raise ValueError("知识库名称不能为空")
    if len(normalized) > 128:
        raise ValueError("知识库名称长度不能超过 128")
    if strict and not _COLLECTION_NAME_PATTERN.match(normalized):
        raise ValueError("知识库名称仅支持中文、字母、数字、下划线和中划线，长度 1-64")
    return normalized


def _invalidate_kb_cache(collection_name: Optional[str] = None) -> None:
    cache = get_cache()
    cache.clear()
    try:
        from tools.bm25_retriever import clear_bm25_cache

        if collection_name:
            clear_bm25_cache.invoke({"collection_name": collection_name})
        else:
            clear_bm25_cache.invoke({})
    except Exception as error:
        logger.warning(f"清理 BM25 缓存失败: {error}")


@router.get("/stats")
@cached(ttl=60, key_prefix="kb_stats")
async def get_knowledge_stats(collection_name: str = "knowledge_base"):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            stats_data = doc_mgr.get_statistics(db, collection_name=collection_name)
            return {"status": "success", "stats": stats_data}
        finally:
            db.close()
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.get("/documents")
async def get_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    limit: Optional[int] = None,
    search: str = "",
    collection_name: str = "knowledge_base",
    file_type: Optional[str] = None,
):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

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
                file_type=file_type,
            )
            total = doc_mgr.count_documents(
                db=db,
                search=search,
                collection_name=collection_name,
                file_type=file_type,
            )
            return {
                "status": "success",
                "documents": documents,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size,
                },
            }
        finally:
            db.close()
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.get("/collections")
async def list_collections():
    try:
        import asyncio

        rag_service = await get_rag_service()
        try:
            collections = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, rag_service.get_collection_names),
                timeout=5.0,
            )
            return {"status": "success", "collections": collections}
        except asyncio.TimeoutError:
            logger.error("获取知识库列表超时，返回默认集合")
            return {"status": "success", "collections": ["knowledge_base"]}
    except Exception as error:
        logger.error(f"获取知识库列表失败: {error}")
        return {"status": "error", "message": str(error), "collections": []}


@router.post("/collections")
async def create_collection(payload: CollectionCreateRequest):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        collection_name = _validate_collection_name(payload.name, strict=True)
        db = get_session()
        try:
            doc_mgr = DocumentManager()
            created = doc_mgr.create_collection(db, collection_name=collection_name)
        finally:
            db.close()

        _collection_settings_cache.setdefault(collection_name, _default_collection_settings(collection_name))
        _invalidate_kb_cache(collection_name)
        return {
            "status": "success",
            "message": f"知识库 {collection_name} 创建成功",
            "collection": created,
        }
    except ValueError as error:
        return {"status": "error", "message": str(error)}
    except Exception as error:
        logger.error(f"Create collection failed: {error}")
        return {"status": "error", "message": str(error)}


@router.patch("/collections/{collection_name}")
async def rename_collection(collection_name: str, payload: CollectionRenameRequest):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        old_name = _validate_collection_name(collection_name, strict=False)
        new_name = _validate_collection_name(payload.new_name, strict=True)

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            renamed = doc_mgr.rename_collection(db, old_name=old_name, new_name=new_name)
        finally:
            db.close()

        if not renamed:
            return {"status": "error", "message": f"知识库不存在: {old_name}"}

        if old_name in _collection_settings_cache:
            settings = dict(_collection_settings_cache.pop(old_name))
            settings["collection_name"] = new_name
            _collection_settings_cache[new_name] = settings

        _invalidate_kb_cache()
        return {
            "status": "success",
            "message": f"知识库已重命名为 {new_name}",
            "old_name": old_name,
            "new_name": new_name,
        }
    except ValueError as error:
        return {"status": "error", "message": str(error)}
    except Exception as error:
        logger.error(f"Rename collection failed: {error}")
        return {"status": "error", "message": str(error)}


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str, delete_documents: bool = Query(True)):
    try:
        from sqlalchemy import func
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager
        from storage.database.shared.model import LangchainPgCollection, LangchainPgEmbedding
        from storage.document_storage import get_document_storage

        target_name = _validate_collection_name(collection_name, strict=False)
        object_keys = set()
        db = get_session()
        try:
            collection = db.query(LangchainPgCollection).filter(
                LangchainPgCollection.name == target_name
            ).first()
            if not collection:
                return {"status": "error", "message": f"知识库不存在: {target_name}"}

            chunk_count = db.query(func.count(LangchainPgEmbedding.id)).filter(
                LangchainPgEmbedding.collection_id == collection.uuid
            ).scalar() or 0
            if chunk_count > 0 and not delete_documents:
                return {"status": "error", "message": "知识库内仍有文档，请确认删除文档后重试"}

            if delete_documents and chunk_count > 0:
                metadata_rows = db.query(LangchainPgEmbedding.cmetadata).filter(
                    LangchainPgEmbedding.collection_id == collection.uuid
                ).all()
                for row in metadata_rows:
                    metadata = row[0] if isinstance(row, tuple) else row
                    if isinstance(metadata, dict) and metadata.get("object_key"):
                        object_keys.add(metadata["object_key"])

            doc_mgr = DocumentManager()
            deleted = doc_mgr.delete_collection(db, collection_name=target_name)
        finally:
            db.close()

        if not deleted:
            return {"status": "error", "message": f"知识库不存在: {target_name}"}

        if object_keys:
            storage = get_document_storage()
            for object_key in object_keys:
                try:
                    storage.delete_document(object_key)
                except Exception as error:
                    logger.warning(f"删除对象存储文件失败 {object_key}: {error}")

        _collection_settings_cache.pop(target_name, None)
        _invalidate_kb_cache()
        return {"status": "success", "message": f"知识库 {target_name} 删除成功"}
    except ValueError as error:
        return {"status": "error", "message": str(error)}
    except Exception as error:
        logger.error(f"Delete collection failed: {error}")
        return {"status": "error", "message": str(error)}


@router.get("/rag-settings")
async def get_rag_settings():
    try:
        return {"status": "success", "settings": get_runtime_rag_settings()}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.post("/rag-settings")
async def update_rag_settings(payload: RagSettingsRequest):
    try:
        settings = set_runtime_rag_settings(payload.model_dump(exclude_none=True))
        return {"status": "success", "settings": settings}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    use_hierarchical: bool = Form(False),
    collection_name: str = Form("knowledge_base"),
):
    try:
        rag_service = await get_rag_service()
        if not file.filename:
            return {"status": "error", "message": "未选择文件"}

        content = await file.read()
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
                collection_name=collection_name,
            )
            _invalidate_kb_cache(collection_name)
            return {
                "status": "success",
                "message": f"上传成功: {file.filename}",
                "object_key": ingest_result["object_key"],
                "chunks_count": ingest_result["chunks"],
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as error:
        logger.error(f"Upload failed: {error}")
        return {"status": "error", "message": str(error)}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, collection_name: str = Query("knowledge_base")):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager
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
                obj_key = (chunks[0].get("metadata") or {}).get("object_key")
                if obj_key:
                    doc_storage.delete_document(obj_key)

            success = doc_mgr.delete_document(db, doc_id, collection_name=collection_name)
            if success:
                _invalidate_kb_cache(collection_name)
                return {"status": "success", "message": f"文档 {doc_id} 删除成功"}
            return {"status": "error", "message": "删除失败"}
        finally:
            db.close()
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.patch("/documents/{doc_id}")
async def rename_document(
    doc_id: str,
    payload: DocumentRenameRequest,
    collection_name: str = Query("knowledge_base"),
):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        new_name = (payload.new_name or "").strip()
        if not new_name:
            return {"status": "error", "message": "新文档名不能为空"}
        if "/" in new_name or "\\" in new_name:
            return {"status": "error", "message": "文档名不能包含路径分隔符"}

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            exists = doc_mgr.get_document_by_name(db, new_name, collection_name=collection_name)
            if exists:
                return {"status": "error", "message": f"同名文档已存在: {new_name}"}

            renamed_count = doc_mgr.rename_document(
                db,
                old_name=doc_id,
                new_name=new_name,
                collection_name=collection_name,
            )
        finally:
            db.close()

        if renamed_count <= 0:
            return {"status": "error", "message": f"文档不存在: {doc_id}"}

        _invalidate_kb_cache(collection_name)
        return {
            "status": "success",
            "message": f"文档已重命名为 {new_name}",
            "old_name": doc_id,
            "new_name": new_name,
        }
    except Exception as error:
        logger.error(f"Rename document failed: {error}")
        return {"status": "error", "message": str(error)}


@router.patch("/documents/{doc_id}/chunks/{chunk_id}")
async def update_document_chunk(
    doc_id: str,
    chunk_id: str,
    payload: ChunkUpdateRequest,
    collection_name: str = Query("knowledge_base"),
):
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        new_content = payload.content or ""
        if not new_content.strip():
            return {"status": "error", "message": "分段内容不能为空"}

        embedding_vector = None
        embedding_warning = None
        if payload.update_embedding:
            try:
                from tools.vector_store import get_embeddings

                embeddings = get_embeddings()
                embedding_vector = embeddings.embed_query(new_content)
            except Exception as error:
                embedding_warning = f"向量更新失败，已仅保存文本内容: {error}"
                logger.warning(
                    "Update chunk embedding failed for %s/%s/%s: %s",
                    collection_name,
                    doc_id,
                    chunk_id,
                    error,
                )

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            updated = doc_mgr.update_chunk_content(
                db=db,
                chunk_id=chunk_id,
                document_name=doc_id,
                new_content=new_content,
                collection_name=collection_name,
                embedding_vector=embedding_vector,
            )
        finally:
            db.close()

        if not updated:
            return {"status": "error", "message": "未找到对应分段或文档"}

        _invalidate_kb_cache(collection_name)
        response = {
            "status": "success",
            "message": "分段内容已更新",
            "chunk": updated,
        }
        if embedding_warning:
            response["warning"] = embedding_warning
        return response
    except Exception as error:
        logger.error(f"Update chunk content failed: {error}")
        return {"status": "error", "message": str(error)}


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, collection_name: str = Query("knowledge_base")):
    import io

    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager
        from storage.provider import get_storage_provider

        provider = get_storage_provider()
        object_key = doc_id

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            chunks = doc_mgr.get_document_chunks(db, doc_id, collection_name=collection_name, limit=1)
            if chunks:
                metadata = chunks[0].get("metadata") or {}
                if metadata.get("object_key"):
                    object_key = metadata["object_key"]
        finally:
            db.close()

        file_content = provider.query_document(object_key)
        if not file_content:
            return {"status": "error", "message": "文档不存在"}

        content_type = provider.doc_storage._guess_content_type(object_key)
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={doc_id}"},
        )
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.get("/documents/{doc_id}/export-docx")
async def export_document_docx(doc_id: str, collection_name: str = Query("knowledge_base")):
    import io

    try:
        from docx import Document
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

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
                headers={"Content-Disposition": f"attachment; filename={file_name}"},
            )
        finally:
            db.close()
    except Exception as error:
        logger.error(f"Export docx failed: {error}")
        return {"status": "error", "message": str(error)}


@router.post("/traceability")
async def traceability_query(request: TraceabilityRequest):
    try:
        rag_service = await get_rag_service()
        results = rag_service.get_traceability(request.query, request.collection_name)
        return {"status": "success", "results": results}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.post("/compare")
async def compare_methods(request: CompareRequest):
    try:
        rag_service = await get_rag_service()
        results = rag_service.compare_methods(request.query, request.methods, request.collection_name)
        return {"status": "success", "results": results}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.get("/heatmap")
async def get_heatmap():
    try:
        rag_service = await get_rag_service()
        data = rag_service.get_heatmap(topic_level=3, min_frequency=1)
        return {"status": "success", "heatmap": data}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.get("/hierarchy/{doc_id}")
async def get_hierarchy(doc_id: str, collection_name: str = Query("knowledge_base")):
    try:
        rag_service = await get_rag_service()
        data = rag_service.get_hierarchy(doc_id, collection_name=collection_name)
        return {"status": "success", "hierarchy": data}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@router.post("/collection-settings")
async def save_collection_settings(settings: CollectionSettings):
    try:
        collection_name = settings.collection_name
        _collection_settings_cache[collection_name] = settings.dict()

        runtime_settings = {
            "top_k": settings.top_k,
            "use_rerank": settings.use_rerank,
            "rerank_top_n": settings.rerank_top_n,
        }
        set_runtime_rag_settings(runtime_settings)

        return {
            "status": "success",
            "message": "知识库设置已保存",
            "settings": _collection_settings_cache[collection_name],
        }
    except Exception as error:
        logger.error(f"保存知识库设置失败: {error}")
        return {"status": "error", "message": str(error)}


@router.get("/collection-settings")
async def get_collection_settings(collection_name: str = "knowledge_base"):
    try:
        settings = _collection_settings_cache.get(collection_name)
        if settings is None:
            settings = _default_collection_settings(collection_name)
            settings["is_default"] = True
        return {"status": "success", "settings": settings}
    except Exception as error:
        logger.error(f"获取知识库设置失败: {error}")
        return {"status": "error", "message": str(error)}
