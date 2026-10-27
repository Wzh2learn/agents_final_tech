#!/usr/bin/env python3
"""Build a pre-output exposure receipt and freeze eight new table families."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT))

from research.adaptive_mechanism_20261027_v1.scoring_v2.scorer import (
    parse_decimal,
    parse_table,
)


ROOT = REPOSITORY_ROOT
OUT = Path(__file__).resolve().parent
DEV = Path(
    "/home/testuser/wzh/projects/agents_final_tech/data/research/"
    "tatqa_raw_2026/tatqa_dataset_dev.json"
)
TRAIN = DEV.with_name("tatqa_dataset_train.json")
EXPOSURE_UNION = (
    ROOT / "research/feedback_delivery_continuation_20261025_v1/"
    "EXPOSURE_UNION_SOURCES_V1.json"
)
EXPOSURE_AUDIT = (
    ROOT
    / "research/tatqa_wp0_2026/history_collection_offline_v1/"
    "EXPOSURE_AND_SPLIT_AUDIT.json"
)
PRIOR_PANEL = (
    ROOT
    / "research/adaptive_mechanism_20261027_v1/diagnostic_panel/"
    "DIAGNOSTIC_PANEL_PREREGISTRATION.json"
)
IDENTITY_KEYS = {
    "uid",
    "question_uid",
    "table_uid",
    "task_id",
    "source_task_id",
    "base_instance_id",
    "family_id",
    "report_uid",
    "source_key",
    "origin_uid",
}
LIST_IDENTITY_KEYS = {
    "selected_task_ids",
    "selected_table_uids",
    "task_ids",
    "source_keys",
    "panel_uids",
}
SEED = 20261027
PANEL_SIZE = 8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(value: str) -> str:
    return hashlib.sha256(f"{SEED}:{value}".encode("utf-8")).hexdigest()


def identities(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in IDENTITY_KEYS and item:
                text = str(item)
                found.add(text)
                found.add(text.split("::", 1)[0])
            elif key in LIST_IDENTITY_KEYS and isinstance(item, list):
                found.update(str(entry) for entry in item if entry)
            elif isinstance(item, dict) and key == "members" and isinstance(item, list):
                found.update(str(entry) for entry in item if entry)
            else:
                found.update(identities(item))
        members = value.get("members")
        if isinstance(members, list):
            found.update(str(entry) for entry in members if entry)
    elif isinstance(value, list):
        for item in value:
            found.update(identities(item))
    return found


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    value = json.loads(text)
    return value if isinstance(value, list) else [value]


def infer_role(path: Path) -> str:
    lowered = str(path).casefold()
    if "error_pool" in lowered or "error_repair" in lowered:
        return "error_pool"
    if "confirmation" in lowered:
        return "confirmation"
    if "train" in lowered:
        return "training"
    if "development" in lowered or "evaluation" in lowered or "diagnostic" in lowered:
        return "development_or_diagnostic"
    if "prior" in lowered or "panel" in lowered:
        return "prior_panel_or_uid_record"
    return "repository_identity_artifact"


def scan_repository() -> tuple[
    set[str],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    union: set[str] = set()
    sources: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    exposure_registers: list[dict[str, Any]] = []
    for path in sorted((ROOT / "research").rglob("*")):
        if not path.is_file() or path.suffix not in {".json", ".jsonl"}:
            continue
        if OUT in path.parents:
            continue
        # Exposure audit/qualification files are exclusion registers. Their
        # member IDs document scans or reservations and are not exposure by
        # themselves; their contents are hashed separately below.
        lowered_path = str(path).casefold()
        structural_markers = (
            "exposure",
            "source_clusters",
            "split_proposal",
            "qualification",
            "candidate_b",
        )
        if any(marker in lowered_path for marker in structural_markers):
            exposure_registers.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "role": "structural_or_exclusion_register_not_treated_as_exposure",
                    "sha256": sha256(path),
                }
            )
            continue
        try:
            rows = load_records(path)
            found = set()
            for row in rows:
                found.update(identities(row))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(
                {"path": str(path), "error": type(exc).__name__, "message": str(exc)}
            )
            continue
        if found:
            union.update(found)
            sources.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "role": infer_role(path),
                    "sha256": sha256(path),
                    "identity_count": len(found),
                }
            )
    return union, sources, errors, exposure_registers


def render_table(table: list[list[str]]) -> str:
    header = "columns: " + " | ".join(f"C{i}={cell}" for i, cell in enumerate(table[0]))
    rows = [header]
    for index, row in enumerate(table[1:], start=1):
        label = row[0] if row else ""
        body = " | ".join(f"C{i}={cell}" for i, cell in enumerate(row))
        rows.append(f"R{index} [{label}] {body}")
    return "\n".join(rows)


STOPWORDS = frozenset(
    "a an and are as at be between by did do for from has have how in is its "
    "many of on or that the their this to was were what within".split()
)


def question_words(question: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9.]+", question.casefold())
        if word not in STOPWORDS and len(word) > 1
    }


def table_bindings(
    record: dict[str, Any], question: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    table = parse_table(render_table(record["table"]["table"]))
    wanted = question_words(question["question"])
    scored: list[tuple[int, int]] = []
    for row_index, label in table.row_labels.items():
        numeric = any(
            parse_decimal(value) is not None
            for column_index, value in table.rows.get(row_index, {}).items()
            if column_index > 0
        )
        if not numeric:
            continue
        overlap = len(wanted & set(re.findall(r"[a-z0-9.]+", label.casefold())))
        if overlap:
            scored.append((overlap, row_index))
    if not scored:
        return [], {"status": "UNRESOLVED", "reason": "row_not_independently_identified"}
    best = max(score for score, _ in scored)
    rows = [row for score, row in scored if score == best]
    if len(rows) != 1:
        return [], {"status": "UNRESOLVED", "reason": "row_tie"}
    row_index = rows[0]
    years = sorted({int(value) for value in re.findall(r"\b(?:19|20)\d{2}\b", question["question"])})
    columns: list[int] = []
    for year in years:
        matches = [
            column
            for column, value in table.columns.items()
            if str(year) in value
        ]
        if not matches:
            matches = [
                column
                for column, value in table.rows.get(row_index, {}).items()
                if str(year) in value
            ]
        if len(matches) != 1:
            return [], {
                "status": "UNRESOLVED",
                "reason": "period_not_independently_identified",
                "year": year,
            }
        columns.append(matches[0])
    if not columns and question["answer_type"] == "arithmetic":
        numeric_columns = [
            column
            for column, value in table.rows.get(row_index, {}).items()
            if column > 0 and parse_decimal(value) is not None
        ]
        if len(numeric_columns) == 1:
            columns = numeric_columns
        else:
            return [], {"status": "UNRESOLVED", "reason": "period_columns_not_identified"}

    requirements: list[dict[str, Any]] = []
    if columns and question["answer_type"] in {"arithmetic", "span", "multi-span"}:
        for position, column in enumerate(columns, start=1):
            requirements.append(
                {
                    "operand_id": f"operand_{position}",
                    "citation": f"TABLE:R{row_index}:C{column}",
                    "binding_mode": "role_period",
                    "row": row_index,
                    "period": table.columns.get(column, ""),
                    "binding_source": "question_period+table_header+row_label",
                }
            )
    else:
        requirements.append(
            {
                "operand_id": "answer",
                "citation": f"TABLE:R{row_index}",
                "binding_mode": "role",
                "row": row_index,
                "binding_source": "question_entity+row_label+source_table",
            }
        )
    return requirements, {
        "status": "RESOLVED",
        "row": row_index,
        "row_label": table.row_labels[row_index],
        "columns": columns,
        "chain": "question wording and table labels/headers only; no actor output and no gold numeric scan",
    }


def paragraph_bindings(
    record: dict[str, Any], question: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paragraphs = sorted(record["paragraphs"], key=lambda item: int(item["order"]))
    index_by_order = {str(item["order"]): index for index, item in enumerate(paragraphs, 1)}
    orders = [str(order) for order in question.get("rel_paragraphs", [])]
    if not orders:
        return [], {"status": "UNRESOLVED", "reason": "no_source_annotation_paragraph"}
    missing = [order for order in orders if order not in index_by_order]
    if missing:
        return [], {"status": "UNRESOLVED", "reason": "annotation_paragraph_missing"}
    return [
        {
            "operand_id": f"paragraph_{position}",
            "citation": f"P{index_by_order[order]}",
            "binding_mode": "role",
            "raw_order": order,
            "binding_source": "source rel_paragraphs annotation+visible paragraph order",
        }
        for position, order in enumerate(orders, start=1)
    ], {
        "status": "RESOLVED",
        "raw_orders": orders,
        "chain": "source rel_paragraphs annotation and deployment-visible paragraph indexing",
    }


def source_requirement(answer_from: str) -> str:
    return {"text": "paragraph", "table": "table", "table-text": "both"}[answer_from]


def required_unit(question: dict[str, Any], table: list[list[str]]) -> str:
    scale = str(question.get("scale") or "").strip()
    if scale:
        return scale
    haystack = " ".join(table[0] + [cell for row in table for cell in row]).casefold()
    if "%" in haystack or "percent" in haystack:
        return "percent"
    if any(marker in haystack for marker in ("in thousands", "$000", "000's")):
        return "thousand"
    if any(marker in haystack for marker in ("in millions", "$m", "millions")):
        return "million"
    return "UNKNOWN"


def task_signature(question: dict[str, Any]) -> str:
    text = question["question"].casefold()
    answer_type = question["answer_type"]
    if answer_type == "count":
        return "count"
    if answer_type == "multi-span":
        return "multi_span_text" if question["answer_from"] == "text" else "multi_span_table"
    if answer_type == "arithmetic":
        if "percentage" in text or re.search(r"\bchange\b", text):
            return "arithmetic_change"
        if "average" in text or "mean" in text:
            return "arithmetic_mean"
        return "arithmetic_comparison"
    return "span_text" if question["answer_from"] == "text" else "span_numeric"


def build_reference(
    record: dict[str, Any], question: dict[str, Any]
) -> dict[str, Any] | None:
    requirement = source_requirement(question["answer_from"])
    table_requirements, table_status = table_bindings(record, question)
    paragraph_requirements, paragraph_status = paragraph_bindings(record, question)
    required: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    if requirement in {"table", "both"}:
        required.extend(table_requirements)
        statuses.append(table_status)
    if requirement in {"paragraph", "both"}:
        required.extend(paragraph_requirements)
        statuses.append(paragraph_status)
    if not required or any(item["status"] != "RESOLVED" for item in statuses):
        return None
    paragraphs = sorted(record["paragraphs"], key=lambda item: int(item["order"]))
    return {
        "question_uid": question["uid"],
        "table_uid": record["table"]["uid"],
        "family_id": record["table"]["uid"],
        "question": question["question"],
        "answer": question["answer"],
        "answer_type": question["answer_type"],
        "program": question.get("derivation", ""),
        "unit": required_unit(question, record["table"]["table"]),
        "source_requirement": requirement,
        "role": "paragraph" if requirement == "paragraph" else "table",
        "table_text": render_table(record["table"]["table"]),
        "paragraphs": [
            {
                "order": str(item["order"]),
                "uid": item.get("uid"),
                "text": item.get("text", ""),
            }
            for item in paragraphs
        ],
        "required_evidence": required,
        "binding_chain": {
            "table": table_status,
            "paragraph": paragraph_status,
            "independent_of_actor_output": True,
            "gold_numeric_value_scan": False,
        },
        "accepted_answer_source": "TAT-QA dev source answer field; frozen reference side",
        "task_signature": task_signature(question),
    }


def main() -> int:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    train_rows = json.loads(TRAIN.read_text(encoding="utf-8"))
    dev_rows = json.loads(DEV.read_text(encoding="utf-8"))
    union_manifest = json.loads(EXPOSURE_UNION.read_text(encoding="utf-8"))
    exposure_audit = json.loads(EXPOSURE_AUDIT.read_text(encoding="utf-8"))
    prior_panel = json.loads(PRIOR_PANEL.read_text(encoding="utf-8"))

    repo_union, repo_sources, parse_errors, exposure_registers = scan_repository()
    union: set[str] = set(repo_union)
    source_receipts: list[dict[str, Any]] = [
        {
            "path": str(TRAIN),
            "role": "source_split_training",
            "sha256": sha256(TRAIN),
            "identity_count": sum(
                len({item["uid"] for item in row["questions"]})
                + 1
                for row in train_rows
            ),
        },
        {
            "path": str(DEV),
            "role": "source_split_candidate_dev_not_treated_as_exposure_by_itself",
            "sha256": sha256(DEV),
            "identity_count": sum(
                len({item["uid"] for item in row["questions"]}) + 1
                for row in dev_rows
            ),
        },
        {
            "path": str(EXPOSURE_UNION),
            "role": "training_development_confirmation_error_pool_union",
            "sha256": sha256(EXPOSURE_UNION),
            "declared_source_count": len(union_manifest["sources"]),
        },
        {
            "path": str(EXPOSURE_AUDIT),
            "role": "prior_uid_and_source_cluster_audit",
            "sha256": sha256(EXPOSURE_AUDIT),
            "non_structural_uid_count": exposure_audit["exposure_model"][
                "non_structural_exposure_register"
            ]["uid_count"],
        },
        {
            "path": str(PRIOR_PANEL),
            "role": "prior_diagnostic_panel_uids",
            "sha256": sha256(PRIOR_PANEL),
            "uid_count": len(prior_panel["panel_uids"]),
        },
    ]
    for source in union_manifest["sources"]:
        path = Path(source["path"])
        found = identities(load_records(path)) if path.exists() else set()
        union.update(found)
        union.update(
            identities(load_records(path)) if path.exists() else set()
        )
        source_receipts.append(
            {
                "path": str(path),
                "role": source["role"],
                "sha256": sha256(path) if path.exists() else None,
                "identity_count": len(found),
                "exists": path.exists(),
            }
        )
    # The full audit contains structural-scan membership for nearly every dev
    # UID; only its explicit non-structural/model exposure registers are used.
    register = exposure_audit["exposure_model"]["non_structural_exposure_register"]
    union.update(str(uid) for uid in register["uids"])
    for evidence in exposure_audit["exposure_model"][
        "model_exposure_provenance"
    ].values():
        declared_uids = evidence.get("uids")
        if isinstance(declared_uids, dict):
            union.update(str(uid) for uid in declared_uids)
        elif isinstance(declared_uids, list):
            union.update(str(uid) for uid in declared_uids)
    union.update(identities(prior_panel))
    # Train is excluded from the candidate union; dev is used only as source data.
    for row in train_rows:
        union.add(row["table"]["uid"])
        union.update(item["uid"] for item in row["questions"])

    inspected_questions = [
        {
            "question_uid": "23801627-ff77-4597-8d24-1c99e2452082",
            "reason": "this-round source inspection",
        },
        {
            "question_uid": "86ae8d77-4dcd-4f82-baac-61c6a2551760",
            "reason": "this-round source inspection",
        },
        {
            "question_uid": "682e2b7e-2b40-4849-8671-2b85dd3c7f10",
            "reason": "this-round source inspection",
        },
    ]
    inspected_uids = {item["question_uid"] for item in inspected_questions}
    union.update(inspected_uids)

    records_by_uid = {row["table"]["uid"]: row for row in dev_rows}
    inspected_families: list[str] = []
    for uid in sorted(inspected_uids):
        for record in dev_rows:
            if any(question["uid"] == uid for question in record["questions"]):
                inspected_families.append(record["table"]["uid"])
                break
    union.update(inspected_families)

    eligible_families: dict[str, dict[str, Any]] = {}
    excluded: dict[str, Counter[str]] = defaultdict(Counter)
    for record in dev_rows:
        family_uid = record["table"]["uid"]
        family_ids = {family_uid} | {question["uid"] for question in record["questions"]}
        overlap = sorted(family_ids & union)
        if overlap:
            reason = (
                "this_round_inspected_family"
                if family_uid in inspected_families
                else "existing_exposure_identity"
            )
            excluded[reason][family_uid] = len(overlap)
            continue
        references = [
            reference
            for question in record["questions"]
            if (reference := build_reference(record, question)) is not None
        ]
        if not references:
            excluded["independent_reference_binding_unresolved"][family_uid] = 1
            continue
        eligible_families[family_uid] = {
            "record": record,
            "references": references,
        }

    by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for family in eligible_families.values():
        for reference in family["references"]:
            by_signature[reference["task_signature"]].append(reference)
    for items in by_signature.values():
        items.sort(key=lambda item: rank(item["question_uid"]))

    preferred = [
        "count",
        "multi_span_text",
        "multi_span_table",
        "span_numeric",
        "span_text",
        "arithmetic_change",
        "arithmetic_mean",
        "arithmetic_comparison",
    ]
    selected: list[dict[str, Any]] = []
    used_families: set[str] = set()
    for signature in preferred:
        for candidate in by_signature.get(signature, []):
            if candidate["family_id"] in used_families:
                continue
            selected.append(candidate)
            used_families.add(candidate["family_id"])
            break
    if len(selected) < PANEL_SIZE:
        for signature in sorted(by_signature):
            for candidate in by_signature[signature]:
                if len(selected) >= PANEL_SIZE:
                    break
                if candidate["family_id"] in used_families:
                    continue
                selected.append(candidate)
                used_families.add(candidate["family_id"])
            if len(selected) >= PANEL_SIZE:
                break
    selected.sort(key=lambda item: rank(item["question_uid"]))
    if len(selected) != PANEL_SIZE:
        raise SystemExit(f"unable_to_select_8_diverse_unexposed_families:{len(selected)}")

    exposure_payload = {
        "schema": "word_new_family_exposure_manifest_v1",
        "task_id": "word-scoring-new-family-a-20261027",
        "created_at": now,
        "status": "PRE_OUTPUT_EXPOSURE_AUDIT_COMPLETE",
        "model_output_before_manifest": 0,
        "source_splits": {
            "train": {"path": str(TRAIN), "sha256": sha256(TRAIN), "families": len(train_rows)},
            "dev": {"path": str(DEV), "sha256": sha256(DEV), "families": len(dev_rows)},
            "dev_role": "candidate source; not excluded merely for being dev",
        },
        "source_receipts": source_receipts,
        "repository_identity_artifacts": {
            "scanned": len(repo_sources) + len(parse_errors),
            "identity_bearing": len(repo_sources),
            "sources": repo_sources,
            "parse_errors": parse_errors,
        },
        "exposure_membership_registers": {
            "policy": "member IDs are exclusions/audits, not exposure unless corroborated by a run, development, confirmation or error-pool artifact",
            "count": len(exposure_registers),
            "sources": exposure_registers,
        },
        "this_round_inspected_questions": inspected_questions,
        "this_round_inspected_families": sorted(set(inspected_families)),
        "exposure_union_identity_count": len(union),
        "exposure_union_sha256": hashlib.sha256(
            "\n".join(sorted(union)).encode("utf-8")
        ).hexdigest(),
        "family_exclusion_counts": {
            reason: len(values) for reason, values in sorted(excluded.items())
        },
        "eligible_unexposed_family_count": len(eligible_families),
        "historical_pretraining_exposure": {
            "auditable": False,
            "reason": "base-model pretraining corpus and token-level membership are unavailable",
            "boundary": "project experimental exposure is auditable; historical pretraining exposure is not",
        },
        "source_identity_label": "SAME_SOURCE_NEW_TABLE_FAMILIES",
        "claim_boundary": (
            "TAT-QA dev selection with distinct table families; not cross-source, "
            "not human gold, and not model-pretraining-disjoint."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "EXPOSURE_MANIFEST.json").write_text(
        json.dumps(exposure_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    panel = {
        "schema": "word_new_family_eight_uid_panel_v1",
        "task_id": "word-scoring-new-family-a-20261027",
        "frozen_at": now,
        "status": "FROZEN_PRE_MODEL_OUTPUT",
        "source_identity_label": "SAME_SOURCE_NEW_TABLE_FAMILIES",
        "selection": {
            "seed": SEED,
            "rule": "one independently bound UID per table family; preferred task signatures then SHA256(seed:uid)",
            "family_count": len(selected),
            "uid_count": len(selected),
            "unique_families": len({item["family_id"] for item in selected}),
            "model_output_read": False,
        },
        "task_signature_counts": dict(
            sorted(Counter(item["task_signature"] for item in selected).items())
        ),
        "answer_type_counts": dict(
            sorted(Counter(item["answer_type"] for item in selected).items())
        ),
        "references": selected,
        "exposure_manifest_sha256": sha256(OUT / "EXPOSURE_MANIFEST.json"),
        "claim_boundary": (
            "Natural reference-side selection before model output; does not claim "
            "cross-source validation, pretraining-disjointness, confirmation or method gain."
        ),
    }
    (OUT / "PANEL_FREEZE.json").write_text(
        json.dumps(panel, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": panel["status"],
                "families": len(selected),
                "answer_types": panel["answer_type_counts"],
                "task_signatures": panel["task_signature_counts"],
                "exposure_union": len(union),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
