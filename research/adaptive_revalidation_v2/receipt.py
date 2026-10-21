"""Hash-bound deterministic result receipts for development-only fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from .fixtures import DEV_ONLY_STATUS, PUBLIC_TOOL_NAMES
from .model import canonical_json_bytes
from .runner import DEFAULT_POLICY_SPECS, experiment_as_dict, run_experiment
from .fixtures import load_frozen_scenarios


RECEIPT_SCHEMA = "adaptive-revalidation-receipt-v1"
REQUIRED_METRICS = {
    "final_action_loss",
    "repair_loss",
    "query_cost",
    "recomputation_cost",
    "missed_invalidation",
    "over_invalidation",
    "regression_rate",
    "completion",
    "abstention",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_source_hashes(root: Path) -> Mapping[str, str]:
    """Hash the owned implementation, tests, fixtures, and source notes."""
    root = root.resolve()
    paths = []
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "result_receipt.json":
            continue
        if path.suffix in {".py", ".json", ".md"} or path.name == "py.typed":
            paths.append(path)
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix())
    }


def build_receipt(
    root: Path,
    test_command: str,
    test_exit_code: int,
    test_passed: int,
    test_failed: int,
    test_skipped: int,
) -> Mapping[str, Any]:
    """Build a deterministic receipt from a fresh in-process experiment replay."""
    scenarios = load_frozen_scenarios()
    experiment = run_experiment(scenarios, DEFAULT_POLICY_SPECS)
    result = experiment_as_dict(experiment)
    payload: Dict[str, Any] = {
        "receipt_schema": RECEIPT_SCHEMA,
        "status": DEV_ONLY_STATUS,
        "evidence_boundary": DEV_ONLY_STATUS,
        "claims": {
            "external_task_performance": False,
            "model_calls": 0,
            "network_calls": 0,
            "production_behavior": False,
        },
        "zero_call_accounting": {
            "model_calls": 0,
            "judge_calls": 0,
            "network_calls": 0,
            "database_calls": 0,
            "training_calls": 0,
        },
        "environment_contract": {
            "executable_node_count": 12,
            "output_count": 3,
            "public_tools": list(PUBLIC_TOOL_NAMES),
            "query_policy_kinds": [spec.policy_kind.value for spec in DEFAULT_POLICY_SPECS],
            "query_cost_unit": 1,
        },
        "fixtures": {
            "path": "fixtures/scenarios.json",
            "scenario_count": len(scenarios),
            "families": [scenario.family for scenario in scenarios],
            "status": DEV_ONLY_STATUS,
        },
        "test_summary": {
            "command": test_command,
            "exit_code": int(test_exit_code),
            "passed": int(test_passed),
            "failed": int(test_failed),
            "skipped": int(test_skipped),
            "status": "PASS" if test_exit_code == 0 and test_failed == 0 else "FAIL",
        },
        "policy_aggregate": result["policy_aggregate"],
        "policy_results": result["policy_results"],
        "evaluator_only_upper_bounds": result["evaluator_only_upper_bounds"],
        "source_hashes": dict(collect_source_hashes(root)),
        "source_hash_algorithm": "sha256",
    }
    return payload


def write_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    """Write a human-readable but deterministic JSON receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    path.write_text(text + "\n", encoding="utf-8")


def verify_receipt(path: Path, root: Path) -> Mapping[str, Any]:
    """Verify status, source hashes, zero-call claims, and metric contracts."""
    root = root.resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("receipt_schema") != RECEIPT_SCHEMA:
        raise ValueError("RECEIPT_SCHEMA_MISMATCH")
    if payload.get("status") != DEV_ONLY_STATUS:
        raise ValueError("RECEIPT_STATUS_MISMATCH")
    if payload.get("claims", {}).get("model_calls") != 0:
        raise ValueError("RECEIPT_MODEL_CALL_CLAIM_NONZERO")
    if payload.get("claims", {}).get("network_calls") != 0:
        raise ValueError("RECEIPT_NETWORK_CALL_CLAIM_NONZERO")
    current_hashes = dict(collect_source_hashes(root))
    recorded_hashes = payload.get("source_hashes")
    if recorded_hashes != current_hashes:
        missing = sorted(set(current_hashes) - set(recorded_hashes or {}))
        stale = sorted(set(recorded_hashes or {}) - set(current_hashes))
        mismatched = sorted(
            key
            for key in set(current_hashes) & set(recorded_hashes or {})
            if current_hashes[key] != recorded_hashes[key]
        )
        raise ValueError("RECEIPT_SOURCE_HASH_MISMATCH", missing, stale, mismatched)
    policy_results = payload.get("policy_results")
    if not isinstance(policy_results, list) or not policy_results:
        raise ValueError("RECEIPT_POLICY_RESULTS_EMPTY")
    for episode in policy_results:
        metrics = episode.get("metrics", {})
        missing_metrics = sorted(REQUIRED_METRICS - set(metrics))
        if missing_metrics:
            raise ValueError("RECEIPT_REQUIRED_METRIC_MISSING", missing_metrics)
        serialized = canonical_json_bytes(episode)
        lowered = serialized.lower()
        for forbidden in (b"gold", b"hidden_checker_graph", b"hidden_trace"):
            if forbidden in lowered:
                raise ValueError("RECEIPT_POLICY_SERIALIZATION_LEAK", forbidden.decode())
    upper_bounds = payload.get("evaluator_only_upper_bounds", {})
    if upper_bounds.get("policy_eligible") is not False:
        raise ValueError("RECEIPT_UPPER_BOUND_POLICY_LEAK")
    return {
        "status": "PASS",
        "source_files": len(current_hashes),
        "policy_episodes": len(policy_results),
        "receipt_sha256": _sha256(path),
    }


def receipt_hash(path: Path) -> str:
    """Return the SHA-256 of a receipt file."""
    return _sha256(path)
