#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
VALIDATION_ROOT = TASK_ROOT / "validation"
MANIFEST_PATH = VALIDATION_ROOT / "ARTIFACT_HASHES.json"
RECEIPT_PATH = VALIDATION_ROOT / "VALIDATION_RECEIPT.json"
AUTHORITY_PATH = REPO_ROOT / "docs/research/LOOP_D_RESEARCH_PROMPT.md"
AUTHORITY_BLOB = "a2463f555f4ede2afcebb14dea2b627a0e5b99db"
AUTHORITY_SHA256 = "1414d5b1ce4dc1b47c736c2b5d661366b19d55faa3736dbae5d7c7a7066aac93"
EXPECTED_JSON_COUNT = 45
EXPECTED_JSONL_COUNT = 6
OWNED_THESIS_PATHS = (
    REPO_ROOT
    / "research/feedback_learning_phase_b_20261026_v1/thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md",
    REPO_ROOT
    / "research/feedback_learning_phase_b_20261026_v1/thesis_draft/EVIDENCE_TABLE.md",
)
EXCLUDED_JSON = {MANIFEST_PATH, RECEIPT_PATH}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def artifact_paths() -> list[Path]:
    paths = []
    for path in TASK_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path in EXCLUDED_JSON or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        paths.append(path)
    paths.extend(path for path in OWNED_THESIS_PATHS if path.is_file())
    return sorted(set(paths), key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def validate_parsers() -> dict:
    json_paths = sorted(
        path
        for path in TASK_ROOT.rglob("*.json")
        if path not in EXCLUDED_JSON and "__pycache__" not in path.parts
    )
    jsonl_paths = sorted(
        path
        for path in TASK_ROOT.rglob("*.jsonl")
        if "__pycache__" not in path.parts
    )
    for path in json_paths:
        read_json(path)
    jsonl_records = 0
    for path in jsonl_paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc
                jsonl_records += 1
    actual_json_count = len(json_paths) + len(EXCLUDED_JSON)
    if actual_json_count != EXPECTED_JSON_COUNT:
        raise ValueError(
            f"expected {EXPECTED_JSON_COUNT} JSON files, found {actual_json_count}"
        )
    if len(jsonl_paths) != EXPECTED_JSONL_COUNT:
        raise ValueError(
            f"expected {EXPECTED_JSONL_COUNT} JSONL files, found {len(jsonl_paths)}"
        )
    return {
        "json_files": actual_json_count,
        "jsonl_files": len(jsonl_paths),
        "jsonl_records": jsonl_records,
        "parsed_without_error": True,
    }


def validate_authority() -> dict:
    blob = subprocess.check_output(
        ["git", "hash-object", str(AUTHORITY_PATH)],
        cwd=REPO_ROOT,
        text=True,
    ).strip()
    digest = sha256_file(AUTHORITY_PATH)
    if blob != AUTHORITY_BLOB or digest != AUTHORITY_SHA256:
        raise ValueError(
            f"authority mismatch: blob={blob}, lf_sha256={digest}"
        )
    return {
        "path": AUTHORITY_PATH.relative_to(REPO_ROOT).as_posix(),
        "git_blob": blob,
        "lf_sha256": digest,
        "matches_task_authority": True,
    }


def validate_substantive_receipts() -> dict:
    source = read_json(TASK_ROOT / "paper_e_word/SOURCE_CHECK_RECEIPT.json")
    scoring = read_json(TASK_ROOT / "scoring_v3/SCORING_TEST_RECEIPT.json")
    exposure = read_json(TASK_ROOT / "exposure/EXPOSURE_MANIFEST.json")
    freeze = read_json(TASK_ROOT / "exposure/PANEL_FREEZE.json")
    generation = read_json(TASK_ROOT / "generation/GENERATION_RECEIPT.json")
    diagnostic = read_json(
        TASK_ROOT / "scoring_v3/results/DIAGNOSTIC_SUMMARY.json"
    )
    budget_fault = read_json(TASK_ROOT / "budget/BUDGET_FAULT_TEST_RECEIPT.json")
    a_return = read_json(TASK_ROOT / "A_RETURN.json")
    checks = {
        "word_source_check_pass": source.get("status") == "PASS",
        "scoring_targeted_7_of_7": scoring.get("v3_targeted_controls", {}).get("passed")
        == 7,
        "scoring_v2_regression_17_of_17": scoring.get(
            "v2_regression_controls", {}
        ).get(
            "passed"
        )
        == 17,
        "exposure_eligible_38": exposure.get("eligible_unexposed_family_count") == 38,
        "panel_selected_8": freeze.get("selection", {}).get("family_count") == 8,
        "panel_frozen_before_generation": freeze.get("status")
        == "FROZEN_PRE_MODEL_OUTPUT",
        "generation_24_rows": generation.get("primary_attempts_completed") == 24,
        "diagnostic_24_rows": diagnostic.get("rows") == 24,
        "budget_fault_11_of_11": budget_fault.get("status") == "PASS"
        and budget_fault.get("test_run") == 11,
        "a_return_complete_pending_gates": a_return.get("status")
        == "A_TASK_COMPLETE_PENDING_D_CONVERSION_AND_C_REVIEW",
        "thesis_method_results_updated": "## 11. Word 交付、Scoring V3"
        in OWNED_THESIS_PATHS[0].read_text(encoding="utf-8"),
        "thesis_evidence_updated": "Word/Scoring V3/同源新表族 A补充"
        in OWNED_THESIS_PATHS[1].read_text(encoding="utf-8"),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"substantive receipt checks failed: {failed}")
    return checks


def main() -> None:
    parser_counts = validate_parsers()
    authority = validate_authority()
    substantive_checks = validate_substantive_receipts()
    paths = artifact_paths()
    artifacts = {
        path.relative_to(REPO_ROOT).as_posix(): sha256_file(path) for path in paths
    }
    manifest = {
        "schema": "word_scoring_new_family_artifact_hashes_v1",
        "path_base": "repository_root",
        "hash_algorithm": "sha256",
        "generated_date": "2026-10-27",
        "excluded": [
            "research/word_scoring_new_family_20261027_v1/validation/ARTIFACT_HASHES.json",
            "research/word_scoring_new_family_20261027_v1/validation/VALIDATION_RECEIPT.json",
            "**/__pycache__/**",
            "**/*.pyc",
        ],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    ledger_path = Path(
        "/home/testuser/wzh/research_runs/persistent_budget/"
        "word_new_family_20261027/ledger.jsonl"
    )
    ledger_sha256 = sha256_file(ledger_path)
    expected_ledger_sha256 = (
        "c7bd1f7207b610ad17c194727a8d0affdb0105996ed2e97603cfeea408ca71ac"
    )
    if ledger_sha256 != expected_ledger_sha256:
        raise ValueError(
            f"persistent ledger hash mismatch: {ledger_sha256}"
        )
    receipt = {
        "schema": "word_scoring_new_family_validation_receipt_v1",
        "task_id": "word-scoring-new-family-a-20261027",
        "status": "PASS",
        "generated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(
            timespec="seconds"
        ),
        "path_base": "repository_root",
        "authority": authority,
        "parser_validation": parser_counts,
        "substantive_receipt_checks": substantive_checks,
        "artifact_validation": {
            "manifest_path": MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(),
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "artifact_count": len(artifacts),
            "all_listed_hashes_recomputed": True,
        },
        "persistent_ledger": {
            "path": str(ledger_path),
            "sha256": ledger_sha256,
            "matches_a_return": ledger_sha256 == expected_ledger_sha256,
        },
        "excluded_from_claim": [
            "DOCX/PDF visual acceptance",
            "formal C acceptance",
            "cross-source validation",
            "historical pretraining disjointness",
            "new-family method gain",
        ],
    }
    RECEIPT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for path in paths:
        expected = artifacts[path.relative_to(REPO_ROOT).as_posix()]
        if sha256_file(path) != expected:
            raise ValueError(f"artifact changed during validation: {path}")
    print(
        json.dumps(
            {
                "status": "PASS",
                "json_files": parser_counts["json_files"],
                "jsonl_files": parser_counts["jsonl_files"],
                "artifacts": len(artifacts),
                "manifest_sha256": receipt["artifact_validation"][
                    "manifest_sha256"
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
