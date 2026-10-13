from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


TASK = "tatqa_wp1_loop_a"


def task_provenance() -> dict[str, Any]:
    return {
        "writer": "research/tatqa_wp0_2026/wp1/provenance.py",
        "task": TASK,
        "role": "Loop A / GB10 implementation",
        "model_calls": 0,
        "endpoint_calls": 0,
    }


def attributed_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["provenance"] = task_provenance()
    return result


def write_json_lf(path: str | Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    destination.write_text(text + "\n", encoding="utf-8", newline="\n")
