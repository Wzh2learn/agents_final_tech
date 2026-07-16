"""Read-only MCP tools backed by the existing RAG service."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from biz.rag_service import get_rag_service_sync
from storage.database.db import get_session
from storage.database.document_manager import DocumentManager


mcp = FastMCP(
    "JinRongAgents Knowledge",
    instructions=(
        "Use these read-only tools for M1/M2 knowledge retrieval. "
        "Always preserve returned source and business identifiers."
    ),
)


def search_knowledge(
    query: str,
    collection_names: Optional[List[str]] = None,
    top_k: int = 5,
    max_results: int = 10,
    use_rerank: bool = True,
) -> Dict[str, Any]:
    """Run the existing hybrid retrieval pipeline and return traceable evidence."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("query must not be empty")
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    if not 1 <= max_results <= 50:
        raise ValueError("max_results must be between 1 and 50")

    service = get_rag_service_sync()
    results = service.smart_retrieve(
        query=clean_query,
        collection_names=collection_names,
        top_k=top_k,
        max_results=max_results,
        use_rerank=use_rerank,
    )
    return {
        "status": "success",
        "query": clean_query,
        "count": len(results),
        "results": results,
    }


def list_knowledge_collections() -> Dict[str, Any]:
    """List collections already managed by JinRongAgents."""
    collections = get_rag_service_sync().get_collection_names()
    return {
        "status": "success",
        "count": len(collections),
        "collections": collections,
    }


def get_knowledge_source(
    document_id: str,
    collection_name: str = "knowledge_base",
    max_chunks: int = 20,
) -> Dict[str, Any]:
    """Return source chunks for a document without bypassing the document manager."""
    clean_document_id = document_id.strip()
    clean_collection = collection_name.strip()
    if not clean_document_id:
        raise ValueError("document_id must not be empty")
    if not clean_collection:
        raise ValueError("collection_name must not be empty")
    if not 1 <= max_chunks <= 100:
        raise ValueError("max_chunks must be between 1 and 100")

    db = get_session()
    try:
        chunks = DocumentManager().get_document_chunks(
            db,
            clean_document_id,
            collection_name=clean_collection,
            limit=max_chunks,
        )
    finally:
        db.close()

    return {
        "status": "success" if chunks else "not_found",
        "document_id": clean_document_id,
        "collection": clean_collection,
        "count": len(chunks),
        "chunks": chunks,
    }


@mcp.tool(name="knowledge_search")
def knowledge_search_tool(
    query: str,
    collection_names: Optional[List[str]] = None,
    top_k: int = 5,
    max_results: int = 10,
    use_rerank: bool = True,
) -> Dict[str, Any]:
    """Search the existing knowledge base with hybrid retrieval and citations."""
    return search_knowledge(
        query=query,
        collection_names=collection_names,
        top_k=top_k,
        max_results=max_results,
        use_rerank=use_rerank,
    )


@mcp.tool(name="knowledge_list_collections")
def knowledge_list_collections_tool() -> Dict[str, Any]:
    """List the knowledge collections available to M1/M2 tasks."""
    return list_knowledge_collections()


@mcp.tool(name="knowledge_get_source")
def knowledge_get_source_tool(
    document_id: str,
    collection_name: str = "knowledge_base",
    max_chunks: int = 20,
) -> Dict[str, Any]:
    """Get source chunks for a document returned by knowledge_search."""
    return get_knowledge_source(
        document_id=document_id,
        collection_name=collection_name,
        max_chunks=max_chunks,
    )


def main() -> None:
    """Run the local stdio MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
