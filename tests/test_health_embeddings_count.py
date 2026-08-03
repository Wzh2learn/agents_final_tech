"""T2 regression: /api/health/full embeddings count must reflect real PG rows.

The old health check called ``rag.collection.count()``, but RAGService has no
``.collection`` attribute, so the count silently returned 0.
"""
import pytest


def _pg_ready() -> bool:
    try:
        from biz.m2_service import collection_name

        collection_name()
        from storage.database.db import get_session

        db = get_session()
        db.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _pg_ready(), reason="PGVector not reachable")
def test_embedding_count_positive():
    from biz.m2_service import embedding_count

    assert embedding_count() > 0


def test_health_full_reports_real_embedding_count():
    import json
    import urllib.request

    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(
            "http://127.0.0.1:5050/api/health/full", timeout=10
        ) as resp:
            data = json.loads(resp.read())
    except Exception:
        pytest.skip("FastAPI server on :5050 not reachable")
    count = data["components"]["pgvector"]["embeddings"]
    assert count > 0
