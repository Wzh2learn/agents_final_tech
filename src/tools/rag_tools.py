"""
RAG 核心工具集 (Agent 面向)
这些工具通过 Biz 层的 RAGService 代理实现，为 Agent 提供统一的知识库操作接口。
"""
import json
import logging
from typing import Optional, List, Dict, Any
from langchain.tools import tool
from pydantic import BaseModel, Field, validator
@tool
def add_document_to_knowledge_base(
    file_path: str,
    metadata: Optional[str] = None
) -> str:
    """
    添加文档到知识库 (通过 RAGService 统一处理)
    """
    try:
        import asyncio
        from biz.rag_service import get_rag_service
        validated = AddDocumentInput(file_path=file_path, metadata=metadata)
        meta_dict = json.loads(validated.metadata) if validated.metadata else {}
        
        rag_service = get_rag_service()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(rag_service.ingest_file(validated.file_path, meta_dict))
        
        return f"✅ 文档已成功入库: {file_path}\n对象Key: {res['object_key']}\n分割块数: {res['chunks']}"
    except Exception as e:
        return f"❌ 处理文档失败: {str(e)}"

@tool
def smart_retrieve(
    query: str,
    top_k: Optional[int] = 5
) -> str:
    """
    智能 RAG 检索：根据问题类型自动选择最优检索策略并进行重排序。
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    try:
        from biz.rag_service import get_rag_service
        rag_service = get_rag_service()
        results = rag_service.smart_retrieve(query=query, top_k=top_k)
        
        return json.dumps({
            "query": query,
            "results": results,
            "count": len(results)
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"检索失败: {str(e)}"}, ensure_ascii=False)

@tool
def batch_retrieve(queries: str, top_k: Optional[int] = 5) -> str:
    """批量对多个问题执行智能检索。"""
    try:
        from biz.rag_service import get_rag_service
        query_list = json.loads(queries)
        rag_service = get_rag_service()
        result = rag_service.batch_retrieve(query_list, top_k)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"批量检索失败: {str(e)}"}, ensure_ascii=False)

@tool
def get_retrieval_statistics(queries: str) -> str:
    """分析多条查询的检索效果统计。"""
    try:
        from biz.rag_service import get_rag_service
        query_list = json.loads(queries)
        rag_service = get_rag_service()
        result = rag_service.get_statistics(query_list)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"统计失败: {str(e)}"}, ensure_ascii=False)

@tool
def delete_documents_from_knowledge_base(source: str) -> str:
    """从知识库中删除指定来源的文档。"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session
        doc_mgr = DocumentManager()
        db = get_session()
        success = doc_mgr.delete_document(db, source)
        db.close()
        return f"✅ 文档 {source} 删除{'成功' if success else '失败'}"
    except Exception as e:
        return f"❌ 删除失败: {str(e)}"
