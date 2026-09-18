from __future__ import annotations

from dataclasses import dataclass, field, fields as dc_fields
from datetime import datetime
from typing import Optional
import uuid


SOURCE_TYPES = {"paper", "experiment", "insight", "concept", "conflict", "analysis"}
NODE_TYPES = {"concept", "method", "finding", "problem"}
EDGE_TYPES = {"supports", "contradicts", "related"}
DIRECTIONS = {"a_to_b", "b_to_a", "bidirectional"}
CONFIDENCE_LEVELS = {"high", "high_risk_high_reward", "engineering_only"}


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now()


@dataclass
class MemoryNode:
    id: str = field(default_factory=_new_id)
    content: str = ""
    gist: str = ""
    tags: list[str] = field(default_factory=list)
    content_hash: str = ""

    source_path: str = ""
    source_type: str = ""
    chunk_index: int = 0

    importance: float = 0.5
    decay_factor: float = 1.0
    access_count: int = 0

    created_at: datetime = field(default_factory=_now)
    last_accessed: datetime = field(default_factory=_now)

    def to_payload(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "gist": self.gist,
            "tags": ",".join(self.tags),
            "content_hash": self.content_hash,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "chunk_index": self.chunk_index,
            "importance": self.importance,
            "decay_factor": self.decay_factor,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
        }

    @classmethod
    def from_payload(cls, payload: dict) -> MemoryNode:
        raw_tags = payload.get("tags", "")
        if isinstance(raw_tags, str):
            tags = [t for t in raw_tags.split(",") if t] if raw_tags else []
        else:
            tags = raw_tags
        return cls(
            id=payload["id"],
            content=payload.get("content", ""),
            gist=payload.get("gist", ""),
            tags=tags,
            content_hash=payload.get("content_hash", ""),
            source_path=payload.get("source_path", ""),
            source_type=payload.get("source_type", ""),
            chunk_index=payload.get("chunk_index", 0),
            importance=payload.get("importance", 0.5),
            decay_factor=payload.get("decay_factor", 1.0),
            access_count=payload.get("access_count", 0),
            created_at=datetime.fromisoformat(payload["created_at"]) if "created_at" in payload else _now(),
            last_accessed=datetime.fromisoformat(payload["last_accessed"]) if "last_accessed" in payload else _now(),
        )


@dataclass
class ConceptNode:
    id: str = field(default_factory=_new_id)
    name: str = ""
    node_type: str = ""
    gist: str = ""
    tags: list[str] = field(default_factory=list)

    source_memory_ids: list[str] = field(default_factory=list)

    activation: float = 0.0
    importance: float = 0.5
    access_count: int = 0

    canonical: bool = True
    merged_into: Optional[str] = None


@dataclass
class GraphEdge:
    source_id: str = ""
    target_id: str = ""
    edge_type: str = "related"
    weight: float = 0.5
    description: str = ""
    direction: str = "bidirectional"

    created_at: datetime = field(default_factory=_now)
    last_reinforced: datetime = field(default_factory=_now)
    reinforce_count: int = 0


@dataclass
class IdeaCandidate:
    id: str = field(default_factory=_new_id)
    title: str = ""
    contribution: str = ""

    problem: str = ""
    insight: str = ""
    method: str = ""
    expected_result: str = ""

    strongest_objection: str = ""
    min_experiment: str = ""
    dream_scene: str = ""
    forgotten_variable: str = ""

    novelty_score: float = 0.0
    confidence: str = "high"
    source_round: int = 1
    dream_path: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

    # 层2: 可读表达
    readable_abstract: str = ""
    illustration: str = ""

    # 多维评分 (0.0-1.0)
    score_novelty: float = 0.0
    score_feasibility: float = 0.0
    score_soundness: float = 0.0
    score_surprise: float = 0.0
    score_applicability: float = 0.0
    score_rationale: str = ""

    user_rating: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "contribution": self.contribution,
            "problem": self.problem,
            "insight": self.insight,
            "method": self.method,
            "expected_result": self.expected_result,
            "strongest_objection": self.strongest_objection,
            "min_experiment": self.min_experiment,
            "dream_scene": self.dream_scene,
            "forgotten_variable": self.forgotten_variable,
            "novelty_score": self.novelty_score,
            "confidence": self.confidence,
            "source_round": self.source_round,
            "dream_path": self.dream_path,
            "evidence_ids": self.evidence_ids,
            "readable_abstract": self.readable_abstract,
            "illustration": self.illustration,
            "score_novelty": self.score_novelty,
            "score_feasibility": self.score_feasibility,
            "score_soundness": self.score_soundness,
            "score_surprise": self.score_surprise,
            "score_applicability": self.score_applicability,
            "score_rationale": self.score_rationale,
            "user_rating": self.user_rating,
        }

    @classmethod
    def from_dict(cls, d: dict) -> IdeaCandidate:
        return cls(**{k: v for k, v in d.items() if k in {f.name for f in dc_fields(cls)}})


@dataclass
class DreamResult:
    id: str = field(default_factory=_new_id)
    timestamp: datetime = field(default_factory=_now)

    rounds_config: list[dict] = field(default_factory=list)
    gravity_centers: list[str] = field(default_factory=list)

    ideas: list[IdeaCandidate] = field(default_factory=list)
    total_nodes_processed: int = 0
    total_paths_explored: int = 0

    duration_seconds: float = 0.0
    llm_calls: int = 0
    llm_tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "rounds_config": self.rounds_config,
            "gravity_centers": self.gravity_centers,
            "ideas": [idea.to_dict() for idea in self.ideas],
            "total_nodes_processed": self.total_nodes_processed,
            "total_paths_explored": self.total_paths_explored,
            "duration_seconds": self.duration_seconds,
            "llm_calls": self.llm_calls,
            "llm_tokens_used": self.llm_tokens_used,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DreamResult:
        result = cls(
            id=d["id"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            rounds_config=d.get("rounds_config", []),
            gravity_centers=d.get("gravity_centers", []),
            total_nodes_processed=d.get("total_nodes_processed", 0),
            total_paths_explored=d.get("total_paths_explored", 0),
            duration_seconds=d.get("duration_seconds", 0.0),
            llm_calls=d.get("llm_calls", 0),
            llm_tokens_used=d.get("llm_tokens_used", 0),
        )
        result.ideas = [IdeaCandidate.from_dict(i) for i in d.get("ideas", [])]
        return result
