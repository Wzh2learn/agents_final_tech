#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


TASK_ID = "tatqa-candidate-b-qualification-a-20261019"
PACKAGE_SCHEMA = "tatqa_candidate_b_qualification_v1"
SELECTION_RULE_ID = "candidate_b_source_structure_only_v1"
SELECTION_SEED = "tatqa-candidate-b-qualification-a-20261019-reserve-order-v1"
CLASSIFICATIONS = {
    "REFERENCE_VALID_DETERMINISTIC",
    "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION",
    "UNSCORABLE_FOR_REFERENCE",
    "EXCLUDE_SOURCE_OR_EXPOSURE",
}
EXPOSURE_MAP = {
    "STRUCTURAL_SCAN_ONLY": "ID_SCAN_ONLY",
    "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE": "PROGRAMMATIC_ONLY",
    "METHOD_DEVELOPMENT_OR_DIAGNOSTIC": "DESIGN_OR_DIAGNOSTIC",
    "MODEL_OR_FEEDBACK_EXPOSURE": "MODEL_OR_FEEDBACK_EXPOSED",
    "EXPOSURE_UNKNOWN": "EXPOSURE_UNKNOWN",
}
FORBIDDEN_ACTOR_KEYS = {
    "hidden",
    "hidden_reference",
    "reference",
    "coordinates",
    "row_index",
    "early_period_index",
    "late_period_index",
    "source_values",
    "reference_answer",
    "expected_calculator_expression",
}


class ReferenceCheckError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_record(path: Path, root: Path) -> dict[str, Any]:
    try:
        display_path = path.relative_to(root).as_posix()
    except ValueError:
        display_path = str(path)
    return {
        "path": display_path,
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_path(path) if path.is_file() else None,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def normalized_label(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"-", "–", "—", "n/a", "na", "nm", "n/m", "x"}:
        return None
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    if text.startswith(("−", "-")):
        negative = True
        text = text[1:].strip()
    if text.startswith(("$", "€", "£")):
        text = text[1:].strip()
    text = text.replace(",", "").replace("−", "-")
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*%?", text)
    if not match:
        return None
    try:
        result = Decimal(match.group(1))
    except InvalidOperation:
        return None
    return -result if negative else result


def decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def cell_unit(value: Any) -> str:
    return "percent" if "%" in str(value).strip() else "plain"


def cell_currency(value: Any) -> str | None:
    text = str(value).strip()
    if "USD" in text.upper() or "$" in text:
        return "USD"
    if "EUR" in text.upper() or "€" in text:
        return "EUR"
    if "GBP" in text.upper() or "£" in text:
        return "GBP"
    return None


def infer_unit_context(header_cell: Any) -> dict[str, str] | None:
    text = normalized_label(header_cell).lower().replace("’", "'")
    if text.count("$") > 1 or "except" in text:
        return None
    if "%" in text or "percent" in text:
        if "usd" in text or "eur" in text or "gbp" in text or "$" in text:
            return None
        return {
            "unit": "percentage_point",
            "scale": "one",
            "multiplier": "1",
        }
    currency_codes = []
    if "usd" in text or "$" in text or "dollar" in text:
        currency_codes.append("USD")
    if "eur" in text or "€" in text or "euro" in text:
        currency_codes.append("EUR")
    if "gbp" in text or "£" in text or "pound" in text:
        currency_codes.append("GBP")
    if len(currency_codes) != 1:
        return None
    scale_matches = []
    for scale, pattern in (
        ("million", r"(?:\bmil(?:lion)?s?\b|\bm\b)"),
        ("billion", r"(?:\bbil(?:lion)?s?\b|\bb\b)"),
        ("thousand", r"(?:\bthousand(?:s)?\b|\bk\b|'000|’000)"),
    ):
        if re.search(pattern, text):
            scale_matches.append(scale)
    if len(scale_matches) != 1:
        return None
    multiplier = {
        "million": "1000000",
        "billion": "1000000000",
        "thousand": "1000",
    }[scale_matches[0]]
    return {
        "unit": currency_codes[0],
        "scale": scale_matches[0],
        "multiplier": multiplier,
    }


def period_columns(table: list[list[Any]]) -> tuple[list[tuple[int, str, int]], str | None]:
    if not table or not isinstance(table[0], list):
        return [], "MISSING_HEADER"
    periods: list[tuple[int, str, int]] = []
    years: dict[int, list[int]] = {}
    for column, value in enumerate(table[0][1:], start=1):
        label = normalized_label(value)
        matches = re.findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", label)
        if len(matches) != 1:
            continue
        year = int(matches[0])
        years.setdefault(year, []).append(column)
        periods.append((column, label, year))
    ambiguous = {year for year, columns in years.items() if len(columns) != 1}
    clean = [period for period in periods if period[2] not in ambiguous]
    clean.sort(key=lambda item: (item[2], item[0]))
    if len({item[2] for item in clean}) < 2:
        return clean, "INSUFFICIENT_STRUCTURAL_PERIODS"
    return clean, None


def structural_signature(record: dict[str, Any]) -> dict[str, Any]:
    table = record["table"]
    if (
        not isinstance(table, list)
        or len(table) < 3
        or not table[0]
        or len(table[0]) < 3
    ):
        return {"eligible": False, "reason": "TABLE_TOO_SMALL"}
    unit = infer_unit_context(table[0][0])
    if unit is None:
        return {"eligible": False, "reason": "AMBIGUOUS_OR_UNSUPPORTED_UNIT"}
    periods, error = period_columns(table)
    if error:
        return {"eligible": False, "reason": error}
    selected_periods = [periods[-2], periods[-1]]
    period_columns_used = [item[0] for item in selected_periods]
    row_labels = [
        normalized_label(row[0])
        if isinstance(row, list) and row and str(row[0]).strip()
        else ""
        for row in table[1:]
    ]
    duplicate_labels = {
        label
        for label, count in Counter(row_labels).items()
        if label and count > 1
    }
    eligible_rows = []
    for offset, row_label in enumerate(row_labels, start=1):
        row = table[offset]
        if (
            not row_label
            or row_label in duplicate_labels
            or len(row) <= max(period_columns_used)
        ):
            continue
        cells = [row[column] for column in period_columns_used]
        kinds = [cell_unit(cell) for cell in cells]
        values = [parse_decimal(cell) for cell in cells]
        if kinds[0] != kinds[1] or any(value is None for value in values):
            continue
        expected_kind = "percent" if unit["unit"] == "percentage_point" else "plain"
        if kinds[0] != expected_kind:
            continue
        currencies = [cell_currency(cell) for cell in cells if cell_currency(cell)]
        if unit["unit"] != "percentage_point":
            if len(set(currencies)) > 1:
                continue
            if currencies and currencies[0] != unit["unit"]:
                continue
        eligible_rows.append(offset)
    if len(eligible_rows) < 2:
        return {
            "eligible": False,
            "reason": "INSUFFICIENT_NUMERIC_ROWS",
            "unit": unit,
            "periods": periods,
            "eligible_rows": eligible_rows,
        }
    return {
        "eligible": True,
        "reason": "ELIGIBLE",
        "unit": unit,
        "periods": periods,
        "selected_periods": selected_periods,
        "eligible_rows": eligible_rows,
        "selected_rows": eligible_rows[:2],
        "duplicate_row_labels": sorted(duplicate_labels),
        "period_pair": [period[2] for period in selected_periods],
    }


def root_path() -> Path:
    return Path(__file__).resolve().parents[2]


def load_raw_records(root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for raw_split in ("train", "dev"):
        path = root / f"data/research/tatqa_raw_2026/tatqa_dataset_{raw_split}.json"
        data = read_json(path)
        for source_index, item in enumerate(data):
            table_payload = item["table"]
            uid = table_payload["uid"]
            if uid in records:
                raise ReferenceCheckError(f"DUPLICATE_RAW_UID:{uid}")
            records[uid] = {
                "uid": uid,
                "raw_split": raw_split,
                "source_index": source_index,
                "table": table_payload["table"],
                "record": item,
            }
    return records


def verify_reused_evidence(root: Path) -> dict[str, Any]:
    paths = [
        "research/paper_e_contribution_reassessment_v1/REUSE_TASK_REDESIGN.md",
        "research/paper_e_contribution_reassessment_v1/NEXT_DEVELOPMENT_RUN_CARD_DRAFT.md",
        "data/research/tatqa_raw_2026/tatqa_dataset_train.json",
        "data/research/tatqa_raw_2026/tatqa_dataset_dev.json",
        "data/research/tatqa_raw_2026/FETCH_RECEIPT.txt",
        "data/research/tatqa_raw_2026/FETCH_RECEIPT.sha256",
        "data/research/tatqa_wp0_2026/origin_manifest.json",
        "data/research/tatqa_wp0_2026/candidate_items_v2.json",
        "data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json",
        "research/tatqa_wp0_2026/history_collection_offline_v1/SOURCE_CLUSTERS.json",
        "research/tatqa_wp0_2026/history_collection_offline_v1/SPLIT_PROPOSAL.json",
        "research/tatqa_wp0_2026/history_collection_offline_v1/EXPOSURE_AND_SPLIT_AUDIT.json",
        "research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_SPLIT_DELTA_REAUDIT.md",
        "research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_PROGRAM_EXPOSURE_REVIEW.md",
        "research/tatqa_wp0_2026/WP2_SPLIT_DRYRUN_RECEIPT.json",
        "research/tatqa_wp0_2026/history_collection_execution_v1/TASK_REFERENCE_MANIFEST.json",
        "research/tatqa_wp0_2026/history_collection_execution_v1/PRE_COLLECTION_EXECUTION_BUNDLE.json",
        "research/tatqa_wp0_2026/history_collection_execution_v1/MANIFEST_COMPARISON.json",
        "research/tatqa_wp0_2026/history_collection_execution_v1/RUN_DISPATCH_RECEIPT.json",
    ]
    artifacts = [artifact_record(root / relative, root) for relative in paths]
    if not all(item["exists"] for item in artifacts):
        raise ReferenceCheckError("REUSED_ARTIFACT_MISSING")
    train = root / paths[2]
    dev = root / paths[3]
    fetch_text = (root / paths[4]).read_text(encoding="utf-8")
    expected_fetch = {
        "train": sha256_path(train),
        "dev": sha256_path(dev),
    }
    for split, digest in expected_fetch.items():
        if not re.search(
            rf"(?m)^{re.escape(digest)}\s+tatqa_dataset_{split}\.json$",
            fetch_text,
        ):
            raise ReferenceCheckError(f"FETCH_RECEIPT_MISMATCH:{split}")
    audit = read_json(root / paths[11])
    if audit["source_identity"]["train_sha256"] != expected_fetch["train"]:
        raise ReferenceCheckError("AUDIT_TRAIN_HASH_MISMATCH")
    if audit["source_identity"]["dev_sha256"] != expected_fetch["dev"]:
        raise ReferenceCheckError("AUDIT_DEV_HASH_MISMATCH")
    if (
        audit["source_identity"]["candidate_items_sha256"]
        != sha256_path(root / paths[7])
    ):
        raise ReferenceCheckError("AUDIT_CANDIDATE_ITEMS_HASH_MISMATCH")
    task_manifest = read_json(root / paths[15])
    comparison = read_json(root / paths[17])
    if sha256_path(root / paths[15]) != comparison["current_manifest_sha256"]:
        raise ReferenceCheckError("TASK_MANIFEST_COMPARISON_MISMATCH")
    if not comparison["byte_identical"]:
        raise ReferenceCheckError("TASK_MANIFEST_NOT_BYTE_IDENTICAL")
    return {
        "artifacts": artifacts,
        "raw_hashes_match_audit": True,
        "raw_hashes_match_fetch_receipt": True,
        "candidate_items_hash_matches_audit": True,
        "history_task_manifest_counts": task_manifest["counts"],
        "referenced_candidate_items_exists": (
            root / "data/research/tatqa_wp0_2026/candidate_items_v2.json"
        ).is_file(),
        "referenced_candidate_items_expected_sha256": audit["source_identity"][
            "candidate_items_sha256"
        ],
    }


def load_split_universe(root: Path, raw_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_clusters = read_json(
        root / "research/tatqa_wp0_2026/history_collection_offline_v1/SOURCE_CLUSTERS.json"
    )
    split_proposal = read_json(
        root / "research/tatqa_wp0_2026/history_collection_offline_v1/SPLIT_PROPOSAL.json"
    )
    exposure_audit = read_json(
        root / "research/tatqa_wp0_2026/history_collection_offline_v1/EXPOSURE_AND_SPLIT_AUDIT.json"
    )
    if source_clusters["record_count"] != len(raw_records):
        raise ReferenceCheckError("SOURCE_RECORD_COUNT_MISMATCH")
    if source_clusters["cluster_count"] != len(source_clusters["clusters"]):
        raise ReferenceCheckError("SOURCE_CLUSTER_COUNT_MISMATCH")
    cluster_by_id = {row["cluster_id"]: row for row in source_clusters["clusters"]}
    if len(cluster_by_id) != len(source_clusters["clusters"]):
        raise ReferenceCheckError("DUPLICATE_CLUSTER_ID")
    member_owners: dict[str, str] = {}
    for cluster in source_clusters["clusters"]:
        for uid in cluster["members"]:
            if uid not in raw_records:
                raise ReferenceCheckError(f"UNKNOWN_CLUSTER_MEMBER:{uid}")
            if uid in member_owners:
                raise ReferenceCheckError(f"DUPLICATE_CLUSTER_MEMBER:{uid}")
            member_owners[uid] = cluster["cluster_id"]
    role_by_cluster: dict[str, str] = {}
    split_rows: dict[str, dict[str, Any]] = {}
    for role in (
        "development",
        "history",
        "future_test",
        "reserve",
        "excluded_pending_review",
    ):
        for row in split_proposal[role]:
            cluster_id = row["cluster_id"]
            if cluster_id in role_by_cluster:
                raise ReferenceCheckError(f"ROLE_OVERLAP:{cluster_id}")
            if cluster_id not in cluster_by_id:
                raise ReferenceCheckError(f"UNKNOWN_SPLIT_CLUSTER:{cluster_id}")
            role_by_cluster[cluster_id] = role
            split_rows[cluster_id] = row
    audit_rows = {row["cluster_id"]: row for row in exposure_audit["cluster_rows"]}
    if len(audit_rows) != len(source_clusters["clusters"]):
        raise ReferenceCheckError("EXPOSURE_CLUSTER_ROW_COUNT_MISMATCH")
    return {
        "source_clusters": source_clusters,
        "split_proposal": split_proposal,
        "exposure_audit": exposure_audit,
        "cluster_by_id": cluster_by_id,
        "member_owners": member_owners,
        "role_by_cluster": role_by_cluster,
        "split_rows": split_rows,
        "audit_rows": audit_rows,
    }


def make_reference_item(
    task_id: str,
    partition: str,
    cluster_id: str,
    raw_record: dict[str, Any],
    signature: dict[str, Any],
    row_index: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    table = raw_record["table"]
    early_column, early_label, early_year = signature["selected_periods"][0]
    late_column, late_label, late_year = signature["selected_periods"][1]
    early_display = table[row_index][early_column]
    late_display = table[row_index][late_column]
    early_value = parse_decimal(early_display)
    late_value = parse_decimal(late_display)
    if early_value is None or late_value is None:
        raise ReferenceCheckError(f"NON_NUMERIC_SELECTED_CELL:{task_id}")
    reference = late_value - early_value
    unit = dict(signature["unit"])
    expression = (
        f"calc(late={decimal_text(late_value)}, "
        f"early={decimal_text(early_value)}, "
        f"operation=late_minus_early, "
        f"unit={unit['unit']}, scale={unit['scale']})"
    )
    actor_task = {
        "schema": "tatqa_candidate_b_actor_task_v1",
        "task_id": task_id,
        "question": (
            f"How did {normalized_label(table[row_index][0])} change "
            f"from {early_label} to {late_label}?"
        ),
        "table": table,
        "instructions": (
            "Select the correct row and the two named period cells, determine "
            "the applicable unit and scale, and calculate the change using "
            "the displayed table values."
        ),
    }
    hidden = {
        "schema": "tatqa_candidate_b_hidden_reference_v1",
        "task_id": task_id,
        "classification": "REFERENCE_VALID_DETERMINISTIC",
        "partition": partition,
        "source_cluster_id": cluster_id,
        "source_uid": raw_record["uid"],
        "raw_split": raw_record["raw_split"],
        "source_record_index": raw_record["source_index"],
        "frozen_table_sha256": sha256_bytes(canonical_bytes(table)),
        "coordinates": {
            "row_index": row_index,
            "early_period_index": early_column,
            "late_period_index": late_column,
        },
        "canonical_labels": {
            "row": normalized_label(table[row_index][0]),
            "early_period": early_label,
            "late_period": late_label,
            "early_year": early_year,
            "late_year": late_year,
        },
        "source_values": {
            "early": float(early_value),
            "late": float(late_value),
            "early_display": early_display,
            "late_display": late_display,
        },
        "sign_convention": "late_minus_early",
        "source_unit": unit,
        "target_unit": unit,
        "deterministic_reference": {
            "late_minus_early": float(reference),
            "decimal": decimal_text(reference),
            "display": decimal_text(reference),
            "unit": unit["unit"],
            "scale": unit["scale"],
        },
        "expected_calculator_expression": expression,
        "distractors": {
            "row_indices": [
                row
                for row in range(1, len(table))
                if row != row_index and normalized_label(table[row][0])
            ],
            "period_indices": [item[0] for item in signature["periods"]],
        },
    }
    return actor_task, hidden


def build_core(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    evidence = verify_reused_evidence(root)
    raw_records = load_raw_records(root)
    universe = load_split_universe(root, raw_records)
    cluster_rows = []
    signatures: dict[str, dict[str, Any]] = {}
    old_task_roles = {"development", "history", "future_test", "excluded_pending_review"}
    for cluster_id in sorted(universe["cluster_by_id"]):
        role = universe["role_by_cluster"].get(cluster_id, "UNASSIGNED")
        split_row = universe["split_rows"].get(cluster_id)
        audit_row = universe["audit_rows"][cluster_id]
        raw_payload = audit_row["exposure"]
        raw_category = (
            raw_payload["category"]
            if isinstance(raw_payload, dict)
            else raw_payload
        )
        effective_category = (
            split_row["effective_exposure_category"]
            if split_row
            else raw_category
        )
        evidence_class = EXPOSURE_MAP.get(effective_category, "EXPOSURE_UNKNOWN")
        member_signatures = []
        for uid in sorted(universe["cluster_by_id"][cluster_id]["members"]):
            signature = structural_signature(raw_records[uid])
            if signature["eligible"]:
                member_signatures.append((uid, signature))
        structural_status = "NOT_SCANNED"
        structural_reason = None
        if role == "reserve":
            if len(member_signatures) == 1:
                signatures[cluster_id] = {
                    "uid": member_signatures[0][0],
                    "signature": member_signatures[0][1],
                }
                structural_status = "STRUCTURALLY_ELIGIBLE"
            elif len(member_signatures) > 1:
                structural_status = "EXCLUDED"
                structural_reason = "AMBIGUOUS_CLUSTER_SOURCE"
            else:
                structural_status = "EXCLUDED"
                structural_reason = "NO_STRUCTURALLY_ELIGIBLE_MEMBER"
        elif role in old_task_roles:
            structural_status = "EXCLUDED"
            structural_reason = "PRESERVE_OLD_TASK_OR_HISTORY_ROLE"
        eligible_new_pool = (
            role == "reserve"
            and evidence_class == "PROGRAMMATIC_ONLY"
            and structural_status == "STRUCTURALLY_ELIGIBLE"
        )
        cluster_rows.append(
            {
                "cluster_id": cluster_id,
                "members": universe["cluster_by_id"][cluster_id]["members"],
                "existing_role": role,
                "raw_exposure_category": raw_category,
                "effective_exposure_category": effective_category,
                "evidence_class": evidence_class,
                "structural_status": structural_status,
                "structural_reason": structural_reason,
                "eligible_new_candidate_pool": eligible_new_pool,
            }
        )
    eligible_ids = [
        row["cluster_id"]
        for row in cluster_rows
        if row["eligible_new_candidate_pool"]
    ]
    eligible_ids.sort(
        key=lambda cluster_id: sha256_bytes(
            f"{SELECTION_SEED}:{cluster_id}".encode("utf-8")
        )
    )
    if len(eligible_ids) >= 16:
        development_ids = eligible_ids[:8]
        future_ids = eligible_ids[8:16]
    else:
        development_ids = eligible_ids[:8]
        future_ids = eligible_ids[8:16]
    partition_ids = [
        *((cluster_id, "development") for cluster_id in development_ids),
        *((cluster_id, "future_validation") for cluster_id in future_ids),
    ]
    actor_tasks = []
    hidden_references = []
    for ordinal, (cluster_id, partition) in enumerate(partition_ids, start=1):
        selected = signatures[cluster_id]
        raw_record = raw_records[selected["uid"]]
        prefix = "DEV" if partition == "development" else "FVAL"
        task_id = f"CB_{prefix}_{ordinal:02d}_{sha256_bytes(cluster_id.encode())[:8].upper()}"
        for task_number, row_index in enumerate(
            selected["signature"]["selected_rows"], start=1
        ):
            item_task_id = f"{task_id}_T{task_number}"
            actor_task, hidden = make_reference_item(
                item_task_id,
                partition,
                cluster_id,
                raw_record,
                selected["signature"],
                row_index,
            )
            actor_tasks.append(actor_task)
            hidden_references.append(hidden)
    role_counts = Counter(universe["role_by_cluster"].values())
    exposure_counts = Counter(row["evidence_class"] for row in cluster_rows)
    status = (
        "PANEL_COUNTS_AVAILABLE"
        if len(development_ids) == 8 and len(future_ids) == 8
        else "INSUFFICIENT_PANEL"
    )
    source_exposure = {
        "schema": PACKAGE_SCHEMA,
        "task_id": TASK_ID,
        "status": status,
        "source_identity": {
            "train_sha256": sha256_path(
                root / "data/research/tatqa_raw_2026/tatqa_dataset_train.json"
            ),
            "dev_sha256": sha256_path(
                root / "data/research/tatqa_raw_2026/tatqa_dataset_dev.json"
            ),
            "raw_hashes_match_existing_audit": evidence[
                "raw_hashes_match_audit"
            ],
            "raw_hashes_match_fetch_receipt": evidence[
                "raw_hashes_match_fetch_receipt"
            ],
        },
        "report_identity": {
            "status": "UNRESOLVED",
            "report_disjointness_claimed": False,
            "reason": (
                "Raw records have no report ID; source-association clusters "
                "cannot establish report-level independence."
            ),
        },
        "exposure_evidence_model": {
            "ID_SCAN_ONLY": ["STRUCTURAL_SCAN_ONLY"],
            "PROGRAMMATIC_ONLY": [
                "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE"
            ],
            "DESIGN_OR_DIAGNOSTIC": [
                "METHOD_DEVELOPMENT_OR_DIAGNOSTIC"
            ],
            "MODEL_OR_FEEDBACK_EXPOSED": [
                "MODEL_OR_FEEDBACK_EXPOSURE"
            ],
            "EXPOSURE_UNKNOWN": ["EXPOSURE_UNKNOWN"],
        },
        "counts": {
            "raw_records": len(raw_records),
            "source_clusters": len(cluster_rows),
            "existing_roles": dict(sorted(role_counts.items())),
            "exposure_classes": dict(sorted(exposure_counts.items())),
            "reserve_structurally_eligible": sum(
                row["eligible_new_candidate_pool"] for row in cluster_rows
            ),
            "development_clusters_selected": len(development_ids),
            "future_validation_clusters_selected": len(future_ids),
        },
        "selection": {
            "rule_id": SELECTION_RULE_ID,
            "seed": SELECTION_SEED,
            "label_blind": True,
            "source_structure_only": True,
            "old_designated_roles_excluded": sorted(old_task_roles),
            "eligible_cluster_order_sha256": eligible_ids,
            "development_cluster_ids": development_ids,
            "future_validation_cluster_ids": future_ids,
        },
        "shortfall": {
            "development": max(0, 8 - len(development_ids)),
            "future_validation": max(0, 8 - len(future_ids)),
        },
        "input_verification": {
            "task_card": artifact_record(
                Path("/tmp/tatqa_candidate_b_qualification_task_card.md"), root
            ),
            "named_inputs": [
                artifact_record(
                    root
                    / "research/paper_e_contribution_reassessment_v1/"
                    "REUSE_TASK_REDESIGN.md",
                    root,
                ),
                artifact_record(
                    root
                    / "research/paper_e_contribution_reassessment_v1/"
                    "NEXT_DEVELOPMENT_RUN_CARD_DRAFT.md",
                    root,
                ),
            ],
        },
        "reused_evidence": evidence,
        "clusters": cluster_rows,
    }
    tasks_manifest = {
        "schema": PACKAGE_SCHEMA,
        "task_id": TASK_ID,
        "status": status,
        "selection_rule_id": SELECTION_RULE_ID,
        "actor_facing": True,
        "task_ids": [task["task_id"] for task in actor_tasks],
        "tasks": actor_tasks,
    }
    hidden_manifest = {
        "schema": PACKAGE_SCHEMA,
        "task_id": TASK_ID,
        "status": status,
        "selection_rule_id": SELECTION_RULE_ID,
        "selection_seed": SELECTION_SEED,
        "rule": {
            "label_blind": True,
            "source_structure_only": True,
            "eligibility": [
                "reserve role only; all old development/history/future-test roles are excluded",
                "effective exposure is PROGRAMMATIC_ONLY",
                "exactly one cluster member has a structurally eligible frozen table",
                "same table supplies all candidate and distractor rows",
                "latest two unambiguous year-labelled period columns are identifiable",
                "at least two body rows have unique labels and numeric same-unit cells in both periods",
                "tasks use the first two eligible row coordinates; no model output, expected error, or observed failure is read",
            ],
            "order": "ascending sha256(seed:cluster_id)",
            "allocation": "first eight development; next eight future validation",
            "sign_convention": "late - early",
        },
        "counts": {
            "development_clusters": len(development_ids),
            "future_validation_clusters": len(future_ids),
            "development_tasks": sum(
                item["partition"] == "development" for item in hidden_references
            ),
            "future_validation_tasks": sum(
                item["partition"] == "future_validation"
                for item in hidden_references
            ),
            "reference_valid": sum(
                item["classification"] == "REFERENCE_VALID_DETERMINISTIC"
                for item in hidden_references
            ),
            "requires_human_semantic_adjudication": sum(
                item["classification"]
                == "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION"
                for item in hidden_references
            ),
            "unscorable_for_reference": sum(
                item["classification"] == "UNSCORABLE_FOR_REFERENCE"
                for item in hidden_references
            ),
            "excluded": 0,
        },
        "references": hidden_references,
    }
    return source_exposure, tasks_manifest, hidden_manifest


def assert_no_hidden_leakage(actor_task: dict[str, Any]) -> None:
    stack = [actor_task]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                if key in FORBIDDEN_ACTOR_KEYS:
                    raise ReferenceCheckError("HIDDEN_FIELD_LEAKAGE")
                stack.append(child)
        elif isinstance(value, list):
            stack.extend(value)
    serialized = canonical_bytes(actor_task).decode("utf-8")
    for forbidden in (
        "late_minus_early",
        "expected_calculator_expression",
        '"source_cluster_id"',
        '"row_index"',
    ):
        if forbidden in serialized:
            raise ReferenceCheckError("HIDDEN_FIELD_LEAKAGE")


def verify_hidden_reference(
    table: list[list[Any]],
    hidden: dict[str, Any],
) -> None:
    coordinates = hidden.get("coordinates")
    if not isinstance(coordinates, dict):
        raise ReferenceCheckError("MISSING_COORDINATES")
    required = {"row_index", "early_period_index", "late_period_index"}
    if set(coordinates) != required:
        raise ReferenceCheckError("AMBIGUOUS_COORDINATES")
    row_index = coordinates["row_index"]
    early_column = coordinates["early_period_index"]
    late_column = coordinates["late_period_index"]
    if not all(isinstance(value, int) for value in coordinates.values()):
        raise ReferenceCheckError("NONINTEGER_COORDINATE")
    if row_index <= 0 or row_index >= len(table):
        raise ReferenceCheckError("WRONG_ROW")
    if early_column <= 0 or late_column <= 0:
        raise ReferenceCheckError("WRONG_PERIOD")
    if early_column == late_column or max(early_column, late_column) >= len(
        table[0]
    ):
        raise ReferenceCheckError("WRONG_PERIOD")
    if sha256_bytes(canonical_bytes(table)) != hidden["frozen_table_sha256"]:
        raise ReferenceCheckError("FROZEN_TABLE_HASH_MISMATCH")
    canonical_row = normalized_label(table[row_index][0])
    row_labels = [
        normalized_label(row[0])
        if isinstance(row, list) and row and str(row[0]).strip()
        else ""
        for row in table[1:]
    ]
    if canonical_row != hidden["canonical_labels"]["row"]:
        raise ReferenceCheckError("WRONG_ROW")
    if canonical_row in {
        label
        for label, count in Counter(row_labels).items()
        if label and count > 1
    }:
        raise ReferenceCheckError("AMBIGUOUS_ROW_LABEL")
    early_period = normalized_label(table[0][early_column])
    late_period = normalized_label(table[0][late_column])
    if (
        early_period != hidden["canonical_labels"]["early_period"]
        or late_period != hidden["canonical_labels"]["late_period"]
    ):
        raise ReferenceCheckError("WRONG_PERIOD")
    periods, period_error = period_columns(table)
    if period_error:
        raise ReferenceCheckError("AMBIGUOUS_PERIOD_LABEL")
    if (
        early_period == late_period
        or len({label for _, label, _ in periods}) != len(periods)
        or [(item[0], item[1]) for item in periods[-2:]]
        != [
            (early_column, early_period),
            (late_column, late_period),
        ]
    ):
        raise ReferenceCheckError("AMBIGUOUS_PERIOD_LABEL")
    inferred_unit = infer_unit_context(table[0][0])
    if inferred_unit != hidden["source_unit"] or inferred_unit != hidden[
        "target_unit"
    ]:
        raise ReferenceCheckError("INCONSISTENT_UNIT_OR_SCALE")
    early_cell = table[row_index][early_column]
    late_cell = table[row_index][late_column]
    if early_cell in (None, "") or late_cell in (None, ""):
        raise ReferenceCheckError("MISSING_CELL")
    early_value = parse_decimal(early_cell)
    late_value = parse_decimal(late_cell)
    if early_value is None or late_value is None:
        raise ReferenceCheckError("NON_NUMERIC_CELL")
    if cell_unit(early_cell) != cell_unit(late_cell):
        raise ReferenceCheckError("INCONSISTENT_CELL_UNIT")
    if hidden["sign_convention"] != "late_minus_early":
        raise ReferenceCheckError("REVERSED_SIGN")
    source_unit = hidden["source_unit"]
    target_unit = hidden["target_unit"]
    if source_unit != target_unit:
        raise ReferenceCheckError("INCONSISTENT_UNIT_OR_SCALE")
    expected_kind = (
        "percent" if source_unit["unit"] == "percentage_point" else "plain"
    )
    if cell_unit(early_cell) != expected_kind:
        raise ReferenceCheckError("INCONSISTENT_CELL_UNIT")
    stored_early = Decimal(str(hidden["source_values"]["early"]))
    stored_late = Decimal(str(hidden["source_values"]["late"]))
    if early_value != stored_early or late_value != stored_late:
        raise ReferenceCheckError("SOURCE_VALUE_MISMATCH")
    expected = late_value - early_value
    stored = Decimal(hidden["deterministic_reference"]["decimal"])
    if expected != stored:
        raise ReferenceCheckError("REFERENCE_RECOMPUTE_MISMATCH")


def decimal_from_submission(
    submission: dict[str, Any],
    key: str,
) -> Decimal | None:
    value = submission.get(key)
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ReferenceCheckError("NON_NUMERIC_SUBMISSION") from exc


def validate_submission(
    actor_task: dict[str, Any],
    hidden: dict[str, Any],
    submission: dict[str, Any],
    table: list[list[Any]],
) -> dict[str, Any]:
    assert_no_hidden_leakage(actor_task)
    verify_hidden_reference(table, hidden)
    if submission.get("sign_convention") != "late_minus_early":
        raise ReferenceCheckError("REVERSED_SIGN")
    coordinates = hidden["coordinates"]
    if submission.get("row_index") != coordinates["row_index"]:
        raise ReferenceCheckError("WRONG_ROW")
    if (
        submission.get("early_period_index")
        != coordinates["early_period_index"]
        or submission.get("late_period_index")
        != coordinates["late_period_index"]
    ):
        raise ReferenceCheckError("WRONG_PERIOD")
    source_unit = hidden["source_unit"]
    target_unit = hidden["target_unit"]
    for key, expected in (
        ("source_unit", source_unit["unit"]),
        ("source_scale", source_unit["scale"]),
        ("target_unit", target_unit["unit"]),
        ("target_scale", target_unit["scale"]),
    ):
        if submission.get(key) != expected:
            raise ReferenceCheckError("WRONG_UNIT_OR_SCALE")
    selected_values = submission.get("selected_values")
    if not isinstance(selected_values, dict):
        raise ReferenceCheckError("MISSING_CELLS")
    for key in ("early", "late"):
        if key not in selected_values:
            raise ReferenceCheckError("MISSING_CELLS")
    early_value = decimal_from_submission(selected_values, "early")
    late_value = decimal_from_submission(selected_values, "late")
    if early_value is None or late_value is None:
        raise ReferenceCheckError("MISSING_CELLS")
    if early_value != Decimal(str(hidden["source_values"]["early"])) or late_value != Decimal(
        str(hidden["source_values"]["late"])
    ):
        raise ReferenceCheckError("SELECTED_CELL_MISMATCH")
    answer = decimal_from_submission(submission, "answer")
    tool_result = decimal_from_submission(submission, "tool_result")
    if answer is None or tool_result is None:
        raise ReferenceCheckError("MISSING_ANSWER_OR_TOOL_RESULT")
    expected = Decimal(hidden["deterministic_reference"]["decimal"])
    if answer != expected:
        if answer == -expected:
            raise ReferenceCheckError("REVERSED_SIGN")
        raise ReferenceCheckError("WRONG_REFERENCE_VALUE")
    if tool_result != expected:
        raise ReferenceCheckError("ANSWER_TOOL_INCONSISTENCY")
    if submission.get("tool_expression") != hidden[
        "expected_calculator_expression"
    ]:
        raise ReferenceCheckError("ANSWER_TOOL_INCONSISTENCY")
    return {
        "valid": True,
        "reference_decimal": decimal_text(expected),
        "classification": "REFERENCE_VALID_DETERMINISTIC",
    }


def correct_submission(hidden: dict[str, Any]) -> dict[str, Any]:
    unit = hidden["source_unit"]
    target_unit = hidden["target_unit"]
    return {
        "row_index": hidden["coordinates"]["row_index"],
        "early_period_index": hidden["coordinates"]["early_period_index"],
        "late_period_index": hidden["coordinates"]["late_period_index"],
        "sign_convention": hidden["sign_convention"],
        "source_unit": unit["unit"],
        "source_scale": unit["scale"],
        "target_unit": target_unit["unit"],
        "target_scale": target_unit["scale"],
        "selected_values": {
            "early": hidden["source_values"]["early"],
            "late": hidden["source_values"]["late"],
        },
        "answer": hidden["deterministic_reference"]["late_minus_early"],
        "tool_result": hidden["deterministic_reference"]["late_minus_early"],
        "tool_expression": hidden["expected_calculator_expression"],
    }


def verify_core(
    source_exposure: dict[str, Any],
    tasks_manifest: dict[str, Any],
    hidden_manifest: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    raw_records = load_raw_records(root)
    task_ids = [task["task_id"] for task in tasks_manifest["tasks"]]
    hidden_ids = [item["task_id"] for item in hidden_manifest["references"]]
    if task_ids != hidden_ids or len(task_ids) != len(set(task_ids)):
        raise ReferenceCheckError("TASK_REFERENCE_SET_MISMATCH")
    for actor_task, hidden in zip(
        tasks_manifest["tasks"], hidden_manifest["references"]
    ):
        assert_no_hidden_leakage(actor_task)
        verify_hidden_reference(
            raw_records[hidden["source_uid"]]["table"], hidden
        )
        validate_submission(
            actor_task,
            hidden,
            correct_submission(hidden),
            raw_records[hidden["source_uid"]]["table"],
        )
    counts = hidden_manifest["counts"]
    expected_counts = {
        "development_clusters": 8
        if source_exposure["counts"]["development_clusters_selected"] == 8
        else source_exposure["counts"]["development_clusters_selected"],
        "future_validation_clusters": 8
        if source_exposure["counts"]["future_validation_clusters_selected"] == 8
        else source_exposure["counts"]["future_validation_clusters_selected"],
        "development_tasks": counts["development_clusters"] * 2,
        "future_validation_tasks": counts["future_validation_clusters"] * 2,
        "reference_valid": len(task_ids),
        "requires_human_semantic_adjudication": 0,
        "unscorable_for_reference": 0,
        "excluded": 0,
    }
    if counts != expected_counts:
        raise ReferenceCheckError("COUNT_RECONCILIATION_MISMATCH")
    repeated_source, repeated_tasks, repeated_hidden = build_core(root)
    if canonical_bytes(
        (repeated_source, repeated_tasks, repeated_hidden)
    ) != canonical_bytes((source_exposure, tasks_manifest, hidden_manifest)):
        raise ReferenceCheckError("MANIFEST_NONDETERMINISM")
    return {
        "source_hash_checks": "PASS",
        "exposure_cluster_count_reconciliation": "PASS",
        "actor_hidden_separation": "PASS",
        "reference_recomputation": "PASS",
        "manifest_two_run_determinism": "PASS",
        "task_count": len(task_ids),
    }


def build_package(output_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    root = root_path()
    source_exposure, tasks_manifest, hidden_manifest = build_core(root)
    write_json(output_dir / "SOURCE_EXPOSURE_QUALIFICATION.json", source_exposure)
    write_json(output_dir / "CANDIDATE_B_TASKS_DRAFT.json", tasks_manifest)
    write_json(output_dir / "HIDDEN_REFERENCE_MANIFEST.json", hidden_manifest)
    (output_dir / "candidate_b_reference_checker_v1.py").write_bytes(
        Path(__file__).read_bytes()
    )
    tests_dir = output_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    source_tests = Path(__file__).with_name("tests") / "test_candidate_b_reference_checker_v1.py"
    (tests_dir / "test_candidate_b_reference_checker_v1.py").write_bytes(
        source_tests.read_bytes()
    )
    return source_exposure, tasks_manifest, hidden_manifest


def run_focused_tests(output_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(output_dir / "tests"),
        "-p",
        "test_candidate_b_reference_checker_v1.py",
        "-v",
    ]
    completed = subprocess.run(
        command,
        cwd=root_path(),
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode != 0:
        raise ReferenceCheckError(f"FOCUSED_TESTS_FAILED:{output[-2000:]}")
    matches = re.findall(r"Ran (\d+) tests?", output)
    test_count = int(matches[-1]) if matches else None
    if "OK" not in output.splitlines()[-3:]:
        raise ReferenceCheckError("FOCUSED_TEST_RESULT_UNVERIFIED")
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "test_count": test_count,
        "result": "PASS",
    }


def finalize_package(output_dir: Path) -> dict[str, Any]:
    source_exposure, tasks_manifest, hidden_manifest = build_package(output_dir)
    test_result = run_focused_tests(output_dir)
    checks = verify_core(
        source_exposure, tasks_manifest, hidden_manifest, root_path()
    )
    named_missing = [
        item["path"]
        for item in source_exposure["input_verification"]["named_inputs"]
        if not item["exists"]
    ]
    blockers = [
        f"MISSING_REQUIRED_INPUT:{path}" for path in named_missing
    ]
    if not source_exposure["reused_evidence"]["referenced_candidate_items_exists"]:
        blockers.append(
            "MISSING_REFERENCED_ARTIFACT:data/research/tatqa_wp0_2026/"
            "candidate_items_v2.json"
        )
    if source_exposure["shortfall"]["development"] or source_exposure[
        "shortfall"
    ]["future_validation"]:
        status = "CANDIDATE_B_INSUFFICIENT_HEADROOM_PANEL"
    elif blockers:
        status = "CANDIDATE_B_CONDITIONAL"
    else:
        status = "CANDIDATE_B_QUALIFIED_OFFLINE"
    counts = hidden_manifest["counts"]
    check_records = [
        {
            "name": "raw_source_hash_verification",
            "result": "PASS",
            "detail": (
                "Train and dev SHA-256 match EXPOSURE_AND_SPLIT_AUDIT.json "
                "and FETCH_RECEIPT.txt."
            ),
        },
        {
            "name": "cluster_exposure_count_reconciliation",
            "result": "PASS",
            "detail": (
                f"{source_exposure['counts']['source_clusters']} clusters; "
                f"{source_exposure['counts']['reserve_structurally_eligible']} "
                "reserve clusters satisfy frozen structure and exposure rules."
            ),
        },
        {
            "name": "actor_hidden_field_separation",
            "result": checks["actor_hidden_separation"],
            "detail": "All actor tasks pass recursive forbidden-key and hidden-marker checks.",
        },
        {
            "name": "negative_checker_tests",
            "result": "PASS",
            "detail": (
                "Focused tests cover wrong row, wrong period, reversed sign, "
                "wrong unit, missing cells, ambiguity, hidden leakage, and "
                "answer/tool inconsistency."
            ),
        },
        {
            "name": "deterministic_reference_recomputation",
            "result": checks["reference_recomputation"],
            "detail": "Every stored reference recomputes from frozen source cells.",
        },
        {
            "name": "two_run_manifest_determinism",
            "result": checks["manifest_two_run_determinism"],
            "detail": "Core source, task, and hidden payloads are byte-canonical identical.",
        },
        {
            "name": "focused_unittest",
            "result": "PASS",
            "detail": f"{test_result['test_count']} focused unittest cases passed.",
        },
        {
            "name": "human_adjudication_count",
            "result": "PASS",
            "detail": (
                "0 items require AI-to-human semantic conversion; all selected "
                "items are deterministic by frozen structure."
            ),
        },
    ]
    summary = {
        "schema": PACKAGE_SCHEMA,
        "task_id": TASK_ID,
        "status": status,
        "authorization": "ONLINE_NOT_AUTHORIZED",
        "counts": {
            "development_clusters": counts["development_clusters"],
            "future_clusters": counts["future_validation_clusters"],
            "development_tasks": counts["development_tasks"],
            "future_tasks": counts["future_validation_tasks"],
            "reference_valid": counts["reference_valid"],
            "human_adjudication_required": counts[
                "requires_human_semantic_adjudication"
            ],
            "unscorable": counts["unscorable_for_reference"],
            "excluded": counts["excluded"],
        },
        "classification_policy": {
            "REFERENCE_VALID_DETERMINISTIC": counts["reference_valid"],
            "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION": counts[
                "requires_human_semantic_adjudication"
            ],
            "UNSCORABLE_FOR_REFERENCE": counts["unscorable_for_reference"],
            "EXCLUDE_SOURCE_OR_EXPOSURE": counts["excluded"],
            "ai_can_convert_human_adjudication_to_gold": False,
        },
        "checks": check_records,
        "focused_test_result": test_result,
        "blockers": blockers,
        "shortfall": source_exposure["shortfall"],
        "cost": {
            "model_or_judge_calls": 0,
            "online_requests": 0,
            "actor_calls": 0,
            "database_calls": 0,
            "service_calls": 0,
            "pilot_calls": 0,
            "training_calls": 0,
        },
        "boundaries": {
            "model_outputs_inspected": False,
            "expected_errors_inspected": False,
            "current_b0_failures_inspected": False,
            "b0_r_c_h_runs": 0,
            "old_tasks_or_results_modified": False,
            "report_disjointness_claimed": False,
        },
    }
    write_json(output_dir / "QUALIFICATION_SUMMARY.json", summary)
    loop_return = "\n".join(
        [
            "# LOOP A RETURN — CANDIDATE B OFFLINE QUALIFICATION",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Status: `{status}`",
            "- Authorization: `ONLINE_NOT_AUTHORIZED`",
            f"- Development: `{counts['development_clusters']}` clusters / "
            f"`{counts['development_tasks']}` tasks",
            f"- Future validation: `{counts['future_validation_clusters']}` clusters / "
            f"`{counts['future_validation_tasks']}` tasks",
            f"- Deterministic references: `{counts['reference_valid']}`",
            "- Human adjudication required: `0`",
            "- Unscorable references: `0`",
            "- Excluded constructed items: `0`",
            "- Model or judge calls: `0`",
            "- Online requests: `0`",
            "",
            "## Verification",
            "",
            "- Raw train/dev SHA-256 matches the existing audit and fetch receipt.",
            "- Source-cluster and exposure counts reconcile against actual manifests.",
            "- Actor-facing and hidden manifests pass leakage separation.",
            "- Checker rejects wrong row, period, sign, unit, missing cells, ambiguity, leakage, and tool inconsistency.",
            "- References recompute deterministically from frozen source cells.",
            "- Two independent core builds are byte-canonical identical.",
            f"- Focused unittest: PASS ({test_result['test_count']} tests).",
            "",
            "## Blockers",
            "",
            *([f"- `{blocker}`" for blocker in blockers] or ["- None"]),
            "",
            "The package is not authorized for actor, model, judge, database, service, pilot, training, or production use.",
            "",
        ]
    )
    (output_dir / "LOOP_A_RETURN.md").write_text(loop_return, encoding="utf-8")
    artifact_names = [
        "SOURCE_EXPOSURE_QUALIFICATION.json",
        "CANDIDATE_B_TASKS_DRAFT.json",
        "HIDDEN_REFERENCE_MANIFEST.json",
        "candidate_b_reference_checker_v1.py",
        "tests/test_candidate_b_reference_checker_v1.py",
        "QUALIFICATION_SUMMARY.json",
        "LOOP_A_RETURN.md",
    ]
    package_artifacts = [
        artifact_record(output_dir / name, output_dir) for name in artifact_names
    ]
    selection_rule = hidden_manifest["rule"]
    receipt = {
        "schema": PACKAGE_SCHEMA,
        "task_id": TASK_ID,
        "status": status,
        "authorization": "ONLINE_NOT_AUTHORIZED",
        "task_card_and_design_inputs": source_exposure["reused_evidence"][
            "artifacts"
        ][:2],
        "raw_sources": source_exposure["reused_evidence"]["artifacts"][2:4],
        "reused_source_exposure_and_cluster_artifacts": source_exposure[
            "reused_evidence"
        ]["artifacts"][4:],
        "task_selection_rule": {
            "rule_id": SELECTION_RULE_ID,
            "sha256": sha256_bytes(canonical_bytes(selection_rule)),
            "payload": selection_rule,
        },
        "package_artifacts": package_artifacts,
        "counts": summary["counts"],
        "checks": summary["checks"],
        "blockers": blockers,
        "cost": summary["cost"],
    }
    write_json(output_dir / "candidate_b_qualification_receipt.json", receipt)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "finalize"))
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    if args.mode == "build":
        build_package(output_dir)
    else:
        finalize_package(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
