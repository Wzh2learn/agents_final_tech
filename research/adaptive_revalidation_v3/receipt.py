"""Replay-bound deterministic receipts for development-only V3 fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Sequence, Set

from .actor import canonical_json, canonical_json_bytes
from .fixtures import DEV_ONLY_STATUS, PUBLIC_TOOL_NAMES, CHECKER_GRAPH
from .runner import DEFAULT_POLICY_SPECS, experiment_as_dict, run_budget_sweep


RECEIPT_SCHEMA = "adaptive-revalidation-receipt-v3"
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
ZERO_CALL_FIELDS = (
    "model_calls",
    "judge_calls",
    "network_calls",
    "database_calls",
    "training_calls",
)
RESULT_SECTIONS = (
    "budget_policy_aggregate",
    "budgets",
    "capability_boundary",
    "cost_action_loss_frontier",
    "evidence_boundary",
    "evaluator_only_upper_bounds",
    "family_count",
    "paired_policy_comparison",
    "policy_aggregate",
    "policy_results",
    "semantic_label_policy",
)
REPLAY_HASH_SECTIONS = (
    "budget_policy_aggregate",
    "cost_action_loss_frontier",
    "evaluator_only_upper_bounds",
    "paired_policy_comparison",
    "policy_aggregate",
    "policy_results",
)


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


def recompute_result_payload() -> Mapping[str, Any]:
    """Replay all budgets and return the canonical receipt result sections."""
    result = experiment_as_dict(run_budget_sweep())
    return {section: result[section] for section in RESULT_SECTIONS}


def _result_hashes(result: Mapping[str, Any]) -> Mapping[str, str]:
    return {
        section: hashlib.sha256(canonical_json_bytes(result[section])).hexdigest()
        for section in REPLAY_HASH_SECTIONS
    }


def _validate_test_summary(test_summary: Mapping[str, Any]) -> None:
    expected_fields = {
        "command",
        "exit_code",
        "passed",
        "failed",
        "skipped",
        "status",
    }
    if set(test_summary) != expected_fields:
        raise ValueError("RECEIPT_TEST_SUMMARY_FIELDS_MISMATCH")
    command = test_summary["command"]
    if not isinstance(command, str) or not command.strip():
        raise ValueError("RECEIPT_TEST_COMMAND_INVALID")
    if "adaptive_revalidation_v3" not in command:
        raise ValueError("RECEIPT_TEST_COMMAND_WRONG_PACKAGE")
    numeric = {
        name: test_summary[name]
        for name in ("exit_code", "passed", "failed", "skipped")
    }
    if any(isinstance(value, bool) or not isinstance(value, int) for value in numeric.values()):
        raise ValueError("RECEIPT_TEST_COUNT_NOT_INTEGER")
    if numeric["exit_code"] < 0:
        raise ValueError("RECEIPT_TEST_EXIT_CODE_NEGATIVE")
    if any(numeric[name] < 0 for name in ("passed", "failed", "skipped")):
        raise ValueError("RECEIPT_TEST_COUNT_NEGATIVE")
    if numeric["passed"] + numeric["failed"] + numeric["skipped"] <= 0:
        raise ValueError("RECEIPT_TEST_SUMMARY_EMPTY")
    expected_status = (
        "PASS" if numeric["exit_code"] == 0 and numeric["failed"] == 0 else "FAIL"
    )
    if test_summary["status"] != expected_status:
        raise ValueError("RECEIPT_TEST_STATUS_INCONSISTENT")


def _validate_zero_calls(payload: Mapping[str, Any]) -> None:
    accounting = payload.get("zero_call_accounting")
    if not isinstance(accounting, dict) or set(accounting) != set(ZERO_CALL_FIELDS):
        raise ValueError("RECEIPT_ZERO_CALL_FIELDS_MISMATCH")
    for field in ZERO_CALL_FIELDS:
        value = accounting[field]
        if isinstance(value, bool) or not isinstance(value, int) or value != 0:
            raise ValueError("RECEIPT_ZERO_CALL_ACCOUNTING_NONZERO", field)
    claims = payload.get("claims")
    expected_claims = {
        "database_calls": 0,
        "external_task_performance": False,
        "judge_calls": 0,
        "model_calls": 0,
        "network_calls": 0,
        "production_behavior": False,
        "training_calls": 0,
    }
    if claims != expected_claims:
        raise ValueError("RECEIPT_CLAIMS_MISMATCH")


def _validate_result_contract(result: Mapping[str, Any]) -> None:
    policy_results = result.get("policy_results")
    if not isinstance(policy_results, list) or not policy_results:
        raise ValueError("RECEIPT_POLICY_RESULTS_EMPTY")
    expected_keys = set()
    patterns = {
        "scenario_id": re.compile(r"^S[0-9a-f]{12}$"),
        "node_id": re.compile(r"^N[0-9a-f]{12}$"),
        "output_id": re.compile(r"^O[0-9a-f]{12}$"),
        "change_id": re.compile(r"^C[0-9a-f]{12}$"),
    }
    for episode in policy_results:
        metrics = episode.get("metrics", {})
        if set(metrics) != REQUIRED_METRICS:
            raise ValueError("RECEIPT_REQUIRED_METRIC_MISMATCH")
        scenario_id = str(episode.get("scenario_id", ""))
        if not patterns["scenario_id"].fullmatch(scenario_id):
            raise ValueError("RECEIPT_SCENARIO_ID_NOT_OPAQUE")
        query_budget = episode.get("query_budget")
        if isinstance(query_budget, bool) or not isinstance(query_budget, int):
            raise ValueError("RECEIPT_QUERY_BUDGET_NOT_INTEGER")
        if not 0 <= query_budget <= 9:
            raise ValueError("RECEIPT_QUERY_BUDGET_OUTSIDE_SWEEP")
        if metrics["query_cost"] > query_budget:
            raise ValueError("RECEIPT_QUERY_COST_EXCEEDS_BUDGET")
        actor_input = episode.get("evidence", {}).get("actor_input", {})
        if actor_input.get("scenario_id") != scenario_id:
            raise ValueError("RECEIPT_ACTOR_SCENARIO_MISMATCH")
        for node_id in actor_input.get("node_ids", []):
            if not patterns["node_id"].fullmatch(str(node_id)):
                raise ValueError("RECEIPT_NODE_ID_NOT_OPAQUE")
        for output_id in actor_input.get("output_ids", []):
            if not patterns["output_id"].fullmatch(str(output_id)):
                raise ValueError("RECEIPT_OUTPUT_ID_NOT_OPAQUE")
        for change in actor_input.get("changes", []):
            if not patterns["change_id"].fullmatch(str(change.get("change_id", ""))):
                raise ValueError("RECEIPT_CHANGE_ID_NOT_OPAQUE")
            if not patterns["node_id"].fullmatch(str(change.get("node_id", ""))):
                raise ValueError("RECEIPT_CHANGE_NODE_ID_NOT_OPAQUE")
        actor_text = canonical_json(actor_input).lower()
        for forbidden in (
            "gold",
            "hidden",
            "trace",
            "oracle",
            "before_value",
            "after_value",
            "delta",
            "visible_dependencies",
            "before_success_snapshot",
            "post_source_values",
        ):
            if forbidden in actor_text:
                raise ValueError("RECEIPT_POLICY_SERIALIZATION_LEAK", forbidden)
        key = (query_budget, scenario_id, episode.get("policy"))
        if key in expected_keys:
            raise ValueError("RECEIPT_DUPLICATE_POLICY_RESULT", key)
        expected_keys.add(key)
    if len(policy_results) != 450:
        raise ValueError("RECEIPT_POLICY_EPISODE_COUNT_MISMATCH")
    if result.get("budgets") != list(range(10)):
        raise ValueError("RECEIPT_BUDGET_SWEEP_MISMATCH")
    if result.get("family_count") != 9:
        raise ValueError("RECEIPT_FAMILY_COUNT_MISMATCH")
    boundary = result.get("capability_boundary", {})
    if boundary.get("policy_execution") != "spawned_process_rpc":
        raise ValueError("RECEIPT_POLICY_BOUNDARY_MISMATCH")
    if boundary.get("actor_input_encoding") != "canonical_json":
        raise ValueError("RECEIPT_ACTOR_ENCODING_MISMATCH")
    if tuple(boundary.get("policy_public_tools", ())) != PUBLIC_TOOL_NAMES:
        raise ValueError("RECEIPT_POLICY_TOOL_CONTRACT_MISMATCH")
    if result.get("evidence_boundary") != DEV_ONLY_STATUS:
        raise ValueError("RECEIPT_EVIDENCE_BOUNDARY_MISMATCH")
    upper_bounds = result.get("evaluator_only_upper_bounds", {})
    if upper_bounds.get("policy_eligible") is not False:
        raise ValueError("RECEIPT_UPPER_BOUND_POLICY_LEAK")


def build_receipt(
    root: Path,
    test_command: str,
    test_exit_code: int,
    test_passed: int,
    test_failed: int,
    test_skipped: int,
) -> Mapping[str, Any]:
    """Build a receipt from a fresh isolated-process budget-sweep replay."""
    result = recompute_result_payload()
    test_summary = {
        "command": test_command,
        "exit_code": int(test_exit_code),
        "failed": int(test_failed),
        "passed": int(test_passed),
        "skipped": int(test_skipped),
        "status": "PASS" if test_exit_code == 0 and test_failed == 0 else "FAIL",
    }
    _validate_test_summary(test_summary)
    _validate_result_contract(result)
    payload: Dict[str, Any] = {
        "receipt_schema": RECEIPT_SCHEMA,
        "status": DEV_ONLY_STATUS,
        "claims": {
            "database_calls": 0,
            "external_task_performance": False,
            "judge_calls": 0,
            "model_calls": 0,
            "network_calls": 0,
            "production_behavior": False,
            "training_calls": 0,
        },
        "zero_call_accounting": {field: 0 for field in ZERO_CALL_FIELDS},
        "environment_contract": {
            "actor_id_namespaces": ["S", "C", "N", "O"],
            "budget_sweep": list(range(10)),
            "executable_node_count": len(CHECKER_GRAPH.node_ids),
            "output_count": len(CHECKER_GRAPH.output_ids),
            "policy_capability_boundary": "spawned_process_rpc",
            "public_tools": list(PUBLIC_TOOL_NAMES),
            "query_cost_unit": 1,
            "query_policy_kinds": [
                spec.policy_kind.value for spec in DEFAULT_POLICY_SPECS
            ],
        },
        "fixtures": {
            "families": sorted(
                {episode["scenario_family"] for episode in result["policy_results"]}
            ),
            "path": "fixtures/scenarios.json",
            "scenario_count": len(
                {episode["scenario_id"] for episode in result["policy_results"]}
            ),
            "status": DEV_ONLY_STATUS,
        },
        "test_summary": test_summary,
        "source_hashes": dict(collect_source_hashes(root)),
        "source_hash_algorithm": "sha256",
    }
    payload.update(result)
    payload["replay_hashes"] = _result_hashes(result)
    payload["result_payload_sha256"] = hashlib.sha256(
        canonical_json_bytes(result)
    ).hexdigest()
    serialized_replay = (
        json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    payload["serialized_replay_sha256"] = hashlib.sha256(
        serialized_replay.encode("utf-8")
    ).hexdigest()
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
    """Recompute results and reject source, result, and summary tampering."""
    root = root.resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("receipt_schema") != RECEIPT_SCHEMA:
        raise ValueError("RECEIPT_SCHEMA_MISMATCH")
    if payload.get("status") != DEV_ONLY_STATUS:
        raise ValueError("RECEIPT_STATUS_MISMATCH")
    _validate_zero_calls(payload)
    _validate_test_summary(payload.get("test_summary", {}))

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

    recomputed = recompute_result_payload()
    for section in RESULT_SECTIONS:
        if canonical_json(payload.get(section)) != canonical_json(recomputed[section]):
            raise ValueError("RECEIPT_RESULT_PAYLOAD_TAMPERING", section)
    _validate_result_contract(payload)
    expected_result_hash = hashlib.sha256(canonical_json_bytes(recomputed)).hexdigest()
    if payload.get("result_payload_sha256") != expected_result_hash:
        raise ValueError("RECEIPT_RESULT_HASH_MISMATCH")
    expected_replay_hashes = _result_hashes(recomputed)
    if payload.get("replay_hashes") != expected_replay_hashes:
        raise ValueError("RECEIPT_REPLAY_HASH_MISMATCH")
    serialized_replay = (
        json.dumps(
            recomputed,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    expected_serialized_replay_hash = hashlib.sha256(
        serialized_replay.encode("utf-8")
    ).hexdigest()
    if payload.get("serialized_replay_sha256") != expected_serialized_replay_hash:
        raise ValueError("RECEIPT_SERIALIZED_REPLAY_HASH_MISMATCH")

    policy_results = payload["policy_results"]
    return {
        "budgets": payload["budgets"],
        "families": payload["family_count"],
        "policy_episodes": len(policy_results),
        "receipt_sha256": _sha256(path),
        "source_files": len(current_hashes),
        "status": "PASS",
    }


def receipt_hash(path: Path) -> str:
    """Return the SHA-256 of a receipt file."""
    return _sha256(path)
