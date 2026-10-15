#!/usr/bin/env python3
"""Run the frozen Paper E Layer-1 independent-gold contract with zero external calls."""

from __future__ import annotations

import hashlib
import json
import re
import string
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


RUN_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUN_DIR.parents[1]

PLAN_PATH = RUN_DIR / "LAYER1_ANALYSIS_PLAN_v1.md"
RESULTS_PATH = RUN_DIR / "LAYER1_RESULTS_v1.json"
RECEIPT_PATH = RUN_DIR / "LAYER1_RECEIPT_v1.json"
SUMMARY_PATH = RUN_DIR / "LAYER1_SUMMARY_v1.md"

INJECTION_MAP_PATH = REPO_ROOT / "data/research/drift_v0/output/injection_map.json"
SOURCE_TABLES_PATH = REPO_ROOT / "data/research/drift_v0/input/tatqa_tables.json"
INJECTED_TABLES_PATH = REPO_ROOT / "data/research/drift_v0/output/injected_tables.json"
CHECKER_PATH = REPO_ROOT / "logs/graph/eval/t2_visibility_sensitivity.json"

FROZEN_PLAN_SHA256 = "a275e55ae3485db5f37716c6c6c229f9d4efd58dfbb078af2db5768cc043e3d9"
EXPECTED_HASHES = {
    str(INJECTION_MAP_PATH.relative_to(REPO_ROOT)): (
        "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e"
    ),
    str(SOURCE_TABLES_PATH.relative_to(REPO_ROOT)): (
        "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302"
    ),
}

LABEL_E = "LEGAL_VARIATION"
LABEL_H = "HARMFUL_ERROR"
LABEL_U = "INSUFFICIENT_EVIDENCE"
VALID_LABELS = (LABEL_E, LABEL_H, LABEL_U)
CHECKER_VERDICTS = ("visible", "blind")
U_RATE_CEILING = 0.30
CALL_COUNTS = {
    "model_calls": 0,
    "judge_calls": 0,
    "endpoint_calls": 0,
    "network_calls": 0,
    "training_calls": 0,
    "total_calls": 0,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_norm(value: Any) -> str:
    if not isinstance(value, str):
        return "NON_STRING"
    normalized = unicodedata.normalize("NFKC", value)
    folded = normalized.casefold()
    punctuation_replaced = "".join(
        " "
        if unicodedata.category(character).startswith("P") or character in string.punctuation
        else character
        for character in folded
    )
    whitespace_collapsed = re.sub(r"\s+", " ", punctuation_replaced)
    return whitespace_collapsed.strip(" ")


def levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1]
                    + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def scalar_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def injection_id(entry: dict[str, Any]) -> str:
    explicit = entry.get("injection_id")
    if isinstance(explicit, str) and explicit:
        return explicit
    fields = (
        "uid",
        "col",
        "original",
        "injected",
        "type",
        "variant",
        "seed_component",
    )
    return "\x1f".join(scalar_json(entry.get(field)) for field in fields)


def is_dev(identifier: str) -> bool:
    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    value = int.from_bytes(digest, "big")
    return value % 10 < 5


def checker_core_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entry.get("uid"),
        entry.get("col"),
        entry.get("original"),
        entry.get("injected"),
        entry.get("type"),
    )


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def index_unique_tables(records: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError(f"{label} must be a JSON array")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("uid"), str):
            raise ValueError(f"{label} has a non-object or non-string uid")
        uid = record["uid"]
        if uid in indexed:
            raise ValueError(f"{label} has duplicate uid {uid}")
        if not isinstance(record.get("table"), list) or not record["table"]:
            raise ValueError(f"{label} uid {uid} has no table rows")
        indexed[uid] = record
    return indexed


def extract_column_values(
    table: list[Any], column_index: int, row_count: int
) -> list[Any]:
    values: list[Any] = []
    for row_index in range(1, row_count):
        row = table[row_index]
        if not isinstance(row, list) or column_index >= len(row):
            raise ValueError(f"row {row_index} cannot supply column {column_index}")
        values.append(row[column_index])
    return values


def serialize_values(values: list[Any]) -> bytes:
    return json.dumps(
        values,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def u_row(
    identifier: str,
    entry: dict[str, Any],
    split: str,
    reason: str,
    value_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "injection_id": identifier,
        "uid": entry.get("uid"),
        "col": entry.get("col"),
        "type": entry.get("type"),
        "original": entry.get("original"),
        "injected": entry.get("injected"),
        "split": split,
        "label": LABEL_U,
        "binding": None,
        "nearest_distances": None,
        "tie": None,
        "reasons": [reason],
        "value_invariant": None,
        "clean_column_sha256": None,
        "injected_column_sha256": None,
    }
    if value_evidence is not None:
        row.update(value_evidence)
    return row


def evaluate_dev_case(
    entry: dict[str, Any],
    identifier: str,
    split: str,
    source_by_uid: dict[str, dict[str, Any]],
    injected_by_uid: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    uid = entry.get("uid")
    if not isinstance(uid, str):
        return u_row(identifier, entry, split, "uid_not_string")
    if uid not in source_by_uid or uid not in injected_by_uid:
        return u_row(identifier, entry, split, "table_lookup_missing")
    if entry.get("row") != 0:
        return u_row(identifier, entry, split, "header_row_not_zero")

    source_table = source_by_uid[uid]["table"]
    injected_table = injected_by_uid[uid]["table"]
    if not source_table or not injected_table:
        return u_row(identifier, entry, split, "table_header_missing")
    if not isinstance(source_table[0], list) or not source_table[0]:
        return u_row(identifier, entry, split, "source_header_not_list")
    if not isinstance(injected_table[0], list) or not injected_table[0]:
        return u_row(identifier, entry, split, "injected_header_not_list")

    source_headers = source_table[0]
    if not all(isinstance(header, str) for header in source_headers):
        return u_row(identifier, entry, split, "source_header_non_string")

    column_index = entry.get("col")
    if isinstance(column_index, bool) or not isinstance(column_index, int):
        return u_row(identifier, entry, split, "column_index_not_integer")
    if column_index < 0 or column_index >= len(source_headers):
        return u_row(identifier, entry, split, "column_index_out_of_range")
    if entry.get("original") != source_headers[column_index]:
        return u_row(identifier, entry, split, "original_header_provenance_mismatch")

    expected_injected_header = entry.get("injected")
    if (
        column_index >= len(injected_table[0])
        or injected_table[0][column_index] != expected_injected_header
    ):
        return u_row(identifier, entry, split, "injected_header_provenance_mismatch")

    if len(source_table) != len(injected_table):
        return u_row(identifier, entry, split, "row_count_mismatch")
    try:
        clean_values = extract_column_values(source_table, column_index, len(source_table))
        injected_values = extract_column_values(
            injected_table, column_index, len(injected_table)
        )
        clean_bytes = serialize_values(clean_values)
        injected_bytes = serialize_values(injected_values)
    except (TypeError, ValueError, OverflowError) as error:
        return u_row(
            identifier,
            entry,
            split,
            "value_serialization_failure",
            {"value_error": str(error)},
        )

    value_evidence = {
        "value_invariant": clean_bytes == injected_bytes,
        "clean_column_sha256": hashlib.sha256(clean_bytes).hexdigest(),
        "injected_column_sha256": hashlib.sha256(injected_bytes).hexdigest(),
        "clean_value_count": len(clean_values),
        "injected_value_count": len(injected_values),
    }
    if clean_bytes != injected_bytes:
        row = u_row(
            identifier,
            entry,
            split,
            "value_invariance_failed_bytewise",
            value_evidence,
        )
        return row

    canonical_headers = [canonical_norm(header) for header in source_headers]
    if any(header == "" for header in canonical_headers):
        return u_row(
            identifier,
            entry,
            split,
            "source_header_empty_after_norm",
            value_evidence,
        )
    if len(set(canonical_headers)) != len(canonical_headers):
        return u_row(
            identifier,
            entry,
            split,
            "source_header_canonical_collision",
            value_evidence,
        )

    original_norm = canonical_norm(entry.get("original"))
    injected_norm = canonical_norm(entry.get("injected"))
    if original_norm == "NON_STRING" or injected_norm == "NON_STRING":
        return u_row(identifier, entry, split, "header_non_string", value_evidence)
    if injected_norm == "":
        return u_row(identifier, entry, split, "injected_header_empty_after_norm", value_evidence)
    if original_norm != source_headers[column_index] and canonical_norm(
        source_headers[column_index]
    ) != original_norm:
        return u_row(
            identifier,
            entry,
            split,
            "original_header_canonical_provenance_mismatch",
            value_evidence,
        )

    row = {
        "injection_id": identifier,
        "uid": uid,
        "col": column_index,
        "type": entry.get("type"),
        "original": entry.get("original"),
        "injected": entry.get("injected"),
        "split": split,
        "original_norm": original_norm,
        "injected_norm": injected_norm,
        "reasons": [],
        **value_evidence,
    }

    if injected_norm == original_norm:
        matching_positions = [
            position
            for position, canonical in enumerate(canonical_headers)
            if canonical == original_norm
        ]
        if matching_positions != [column_index]:
            row.update(
                {
                    "label": LABEL_U,
                    "binding": None,
                    "nearest_distances": None,
                    "tie": None,
                    "reasons": ["direct_match_not_unique_target"],
                }
            )
            return row
        row.update(
            {
                "label": LABEL_E,
                "binding": column_index,
                "nearest_distances": None,
                "tie": False,
                "reasons": ["canonical_exact_match_to_target"],
            }
        )
        return row

    distances = {
        str(position): levenshtein(injected_norm, canonical)
        for position, canonical in enumerate(canonical_headers)
    }
    minimum = min(distances.values(), default=None)
    if minimum is None:
        row.update(
            {
                "label": LABEL_U,
                "binding": None,
                "nearest_distances": distances,
                "tie": None,
                "reasons": ["source_header_set_empty"],
            }
        )
        return row
    nearest_positions = [
        position
        for position, distance in enumerate(distances.values())
        if distance == minimum
    ]
    if len(nearest_positions) != 1:
        row.update(
            {
                "label": LABEL_U,
                "binding": None,
                "nearest_distances": distances,
                "tie": True,
                "reasons": ["nearest_neighbour_tie"],
            }
        )
        return row

    binding = nearest_positions[0]
    row.update(
        {
            "label": LABEL_E if binding == column_index else LABEL_H,
            "binding": binding,
            "nearest_distances": distances,
            "tie": False,
            "reasons": (
                ["unique_nearest_neighbour_target"]
                if binding == column_index
                else ["unique_nearest_neighbour_other_column"]
            ),
        }
    )
    return row


def build_contingency(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        verdict: {
            label: sum(
                1
                for row in rows
                if row["checker_verdict"] == verdict and row["label"] == label
            )
            for label in VALID_LABELS
        }
        for verdict in CHECKER_VERDICTS
    }


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def markdown_contingency(contingency: dict[str, dict[str, int]]) -> str:
    lines = [
        "| checker verdict | E | H | U |",
        "|---|---:|---:|---:|",
    ]
    for verdict in CHECKER_VERDICTS:
        counts = contingency[verdict]
        lines.append(
            f"| {verdict} | {counts[LABEL_E]} | {counts[LABEL_H]} | {counts[LABEL_U]} |"
        )
    return "\n".join(lines)


def emit_stop(status: str, message: str, input_evidence: dict[str, Any]) -> None:
    plan_hash = sha256_file(PLAN_PATH) if PLAN_PATH.is_file() else None
    results = {
        "schema": "paper_e_layer1_results_v1",
        "status": status,
        "message": message,
        "case_rows": [],
        "contingency": None,
        "rates": None,
        "self_check": False,
    }
    receipt = {
        "schema": "paper_e_layer1_receipt_v1",
        "status": status,
        "message": message,
        "plan": {
            "path": str(PLAN_PATH.relative_to(REPO_ROOT)),
            "sha256": plan_hash,
            "frozen_sha256": FROZEN_PLAN_SHA256,
            "hash_matches_frozen": plan_hash == FROZEN_PLAN_SHA256,
        },
        "inputs": input_evidence,
        "counts": {"dev_cases": 0, "label_counts": {}, "contingency": None},
        "calls": CALL_COUNTS,
        "self_check": False,
    }
    summary = (
        f"# Paper E Layer-1 Independent Gold Summary v1\n\n"
        f"**Status:** `{status}`  \n"
        f"**Report:** {message}\n\n"
        "No case label is claimed under this stop. Calls remain zero.\n"
    )
    write_json(RESULTS_PATH, results)
    write_json(RECEIPT_PATH, receipt)
    write_text(SUMMARY_PATH, summary)


def main() -> int:
    required_paths = (
        PLAN_PATH,
        INJECTION_MAP_PATH,
        SOURCE_TABLES_PATH,
        INJECTED_TABLES_PATH,
        CHECKER_PATH,
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required_paths if not path.is_file()]
    input_evidence: dict[str, Any] = {}
    if missing:
        emit_stop("INPUT_MISSING", f"Required input absent: {', '.join(missing)}", input_evidence)
        return 2

    actual_hashes = {
        str(path.relative_to(REPO_ROOT)): sha256_file(path)
        for path in (
            INJECTION_MAP_PATH,
            SOURCE_TABLES_PATH,
            INJECTED_TABLES_PATH,
            CHECKER_PATH,
        )
    }
    for relative_path, expected in EXPECTED_HASHES.items():
        input_evidence[relative_path] = {
            "present": True,
            "sha256": actual_hashes[relative_path],
            "expected_sha256": expected,
            "matches_expected": actual_hashes[relative_path] == expected,
        }
    mismatches = [
        relative_path
        for relative_path, expected in EXPECTED_HASHES.items()
        if actual_hashes[relative_path] != expected
    ]
    for relative_path in (str(INJECTED_TABLES_PATH.relative_to(REPO_ROOT)), str(CHECKER_PATH.relative_to(REPO_ROOT))):
        input_evidence[relative_path] = {
            "present": True,
            "sha256": actual_hashes[relative_path],
            "expected_sha256": None,
            "matches_expected": None,
        }
    if mismatches:
        emit_stop(
            "HASH_MISMATCH",
            f"Expected input hash mismatch: {', '.join(mismatches)}",
            input_evidence,
        )
        return 3

    plan_hash = sha256_file(PLAN_PATH)
    input_evidence["plan"] = {
        "present": True,
        "sha256": plan_hash,
        "expected_sha256": FROZEN_PLAN_SHA256,
        "matches_expected": plan_hash == FROZEN_PLAN_SHA256,
    }
    if plan_hash != FROZEN_PLAN_SHA256:
        emit_stop(
            "RULE_AMBIGUOUS",
            "The frozen analysis plan hash does not match the pre-case freeze receipt.",
            input_evidence,
        )
        return 4

    try:
        injection_payload = load_json(INJECTION_MAP_PATH)
        source_records = load_json(SOURCE_TABLES_PATH)
        injected_records = load_json(INJECTED_TABLES_PATH)
        checker_payload = load_json(CHECKER_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        emit_stop("INPUT_MISSING", f"Required input could not be read: {error}", input_evidence)
        return 2

    if not isinstance(injection_payload, dict) or not isinstance(
        injection_payload.get("mapping"), list
    ):
        emit_stop("RULE_AMBIGUOUS", "injection_map.mapping is not a list.", input_evidence)
        return 4
    entries = injection_payload["mapping"]
    if not all(isinstance(entry, dict) for entry in entries):
        emit_stop("RULE_AMBIGUOUS", "An injection entry is not an object.", input_evidence)
        return 4
    identifiers = [injection_id(entry) for entry in entries]
    if len(set(identifiers)) != len(identifiers):
        emit_stop(
            "RULE_AMBIGUOUS",
            "The frozen injection-id rule does not produce unique identifiers.",
            input_evidence,
        )
        return 4

    try:
        source_by_uid = index_unique_tables(source_records, "source tables")
        injected_by_uid = index_unique_tables(injected_records, "injected tables")
    except ValueError as error:
        emit_stop("INPUT_MISSING", str(error), input_evidence)
        return 2

    if not isinstance(checker_payload, dict) or not isinstance(
        checker_payload.get("injections"), list
    ):
        emit_stop("INPUT_MISSING", "checker.injections is not a list.", input_evidence)
        return 2
    checker_records = checker_payload["injections"]
    checker_lookup: dict[tuple[Any, ...], bool] = {}
    for record in checker_records:
        if not isinstance(record, dict) or not isinstance(record.get("visible_frozen"), bool):
            emit_stop(
                "INPUT_MISSING",
                "A checker injection lacks boolean visible_frozen.",
                input_evidence,
            )
            return 2
        key = checker_core_key(record)
        if key in checker_lookup:
            emit_stop("INPUT_MISSING", "Checker join key is not unique.", input_evidence)
            return 2
        checker_lookup[key] = record["visible_frozen"]

    dev_entries: list[tuple[str, dict[str, Any]]] = []
    held_out_ids: list[str] = []
    for entry, identifier in zip(entries, identifiers, strict=True):
        if is_dev(identifier):
            dev_entries.append((identifier, entry))
        else:
            held_out_ids.append(identifier)

    rows = [
        evaluate_dev_case(entry, identifier, "dev", source_by_uid, injected_by_uid)
        for identifier, entry in dev_entries
    ]
    if any(row["label"] not in VALID_LABELS for row in rows):
        emit_stop(
            "RULE_AMBIGUOUS",
            "A dev case received a label outside {E,H,U}.",
            input_evidence,
        )
        return 4

    missing_checker: list[str] = []
    for row in rows:
        entry = next(entry for identifier, entry in dev_entries if identifier == row["injection_id"])
        key = checker_core_key(entry)
        if key not in checker_lookup:
            missing_checker.append(row["injection_id"])
            continue
        row["checker_verdict"] = "visible" if checker_lookup[key] else "blind"
    if missing_checker:
        emit_stop(
            "INPUT_MISSING",
            f"Checker verdict absent for {len(missing_checker)} dev cases.",
            input_evidence,
        )
        return 2

    contingency = build_contingency(rows)
    label_counts_all = Counter(row["label"] for row in rows)
    label_counts = {label: label_counts_all.get(label, 0) for label in VALID_LABELS}
    checker_counts = {
        verdict: sum(
            1 for row in rows if row["checker_verdict"] == verdict
        )
        for verdict in CHECKER_VERDICTS
    }
    u_rate = ratio(label_counts[LABEL_U], len(rows))
    co_miss_rate = ratio(contingency["blind"][LABEL_H], checker_counts["blind"])
    co_alarm_rate = ratio(contingency["visible"][LABEL_E], checker_counts["visible"])
    rates = {
        "co_miss_rate_gold_h_given_checker_blind": co_miss_rate,
        "co_alarm_rate_gold_e_given_checker_visible": co_alarm_rate,
        "u_rate_dev": u_rate,
        "u_rate_ceiling": U_RATE_CEILING,
        "u_rate_within_ceiling": u_rate is not None and u_rate <= U_RATE_CEILING,
        "checker_counts": checker_counts,
        "value_invariant_count": sum(
            1 for row in rows if row.get("value_invariant") is True
        ),
    }

    self_checks = {
        "input_hashes_match": all(
            evidence.get("matches_expected") is not False
            for evidence in input_evidence.values()
            if isinstance(evidence, dict)
        ),
        "plan_hash_matches": plan_hash == FROZEN_PLAN_SHA256,
        "all_dev_cases_exactly_one_valid_label": len(rows)
        == sum(label_counts.values())
        and all(row["label"] in VALID_LABELS for row in rows),
        "dev_membership_count_reconciles": len(rows) + len(held_out_ids) == len(entries),
        "checker_join_count_reconciles": sum(checker_counts.values()) == len(rows),
        "contingency_total_reconciles": sum(
            count for verdict in CHECKER_VERDICTS for count in contingency[verdict].values()
        )
        == len(rows),
        "all_u_remain_u": label_counts[LABEL_U]
        == sum(1 for row in rows if row["label"] == LABEL_U),
        "value_invariance_recomputed_for_every_dev_case": all(
            isinstance(row.get("value_invariant"), bool) for row in rows
        ),
        "calls_zero": all(value == 0 for value in CALL_COUNTS.values()),
    }
    self_check_pass = all(self_checks.values())
    if not self_check_pass:
        status = "RULE_AMBIGUOUS"
        message = "Self-check failed; no completion claim is made."
    elif u_rate is None or u_rate > U_RATE_CEILING:
        status = "GOLD_NOT_ESTABLISHED"
        message = "The independent-gold U rate exceeds the frozen 30% ceiling."
    else:
        status = "SELF_CHECK_PASS"
        message = "The frozen independent contract produced one label per dev case."

    results = {
        "schema": "paper_e_layer1_results_v1",
        "status": status,
        "plan_sha256": plan_hash,
        "scope": {
            "total_injections": len(entries),
            "dev_cases": len(rows),
            "held_out_cases": len(held_out_ids),
            "held_out_injection_ids": held_out_ids,
            "dev_split_rule": "int(sha256(injection_id).digest(), big) mod 10 < 5",
        },
        "label_counts": label_counts,
        "case_rows": rows,
        "contingency": contingency,
        "rates": rates,
        "human_adjudication_required": [
            {
                "injection_id": row["injection_id"],
                "uid": row["uid"],
                "col": row["col"],
                "reasons": row["reasons"],
            }
            for row in rows
            if row["label"] == LABEL_U
        ],
        "self_check": self_check_pass,
        "self_checks": self_checks,
    }

    receipt = {
        "schema": "paper_e_layer1_receipt_v1",
        "status": status,
        "plan": {
            "path": str(PLAN_PATH.relative_to(REPO_ROOT)),
            "sha256": plan_hash,
            "frozen_sha256": FROZEN_PLAN_SHA256,
            "hash_matches_frozen": plan_hash == FROZEN_PLAN_SHA256,
            "frozen_before_case_read": True,
        },
        "inputs": input_evidence,
        "frozen_rule": {
            "norm": (
                "NFKC -> casefold -> Unicode/ASCII punctuation and underscore to space -> "
                "whitespace collapse -> strip ASCII spaces"
            ),
            "dev_split": (
                "SHA-256 of UTF-8 injection id interpreted big-endian; dev iff mod 10 < 5"
            ),
            "binding": (
                "direct canonical target match, otherwise unique minimum Levenshtein "
                "neighbour in source headers; ties are U"
            ),
            "value_invariance": (
                "UTF-8 bytes of JSON-serialized target-column value lists must be identical"
            ),
            "labels": {
                LABEL_E: "canonical correspondence preserved and value-invariant",
                LABEL_H: "unique identity binds elsewhere or cannot consume target values",
                LABEL_U: (
                    "source/provenance/collision/empty/value/tie evidence is insufficient"
                ),
            },
        },
        "frozen_rule_text": PLAN_PATH.read_text(encoding="utf-8"),
        "counts": {
            "total_injections": len(entries),
            "dev_cases": len(rows),
            "held_out_cases": len(held_out_ids),
            "label_counts": label_counts,
            "checker_counts": checker_counts,
            "contingency": contingency,
            "value_invariant_count": sum(
                1 for row in rows if row.get("value_invariant") is True
            ),
        },
        "calls": CALL_COUNTS,
        "self_check": self_check_pass,
        "self_checks": self_checks,
        "per_case_rows": rows,
    }

    u_rate_text = "null" if u_rate is None else f"{u_rate:.6f}"
    co_miss_text = "null" if co_miss_rate is None else f"{co_miss_rate:.6f}"
    co_alarm_text = "null" if co_alarm_rate is None else f"{co_alarm_rate:.6f}"
    if status == "GOLD_NOT_ESTABLISHED":
        feasibility = (
            "**Independent gold NOT established on this dev corpus** under the frozen "
            "contract; the U rate exceeds 30%."
        )
    elif status == "SELF_CHECK_PASS":
        feasibility = (
            "**Independent gold is usable on this frozen dev split** under the frozen "
            "contract; this is a feasibility result, not a population estimate."
        )
    else:
        feasibility = f"**No feasibility conclusion:** `{status}`."

    u_rows = [row for row in rows if row["label"] == LABEL_U]
    summary = f"""# Paper E Layer-1 Independent Gold Summary v1

**Status:** `{status}`  
**Feasibility verdict:** {feasibility}

## Evidence

- **Primary:** {len(rows)} dev cases were labelled independently of the audited greedy matcher and semantic judge; `plan_sha256={plan_hash}`.
- **Primary contingency (checker verdict × independent gold):**

{markdown_contingency(contingency)}

- **Exploratory rates:** `P(H | blind)={co_miss_text}`, `P(E | visible)={co_alarm_text}`, `U rate={u_rate_text}`.
- **Engineering:** `calls={CALL_COUNTS["total_calls"]}`; value-invariance was recomputed bytewise for `{sum(1 for row in rows if row.get("value_invariant") is True)}/{len(rows)}` dev cases; input, plan, label, join, and contingency self-checks: `{"PASS" if self_check_pass else "FAIL"}`.

## Boundary

The result is a descriptive feasibility/dev contingency only. It is not a population rate, does
not establish an OCR conclusion, and does not by itself claim a harmful blind spot. Checker
verdicts were comparison targets only and were not used to assign any `E`, `H`, or `U` label.

## Human Adjudication

`{len(u_rows)}` dev case(s) remain `INSUFFICIENT_EVIDENCE` and must not be auto-labelled:

"""
    if u_rows:
        for row in u_rows:
            summary += (
                f"- `{row['injection_id']}` — uid={row['uid']}, col={row['col']}, "
                f"reasons={', '.join(row['reasons'])}\n"
            )
    else:
        summary += "- None.\n"

    write_json(RESULTS_PATH, results)
    write_json(RECEIPT_PATH, receipt)
    write_text(SUMMARY_PATH, summary)
    print(
        json.dumps(
            {
                "status": status,
                "dev_cases": len(rows),
                "labels": label_counts,
                "u_rate": u_rate,
                "contingency": contingency,
                "self_check": self_check_pass,
                "calls": CALL_COUNTS["total_calls"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status in {"SELF_CHECK_PASS", "GOLD_NOT_ESTABLISHED"} else 5


if __name__ == "__main__":
    sys.exit(main())
