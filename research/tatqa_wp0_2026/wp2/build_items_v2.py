#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data/research/tatqa_wp0_2026"
RAW_DIR = ROOT / "data/research/tatqa_raw_2026"
ORIGIN_MANIFEST_PATH = DATA_DIR / "origin_manifest.json"
RAW_TRAIN_PATH = RAW_DIR / "tatqa_dataset_train.json"
RAW_DEV_PATH = RAW_DIR / "tatqa_dataset_dev.json"
DRAFT_SPLIT_RECEIPT_PATH = (
    ROOT / "research/tatqa_wp0_2026/WP2_SPLIT_DRYRUN_RECEIPT.json"
)
OUTPUT_PATH = DATA_DIR / "candidate_items_v2.json"
RECEIPT_PATH = ROOT / (
    "research/tatqa_wp0_2026/wp2/ITEMS_V2_RECEIPT.json"
)

YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
UNIT_PATTERN = re.compile(
    r"(%|\$|¥|£|€|EUR|USD|RMB|CNY|million|thousand|billion)",
    re.IGNORECASE,
)
SCALE_MARKERS = [
    ("billion", Decimal(10) ** 9),
    ("million", Decimal(10) ** 6),
    ("thousand", Decimal(10) ** 3),
    ("%", Decimal(1)),
]


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


def parse_numeric(value: Any) -> Decimal | None:
    text = str(value).strip().replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric cell: {value!r}") from exc
    return -parsed if negative else parsed


def header_scale(header: str) -> str | None:
    lowered = header.lower()
    for marker, _ in SCALE_MARKERS:
        if marker.lower() in lowered:
            return marker
    if re.search(r"[$¥£€]", header):
        return "currency"
    return None


def json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def load_raw_records() -> dict[str, tuple[str, dict[str, Any]]]:
    records: dict[str, tuple[str, dict[str, Any]]] = {}
    for split, path in (
        ("train", RAW_TRAIN_PATH),
        ("dev", RAW_DEV_PATH),
    ):
        for record in load_json(path):
            uid = str(record["table"]["uid"])
            require(
                uid not in records,
                f"duplicate raw TAT-QA uid: {uid}",
            )
            records[uid] = (split, record)
    return records


def build_candidate_payload() -> dict[str, Any]:
    manifest = load_json(ORIGIN_MANIFEST_PATH)
    raw_records = load_raw_records()
    items: list[dict[str, Any]] = []

    for origin in manifest["origins"]:
        usable_rows = [int(row) for row in origin["usable_rows"]]
        if len(usable_rows) < 2:
            continue
        origin_id = str(origin["origin_id"])
        uid = str(origin["uid"])
        require(
            origin_id == f"tatqa_{uid}",
            f"origin/uid mismatch: {origin_id} / {uid}",
        )
        require(
            uid in raw_records,
            f"origin is absent from raw inputs: {origin_id}",
        )
        split, record = raw_records[uid]
        require(
            split == origin["split"],
            f"origin split mismatch: {origin_id}",
        )
        table = record["table"]["table"]
        require(
            isinstance(table, list) and len(table) >= 2,
            f"invalid table for {origin_id}",
        )
        headers = [str(cell) for cell in table[0]]
        period_columns = [int(col) for col in origin["period_columns"]]
        require(
            len(period_columns) >= 2,
            f"origin has fewer than two periods: {origin_id}",
        )
        for position, row_index in enumerate(usable_rows[:2]):
            row = table[row_index]
            valid_periods = []
            for period_col in period_columns:
                require(
                    period_col < len(row),
                    f"period cell out of bounds: {origin_id} row {row_index}",
                )
                value = parse_numeric(row[period_col])
                if value is not None:
                    valid_periods.append((period_col, value))
            require(
                len(valid_periods) >= 2,
                f"fewer than two numeric period cells: {origin_id} row {row_index}",
            )
            late_col, late_value = valid_periods[0]
            early_col, early_value = valid_periods[-1]
            late_label = headers[late_col]
            early_label = headers[early_col]
            source_unit = (
                header_scale(late_label) or header_scale(early_label)
            )
            delta = late_value - early_value
            items.append(
                {
                    "item_id": (
                        f"wp2_{uid[:8]}_r{row_index}_p{position}"
                    ),
                    "origin_id": origin_id,
                    "split": split,
                    "table": table,
                    "row_index": row_index,
                    "period_late": {
                        "col": late_col,
                        "label": late_label,
                    },
                    "period_early": {
                        "col": early_col,
                        "label": early_label,
                    },
                    "source_unit": source_unit,
                    "requested_quantity": (
                        "increase" if delta >= 0 else "decrease"
                    ),
                    "gold_delta_source_unit": json_number(delta),
                    "gold_recompute_rule": (
                        "value(late) - value(early) on row_index, "
                        "both read from the table cells"
                    ),
                }
            )

    return {
        "schema": "wp2_tatqa_candidate_items_v2",
        "status": "DRAFT_NOT_FROZEN",
        "note": (
            "Deterministic expansion to two candidate items for every "
            "origin with at least two usable rows. Gold is recomputed "
            "from table cells and is not a model output or dataset "
            "annotation. target_unit remains unresolved under WP2 S2."
        ),
        "item_count": len(items),
        "items": items,
    }


def canonical_bytes(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    ).encode("utf-8")


def build_receipt(
    manifest: dict[str, Any],
    draft_split_receipt: dict[str, Any],
    candidate_bytes: bytes,
    deterministic_equal: bool,
) -> dict[str, Any]:
    payload = json.loads(candidate_bytes.decode("utf-8"))
    items = payload["items"]
    items_per_origin = Counter(item["origin_id"] for item in items)
    eligible_origins = [
        origin
        for origin in manifest["origins"]
        if len(origin["usable_rows"]) >= 2
    ]
    role_origins = [
        origin_id
        for role in (
            "pilot",
            "pilot_reserve",
            "development",
            "history",
        )
        for origin_id in draft_split_receipt["roles"][role]
    ]
    role_checks = {
        origin_id: {
            "items": items_per_origin[origin_id],
            "ge2_items": items_per_origin[origin_id] >= 2,
        }
        for origin_id in role_origins
    }
    require(len(role_origins) == 22, "draft split does not contain 22 roles")
    require(
        all(row["ge2_items"] for row in role_checks.values()),
        "a draft role origin has fewer than two candidate items",
    )
    require(
        len(items_per_origin) == len(eligible_origins) == 176,
        "eligible-origin coverage is not 176",
    )
    require(
        all(count >= 2 for count in items_per_origin.values()),
        "an eligible origin has fewer than two items",
    )
    require(deterministic_equal, "builder rerun was not byte-identical")

    return {
        "schema": "wp2_items_v2_receipt_v1",
        "status": "DRAFT_NOT_FROZEN",
        "builder": "research/tatqa_wp0_2026/wp2/build_items_v2.py",
        "counts": {
            "origins_total": len(manifest["origins"]),
            "origins_with_ge2_usable_rows": len(eligible_origins),
            "candidate_items": len(items),
            "distinct_item_origins": len(items_per_origin),
            "role_origins_checked": len(role_origins),
            "role_origins_with_ge2_items": sum(
                row["ge2_items"] for row in role_checks.values()
            ),
        },
        "items_per_origin_distribution": {
            str(count): total
            for count, total in sorted(
                Counter(items_per_origin.values()).items()
            )
        },
        "source_unit_distribution": {
            unit_name: total
            for unit_name, total in sorted(
                Counter(
                    (
                        "null"
                        if item.get("source_unit") is None
                        else str(item["source_unit"])
                    )
                    for item in items
                ).items()
            )
        },
        "usable_rows_per_eligible_origin_distribution": {
            str(count): total
            for count, total in sorted(
                Counter(
                    len(origin["usable_rows"])
                    for origin in eligible_origins
                ).items()
            )
        },
        "role_origin_checks": role_checks,
        "determinism": {
            "builder_executions_compared": 2,
            "byte_identical": deterministic_equal,
            "first_output_sha256": hashlib.sha256(
                candidate_bytes
            ).hexdigest(),
            "second_output_sha256": hashlib.sha256(
                candidate_bytes
            ).hexdigest(),
        },
        "input_hashes": {
            "origin_manifest": sha256_file(ORIGIN_MANIFEST_PATH),
            "raw_train": sha256_file(RAW_TRAIN_PATH),
            "raw_dev": sha256_file(RAW_DEV_PATH),
            "draft_split_receipt": sha256_file(
                DRAFT_SPLIT_RECEIPT_PATH
            ),
        },
        "output_hashes": {
            "candidate_items_v2": hashlib.sha256(
                candidate_bytes
            ).hexdigest(),
            "builder": sha256_file(Path(__file__)),
        },
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
        },
    }


def main() -> int:
    first = build_candidate_payload()
    second = build_candidate_payload()
    first_bytes = canonical_bytes(first)
    second_bytes = canonical_bytes(second)
    deterministic_equal = first_bytes == second_bytes
    require(deterministic_equal, "two builder executions differ")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(first_bytes)
    receipt = build_receipt(
        load_json(ORIGIN_MANIFEST_PATH),
        load_json(DRAFT_SPLIT_RECEIPT_PATH),
        first_bytes,
        deterministic_equal,
    )
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_bytes(canonical_bytes(receipt))
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "counts": receipt["counts"],
                "items_per_origin_distribution": receipt[
                    "items_per_origin_distribution"
                ],
                "byte_identical": deterministic_equal,
                "candidate_items_v2_sha256": receipt[
                    "output_hashes"
                ]["candidate_items_v2"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
