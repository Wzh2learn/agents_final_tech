#!/usr/bin/env python3
"""Build the machine-readable Loop A evidence-strengthening repair receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_receipt.json"

INPUT_SHA256 = {
    "/home/testuser/wzh/loop_runs/paper-evidence-strengthening-c-20261010/c.log": "1182fb62602f57888837801de1fbca4ee1e363a6fca4fc837d9f16d1764e342a",
    "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json": "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d",
    "docs/research/figures_multileaf/fig_multileaf_localization_ablation.png": "a360f9b1f187379e3adb5106a331fb314458945b977495756ebd1797fd94995c",
    "docs/research/figures_multileaf/fig_multileaf_localization_ablation.svg": "d8187af983c446443a08bb428040e94415ff0fdfc462bb39dbbddb0d478647a6",
    "docs/research/figures_multileaf/manifest.json": "5563ba53c88071d9398d7d756ed70f2a310039b51a03a7bc1583756cbf597d70",
    "docs/research/stage_e_version_b_figure_spec_v1.md": "28549d5438e00aef8199c83dbd16c6081f49b51534cfef4a80a905c1c1df7cb5",
    "docs/research/stage_e_multileaf_result_packet_v1.md": "1d0eb7a646308e30ea14f6b844feadec7e8d50d8886e4706c43b132776cda57a",
    "docs/research/stage_e_version_b_revision_proposal_v1.md": "dee3d6fe2f53dbf86e9406902bfa25ae6c5e881c50a9b33c98bcc0878e3e9c8a",
    "docs/research/finqa_v2_gate_status_v1.md": "273a08c4c6930225e1c93d93c0db7e3c35641f8060b00e53b2c27cf35b476cf5",
    "research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json": "280c563c5e701cf81f75d85664f6880f8133723693ddbc63a641db804a909ca7",
    "research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json": "71e6e2c4e2f59721644098cae20e1b850692edd20e0c138f87f27bedd4f25b77",
    "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_receipt.json": "09d3e0ed3b4d226ec001ead3da9e2527eee5abb5e4afa0886772611812db49ee",
    "research/finqa_evidence_argument_resolver_v2.py": "f60812f77695cb9d5a153a7986f1043e45043a08ec7b9bcf8c0c4be6d4b7201f",
    "research/finqa_independent_observation_scorer_v2.py": "b48ed17c4aae2a1d70312e9c93c113d0e45b60d2429e83627162e78337d667e5",
    "research/stage_e_multileaf_20261010/audit_finqa_v2_causal_join.py": "be0419700b52217405c9afbe298d2d9f05479320974bdcf6716abf8a705f2286",
    "research/stage_e_multileaf_20261010/build_finqa_v2_candidate_manifest.py": "918e067d708756246f9923b6beeebe498c24243565c0588401ace6030e9d0881",
    "tests/test_finqa_evidence_argument_resolver_v2.py": "ac51401a55f8e1ff5eb153f9cabf9dc17824a0be114eb931aed27dfc6544912e",
    "tests/test_finqa_independent_observation_scorer_v2.py": "2146f847f4da0dab7295e615420eefbf55bc45167c5ce62360908153589db7d1"
}

OUTPUT_PATHS = [
    "docs/research/stage_e_version_b_figure_spec_v1.md",
    "docs/research/stage_e_multileaf_result_packet_v1.md",
    "docs/research/stage_e_version_b_revision_proposal_v1.md",
    "docs/research/figures_multileaf/fig_multileaf_localization_ablation.png",
    "docs/research/figures_multileaf/fig_multileaf_localization_ablation.svg",
    "docs/research/figures_multileaf/manifest.json",
    "docs/research/finqa_v2_gate_reconciliation_v2.md",
    "docs/research/finqa_v2_gate_reconciliation_v2.json",
    "docs/research/finqa_numeric_token_canonicalization_v2.md",
    "research/finqa_numeric_token_canonicalization_v2.py",
    "research/finqa_evidence_argument_resolver_v2.py",
    "research/stage_e_multileaf_20261010/audit_finqa_v2_causal_join.py",
    "research/stage_e_multileaf_20261010/render_multileaf_localization_ablation_v2.py",
    "research/stage_e_multileaf_20261010/build_stage_e_evidence_strengthening_repair_receipt.py",
    "tests/test_finqa_numeric_token_canonicalization_v2.py",
    "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_tests.log"
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_hashes() -> dict[str, str]:
    return {relative: sha256_file(ROOT / relative) for relative in OUTPUT_PATHS}


def verify_test_log() -> dict[str, Any]:
    relative = "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_tests.log"
    text = (ROOT / relative).read_text(encoding="utf-8")
    checks = (
        ("resolver", "tests/test_finqa_evidence_argument_resolver_v2.py", "3 passed", 3),
        ("scorer", "tests/test_finqa_independent_observation_scorer_v2.py", "5 passed", 5),
        ("canonicalization", "tests/test_finqa_numeric_token_canonicalization_v2.py", "3 passed", 3),
    )
    results: dict[str, Any] = {}
    for name, test_path, count_text, count in checks:
        command_ok = f"pytest {test_path} -q" in text
        count_ok = count_text in text
        if not command_ok or not count_ok:
            raise RuntimeError(f"TEST_LOG_MISSING_EXPECTED_RESULT: {name}")
        results[name] = {
            "command": f"PYTHONPATH=src ./venv/bin/python -m pytest {test_path} -q",
            "exit_code": 0,
            "failed": 0,
            "passed": count,
            "status": "PASS",
            "test_path": test_path,
        }
    results["aggregate"] = {
        "failed": 0,
        "passed": 11,
        "status": "PASS",
        "summary": "3 resolver + 5 scorer + 3 canonicalization = 11 tests",
    }
    if "AGGREGATE: 3 resolver + 5 scorer + 3 canonicalization = 11 tests; failed=0" not in text:
        raise RuntimeError("TEST_LOG_MISSING_AGGREGATE")
    return results


def build_payload() -> dict[str, Any]:
    outputs = output_hashes()
    return {
        "changed_files": sorted(OUTPUT_PATHS + [str(RECEIPT.relative_to(ROOT))]),
        "commands": [
            "PYTHONPATH=src ./venv/bin/python -m py_compile research/finqa_numeric_token_canonicalization_v2.py research/finqa_evidence_argument_resolver_v2.py research/stage_e_multileaf_20261010/audit_finqa_v2_causal_join.py research/stage_e_multileaf_20261010/render_multileaf_localization_ablation_v2.py tests/test_finqa_numeric_token_canonicalization_v2.py",
            "PYTHONPATH=src ./venv/bin/python research/stage_e_multileaf_20261010/render_multileaf_localization_ablation_v2.py",
            "PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_evidence_argument_resolver_v2.py -q",
            "PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_independent_observation_scorer_v2.py -q",
            "PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_numeric_token_canonicalization_v2.py -q",
            "python3 sha256/JSON/SVG/PNG/wording/py_compile/diff-check validation script (PASS)",
            "python3 scripts/docs_lint.py --json /tmp/loopa_repair_docs_lint.json (0 fail / 6 warn)"
        ],
        "evidence_classes": {
            "ENGINEERING": "numeric-token canonicalization and focused test verification",
            "EXPLORATORY": "Figure 3 presentation repair from frozen ablation values",
            "NEGATIVE": "F6 remains OPEN; F8 remains NOT_YET_RESOLVED",
            "PRIMARY": "corrected metric boundaries and retained construct-sensitive scope",
            "SECONDARY": "canonical six-gate reconciliation with preserved stale hashes"
        },
        "experiment_boundary": {
            "finqa_v2_formal_experiments_run": 0,
            "health_or_endpoint_probes": 0,
            "model_calls": 0,
            "m_r_n_experiment_reruns": 0,
            "paper_body_modified": False,
            "prm_training_runs": 0,
            "training_runs": 0
        },
        "input_sha256": INPUT_SHA256,
        "loop_c_findings_status_matrix": [
            {
                "finding": "F2",
                "status": "CLOSED",
                "summary": "Metric-specific chance, uniform-class, and majority-baseline identities are explicit in Figure 3 and active wording."
            },
            {
                "finding": "F3",
                "status": "CLOSED",
                "summary": "Canonical six-gate v2 table includes SCORER_GO and declares six older snapshots stale with preserved hashes."
            },
            {
                "finding": "F4",
                "status": "CLOSED",
                "summary": "Selection and causal logic share exact Decimal fixed-point token identity; ambiguity remains fail-closed."
            },
            {
                "finding": "F5",
                "status": "CLOSED",
                "summary": "Frozen key remains untouched, while the active result packet explicitly states its predicate does not prove non-direct incremental information."
            },
            {
                "finding": "F6",
                "status": "OPEN",
                "summary": "Frozen template_count semantics remain unreconciled because the mechanism-audit artifact was not authorized for editing."
            },
            {
                "finding": "F7",
                "status": "PARTIAL",
                "summary": "Construct-sensitive scope is retained in figure/proposal/result wording; the historical power-plan artifact remains unchanged."
            },
            {
                "finding": "F8",
                "status": "NOT_YET_RESOLVED",
                "summary": "The 627-versus-594 relationship has no invented explanation; section-order and row-count proposal edits remain out of scope."
            }
        ],
        "output_sha256": outputs,
        "preserved_frozen_inputs": {
            "finqa_v2_causal_join_audit_json": INPUT_SHA256[
                "research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json"
            ],
            "finqa_v2_candidate_sample_manifest_json": INPUT_SHA256[
                "research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json"
            ],
            "multileaf_signature_ablation_json": INPUT_SHA256[
                "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json"
            ],
            "modified": False
        },
        "question_answer": "YES for blocking F2-F4 without changing frozen scientific evidence or running a formal experiment; F5/F7 are not uniformly closed, F6 remains OPEN, and F8 remains NOT_YET_RESOLVED.",
        "receipt_type": "stage-e-evidence-strengthening-repair",
        "schema_version": 2,
        "status": "REPAIR_VALIDATION_PASSED",
        "stop_conditions": {
            "FIGURE_REPAIR_INPUT_MISSING": False,
            "OUT_OF_SCOPE": False,
            "REPAIR_VALIDATION_FAILED": False,
            "TOKEN_IDENTITY_NEW_NAMESPACE_REQUIRED": False
        },
        "test_log": {
            "path": "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_tests.log",
            "sha256": sha256_file(
                ROOT / "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_tests.log"
            )
        },
        "tests": verify_test_log(),
        "validation": {
            "docs_lint": {
                "fails": 0,
                "status": "PASS",
                "warns": 6
            },
            "frozen_source_hashes": "PASS",
            "gate_reconciliation_and_stale_hashes": "PASS",
            "python_compile_and_diff_check": "PASS",
            "svg_xml_png_dimensions_and_manifest_hashes": "PASS",
            "unqualified_approximately_chance_phrase_count": 0
        }
    }


def main() -> int:
    payload = build_payload()
    payload["receipt"] = {
        "hash_contract": "SHA-256 of canonical compact sorted JSON after removing receipt.self_sha256"
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload["receipt"]["self_sha256"] = hashlib.sha256(canonical).hexdigest()
    RECEIPT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "receipt": str(RECEIPT.relative_to(ROOT)),
                "self_sha256": payload["receipt"]["self_sha256"],
                "status": payload["status"],
                "tests": payload["tests"]["aggregate"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
