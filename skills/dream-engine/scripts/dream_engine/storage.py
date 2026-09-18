"""JSONL-based storage layer replacing ChromaDB.

All persistence goes through this module. No embeddings, no vector DB.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from .models import MemoryNode


def content_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class MemoryStore:
    def __init__(self, path: str):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._hashes: set[str] = set()
        self._nodes: list[MemoryNode] | None = None
        self._load_hashes()

    def _load_hashes(self) -> None:
        if not self._path.exists():
            return
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    h = obj.get("content_hash", "")
                    if h:
                        self._hashes.add(h)
                except json.JSONDecodeError:
                    continue

    def add_batch(self, nodes: list[MemoryNode]) -> int:
        new_count = 0
        with open(self._path, "a", encoding="utf-8") as f:
            for node in nodes:
                if not node.content_hash:
                    node.content_hash = content_hash(node.content)
                if node.content_hash in self._hashes:
                    continue
                self._hashes.add(node.content_hash)
                f.write(json.dumps(node.to_payload(), ensure_ascii=False) + "\n")
                new_count += 1
        self._nodes = None
        return new_count

    def get_all(self) -> list[MemoryNode]:
        if self._nodes is not None:
            return self._nodes
        nodes = []
        if not self._path.exists():
            return nodes
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    nodes.append(MemoryNode.from_payload(obj))
                except (json.JSONDecodeError, KeyError):
                    continue
        self._nodes = nodes
        return nodes

    def get_all_gists(self) -> list[dict]:
        nodes = self.get_all()
        return [
            {
                "id": n.id,
                "gist": n.gist or n.content[:80],
                "source_type": n.source_type,
                "source_path": Path(n.source_path).name if n.source_path else "",
                "tags": n.tags,
                "content_preview": n.content[:120].replace("\n", " "),
            }
            for n in nodes
        ]

    def get_nodes_by_ids(self, ids: list[str]) -> list[MemoryNode]:
        all_nodes = self.get_all()
        result = []
        for target_id in ids:
            for n in all_nodes:
                if n.id == target_id or n.id.startswith(target_id):
                    result.append(n)
                    break
        return result

    def count(self) -> int:
        return len(self.get_all())

    def dedup_check(self, text: str) -> bool:
        return content_hash(text) in self._hashes

    def update_node(self, node_id: str, updates: dict) -> bool:
        nodes = self.get_all()
        found = False
        for node in nodes:
            if node.id == node_id:
                for k, v in updates.items():
                    if hasattr(node, k):
                        setattr(node, k, v)
                found = True
                break
        if found:
            self._rewrite(nodes)
        return found

    def _rewrite(self, nodes: list[MemoryNode]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            for node in nodes:
                f.write(json.dumps(node.to_payload(), ensure_ascii=False) + "\n")
        self._nodes = nodes
