from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_local_embedding_backend_is_selected_from_environment(monkeypatch, tmp_path):
    model_path = tmp_path / "embedding-model"
    model_path.mkdir()
    fake_model = MagicMock()
    fake_model.encode.return_value = SimpleNamespace(tolist=lambda: [[0.1, 0.2]])
    fake_module = SimpleNamespace(SentenceTransformer=MagicMock(return_value=fake_model))
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    monkeypatch.setenv("LOCAL_EMBEDDING_MODEL_PATH", str(model_path))
    monkeypatch.setenv("LOCAL_EMBEDDING_DEVICE", "cpu")

    import tools.vector_store as vector_store

    monkeypatch.setattr(vector_store, "_embeddings_client", None)
    embeddings = vector_store.get_embeddings()
    assert embeddings.embed_query("query") == [0.1, 0.2]
    fake_module.SentenceTransformer.assert_called_once_with(
        str(model_path), trust_remote_code=True, device="cpu"
    )


def test_parsed_blocks_keep_traceable_metadata(monkeypatch):
    import biz.rag_service as rag_service

    store = MagicMock()
    monkeypatch.setattr(rag_service, "get_vector_store", MagicMock(return_value=store))
    service = rag_service.RAGService(collection_name="tat-dqa-validation")
    result = service.ingest_parsed_blocks(
        "doc-1",
        [
            {
                "block_id": "block-1",
                "text": "Revenue increased.",
                "page": 1,
                "bbox": [0, 0, 10, 10],
                "order": 2,
            },
            {"block_id": "", "text": "ignored"},
        ],
        metadata={"source": "doc-1.pdf", "split": "validation"},
    )

    assert result == {
        "document_id": "doc-1",
        "source": "doc-1.pdf",
        "chunks": 1,
        "collection": "tat-dqa-validation",
    }
    document = store.add_documents.call_args.args[0][0]
    assert document.page_content == "Revenue increased."
    assert document.metadata["block_id"] == "block-1"
    assert document.metadata["document_id"] == "doc-1"
    assert document.metadata["parsed_upper_bound"] is True
