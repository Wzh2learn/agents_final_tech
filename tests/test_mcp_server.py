from __future__ import annotations

from unittest.mock import Mock

import pytest

from mcp_server import server


def test_search_knowledge_forwards_retrieval_options(monkeypatch):
    service = Mock()
    service.smart_retrieve.return_value = [
        {
            "content": "Interest accrues after 90 days.",
            "source": "policy.md",
            "collection": "rules",
        }
    ]
    monkeypatch.setattr(server, "get_rag_service_sync", lambda: service)

    result = server.search_knowledge(
        " installment rule ",
        collection_names=["rules"],
        top_k=4,
        max_results=6,
        use_rerank=False,
    )

    assert result["status"] == "success"
    assert result["count"] == 1
    service.smart_retrieve.assert_called_once_with(
        query="installment rule",
        collection_names=["rules"],
        top_k=4,
        max_results=6,
        use_rerank=False,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("query", " "),
        ("top_k", 0),
        ("max_results", 51),
    ],
)
def test_search_knowledge_validates_inputs(field, value):
    kwargs = {"query": "rule", "top_k": 5, "max_results": 10}
    kwargs[field] = value

    with pytest.raises(ValueError):
        server.search_knowledge(**kwargs)


def test_list_knowledge_collections(monkeypatch):
    service = Mock()
    service.get_collection_names.return_value = ["knowledge_base", "finance_rules"]
    monkeypatch.setattr(server, "get_rag_service_sync", lambda: service)

    result = server.list_knowledge_collections()

    assert result == {
        "status": "success",
        "count": 2,
        "collections": ["knowledge_base", "finance_rules"],
    }


def test_get_knowledge_source_closes_database_session(monkeypatch):
    db = Mock()
    manager = Mock()
    manager.get_document_chunks.return_value = [
        {"id": "chunk-1", "content": "Rule evidence", "metadata": {"page": 2}}
    ]
    monkeypatch.setattr(server, "get_session", lambda: db)
    monkeypatch.setattr(server, "DocumentManager", lambda: manager)

    result = server.get_knowledge_source(
        "policy.md",
        collection_name="finance_rules",
        max_chunks=8,
    )

    assert result["status"] == "success"
    assert result["count"] == 1
    manager.get_document_chunks.assert_called_once_with(
        db,
        "policy.md",
        collection_name="finance_rules",
        limit=8,
    )
    db.close.assert_called_once_with()
