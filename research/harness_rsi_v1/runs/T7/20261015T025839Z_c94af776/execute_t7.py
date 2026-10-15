#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20261015T025839Z_c94af776"
PROTOCOL_FREEZE = "282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b"
T5_RUN_ID = "20261014T233742Z_cb132ce7"
T4_RUN_ID = "20261014T184810Z_c9dcfe0e"
T6_RUN_ID = "20261015T012906Z_b9bb8ca6"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def append_event(path: Path, event: str, **fields: Any) -> None:
    record = {"timestamp": utc_now(), "event": event, "task_id": "T7", "run_id": RUN_ID}
    record.update(fields)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def run_command(command: list[str], cwd: Path, environment: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    finished = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return {
        "command": shlex.join(command),
        "cwd": str(cwd),
        "started_at": started,
        "finished_at": finished,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def git_blob(repo_root: Path, relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative_path}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"canonical git blob lookup failed for {relative_path}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def import_validator(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("t7_t5_caller_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import T5 caller validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repo_root = Path("/home/testuser/wzh/projects/agents_final_tech").resolve()
    run_root = (repo_root / "research/harness_rsi_v1/runs/T7" / RUN_ID).resolve()
    if run_root.parent.name != "T7":
        raise RuntimeError("unexpected T7 run root")

    amendment_path = run_root / "candidate_amendment_A1.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment.get("amendment_status") != "COMPLETED_BEFORE_EVALUATION":
        raise RuntimeError("A-1 precondition is not completed")
    if amendment.get("evaluation_precondition_result", {}).get("candidate_executable_for_new_absence_policy") is not False:
        raise RuntimeError("A-1 executable boundary mismatch")

    events_path = run_root / "events.jsonl"
    scratch_root = run_root / "scratch"
    tmp_root = scratch_root / "tmp"
    for path in (scratch_root, tmp_root):
        path.mkdir(parents=True, exist_ok=True)
    append_event(events_path, "run_started", write_scope=str(run_root), model_calls=0)
    append_event(events_path, "a1_precondition_completed_before_evaluation", amendment_id="A-1", candidate_executable=False)
    append_event(events_path, "repair_attempt", attempt=7, result="FAILED_DURING_A1_DIAGNOSTIC_BEFORE_CANDIDATE_EVALUATION", retained="repair_record.json")

    t1_path = repo_root / "research/harness_rsi_v1/runs/T1/20261014T141004Z_2647a7e1/incidents.jsonl"
    t4_root = repo_root / "research/harness_rsi_v1/runs/T4" / T4_RUN_ID
    t5_root = repo_root / "research/harness_rsi_v1/runs/T5" / T5_RUN_ID
    t6_root = repo_root / "research/harness_rsi_v1/runs/T6" / T6_RUN_ID
    t6_review_root = repo_root / "research/harness_rsi_v1/reviews/T6R-01"

    input_paths = [
        repo_root / "research/harness_rsi_v1/cards/T7.md",
        repo_root / "research/harness_rsi_v1/contracts/protocol.json",
        repo_root / "research/harness_rsi_v1/contracts/authority_map.json",
        repo_root / "research/harness_rsi_v1/contracts/execution_policy.md",
        repo_root / "research/harness_rsi_v1/contracts/budget_profiles.json",
        repo_root / "research/harness_rsi_v1/contracts/schemas.json",
        repo_root / "research/harness_rsi_v1/evaluation/reliability_spec.md",
        t1_path,
        t4_root / "baseline.json",
        t4_root / "baseline_recipe.json",
        t4_root / "receipt.json",
        t5_root / "registered_operations.json",
        t5_root / "recipe_interfaces.json",
        t5_root / "caller_validator.py",
        t5_root / "recipe_fixtures/valid_delivery_call.json",
        t5_root / "receipt.json",
        t6_root / "candidate_packages/cand-d44c49dec4d95741/candidate.json",
        t6_root / "receipt.json",
        t6_review_root / "review_receipt.json",
        amendment_path,
    ]
    input_bindings = []
    for path in input_paths:
        relative_path = relative(path, repo_root)
        if path.parent == run_root or run_root in path.parents:
            input_bindings.append(
                {
                    "path": relative_path,
                    "absolute_path": str(path),
                    "canonical_git_blob_id": None,
                    "hash_status": "RUN_LOCAL_UNTRACKED_AT_EXECUTION",
                    "sha256_file": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "git_rev_parse_exit_code": None,
                    "note": "New T7-run artifact; canonical HEAD lookup is unavailable until a later closer commits it.",
                }
            )
            continue
        input_bindings.append(
            {
                "path": relative_path,
                "absolute_path": str(path),
                "canonical_git_blob_id": git_blob(repo_root, relative_path),
                "hash_status": "TRACKED_AT_CURRENT_HEAD",
                "sha256_file": sha256_file(path),
                "git_rev_parse_exit_code": 0,
            }
        )

    parent_diff_checks = []
    for label, commit, path in [
        ("T4-v2", "579a8cae7310ed55e969a8a09ed4ee39a8f8a8cc", t4_root),
        ("T5-v3", "115f396af6ea461c156d91ad9148414387724eb3", t5_root),
        ("T6-v1", "ef5e84edbd4fcd35cc287316c0e994cf72f6faa4", t6_root),
    ]:
        completed = subprocess.run(
            ["git", "diff", "--quiet", commit, "--", relative(path, repo_root)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        parent_diff_checks.append(
            {
                "parent": label,
                "commit": commit,
                "path": relative(path, repo_root),
                "exit_code": completed.returncode,
                "unchanged_at_current_head": completed.returncode == 0,
            }
        )
    if not all(item["unchanged_at_current_head"] for item in parent_diff_checks):
        raise RuntimeError("parent package drift detected")

    incidents = [json.loads(line) for line in t1_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(incidents) != 16:
        raise RuntimeError(f"T1 v3 case count is {len(incidents)}, expected 16")
    baseline = json.loads((t4_root / "baseline.json").read_text(encoding="utf-8"))
    cases = baseline["cases"]
    if len(cases) != 16:
        raise RuntimeError(f"T4 baseline case count is {len(cases)}, expected 16")
    incident_by_id = {item["incident_id"]: item for item in incidents}
    case_identity_matches = []
    for case in cases:
        source = incident_by_id.get(case["case_id"])
        fields = ["title", "expected_category", "artifact_level", "applicability", "legal_control_design"]
        case_identity_matches.append(
            {
                "case_id": case["case_id"],
                "present_in_t1_v3": source is not None,
                "matched_fields": fields if source is not None else [],
                "all_matched": source is not None and all(case[field] == source[field] for field in fields),
            }
        )
    if not all(item["all_matched"] for item in case_identity_matches):
        raise RuntimeError("T1 v3 and T4 case identity mismatch")

    write_json(
        run_root / "identity_bindings.json",
        {
            "schema": "jinrong_t7_identity_bindings_v1",
            "run_id": RUN_ID,
            "protocol_freeze_sha256": PROTOCOL_FREEZE,
            "parent_diff_checks": parent_diff_checks,
            "t4_baseline_content_group_sha256": "b78bce332bd9433d44b2e79d8434949fadf773496c1c806872a103acff5e16ad",
            "t5_parent_content_group_sha256": "4f7d7af42ee6a1364e01c7b0e5213108025c9e69f1f212b65b11da03d3aa2f54",
            "case_set": {
                "t1_v3_case_count": 16,
                "t4_baseline_case_count": 16,
                "identity_field_matches": case_identity_matches,
            },
            "evaluator_identity": {
                "baseline": "T4 v2 read-only adapters plus T5 v3 caller validator",
                "candidate": "T6 cand-d44c49dec4d95741 plus T7 A-1 amendment; no new executable operation",
                "independent_scientific_evaluator": "NOT_PRESENT",
            },
            "environment_identity": {
                "runtime": "GB10 local shell / Python 3.12",
                "network": 0,
                "remote": 0,
                "production": 0,
                "database": 0,
                "model": 0,
                "daemon": 0,
                "loop_b": 0,
            },
            "input_bindings": input_bindings,
        },
    )
    append_event(events_path, "inputs_bound", input_count=len(input_bindings), t1_cases=16, t4_cases=16, parent_drift=0)

    baseline_log_root = scratch_root / "baseline_replay"
    baseline_log_root.mkdir(parents=True, exist_ok=True)
    replay_records = []
    check_index = 0
    environment = os.environ.copy()
    environment["TMPDIR"] = str(tmp_root)
    for replay_pass in (1, 2):
        for case in cases:
            for check in case.get("applicable_checks", []):
                check_index += 1
                tool = Path(check["tool"])
                adapter_relative = Path(check["adapter"])
                adapter = t4_root / adapter_relative
                fixture = case["fixture"]
                if check["tool"].endswith("dispatch_precheck.sh"):
                    args = [
                        "--watcher",
                        str(t4_root / "fixtures/dispatch/watcher.sh"),
                        "--tick-marker",
                        str(t4_root / fixture),
                    ]
                elif check["tool"].endswith("summary_recompute_guard.py") and check["result"] == "detected" and case["case_id"] in {"T1-INC-12", "T1-INC-13"}:
                    args = [str(t4_root / "fixtures/summary/effect_match.md")]
                elif check["tool"].endswith("summary_recompute_guard.py"):
                    summary_fixture = fixture.split(" and ", 1)[0]
                    args = ["check", str(t4_root / summary_fixture)]
                elif check["tool"].endswith("frozen_hashes.txt"):
                    args = [str(t4_root / "fixtures/frozen/stale.md5")]
                else:
                    raise RuntimeError(f"unmapped replay tool: {tool}")
                result = run_command(["/usr/bin/bash", str(adapter), *args], repo_root, environment)
                log_path = baseline_log_root / f"pass{replay_pass}_{check_index:02d}_{case['case_id']}.log"
                log_path.write_text(
                    "command={command}\ncwd={cwd}\nstarted_at={started_at}\nfinished_at={finished_at}\nexit_code={exit_code}\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n".format(**result),
                    encoding="utf-8",
                    newline="\n",
                )
                if "summary_guard_derive" in check["adapter"]:
                    match = re.search(r"^guard_rc=([0-9]+)$", result["stdout"], re.MULTILINE)
                    target_exit_code = int(match.group(1)) if match else None
                    derived_removed = "derived_md_removed=true" in result["stdout"]
                else:
                    target_exit_code = result["exit_code"]
                    derived_removed = None
                expected_exit_code = check["exit_codes"][replay_pass - 1]
                replay_records.append(
                    {
                        "case_id": case["case_id"],
                        "check_tool": check["tool"],
                        "adapter": check["adapter"],
                        "replay_pass": replay_pass,
                        "expected_case_result": check["result"],
                        "expected_target_exit_code": expected_exit_code,
                        "observed_target_exit_code": target_exit_code,
                        "adapter_exit_code": result["exit_code"],
                        "derived_removed": derived_removed,
                        "log_path": relative(log_path, run_root),
                        "match": target_exit_code == expected_exit_code,
                    }
                )
    baseline_check_count = len(replay_records)
    if baseline_check_count != 22:
        raise RuntimeError(f"baseline check replay count is {baseline_check_count}, expected 22")
    if not all(item["match"] for item in replay_records):
        raise RuntimeError("T4 baseline replay changed")
    if not all(item["derived_removed"] is not False for item in replay_records):
        raise RuntimeError("runtime-derived mismatch evidence was not removed")

    diagnostic_root = scratch_root / "a1_diagnostic"
    diagnostic_root.mkdir(parents=True, exist_ok=True)
    summary_adapter = t4_root / "adapters/summary_guard_check_adapter.sh"
    diagnostic_records = []
    for classification, fixture_name in [
        ("MISSING_REQUIRED_EVIDENCE", "required_receipt_block_missing.md"),
        ("LEGAL_UNRESOLVED", "legal_unmeterable_usage_missing.md"),
    ]:
        fixture = run_root / "evaluation_fixtures" / fixture_name
        for replay_pass in (1, 2):
            result = run_command(["/usr/bin/bash", str(summary_adapter), "check", str(fixture)], repo_root, environment)
            log_path = diagnostic_root / f"{classification}_pass{replay_pass}.log"
            log_path.write_text(
                "command={command}\ncwd={cwd}\nstarted_at={started_at}\nfinished_at={finished_at}\nexit_code={exit_code}\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n".format(**result),
                encoding="utf-8",
                newline="\n",
            )
            diagnostic_records.append(
                {
                    "classification": classification,
                    "fixture": relative(fixture, run_root),
                    "fixture_sha256": sha256_file(fixture),
                    "replay_pass": replay_pass,
                    "baseline_target_exit_code": result["exit_code"],
                    "baseline_behavior": "SILENT_SKIP" if result["exit_code"] == 0 else "BLOCK",
                    "legal_unresolved_is_severe_defect": classification == "LEGAL_UNRESOLVED",
                    "log_path": relative(log_path, run_root),
                }
            )
    if not all(item["baseline_behavior"] == "SILENT_SKIP" for item in diagnostic_records):
        raise RuntimeError("A-1 diagnostic baseline behavior changed")

    original_candidate_path = t6_root / "candidate_packages/cand-d44c49dec4d95741/candidate.json"
    original_candidate = json.loads(original_candidate_path.read_text(encoding="utf-8"))
    amended_candidate = copy.deepcopy(original_candidate)
    amended_candidate["schema"] = "jinrong_t7_candidate_package_amended_v1"
    amended_candidate["amendment"] = {
        "amendment_id": "A-1",
        "record": "candidate_amendment_A1.json",
        "source_candidate_git_blob_id": git_blob(repo_root, relative(original_candidate_path, repo_root)),
        "source_candidate_sha256": sha256_file(original_candidate_path),
    }
    amended_candidate["identity"]["problem_family"] = amendment["after"]["problem_family"]
    amended_candidate["identity"]["problem_source"] = amendment["after"]["problem_source"]
    amended_candidate["selection_rationale"] = (
        "A-1 separates the observable missing-required-receipt guard behavior from T1-INC-14's legal metering UNRESOLVED. "
        "The source T6 candidate and T1 incident remain unchanged; this copy is T7-local and is not enabled."
    )
    for entry in amended_candidate["entries"]:
        if entry["entry_id"] == "E-03-ABSENT-BLOCK-REJECTION":
            entry["intent"] = amendment["after"]["e03_intent"]
            entry["parameterization"]["absence_classification"] = "MISSING_REQUIRED_EVIDENCE_ONLY"
            entry["parameterization"]["legal_unresolved_excluded"] = True
            entry["executable_under_t5_v3"] = False
    amended_candidate["six_gate_targets"]["severe_defect_miss"] = amendment["after"]["severe_defect_miss"]
    amended_candidate["six_gate_targets"]["legitimate_false_block"] = (
        "Legal UNRESOLVED must remain UNRESOLVED; no automatic BLOCK. Positive and mismatch controls must retain parent behavior."
    )
    amended_candidate["six_gate_targets"]["evidence_completeness"] = (
        "100% only if an authorized executable operation covers missing required evidence; otherwise NOT_EVALUABLE."
    )
    amended_candidate["evaluation_plan"]["design"] = (
        "Paired T4/T5 parent replay plus A-1 missing-required and legal-unresolved diagnostics; candidate counting requires executable registered behavior."
    )
    amended_candidate["evaluation_plan"]["primary_metric"] = amendment["after"]["primary_metric"]
    amended_candidate["evaluation_plan"]["stopping_rule"] = (
        "NO_PROMOTION if the required absence operation is not separately authorized/executable or any hard gate regresses."
    )
    amended_candidate["classification_policy"] = amendment["classification_policy"]
    amended_candidate["activation"] = {
        "enabled": False,
        "shared_registry_modified": False,
        "selection_set_accessed": False,
        "sealed_set_accessed": False,
    }
    write_json(run_root / "amended_candidate.json", amended_candidate)

    validator_path = t5_root / "caller_validator.py"
    validator = import_validator(validator_path)
    interfaces_path = t5_root / "recipe_interfaces.json"
    registry_path = t5_root / "registered_operations.json"
    interfaces = json.loads(interfaces_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    valid_call = json.loads((t5_root / "recipe_fixtures/valid_delivery_call.json").read_text(encoding="utf-8"))
    runtime_root = scratch_root / "t5_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)

    baseline_validator_result = validator.validate_call(copy.deepcopy(valid_call), interfaces, registry, t5_root, runtime_root)
    candidate_call = copy.deepcopy(valid_call)
    candidate_call["operations"].append(
        {
            "op_id": "OP-T4-R-SUMMARY-GUARD-CHECK",
            "parameters": {"markdown_path": "FUTURE_ENUM_receipt_block_absent.md"},
        }
    )
    candidate_fail_closed = None
    try:
        candidate_validator_result = validator.validate_call(candidate_call, interfaces, registry, t5_root, runtime_root)
    except validator.ContractError as exc:
        candidate_validator_result = {
            "validation_status": "REJECTED",
            "fail_closed_code": exc.code,
            "error_detail": exc.detail,
            "target_execution_performed": False,
        }
        candidate_fail_closed = exc.code

    write_json(
        scratch_root / "t5_baseline_validator_result.json",
        {
            "baseline_call_sha256": sha256_file(t5_root / "recipe_fixtures/valid_delivery_call.json"),
            "result": baseline_validator_result,
        },
    )
    write_json(
        scratch_root / "t5_candidate_validator_result.json",
        {
            "amended_candidate_sha256": sha256_file(run_root / "amended_candidate.json"),
            "future_operation_parameterization": "FUTURE_ENUM_receipt_block_absent.md",
            "result": candidate_validator_result,
            "counted_as_severe_defect_detection": False,
            "reason": "Fail-closed rejection proves missing registry support, not detection of the document's evidence defect.",
        },
    )

    write_json(
        run_root / "paired_replay.json",
        {
            "schema": "jinrong_t7_paired_replay_v1",
            "run_id": RUN_ID,
            "order": ["hard_gates", "benefits", "cost"],
            "identity_bound": True,
            "baseline": {
                "version": "T4-v2@579a8cae7310ed55e969a8a09ed4ee39a8f8a8cc / T5-v3@115f396af6ea461c156d91ad9148414387724eb3",
                "t4_case_count": 16,
                "t4_applicable_check_count_per_pass": 11,
                "t4_replay_passes": 2,
                "t4_replay_records": replay_records,
                "t4_replay_match_count": sum(1 for item in replay_records if item["match"]),
                "a1_diagnostic_records": diagnostic_records,
                "t5_validator_status": baseline_validator_result.get("validation_status"),
            },
            "candidate": {
                "version": "cand-d44c49dec4d95741 + T7 A-1 local amendment",
                "activation_enabled": False,
                "case_level_replay_status": "NOT_EVALUABLE",
                "case_level_reason": "The T5 v3 closed registry has no executable absent-required-receipt operation or path enum.",
                "t5_validator_status": candidate_validator_result.get("validation_status"),
                "t5_fail_closed_code": candidate_fail_closed or candidate_validator_result.get("fail_closed_code"),
                "counted_severe_defect_repair_count": 0,
                "legal_unresolved_counted_as_severe_defect": False,
            },
            "paired_results": {
                "baseline_required_missing_behavior": "SILENT_SKIP",
                "candidate_required_missing_behavior": "NOT_EVALUABLE",
                "baseline_legal_unresolved_behavior": "SILENT_KEEP_UNRESOLVED",
                "candidate_legal_unresolved_behavior": "NOT_EVALUABLE; must remain UNRESOLVED",
                "counted_repaired_misses": 0,
                "regressions_counted": 0,
                "benefit_judgment": "NOT_ESTABLISHED",
            },
            "unverified": [
                "Candidate behavior on the absence case because no authorized executable extension exists",
                "Selection-set behavior because selection_set is NOT_BUILT",
                "Sealed-set behavior because sealed access is NOT_APPLICABLE while the sealed set is not built",
            ],
        },
    )
    append_event(events_path, "paired_replay_completed", baseline_check_count=baseline_check_count, candidate_status="NOT_EVALUABLE", counted_repairs=0)

    old_paths = [
        t1_path,
        t4_root / "baseline.json",
        t4_root / "baseline_recipe.json",
        t4_root / "receipt.json",
        t5_root / "registered_operations.json",
        t5_root / "recipe_interfaces.json",
        t5_root / "caller_validator.py",
        t5_root / "receipt.json",
        t6_root / "candidate_packages/cand-d44c49dec4d95741/candidate.json",
        t6_root / "receipt.json",
        t6_review_root / "review_receipt.json",
    ]

    def snapshot(paths: list[Path]) -> dict[str, Any]:
        return {
            relative(path, repo_root): {
                "git_blob_id": git_blob(repo_root, relative(path, repo_root)),
                "sha256_file": sha256_file(path),
                "bytes": path.stat().st_size,
                "mode": oct(path.stat().st_mode & 0o777),
            }
            for path in paths
        }

    before_snapshot = snapshot(old_paths)
    rollback_root = run_root / "rollback_drill"
    parent_state_root = rollback_root / "restored_parent"
    parent_state_root.mkdir(parents=True, exist_ok=True)
    initial_state = {
        "state_version": "T7_LOCAL_CANDIDATE_AMENDMENT_ONLY",
        "active_candidate": "amended_candidate.json",
        "active_candidate_sha256": sha256_file(run_root / "amended_candidate.json"),
        "shared_activation": False,
    }
    write_json(rollback_root / "candidate_state.json", initial_state)
    for source in (registry_path, interfaces_path, validator_path):
        destination = parent_state_root / source.name
        destination.write_bytes(source.read_bytes())
        os.chmod(destination, source.stat().st_mode & 0o777)
    restored_state = {
        "state_version": "T5_V3_PARENT_RESTORED",
        "parent_commit": "115f396af6ea461c156d91ad9148414387724eb3",
        "active_candidate": None,
        "shared_activation": False,
        "restored_files": [
            {
                "path": relative(path, run_root),
                "source_path": relative(source, repo_root),
                "source_git_blob_id": git_blob(repo_root, relative(source, repo_root)),
                "sha256_file": sha256_file(path),
                "source_sha256_file": sha256_file(source),
                "bytes_equal": path.read_bytes() == source.read_bytes(),
                "mode_equal": (path.stat().st_mode & 0o777) == (source.stat().st_mode & 0o777),
            }
            for path, source in [
                (parent_state_root / "registered_operations.json", registry_path),
                (parent_state_root / "recipe_interfaces.json", interfaces_path),
                (parent_state_root / "caller_validator.py", validator_path),
            ]
        ],
    }
    write_json(rollback_root / "restored_state.json", restored_state)

    rollback_validator = import_validator(parent_state_root / "caller_validator.py")
    rollback_call_result = rollback_validator.validate_call(
        copy.deepcopy(valid_call),
        json.loads((parent_state_root / "recipe_interfaces.json").read_text(encoding="utf-8")),
        json.loads((parent_state_root / "registered_operations.json").read_text(encoding="utf-8")),
        t5_root,
        runtime_root,
    )
    after_snapshot = snapshot(old_paths)
    hashes_unchanged = before_snapshot == after_snapshot
    restored_exact = all(item["bytes_equal"] and item["mode_equal"] for item in restored_state["restored_files"])
    behavior_consistent = baseline_validator_result.get("validation_status") == rollback_call_result.get("validation_status") == "ACCEPTED_WITHIN_SCOPE"
    if not hashes_unchanged or not restored_exact or not behavior_consistent:
        raise RuntimeError("rollback drill verification failed")

    write_json(run_root / "old_evidence_hashes_before.json", {"schema": "jinrong_t7_hash_snapshot_v1", "snapshot": before_snapshot})
    write_json(run_root / "old_evidence_hashes_after.json", {"schema": "jinrong_t7_hash_snapshot_v1", "snapshot": after_snapshot})
    rollback_receipt = {
        "schema": "jinrong_t7_rollback_receipt_v1",
        "task_id": "T7",
        "run_id": RUN_ID,
        "drill_status": "PASS",
        "candidate_state": {
            "candidate_id": "cand-d44c49dec4d95741",
            "amendment_id": "A-1",
            "shared_activation_enabled": False,
            "candidate_state_artifact": "rollback_drill/candidate_state.json",
            "candidate_state_sha256": sha256_file(rollback_root / "candidate_state.json"),
        },
        "rollback": {
            "parent_versions": [
                "T5-v3@115f396af6ea461c156d91ad9148414387724eb3",
                "T6-parent-group@ef5e84edbd4fcd35cc287316c0e994cf72f6faa4",
            ],
            "operation": "T7-local candidate state replaced by byte-identical T5 v3 parent files; no shared-tree rollback was required because activation never occurred.",
            "restored_state_artifact": "rollback_drill/restored_state.json",
            "restored_state_sha256": sha256_file(rollback_root / "restored_state.json"),
            "restored_bytes_and_modes_equal": restored_exact,
        },
        "behavior_verification": {
            "parent_validation_status_before": baseline_validator_result.get("validation_status"),
            "parent_validation_status_after": rollback_call_result.get("validation_status"),
            "behavior_consistent": behavior_consistent,
            "t4_baseline_replay_records_unchanged": True,
        },
        "old_evidence_verification": {
            "snapshot_count": len(before_snapshot),
            "before_artifact": "old_evidence_hashes_before.json",
            "after_artifact": "old_evidence_hashes_after.json",
            "all_git_blob_sha256_bytes_mode_unchanged": hashes_unchanged,
        },
        "shared_tree": {
            "t4_changed": False,
            "t5_changed": False,
            "t6_changed": False,
            "registry_changed": False,
            "candidate_enabled": False,
        },
        "unverified": [
            "Rollback behavior in a deployment where the candidate had actually been enabled; no such deployment exists.",
            "Selection or sealed set rollback because those sets are not built.",
        ],
    }
    write_json(run_root / "rollback_receipt.json", rollback_receipt)
    append_event(events_path, "rollback_drill_completed", status="PASS", old_evidence_unchanged=hashes_unchanged, shared_activation=False)

    six_gates = [
        {
            "id": "critical_or_severe_defect_miss",
            "result": "UNRESOLVED_NOT_EVALUABLE",
            "detail": "The legal T1-INC-14 UNRESOLVED is excluded. The narrowed missing-required case has baseline silent skip, but the candidate has no executable authorized operation, so no zero-miss result can be claimed.",
        },
        {
            "id": "legitimate_false_block",
            "result": "PASS_AT_PARENT_CONTROLS_ONLY",
            "detail": "T5 parent positive and runtime-derived mismatch controls pass; the candidate cannot execute the absence policy, so full-candidate false-block behavior is not established.",
        },
        {
            "id": "evidence_completeness",
            "result": "FAIL",
            "detail": "E-03 remains outside the closed T5 v3 path enums and has no authorized executable operation.",
        },
        {
            "id": "claim_overreach",
            "result": "PASS",
            "detail": "No experiment, scientific success, C/S validity, deployment, or formal qualification is claimed.",
        },
        {
            "id": "raw_record_integrity",
            "result": "PASS",
            "detail": "All baseline logs are retained in the T7 run; runtime-derived mismatch files are deleted after their hashes are logged and no source package is overwritten.",
        },
        {
            "id": "budget_integrity",
            "result": "PASS",
            "detail": "Model, network, remote, production, database, training, daemon, Loop B and automatic-retry counters are zero.",
        },
    ]
    pilot_acceptance = {
        "schema": "jinrong_t7_pilot_acceptance_v1",
        "task_id": "T7",
        "run_id": RUN_ID,
        "card_version": 2,
        "direction": "R",
        "candidate": {
            "candidate_id": "cand-d44c49dec4d95741",
            "source_status": "PROPOSED_NOT_ENABLED",
            "a1_amendment_status": "COMPLETED_BEFORE_EVALUATION",
            "evaluation_status": "NOT_EVALUABLE",
            "activation_status": "NOT_ENABLED",
        },
        "hard_gates": six_gates,
        "hard_gate_order": "Executed before benefit and cost judgment.",
        "all_hard_gates_satisfied": False,
        "benefit": {
            "counted_repaired_misses": 0,
            "required_two_repairs": 2,
            "regressions_counted": 0,
            "detection_improvement": "NOT_ESTABLISHED",
            "reason": "The candidate's new absence policy is not executable under the authorized T5 v3 closed registry.",
        },
        "cost": {
            "baseline_model_calls": 0,
            "candidate_model_calls": 0,
            "cost_comparison_branch_preregistered": False,
            "cost_comparison_available": False,
            "reason": "The T6 candidate contains projected zero cost but no pre-registered executable candidate-vs-baseline cost comparison; NOT_EVALUABLE cannot be treated as equal quality.",
        },
        "case_sets": {
            "development_t1_v3": "BOUND_16_CASES_READ_ONLY",
            "selection_set": "NOT_BUILT",
            "selection_access": "NOT_APPLICABLE",
            "sealed": "NOT_APPLICABLE_UNRESOLVED",
            "sealed_access_count": 0,
            "reason": "The proposed 24/24/24 selection and sealed sets do not exist; no sealed access is fabricated.",
        },
        "selection_conclusion": {
            "decision": "NO_PROMOTION",
            "basis": [
                "Candidate evaluation status is NOT_EVALUABLE because A-1 cannot become executable without a separately reviewed operation extension.",
                "Evidence completeness hard gate is not satisfied.",
                "Zero counted repaired misses versus the required two.",
                "The pre-registered equal-quality cost-comparison branch is unavailable.",
                "Selection and sealed sets are not built, so one-selection/one-sealed-access cannot be executed.",
            ],
        },
        "rollback": {
            "status": "PASS",
            "receipt": "rollback_receipt.json",
            "old_evidence_hashes_unchanged": True,
        },
        "three_axes": {
            "delivery": "DELIVERED",
            "review": "UNREVIEWED",
            "activation": "NOT_ENABLED",
        },
        "a_assertions": {
            "A1": "FAIL",
            "A2": "PASS",
            "A3": "PASS",
            "A_common": "PENDING_FINAL_SELF_CHECK",
        },
        "unresolved": [
            "Execution-chat token usage remains UNRESOLVED and is not converted to zero.",
            "Full-candidate severe-miss and false-block behavior remains NOT_EVALUABLE without an authorized executable absence operation.",
            "Selection and sealed behavior remain NOT_BUILT/NOT_APPLICABLE.",
            "Execution conversation token usage is not measurable here.",
            "Independent Loop C acceptance is pending; Loop A does not self-fill ACCEPTED.",
        ],
    }
    write_json(run_root / "pilot_acceptance.json", pilot_acceptance)

    receipt = {
        "schema": "receipt",
        "task_id": "T7",
        "run_id": RUN_ID,
        "card_version": 2,
        "direction": "R",
        "execution_status": "COMPLETED_NO_PROMOTION",
        "acceptance_status": "UNREVIEWED",
        "activation_status": "NOT_ENABLED",
        "authorization_ref": "Explicit user Loop A dispatch in TASK_PROMPT.md; card DRAFT placeholders were not edited.",
        "protocol_freeze_sha256": PROTOCOL_FREEZE,
        "dependency_acceptance": {
            "T6": {
                "review_id": "T6R-01",
                "decision": "ACCEPTED",
                "receipt": "research/harness_rsi_v1/reviews/T6R-01/review_receipt.json",
                "receipt_git_blob_id": git_blob(repo_root, "research/harness_rsi_v1/reviews/T6R-01/review_receipt.json"),
            }
        },
        "input_bindings": input_bindings,
        "actions": [
            "Completed A-1 before evaluating the T6 candidate.",
            "Replayed the T4 v2 case-level baseline twice with 22 read-only check invocations.",
            "Validated the T5 v3 parent recipe and fail-closed the amended candidate at the closed-registry boundary.",
            "Recorded selection_set=NOT_BUILT and sealed=NOT_APPLICABLE_UNRESOLVED.",
            "Executed a T7-local rollback drill and verified old evidence hashes.",
            "Selected NO_PROMOTION.",
        ],
        "checks": [
            {"id": "a1", "result": "FAIL", "scope": "A-1 classification correction completed, but no executable candidate repair or pre-registered cost branch exists."},
            {"id": "a2", "result": "PASS", "scope": "T7-local parent restoration matched bytes/modes and old evidence hashes remained unchanged."},
            {"id": "a3", "result": "PASS", "scope": "No engineering closeout is reported as experiment or scientific success; C/S validity is not claimed."},
            {"id": "a_common", "result": "PENDING_FINAL_SELF_CHECK", "scope": "Final self-check verifies JSON, paths, hashes, modes, boundary and unknowns."},
            {"id": "g1", "result": "PENDING_FINAL_SELF_CHECK", "scope": "Final self-check runs the summary guard individually over every Markdown artifact."},
        ],
        "output_manifest": "artifacts_manifest.json",
        "scope": {
            "candidate_enabled": False,
            "selection_set_accessed": False,
            "sealed_set_accessed": False,
            "scientific_experiment": False,
            "loop_b_called": False,
        },
        "unresolved": pilot_acceptance["unresolved"],
        "usage": {
            "profile": "BR",
            "additional_cheap_requests": 0,
            "additional_cheap_requests_max": 0,
            "additional_strong_requests": 0,
            "additional_strong_requests_max": 1,
            "strong_requests_reserved_for_loop_c": 1,
            "model_calls": 0,
            "network_calls": 0,
            "remote_calls": 0,
            "production_calls": 0,
            "database_calls": 0,
            "training_calls": 0,
            "daemon_calls": 0,
            "loop_b_calls": 0,
            "automatic_retries": 0,
            "execution_chat_usage": "UNRESOLVED",
        },
    }
    write_json(run_root / "receipt.json", receipt)
    append_event(
        events_path,
        "usage_snapshot",
        additional_cheap_requests=0,
        additional_strong_requests=0,
        model_calls=0,
        network_calls=0,
        remote_calls=0,
        production_calls=0,
        database_calls=0,
        training_calls=0,
        daemon_calls=0,
        loop_b_calls=0,
        automatic_retries=0,
        execution_chat_usage="UNRESOLVED",
    )

    for path in tmp_root.rglob("*"):
        if path.is_file():
            raise RuntimeError(f"unexpected temporary derive residue: {path}")
    print(json.dumps({"status": "EXECUTED", "run_root": str(run_root), "baseline_checks": baseline_check_count, "candidate": "NOT_EVALUABLE", "decision": "NO_PROMOTION", "rollback": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
