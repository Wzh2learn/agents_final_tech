"""Offline contracts for session-scoped episodic memory metadata and recall."""

import asyncio

from langchain_core.documents import Document

from storage.memory.episodic_memory import EpisodicMemoryProvider


class FakeVectorStore:
    def __init__(self, matches=()):
        self.documents = []
        self.matches = list(matches)
        self.search_arguments = None

    def add_documents(self, documents):
        self.documents.extend(documents)

    def similarity_search(self, query, k, filter):
        self.search_arguments = (query, k, filter)
        return self.matches


def test_attached_metadata_cannot_override_session_or_memory_type():
    provider = EpisodicMemoryProvider()
    store = FakeVectorStore()
    provider._vector_store = store

    asyncio.run(provider.add_memory(
        session_id="conversation-a", content="remember this",
        metadata={"session_id": "conversation-b", "type": "system", "tag": "useful"},
    ))

    assert len(store.documents) == 1
    assert store.documents[0].metadata == {
        "session_id": "conversation-a", "type": "episodic", "tag": "useful"
    }


def test_recall_filters_other_sessions_even_if_backend_ignores_filter():
    provider = EpisodicMemoryProvider()
    store = FakeVectorStore([
        Document(page_content="other", metadata={"session_id": "conversation-b"}),
        Document(page_content="mine", metadata={"session_id": "conversation-a"}),
        Document(page_content="untagged", metadata={}),
    ])
    provider._vector_store = store

    found = asyncio.run(provider.search_memory("question", "conversation-a", top_k=3))

    assert store.search_arguments == ("question", 3, {"session_id": "conversation-a"})
    assert [item.page_content for item in found] == ["mine"]
