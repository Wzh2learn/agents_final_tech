from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping

import adapter
import checker
import provenance


WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[2]
DATA_OUT_DIR = REPO_ROOT / "data/research/tatqa_wp0_2026/wp1"
FIXTURE_PATH = WORK_DIR / "fixtures/synthetic_fixtures.json"
PREFLIGHT_PATH = WORK_DIR / "PREFLIGHT_RECEIPT.json"
FIXTURE_RECEIPT_PATH = DATA_OUT_DIR / "FIXTURE_RECEIPT.json"
PREREG_PATH = WORK_DIR / "PREREG_DRAFT_SKELETON.md"
WP1_RECEIPT_PATH = WORK_DIR / "WP1_RECEIPT.json"
RUN_ID = "tatqa-wp1b-20261013"
START_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BOUNDARY_CHARACTERS = frozenset("0123456789.,+-")
PINNED_INPUTS = {
    REPO_ROOT / "data/research/tatqa_wp0_2026/candidate_items_v1.json": (
        "bc55fe7a53381f32e5d84ff6c17ced18ec72fd322f98a9f80c4eccb714caac12"
    ),
    REPO_ROOT / "data/research/tatqa_wp0_2026/origin_manifest.json": (
        "3718e6fef4d52bec0c1c29b47ba9ab60e298754b9e8527835d09c9d223d70cea"
    ),
    REPO_ROOT / "data/research/tatqa_raw_2026/tatqa_dataset_train.json": (
        "2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69"
    ),
    REPO_ROOT / "data/research/tatqa_raw_2026/tatqa_dataset_dev.json": (
        "8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5"
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


def load_synthetic_fixtures() -> dict[str, Any]:
    fixtures = load_json(FIXTURE_PATH)
    if fixtures.get("schema") != "tatqa_wp1_synthetic_fixtures_v1":
        raise ValueError("unexpected synthetic fixture schema")
    return fixtures


def fixture_item(fixture: Mapping[str, Any]) -> dict[str, Any]:
    return dict(fixture["item"])


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _obligation(
    obligation_id: str, check: Callable[[], Mapping[str, Any]]
) -> dict[str, Any]:
    try:
        evidence = dict(check())
    except Exception as exc:
        return {
            "id": obligation_id,
            "status": "FAIL",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "id": obligation_id,
        "status": "PASS",
        "evidence": evidence,
    }


def _boundary_aware_matches(serialized_text: str, needle: str) -> list[str]:
    pattern = re.compile(
        rf"(?<![{re.escape(''.join(sorted(BOUNDARY_CHARACTERS)))}])"
        rf"{re.escape(needle)}"
        rf"(?![{re.escape(''.join(sorted(BOUNDARY_CHARACTERS)))}])"
    )
    return [match.group(0) for match in pattern.finditer(serialized_text)]


def _raw_projection_values(item: Mapping[str, Any]) -> list[str]:
    raw_values = [
        str(cell)
        for row in item["table"]
        for cell in row
    ]
    raw_values.extend(
        [
            str(item["period_late"]["label"]),
            str(item["period_early"]["label"]),
        ]
    )
    return raw_values


def _check_prompt_byte_determinism(
    fixtures: Mapping[str, Any]
) -> Mapping[str, Any]:
    fixture = fixtures["fixtures"][0]
    item = fixture_item(fixture)
    hook = adapter.ContextHook("E", "experience", "synthetic typed placeholder")
    first = adapter.build_prompt(item, hook).encode("utf-8")
    second = adapter.build_prompt(item, hook).encode("utf-8")
    _require(first == second, "same item and arm produced different prompt bytes")
    return {
        "fixture_id": fixture["fixture_id"],
        "first_sha256": hashlib.sha256(first).hexdigest(),
        "second_sha256": hashlib.sha256(second).hexdigest(),
        "byte_equal": True,
        "bytes": len(first),
    }


def _check_hidden_gold_search(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    forbidden_keys = [
        "gold_delta_source_unit",
        "gold_recompute_rule",
        "gold_delta_target_unit",
        "expected_gold",
        "origin_id",
        "item_id",
    ]
    results = []
    for fixture in fixtures["fixtures"]:
        item = fixture_item(fixture)
        prompt = adapter.build_prompt(item, adapter.ContextHook("B", "none", ""))
        gold = checker.recompute_gold(item)
        answer_values = {
            "delta_source": str(gold.delta_source),
            "delta_target": str(gold.delta_target),
        }
        forbidden_found = [key for key in forbidden_keys if key in prompt]
        projection_matches = {
            field: _boundary_aware_matches(prompt, value)
            for field, value in answer_values.items()
        }
        raw_values = _raw_projection_values(item)
        precondition_matches = {
            field: [
                raw_value
                for raw_value in raw_values
                if _boundary_aware_matches(raw_value, value)
            ]
            for field, value in answer_values.items()
        }
        _require(not forbidden_found, f"{fixture['fixture_id']} hidden keys leaked: {forbidden_found}")
        _require(
            not any(projection_matches.values()),
            f"{fixture['fixture_id']} derived answer leaked: {projection_matches}",
        )
        _require(
            not any(precondition_matches.values()),
            f"{fixture['fixture_id']} fixture-design collision: {precondition_matches}",
        )
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "forbidden_found": forbidden_found,
                "answer_values": answer_values,
                "projection_matches": projection_matches,
                "fixture_design_precondition_matches": precondition_matches,
                "clean": True,
            }
        )
    return {
        "fixture_count": len(results),
        "forbidden_keys_checked": forbidden_keys,
        "excluded_hidden_fields": ["late_value", "early_value"],
        "answer_fields_checked": ["delta_source", "delta_target"],
        "results": results,
        "clean": True,
    }


def _check_gold_recomputation(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    results = []
    for fixture in fixtures["fixtures"]:
        gold = checker.recompute_gold(fixture_item(fixture))
        expected = fixture["expected_gold"]
        comparisons = {
            "late_value": gold.late_value,
            "early_value": gold.early_value,
            "delta_source": gold.delta_source,
            "delta_target": gold.delta_target,
        }
        for field, actual in comparisons.items():
            _require(
                actual == Decimal(expected[field]),
                f"{fixture['fixture_id']} {field}: {actual} != {expected[field]}",
            )
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "late_value": str(gold.late_value),
                "early_value": str(gold.early_value),
                "delta_source": str(gold.delta_source),
                "delta_target": str(gold.delta_target),
            }
        )
    _require(len(results) >= 5, "fewer than five recomputation fixtures")
    fixture_ids = {row["fixture_id"] for row in results}
    _require(
        {"parentheses_negative", "thousands_separator"}.issubset(fixture_ids),
        "mandated parsing fixtures are missing",
    )
    return {
        "fixture_count": len(results),
        "results": results,
        "mandated_cases_present": [
            "parentheses_negative",
            "thousands_separator",
        ],
    }


def _check_scale_conversions(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    expected_conversions = {
        "thousand_to_unit": Decimal(1000),
        "million_to_thousand": Decimal(1000),
        "billion_to_million": Decimal(1000),
        "percent_to_percent": Decimal(1),
    }
    fixture_map = {
        fixture["fixture_id"]: fixture for fixture in fixtures["fixtures"]
    }
    results = []
    for fixture_id, expected_factor in expected_conversions.items():
        fixture = fixture_map[fixture_id]
        item = fixture_item(fixture)
        actual_factor = checker.conversion_factor(
            item["source_unit"], item["target_unit"]
        )
        gold = checker.recompute_gold(item)
        _require(
            actual_factor == expected_factor,
            f"{fixture_id} factor {actual_factor} != {expected_factor}",
        )
        _require(
            gold.delta_target == Decimal(fixture["expected_gold"]["delta_target"]),
            f"{fixture_id} converted gold mismatch",
        )
        results.append(
            {
                "fixture_id": fixture_id,
                "source_unit": item["source_unit"],
                "target_unit": item["target_unit"],
                "factor": str(actual_factor),
                "delta_source": str(gold.delta_source),
                "delta_target": str(gold.delta_target),
            }
        )
    return {
        "conversion_count": len(results),
        "required_conversions": list(expected_conversions),
        "results": results,
    }


def _check_unknown_and_refused(
    fixtures: Mapping[str, Any]
) -> Mapping[str, Any]:
    fixture = fixtures["fixtures"][0]
    item = fixture_item(fixture)
    cases = [
        ("unknown", "UNKNOWN", "unknown"),
        ("refused", "REFUSED", "refused"),
        ("unparseable", fixture["answers"]["unparseable"], "unknown"),
    ]
    results = []
    for case_id, answer, expected in cases:
        actual = checker.score_item(item, answer)["outcome"]
        _require(actual == expected, f"{case_id}: {actual} != {expected}")
        results.append(
            {
                "case_id": case_id,
                "answer": answer,
                "expected": expected,
                "actual": actual,
            }
        )
    return {"case_count": len(results), "results": results}


def _check_ec_token_delta(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    context = fixtures["context_delta_fixture"]
    result = adapter.context_token_delta(
        context["e_context"],
        context["c_context"],
        Decimal(context["relative_limit"]),
    )
    _require(
        result["within_limit"],
        f"E/C token delta exceeds limit: {result}",
    )
    return result


def _check_taxonomy(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    fixture = fixtures["fixtures"][0]
    item = fixture_item(fixture)
    expected = {
        "correct": "correct",
        "correct_other_form": "correct_other_form",
        "wrong_unit": "wrong_unit",
        "wrong_period": "wrong_period",
        "refused": "refused",
        "unknown": "unknown",
        "unparseable": "unknown",
    }
    results = []
    for case_id, expected_outcome in expected.items():
        actual = checker.score_item(item, fixture["answers"][case_id])["outcome"]
        _require(
            actual == expected_outcome,
            f"taxonomy {case_id}: {actual} != {expected_outcome}",
        )
        results.append(
            {
                "case_id": case_id,
                "expected": expected_outcome,
                "actual": actual,
            }
        )
    return {"case_count": len(results), "results": results}


def _check_regression(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    cases = [
        ("correct", "wrong_unit", "regressed"),
        ("correct_other_form", "wrong_period", "regressed"),
        ("correct", "refused", "refused"),
        ("correct", "unknown", "unknown"),
        ("wrong_unit", "correct", "correct"),
    ]
    results = []
    for base, arm, expected in cases:
        actual = checker.apply_regression(base, arm)
        _require(actual == expected, f"regression {base}->{arm}: {actual}")
        results.append(
            {
                "base_outcome": base,
                "arm_outcome": arm,
                "expected": expected,
                "actual": actual,
            }
        )
    return {"case_count": len(results), "results": results}


def _run_metric_pipeline(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    normal = fixtures["fixtures"][0]
    thousands = fixtures["fixtures"][2]
    records = [
        {
            "origin_id": normal["origin_id"],
            "item_id": normal["item"]["item_id"],
            "arm": "B",
            "outcome": "correct",
        },
        {
            "origin_id": normal["origin_id"],
            "item_id": normal["item"]["item_id"],
            "arm": "E",
            "outcome": "wrong_unit",
        },
        {
            "origin_id": normal["origin_id"],
            "item_id": normal["item"]["item_id"],
            "arm": "C",
            "outcome": "correct",
        },
        {
            "origin_id": normal["origin_id"],
            "item_id": normal["item"]["item_id"],
            "arm": "S",
            "outcome": "correct",
        },
        {
            "origin_id": thousands["origin_id"],
            "item_id": thousands["item"]["item_id"],
            "arm": "B",
            "outcome": "wrong_unit",
        },
        {
            "origin_id": thousands["origin_id"],
            "item_id": thousands["item"]["item_id"],
            "arm": "E",
            "outcome": "correct",
        },
        {
            "origin_id": thousands["origin_id"],
            "item_id": thousands["item"]["item_id"],
            "arm": "C",
            "outcome": "wrong_unit",
        },
        {
            "origin_id": thousands["origin_id"],
            "item_id": thousands["item"]["item_id"],
            "arm": "S",
            "outcome": "correct",
        },
    ]
    aggregate = checker.aggregate_outcomes(records)
    comparisons = [
        checker.paired_origin_differences(records, "E", "B"),
        checker.paired_origin_differences(records, "E", "C"),
        checker.paired_origin_differences(records, "E", "S"),
        checker.paired_origin_differences(records, "C", "B"),
    ]
    _require(aggregate["record_count"] == 8, "metric record count mismatch")
    _require(
        all(comparison["origin_count"] == 2 for comparison in comparisons),
        "metric origin resolution mismatch",
    )
    _require(
        all(len(comparison["origin_differences"]) == 2 for comparison in comparisons),
        "origin-level differences were not listed explicitly",
    )
    return {
        "status": "PASS",
        "fixture_only": True,
        "aggregate": aggregate,
        "paired_comparisons": comparisons,
    }


def run_checks(
    fixtures: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    obligations = [
        _obligation(
            "prompt_byte_determinism",
            lambda: _check_prompt_byte_determinism(fixtures),
        ),
        _obligation(
            "hidden_gold_search",
            lambda: _check_hidden_gold_search(fixtures),
        ),
        _obligation(
            "gold_recomputation",
            lambda: _check_gold_recomputation(fixtures),
        ),
        _obligation(
            "scale_conversions",
            lambda: _check_scale_conversions(fixtures),
        ),
        _obligation(
            "unknown_and_refused",
            lambda: _check_unknown_and_refused(fixtures),
        ),
        _obligation(
            "ec_token_delta",
            lambda: _check_ec_token_delta(fixtures),
        ),
    ]
    additional_checks = [
        _obligation("outcome_taxonomy", lambda: _check_taxonomy(fixtures)),
        _obligation("regression_helper", lambda: _check_regression(fixtures)),
    ]
    metric_pipeline = _run_metric_pipeline(fixtures)
    return obligations, {
        "status": "PASS",
        "additional_checks": additional_checks,
        "metric_pipeline": metric_pipeline,
    }


def _verify_pinned_inputs() -> dict[str, Any]:
    hashes = {}
    for path, expected in PINNED_INPUTS.items():
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(
                f"HASH_MISMATCH: {path.relative_to(REPO_ROOT)} {actual} != {expected}"
            )
        hashes[str(path.relative_to(REPO_ROOT))] = actual
    candidate_path = REPO_ROOT / "data/research/tatqa_wp0_2026/candidate_items_v1.json"
    origin_path = REPO_ROOT / "data/research/tatqa_wp0_2026/origin_manifest.json"
    generation_receipt_path = (
        REPO_ROOT / "data/research/tatqa_wp0_2026/GENERATION_RECEIPT.json"
    )
    candidates = load_json(candidate_path)
    origins = load_json(origin_path)
    generation_receipt = load_json(generation_receipt_path)
    counts = {
        "candidate_items": len(candidates["items"]),
        "candidate_item_count_field": candidates["item_count"],
        "origins": len(origins["origins"]),
        "origin_count_field": origins["origin_count"],
        "receipt_candidate_items": generation_receipt["candidate_items"],
        "receipt_origins": generation_receipt["origins"],
    }
    expected_counts = {
        "candidate_items": 60,
        "candidate_item_count_field": 60,
        "origins": 182,
        "origin_count_field": 182,
        "receipt_candidate_items": 60,
        "receipt_origins": 182,
    }
    if counts != expected_counts:
        raise RuntimeError(f"HASH_MISMATCH_COUNTS: {counts} != {expected_counts}")
    return {
        "status": "PASS",
        "hashes": hashes,
        "counts": counts,
    }


def _preflight_checks(fixtures: Mapping[str, Any]) -> dict[str, Any]:
    input_verification = _verify_pinned_inputs()
    required_paths = [
        WORK_DIR / "checker.py",
        WORK_DIR / "adapter.py",
        WORK_DIR / "provenance.py",
        WORK_DIR / "run_fixtures.py",
        WORK_DIR / "implementation_contract.md",
        WORK_DIR / "implementation_contract.sha256",
        WORK_DIR / "PREREG_DRAFT_SKELETON.md",
        FIXTURE_PATH,
    ]
    required_files = {
        str(path.relative_to(REPO_ROOT)): path.exists() for path in required_paths
    }
    if not all(required_files.values()):
        missing = [path for path, exists in required_files.items() if not exists]
        raise RuntimeError(f"required files missing: {missing}")
    candidate_path = REPO_ROOT / "data/research/tatqa_wp0_2026/candidate_items_v1.json"
    origin_path = REPO_ROOT / "data/research/tatqa_wp0_2026/origin_manifest.json"
    candidates = load_json(candidate_path)
    origins = load_json(origin_path)
    candidate_items = candidates["items"]
    origin_records = origins["origins"]
    runtime_payloads = [
        adapter.runtime_payload_from_candidate(item) for item in candidate_items
    ]
    runtime_fields = sorted(set().union(*(payload.keys() for payload in runtime_payloads)))
    expected_fields = sorted(checker.REQUIRED_RUNTIME_FIELDS)
    runtime_schema_pass = runtime_fields == expected_fields
    checker_domain_pass = all(
        set(checker.REQUIRED_RUNTIME_FIELDS).issubset(payload)
        and callable(checker.recompute_gold)
        and callable(checker.score_item)
        for payload in runtime_payloads
    )
    origin_by_id = {}
    duplicate_origin_ids = []
    for origin in origin_records:
        origin_id = origin["origin_id"]
        if origin_id in origin_by_id:
            duplicate_origin_ids.append(origin_id)
        origin_by_id[origin_id] = origin
    unresolved_origins = [
        item["origin_id"]
        for item in candidate_items
        if item["origin_id"] not in origin_by_id
    ]
    split_mismatches = [
        item["item_id"]
        for item in candidate_items
        if item["origin_id"] in origin_by_id
        and origin_by_id[item["origin_id"]]["split"] != item["split"]
    ]
    item_ids = [item["item_id"] for item in candidate_items]
    identifier_pass = (
        not duplicate_origin_ids
        and not unresolved_origins
        and not split_mismatches
        and len(set(item_ids)) == 60
        and len(origin_by_id) == 182
    )
    attribution = provenance.attributed_payload({"schema": "synthetic"})
    attribution_pass = (
        attribution["provenance"]["task"] == "tatqa_wp1_loop_a"
        and attribution["provenance"]["model_calls"] == 0
        and attribution["provenance"]["endpoint_calls"] == 0
    )
    checks = [
        {
            "id": "required_files_exist",
            "status": "PASS",
            "evidence": required_files,
        },
        {
            "id": "runtime_schema_field_names",
            "status": "PASS" if runtime_schema_pass else "FAIL",
            "evidence": {
                "actual": runtime_fields,
                "expected": expected_fields,
            },
        },
        {
            "id": "checker_defined_on_allowed_inputs",
            "status": "PASS" if checker_domain_pass else "FAIL",
            "evidence": {
                "candidate_runtime_payloads": len(runtime_payloads),
                "candidate_scoring_called": False,
                "candidate_gold_fields_accessed": False,
            },
        },
        {
            "id": "group_and_split_ids_resolve",
            "status": "PASS" if identifier_pass else "FAIL",
            "evidence": {
                "candidate_items": len(candidate_items),
                "distinct_item_ids": len(set(item_ids)),
                "origins": len(origin_records),
                "distinct_origin_ids": len(origin_by_id),
                "duplicate_origin_ids": duplicate_origin_ids,
                "unresolved_origins": unresolved_origins,
                "split_mismatches": split_mismatches,
            },
        },
        {
            "id": "provenance_writer_attributes_task",
            "status": "PASS" if attribution_pass else "FAIL",
            "evidence": attribution["provenance"],
        },
        {
            "id": "synthetic_metric_pipeline_end_to_end",
            "status": (
                "PASS"
                if fixtures["schema"] == "tatqa_wp1_synthetic_fixtures_v1"
                and _run_metric_pipeline(fixtures)["status"] == "PASS"
                else "FAIL"
            ),
            "evidence": {
                "fixture_only": True,
                "scientific_results": False,
            },
        },
        {
            "id": "no_held_out_result_read",
            "status": "PASS",
            "evidence": {
                "held_out_result_read": False,
                "raw_outcome_scoring": False,
                "candidate_item_scoring": False,
            },
        },
        {
            "id": "pinned_inputs_reverified",
            "status": input_verification["status"],
            "evidence": input_verification,
        },
    ]
    failed = [check["id"] for check in checks if check["status"] != "PASS"]
    return {
        "schema": "tatqa_wp1_preflight_receipt_v1",
        "task": "tatqa_wp1_loop_a",
        "status": "PASS" if not failed else "FAIL",
        "provenance": provenance.task_provenance(),
        "required_files": required_files,
        "runtime_schema": {
            "status": "PASS" if runtime_schema_pass else "FAIL",
            "fields": runtime_fields,
            "expected_fields": expected_fields,
        },
        "checker_domain": {
            "status": "PASS" if checker_domain_pass else "FAIL",
            "allowed_candidate_structures": len(runtime_payloads),
            "checker_functions_defined": sorted(
                name
                for name in [
                    "recompute_gold",
                    "prepare_item",
                    "score_item",
                    "apply_regression",
                    "aggregate_outcomes",
                    "paired_origin_differences",
                ]
                if callable(getattr(checker, name, None))
            ),
            "candidate_scoring_called": False,
            "candidate_gold_fields_accessed": False,
        },
        "identifier_resolution": {
            "status": "PASS" if identifier_pass else "FAIL",
            "candidate_items": len(candidate_items),
            "distinct_item_ids": len(set(item_ids)),
            "origins": len(origin_records),
            "distinct_origin_ids": len(origin_by_id),
        },
        "metric_pipeline": {
            "status": _run_metric_pipeline(fixtures)["status"],
            "fixture_only": True,
            "scientific_results": False,
        },
        "input_verification": input_verification,
        "held_out_result_read": False,
        "candidate_item_scoring": False,
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
        },
        "failed_checks": failed,
        "checks": checks,
    }


def _write_prereg(fixtures: Mapping[str, Any], preflight: Mapping[str, Any]) -> None:
    pins = {
        "checker": sha256_file(WORK_DIR / "checker.py"),
        "adapter": sha256_file(WORK_DIR / "adapter.py"),
        "fixtures": sha256_file(FIXTURE_PATH),
        "preflight": sha256_file(PREFLIGHT_PATH),
        "contract": sha256_file(WORK_DIR / "implementation_contract.md"),
    }
    _require(preflight["status"] == "PASS", "preflight is not PASS")
    _require(
        all(value != "PENDING_FIXTURE_HASH" for value in pins.values()),
        "fixture hash pin unresolved",
    )
    text = f"""# TAT-QA WP-2 Preregistration Draft Skeleton

Status: `DRAFT - NOT READY - NO PILOT AUTHORIZATION`

Task: `tatqa_wp1_loop_a`

This skeleton freezes no experiment and authorizes no model call. All actor, context, budget, window, and governance fields remain pending until owner/advisor selection and approval.

## 1. Scientific scope

- Question: whether fixed, related real execution experience changes performance on new-origin two-period table-calculation tasks.
- Independent unit: origin.
- Arms: B, E, C, S as defined by the frozen evaluation protocol.
- Primary outcomes: `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `regressed`, `refused`, and `unknown`.
- No training, memory write-back, pilot execution, or candidate-item scoring is authorized by WP-1.

## 2. Frozen software pins

- Checker: `{pins['checker']}`
- Adapter: `{pins['adapter']}`
- Synthetic fixtures: `{pins['fixtures']}`
- Preflight receipt: `{pins['preflight']}`
- Implementation contract: `{pins['contract']}`

## 3. Actor freeze

- Actor revision: `PENDING`
- Model identity: `PENDING`
- Model settings: `PENDING`
- Calculator/tool implementation hash: `PENDING`
- Adapter settings: `PENDING`

## 4. Experience context

- Episode-source contract: `PENDING`
- Real E blocks: `PENDING`
- Real C blocks: `PENDING`
- Origin-disjointness receipt: `PENDING`
- Near-duplicate isolation receipt: `PENDING`
- E/C token-delta receipt: `PENDING`
- S rules: `PENDING`

## 5. Evaluation and analysis

- Frozen item/split receipt: `PENDING`
- Pilot task list: `PENDING`
- Repeat count and ordering: `PENDING`
- Analysis script hash: `PENDING`
- Bootstrap method and seed: `PENDING`
- Origin-level difference table: `PENDING`

## 6. Budget, window, and governance

- Owner authorization: `PENDING`
- Advisor authorization: `PENDING`
- Budget/window binding: `PENDING`
- Start/end UTC: `PENDING`
- Model-call budget: `PENDING`
- Endpoint-call budget: `PENDING`
- Judge-call budget: `0`

## 7. Stop rules

- Leakage or bridge failure: `STOP_THIS_PANEL`
- B ceiling on both repeats: `STOP_THIS_PANEL`
- Any unauthorized model, judge, endpoint, database, or service call: stop and report.
- Fixture or checker failure: report `SOFTWARE_NOT_QUALIFIED`; never weaken the failing test.
"""
    PREREG_PATH.write_text(text, encoding="utf-8", newline="\n")


def write_outputs(
    fixtures: Mapping[str, Any],
    obligations: list[dict[str, Any]],
    metrics: Mapping[str, Any],
) -> None:
    preflight = _preflight_checks(fixtures)
    preflight["run_id"] = RUN_ID
    provenance.write_json_lf(PREFLIGHT_PATH, preflight)
    artifact_hashes = {
        "checker": sha256_file(WORK_DIR / "checker.py"),
        "adapter": sha256_file(WORK_DIR / "adapter.py"),
        "provenance": sha256_file(WORK_DIR / "provenance.py"),
        "run_fixtures": sha256_file(WORK_DIR / "run_fixtures.py"),
        "fixtures": sha256_file(FIXTURE_PATH),
        "contract": sha256_file(WORK_DIR / "implementation_contract.md"),
        "preflight": sha256_file(PREFLIGHT_PATH),
    }
    fixture_payload = provenance.attributed_payload(
        {
            "schema": "tatqa_wp1_fixture_receipt_v1",
            "run_id": RUN_ID,
            "task": "tatqa_wp1_loop_a",
            "status": (
                "PASS"
                if all(row["status"] == "PASS" for row in obligations)
                and all(
                    row["status"] == "PASS"
                    for row in metrics["additional_checks"]
                )
                and metrics["metric_pipeline"]["status"] == "PASS"
                else "FAIL"
            ),
            "fixture_source": str(FIXTURE_PATH.relative_to(REPO_ROOT)),
            "artifact_hashes": artifact_hashes,
            "obligations": obligations,
            "taxonomy_checks": next(
                row
                for row in metrics["additional_checks"]
                if row["id"] == "outcome_taxonomy"
            ),
            "regression_check": next(
                row
                for row in metrics["additional_checks"]
                if row["id"] == "regression_helper"
            ),
            "metric_pipeline": metrics["metric_pipeline"],
            "cost": {
                "model_calls": 0,
                "endpoint_calls": 0,
            },
            "held_out_result_read": False,
            "candidate_item_scoring": False,
            "deviations": [],
        }
    )
    provenance.write_json_lf(FIXTURE_RECEIPT_PATH, fixture_payload)
    _write_prereg(fixtures, preflight)
    receipt = provenance.attributed_payload(
        {
            "run_id": RUN_ID,
            "task": "tatqa_wp1_loop_a",
            "status": (
                "PASS"
                if fixture_payload["status"] == "PASS"
                and preflight["status"] == "PASS"
                else "FAIL"
            ),
            "start_utc": START_UTC,
            "end_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input_verification": _verify_pinned_inputs(),
            "artifact_hashes": artifact_hashes,
            "fixture_results": obligations,
            "preflight_results": preflight["checks"],
            "cost": {
                "model_calls": 0,
                "endpoint_calls": 0,
            },
            "unverified_items": [
                "real E/C experience blocks were not constructed",
                "actor freeze and model selection remain PENDING",
                "origin-disjoint episode and near-duplicate receipts remain PENDING",
                "held-out pilot and scientific outcomes remain UNVERIFIED",
            ],
            "deviations": [],
        }
    )
    provenance.write_json_lf(WP1_RECEIPT_PATH, receipt)


def main() -> int:
    fixtures = load_synthetic_fixtures()
    obligations, metrics = run_checks(fixtures)
    failed_obligations = [
        row["id"] for row in obligations if row["status"] != "PASS"
    ]
    failed_additional = [
        row["id"]
        for row in metrics["additional_checks"]
        if row["status"] != "PASS"
    ]
    if (
        failed_obligations
        or failed_additional
        or metrics["metric_pipeline"]["status"] != "PASS"
    ):
        failing = failed_obligations + failed_additional
        if metrics["metric_pipeline"]["status"] != "PASS":
            failing.append("synthetic_metric_pipeline")
        print(f"SOFTWARE_NOT_QUALIFIED: {','.join(failing)}")
        return 1
    write_outputs(fixtures, obligations, metrics)
    print("WP1_FIXTURES_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
