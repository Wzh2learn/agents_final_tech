#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/home/testuser/wzh/projects/agents_final_tech")
TASK_PROMPT_SOURCE = REPO_ROOT / "research/harness_rsi_v1/runs/T5/_dispatch/loop_a_prompt_t5_v3.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_id(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load_validator(run_root: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("t5_selfcheck_validator", run_root / "caller_validator.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load caller validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    output = Path(args.output).resolve()
    if output == run_root or run_root in output.parents:
        raise SystemExit("self-check output must be outside the delivered run tree")
    if output.exists():
        raise SystemExit("refuse to overwrite self-check output")
    checks: list[dict[str, Any]] = []

    def check(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "evidence": evidence})

    json_paths = sorted(run_root.rglob("*.json"))
    json_failures = []
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            json_failures.append({"path": path.relative_to(run_root).as_posix(), "error": str(exc)})
    check("JSON_PARSE", not json_failures, {"checked": len(json_paths), "failures": json_failures})

    manifest = json.loads((run_root / "artifacts_manifest.json").read_text(encoding="utf-8"))
    manifest_failures = []
    for artifact in manifest["artifacts"]:
        path = run_root / artifact["relative_path"]
        actual = {"bytes": path.stat().st_size, "sha256": sha256_file(path), "mode": format(path.stat().st_mode, "o")}
        if any(actual[key] != artifact[key] for key in actual):
            manifest_failures.append({"relative_path": artifact["relative_path"], "actual": actual, "declared": artifact})
    expected_files = {artifact["relative_path"] for artifact in manifest["artifacts"]} | {"artifacts_manifest.json"}
    actual_files = {path.relative_to(run_root).as_posix() for path in run_root.rglob("*") if path.is_file()}
    check("MANIFEST_45_OF_45", manifest["artifact_count"] == 45 and len(manifest["artifacts"]) == 45 and not manifest_failures and expected_files == actual_files, {"declared": manifest["artifact_count"], "checked": len(manifest["artifacts"]), "failures": manifest_failures, "missing": sorted(expected_files - actual_files), "extra": sorted(actual_files - expected_files)})

    validator = load_validator(run_root)
    interfaces_hash = sha256_file(run_root / "recipe_interfaces.json")
    operations_hash = sha256_file(run_root / "registered_operations.json")
    registry = json.loads((run_root / "registered_operations.json").read_text(encoding="utf-8"))
    target_rows = [{"op_id": item["op_id"], "declared": item["target"]["git_blob_id"], "actual": git_blob_id(Path(item["target"]["path"]))} for item in registry["operations"]]
    check("NEW1_IDENTITY_PINS", interfaces_hash == validator.INTERFACES_SHA256 and operations_hash == validator.OPERATIONS_SHA256 and all(row["declared"] == row["actual"] for row in target_rows), {"interfaces_sha256": interfaces_hash, "operations_sha256": operations_hash, "targets": target_rows})

    precheck = json.loads((run_root / "recipe_fixtures/valid_precheck_call.json").read_text(encoding="utf-8"))
    definitions = json.loads((run_root / "recipe_fixtures/probe_definitions.json").read_text(encoding="utf-8"))
    by_case = {item["case_id"]: item for item in definitions["cases"]}
    check("REPLAY_STABLE_TIME", precheck["operations"][0]["parameters"]["max_tick_age_minutes"] == 0 and by_case["P09-PRECHECK-BOUNDED-TICK-AGE-60"].get("runtime_tick") is True and not (run_root / "scratch/prepare_runtime_fixtures.py").exists(), {"p01_max_tick_age_minutes": precheck["operations"][0]["parameters"]["max_tick_age_minutes"], "p09_runtime_tick": by_case["P09-PRECHECK-BOUNDED-TICK-AGE-60"].get("runtime_tick"), "in_run_prepare_script": False})

    replay = json.loads((run_root / "scratch/replay/replay_summary.json").read_text(encoding="utf-8"))
    replay_rounds = replay["current_tree"]["rounds"] + replay["fresh_delivery"]["rounds"]
    check("EMBEDDED_REPLAY_EVIDENCE", replay["passed"] and replay["prerequisites"] == "NONE" and replay["delivery_tree_read_only"] and len(replay_rounds) == 4 and all(item["record_count"] == 23 and item["exit_code"] == 0 for item in replay_rounds), replay)

    adversarial = json.loads((run_root / "scratch/new1_trust_boundary.json").read_text(encoding="utf-8"))
    full_failure = json.loads((run_root / "scratch/full_matrix_failure_evidence.json").read_text(encoding="utf-8"))
    check("ADVISORY_FOLDING", adversarial["passed"] and full_failure["new2_full_matrix_on_failure"]["passed"], {"new1": adversarial, "new2": full_failure["new2_full_matrix_on_failure"]})

    guard_rows = []
    for path in sorted(run_root.rglob("*.md")):
        completed = subprocess.run(["python3", str(REPO_ROOT / "scripts/graph/hooks/summary_recompute_guard.py"), "check", str(path)], text=True, capture_output=True, check=False)
        guard_rows.append({"relative_path": path.relative_to(run_root).as_posix(), "rc": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    check("G1_ALL_MARKDOWN", all(row["rc"] == 0 for row in guard_rows), guard_rows)

    prompt_match = (run_root / "TASK_PROMPT.md").read_bytes() == TASK_PROMPT_SOURCE.read_bytes()
    check("TASK_PROMPT_VERBATIM", prompt_match, {"source": str(TASK_PROMPT_SOURCE), "sha256": sha256_file(run_root / "TASK_PROMPT.md")})

    t4_evidence = json.loads((run_root / "scratch/t4_consumption_evidence.json").read_text(encoding="utf-8"))
    check("T4_CASE_LEVEL_CONSUMPTION", t4_evidence["forbidden_field_occurrences"] == 0 and t4_evidence["consumption_policy"] == "CASE_LEVEL_ONLY", t4_evidence)

    receipt = json.loads((run_root / "receipt.json").read_text(encoding="utf-8"))
    chain = receipt["supersedes"]["review_chain"]
    usage = receipt["usage"]
    check("RECEIPT_CHAIN_AND_B0", [item["review_id"] for item in chain] == ["T5R-01", "T5R-02"] and all(item["decision"] == "REJECTED" for item in chain) and all(usage[key] == 0 for key in ["additional_cheap_requests_actual", "additional_strong_requests_actual", "orchestrated_model_requests", "automatic_retries", "network_calls", "remote_calls", "production_calls", "database_calls", "training_calls", "daemon_calls", "loop_b_calls"]) and usage["execution_chat_usage"] == "UNRESOLVED", {"chain": chain, "usage": usage})

    check("THREE_AXES", receipt["execution_status"] == "DELIVERED" and receipt["acceptance_status"] == "UNREVIEWED" and receipt["activation_status"] == "NOT_ENABLED", {key: receipt[key] for key in ["execution_status", "acceptance_status", "activation_status"]})

    result = {
        "schema": "jinrong_t5_self_check_result_v1",
        "run_id": run_root.name,
        "overall": "CONTRACT_PASS" if all(item["status"] == "PASS" for item in checks) else "CONTRACT_FAIL",
        "scope": "Current delivered T5 v3 run bytes only; deterministic local contract, identity, replay-evidence, G1 and B0 checks. No scientific, production, database, model, daemon, formal-run or independent-review claim.",
        "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"overall": result["overall"], "checks": {item["check_id"]: item["status"] for item in checks}}, ensure_ascii=False, sort_keys=True))
    return 0 if result["overall"] == "CONTRACT_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
