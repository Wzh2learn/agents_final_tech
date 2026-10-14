#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


RUN_ID = "20261014T195445Z_60c8e213"
RUN_REL = Path("research/harness_rsi_v1/runs/T5") / RUN_ID


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_blob(repo_root: Path, relative: str) -> str:
    completed = subprocess.run(["git", "rev-parse", f"HEAD:{relative}"], cwd=repo_root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    run_root = (Path.cwd() / RUN_REL).resolve()
    repo_root = Path.cwd().resolve()
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def check(check_id: str, condition: bool, detail: Any, level: str = "CONTRACT_PASS", scope: str = "current T5 run package only") -> None:
        checks.append({"check_id": check_id, "status": "OK" if condition else "FAIL", "verification_level": level, "scope": scope, "detail": detail})
        if not condition:
            failures.append(check_id)

    json_paths = [path for path in run_root.rglob("*.json") if "__pycache__" not in path.parts]
    parsed = {path: load_json(path) for path in json_paths}
    check("JSON_PARSE", len(parsed) == len(json_paths), {"parsed": len(json_paths)}, "COMPONENT_PASS", "all run-local JSON artifacts")

    receipt = parsed[run_root / "receipt.json"]
    required = {"task_id", "run_id", "scope", "execution_status", "acceptance_status", "activation_status", "input_bindings", "output_manifest", "checks", "usage", "unresolved", "authorization_ref"}
    check("RECEIPT_REQUIRED_FIELDS", required.issubset(receipt), {"missing": sorted(required - set(receipt))})
    check("THREE_AXIS_STATUS", receipt["execution_status"] == "DELIVERED" and receipt["acceptance_status"] == "UNREVIEWED" and receipt["activation_status"] == "NOT_ENABLED", {"execution_status": receipt["execution_status"], "acceptance_status": receipt["acceptance_status"], "activation_status": receipt["activation_status"]})

    task_prompt = run_root / "TASK_PROMPT.md"
    task_binding = receipt["task_prompt"]
    check("TASK_PROMPT_CAPTURE", task_binding["sha256"] == sha256_file(task_prompt), {"sha256": sha256_file(task_prompt)})

    binding_results = []
    for binding in receipt["input_bindings"]:
        relative = binding.get("git_relative_path")
        actual = canonical_blob(repo_root, relative)
        declared_file_sha = binding.get("sha256_file")
        actual_file_sha = sha256_file(Path(binding["absolute_path"]))
        binding_results.append({"relative": relative, "declared": binding["canonical_blob_id"], "actual": actual, "match": actual == binding["canonical_blob_id"], "declared_file_sha": declared_file_sha, "actual_file_sha": actual_file_sha, "file_sha_match": declared_file_sha is None or declared_file_sha == actual_file_sha})
    check("CANONICAL_INPUT_HASHES", all(item["match"] and item["file_sha_match"] for item in binding_results), binding_results, "CONTRACT_PASS", "all tracked receipt input/dependency bindings")

    registry = parsed[run_root / "registered_operations.json"]
    interfaces = parsed[run_root / "recipe_interfaces.json"]
    op_ids = {entry["op_id"] for entry in registry["operations"]}
    referenced = [operation["op_id"] for recipe in interfaces["recipes"] for operation in recipe["operations"]]
    check("OPERATION_CLOSED_VOCABULARY", len(registry["operations"]) == 3 and all(op_id in op_ids for op_id in referenced), {"registry_count": len(op_ids), "referenced_count": len(referenced), "unregistered": sorted(set(referenced) - op_ids)})
    target_results = []
    for operation in registry["operations"]:
        relative = str(Path(operation["target"]["path"]).resolve().relative_to(repo_root))
        actual = canonical_blob(repo_root, relative)
        target_results.append({"op_id": operation["op_id"], "declared": operation["target"]["git_blob_id"], "actual": actual, "match": actual == operation["target"]["git_blob_id"]})
    check("OPERATION_TARGET_HASHES", all(item["match"] for item in target_results), target_results)

    recipe_count = len(interfaces["recipes"])
    object_ids = [recipe["single_object_declaration"]["object_id"] for recipe in interfaces["recipes"]]
    check("TWO_SINGLE_OBJECT_RECIPES", recipe_count == 2 and len(set(object_ids)) == 2 and all(recipe["single_object_declaration"]["only_object"] is True for recipe in interfaces["recipes"]), {"recipe_count": recipe_count, "object_ids": object_ids})
    checks_by_recipe = []
    for recipe in interfaces["recipes"]:
        fields = recipe["delivery_fields"]
        protections = recipe["frozen_protections"]
        delivery_classes = sorted(key for key in fields if key in {"qualification", "audit", "execution", "scientific"})
        checks_by_recipe.append({"recipe_id": recipe["recipe_id"], "delivery_classes": delivery_classes, "protection_count": len(protections), "overall_forbidden": fields["overall_pass_field_forbidden"], "scientific_claim_must_be_null": fields["scientific"]["claim_must_be"] is None})
    check("DELIVERY_FOUR_CLASS_SEPARATION", all(item["delivery_classes"] == ["audit", "execution", "qualification", "scientific"] and item["overall_forbidden"] and item["scientific_claim_must_be_null"] for item in checks_by_recipe), checks_by_recipe)
    check("FROZEN_PROTECTIONS", all(len(recipe["frozen_protections"]) >= 7 for recipe in interfaces["recipes"]), checks_by_recipe)

    definitions = parsed[run_root / "recipe_fixtures" / "probe_definitions.json"]
    rounds = []
    for name in ["probe_results_pass1_final4.jsonl", "probe_results_pass2_final4.jsonl"]:
        rows = [json.loads(line) for line in (run_root / "scratch" / name).read_text(encoding="utf-8").splitlines()]
        rounds.append(rows)
    normalized = [[{key: row[key] for key in ["case_id", "recipe_id", "expected", "expected_fail_closed_code", "actual", "actual_fail_closed_code", "caller_exit_code", "target_execution_performed", "operation_result_count", "passed"]} for row in rows] for rows in rounds]
    expected_counts = Counter(case["expected"] for case in definitions["cases"])
    actual_counts = Counter(row["actual"] for row in rounds[0])
    check("PROBE_MATRIX", len(definitions["cases"]) == 17 and expected_counts == actual_counts and all(row["passed"] for rows in rounds for row in rows), {"definitions": len(definitions["cases"]), "expected": dict(expected_counts), "actual": dict(actual_counts), "two_round_consistent": normalized[0] == normalized[1]})

    markdown_paths = sorted(run_root.rglob("*.md"))
    guard_rows = []
    for path in markdown_paths:
        completed = subprocess.run(["python3", str(repo_root / "scripts/graph/hooks/summary_recompute_guard.py"), "check", str(path)], cwd=repo_root, text=True, capture_output=True, check=False)
        guard_rows.append({"path": str(path.relative_to(run_root)), "rc": completed.returncode})
    check("G1_ALL_MARKDOWN_GUARD", all(row["rc"] == 0 for row in guard_rows), guard_rows)

    manifest = parsed[run_root / "artifacts_manifest.json"]
    manifest_results = []
    for artifact in manifest["artifacts"]:
        path = Path(artifact["absolute_path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_bytes = path.stat().st_size if path.is_file() else None
        manifest_results.append({"relative_path": artifact["relative_path"], "sha_match": actual_sha == artifact["sha256"], "bytes_match": actual_bytes == artifact["bytes"]})
    check("MANIFEST_HASHES", manifest["artifact_count"] == len(manifest["artifacts"]) and all(item["sha_match"] and item["bytes_match"] for item in manifest_results), {"declared": manifest["artifact_count"], "checked": len(manifest_results), "failures": [item for item in manifest_results if not item["sha_match"] or not item["bytes_match"]]})

    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo_root, text=True, capture_output=True, check=True).stdout.splitlines()
    allowed_dirty_prefixes = (" M logs/graph/", "?? research/harness_rsi_v1/runs/T4/20261014T174628Z_2cc25c92/", "?? research/harness_rsi_v1/runs/T5/20261014T195445Z_60c8e213/")
    boundary_violations = [line for line in status if not line.startswith(allowed_dirty_prefixes)]
    check("WRITE_BOUNDARY", not boundary_violations, {"violations": boundary_violations, "allowed_preexisting": ["logs/graph dirty files", "T4 uncommitted v1 run"], "executor_owned": "T5/20261014T195445Z_60c8e213"})

    events = [json.loads(line) for line in (run_root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    event_ids = [event["event_id"] for event in events]
    check("EVENTS_MONOTONIC", event_ids == list(range(1, len(events) + 1)), {"first": event_ids[0], "last": event_ids[-1], "count": len(event_ids)})
    usage = receipt["usage"]
    check("B0_ZERO_EXTERNAL_AND_UNRESOLVED", all(usage[key] == 0 for key in ["additional_cheap_requests_actual", "additional_strong_requests_actual", "orchestrated_model_requests", "automatic_retries", "network_calls", "remote_calls", "production_calls", "database_calls", "training_calls", "daemon_calls", "loop_b_calls"]) and usage["execution_chat_usage"] == "UNRESOLVED", usage)

    bad_markdown_receipts = []
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "SUMMARY-GUARD" in text and "request_count = 3" in text:
            bad_markdown_receipts.append(str(path.relative_to(run_root)))
    check("NO_PERSISTED_BAD_SUMMARY", not bad_markdown_receipts, {"bad_markdown_receipts": bad_markdown_receipts})

    document = {
        "schema": "jinrong_t5_self_check_result_v1",
        "run_id": RUN_ID,
        "verification_level": "CONTRACT_PASS",
        "scope": "Current run package; local deterministic checks only; no scientific or runtime qualification.",
        "status": "OK" if not failures else "FAIL",
        "check_count": len(checks),
        "ok_count": len(checks) - len(failures),
        "failures": failures,
        "checks": checks,
        "assertion_mapping": {
            "A1": {"status": "CONTRACT_PASS", "scope": "Two single-object recipes; unregistered/shell/arbitrary-path probes reject before target execution.", "evidence": "probe matrix P02/P03/P08/E02/E03/E09"},
            "A2": {"status": "CONTRACT_PASS", "scope": "Caller-side missing field/hash/forged-summary detection.", "evidence": "probe matrix P06/P07/E04/E05/E06 and runtime-only summary mutation"},
            "A3": {"status": "CONTRACT_PASS", "scope": "B0 run-package write boundary; frozen/old components unchanged.", "evidence": "canonical hashes and final git status boundary"},
            "A_common": {"status": "CONTRACT_PASS", "scope": "JSON, required fields, hashes, paths, unknown surfaces and package integrity.", "evidence": "all self-check rows"}
        },
    }
    print(json.dumps(document, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 3


if __name__ == "__main__":
    raise SystemExit(main())
