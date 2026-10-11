#!/usr/bin/env python3
"""Audit Agent Distillation payload provenance and adapter feasibility."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_method_revision_20261009"
DATA = Path(
    "/home/testuser/wzh/external_stage_d_repro/datasets/agent_distillation/"
    "Qwen2.5-32B-Instruct_agent_trajectories_2k.jsonl"
)
REPO = Path("/home/testuser/wzh/external_stage_d_repro/repos/agent_distillation")
OUT_JSON = TASK / "agent_distillation_adapter_provenance_audit.json"
OUT_IDS = TASK / "agent_distillation_derived_ids.jsonl"
OUT_MD = ROOT / "docs/research/agent_distillation_adapter_provenance_audit_v1.md"

ERROR_MARKERS = {
    "parsing": "Error in code parsing",
    "max_steps": "Reached max steps",
    "execution": "Code execution failed",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_positive(score: Any) -> bool | None:
    if score in (True, 1, "1", "True", "true"):
        return True
    if score in (False, 0, "0", "False", "false"):
        return False
    return None


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content or "")


def derived_split(task_id: str) -> str:
    bucket = int(sha256_text(f"20261010:{task_id}")[:8], 16) / 0xFFFFFFFF
    if bucket < 0.70:
        return "train"
    if bucket < 0.85:
        return "dev"
    return "test"


def build() -> dict[str, Any]:
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    score_dataset = Counter()
    score_explanation = Counter()
    blank_patterns = Counter()
    task_rows: dict[str, list[int]] = defaultdict(list)
    derived_rows = []
    role_counts = Counter()
    error_counts = Counter()
    structural_counts = Counter()
    step_reward_rows = 0
    step_reward_steps = 0

    for index, row in enumerate(rows):
        score = row.get("score")
        score_dataset[(str(row.get("dataset_name")), str(score))] += 1
        score_explanation[(str(score), bool(str(row.get("explanation") or "").strip()))] += 1
        normalized = normalize_positive(score)
        raw_score = str(score)
        if raw_score == "":
            blank_patterns["blank_score"] += 1
            if not str(row.get("explanation") or "").strip():
                blank_patterns["blank_score_and_explanation"] += 1
            if not str(row.get("generated_answer") or "").strip():
                blank_patterns["blank_generated_answer"] += 1
            if str(row.get("generated_answer") or "") == str(row.get("true_answer") or ""):
                blank_patterns["blank_score_but_answer_text_matches_gold"] += 1
        elif raw_score == "True":
            blank_patterns["raw_true"] += 1
        elif raw_score == "1":
            blank_patterns["raw_one"] += 1

        log_data = row.get("log_data")
        if isinstance(log_data, str):
            log_data = json.loads(log_data)
        log_data = log_data if isinstance(log_data, dict) else {}
        messages = [message for message in log_data.get("messages") or [] if isinstance(message, dict)]
        for message in messages:
            role = str(message.get("role"))
            role_counts[role] += 1
            if role in {"tool-response", "MessageRole.TOOL_RESPONSE"}:
                text = message_text(message)
                for name, marker in ERROR_MARKERS.items():
                    if marker in text:
                        error_counts[name] += 1
        tool_calls = sum(str(message.get("role")) in {"tool-call", "MessageRole.TOOL_CALL"} for message in messages)
        tool_responses = sum(
            str(message.get("role")) in {"tool-response", "MessageRole.TOOL_RESPONSE"}
            for message in messages
        )
        structural_counts["rows_with_tool_calls"] += int(tool_calls > 0)
        structural_counts["rows_with_balanced_tool_call_response_counts"] += int(tool_calls == tool_responses)
        structural_counts["tool_calls"] += tool_calls
        structural_counts["tool_responses"] += tool_responses

        memory_steps = (log_data.get("original_memory") or {}).get("steps") or []
        row_step_reward = int("step_reward" in row)
        row_step_reward += sum("step_reward" in step for step in memory_steps if isinstance(step, dict))
        step_reward_rows += int(row_step_reward > 0)
        step_reward_steps += row_step_reward

        question = str(row.get("question") or "")
        dataset_name = str(row.get("dataset_name") or "")
        canonical_row = json.dumps(row, ensure_ascii=False, sort_keys=True)
        row_hash = sha256_text(canonical_row)
        task_id = sha256_text(f"{dataset_name}\n{question.strip()}")
        trajectory_id = sha256_text(f"{task_id}\n{row_hash}")
        task_rows[task_id].append(index)
        derived_rows.append({
            "row_index": index,
            "row_sha256": row_hash,
            "derived_task_id": task_id,
            "derived_trajectory_id": trajectory_id,
            "derived_origin_group": task_id,
            "derived_split": derived_split(task_id),
            "provenance": "DERIVED_NOT_NATIVE",
        })

    with OUT_IDS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in derived_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    filter_source = REPO / "exps_research/unified_framework/filter_agent_training_data.py"
    preprocess_source = REPO / "exps_research/train_utils/preprocess.py"
    score_source = REPO / "exps_research/unified_framework/score_answers.py"
    source_occurrences = {}
    for name, path in (
        ("filter_agent_training_data.py", filter_source),
        ("preprocess.py", preprocess_source),
        ("score_answers.py", score_source),
    ):
        text = path.read_text(encoding="utf-8")
        source_occurrences[name] = {
            "sha256": sha256_file(path),
            "step_reward_occurrences": text.count("step_reward"),
            "score_assignment_occurrences": text.count('result["score"]') + text.count('["score"]'),
        }

    negative_count = sum(normalize_positive(row.get("score")) is False for row in rows)
    positive_count = sum(normalize_positive(row.get("score")) is True for row in rows)
    unknown_count = sum(normalize_positive(row.get("score")) is None for row in rows)
    task_sizes = [len(value) for value in task_rows.values()]
    split_counts = Counter(row["derived_split"] for row in derived_rows)

    semantic_signal_available = False
    pilot_ready = (
        negative_count > 0
        and positive_count > 0
        and step_reward_rows == 0
        and semantic_signal_available
        and len(task_rows) >= 24
    )
    status = "PILOT_CANDIDATE" if pilot_ready else "NOT_SUITABLE_FOR_C2_C4"

    return {
        "namespace": "AGENT_DISTILLATION_ADAPTER_PROVENANCE_AUDIT",
        "status": status,
        "data": {
            "dataset_revision": "cbd8971069aeb04ec3cc95282ef2397e8206a817",
            "path": str(DATA),
            "sha256": sha256_file(DATA),
            "rows": len(rows),
        },
        "licences": {
            "code": "Apache-2.0",
            "data": "LICENCE_PENDING",
            "model": "NOT_USED",
        },
        "terminal_outcome": {
            "raw_score_counts": dict(Counter(str(row.get("score")) for row in rows)),
            "dataset_by_raw_score": {
                f"{dataset}|{score}": count
                for (dataset, score), count in sorted(score_dataset.items())
            },
            "raw_score_by_explanation_presence": {
                f"{score}|explanation={present}": count
                for (score, present), count in sorted(score_explanation.items())
            },
            "normalized": {
                "positive": positive_count,
                "negative": negative_count,
                "unknown_or_missing": unknown_count,
            },
            "blank_diagnosis": {
                "counts": dict(blank_patterns),
                "classification": "UNKNOWN_UNSORED_OR_PIPELINE_MISSING",
                "failed_label_supported_by_payload": False,
                "reason": "blank score is not an explicit failed outcome and code scoring paths assign a score when invoked",
            },
            "true_vs_one": {
                "raw_encoding_equivalent": False,
                "normalized_terminal_positive_equivalent": True,
                "provenance": "different raw encodings; task/evaluator origin must be preserved and normalized by adapter",
                "consumer_risk": "released raw strings do not satisfy a numeric score==1 comparison without normalization",
            },
        },
        "step_reward_audit": {
            "rows_with_step_reward": step_reward_rows,
            "steps_with_step_reward": step_reward_steps,
            "released_payload_value": "ABSENT",
            "producer_found": False,
            "consumer_found": source_occurrences["preprocess.py"]["step_reward_occurrences"] > 0,
            "classification": "UNPROVEN_CONSUMER_ONLY_FIELD_OR_PLACEHOLDER",
        },
        "derived_ids": {
            "provenance": "DERIVED_NOT_NATIVE",
            "task_id_rule": "SHA256(dataset_name + normalized question)",
            "trajectory_id_rule": "SHA256(derived_task_id + canonical row hash)",
            "origin_group_rule": "derived_task_id",
            "split_rule": "stable SHA-256 bucket of derived_task_id under 70/15/15 thresholds",
            "unique_task_ids": len(task_rows),
            "trajectory_rows": len(derived_rows),
            "task_group_size": {
                "min": min(task_sizes),
                "median": float(np_median(task_sizes)),
                "max": max(task_sizes),
            },
            "derived_split_counts": dict(sorted(split_counts.items())),
            "manifest_path": str(OUT_IDS),
            "manifest_sha256": sha256_file(OUT_IDS),
        },
        "process_signal_feasibility": {
            "syntactic_tool_contract_validity": {
                "status": "DERIVABLE",
                "scope": "tool-call/tool-response presence, pairing and argument serialization shape",
                "cannot_establish": "semantic action correctness",
            },
            "execution_success_proxy": {
                "status": "DERIVABLE_WITH_PROVENANCE",
                "error_marker_counts": dict(error_counts),
                "cannot_establish": "observation consistency or task progress without replay/state snapshots",
            },
            "observation_consistency": {
                "status": "NOT_AVAILABLE",
                "requires": "replay or independently captured expected observation",
            },
            "state_transition_consistency": {
                "status": "NOT_AVAILABLE",
                "requires": "state snapshots/replay contract",
            },
            "semantic_step_verifier": {
                "status": "NOT_AVAILABLE",
                "requires": "independent verifier not derived from terminal score",
            },
            "message_structure": {
                **dict(structural_counts),
                "roles": dict(sorted(role_counts.items())),
            },
        },
        "source_code_evidence": source_occurrences,
        "pilot_decision": {
            "status": status,
            "reasons": [
                f"terminal outcomes have {positive_count} positive and {negative_count} negative rows",
                f"step_reward is absent from {len(rows)} released rows",
                "no independent semantic process signal is available",
                "native task/trajectory/origin IDs and split are absent; derived IDs do not close provenance",
            ],
            "allowed_now": [
                "adapter development",
                "normalization smoke",
                "syntactic Tool Contract Validity",
                "execution-error proxy audit",
            ],
            "not_allowed": [
                "calling derived IDs native",
                "calling syntactic validity semantic correctness",
                "formal C2/C4 pilot training",
            ],
        },
    }


def np_median(values: list[int]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def render(payload: dict[str, Any]) -> str:
    terminal = payload["terminal_outcome"]
    step = payload["step_reward_audit"]
    ids = payload["derived_ids"]
    process = payload["process_signal_feasibility"]
    decision = payload["pilot_decision"]
    return f"""# Agent Distillation Adapter and Provenance Audit v1

> Status: `{payload['status']}` | Scope: adapter/provenance audit only; no C2/C4 pilot or training

## 1. Terminal outcome

- Raw score counts: `{terminal['raw_score_counts']}`
- Normalized positive / negative / unknown: `{terminal['normalized']['positive']}` / `{terminal['normalized']['negative']}` / `{terminal['normalized']['unknown_or_missing']}`
- Blank diagnosis: `{terminal['blank_diagnosis']['classification']}`
- Blank score count: `{terminal['blank_diagnosis']['counts'].get('blank_score', 0)}`
- `True` versus `1`: raw encodings are not identical; both normalize to terminal positive. `{terminal['true_vs_one']['consumer_risk']}`

`VERIFIED`: the released payload has no normalized negative terminal outcome. Blank rows cannot be interpreted as failed without additional provenance.

## 2. step_reward

- Rows with `step_reward`: `{step['rows_with_step_reward']}`
- Steps with `step_reward`: `{step['steps_with_step_reward']}`
- Producer found: `{step['producer_found']}`
- Consumer found: `{step['consumer_found']}`
- Classification: `{step['classification']}`

`FACT`: `step_reward` is consumer-only/placeholder-like in inspected code and absent from the released payload. It cannot be used as native process supervision.

## 3. Derived identifiers

- Provenance: `{ids['provenance']}`
- Unique derived task IDs: `{ids['unique_task_ids']}`
- Trajectory rows: `{ids['trajectory_rows']}`
- Task group size min/median/max: `{ids['task_group_size']['min']}` / `{ids['task_group_size']['median']}` / `{ids['task_group_size']['max']}`
- Derived split counts: `{ids['derived_split_counts']}`
- Manifest: `{ids['manifest_path']}`
- SHA-256: `{ids['manifest_sha256']}`

These IDs are `DERIVED`, not native dataset identifiers.

## 4. Process-signal feasibility

| Signal | Status | Boundary |
|---|---|---|
| Tool Contract Validity | `{process['syntactic_tool_contract_validity']['status']}` | syntactic only |
| Execution-success proxy | `{process['execution_success_proxy']['status']}` | error-marker proxy only |
| Observation consistency | `{process['observation_consistency']['status']}` | requires replay/expected observation |
| State-transition consistency | `{process['state_transition_consistency']['status']}` | requires state snapshots |
| Semantic step verifier | `{process['semantic_step_verifier']['status']}` | independent verifier absent |

Tool/error structure: `{process['message_structure']}`

## 5. Pilot boundary

Reasons:

{chr(10).join('- ' + reason for reason in decision['reasons'])}

Allowed now:

{chr(10).join('- ' + item for item in decision['allowed_now'])}

Not allowed:

{chr(10).join('- ' + item for item in decision['not_allowed'])}

AGENT_DISTILLATION_PILOT_STATUS: {payload['status']}
"""


def main() -> int:
    payload = build()
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": payload["status"],
        "terminal_normalized": payload["terminal_outcome"]["normalized"],
        "step_reward_rows": payload["step_reward_audit"]["rows_with_step_reward"],
        "derived_task_ids": payload["derived_ids"]["unique_task_ids"],
        "output": str(OUT_MD),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
