"""Offline contracts for session-scoped episodic memory metadata and recall."""

import asyncio
import json
import sys
import types

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from agents.agent import _windowed_messages
from biz.agent_service import AgentService
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

    saved = asyncio.run(provider.add_memory(
        session_id="conversation-a", content="remember this",
        metadata={"session_id": "conversation-b", "type": "system", "tag": "useful"},
    ))

    assert saved is True
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


def test_storage_failure_is_reported_without_advancing_a_caller():
    class FailingStore:
        def add_documents(self, documents):
            raise RuntimeError("synthetic storage failure")

    provider = EpisodicMemoryProvider()
    provider._vector_store = FailingStore()
    assert asyncio.run(provider.add_memory("conversation-a", "synthetic")) is False


class FakeReflector:
    def __init__(self):
        self.batches = []

    async def ainvoke(self, payload):
        self.batches.append(json.loads(payload))
        return json.dumps({"summary": "synthetic summary", "facts": []})


class FakeMemory:
    def __init__(self, results=(True,)):
        self.results = list(results)
        self.writes = []

    async def add_memory(self, **kwargs):
        self.writes.append(kwargs)
        return self.results.pop(0) if self.results else True


def install_fakes(monkeypatch, reflector, memory):
    reflection = types.ModuleType("tools.memory_reflector")
    reflection.reflect_on_conversation = reflector
    storage = types.ModuleType("storage.memory.episodic_memory")
    storage.get_episodic_memory_provider = lambda: memory
    monkeypatch.setitem(sys.modules, "tools.memory_reflector", reflection)
    monkeypatch.setitem(sys.modules, "storage.memory.episodic_memory", storage)


def synthetic_messages(count):
    return [HumanMessage(content=f"synthetic-{i}", id=f"message-{i}") for i in range(count)]


def test_graph_window_assigns_stable_ids_before_reflection():
    window = _windowed_messages([], [HumanMessage(content=f"synthetic-{i}") for i in range(41)])
    assert len(window) == 40
    assert len({message.id for message in window}) == 40
    assert all(isinstance(message.id, str) and message.id for message in window)


def test_reflection_advances_with_sliding_window_without_repeating(monkeypatch):
    reflector, memory = FakeReflector(), FakeMemory()
    install_fakes(monkeypatch, reflector, memory)
    service, messages = AgentService(), synthetic_messages(45)

    async def run():
        for window in (messages[:15], messages[:16], messages[:25], messages[:40], messages[5:45]):
            await service._check_and_trigger_reflection("session-a", window)

    asyncio.run(run())
    assert [[item["content"] for item in batch] for batch in reflector.batches] == [
        [f"synthetic-{i}" for i in range(start, start + 10)] for start in (0, 10, 20, 30)
    ]
    assert len(memory.writes) == 4


def test_failed_storage_retries_the_same_batch(monkeypatch):
    reflector, memory = FakeReflector(), FakeMemory((False, True))
    install_fakes(monkeypatch, reflector, memory)
    service, messages = AgentService(), synthetic_messages(15)

    async def run():
        await service._check_and_trigger_reflection("session-a", messages)
        await service._check_and_trigger_reflection("session-a", messages)

    asyncio.run(run())
    assert len(memory.writes) == 2
    assert reflector.batches[0] == reflector.batches[1]


def test_missing_or_out_of_window_message_ids_do_not_silently_resummarize(monkeypatch):
    reflector, memory = FakeReflector(), FakeMemory()
    install_fakes(monkeypatch, reflector, memory)
    service = AgentService()

    async def run():
        await service._check_and_trigger_reflection("missing-id", [HumanMessage(content="x")] * 15)
        await service._check_and_trigger_reflection("session-a", synthetic_messages(15))
        later = [HumanMessage(content=f"new-{i}", id=f"new-{i}") for i in range(40)]
        await service._check_and_trigger_reflection("session-a", later)

    asyncio.run(run())
    assert len(reflector.batches) == len(memory.writes) == 1


def test_concurrent_reflections_do_not_duplicate_writes(monkeypatch):
    class WaitingReflector(FakeReflector):
        async def ainvoke(self, payload):
            self.batches.append(json.loads(payload))
            started.set()
            await release.wait()
            return json.dumps({"summary": "synthetic summary", "facts": []})

    reflector, memory = WaitingReflector(), FakeMemory()
    install_fakes(monkeypatch, reflector, memory)
    service, messages = AgentService(), synthetic_messages(15)

    async def run():
        nonlocal started, release
        started, release = asyncio.Event(), asyncio.Event()
        first = asyncio.create_task(service._check_and_trigger_reflection("session-a", messages))
        await started.wait()
        second = asyncio.create_task(service._check_and_trigger_reflection("session-a", messages))
        await asyncio.sleep(0)
        release.set()
        await asyncio.gather(first, second)

    started = release = None
    asyncio.run(run())
    assert len(reflector.batches) == len(memory.writes) == 1
