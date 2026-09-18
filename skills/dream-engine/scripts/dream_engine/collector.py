"""Memory collector: file scanning, chunking, and ingestion.

No embedding, no vector DB. Pure file I/O + text processing.
"""
from __future__ import annotations

import re
from pathlib import Path

from .config import Config
from .errors import IngestError
from .models import MemoryNode
from .storage import MemoryStore, content_hash


CHUNK_STRATEGIES = {
    "paper":      {"split_on": "## ",  "min_chars": 100, "max_chars": 2000},
    "concept":    {"split_on": "## ",  "min_chars": 100, "max_chars": 2000},
    "analysis":   {"split_on": "## ",  "min_chars": 100, "max_chars": 2000},
    "experiment": {"split_on": "### ", "min_chars": 200, "max_chars": 5000},
    "insight":    {"split_on": None,   "min_chars": 50,  "max_chars": 3000},
    "conflict":   {"split_on": "## ",  "min_chars": 100, "max_chars": 2000},
}

SOURCE_TYPE_PATTERNS = [
    ("01-论文",          "paper"),
    ("02-概念",          "concept"),
    ("03-来源",          "analysis"),
    ("04-分析",          "analysis"),
    ("00-总览",          "concept"),
    ("EXPERIMENTS_LOG",  "experiment"),
    ("memories/",        "insight"),
]


class MemoryCollector:
    def __init__(self, config: Config, store: MemoryStore):
        self._config = config
        self._store = store

    def ingest_all(self) -> list[MemoryNode]:
        nodes: list[MemoryNode] = []
        for ip in self._config.input_paths:
            p = Path(ip.path)
            if not p.exists():
                print(f"  [skip] 路径不存在: {ip.path}")
                continue
            if p.is_file():
                nodes.extend(self.ingest_file(str(p)))
            elif p.is_dir():
                nodes.extend(self.ingest_directory(str(p), recursive=ip.recursive))
        return nodes

    def ingest_directory(self, dir_path: str, recursive: bool = True) -> list[MemoryNode]:
        p = Path(dir_path)
        if not p.is_dir():
            raise IngestError(f"不是目录: {dir_path}", "请传入一个有效的目录路径")
        pattern = "**/*.md" if recursive else "*.md"
        nodes: list[MemoryNode] = []
        for md_file in sorted(p.glob(pattern)):
            nodes.extend(self.ingest_file(str(md_file)))
        return nodes

    def ingest_file(self, file_path: str) -> list[MemoryNode]:
        p = Path(file_path)
        if not p.exists():
            raise IngestError(f"文件不存在: {file_path}", "检查路径是否正确")
        if p.suffix != ".md":
            return []

        content = p.read_text(encoding="utf-8")
        if not content.strip():
            return []

        source_type = self._detect_source_type(file_path)
        chunks = self._chunk_file(content, source_type)
        if not chunks:
            return []

        nodes: list[MemoryNode] = []
        skipped = 0
        for idx, chunk in enumerate(chunks):
            ch = content_hash(chunk)
            if self._store.dedup_check(chunk):
                skipped += 1
                continue

            node = MemoryNode(
                content=chunk,
                gist=self._extract_gist(chunk),
                content_hash=ch,
                source_path=file_path,
                source_type=source_type,
                chunk_index=idx,
            )
            nodes.append(node)

        new_count = self._store.add_batch(nodes)
        if skipped:
            print(f"  {p.name}: +{new_count} 节点（{skipped} 重复跳过）")
        elif new_count:
            print(f"  {p.name}: +{new_count} 节点")

        return nodes

    def get_all_nodes(self) -> list[MemoryNode]:
        return self._store.get_all()

    def count(self) -> int:
        return self._store.count()

    def _detect_source_type(self, file_path: str) -> str:
        for pattern, stype in SOURCE_TYPE_PATTERNS:
            if pattern in file_path:
                return stype
        return "analysis"

    def _extract_gist(self, chunk: str) -> str:
        """Extract the most informative line as gist, skipping metadata/boilerplate."""
        skip_patterns = ["source:", "---", "id:", "type:", "status:", "updated:", "http"]
        heading = ""
        best_line = ""

        for line in chunk.strip().split("\n"):
            stripped = line.strip()
            if not stripped or len(stripped) < 5:
                continue
            lower = stripped.lower()
            if any(lower.startswith(p) for p in skip_patterns):
                continue
            if stripped.startswith("#") and not heading:
                heading = stripped.lstrip("#").strip()[:60]
                continue
            if stripped.startswith("- ") or stripped.startswith("* "):
                candidate = stripped[2:].strip()
                if len(candidate) > 15 and not best_line:
                    best_line = candidate[:60]
                    continue
            if len(stripped) > 20 and not best_line:
                best_line = stripped[:60]

        if heading and best_line:
            return f"{heading} — {best_line}"[:60]
        return heading or best_line or chunk[:60]

    def _chunk_file(self, content: str, source_type: str) -> list[str]:
        strategy = CHUNK_STRATEGIES.get(source_type, CHUNK_STRATEGIES["analysis"])
        split_on = strategy["split_on"]
        min_chars = strategy["min_chars"]
        max_chars = strategy["max_chars"]

        if split_on is None:
            if len(content.strip()) >= min_chars:
                return [content.strip()]
            return []

        parts = re.split(f"(?=^{re.escape(split_on)})", content, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]

        merged: list[str] = []
        for part in parts:
            if merged and len(merged[-1]) < min_chars:
                merged[-1] += "\n\n" + part
            else:
                merged.append(part)

        final: list[str] = []
        for chunk in merged:
            if len(chunk) <= max_chars:
                if len(chunk) >= min_chars:
                    final.append(chunk)
                elif final:
                    final[-1] += "\n\n" + chunk
            else:
                paragraphs = chunk.split("\n\n")
                buf = ""
                for para in paragraphs:
                    if buf and len(buf) + len(para) > max_chars:
                        if len(buf) >= min_chars:
                            final.append(buf.strip())
                        buf = para
                    else:
                        buf = buf + "\n\n" + para if buf else para
                if buf.strip() and len(buf.strip()) >= min_chars:
                    final.append(buf.strip())
                elif buf.strip() and final:
                    final[-1] += "\n\n" + buf.strip()

        return final
