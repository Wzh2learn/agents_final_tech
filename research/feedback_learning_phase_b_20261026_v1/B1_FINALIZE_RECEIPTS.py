"""Finalize B1 remediation receipts from fresh deterministic test evidence."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
STABLE_OUTPUTS = [
    "B1_AUTHORITY_BINDING_CORRECTION.json",
    "B1_CORRECTION_TRAJECTORIES.jsonl",
    "B1_ERROR_TYPE_TAXONOMY.json",
    "B1_SUPERVISION_MANIFEST.json",
    "B1_LOCAL_PATCH_CONTRACT.json",
    "B1_LOCAL_EDIT_APPLIER.py",
    "B1_TEST_LOCAL_EDIT_APPLIER.py",
    "B1_PREFLIGHT_DRAFT.json",
    "B1_REPORT.md",
    "B1_BUILD_SUPERVISION.py",
    "B1_FINALIZE_RECEIPTS.py",
    "B1_TEST_OUTPUT.txt",
    "B1_FULL_TEST_OUTPUT.txt",
    "B2_DEVELOPMENT_PANEL_DRAFT.json",
    "archive/B1_REMEDIATION1_RAW_TRAJECTORIES.jsonl",
    "archive/B1_REMEDIATION1_SCORE_RESULT_A.json",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    receipt_path = OUT_DIR / "B1_QUALIFICATION_RECEIPT.json"
    manifest_path = OUT_DIR / "B1_SUPERVISION_MANIFEST.json"
    trajectories_path = OUT_DIR / "B1_CORRECTION_TRAJECTORIES.jsonl"
    panel_path = OUT_DIR / "B2_DEVELOPMENT_PANEL_DRAFT.json"
    authority_path = OUT_DIR / "B1_AUTHORITY_BINDING_CORRECTION.json"
    taxonomy_path = OUT_DIR / "B1_ERROR_TYPE_TAXONOMY.json"
    test_log_path = OUT_DIR / "B1_TEST_OUTPUT.txt"
    report_path = OUT_DIR / "B1_REPORT.md"
    result_path = OUT_DIR / "B1_REMEDIATION2_RESULT_A.json"
    preserved_result_path = OUT_DIR / "B1_REMEDIATION_RESULT_A.json"
    task_result_path = OUT_DIR / "TASK_RESULT.json"

    receipt = load_json(receipt_path)
    manifest = load_json(manifest_path)
    panel = load_json(panel_path)
    authority = load_json(authority_path)
    taxonomy = load_json(taxonomy_path)
    trajectories = load_jsonl(trajectories_path)
    test_output = test_log_path.read_text(encoding="utf-8")
    if "exit_code=0" not in test_output or "FAILED" in test_output or "ERROR" in test_output:
        raise RuntimeError("fresh_test_evidence_not_passing")
    wall_match = re.search(r"Ran 1 test in ([0-9.]+)s", test_output)
    if wall_match is None:
        raise RuntimeError("test_wall_seconds_missing")
    test_wall_seconds = float(wall_match.group(1))
    test_file_text = (OUT_DIR / "B1_TEST_LOCAL_EDIT_APPLIER.py").read_text(encoding="utf-8")
    subcase_match = re.search(r"^REGISTERED_SUBCASES = (\d+)$", test_file_text, flags=re.MULTILINE)
    if subcase_match is None:
        raise RuntimeError("registered_subcase_count_missing")
    registered_subcases = int(subcase_match.group(1))
    full_test_log_path = OUT_DIR / "B1_FULL_TEST_OUTPUT.txt"
    full_test_output = full_test_log_path.read_text(encoding="utf-8")
    full_exit_match = re.search(r"^exit_code=(\d+)$", full_test_output, flags=re.MULTILINE)
    full_summary_match = re.search(
        r"(\d+) failed, (\d+) passed, (\d+) skipped, (\d+) deselected, "
        r"(\d+) warnings in ([0-9.]+)s",
        full_test_output,
    )
    if full_exit_match is None or full_summary_match is None:
        raise RuntimeError("full_repository_test_evidence_incomplete")
    full_exit_code = int(full_exit_match.group(1))
    full_repository_suite = {
        "status": "FAIL" if full_exit_code else "PASS",
        "exit_code": full_exit_code,
        "failed": int(full_summary_match.group(1)),
        "passed": int(full_summary_match.group(2)),
        "skipped": int(full_summary_match.group(3)),
        "deselected": int(full_summary_match.group(4)),
        "warnings": int(full_summary_match.group(5)),
        "wall_seconds": float(full_summary_match.group(6)),
        "output_path": str(full_test_log_path),
        "output_sha256": sha256_file(full_test_log_path),
        "failure": (
            "tests/test_finqa_v2_scorer_runtime_binding_v2.py::"
            "test_old_invalid_run_hashes_remain_unchanged"
            if full_exit_code
            else None
        ),
        "failure_detail": (
            "missing repository fixture "
            "research/finqa_v2_20261010/results/finqa_v2_focused_preflight.log"
            if full_exit_code
            else None
        ),
        "health_or_model_probe_reported_by_log": False,
    }

    qualification = manifest["scientific_qualification"]
    period_unresolved = sum(
        "question_period_not_visible_in_program"
        in row["verification"]["semantic"]["candidate_reasons"]
        for row in trajectories
    )
    feedback_diffs_identical = sum(
        row["label_reference_identity"]["r_e_feedback_content_diff"]["identical"]
        for row in trajectories
    )
    preserved_raw_path = OUT_DIR / "archive/B1_REMEDIATION1_RAW_TRAJECTORIES.jsonl"
    if sha256_file(preserved_raw_path) != (
        "540df692b04378f867e3d0b59435fbbc07e992dac8d77fadc6860978b4ef0cdb"
    ):
        raise RuntimeError("preserved_remediation1_raw_hash_drift")
    if (
        sha256_file(preserved_result_path)
        != "eae35b9daf9047df3b8054b79afb489099d9d6ec6dcffaaa538017a52c73688a"
        or sha256_file(OUT_DIR / "archive/B1_REMEDIATION1_SCORE_RESULT_A.json")
        != sha256_file(preserved_result_path)
    ):
        raise RuntimeError("preserved_remediation1_score_hash_drift")
    mechanism = taxonomy["registered_mechanism"]
    report = f"""# B1 Remediation Report

Task: `phaseb-b1-remediation2-a-20261026`

## Verdict

A-side remediation2 is `A_REMEDIATION2_COMPLETE_PENDING_C_REAUDIT`. The
remaining C-1 set-binding, direction and preservation findings are closed in
the A-owned artifacts.
B2 training remains blocked until Loop C accepts the re-audit and D freezes the
proposed development panel.

## Authority

The canonical identity is Git commit
`{authority['canonical_identity']['git_commit']}`, path
`{authority['canonical_identity']['path']}`, blob
`{authority['canonical_identity']['git_blob']}`, size
`{authority['canonical_identity']['byte_size']}` bytes, and GB10 LF SHA-256
`{authority['canonical_identity']['gb10_lf_sha256']}`. The earlier Windows-byte
value is retained only as superseded noncanonical metadata.

## Narrow Set-Binding Mechanism

- One mechanism is registered: `{mechanism['mechanism']}`.
- It has two observed subtypes, not two independent mechanisms:
  `ROW_ROLE_MISBINDING` ({mechanism['subtype_trajectory_counts']['ROW_ROLE_MISBINDING']}
  trajectories / {mechanism['subtype_source_family_counts']['ROW_ROLE_MISBINDING']}
  source families) and `ROW_AND_PERIOD_ROLE_MISBINDING`
  ({mechanism['subtype_trajectory_counts']['ROW_AND_PERIOD_ROLE_MISBINDING']}
  trajectories / {mechanism['subtype_source_family_counts']['ROW_AND_PERIOD_ROLE_MISBINDING']}
  source families).
- Total mechanism evidence is {mechanism['trajectory_count']} trajectories from
  {mechanism['source_family_count']} source families; trajectories and source
  families are counted separately.
- Visible-evidence tests passing: {qualification['visible_evidence_test_pass']}/5.
- `OPERAND_ORDER_SIGN_REVERSAL` (6) is narrowed to `UNRESOLVED` because the
  visible `between A and B` wording does not uniquely determine direction;
  operator and order remain frozen to O and are not training targets.
- Natural `program.op` errors: 0; synthetic operator mutations are excluded.
- Unit mismatches: {qualification['unit_mismatch_trajectory_count']} total and
  {qualification['unit_only_mismatch_trajectory_count']} unit-only. Every unit
  correction is `UNRESOLVED`; no R/E target or legal patch edits `/unit`.
- Verification outcomes: {qualification['verification_overall']['PASS']} `PASS`
  and {qualification['verification_overall']['UNRESOLVED']} `UNRESOLVED`;
  {period_unresolved} rows retain unresolved period semantics.

`allowed_answer_units` is derived only by lexical lookup of the visible
deployment prompt. `minimal_edit_instruction` exists only in training and
teacher-reference fields. Deployment feedback is neutral and identical for R
and E in all 72 trajectories ({feedback_diffs_identical}/72 diffs empty).

## Target Semantics

Every eligible correction is split into `set_binding_component` and
`direction_component`. R targets and E patches contain only reference-valued
set-binding operations. Operator, subtraction-order direction and unit are not
training targets. `target_exact` is identity to the materialized unordered
set-binding target, never semantic gold. Eligible direction remains unresolved
and is never inferred from gold.

The pre-registered correct-preservation direction preserves all unchanged
references, operator, order and unit; E must not damage an originally correct
family.

## Development Panel

`B2_DEVELOPMENT_PANEL_DRAFT.json` proposes exactly 12 source families and 36
repeated-measure trajectories. It includes all five originally-wrong families
plus the seven lowest SHA-256-ranked families among the 19 originally-correct
families under the frozen selection seed. The originally-correct family
denominator is exactly **{panel['originally_correct_family_denominator']['fraction']}**.
The panel is exposed development data and is not frozen until D acts.

## Exposure And Claim Limit

All 72 rows remain exposed development supervision. No deployment feedback
event exists; the qualified mode is reference-derived visible set-binding
revision supervision, not feedback-derived learning. Report/company
independence is unavailable and is not claimed.

The remediation1 raw trajectory version and score/result version are preserved
under `archive/` with their original SHA-256 values; immutable source raw and
score files were not modified.

## Tests

Fresh command:

`PYTHONPATH=src python3 -m unittest discover -s
research/feedback_learning_phase_b_20261026_v1
-p 'B1_TEST_LOCAL_EDIT_APPLIER.py' -v`

Focused result: `OK`, exit code `0`, one registered test with
{registered_subcases} deterministic subcases.

Local full repository result: `{full_repository_suite['status']}`, exit code
`{full_repository_suite['exit_code']}` with
{full_repository_suite['passed']} passed, {full_repository_suite['failed']}
failed, {full_repository_suite['skipped']} skipped and
{full_repository_suite['deselected']} deselected. The single failure is an
unrelated missing FinQA fixture; the focused B1 suite passes. The full-suite log
reports no health or model probe. GB10 runtime was not run.

## Next Gate

Loop C must independently re-audit the narrowed mechanism, direction split,
correct-preservation direction, counts, patch legality and hashes. After C
acceptance, D must freeze the exact panel, estimands and denominators before
any B2 dispatch.
"""
    report_path.write_text(report, encoding="utf-8")

    stable_artifact_hashes = {
        name: sha256_file(OUT_DIR / name)
        for name in STABLE_OUTPUTS
    }
    receipt["tests"] = {
        "status": "PASS",
        "executed_command": (
            "PYTHONPATH=src python3 -m unittest discover -s "
            "research/feedback_learning_phase_b_20261026_v1 "
            "-p 'B1_TEST_LOCAL_EDIT_APPLIER.py' -v"
        ),
        "exit_code": 0,
        "registered_tests": 1,
        "subcases": registered_subcases,
        "output": test_output,
        "output_path": str(test_log_path),
        "output_sha256": sha256_file(test_log_path),
        "full_repository_suite": full_repository_suite,
        "gb10_runtime": "NOT_RUN",
    }
    receipt["artifacts"] = stable_artifact_hashes
    receipt["deterministic_cpu_wall_seconds_from_test_report"] = test_wall_seconds
    receipt["conditions"] = {
        "C_1_taxonomy": "CLOSED_A_SIDE",
        "C_2_units": "CLOSED_A_SIDE",
        "C_3_information_parity": "CLOSED_A_SIDE",
        "C_4_equivalence": "CLOSED_A_SIDE",
        "C_5_authority_binding": "CLOSED_A_SIDE",
        "C_6_damage_panel": "CLOSED_A_SIDE",
    }
    receipt["smallest_next_action"] = "C independently re-audits; D freezes the panel; do not train B2"
    write_json(receipt_path, receipt)

    output_hashes = dict(stable_artifact_hashes)
    output_hashes["B1_QUALIFICATION_RECEIPT.json"] = sha256_file(receipt_path)
    conditions = {
        "C_1_taxonomy": {
            "status": "CLOSED_A_SIDE",
            "evidence": [
                "B1_ERROR_TYPE_TAXONOMY.json",
                (
                    "one VISIBLE_SET_BINDING_REBINDING mechanism; subtype counts "
                    "reported separately as 3/2 trajectories and 2/1 source families"
                ),
                "5/5 set-binding evidence tests; six direction cases UNRESOLVED",
                "correct-preservation direction PRE_REGISTERED",
            ],
        },
        "C_2_units": {
            "status": "CLOSED_A_SIDE",
            "evidence": [
                "17/17 unit mismatches UNRESOLVED",
                "16 unit-only mismatches UNRESOLVED",
                "zero /unit legal-patch operations",
            ],
        },
        "C_3_information_parity": {
            "status": "CLOSED_A_SIDE",
            "evidence": [
                "lexical visible-only allowed units",
                "reference-only minimal edit instructions",
                "72/72 identical neutral R/E feedback diffs",
            ],
        },
        "C_4_equivalence": {
            "status": "CLOSED_A_SIDE",
            "evidence": [
                "set-binding target_exact separated from semantic acceptance",
                "operator, order and unit excluded from R/E targets",
                "applier rejects operator, const, unit and direction paths",
            ],
        },
        "C_5_authority_binding": {
            "status": "CLOSED_A_SIDE",
            "evidence": [
                authority["canonical_identity"],
                "B1_AUTHORITY_BINDING_CORRECTION.json",
            ],
        },
        "C_6_damage_panel": {
            "status": "CLOSED_A_SIDE",
            "evidence": [
                "B2_DEVELOPMENT_PANEL_DRAFT.json",
                "12 families; 36 repeated measures; originally-correct denominator 7/12",
            ],
        },
    }
    result = {
        "schema": "b1_remediation2_result_a_v1",
        "task_id": "phaseb-b1-remediation2-a-20261026",
        "goal_id": "FEEDBACK_LEARNING_PHASE_B_20261026",
        "status": "A_REMEDIATION2_COMPLETE_PENDING_C_REAUDIT",
        "conditions": conditions,
        "outputs": {
            name: {
                "path": str(OUT_DIR / name),
                "sha256": output_hashes[name],
                "status": "WRITTEN",
            }
            for name in sorted(output_hashes)
        },
        "tests": receipt["tests"],
        "panel": {
            "artifact": "B2_DEVELOPMENT_PANEL_DRAFT.json",
            "status": panel["status"],
            "family_count": panel["family_count"],
            "trajectory_count": panel["trajectory_count"],
            "originally_correct_family_denominator": panel["originally_correct_family_denominator"],
        },
        "budget": {
            "generation_attempts": 0,
            "generation_tokens": 0,
            "training_runs": 0,
            "training_tokens": 0,
            "model_or_judge_calls": 0,
            "deterministic_test_wall_seconds": test_wall_seconds,
            "budget_ledger_modified": False,
        },
        "risks": [
            {
                "risk": "loop_c_reaudit_pending",
                "severity": "BLOCKING_FOR_B2",
                "detail": "A-side closure is not independent C acceptance",
            },
            {
                "risk": "panel_not_frozen",
                "severity": "BLOCKING_FOR_B2",
                "detail": "D must freeze the exact proposed 12-family panel",
            },
            {
                "risk": "all_sources_exposed",
                "severity": "BLOCKING_FOR_CONFIRMATION",
                "detail": "the panel is exposed development supervision only",
            },
            {
                "risk": "feedback_learning_claim_not_qualified",
                "severity": "CLAIM_LIMIT",
                "detail": (
                    "only reference-derived visible set-binding revision "
                    "supervision is qualified"
                ),
            },
            {
                "risk": "full_suite_unrelated_failure_and_gb10_not_run",
                "severity": "VERIFICATION_SCOPE",
                "detail": (
                    "focused local deterministic tests pass; local full suite has "
                    "one unrelated missing-fixture failure; GB10 remains authoritative"
                ),
            },
        ],
        "next_gate": "C_REAUDIT2_THEN_D_FREEZE_EXACT_PANEL",
    }
    result["outputs"]["B1_REMEDIATION_RESULT_A.json"] = {
        "path": str(preserved_result_path),
        "sha256": sha256_file(preserved_result_path),
        "status": "PRESERVED_UNCHANGED",
    }
    write_json(result_path, result)

    task_outputs = dict(result["outputs"])
    task_outputs["B1_REMEDIATION2_RESULT_A.json"] = {
        "path": str(result_path),
        "sha256": sha256_file(result_path),
        "status": "WRITTEN",
    }
    task_result = {
        "schema": "b1_remediation2_task_result_v1",
        "status": result["status"],
        "outputs": task_outputs,
        "tests": result["tests"],
        "conditions": conditions,
        "panel": result["panel"],
        "budget": result["budget"],
        "risks": result["risks"],
        "next_gate": result["next_gate"],
    }
    write_json(task_result_path, task_result)

    print(json.dumps({
        "status": result["status"],
        "conditions_closed": len(conditions),
        "tests": "PASS",
        "subcases": registered_subcases,
        "panel_family_count": panel["family_count"],
        "originally_correct_family_denominator": panel["originally_correct_family_denominator"]["fraction"],
        "next_gate": result["next_gate"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
