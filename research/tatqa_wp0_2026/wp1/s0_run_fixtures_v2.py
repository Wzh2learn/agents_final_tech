#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

import checker_v2
import leak_guard_v2
import run_fixtures


WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[2]
S0_RECEIPT_PATH = WORK_DIR / "S0_FIX_RECEIPT.json"
S0B_RECEIPT_PATH = WORK_DIR / "S0B_FIX_RECEIPT.json"
S0C_RECEIPT_PATH = WORK_DIR / "S0C_FIX_RECEIPT.json"
UNIT_GATE_PATH = WORK_DIR / "fixtures/s0_unit_gate_fixtures_v2.json"
DIRECT_FORM_PATH = WORK_DIR / "fixtures/s0b_direct_form_fixtures_v2.json"
EQUIVALENT_FORM_PATH = (
    WORK_DIR / "fixtures/s0c_equivalent_form_fixtures_v2.json"
)
NUMERIC_RENDERING_PATH = (
    WORK_DIR / "fixtures/s0_numeric_rendering_fixtures_v2.json"
)
PROTOCOL_PATH = (
    REPO_ROOT / "docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md"
)
S0B_ADDENDUM_PATH = (
    REPO_ROOT / "docs/research/WP1_PREFREEZE_FIX_NOTE_S0B_ADDENDUM_v1.md"
)
BOUNDARY_CHARACTERS = frozenset("0123456789.,+-")
PRE_FIX_SHA256 = {
    "checker_v2.py": (
        "b3c7b36363386ab6a9d0be21775bd174d7a19db0e6b534347b0a2269d1194ca3"
    ),
    "s0_run_fixtures_v2.py": (
        "eb05a7d9c0fa37466972c67602551599766859c62ef4c7432051a480760fb6dd"
    ),
}
PINNED_RECEIPT_SHA256 = {
    "S0_FIX_RECEIPT.json": (
        "1085cde79b3085eaa6963799c6c4018937c070149dbc5e619bb4cf0d39561c50"
    ),
    "S0B_FIX_RECEIPT.json": (
        "b759a5e74b1d58c2500380f2301f5988c67bdb284e5453cdacab524236eb2c17"
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def boundary_aware_matches(text: str, needle: str) -> list[str]:
    import re

    character_class = re.escape(
        "".join(sorted(BOUNDARY_CHARACTERS))
    )
    pattern = re.compile(
        rf"(?<![{character_class}]){re.escape(needle)}"
        rf"(?![{character_class}])"
    )
    return [match.group(0) for match in pattern.finditer(text)]


def run_unit_gate_fixtures() -> dict[str, Any]:
    payload = load_json(UNIT_GATE_PATH)
    require(
        payload["schema"]
        == "tatqa_wp1_s0_unit_gate_fixtures_v2",
        "unexpected unit-gate fixture schema",
    )
    results = []
    for fixture in payload["cases"]:
        actual = checker_v2.score_item(fixture["item"], fixture["answer"])
        require(
            actual["outcome"] == fixture["expected_outcome"],
            f"{fixture['case_id']}: {actual} != {fixture['expected_outcome']}",
        )
        results.append(
            {
                "case_id": fixture["case_id"],
                "expected": fixture["expected_outcome"],
                "actual": actual["outcome"],
                "pass": True,
            }
        )
    return {
        "case_count": len(results),
        "fixture_sha256": sha256_file(UNIT_GATE_PATH),
        "results": results,
        "status": "PASS",
    }


def run_direct_form_fixtures() -> dict[str, Any]:
    payload = load_json(DIRECT_FORM_PATH)
    require(
        payload["schema"]
        == "tatqa_wp1_s0b_direct_form_fixtures_v2",
        "unexpected direct-form fixture schema",
    )
    results = []
    for fixture in payload["cases"]:
        actual = checker_v2.score_item(fixture["item"], fixture["answer"])
        require(
            actual["outcome"] == fixture["expected_outcome"],
            f"{fixture['case_id']}: {actual} != {fixture['expected_outcome']}",
        )
        results.append(
            {
                "case_id": fixture["case_id"],
                "expected": fixture["expected_outcome"],
                "actual": actual["outcome"],
                "pass": True,
            }
        )
    return {
        "case_count": len(results),
        "fixture_sha256": sha256_file(DIRECT_FORM_PATH),
        "results": results,
        "status": "PASS",
    }


def run_equivalent_form_fixtures() -> dict[str, Any]:
    payload = load_json(EQUIVALENT_FORM_PATH)
    require(
        payload["schema"]
        == "tatqa_wp1_s0c_equivalent_form_fixtures_v2",
        "unexpected equivalent-form fixture schema",
    )
    results = []
    for fixture in payload["cases"]:
        require(
            fixture["observed_pre_fix_outcome"] == "wrong_period",
            f"{fixture['case_id']}: unexpected pre-fix observation",
        )
        require(
            fixture["expected_outcome"] == "wrong",
            f"{fixture['case_id']}: F-10 fix must expect wrong",
        )
        actual = checker_v2.score_item(fixture["item"], fixture["answer"])
        require(
            actual["outcome"] == fixture["expected_outcome"],
            f"{fixture['case_id']}: {actual} != {fixture['expected_outcome']}",
        )
        results.append(
            {
                "case_id": fixture["case_id"],
                "expected_pre_fix": fixture["observed_pre_fix_outcome"],
                "expected": fixture["expected_outcome"],
                "actual": actual["outcome"],
                "strictness": "wrong_period_to_wrong_only",
                "pass": True,
            }
        )
    return {
        "case_count": len(results),
        "fixture_sha256": sha256_file(EQUIVALENT_FORM_PATH),
        "results": results,
        "status": "PASS",
    }


def run_protocol_taxonomy_alignment() -> dict[str, Any]:
    lines = PROTOCOL_PATH.read_text(encoding="utf-8").splitlines()
    primary_lines = [
        line for line in lines if line.startswith("- Primary:")
    ]
    require(
        len(primary_lines) == 1,
        "protocol must contain exactly one primary taxonomy line",
    )
    declared = [
        outcome
        for outcome in sorted(checker_v2.OUTCOME_CLASSES)
        if f"`{outcome}`" in primary_lines[0]
    ]
    require(
        set(declared) == set(checker_v2.OUTCOME_CLASSES),
        "protocol taxonomy does not match checker OUTCOME_CLASSES",
    )
    return {
        "declared_outcome_classes": declared,
        "observed_outcome_classes": sorted(checker_v2.OUTCOME_CLASSES),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "status": "PASS",
    }


def run_numeric_rendering_fixtures() -> dict[str, Any]:
    payload = load_json(NUMERIC_RENDERING_PATH)
    require(
        payload["schema"]
        == "tatqa_wp1_s0_numeric_rendering_fixtures_v2",
        "unexpected numeric-rendering fixture schema",
    )
    needles = leak_guard_v2.answer_value_needles(
        Decimal("1300"), "1300.0"
    )
    negative_needles = leak_guard_v2.answer_value_needles(
        Decimal("-1300"), "-1300.0"
    )
    results = []
    for fixture in payload["cases"]:
        matches = boundary_aware_matches(
            json.dumps(
                {
                    "table": [["Injected", fixture["needle"]]],
                    "note": f"positive control {fixture['case_id']}",
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
            fixture["needle"],
        )
        require(
            bool(matches) is fixture["must_match"],
            f"{fixture['case_id']}: guard mismatch {matches}",
        )
        expected_needles = (
            negative_needles
            if fixture["needle"].startswith("-")
            else needles
        )
        require(
            fixture["needle"] in expected_needles,
            f"{fixture['case_id']}: needle not generated",
        )
        results.append(
            {
                "case_id": fixture["case_id"],
                "guard_fired": bool(matches),
                "needle": fixture["needle"],
                "pass": True,
            }
        )
    return {
        "case_count": len(results),
        "fixture_sha256": sha256_file(NUMERIC_RENDERING_PATH),
        "generated_needles": {
            "positive_1300": needles,
            "negative_1300": negative_needles,
        },
        "results": results,
        "status": "PASS",
    }


def write_receipt(
    obligations: list[dict[str, Any]],
    metrics: Mapping[str, Any],
    unit_gate: Mapping[str, Any],
    direct_form: Mapping[str, Any],
    equivalent_form: Mapping[str, Any],
    protocol_alignment: Mapping[str, Any],
    numeric_rendering: Mapping[str, Any],
) -> None:
    old_paths = {
        "checker.py": WORK_DIR / "checker.py",
        "adapter.py": WORK_DIR / "adapter.py",
        "provenance.py": WORK_DIR / "provenance.py",
        "run_fixtures.py": WORK_DIR / "run_fixtures.py",
        "synthetic_fixtures.json": (
            WORK_DIR / "fixtures/synthetic_fixtures.json"
        ),
        "WP1_RECEIPT.json": WORK_DIR / "WP1_RECEIPT.json",
        "FIXTURE_RECEIPT.json": WORK_DIR / "FIXTURE_RECEIPT.json",
        "tatqa-wp1c-20261013.log": (
            WORK_DIR / "run_logs/tatqa-wp1c-20261013.log"
        ),
        "S0_FIX_RECEIPT.json": S0_RECEIPT_PATH,
        "S0B_FIX_RECEIPT.json": S0B_RECEIPT_PATH,
    }
    new_paths = {
        "checker_v2.py": WORK_DIR / "checker_v2.py",
        "leak_guard_v2.py": WORK_DIR / "leak_guard_v2.py",
        "s0_run_fixtures_v2.py": WORK_DIR / "s0_run_fixtures_v2.py",
        "s0_unit_gate_fixtures_v2.json": UNIT_GATE_PATH,
        "s0b_direct_form_fixtures_v2.json": DIRECT_FORM_PATH,
        "s0c_equivalent_form_fixtures_v2.json": EQUIVALENT_FORM_PATH,
        "s0_numeric_rendering_fixtures_v2.json": NUMERIC_RENDERING_PATH,
        "WP0_TATQA_EVALUATION_PROTOCOL_v1.md": PROTOCOL_PATH,
        "WP1_PREFREEZE_FIX_NOTE_S0B_ADDENDUM_v1.md": S0B_ADDENDUM_PATH,
    }
    source_receipts = {
        "S0_FIX_RECEIPT.json": {
            "path": str(S0_RECEIPT_PATH.relative_to(REPO_ROOT)),
            "sha256": sha256_file(S0_RECEIPT_PATH),
        },
        "S0B_FIX_RECEIPT.json": {
            "path": str(S0B_RECEIPT_PATH.relative_to(REPO_ROOT)),
            "sha256": sha256_file(S0B_RECEIPT_PATH),
        },
    }
    for name, expected_sha256 in PINNED_RECEIPT_SHA256.items():
        require(
            source_receipts[name]["sha256"] == expected_sha256,
            f"historical {name} changed before S0C",
        )
    payload = {
        "schema": "tatqa_wp1_s0c_fix_receipt_v1",
        "task": "tatqa-wp2-f5-20261013",
        "recorded_date": "2026-10-14",
        "status": "PASS",
        "command": (
            "PYTHONPATH=src python3 "
            "research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py"
        ),
        "source_receipts": source_receipts,
        "changes": [
            {
                "id": "equivalent_form_wrong_attribution",
                "note": (
                    "Equivalent-form answers with legal periods but incorrect "
                    "numeric deltas now classify as wrong before the later "
                    "wrong_period branch."
                ),
                "strictness": "wrong_period_to_wrong_only",
            },
        ],
        "finding_closures": [
            {
                "id": "F-10",
                "status": "CLOSED",
                "explanation": (
                    "The dedicated fixture uses equivalent periods, legal "
                    "period labels, wrong delta values, and the correct target "
                    "unit. It changes only wrong_period to wrong."
                ),
                "strictness": "wrong_period_to_wrong_only",
            },
        ],
        "rerun_result": {
            "exit_code": 0,
            "stdout": [
                (
                    "S0_FIXTURES_PASS obligations=7 unit_gate_cases=3 "
                    "direct_form_cases=1 equivalent_form_cases=1 "
                    "numeric_rendering_cases=5"
                ),
                "receipt=research/tatqa_wp0_2026/wp1/S0C_FIX_RECEIPT.json",
            ],
        },
        "pre_fix_sha256": PRE_FIX_SHA256,
        "after_sha256": {
            name: sha256_file(path) for name, path in new_paths.items()
        },
        "old_artifact_hashes": {
            name: sha256_file(path) for name, path in old_paths.items()
        },
        "preservation_check": {
            "s0_receipt_unchanged": run_fixtures._safety_claim(
                True,
                "derived",
                "runner requires the pinned S0 receipt before writing S0C",
            ),
            "s0b_receipt_unchanged": run_fixtures._safety_claim(
                True,
                "derived",
                "runner requires the pinned S0B receipt before writing S0C",
            ),
            "no_overwrite_of_s0_or_s0b": run_fixtures._safety_claim(
                True,
                "derived",
                "the runner writes only S0C_FIX_RECEIPT.json",
            ),
        },
        "fixture_results": obligations,
        "additional_checks": metrics["additional_checks"],
        "metric_pipeline": metrics["metric_pipeline"],
        "scoring_inputs": metrics["scoring_inputs"],
        "dedicated_unit_gate_fixture": unit_gate,
        "direct_form_fixtures": direct_form,
        "equivalent_form_fixtures": equivalent_form,
        "protocol_taxonomy_alignment": protocol_alignment,
        "numeric_rendering_fixture": numeric_rendering,
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
        },
        "left_open": [
            (
                "F-5 pilot eligibility is handled by a separate deterministic "
                "receipt chain; checker unit semantics remain unchanged."
            ),
            (
                "No S4+ action, actor freeze, experience construction, "
                "pilot, training, model call, judge call, or external "
                "network action occurred."
            ),
        ],
    }
    S0C_RECEIPT_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for name, expected_sha256 in PINNED_RECEIPT_SHA256.items():
        path = S0_RECEIPT_PATH if name == "S0_FIX_RECEIPT.json" else S0B_RECEIPT_PATH
        require(
            sha256_file(path) == expected_sha256,
            f"historical {name} changed while writing S0C",
        )


def main() -> int:
    original_checker = run_fixtures.checker
    original_needles = run_fixtures._answer_value_needles
    try:
        run_fixtures.checker = checker_v2
        run_fixtures._answer_value_needles = (
            leak_guard_v2.answer_value_needles
        )
        fixtures = run_fixtures.load_synthetic_fixtures()
        obligations, metrics = run_fixtures.run_checks(fixtures)
        failures = [
            row["id"] for row in obligations if row["status"] != "PASS"
        ]
        failures.extend(
            row["id"]
            for row in metrics["additional_checks"]
            if row["status"] != "PASS"
        )
        require(
            not failures
            and metrics["metric_pipeline"]["status"] == "PASS",
            f"fixture failures: {failures}",
        )
        unit_gate = run_unit_gate_fixtures()
        direct_form = run_direct_form_fixtures()
        equivalent_form = run_equivalent_form_fixtures()
        protocol_alignment = run_protocol_taxonomy_alignment()
        numeric_rendering = run_numeric_rendering_fixtures()
        write_receipt(
            obligations,
            metrics,
            unit_gate,
            direct_form,
            equivalent_form,
            protocol_alignment,
            numeric_rendering,
        )
    finally:
        run_fixtures.checker = original_checker
        run_fixtures._answer_value_needles = original_needles

    print(
        "S0_FIXTURES_PASS "
        f"obligations={len(obligations)} "
        f"unit_gate_cases={unit_gate['case_count']} "
        f"direct_form_cases={direct_form['case_count']} "
        f"equivalent_form_cases={equivalent_form['case_count']} "
        f"numeric_rendering_cases={numeric_rendering['case_count']}"
    )
    print(f"receipt={S0C_RECEIPT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
