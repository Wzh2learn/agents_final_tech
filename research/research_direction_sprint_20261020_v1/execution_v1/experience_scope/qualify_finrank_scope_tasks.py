"""Qualify a bounded FinRank experience-scope development design.

This script performs deterministic, non-generative checks only. It separates
actor-visible task material from frozen references and records limitations that
prevent the draft from being described as an unseen confirmation set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "finrank_experience_scope_qualification_v2"
SPLIT_VERSION = "finrank_scope_split_v1"
TASK_DRAFT_VERSION = "finrank_scope_task_draft_v2"

SECTOR_TICKERS = {
    "HISTORY_PHARMA": {
        "ABBV",
        "AMGN",
        "JNJ",
        "LLY",
        "MRK",
        "MRNA",
        "PFE",
    },
    "DEVELOPMENT_AUTO": {"F", "GM", "TSLA"},
    "FUTURE_HOLDOUT_ENERGY": {
        "COP",
        "CTRA",
        "CVX",
        "DVN",
        "EOG",
        "EPD",
        "ET",
        "KMI",
        "LNG",
        "MPC",
        "WMB",
        "XOM",
    },
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "can",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "might",
    "no",
    "not",
    "of",
    "on",
    "or",
    "over",
    "should",
    "than",
    "that",
    "the",
    "their",
    "these",
    "this",
    "those",
    "to",
    "under",
    "was",
    "were",
    "what",
    "when",
    "which",
    "who",
    "why",
    "will",
    "with",
}

COMPANY_NAMES = {
    "ABBV": "AbbVie",
    "AMGN": "Amgen",
    "COP": "ConocoPhillips",
    "CTRA": "Coterra Energy",
    "CVX": "Chevron",
    "DVN": "Devon Energy",
    "EOG": "EOG Resources",
    "EPD": "Enterprise Products Partners",
    "ET": "Energy Transfer",
    "F": "Ford Motor Company",
    "GM": "General Motors",
    "JNJ": "Johnson & Johnson",
    "KMI": "Kinder Morgan",
    "LLY": "Eli Lilly",
    "LNG": "Cheniere Energy",
    "MPC": "Marathon Petroleum",
    "MRK": "Merck",
    "MRNA": "Moderna",
    "PFE": "Pfizer",
    "TSLA": "Tesla",
    "WMB": "Williams Companies",
    "XOM": "Exxon Mobil",
}

PERIOD_STATUS_OVERRIDES = {
    "ESD_005": "UNIQUE_AS_OF_YEAR_WITH_FORECAST_PARAMETERS",
    "ESD_012": "UNIQUE_EXPLICIT_PERIOD_RANGE",
    "ESH_002": "UNRESOLVED_PERIOD_LABEL_CONFLICT",
    "ESH_012": "UNRESOLVED_YEAR_ROLE_MIXED",
}

UNIT_SCOPE_OVERRIDES = {
    "ESD_006": {
        "values": ["percent"],
        "status": "PARTIALLY_EXPLICIT_MULTIPLE_OUTPUTS",
        "basis": ["Gross Margin Percentage"],
    },
    "ESD_009": {
        "values": ["percent"],
        "status": "EXPLICIT_SINGLE_UNIT",
        "basis": ["percentage"],
    },
    "ESD_011": {
        "values": ["times", "ratio"],
        "status": "MULTIPLE_EXPLICIT_UNITS",
        "basis": ["how many times", "ratio"],
    },
    "ESH_001": {
        "values": ["millions of dollars"],
        "status": "EXPLICIT_SINGLE_UNIT",
        "basis": ["in millions of dollars"],
    },
    "ESH_003": {
        "values": ["Bcf", "days"],
        "status": "MULTIPLE_EXPLICIT_UNITS",
        "basis": ["Bcf", "days of production"],
    },
    "ESH_007": {
        "values": ["units"],
        "status": "EXPLICIT_SINGLE_UNIT",
        "basis": ["common units"],
    },
    "ESH_009": {
        "values": ["millions of USD"],
        "status": "EXPLICIT_SINGLE_UNIT",
        "basis": ["in millions of USD"],
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOP_WORDS
    }


def sector_for_ticker(ticker: str) -> str:
    matches = [
        sector
        for sector, tickers in SECTOR_TICKERS.items()
        if ticker in tickers
    ]
    if len(matches) != 1:
        raise ValueError(f"UNRESOLVED_SECTOR_FOR_TICKER:{ticker}")
    return matches[0]


def is_cross_scope_hard_negative(record: dict[str, Any], item: dict[str, Any]) -> bool:
    return (
        item.get("ticker") == record.get("ticker")
        and (
            item.get("year") != record.get("year")
            or item.get("doc_type") != record.get("doc_type")
        )
    )


def is_same_scope_hard_negative(record: dict[str, Any], item: dict[str, Any]) -> bool:
    return (
        item.get("ticker") == record.get("ticker")
        and item.get("year") == record.get("year")
        and item.get("doc_type") == record.get("doc_type")
    )


def build_hash_components(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    tickers = sorted({record["ticker"] for record in records})
    parent = {ticker: ticker for ticker in tickers}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    hash_tickers: dict[str, set[str]] = defaultdict(set)
    for record in records:
        passages = record.get("passages", []) + record.get("hard_negatives", [])
        for passage in passages:
            text_hash = passage.get("text_sha1")
            if text_hash:
                hash_tickers[text_hash].add(record["ticker"])

    for linked_tickers in hash_tickers.values():
        ordered = sorted(linked_tickers)
        for ticker in ordered[1:]:
            union(ordered[0], ticker)

    components: dict[str, set[str]] = defaultdict(set)
    for ticker in tickers:
        components[find(ticker)].add(ticker)

    ticker_to_component = {
        ticker: f"source_component_{index:02d}"
        for index, component in enumerate(
            sorted(components.values(), key=lambda values: sorted(values)), start=1
        )
        for ticker in sorted(component)
    }
    component_records = [
        {
            "source_cluster_id": f"source_component_{index:02d}",
            "tickers": sorted(component),
            "cross_ticker_exact_text_hash_links": sum(
                1
                for linked_tickers in hash_tickers.values()
                if len(linked_tickers.intersection(component)) > 1
            ),
        }
        for index, component in enumerate(
            sorted(components.values(), key=lambda values: sorted(values)), start=1
        )
    ]
    return ticker_to_component, component_records


def lexical_top_k_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_sets = 0
    evaluated = 0
    by_gold_count: dict[str, int] = Counter()
    for record in rows:
        candidates = [
            {
                **item,
                "ticker": item.get("ticker", record.get("ticker")),
                "year": item.get("year", record.get("year")),
                "doc_type": item.get("doc_type", record.get("doc_type")),
                "reference_class": "gold",
            }
            for item in record.get("passages", [])
        ]
        candidates.extend(
            {**item, "reference_class": "hard"}
            for item in record.get("hard_negatives", [])
        )
        gold_ids = {
            item["passage_id"]
            for item in candidates
            if item["reference_class"] == "gold"
        }
        question_tokens = tokens(record["question"])
        scored: list[tuple[float, str]] = []
        for item in candidates:
            passage_tokens = tokens(item.get("text", ""))
            union_size = len(question_tokens.union(passage_tokens))
            overlap = len(question_tokens.intersection(passage_tokens))
            score = overlap / union_size if union_size else 0.0
            scored.append((score, item["passage_id"]))
        scored.sort(key=lambda value: (-value[0], value[1]))
        predicted = {passage_id for _, passage_id in scored[: len(gold_ids)]}
        is_exact = predicted == gold_ids
        exact_sets += int(is_exact)
        evaluated += 1
        by_gold_count[f"{len(gold_ids)}_gold:{str(is_exact).lower()}"] += 1
    return {
        "method": "stopword-filtered question/passage token Jaccard; top-k with k=gold_count",
        "scientific_status": "OFFLINE_HEADROOM_PROBE_NOT_A_MODEL_BASELINE",
        "records_evaluated": evaluated,
        "exact_gold_sets": exact_sets,
        "exact_gold_set_rate": round(exact_sets / evaluated, 6) if evaluated else None,
        "by_gold_count": dict(sorted(by_gold_count.items())),
    }


def visible_year_policy_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = 0
    wrong = 0
    abstain = 0
    for record in rows:
        candidates = [
            {
                **item,
                "ticker": item.get("ticker", record.get("ticker")),
                "year": item.get("year", record.get("year")),
                "doc_type": item.get("doc_type", record.get("doc_type")),
                "reference_class": "gold",
            }
            for item in record.get("passages", [])
        ]
        candidates.extend(
            {**item, "reference_class": "hard"}
            for item in record.get("hard_negatives", [])
        )
        question_years = [
            int(value) for value in re.findall(r"\b20\d{2}\b", record["question"])
        ]
        if not question_years:
            abstain += 1
            continue
        matches = [
            item
            for item in candidates
            if item.get("year") == question_years[-1]
            and item.get("doc_type") == record.get("doc_type")
        ]
        if not matches:
            abstain += 1
        elif any(item["reference_class"] == "gold" for item in matches):
            correct += 1
        else:
            wrong += 1
    return {
        "method": "candidate filing year equals last question year and candidate form equals record form",
        "scientific_status": "LEAKAGE_AND_SIMPLE_RULE_PROBE",
        "correct_if_any_gold_match": correct,
        "wrong_if_only_hard_match": wrong,
        "abstain": abstain,
    }


def balanced_selection(
    records: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_ticker[record["ticker"]].append(record)
    for ticker in by_ticker:
        by_ticker[ticker].sort(
            key=lambda item: (
                item.get("topic", ""),
                item.get("difficulty", ""),
                item["question_id"],
            )
        )
    selected: list[dict[str, Any]] = []
    ticker_order = sorted(by_ticker)
    cursor = 0
    while len(selected) < limit:
        added = False
        for ticker in ticker_order:
            if cursor < len(by_ticker[ticker]):
                selected.append(by_ticker[ticker][cursor])
                added = True
                if len(selected) == limit:
                    break
        if not added:
            break
        cursor += 1
    return sorted(selected, key=lambda item: item["question_id"])


def build_question_scope(record: dict[str, Any], task_id: str) -> dict[str, Any]:
    question = record["question"]
    mentioned = []
    for ticker, name in sorted(COMPANY_NAMES.items()):
        name_pattern = rf"\b{re.escape(name)}\b"
        ticker_pattern = rf"\b{re.escape(ticker)}\b"
        if re.search(name_pattern, question, re.IGNORECASE) or re.search(
            ticker_pattern, question
        ):
            mentioned.append({"ticker": ticker, "name": name})

    years = sorted({int(value) for value in re.findall(r"\b20\d{2}\b", question)})
    dates = re.findall(
        r"\b(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},\s+20\d{2}\b",
        question,
        re.IGNORECASE,
    )
    period_status = PERIOD_STATUS_OVERRIDES.get(
        task_id, "UNIQUE_EXPLICIT_PERIOD_SET"
    )

    if re.search(r"\b10-K\b|\bannual report\b", question, re.IGNORECASE):
        form = {"value": "10-K", "status": "EXPLICIT_OR_ALIAS"}
    elif re.search(r"\b10-Q\b|\bquarterly report\b", question, re.IGNORECASE):
        form = {"value": "10-Q", "status": "EXPLICIT_OR_ALIAS"}
    else:
        form = {"value": None, "status": "NOT_EXPLICIT_IN_QUESTION"}

    unit = UNIT_SCOPE_OVERRIDES.get(
        task_id,
        {
            "values": [],
            "status": "NOT_EXPLICIT_IN_QUESTION",
            "basis": [],
        },
    )
    entity_status = "EXPLICIT_TARGET_ENTITY"
    if len(mentioned) > 1:
        entity_status = "MULTIPLE_EXPLICIT_ENTITY_REFERENCES_TARGET_REQUIRES_HUMAN_CONFIRMATION"
    return {
        "entity": {
            "target_ticker": record["ticker"],
            "target_name": COMPANY_NAMES.get(record["ticker"], record["ticker"]),
            "mentioned_entities": mentioned,
            "status": entity_status,
        },
        "requested_period": {
            "explicit_years": years,
            "explicit_dates": dates,
            "status": period_status,
            "unique": period_status.startswith("UNIQUE_"),
        },
        "form": form,
        "unit": {
            "values": unit["values"],
            "status": unit["status"],
            "basis": unit["basis"],
        },
    }


def visible_source_scope(
    item: dict[str, Any], record: dict[str, Any]
) -> dict[str, Any]:
    ticker = item.get("ticker", record.get("ticker"))
    year = item.get("year", record.get("year"))
    doc_type = item.get("doc_type", record.get("doc_type"))
    resolved = all(value is not None for value in (ticker, year, doc_type))
    return {
        "ticker": ticker if ticker is not None else "UNRESOLVED",
        "year": year if year is not None else "UNRESOLVED",
        "doc_type": doc_type if doc_type is not None else "UNRESOLVED",
        "status": "RESOLVED" if resolved else "UNRESOLVED",
    }


def normalized_numeric_tokens(text: str) -> set[str]:
    values = set()
    for value in re.findall(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?", text):
        normalized = value.replace(",", "")
        if re.fullmatch(r"19\d{2}|20\d{2}", normalized):
            continue
        values.add(normalized)
    return values


def assess_reference_ambiguity(
    record: dict[str, Any],
    source_candidates: list[dict[str, Any]],
    question_scope: dict[str, Any],
    taxonomy_by_passage_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    gold_items = [
        item for item in source_candidates if item["reference_class"] == "gold"
    ]
    hard_items = [
        item for item in source_candidates if item["reference_class"] == "hard"
    ]
    answer_numbers = normalized_numeric_tokens(record["answer"])
    numeric_alternatives = []
    for item in hard_items:
        candidate_numbers = normalized_numeric_tokens(item.get("text", ""))
        if answer_numbers and answer_numbers.issubset(candidate_numbers):
            numeric_alternatives.append(item["passage_id"])

    cross_record_gold_overlaps = [
        item["passage_id"]
        for item in hard_items
        if taxonomy_by_passage_id.get(item["passage_id"], {}).get("overlaps_gold_of")
    ]
    if cross_record_gold_overlaps:
        alternative_status = "POTENTIAL_VISIBLE_ALTERNATIVE_SUPPORT"
        alternative_exists = "POTENTIAL_YES"
    elif numeric_alternatives:
        alternative_status = "POSSIBLE_VISIBLE_ALTERNATIVE_SUPPORT"
        alternative_exists = "UNRESOLVED"
    else:
        alternative_status = "NOT_RULED_OUT_BY_DETERMINISTIC_CHECKS"
        alternative_exists = "UNRESOLVED"

    period_status = question_scope["requested_period"]["status"]
    unit_status = question_scope["unit"]["status"]
    unit_unique = "NO_NOT_EXPLICIT"
    if unit_status in {"EXPLICIT_SINGLE_UNIT", "MULTIPLE_EXPLICIT_UNITS"}:
        unit_unique = "YES_EXPLICIT_SET"
    elif unit_status == "PARTIALLY_EXPLICIT_MULTIPLE_OUTPUTS":
        unit_unique = "UNRESOLVED"

    reason_codes = ["SUPPORT_RELATION_NOT_INDEPENDENTLY_ADJUDICATED"]
    if alternative_exists != "NO":
        reason_codes.append("VISIBLE_ALTERNATIVE_SUPPORT_NOT_EXCLUDED")
    if question_scope["entity"]["status"].startswith("MULTIPLE_"):
        reason_codes.append("MULTIPLE_ENTITY_REFERENCES")
    if not period_status.startswith("UNIQUE_"):
        reason_codes.append("REQUESTED_PERIOD_NOT_UNIQUE")
    if unit_unique == "UNRESOLVED":
        reason_codes.append("REQUESTED_UNIT_NOT_UNIQUE")
    if len(gold_items) > 1:
        reason_codes.append("MULTI_PASSAGE_SUFFICIENCY_REQUIRES_ADJUDICATION")

    return {
        "check_scope": (
            "Conservative deterministic check of exact cross-record gold overlap, "
            "numeric overlap, requested period and requested unit. This is not "
            "an independent human semantic gold judgment."
        ),
        "visible_alternative_support_exists": alternative_exists,
        "visible_alternative_support_status": alternative_status,
        "cross_record_gold_overlap_passage_ids": cross_record_gold_overlaps,
        "possible_numeric_alternative_passage_ids": numeric_alternatives,
        "requested_period_unique": (
            "YES" if period_status.startswith("UNIQUE_") else "NO_OR_UNRESOLVED"
        ),
        "requested_period_status": period_status,
        "requested_unit_unique": unit_unique,
        "requested_unit_status": unit_status,
        "classification": "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION",
        "reason_codes": reason_codes,
        "reference_use_status": "BLOCKED_PENDING_HUMAN_SEMANTIC_ADJUDICATION",
    }


def build_tool_contract_draft() -> dict[str, Any]:
    return {
        "schema": "experience_scope_tool_contract_draft_v2",
        "status": "DRAFT_NOT_EXECUTED",
        "flow": ["plan", "evidence_lookup", "consume"],
        "plan": {
            "actor_output_schema": {
                "type": "object",
                "required": ["experience_actions", "evidence_candidate_ids"],
                "properties": {
                    "experience_actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["experience_id", "decision"],
                            "properties": {
                                "experience_id": {"type": "string"},
                                "decision": {
                                    "enum": ["APPLY", "SKIP", "ABSTAIN"]
                                },
                            },
                            "additionalProperties": False,
                        },
                    },
                    "evidence_candidate_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                },
                "additionalProperties": False,
            }
        },
        "tool": {
            "name": "evidence_lookup",
            "input_schema": {
                "type": "object",
                "required": ["candidate_ids"],
                "properties": {
                    "candidate_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    }
                },
                "additionalProperties": False,
            },
            "output_schema": {
                "type": "object",
                "required": ["tool_status", "evidence"],
                "properties": {
                    "tool_status": {"enum": ["OK", "INVALID_ARGUMENT"]},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": [
                                "candidate_id",
                                "text",
                                "visible_source_scope",
                            ],
                            "properties": {
                                "candidate_id": {"type": "string"},
                                "text": {"type": "string"},
                                "visible_source_scope": {"type": "object"},
                            },
                            "additionalProperties": False,
                        },
                    },
                },
                "additionalProperties": False,
            },
            "behavior": (
                "Return only the visible text and visible source scope for the "
                "supplied candidate IDs. Reject unknown IDs, empty selections, "
                "duplicates and malformed arguments. Never return answers, gold "
                "labels, hidden coordinates or reference metadata."
            ),
        },
        "consume": {
            "actor_output_schema": {
                "type": "object",
                "required": ["answer_status", "answer_value", "used_candidate_ids"],
                "properties": {
                    "answer_status": {
                        "enum": ["ANSWER", "UNKNOWN", "REFUSE"]
                    },
                    "answer_value": {"type": ["string", "null"]},
                    "used_candidate_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                },
                "additionalProperties": False,
            },
            "contract": (
                "Consume the actual evidence_lookup return before answering. "
                "UNKNOWN and REFUSE must set answer_value to null. The checker "
                "records answer/reference match, tool execution status and "
                "answer/tool-return consistency separately."
            ),
        },
    }


def build_actor_and_reference(
    record: dict[str, Any],
    task_id: str,
    split: str,
    taxonomy_by_passage_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_candidates = [
        {**item, "reference_class": "gold"}
        for item in record.get("passages", [])
    ]
    source_candidates.extend(
        {**item, "reference_class": "hard"}
        for item in record.get("hard_negatives", [])
    )
    seed = int(hashlib.sha256(f"{TASK_DRAFT_VERSION}|{task_id}".encode()).hexdigest(), 16)
    shuffled = list(source_candidates)
    random.Random(seed).shuffle(shuffled)
    opaque_ids = {
        item["passage_id"]: f"cand_{index:03d}"
        for index, item in enumerate(shuffled, start=1)
    }
    actor_candidates = [
        {
            "candidate_id": opaque_ids[item["passage_id"]],
            "text": item.get("text"),
            "page_number": item.get("page_number"),
            "visible_source_scope": visible_source_scope(item, record),
        }
        for item in shuffled
    ]
    gold_items = [
        item for item in source_candidates if item["reference_class"] == "gold"
    ]
    hard_items = [
        item for item in source_candidates if item["reference_class"] == "hard"
    ]
    question_scope = build_question_scope(record, task_id)
    reference_ambiguity = assess_reference_ambiguity(
        record,
        source_candidates,
        question_scope,
        taxonomy_by_passage_id,
    )
    return {
        "task_id": task_id,
        "split": split,
        "source_ticker": record["ticker"],
        "source_cluster_id": record["source_cluster_id"],
        "source_report_key": (
            f"{record['ticker']}|{record['year']}|{record['doc_type']}"
        ),
        "actor_view": {
            "instruction": (
                "Select every candidate passage that is sufficient evidence for "
                "the question. Return candidate_id values only. Do not infer "
                "support from topical similarity alone."
            ),
            "question": record["question"],
            "question_scope": question_scope,
            "candidates": actor_candidates,
            "experience_context": "TO_BE_CONSTRUCTED_AFTER_TASK_MATCHED_HISTORY_COLLECTION",
        },
        "reference": {
            "answer": record["answer"],
            "supporting_candidate_ids": [
                opaque_ids[item["passage_id"]] for item in gold_items
            ],
            "supporting_source_passage_ids": [
                item["passage_id"] for item in gold_items
            ],
            "hard_negative_source_passage_ids": [
                item["passage_id"] for item in hard_items
            ],
            "cross_scope_hard_negative_source_passage_ids": [
                item["passage_id"]
                for item in hard_items
                if is_cross_scope_hard_negative(record, item)
            ],
            "same_scope_hard_negative_source_passage_ids": [
                item["passage_id"]
                for item in hard_items
                if is_same_scope_hard_negative(record, item)
            ],
            "reference_provenance": (
                "FinRank human-authored supporting passages and curated hard "
                "negatives; dataset README reports single annotator per record "
                "and no formal inter-annotator agreement"
            ),
            "reference_ambiguity_check": reference_ambiguity,
        },
    }


def qualify(
    finrank_path: Path,
    readme_path: Path,
    license_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    records = [
        json.loads(line)
        for line in finrank_path.open(encoding="utf-8")
        if line.strip()
    ]
    taxonomy_path = finrank_path.parent / "hn_taxonomy.json"
    taxonomy_rows = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    taxonomy_by_passage_id = {
        item["passage_id"]: item for item in taxonomy_rows
    }
    license_text = license_path.read_text(encoding="utf-8", errors="replace")
    readme_text = readme_path.read_text(encoding="utf-8", errors="replace")
    if "CC BY-NC 4.0" not in readme_text:
        raise ValueError("FINRANK_LICENSE_STATUS_NOT_CONFIRMED")
    if "Attribution-NonCommercial" not in license_text:
        raise ValueError("FINRANK_LICENSE_TEXT_NOT_CONFIRMED")

    ticker_to_component, source_components = build_hash_components(records)
    eligible: list[dict[str, Any]] = []
    excluded = Counter()
    for record in records:
        question_years = re.findall(r"\b20\d{2}\b", record["question"])
        hard_negatives = record.get("hard_negatives", [])
        cross_scope = [
            item
            for item in hard_negatives
            if is_cross_scope_hard_negative(record, item)
        ]
        gold_hashes = {
            item.get("text_sha1")
            for item in record.get("passages", [])
            if item.get("text_sha1")
        }
        hard_hashes = {
            item.get("text_sha1")
            for item in hard_negatives
            if item.get("text_sha1")
        }
        if not question_years:
            excluded["NO_EXPLICIT_QUESTION_YEAR"] += 1
            continue
        if not cross_scope:
            excluded["NO_SAME_COMPANY_CROSS_PERIOD_OR_FORM_NEGATIVE"] += 1
            continue
        if gold_hashes.intersection(hard_hashes):
            excluded["GOLD_HARD_TEXT_HASH_OVERLAP"] += 1
            continue
        if not record.get("passages"):
            excluded["NO_SUPPORTING_PASSAGE_REFERENCE"] += 1
            continue
        enriched = dict(record)
        enriched["source_cluster_id"] = ticker_to_component[record["ticker"]]
        enriched["sector_split"] = sector_for_ticker(record["ticker"])
        eligible.append(enriched)

    eligible.sort(key=lambda item: item["question_id"])
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in eligible:
        by_split[record["sector_split"]].append(record)

    development = balanced_selection(
        by_split["DEVELOPMENT_AUTO"], limit=12
    )
    future = balanced_selection(
        by_split["FUTURE_HOLDOUT_ENERGY"], limit=12
    )
    history_candidates = balanced_selection(
        by_split["HISTORY_PHARMA"], limit=24
    )

    task_rows: list[dict[str, Any]] = []
    for split_name, split_rows, prefix in (
        ("DEVELOPMENT", development, "ESD"),
        ("FUTURE_DEVELOPMENT_HOLDOUT", future, "ESH"),
    ):
        for index, record in enumerate(split_rows, start=1):
            task_rows.append(
                build_actor_and_reference(
                    record,
                    task_id=f"{prefix}_{index:03d}",
                    split=split_name,
                    taxonomy_by_passage_id=taxonomy_by_passage_id,
                )
            )

    ambiguity_rows = [
        task["reference"]["reference_ambiguity_check"] for task in task_rows
    ]
    ambiguity_summary = {
        "tasks_checked": len(ambiguity_rows),
        "requires_human_semantic_adjudication": sum(
            row["classification"] == "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION"
            for row in ambiguity_rows
        ),
        "potential_visible_alternative_support": sum(
            row["visible_alternative_support_exists"] == "POTENTIAL_YES"
            for row in ambiguity_rows
        ),
        "visible_alternative_support_unresolved": sum(
            row["visible_alternative_support_exists"] == "UNRESOLVED"
            for row in ambiguity_rows
        ),
        "period_unique": sum(
            row["requested_period_unique"] == "YES" for row in ambiguity_rows
        ),
        "period_unresolved_or_non_unique": sum(
            row["requested_period_unique"] != "YES" for row in ambiguity_rows
        ),
        "unit_explicit_unique_set": sum(
            row["requested_unit_unique"] == "YES_EXPLICIT_SET"
            for row in ambiguity_rows
        ),
        "unit_not_explicit": sum(
            row["requested_unit_unique"] == "NO_NOT_EXPLICIT"
            for row in ambiguity_rows
        ),
        "unit_unresolved": sum(
            row["requested_unit_unique"] == "UNRESOLVED"
            for row in ambiguity_rows
        ),
    }

    qualification = {
        "schema": SCHEMA_VERSION,
        "status": "QUALIFICATION_REVISION_COMPLETE_BLOCKED",
        "scientific_scope": (
            "Development-only feasibility and headroom qualification; no model "
            "request, no learning-effect result and no independent confirmation."
        ),
        "generation_gate": {
            "status": "BLOCKED_REFERENCE_AND_TOOL_CONTRACT_PENDING",
            "reason": (
                "All 24 draft tasks require conservative human semantic "
                "adjudication and the plan->evidence_lookup->consume contract is "
                "draft-only. No generation request is authorized."
            ),
        },
        "inputs": {
            "finrank_jsonl": str(finrank_path),
            "finrank_jsonl_sha256": sha256_file(finrank_path),
            "finrank_readme": str(readme_path),
            "finrank_readme_sha256": sha256_file(readme_path),
            "finrank_license": str(license_path),
            "finrank_license_sha256": sha256_file(license_path),
            "license": "CC BY-NC 4.0",
        },
        "eligibility_rule": {
            "task_need": (
                "Question contains an explicit 20xx period and the record has at "
                "least one same-company hard negative from a different filing "
                "year or document form."
            ),
            "reference_rule": (
                "At least one human-curated supporting passage and no exact "
                "text_sha1 overlap between supporting passages and hard negatives."
            ),
            "not_selected_by_model_error": True,
        },
        "counts": {
            "records_read": len(records),
            "eligible_records": len(eligible),
            "excluded_records": dict(sorted(excluded.items())),
            "eligible_by_sector_split": {
                split: len(rows) for split, rows in sorted(by_split.items())
            },
            "selected_development_tasks": len(development),
            "selected_future_development_holdout_tasks": len(future),
            "selected_history_collection_candidates": len(history_candidates),
            "reference_ambiguity": ambiguity_summary,
        },
        "source_isolation": {
            "method": (
                "Ticker-level baseline plus conservative union across any exact "
                "text_sha1 shared by passages or hard negatives."
            ),
            "components": source_components,
            "report_identity_limit": (
                "The release does not expose a stable filing report ID; "
                "ticker|year|form is a conservative report key and can merge "
                "multiple quarterly filings. Cross-report independence is "
                "UNRESOLVED and must not be claimed."
            ),
            "split_rule": {
                "version": SPLIT_VERSION,
                "HISTORY_PHARMA": sorted(SECTOR_TICKERS["HISTORY_PHARMA"]),
                "DEVELOPMENT_AUTO": sorted(SECTOR_TICKERS["DEVELOPMENT_AUTO"]),
                "FUTURE_HOLDOUT_ENERGY": sorted(
                    SECTOR_TICKERS["FUTURE_HOLDOUT_ENERGY"]
                ),
            },
        },
        "decision_space_probes": {
            "lexical_top_k": lexical_top_k_probe(eligible),
            "visible_year_and_form_rule": visible_year_policy_probe(eligible),
        },
        "reference_quality": {
            "status": "HUMAN_CURATED_WITH_LIMITED_INTER_ANNOTATOR_EVIDENCE",
            "per_task_ambiguity_status": (
                "All 24 tasks are marked "
                "REQUIRES_HUMAN_SEMANTIC_ADJUDICATION; this script does not "
                "create or certify a new human gold label."
            ),
            "facts": [
                "FinRank README states that questions, answers, passages and hard negatives were manually authored.",
                "FinRank README reports single annotator per record and no formal inter-annotator agreement.",
                "No eligible record has exact text_sha1 overlap between a supporting passage and a hard negative.",
                "The per-task check can identify potential visible alternatives but cannot rule out semantic alternative support without human adjudication.",
            ],
            "human_semantic_adjudication_required_for": [
                "Any future case where multiple candidate passages can answer the question despite one recorded supporting-passage label.",
                "Any task whose requested period or unit cannot be uniquely resolved from the question and visible passage text.",
            ],
        },
        "exposure": {
            "researcher_material_exposure": "CONFIRMED",
            "model_training_or_prompt_exposure": "EXPOSURE_UNKNOWN",
            "use_status": (
                "DEVELOPMENT_ONLY; not an unseen or pretraining-unseen "
                "confirmation set."
            ),
        },
        "known_blockers_for_generation": [
            "All 24 task references are BLOCKED_PENDING_HUMAN_SEMANTIC_ADJUDICATION.",
            "No task-matched FinRank historical experience has been collected.",
            "The plan->evidence_lookup->consume contract is a draft and has not been instantiated as a runner or fixture-tested.",
            "The proposed experience gate and strong-rule/solved-example controls have not received independent scientific review.",
            "No fixed runtime, prompt or raw-response contract has been frozen for this candidate.",
            "Exact source-cluster independence beyond the conservative connected components is unresolved.",
        ],
        "next_gate": (
            "Independent review of this qualification and the task draft; if "
            "unblocked, design a small task-matched history collection and B0. "
            "Do not issue a generation request from this artifact alone."
        ),
    }

    task_draft = {
        "schema": TASK_DRAFT_VERSION,
        "status": "DRAFT_ONLINE_NOT_AUTHORIZED",
        "qualification_schema": SCHEMA_VERSION,
        "generation_gate": "BLOCKED_REFERENCE_AND_TOOL_CONTRACT_PENDING",
        "tool_contract_draft": build_tool_contract_draft(),
        "selection": {
            "rule": (
                "Within each sector split, sort by ticker, topic, difficulty and "
                "question_id; round-robin across tickers up to the fixed limit."
            ),
            "development_limit": 12,
            "future_holdout_limit": 12,
            "history_candidate_limit": 24,
            "selection_used_model_outputs": False,
        },
        "history_collection_candidate_ids": [
            record["question_id"] for record in history_candidates
        ],
        "tasks": task_rows,
    }
    return qualification, task_draft


def main() -> None:
    parser = argparse.ArgumentParser()
    script_dir = Path(__file__).resolve().parent
    execution_dir = script_dir.parent
    parser.add_argument(
        "--finrank-jsonl",
        type=Path,
        default=execution_dir
        / "paper_e_audit"
        / "vendor"
        / "FinRank"
        / "FinRank.jsonl",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=execution_dir
        / "paper_e_audit"
        / "vendor"
        / "FinRank"
        / "README.md",
    )
    parser.add_argument(
        "--license",
        type=Path,
        default=execution_dir
        / "paper_e_audit"
        / "vendor"
        / "FinRank"
        / "LICENSE",
    )
    parser.add_argument("--output-dir", type=Path, default=script_dir)
    args = parser.parse_args()

    qualification, task_draft = qualify(
        args.finrank_jsonl.resolve(),
        args.readme.resolve(),
        args.license.resolve(),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    qualification_path = args.output_dir / "SCOPE_TASK_QUALIFICATION.json"
    task_draft_path = args.output_dir / "SCOPE_TASK_DRAFT.json"
    qualification_path.write_text(
        json.dumps(qualification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    task_draft_path.write_text(
        json.dumps(task_draft, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "qualification_status": qualification["status"],
                "eligible_records": qualification["counts"]["eligible_records"],
                "development_tasks": qualification["counts"][
                    "selected_development_tasks"
                ],
                "future_holdout_tasks": qualification["counts"][
                    "selected_future_development_holdout_tasks"
                ],
                "qualification_path": str(qualification_path),
                "task_draft_path": str(task_draft_path),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
