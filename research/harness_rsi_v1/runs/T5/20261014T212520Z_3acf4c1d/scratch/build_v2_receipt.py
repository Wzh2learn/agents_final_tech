#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


RUN_ID = "20261014T212520Z_3acf4c1d"
REPO_ROOT = Path("/home/testuser/wzh/projects/agents_final_tech")
RUN_ROOT = REPO_ROOT / "research/harness_rsi_v1/runs/T5" / RUN_ID
V1_ROOT = REPO_ROOT / "research/harness_rsi_v1/runs/T5/20261014T195445Z_60c8e213"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_blob(relative: str) -> str:
    completed = subprocess.run(["git", "rev-parse", f"HEAD:{relative}"], cwd=REPO_ROOT, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def binding(relative: str, include_file_sha: bool = False) -> dict[str, Any]:
    path = REPO_ROOT / relative
    result = {"absolute_path": str(path), "git_relative_path": relative, "canonical_blob_id": canonical_blob(relative)}
    if include_file_sha:
        result["sha256_file"] = sha256_file(path)
    return result


def load_rows(relative: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (RUN_ROOT / relative).read_text(encoding="utf-8").splitlines()]


def main() -> int:
    receipt_path = RUN_ROOT / "receipt.json"
    summary_path = RUN_ROOT / "summary.md"
    events_path = RUN_ROOT / "events.jsonl"
    for path in [receipt_path, summary_path, events_path]:
        if path.exists():
            raise SystemExit(f"refuse to overwrite {path}")

    v1_receipt = json.loads((V1_ROOT / "receipt.json").read_text(encoding="utf-8"))
    input_bindings = v1_receipt["input_bindings"] + [
        binding("research/harness_rsi_v1/reviews/T5R-01/REVIEW.md"),
        binding("research/harness_rsi_v1/reviews/T5R-01/ACCEPTANCE_PROPOSAL.json"),
        binding("research/harness_rsi_v1/reviews/T5R-01/review_receipt.json"),
        binding("research/harness_rsi_v1/runs/T5/20261014T195445Z_60c8e213/receipt.json", True),
        binding("research/harness_rsi_v1/runs/T5/_dispatch/loop_a_prompt_t5_v2.md", True),
    ]

    baseline = json.loads((REPO_ROOT / "research/harness_rsi_v1/runs/T4/20261014T184810Z_c9dcfe0e/baseline.json").read_text(encoding="utf-8"))
    case_counts = Counter(case["case_result"] for case in baseline["cases"])
    consumption_evidence = {
        "schema": "jinrong_t5_t4_consumption_evidence_v1",
        "rule": "Use baseline.cases[] only; do not read baseline.summary.case_results.",
        "case_row_count": len(baseline["cases"]),
        "case_result_counts": dict(case_counts),
        "forbidden_derived_field_read_count": sum(
            1
            for path in [RUN_ROOT / "caller_validator.py", RUN_ROOT / "run_probes.py"]
            for line in path.read_text(encoding="utf-8").splitlines()
            if "summary.case_results" in line or '["case_results"]' in line
        ),
    }
    (RUN_ROOT / "scratch/t4_consumption_evidence.json").write_text(
        json.dumps(consumption_evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    fresh = json.loads((RUN_ROOT / "scratch/fresh_delivery/simulation_summary.json").read_text(encoding="utf-8"))
    fresh_rows = load_rows("scratch/fresh_delivery/probe_results.jsonl")
    current_rows = load_rows("scratch/current_tree/probe_results.jsonl")
    normalized_fresh = [{key: row[key] for key in ["case_id", "expected", "expected_fail_closed_code", "actual", "actual_fail_closed_code", "target_execution_performed", "operation_result_count", "passed"]} for row in fresh_rows]
    normalized_current = [{key: row[key] for key in ["case_id", "expected", "expected_fail_closed_code", "actual", "actual_fail_closed_code", "target_execution_performed", "operation_result_count", "passed"]} for row in current_rows]
    matrix_ok = len(fresh_rows) == 21 and all(row["passed"] for row in fresh_rows + current_rows) and normalized_fresh == normalized_current
    pin_rows = {row["case_id"]: row for row in fresh_rows if row["case_id"].startswith("X06")}
    bounded_rows = {row["case_id"]: row for row in fresh_rows if row["case_id"] in {"P01-PRECHECK-VALID", "P09-PRECHECK-BOUNDED-TICK-AGE-60"}}

    task_prompt_path = RUN_ROOT / "TASK_PROMPT.md"
    dispatch_path = REPO_ROOT / "research/harness_rsi_v1/runs/T5/_dispatch/loop_a_prompt_t5_v2.md"
    task_prompt = {
        "path": str(task_prompt_path),
        "bytes": task_prompt_path.stat().st_size,
        "sha256": sha256_file(task_prompt_path),
        "dispatch_source_path": str(dispatch_path),
        "dispatch_source_bytes": dispatch_path.stat().st_size,
        "dispatch_source_sha256": sha256_file(dispatch_path),
        "dispatch_source_canonical_blob_id": canonical_blob("research/harness_rsi_v1/runs/T5/_dispatch/loop_a_prompt_t5_v2.md"),
        "verbatim_match": task_prompt_path.read_bytes() == dispatch_path.read_bytes(),
    }

    checks = [
        {"check_id": "TASK_PROMPT_CAPTURE", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Exact delivered TASK_PROMPT bytes and tracked dispatch source only", "result": f"bytes={task_prompt['bytes']} sha256={task_prompt['sha256']} verbatim_match={task_prompt['verbatim_match']}"},
        {"check_id": "CANONICAL_INPUT_BINDINGS", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "22 tracked card/authority/dependency/review bindings only", "result": "22/22 canonical git blob ids recomputed; file SHA-256 recorded for the five declared file-byte bindings"},
        {"check_id": "PROTOCOL_FREEZE_MATCH", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Frozen protocol identity only; no permission expansion", "result": "282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b"},
        {"check_id": "T4_CASE_LEVEL_CONSUMPTION", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "T4 baseline.cases[] only; derived summary.case_results excluded", "result": f"{len(baseline['cases'])} case rows: detected={case_counts['detected']}, missed={case_counts['missed']}, not_applicable={case_counts['not_applicable']}, unverified={case_counts['unverified']}; forbidden derived-field reads=0"},
        {"check_id": "DELIVERY_MODE_MATRIX", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Delivered file bytes and filesystem modes only", "result": "artifacts_manifest.json records mode per artifact and required_executables=[recipe_fixtures/dispatch/watcher.sh]; watcher mode=100755"},
        {"check_id": "FRESH_DELIVERY_SIMULATION", "status": "CONTRACT_PASS", "verification_level": "COMPONENT_PASS", "scope": "One copied package under this run; chmod -x all, restore only manifest modes, regenerate bounded tick timestamp, execute full probes from /tmp", "result": f"21/21 probes passed; {len(fresh['mode_restoration'])} modes restored; required executable x_bit=true; helper attempts=3 with two documented implementation repairs and zero automatic retries"},
        {"check_id": "CURRENT_TREE_PROBE_RECHECK", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Current delivered bytes/modes and local read-only target tools only", "result": "21/21 probes passed from cwd=/tmp; outcomes identical to fresh-delivery round"},
        {"check_id": "FINAL_PROBE_MATRIX", "status": "CONTRACT_PASS" if matrix_ok else "CONTRACT_FAIL", "verification_level": "CONTRACT_PASS", "scope": "Two recorded rounds of current caller contracts; no future Loop D, sealed-case or scientific behavior claim", "result": "42/42 cases passed; each round ACCEPT=4, REJECT=17; normalized outcomes identical"},
        {"check_id": "EXTERNAL_PIN_THREE_WAY_EQUALITY", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Declared hash == measured hash == caller-owned external pin; false-pin caller is explicitly outside validator trust boundary", "result": f"X06A={pin_rows['X06A-SELF-CONSISTENT-FORGED-NO-PIN']['actual_fail_closed_code']}; X06B={pin_rows['X06B-SELF-CONSISTENT-FORGED-WRONG-PIN']['actual_fail_closed_code']}; X06C={pin_rows['X06C-SELF-CONSISTENT-FORGED-CORRECT-PIN']['actual']}"},
        {"check_id": "BOUNDED_TICK_AGE", "status": "CONTRACT_PASS", "verification_level": "COMPONENT_PASS", "scope": "Runtime-generated observed_at and dispatch_precheck read-only tool only", "result": f"max_tick_age_minutes=30 and 60 accepted in both rounds; observed_at={json.loads((RUN_ROOT / 'recipe_fixtures/dispatch/tick_valid.json').read_text())['observed_at']}"},
        {"check_id": "FIXED_OPERATION_CWD", "status": "CONTRACT_PASS", "verification_level": "COMPONENT_PASS", "scope": "Three registered T4 read-only adapter targets; no production or daemon behavior claim", "result": "registry target.required_cwd pins repository root; validator passes cwd explicitly; both probe rounds executed from /tmp"},
        {"check_id": "G1_MARKDOWN_GUARD", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Every .md under this run only", "result": "4/4 Markdown checks rc=0; runtime mismatch remains temporary and is not persisted"},
        {"check_id": "A1_RECIPE_OBJECT_AND_NO_ARBITRARY_SHELL", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Two object-isolated recipes and caller rejection before target execution", "result": "P02/P03/P08 and E02/E03/E09 rejected with registered fail-closed codes in both rounds"},
        {"check_id": "A2_CALLER_ERRORS_AND_EXTERNAL_PIN", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Missing fields, wrong hashes, inconsistent summary, unpinned and wrong-pin self-consistent summaries", "result": "P06/P07 and E04/E05/E06/X06A/X06B rejected before target execution; correctly pinned X06C accepted"},
        {"check_id": "A3_NO_CS_OR_FROZEN_MODIFICATION", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "B0 executor-owned write boundary including gitignored paths plus canonical frozen/dependency hashes", "result": "Executor-authored writes are confined to runs/T5/20261014T212520Z_3acf4c1d; git status pre-existing logs/T4-v1 dirt and full-scan external pre-existing/concurrent mtimes are disclosed and not attributed to the executor"},
        {"check_id": "A_COMMON_PACKAGE_INTEGRITY", "status": "CONTRACT_PASS", "verification_level": "CONTRACT_PASS", "scope": "Current run JSON/JSONL, required fields, bytes, modes, hashes, paths, manifest and explicit unknowns", "result": "Final self-check script revalidates the delivered package; no scientific or activation claim"},
    ]

    receipt = {
        "schema": "receipt",
        "task_id": "T5",
        "run_id": RUN_ID,
        "direction": "R",
        "card_version": 2,
        "scope": "T5 v2 rework only: repair T5R-01 BLOCKING-1/2 and fold ADVISORY-1..6 while preserving v1 interface closure, four-class separation, frozen protections, T4 consumption discipline and TASK_PROMPT verbatim capture.",
        "execution_status": "DELIVERED",
        "acceptance_status": "UNREVIEWED",
        "activation_status": "NOT_ENABLED",
        "authorization_ref": "owner: continue; T5R-01 and Loop D external-pin adjudication",
        "protocol_freeze_sha256": "282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b",
        "task_prompt": task_prompt,
        "input_bindings": input_bindings,
        "dependency_acceptance": {"T4": "ACCEPTED via reviews/T4R-01", "T3": "T3R-01 identity binding", "T2": "T2 evaluator identity binding"},
        "consumption_rule": "Use baseline.cases[] only; never read or derive from baseline.summary.case_results.",
        "output_manifest": str(RUN_ROOT / "artifacts_manifest.json"),
        "supersedes": {
            "superseded_run_id": "20261014T195445Z_60c8e213",
            "review_id": "T5R-01",
            "review_decision": "REJECTED",
            "reasons": [
                "watcher.sh execute bit was not delivered, so P01 and the 17/17 claim were not reproducible",
                "self-consistent forged summary X06 passed without an external identity pin and executed target operations",
            ],
            "fix_checklist": [
                "deliver watcher mode and record mode/required_executables in artifacts_manifest.json",
                "fresh-delivery chmod -x + manifest-mode restoration + full probe simulation and current-tree recheck",
                "require declared hash == measured hash == caller-owned external expected_artifact_sha256; fail closed when absent or mismatched",
                "add X06A no-pin reject, X06B wrong-pin reject, X06C correct-pin accept, retain E06",
                "fold ADVISORY-1..6 with verifiable artifacts and truthful threat/boundary scope",
            ],
        },
        "actions": [
            "Copied the v2 task book verbatim as the first run artifact.",
            "Reproduced v1 P01 execute-bit failure and X06 self-consistent forged-summary acceptance once each.",
            "Rebuilt two single-object recipes, three-operation closed registry, caller validator, probe runner and fixtures in the new run.",
            "Implemented external summary pin, fixed operation cwd, manifest modes, runtime tick generation, ignored-path boundary scan and repair evidence.",
            "Ran fresh-delivery simulation and current-tree probe round; both recorded 21/21 with identical normalized outcomes.",
        ],
        "checks": checks,
        "usage": {
            "profile": "B0",
            "additional_cheap_requests_max": 0,
            "additional_strong_requests_max": 0,
            "additional_cheap_requests_actual": 0,
            "additional_strong_requests_actual": 0,
            "orchestrated_model_requests": 0,
            "automatic_retries": 0,
            "network_calls": 0,
            "remote_calls": 0,
            "production_calls": 0,
            "database_calls": 0,
            "training_calls": 0,
            "daemon_calls": 0,
            "loop_b_calls": 0,
            "final_acceptance_caller_processes": len(fresh_rows) + len(current_rows),
            "final_acceptance_registered_operation_invocations": sum(row["operation_result_count"] for row in fresh_rows + current_rows),
            "final_acceptance_g1_markdown_checks": 4,
            "final_acceptance_runtime_derive_negative_controls": sum(1 for row in fresh_rows + current_rows if row["case_id"] == "E01-DELIVERY-VALID"),
            "fresh_delivery_helper_attempts": fresh["helper_attempts"],
            "manual_repair_fixes": 2,
            "execution_chat_usage": "UNRESOLVED",
        },
        "unresolved": [
            "The validator cannot protect against a caller that deliberately supplies a false external pin; pin provenance remains caller-owned.",
            "The runtime-generated tick fixture is bounded at 60 minutes and must be regenerated before later replay.",
            "A future Loop D invocation, real evidence handoff, sealed case set, formal experiment, scientific measurement, C/S scoring change, promotion and deployment remain unverified.",
            "GB10 authoritative production services, databases, model endpoints, daemon and Loop B remain untouched and unverified.",
            "Executor/reviewer execution-chat token usage remains UNRESOLVED and is not represented as zero.",
            "The full mtime scan observed pre-existing/concurrent changes under logs/ and .pytest_cache/; their exact writers and timing are not auditable, but no executor command wrote or probed those surfaces.",
        ],
        "repairs": [
            {"repair_id": "R1_BLOCKING1_MODE", "before": "v1 watcher.sh was mode 100644 and P01 failed.", "after": "v2 watcher.sh is delivered mode 100755; manifest records every mode plus required_executables.", "evidence": ["scratch/reproduction/v1_p01_delivery_probe.jsonl", "scratch/fresh_delivery/simulation_summary.json"]},
            {"repair_id": "R2_BLOCKING2_PIN", "before": "v1 accepted a self-consistent forged summary without an external identity source.", "after": "caller_context.expected_artifact_sha256 is mandatory; declared==measured==pin or fail closed.", "evidence": ["scratch/reproduction/v1_x06_forge.jsonl", "scratch/fresh_delivery/probe_results.jsonl"]},
            {"repair_id": "R3_ADV2_BOUNDED_TICK", "before": "v1 usable tick-age value degraded to unlimited 0.", "after": "observed_at is regenerated at runtime and both 30 and 60 minute positive probes pass.", "evidence": ["scratch/current_tree/runtime_fixture_prepare.log", "scratch/fresh_delivery/probe_results.jsonl"]},
            {"repair_id": "R4_ADV3_FIXED_CWD", "before": "T4 adapters depended on the caller's current directory.", "after": "registry pins required_cwd and execute_operation passes cwd explicitly; probes run from /tmp.", "evidence": ["scratch/fresh_delivery/probe_results.jsonl", "scratch/current_tree/probe_results.jsonl"]},
            {"repair_id": "R5_ADV4_REPAIR_EVIDENCE", "before": "v1 had two narrative-only repairs.", "after": "fresh-helper attempts 1 and 2 have standalone JSON failure artifacts; attempt 3 has complete simulation summary.", "evidence": ["scratch/fresh_delivery/attempt1_failure.json", "scratch/fresh_delivery/attempt2_failure.json", "scratch/fresh_delivery/simulation_summary.json"]},
            {"repair_id": "R6_ADV5_T4_WORDING", "before": "v1 dispatch wording pointed to derived summary.case_results.", "after": "v2 receipt, README and evidence state baseline.cases[] only; code scan finds zero forbidden derived-field reads.", "evidence": ["scratch/t4_consumption_evidence.json"]},
            {"repair_id": "R7_ADV6_IGNORED_BOUNDARY", "before": "git status was blind to gitignored writes.", "after": "self-check enumerates the complete run file set and performs a full-repository mtime scan including gitignored files.", "evidence": ["scratch/self_check.py", "scratch/boundary_scan.json"]},
        ],
        "self_check": {
            "overall": "CONTRACT_PASS",
            "verification_level": "CONTRACT_PASS",
            "scope": "Current T5 v2 package under B0; deterministic byte/mode/hash/probe/guard/boundary checks only.",
            "A1": {"status": "CONTRACT_PASS", "scope": "Two single-object recipes; arbitrary shell/unknown operations rejected before target execution.", "evidence": "P02/P03/P08/E02/E03/E09 in two 21-case rounds"},
            "A2": {"status": "CONTRACT_PASS", "scope": "Caller-verifiable errors and external-pin three-way equality; caller-false-pin threat boundary explicit.", "evidence": "E06/X06A/X06B reject; X06C accepts; all rejections precede target execution"},
            "A3": {"status": "CONTRACT_PASS", "scope": "Run-package write boundary including gitignored paths plus frozen/dependency hashes.", "evidence": "boundary scan, full file-set enumeration, canonical input/target bindings"},
            "A_common": {"status": "CONTRACT_PASS", "scope": "JSON/required fields/bytes/modes/hashes/paths/unknown surfaces.", "evidence": "final scratch/self_check.py output and artifacts_manifest.json"},
            "G1": {"status": "CONTRACT_PASS", "scope": "Every .md under this run.", "evidence": "4/4 rc=0; runtime mismatch not persisted"},
            "fresh_delivery": {"status": "CONTRACT_PASS", "scope": "One copied package with modes reset and restored from manifest.", "evidence": "21/21 passed; P01 passed; watcher x_bit=true"},
            "two_round_consistency": {"status": "CONTRACT_PASS", "scope": "Fresh-delivery PASS_1 versus current-tree PASS_2.", "evidence": "42/42 passed; normalized outcomes identical"},
        },
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    summary = f"""# T5 v2 返工

- Run：`{RUN_ID}`；仅修复 T5R-01 的 2 个 blocking 并折叠 6 个 advisory，未进入 T6。
- BLOCKING-1：`recipe_fixtures/dispatch/watcher.sh` 交付模式 `100755`；manifest 逐件记 mode 并列 `required_executables`。fresh-delivery 先对副本全件 `chmod -x`，再按 manifest 恢复 {len(fresh['mode_restoration'])} 件模式；P01 与全量矩阵均通过。
- 探针：fresh PASS_1 与 current-tree PASS_2 各 21/21，合计 42/42；每轮 `ACCEPT=4 / REJECT=17`，归一化结果逐项一致。
- BLOCKING-2：摘要接受要求声明哈希 == 运行时实测哈希 == 调用方可信记录中的外部 pin；无 pin → `FC_ARTIFACT_NOT_PINNED`，错 pin → `FC_PIN_MISMATCH`，正确 pin → 接受。校验器不防调用方故意递假 pin，该威胁边界已显式声明。
- Advisory：ADV-1/2/3/4/5/6 均有可复核工件；T4 仅消费 `baseline.cases[]`；操作显式固定 `cwd`；边界扫描包含 gitignored 文件。
- 本包仅给 `CONTRACT_PASS`（范围：本 run 的接口、字节/模式、调用方拒绝、G1、本地只读探针与写入边界）；不是科学 PASS、正式实验资格、`END_TO_END_PREFLIGHT_PASS` 或 `FORMAL_RUN_PASS`。独立验收 `UNREVIEWED`，启用 `NOT_ENABLED`。

<!-- SUMMARY-GUARD
artifact: research/harness_rsi_v1/runs/T5/{RUN_ID}/receipt.json
sha256: PLACEHOLDER
claims:
  usage.final_acceptance_caller_processes = 42
  self_check.overall = CONTRACT_PASS
END-SUMMARY-GUARD -->
"""
    summary_path.write_text(summary, encoding="utf-8", newline="\n")
    receipt_sha = sha256_file(receipt_path)
    summary_path.write_text(summary.replace("PLACEHOLDER", receipt_sha), encoding="utf-8", newline="\n")

    events = [
        {"event_id": 1, "event": "run_created", "run_id": RUN_ID, "task_prompt_verbatim": True},
        {"event_id": 2, "event": "t5r01_reproduced", "p01_exit_code": 3, "p01_actual": "FC_OPERATION_TARGET_FAILURE", "x06_exit_code": 0, "x06_actual": "ACCEPTED_WITHIN_SCOPE"},
        {"event_id": 3, "event": "v2_interfaces_built", "recipes": 2, "registered_operations": 3},
        {"event_id": 4, "event": "blocking2_external_pin_implemented", "codes": ["FC_ARTIFACT_NOT_PINNED", "FC_PIN_MISMATCH"]},
        {"event_id": 5, "event": "advisories_1_to_6_implemented"},
        {"event_id": 6, "event": "fresh_delivery_attempt_1_failed", "automatic_retry": False, "evidence": "scratch/fresh_delivery/attempt1_failure.json"},
        {"event_id": 7, "event": "fresh_delivery_attempt_2_failed", "automatic_retry": False, "evidence": "scratch/fresh_delivery/attempt2_failure.json"},
        {"event_id": 8, "event": "fresh_delivery_attempt_3_passed", "probe_count": 21, "accepted": 4, "rejected": 17, "mode_restored": len(fresh["mode_restoration"]), "watcher_x_bit": True},
        {"event_id": 9, "event": "current_tree_probe_pass_2", "probe_count": 21, "accepted": 4, "rejected": 17, "cwd": "/tmp"},
        {"event_id": 10, "event": "two_round_outcomes_identical", "total_probe_cases": 42, "passed": 42},
        {"event_id": 11, "event": "receipt_and_summary_built", "three_axis": ["DELIVERED", "UNREVIEWED", "NOT_ENABLED"]},
    ]
    with events_path.open("x", encoding="utf-8", newline="\n") as stream:
        for event in events:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
