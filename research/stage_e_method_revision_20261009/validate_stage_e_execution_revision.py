#!/usr/bin/env python3
"""Validate the authorized Stage E claim revision and Stage D qualification packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PAPER = ROOT / "paper"
OUT = TASK / "stage_e_execution_revision_receipt.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docx_text(path: Path) -> str:
    document = Document(path)
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


def main() -> int:
    errors: list[str] = []
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        if not passed:
            errors.append(f"{name}: {detail}")

    markdown_path = PAPER / "teacher_review_draft_v1.md"
    docx_path = PAPER / "teacher_review_draft_v1.docx"
    manifest_path = PAPER / "claim_manifest_v1.json"
    markdown = markdown_path.read_text(encoding="utf-8")
    word = docx_text(docx_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    required = (
        "0/13 OCR-like injections were visible across 11 table clusters",
        "positive affine transformations",
        "identical rankings and ROC geometry",
        "not empirically identifiable",
        "historical fixed-threshold equality",
        "[0, 24.71%]",
        "[0, 28.49%]",
    )
    forbidden = (
        "after matched-false-positive-rate calibration",
        "every bootstrap replicate has zero protocol difference",
        "do not improve matched-FPR discrimination",
        "not matched-FPR discriminability",
        "equivalent after calibration",
    )
    for text_name, text in (("markdown", markdown), ("docx", word)):
        for phrase in required:
            check(f"{text_name}:required:{phrase}", phrase in text)
        for phrase in forbidden:
            check(f"{text_name}:forbidden:{phrase}", phrase not in text)

    zero_note = (ROOT / "docs/research/stage_e_zero_event_uncertainty_note_v1.md").read_text(encoding="utf-8")
    check("zero_note:injection_interval", "[0,24.71%]" in zero_note)
    check("zero_note:table_interval", "[0,28.49%]" in zero_note)
    check("zero_note:distinct_estimands", "separate table-level estimand" in zero_note)
    check("zero_note:no_fake_clustered_ci", "clustered 95% CI of 0/13" not in zero_note)

    for claim in manifest["claims"]:
        for token in claim["manuscript_tokens"]:
            check(f"manifest:{claim['id']}:{token}", token in markdown)
        for evidence in claim["evidence"]:
            check(f"manifest:{claim['id']}:evidence:{evidence}", (ROOT / evidence).is_file())

    freeze_path = TASK / "multileaf_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    check("multileaf:gate", freeze["status"] == "MULTILEAF_READY_FOR_EXECUTION", freeze["status"])
    check("multileaf:not_executed", freeze["formal_experiment_executed"] is False)
    for stage in ("M", "R", "N"):
        check(f"multileaf:{stage}:clusters", freeze["counts"][stage]["clusters"] == 24)
        check(f"multileaf:{stage}:injections", freeze["counts"][stage]["injections"] == 72)
        check(f"multileaf:{stage}:sample_rows", len(freeze["samples"][stage]) == 72)
    predictor = freeze["predictor_contract"]
    check("multileaf:classifier", predictor["classifier"].startswith("deterministic nearest-centroid"))
    check("multileaf:tie_rule", "scored incorrect" in predictor["tie_rule"])
    check("multileaf:permutation_seed", predictor["permutation_seed"] == 20261011)
    check("multileaf:permutation_replicates", predictor["permutation_replicates"] == 10000)
    check("multileaf:bootstrap_seed", predictor["bootstrap_seed"] == 20261012)
    check("multileaf:bootstrap_replicates", predictor["bootstrap_replicates"] == 10000)
    check("multileaf:generator_hash", freeze["generator"]["sha256"] == sha256_file(TASK / "build_multileaf_freeze.py"))
    n_smoke = [sample["generation_smoke"] for sample in freeze["samples"]["N"]]
    check("multileaf:N_original_identity", all(item["original_identity_pass"] for item in n_smoke))
    check("multileaf:N_mutated_identity", all(not item["mutated_identity_pass"] for item in n_smoke))

    qualification_path = TASK / "stage_d_reference_source_qualification.json"
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    prm = qualification["prm800k"]
    agent = qualification["agent_distillation"]
    check("stage_d:licence_policy", "LICENCE_PENDING" in qualification["licence_policy"]["data_model"])
    check("prm:gate", prm["gate"] == "PRM_REFERENCE_READY", prm["gate"])
    check("prm:official_correct", prm["phase2_terminal_answer_correctness"]["correct"] == 659)
    check("prm:official_incorrect", prm["phase2_terminal_answer_correctness"]["incorrect"] == 2103)
    check("prm:data_licence", prm["data_licence"] == "LICENCE_PENDING")
    check("agent:gate", agent["gate"] == "DATA_CAPABLE_LICENCE_PENDING_NOT_PILOT_READY", agent["gate"])
    check("agent:rows", agent["rows"] == 1928)
    check("agent:no_step_reward", agent["step_reward_rows"] == 0)
    check("agent:no_negative_terminal", agent["normalized_score_counts"]["negative"] == 0)
    check("agent:data_licence", agent["data_licence"] == "LICENCE_PENDING")

    receipt = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "authorized Stage E matched-FPR claim correction plus multi-leaf/Stage D freeze; no formal multi-leaf or training",
        "files": {
            str(path.relative_to(ROOT)): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in (
                markdown_path,
                docx_path,
                manifest_path,
                ROOT / "paper/teacher_review_readiness_v2.md",
                ROOT / "docs/research/stage_e_multileaf_preregistration_v1.md",
                ROOT / "docs/research/stage_e_multileaf_power_plan_v1.md",
                ROOT / "docs/research/prm800k_reference_track_audit_v1.md",
                ROOT / "docs/research/stage_d_process_signal_requirements_v1.md",
                ROOT / "docs/research/stage_e_paper_upgrade_plan_v1.md",
                freeze_path,
                qualification_path,
            )
        },
        "checks_passed": sum(bool(item["pass"]) for item in checks),
        "checks_total": len(checks),
        "errors": errors,
        "checks": checks,
        "forbidden_action_counts": {
            "formal_multileaf_runs": 0,
            "training_runs": 0,
            "gpu_calls": 0,
            "judge_calls": 0,
        },
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "checks": f"{receipt['checks_passed']}/{receipt['checks_total']}",
        "errors": errors,
        "output": str(OUT),
    }, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
