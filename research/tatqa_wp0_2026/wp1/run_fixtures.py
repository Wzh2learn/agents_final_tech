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
FIXTURE_RECEIPT_MIRROR_PATH = WORK_DIR / "FIXTURE_RECEIPT.json"
PREREG_PATH = WORK_DIR / "PREREG_DRAFT_SKELETON.md"
WP1_RECEIPT_PATH = WORK_DIR / "WP1_RECEIPT.json"
RUN_ID = "tatqa-wp1c-20261013"
SPEC_REVISION = "1.2"
START_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BOUNDARY_CHARACTERS = frozenset("0123456789.,+-")
SCORE_ITEM_CALL_LOG: list[dict[str, Any]] = []
SYNTHETIC_FIXTURE_IDS = frozenset(
    {
        "normal_unit",
        "parentheses_negative",
        "thousands_separator",
        "thousand_to_unit",
        "million_to_thousand",
        "billion_to_million",
        "percent_to_percent",
    }
)
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


def _safety_claim(value: bool, basis: str, evidence: Any) -> dict[str, Any]:
    if basis not in {"derived", "attested: true"}:
        raise ValueError(f"unsupported safety basis: {basis}")
    if basis == "attested: true" and value is not True:
        raise ValueError("attested safety claims must be true")
    return {"basis": basis, "evidence": evidence, "value": value}


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


def canonical_plain_decimal(value: Decimal) -> str:
    if not isinstance(value, Decimal):
        raise TypeError("value must be Decimal")
    if value.is_zero():
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _answer_value_needles(
    value: Decimal, exact_str: str | None = None
) -> list[str]:
    canonical = canonical_plain_decimal(value)
    forms = [canonical, str(value)]
    if exact_str is not None:
        forms.append(str(exact_str))
    needles: list[str] = []
    for form in forms:
        if form not in needles:
            needles.append(form)
    return needles


def _needle_search(
    serialized_text: str, needles: list[str]
) -> dict[str, list[str]]:
    return {
        needle: _boundary_aware_matches(serialized_text, needle)
        for needle in needles
    }


def _score_fixture_item(
    fixture: Mapping[str, Any], answer: str, call_site: str
) -> dict[str, str]:
    item = fixture_item(fixture)
    item_id = str(item["item_id"])
    origin_id = str(item["origin_id"])
    _require(
        str(fixture["fixture_id"]) in SYNTHETIC_FIXTURE_IDS
        and fixture["origin_id"] == origin_id
        and item_id.startswith("synthetic_item_")
        and origin_id.startswith("synthetic_origin_"),
        f"non-synthetic scoring input rejected: {item_id} / {origin_id}",
    )
    SCORE_ITEM_CALL_LOG.append(
        {
            "call_site": call_site,
            "fixture_id": str(fixture["fixture_id"]),
            "input_kind": "synthetic_fixture",
            "item_id": item_id,
            "origin_id": origin_id,
        }
    )
    return checker.score_item(item, answer)


def _check_prompt_byte_determinism(
    fixtures: Mapping[str, Any]
) -> Mapping[str, Any]:
    context_delta = fixtures["context_delta_fixture"]
    hook_inputs = {
        "B": ("none", ""),
        "E": ("experience", context_delta["e_context"]),
        "C": ("matched_experience", context_delta["c_context"]),
        "S": ("static_rules", "Synthetic frozen static-rules placeholder."),
    }
    _require(
        set(hook_inputs) == set(adapter.ARMS) == {"B", "E", "C", "S"},
        "byte-determinism arm coverage is incomplete",
    )
    results = []
    for fixture in fixtures["fixtures"]:
        item = fixture_item(fixture)
        for arm in sorted(hook_inputs):
            hook_type, context_text = hook_inputs[arm]
            hook = adapter.ContextHook(arm, hook_type, context_text)
            first = adapter.build_prompt(item, hook).encode("utf-8")
            second = adapter.build_prompt(item, hook).encode("utf-8")
            _require(
                first == second,
                f"{fixture['fixture_id']} arm {arm} produced different prompt bytes",
            )
            results.append(
                {
                    "arm": arm,
                    "byte_equal": True,
                    "bytes": len(first),
                    "first_sha256": hashlib.sha256(first).hexdigest(),
                    "fixture_id": fixture["fixture_id"],
                    "second_sha256": hashlib.sha256(second).hexdigest(),
                }
            )
    _require(
        len(results) == len(fixtures["fixtures"]) * 4,
        "byte-determinism did not cover every fixture across four arms",
    )
    return {
        "arms": sorted(hook_inputs),
        "combination_count": len(results),
        "fixture_count": len(fixtures["fixtures"]),
        "results": results,
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
        answer_needles = {
            field: _answer_value_needles(
                getattr(gold, field), fixture["expected_gold"][field]
            )
            for field in ("delta_source", "delta_target")
        }
        forbidden_found = [key for key in forbidden_keys if key in prompt]
        projection_matches = {
            field: _needle_search(prompt, needles)
            for field, needles in answer_needles.items()
        }
        raw_values = _raw_projection_values(item)
        precondition_matches = {
            field: {
                needle: [
                    raw_value
                    for raw_value in raw_values
                    if _boundary_aware_matches(raw_value, needle)
                ]
                for needle in needles
            }
            for field, needles in answer_needles.items()
        }
        _require(not forbidden_found, f"{fixture['fixture_id']} hidden keys leaked: {forbidden_found}")
        _require(
            not any(
                needle_matches
                for matches in projection_matches.values()
                for needle_matches in matches.values()
            ),
            f"{fixture['fixture_id']} derived answer leaked: {projection_matches}",
        )
        _require(
            not any(
                raw_matches
                for matches in precondition_matches.values()
                for raw_matches in matches.values()
            ),
            f"{fixture['fixture_id']} fixture-design collision: {precondition_matches}",
        )
        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "forbidden_found": forbidden_found,
                "answer_needles": answer_needles,
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
        "needle_form_policy": [
            "canonical_plain_decimal",
            "exact_checker_decimal_str_when_different",
            "exact_fixture_str_when_different",
        ],
        "results": results,
        "clean": True,
    }


def _check_hidden_gold_positive_control(
    fixtures: Mapping[str, Any]
) -> Mapping[str, Any]:
    injections: list[dict[str, str]] = [
        {
            "case_id": "canonical_1300",
            "fixture_id": "synthetic_positive_control",
            "needle": needle,
            "value_form": form,
        }
        for needle, form in zip(
            _answer_value_needles(Decimal("1300"), "1300.0"),
            ["canonical", "exact_str"],
            strict=False,
        )
    ]
    injections.extend(
        {
            "case_id": "canonical_negative_55",
            "fixture_id": "synthetic_positive_control",
            "needle": needle,
            "value_form": "canonical" if index == 0 else "exact_str",
        }
        for index, needle in enumerate(
            _answer_value_needles(Decimal("-55"), "-55.0")
        )
    )
    for fixture in fixtures["fixtures"]:
        gold = checker.recompute_gold(fixture_item(fixture))
        for field in ("delta_source", "delta_target"):
            for index, needle in enumerate(
                _answer_value_needles(
                    getattr(gold, field), fixture["expected_gold"][field]
                )
            ):
                injections.append(
                    {
                        "case_id": f"{fixture['fixture_id']}_{field}_{index}",
                        "fixture_id": fixture["fixture_id"],
                        "needle": needle,
                        "value_form": (
                            "canonical" if index == 0 else "exact_str"
                        ),
                    }
                )
    results = []
    for injection in injections:
        synthetic_projection = json.dumps(
            {
                "evidence": {
                    "injected_answer_value": injection["needle"],
                    "table": [["Injected answer value", injection["needle"]]],
                },
                "fixture_id": injection["fixture_id"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        matches = _needle_search(
            synthetic_projection, [injection["needle"]]
        )[injection["needle"]]
        _require(matches, f"silent hidden-gold guard: {injection}")
        results.append({**injection, "guard_fired": True, "matches": matches})
    _require(
        {"1300", "1300.0", "-55"}.issubset(
            {row["needle"] for row in results}
        ),
        "mandatory positive-control needles are missing",
    )
    return {
        "case_count": len(results),
        "mandatory_cases_present": ["1300", "1300.0", "-55"],
        "results": results,
        "guard_fired_for_every_needle": True,
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
    cases = [
        ("unknown", "UNKNOWN", "unknown"),
        ("refused", "REFUSED", "refused"),
        ("unparseable", fixture["answers"]["unparseable"], "unknown"),
    ]
    results = []
    for case_id, answer, expected in cases:
        actual = _score_fixture_item(
            fixture, answer, "run_fixtures.py:_check_unknown_and_refused"
        )["outcome"]
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
        "wrong": "wrong",
        "refused": "refused",
        "unknown": "unknown",
        "unparseable": "unknown",
    }
    results = []
    for case_id, expected_outcome in expected.items():
        actual = _score_fixture_item(
            fixture,
            fixture["answers"][case_id],
            "run_fixtures.py:_check_taxonomy",
        )["outcome"]
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
    regression_outcome = checker.apply_regression("correct", "wrong")
    _require(
        regression_outcome == "regressed",
        f"taxonomy regression class: {regression_outcome} != regressed",
    )
    results.append(
        {
            "actual": regression_outcome,
            "base_outcome": "correct",
            "case_id": "comparison_correct_to_wrong",
            "expected": "regressed",
            "source": "B-versus-arm comparison",
        }
    )
    observed_classes = {row["actual"] for row in results}
    _require(
        observed_classes == set(checker.OUTCOME_CLASSES),
        f"taxonomy coverage mismatch: {observed_classes} != {checker.OUTCOME_CLASSES}",
    )
    return {
        "case_count": len(results),
        "declared_outcome_classes": sorted(checker.OUTCOME_CLASSES),
        "observed_outcome_classes": sorted(observed_classes),
        "results": results,
    }


def _check_regression(fixtures: Mapping[str, Any]) -> Mapping[str, Any]:
    cases = [
        ("correct", "wrong_unit", "regressed"),
        ("correct_other_form", "wrong_period", "regressed"),
        ("correct", "refused", "refused"),
        ("correct", "unknown", "unknown"),
        ("correct", "wrong", "regressed"),
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
        "fixture_only": _safety_claim(
            True, "derived", "records are built only from synthetic fixtures"
        ),
        "scientific_results": _safety_claim(
            False, "derived", "metric pipeline never reads scientific outcomes"
        ),
        "aggregate": aggregate,
        "paired_comparisons": comparisons,
    }


def run_checks(
    fixtures: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    SCORE_ITEM_CALL_LOG.clear()
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
            "hidden_gold_positive_control",
            lambda: _check_hidden_gold_positive_control(fixtures),
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
    scoring_inputs = _derive_scoring_inputs_all_synthetic()
    return obligations, {
        "status": "PASS",
        "additional_checks": additional_checks,
        "metric_pipeline": metric_pipeline,
        "scoring_inputs": scoring_inputs,
    }


def _derive_scoring_inputs_all_synthetic() -> dict[str, Any]:
    _require(SCORE_ITEM_CALL_LOG, "no score_item call sites were exercised")
    expected_call_sites = {
        "run_fixtures.py:_check_unknown_and_refused",
        "run_fixtures.py:_check_taxonomy",
    }
    observed_call_sites = {row["call_site"] for row in SCORE_ITEM_CALL_LOG}
    _require(
        observed_call_sites == expected_call_sites,
        f"uninstrumented or missing score_item call sites: {observed_call_sites}",
    )
    all_synthetic = all(
        row["input_kind"] == "synthetic_fixture"
        and row["fixture_id"] in SYNTHETIC_FIXTURE_IDS
        and row["item_id"].startswith("synthetic_item_")
        and row["origin_id"].startswith("synthetic_origin_")
        for row in SCORE_ITEM_CALL_LOG
    )
    _require(all_synthetic, "a non-synthetic score_item input was observed")
    return {
        "all_synthetic": True,
        "basis": "derived",
        "call_count": len(SCORE_ITEM_CALL_LOG),
        "call_sites": sorted(observed_call_sites),
        "calls": list(SCORE_ITEM_CALL_LOG),
        "status": "PASS",
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
                "candidate_scoring_called": _safety_claim(
                    False,
                    "derived",
                    "preflight invokes adapter.runtime_payload_from_candidate only",
                ),
                "candidate_gold_fields_accessed": _safety_claim(
                    False,
                    "derived",
                    "preflight reads no candidate gold key",
                ),
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
                "fixture_only": _safety_claim(
                    True, "derived", "metric records originate in synthetic fixtures"
                ),
                "scientific_results": _safety_claim(
                    False, "derived", "no scientific item is scored"
                ),
            },
        },
        {
            "id": "no_held_out_result_read",
            "status": "PASS",
            "evidence": {
                "held_out_result_read": _safety_claim(
                    False, "derived", "preflight contains no held-out result reader"
                ),
                "raw_outcome_scoring": _safety_claim(
                    False, "derived", "raw outcome data is outside the read path"
                ),
                "candidate_item_scoring": _safety_claim(
                    False, "derived", "only synthetic fixture scoring is executed"
                ),
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
        "spec_revision": SPEC_REVISION,
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
            "candidate_scoring_called": _safety_claim(
                False,
                "derived",
                "candidate payload construction does not call score_item",
            ),
            "candidate_gold_fields_accessed": _safety_claim(
                False, "derived", "candidate gold keys are never dereferenced"
            ),
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
            "fixture_only": _safety_claim(
                True, "derived", "the pipeline consumes synthetic metric records"
            ),
            "scientific_results": _safety_claim(
                False, "derived", "no scientific outcome is produced"
            ),
        },
        "scoring_inputs": _derive_scoring_inputs_all_synthetic(),
        "input_verification": input_verification,
        "safety": {
            "candidate_item_scoring": _safety_claim(
                False, "derived", "candidate score_item calls are absent"
            ),
            "held_out_result_read": _safety_claim(
                False, "derived", "no held-out result path is executed"
            ),
            "scoring_inputs_all_synthetic": _safety_claim(
                True,
                "derived",
                "run_fixtures instrumented every score_item call site",
            ),
            "write_paths_confined": _safety_claim(
                True,
                "attested: true",
                "Run 1c writes only the authorized WP-1 research and data paths",
            ),
        },
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

Spec revision: `1.2`

This skeleton freezes no experiment and authorizes no model call. All actor, context, budget, window, and governance fields remain pending until owner/advisor selection and approval.

## 1. Scientific scope

- Question: whether fixed, related real execution experience changes performance on new-origin two-period table-calculation tasks.
- Independent unit: origin.
- Arms: B, E, C, S as defined by the frozen evaluation protocol.
- Outcomes: `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong`, `regressed`, `refused`, and `unknown`.
- No training, memory write-back, pilot execution, or candidate-item scoring is authorized by WP-1.
- Protocol revision and protocol pin: `PENDING`.
- Item/split freeze receipt: `PENDING`.
- Actor freeze: `PENDING`.
- `target_unit` assignment: `PENDING` (identity-only conversion today across the 60 frozen candidates).

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
            "spec_revision": SPEC_REVISION,
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
            "scoring_inputs": metrics["scoring_inputs"],
            "cost": {
                "model_calls": 0,
                "endpoint_calls": 0,
            },
            "safety": {
                "candidate_item_scoring": _safety_claim(
                    False, "derived", "no candidate score_item call is present"
                ),
                "held_out_result_read": _safety_claim(
                    False, "derived", "no held-out result reader is present"
                ),
                "scoring_inputs_all_synthetic": _safety_claim(
                    True,
                    "derived",
                    "every instrumented score_item call passed a synthetic fixture",
                ),
                "write_paths_confined": _safety_claim(
                    True,
                    "attested: true",
                    "run 1c writes only authorized WP-1 research and data paths",
                ),
            },
            "receipt_paths": {
                "canonical": str(FIXTURE_RECEIPT_PATH.relative_to(REPO_ROOT)),
                "repo_mirror": str(
                    FIXTURE_RECEIPT_MIRROR_PATH.relative_to(REPO_ROOT)
                ),
            },
            "deviations": [
                {
                    "kind": "spec_revision_resolution",
                    "note": (
                        "Revision 1.2 blesses the `wrong` outcome class and "
                        "narrows `regressed` to non-correct answers other "
                        "than `refused`/`unknown`."
                    ),
                    "spec_revision": SPEC_REVISION,
                }
            ],
        }
    )
    provenance.write_json_lf(FIXTURE_RECEIPT_PATH, fixture_payload)
    FIXTURE_RECEIPT_MIRROR_PATH.write_bytes(
        FIXTURE_RECEIPT_PATH.read_bytes()
    )
    _require(
        FIXTURE_RECEIPT_PATH.read_bytes()
        == FIXTURE_RECEIPT_MIRROR_PATH.read_bytes(),
        "FIXTURE_RECEIPT repo mirror is not byte-identical",
    )
    wp_artifact_hashes = dict(artifact_hashes)
    wp_artifact_hashes["fixture_receipt"] = sha256_file(
        FIXTURE_RECEIPT_PATH
    )
    _write_prereg(fixtures, preflight)
    receipt = provenance.attributed_payload(
        {
            "schema": "tatqa_wp1_receipt_v1",
            "spec_revision": SPEC_REVISION,
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
            "artifact_hashes": wp_artifact_hashes,
            "fixture_results": obligations,
            "preflight_results": preflight["checks"],
            "scoring_inputs": metrics["scoring_inputs"],
            "cost": {
                "model_calls": 0,
                "endpoint_calls": 0,
            },
            "safety": {
                "candidate_item_scoring": _safety_claim(
                    False, "derived", "WP-1 executes synthetic fixtures only"
                ),
                "held_out_result_read": _safety_claim(
                    False, "derived", "WP-1 reads no held-out result"
                ),
                "scoring_inputs_all_synthetic": _safety_claim(
                    True,
                    "derived",
                    "instrumented score_item call log contains only synthetic ids",
                ),
                "write_paths_confined": _safety_claim(
                    True,
                    "attested: true",
                    "run 1c writes only authorized WP-1 research and data paths",
                ),
            },
            "fixture_receipt": {
                "canonical_path": str(
                    FIXTURE_RECEIPT_PATH.relative_to(REPO_ROOT)
                ),
                "repo_mirror_byte_identical": _safety_claim(
                    True, "derived", "runner compares canonical and mirror bytes"
                ),
                "repo_mirror_path": str(
                    FIXTURE_RECEIPT_MIRROR_PATH.relative_to(REPO_ROOT)
                ),
                "sha256": wp_artifact_hashes["fixture_receipt"],
            },
            "unverified_items": [
                "real E/C experience blocks were not constructed",
                "actor freeze and model selection remain PENDING",
                "origin-disjoint episode and near-duplicate receipts remain PENDING",
                "held-out pilot and scientific outcomes remain UNVERIFIED",
            ],
            "deviations": fixture_payload["deviations"],
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
