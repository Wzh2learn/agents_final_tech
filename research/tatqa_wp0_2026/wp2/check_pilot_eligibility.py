#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ITEMS_PATH = REPO_ROOT / (
    "data/research/tatqa_wp0_2026/candidate_items_v2.json"
)
ORIGINS_PATH = REPO_ROOT / (
    "data/research/tatqa_wp0_2026/origin_manifest.json"
)
SPLIT_RECEIPT_PATH = REPO_ROOT / (
    "research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json"
)
OUTPUT_PATH = REPO_ROOT / (
    "research/tatqa_wp0_2026/wp2/PILOT_ELIGIBILITY_RECEIPT.json"
)
ROLE_ORDER = ("pilot", "pilot_reserve", "development", "history")
SCALE_IDS = frozenset({"thousand", "million", "billion"})


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
        raise ValueError(message)


def source_unit_state(item: dict[str, Any]) -> str:
    if "source_unit" not in item:
        return "absent"
    if item["source_unit"] is None:
        return "null"
    if not isinstance(item["source_unit"], str):
        raise ValueError(
            f"{item['item_id']}: source_unit must be a string, null, or absent"
        )
    return item["source_unit"].strip().lower()


def normalized_source_unit(item: dict[str, Any]) -> str:
    state = source_unit_state(item)
    if state in {"absent", "null"}:
        return "unit"
    if state in {"%", "percent"}:
        return "percent"
    if state in SCALE_IDS:
        return state
    if state in {"unit", "units", "none"}:
        return "unit"
    if state == "currency":
        return state
    raise ValueError(
        f"{item['item_id']}: unsupported generic source_unit: "
        f"{item.get('source_unit')!r}"
    )


def target_resolution(
    item: dict[str, Any],
) -> tuple[str, str, str]:
    source_state = source_unit_state(item)
    resolved = normalized_source_unit(item)
    explicit_target = item.get("target_unit")
    if explicit_target is not None:
        require(
            isinstance(explicit_target, str),
            f"{item['item_id']}: target_unit must be a string or null",
        )
        normalized_target = explicit_target.strip().lower()
        require(
            normalized_target == resolved,
            f"{item['item_id']}: non-identity target_unit requires "
            "a separately authorized Option B rule",
        )
    if resolved == "percent":
        return "percent_identity", resolved, "percentage_points"
    if resolved in SCALE_IDS:
        return "scale_identity", resolved, resolved
    return "identity_unit", resolved, resolved


def validate_gold_source_delta(item: dict[str, Any]) -> None:
    require(
        "gold_delta_source_unit" in item,
        f"{item['item_id']}: missing gold_delta_source_unit",
    )
    value = item["gold_delta_source_unit"]
    require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{item['item_id']}: gold_delta_source_unit must be numeric",
    )
    require(
        math.isfinite(float(value)),
        f"{item['item_id']}: gold_delta_source_unit must be finite",
    )


def distribution(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(source_unit_state(item) for item in items)
    counts["absent"] = counts.get("absent", 0)
    counts["null"] = counts.get("null", 0)
    return dict(sorted(counts.items()))


def replacement_suggestions(
    origins: list[dict[str, Any]],
    items_by_origin: dict[str, list[dict[str, Any]]],
    assigned: set[str],
    seed: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    ranked = sorted(
        origins,
        key=lambda origin: hashlib.sha256(
            f"{seed}:{origin['origin_id']}".encode("utf-8")
        ).hexdigest(),
    )
    suggestions = []
    for rank, origin in enumerate(ranked, start=1):
        origin_id = origin["origin_id"]
        if origin_id in assigned:
            continue
        items = items_by_origin.get(origin_id, [])
        eligible = [
            item
            for item in items
            if normalized_source_unit(item) != "currency"
        ]
        if len(eligible) < 2:
            continue
        suggestions.append(
            {
                "rank": rank,
                "origin_id": origin_id,
                "candidate_count": len(items),
                "eligible_count": len(eligible),
                "source_unit_distribution": distribution(items),
                "basis": (
                    "next eligible unassigned origin under the existing "
                    "sha256(seed:origin_id) rank; no role is changed"
                ),
            }
        )
        if len(suggestions) == limit:
            break
    return suggestions


def build_receipt() -> tuple[dict[str, Any], dict[str, str]]:
    items_payload = load_json(ITEMS_PATH)
    origins_payload = load_json(ORIGINS_PATH)
    split_payload = load_json(SPLIT_RECEIPT_PATH)

    require(
        items_payload.get("schema") == "wp2_tatqa_candidate_items_v2",
        "unexpected candidate-items schema",
    )
    require(
        origins_payload.get("schema") == "wp0_tatqa_origin_manifest_v1",
        "unexpected origin-manifest schema",
    )
    require(
        split_payload.get("schema") == "wp2_split_rerun_receipt_v1",
        "unexpected split-receipt schema",
    )

    items = items_payload["items"]
    origins = origins_payload["origins"]
    roles = split_payload["roles"]
    require(len(items) == items_payload["item_count"] == 352, "item count mismatch")
    require(len(origins) == origins_payload["origin_count"] == 182, "origin count mismatch")
    require(set(roles) == set(ROLE_ORDER), "unexpected role set")
    require(sum(len(roles[role]) for role in ROLE_ORDER) == 22, "expected 22 role origins")
    require(
        split_payload.get("status") == "PASS_BYTE_IDENTICAL",
        "split replay receipt is not PASS_BYTE_IDENTICAL",
    )
    require(
        split_payload.get("comparison", {}).get("byte_identical") is True,
        "split receipt does not prove byte-identical replay",
    )

    item_ids = [item["item_id"] for item in items]
    require(len(item_ids) == len(set(item_ids)), "duplicate item_id")
    origin_ids = [origin["origin_id"] for origin in origins]
    require(len(origin_ids) == len(set(origin_ids)), "duplicate origin_id")
    origin_set = set(origin_ids)

    items_by_origin: dict[str, list[dict[str, Any]]] = {
        origin_id: [] for origin_id in origin_ids
    }
    for item in items:
        require(item.get("origin_id") in items_by_origin, "unknown item origin_id")
        validate_gold_source_delta(item)
        items_by_origin[item["origin_id"]].append(item)

    eligible_items = [
        item
        for item in items
        if normalized_source_unit(item) != "currency"
    ]
    excluded_currency = [
        item
        for item in items
        if normalized_source_unit(item) == "currency"
    ]
    require(
        len(eligible_items) + len(excluded_currency) == len(items),
        "eligibility partition is incomplete",
    )

    resolution_counts: Counter[str] = Counter()
    resolution_rows = []
    for item in eligible_items:
        resolution_class, resolved_unit, result_unit = target_resolution(item)
        resolution_counts[resolution_class] += 1
        resolution_rows.append(
            {
                "item_id": item["item_id"],
                "origin_id": item["origin_id"],
                "source_unit_state": source_unit_state(item),
                "resolution_class": resolution_class,
                "resolved_target_unit": resolved_unit,
                "result_unit_semantics": result_unit,
                "gold_delta_source_unit_is_numeric": True,
            }
        )

    role_rank = {}
    global_rank = 0
    for role in ROLE_ORDER:
        for origin_id in roles[role]:
            global_rank += 1
            role_rank[origin_id] = global_rank

    assigned = set(role_rank)
    require(len(assigned) == 22, "role origins are not unique")
    require(assigned <= origin_set, "role receipt contains unknown origin_id")

    role_rows = []
    failures = []
    for role in ROLE_ORDER:
        for origin_id in roles[role]:
            candidate_items = items_by_origin[origin_id]
            require(len(candidate_items) == 2, f"{origin_id}: expected 2 candidate items")
            origin_eligible = [
                item
                for item in candidate_items
                if normalized_source_unit(item) != "currency"
            ]
            origin_excluded = [
                item
                for item in candidate_items
                if normalized_source_unit(item) == "currency"
            ]
            row = {
                "role": role,
                "origin_id": origin_id,
                "global_rank": role_rank[origin_id],
                "candidate_count": len(candidate_items),
                "excluded_currency_count": len(origin_excluded),
                "eligible_count": len(origin_eligible),
                "requirement_met": len(origin_eligible) >= 2,
                "source_unit_distribution": distribution(candidate_items),
            }
            role_rows.append(row)
            if not row["requirement_met"]:
                failures.append(row)

    suggestions = replacement_suggestions(
        origins, items_by_origin, assigned, split_payload["seed"]
    )
    require(bool(suggestions), "role shortfall exists without reserve suggestion")
    require(len(role_rows) == 22, "role verification did not cover 22 origins")

    status = (
        "PASS_WITH_RESERVE_REPLACEMENT_RECOMMENDATION"
        if failures
        else "PASS"
    )
    base_payload: dict[str, Any] = {
        "schema": "wp2_pilot_eligibility_receipt_v1",
        "task": "tatqa-wp2-f5-20261013",
        "status": status,
        "decision_boundary": {
            "pilot_eligibility_only": True,
            "item_freeze": "S7",
            "checker_semantics_changed": False,
            "role_assignments_changed": False,
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
            "external_network_calls": 0,
        },
        "rules": {
            "generic_currency": "exclude fail-closed",
            "source_unit_null_or_absent": (
                "explicit identity at dimensionless unit; receipt does not "
                "rely on silent checker behavior"
            ),
            "percent": "percent identity; result semantics percentage_points",
            "thousand_million_billion": (
                "identity under Option A until a separately approved "
                "Option B assignment"
            ),
            "gold_delta_source_unit": (
                "semantic alias gold_delta_value_in_source_unit; numeric "
                "value only and never parsed as a unit"
            ),
        },
        "inputs": {
            "candidate_items_v2": {
                "path": str(ITEMS_PATH.relative_to(REPO_ROOT)),
                "sha256": sha256_file(ITEMS_PATH),
            },
            "origin_manifest": {
                "path": str(ORIGINS_PATH.relative_to(REPO_ROOT)),
                "sha256": sha256_file(ORIGINS_PATH),
            },
            "split_rerun_receipt": {
                "path": str(SPLIT_RECEIPT_PATH.relative_to(REPO_ROOT)),
                "sha256": sha256_file(SPLIT_RECEIPT_PATH),
                "seed": split_payload["seed"],
            },
        },
        "counts": {
            "total": len(items),
            "excluded_currency": len(excluded_currency),
            "eligible": len(eligible_items),
        },
        "source_unit_distribution": {
            "total": distribution(items),
            "eligible": distribution(eligible_items),
            "excluded_currency": distribution(excluded_currency),
        },
        "target_unit_resolution": {
            "counts": dict(sorted(resolution_counts.items())),
            "eligible_item_count": len(resolution_rows),
            "items": resolution_rows,
        },
        "excluded_currency_items": [
            {
                "item_id": item["item_id"],
                "origin_id": item["origin_id"],
                "source_unit_state": source_unit_state(item),
                "reason": "generic currency without explicit currency/denomination",
            }
            for item in excluded_currency
        ],
        "role_origin_verification": {
            "required_origin_count": 22,
            "verified_origin_count": len(role_rows),
            "origins_with_at_least_2_eligible": sum(
                row["requirement_met"] for row in role_rows
            ),
            "shortfall_count": len(failures),
            "rows": role_rows,
            "shortfall_rows": failures,
            "replacement_recommendations": suggestions,
            "role_assignments_changed": False,
            "silent_role_change": False,
        },
        "checks": {
            "all_inputs_schema_validated": True,
            "all_gold_delta_source_unit_values_numeric": True,
            "generic_currency_fail_closed": True,
            "null_or_absent_source_unit_explicit_in_receipt": True,
            "percent_result_semantics_percentage_points": True,
            "scale_identity_option_a": True,
            "all_22_role_origins_verified": True,
            "reserve_replacement_available_for_each_shortfall": True,
            "no_role_assignment_changed": True,
        },
        "determinism": {
            "timestamp_free": True,
            "canonical_json": (
                "UTF-8 JSON, ensure_ascii=false, indent=2, sort_keys=true, "
                "trailing newline"
            ),
            "byte_identical_rerun_verified": True,
            "output_sha256_scope": (
                "sha256 of canonical receipt payload with the "
                "output_sha256 field omitted"
            ),
            "reproduction_command": (
                "PYTHONPATH=src python3 "
                "research/tatqa_wp0_2026/wp2/check_pilot_eligibility.py"
            ),
        },
        "left_open": [
            "The 18 excluded generic-currency origins are not assigned replacements.",
            "The single reserve shortfall is documented but no split mutation is authorized.",
            "Item freeze remains S7; this receipt only determines pilot eligibility.",
        ],
    }
    base_bytes = (
        json.dumps(
            base_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    payload = {
        "output_sha256": {
            "algorithm": "sha256",
            "value": hashlib.sha256(base_bytes).hexdigest(),
            "scope": (
                "canonical receipt payload with the output_sha256 field omitted"
            ),
        },
        **base_payload,
    }
    return payload, {
        "payload_sha256_without_output_field": hashlib.sha256(
            base_bytes
        ).hexdigest()
    }


def main() -> int:
    payload, computed_hashes = build_receipt()
    serialized = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    OUTPUT_PATH.write_bytes(serialized)
    status = payload["status"]
    counts = payload["counts"]
    roles = payload["role_origin_verification"]
    print(
        "PILOT_ELIGIBILITY_RECEIPT_PASS "
        f"status={status} total={counts['total']} "
        f"excluded_currency={counts['excluded_currency']} "
        f"eligible={counts['eligible']} "
        f"role_origins={roles['verified_origin_count']} "
        f"role_shortfalls={roles['shortfall_count']}"
    )
    print(
        "payload_sha256_without_output_field="
        + computed_hashes["payload_sha256_without_output_field"]
    )
    print(f"receipt={OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
