from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SpreadingActivationConfig:
    decay_factor: float = 0.5
    max_hops: int = 3


@dataclass
class GraphConfig:
    spreading_activation: SpreadingActivationConfig = field(
        default_factory=SpreadingActivationConfig
    )
    global_decay: float = 0.95
    cluster_threshold: float = 0.8
    dedup_cosine_threshold: float = 0.85
    edge_cosine_threshold: float = 0.3
    edge_batch_size: int = 10


@dataclass
class DreamRound:
    name: str = "medium"
    activation_threshold: float = 0.4
    top_k: int = 8


@dataclass
class DreamConfig:
    mode: str = "paper"
    schedule_interval_hours: int = 6
    split_rem_phases: bool = False
    llm_guided_activation: bool = False
    gravity_centers: list[str] = field(default_factory=list)
    rounds: list[DreamRound] = field(default_factory=lambda: [
        DreamRound("shallow", 0.7, 5),
        DreamRound("medium", 0.4, 8),
        DreamRound("deep", 0.1, 10),
    ])


@dataclass
class FeedbackConfig:
    upvote_delta: float = 0.1
    downvote_delta: float = -0.05


@dataclass
class DomainConfig:
    name: str = "推荐系统与序列建模"
    key_venues: str = "RecSys, KDD, WWW, SIGIR"
    reviewer_profile: str = "熟悉推荐系统和信息检索的顶会reviewer"
    examples_dir: str = "examples/recsys/"


@dataclass
class InputPath:
    path: str = ""
    recursive: bool = True


@dataclass
class StorageConfig:
    memories_path: str = "data/memories.jsonl"
    graph_path: str = "data/graph_{namespace}.json"
    dreams_dir: str = "data/dreams/"
    namespace: str = "default"


@dataclass
class Config:
    domain: DomainConfig = field(default_factory=DomainConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    dream: DreamConfig = field(default_factory=DreamConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    input_paths: list[InputPath] = field(default_factory=list)
    node_granularity: str = "related_work_citation"

    @property
    def graph_path(self) -> str:
        return self.storage.graph_path.format(namespace=self.storage.namespace)

    @property
    def memories_path(self) -> str:
        return self.storage.memories_path


def _build_nested(cls: type, data: dict[str, Any]) -> Any:
    import dataclasses
    import typing
    if not isinstance(data, dict):
        return data
    if not dataclasses.is_dataclass(cls):
        return data
    hints = typing.get_type_hints(cls)
    kwargs = {}
    for f in dataclasses.fields(cls):
        if f.name not in data:
            continue
        val = data[f.name]
        ftype = hints.get(f.name, f.type)
        origin = getattr(ftype, "__origin__", None)
        if origin is list and isinstance(val, list):
            args = getattr(ftype, "__args__", ())
            item_cls = args[0] if args else None
            if item_cls and dataclasses.is_dataclass(item_cls):
                kwargs[f.name] = [_build_nested(item_cls, v) for v in val]
            else:
                kwargs[f.name] = val
        elif dataclasses.is_dataclass(ftype):
            kwargs[f.name] = _build_nested(ftype, val)
        else:
            kwargs[f.name] = val
    return cls(**kwargs)


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        return Config()
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return _build_nested(Config, raw)
