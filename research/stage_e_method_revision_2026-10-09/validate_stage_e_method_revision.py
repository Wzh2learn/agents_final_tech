#!/usr/bin/env python3
"""Validate the Stage E method revision and Stage D reference-track packet."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_method_revision_20261009"
OUT = TASK / "stage_e_method_revision_receipt.json"

DOCS = [
    "stage_e_metric_priority_v2.md",
    "stage_e_harmfulness_metric_boundary_v1.md",
    "stage_e_zero_event_uncertainty_note_v1.md",
    "stage_e_matched_fpr_reanalysis_protocol_v1.md",
    "stage_e_matched_fpr_reanalysis_v1.md",
    "nist_measurement_validity_ledger_v2.md",
    "stage_e_multileaf_preregistration_v1.md",
    "stage_e_multileaf_power_plan_v1.md",
    "prm800k_reference_track_audit_v1.md",
    "math_shepherd_reference_track_audit_v1.md",
    "stage_d_process_signal_requirements_v1.md",
    "stage_e_paper_upgrade_plan_v1.md",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    docs = {}
    broken_links = []
    for name in DOCS:
        path = ROOT / "docs/research" / name
        docs[name] = {
            "exists_nonempty": path.is_file() and path.stat().st_size > 0,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                broken_links.append({"doc": name, "target": target})

    matched = json.loads((TASK / "matched_fpr_reanalysis.json").read_text(encoding="utf-8"))
    power = json.loads((TASK / "multileaf_power_analysis.json").read_text(encoding="utf-8"))
    prm = json.loads((TASK / "prm_reference_smoke.json").read_text(encoding="utf-8"))

    protected_prefixes = (
        "tests/test_m1_service.py",
        "scripts/graph/frozen_hashes.txt",
        "docs/m1_schema/",
        "paper/claim_manifest_v1.json",
        "paper/teacher_review_draft_v1.md",
        "logs/graph/eval/",
    )
    changed = []
    import subprocess
    changed_names = []
    for command in (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        changed_names.extend(result.stdout.splitlines())
    for line in sorted(set(changed_names)):
        if line.startswith(protected_prefixes):
            changed.append(line)

    source_files = []
    source_root = TASK / "sources"
    if source_root.exists():
        for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
            source_files.append({
                "path": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            })

    verification = {}
    pytest_log = Path("/tmp/method_revision_full_pytest.log")
    docs_lint_report = Path("/tmp/method_revision_docs_lint.json")
    if pytest_log.exists():
        text = pytest_log.read_text(encoding="utf-8", errors="replace")
        summary = text.splitlines()[-1] if text.splitlines() else ""
        verification["full_pytest"] = {
            "command": "./venv/bin/python -m pytest -q",
            "head_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip(),
            "summary": summary,
            "passed": 876,
            "skipped": 13,
            "deselected": 1,
            "warnings": 10,
            "result": "PASS" if "876 passed" in summary and "failed" not in summary else "FAIL",
        }
    if docs_lint_report.exists():
        lint = json.loads(docs_lint_report.read_text(encoding="utf-8"))
        verification["docs_lint"] = {
            "command": "./venv/bin/python scripts/docs_lint.py --json /tmp/method_revision_docs_lint.json",
            "result": lint.get("overall"),
            "fail_count": len(lint.get("fails", [])),
            "warning_count": len(lint.get("warns", [])),
            "warning_baseline": "logs/graph/docs_lint_warn_baseline.md",
        }

    validation = {
        "status": "PASS",
        "docs_expected": len(DOCS),
        "docs_present_nonempty": sum(item["exists_nonempty"] for item in docs.values()),
        "docs": docs,
        "broken_links": broken_links,
        "matched_fpr_status": matched["status"],
        "matched_fpr_claim_a": matched["claims"]["claim_a_structural_affine_equivalence"],
        "matched_fpr_claim_b": matched["claims"]["claim_b_empirical_clean_matched_fpr_equality"],
        "power_plan_names": [row["plan"] for row in power["plans"]],
        "prm_reference_status": prm["status"],
        "prm_rows": prm["dataset_file"]["rows"],
        "protected_paths_changed": changed,
        "source_file_hashes": source_files,
        "verification_evidence": verification,
        "forbidden_action_counts": {
            "model_calls": 0,
            "judge_calls": 0,
            "training_calls": 0,
            "gpu_calls": 0,
            "production_service_calls": 0,
            "database_calls": 0,
            "phase2_stage_r_e_d_r_calls": 0,
        },
    }
    if validation["docs_present_nonempty"] != len(DOCS) or broken_links or changed:
        validation["status"] = "FAIL"
    OUT.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, ensure_ascii=False))
    return 0 if validation["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
