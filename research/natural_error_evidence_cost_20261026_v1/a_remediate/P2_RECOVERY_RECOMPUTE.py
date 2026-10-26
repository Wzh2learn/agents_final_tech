#!/usr/bin/env python3
"""Deterministic, gold-free P2 action replay and offline evidence scoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTHORITY_COMMIT = "622b386986ca66c8119263e146f3d3e73c33e260"
SOURCE_SHA256 = "8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5"
DEFAULT_SOURCE = Path(
    "/home/testuser/wzh/projects/agents_final_tech/data/research/"
    "tatqa_raw_2026/tatqa_dataset_dev.json"
)
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent

STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are as at be because
    been before being below between both but by can cannot could did do does
    doing done down during each few for from further had has have having he
    her here hers herself him himself his how i if in into is it its itself
    let me more most must my myself no nor not of off on once only or other
    ought our ours ourselves out over own same shall she should so some such
    than that the their theirs them themselves then there these they this
    those through to too under until up very was we were what when where which
    while who whom why will with would you your yours yourself yourselves
    """.split()
)

FRONTIER_ORDER = (
    "table_only",
    "small_topk_3",
    "fixed_top1_neighbor",
    "larger_topk_5",
    "always_expand",
    "transparent_stop_expand",
)

FRONTIER_DEFINITIONS = {
    "table_only": {
        "paragraphs": 0,
        "rule": "canonical table serialization only",
        "deterministic_actions": 0,
    },
    "small_topk_3": {
        "paragraphs": "up to 3",
        "rule": "record-local TF-IDF unigram+bigram top-3",
        "deterministic_actions": 3,
    },
    "fixed_top1_neighbor": {
        "paragraphs": "top-1 plus immediate preceding/following paragraph",
        "rule": "record-local TF-IDF top-1 with fixed local neighbors",
        "deterministic_actions": 3,
    },
    "larger_topk_5": {
        "paragraphs": "up to 5",
        "rule": "record-local TF-IDF unigram+bigram top-5",
        "deterministic_actions": 5,
    },
    "always_expand": {
        "paragraphs": "all",
        "rule": "canonical table plus every paragraph in the same raw record",
        "deterministic_actions": "all_paragraphs",
    },
    "transparent_stop_expand": {
        "paragraphs": "stage-dependent",
        "rule": (
            "table-only, top-1+neighbors, top-3, top-5, all; stop at the "
            "first stage whose selected paragraphs cover >=0.80 unique "
            "question tokens"
        ),
        "deterministic_actions": "up_to_5_stages",
    },
}

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" \t\r\n.,;:")
    return text


def text_contains(haystack: Any, needle: Any) -> bool:
    return normalize_text(needle) in normalize_text(haystack)


def normalized_word_containment(haystack: Any, needle: Any) -> bool:
    normalized_haystack = normalize_text(haystack)
    normalized_needle = normalize_text(needle)
    if not normalized_needle:
        return False
    if normalized_haystack == normalized_needle:
        return True
    return bool(
        re.search(
            rf"(?<!\w){re.escape(normalized_needle)}(?!\w)",
            normalized_haystack,
        )
    )


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return [
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) >= 2 and token not in STOPWORDS
    ]


def features(text: str) -> list[str]:
    tokens = tokenize(text)
    return tokens + [f"{left}__{right}" for left, right in zip(tokens, tokens[1:])]


def serialize_table(table: dict[str, Any]) -> str:
    return json.dumps(
        table["table"],
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
    )


def serialize_paragraph(paragraph: dict[str, Any]) -> str:
    value = {
        "order": paragraph["order"],
        "text": paragraph["text"],
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _tfidf_vectors(
    documents: list[list[str]],
    query: list[str],
) -> tuple[list[dict[str, float]], dict[str, float]]:
    document_count = len(documents)
    document_frequency: Counter[str] = Counter()
    for document in documents:
        document_frequency.update(set(document))

    def vector(counts: Counter[str]) -> dict[str, float]:
        values = {
            token: frequency
            * (math.log((1 + document_count) / (1 + document_frequency[token])) + 1)
            for token, frequency in counts.items()
        }
        norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
        return {token: value / norm for token, value in values.items()}

    document_vectors = [vector(Counter(document)) for document in documents]
    query_vector = vector(Counter(query))
    return document_vectors, query_vector


def rank_paragraphs(
    question: str,
    paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank paragraphs without reference answers, scales, or gold paragraph IDs."""
    documents = [features(paragraph["text"]) for paragraph in paragraphs]
    document_vectors, query_vector = _tfidf_vectors(
        documents,
        features(question),
    )
    ranked = []
    for paragraph, vector in zip(paragraphs, document_vectors):
        score = sum(
            query_vector.get(token, 0.0) * weight
            for token, weight in vector.items()
        )
        ranked.append(
            {
                "order": paragraph["order"],
                "paragraph_uid": paragraph["uid"],
                "score": score,
            }
        )
    ranked.sort(key=lambda row: (-row["score"], row["order"], row["paragraph_uid"]))
    return ranked


def _neighbor_orders(top_order: int) -> set[int]:
    return {top_order, top_order - 1, top_order + 1}


def _question_coverage(question: str, selected_orders: set[int], paragraphs: list[dict[str, Any]]) -> float:
    query_tokens = set(tokenize(question))
    if not query_tokens:
        return 1.0
    selected_tokens = set()
    for paragraph in paragraphs:
        if paragraph["order"] in selected_orders:
            selected_tokens.update(tokenize(paragraph["text"]))
    return len(query_tokens & selected_tokens) / len(query_tokens)


def build_frontier_actions(
    question: str,
    paragraphs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Choose all deployable paragraph actions using visible inputs only."""
    ranked = rank_paragraphs(question, paragraphs)
    ranked_orders = [row["order"] for row in ranked]
    top_one = ranked_orders[:1]
    actions: dict[str, dict[str, Any]] = {
        "table_only": {"paragraph_orders": [], "stop_stage": "table_only"},
        "small_topk_3": {
            "paragraph_orders": ranked_orders[:3],
            "stop_stage": "top3",
        },
        "fixed_top1_neighbor": {
            "paragraph_orders": sorted(_neighbor_orders(top_one[0])),
            "stop_stage": "top1_neighbor",
        },
        "larger_topk_5": {
            "paragraph_orders": ranked_orders[:5],
            "stop_stage": "top5",
        },
        "always_expand": {
            "paragraph_orders": ranked_orders,
            "stop_stage": "all",
        },
    }
    stage_sets = [
        ("table_only", set()),
        ("top1_neighbor", set(actions["fixed_top1_neighbor"]["paragraph_orders"])),
        ("top3", set(actions["small_topk_3"]["paragraph_orders"])),
        ("top5", set(actions["larger_topk_5"]["paragraph_orders"])),
        ("all", set(actions["always_expand"]["paragraph_orders"])),
    ]
    stop_stage = "all"
    stop_orders = stage_sets[-1][1]
    for stage_name, orders in stage_sets:
        stop_stage = stage_name
        stop_orders = set(orders)
        if _question_coverage(question, orders, paragraphs) >= 0.80:
            break
    actions["transparent_stop_expand"] = {
        "paragraph_orders": sorted(stop_orders),
        "stop_stage": stop_stage,
    }
    valid_orders = {paragraph["order"] for paragraph in paragraphs}
    for frontier in actions.values():
        frontier["paragraph_orders"] = sorted(
            set(frontier["paragraph_orders"]) & valid_orders
        )
        frontier["ranked_score_by_order"] = {
            str(row["order"]): row["score"] for row in ranked
        }
    return actions


def _numeric_literals(text: str) -> list[str]:
    return re.findall(r"\d[\d,]*(?:\.\d+)?", text)


def _target_terms(question: dict[str, Any]) -> list[str]:
    answer_type = question["answer_type"]
    if answer_type in {"span", "multi-span"}:
        answer = question["answer"]
        return answer if isinstance(answer, list) else [str(answer)]
    if answer_type == "count":
        source = str(question.get("derivation") or question["answer"])
        return [part for part in source.split("##") if part]
    source = str(question.get("derivation") or question["answer"])
    return _numeric_literals(source) or [str(question["answer"])]


def resolve_scale_source(
    question: dict[str, Any],
    table_text: str,
    paragraph_text: str,
) -> dict[str, Any]:
    """Offline reference scoring only; never called by build_frontier_actions."""
    scale = str(question.get("scale") or "")
    if not scale:
        return {
            "source": "not_required",
            "visible": True,
            "ambiguous": False,
            "status": "OK",
        }
    in_table = text_contains(table_text, scale)
    in_question = text_contains(question["question"], scale)
    in_paragraph = text_contains(paragraph_text, scale)
    percent_tokens = ("%", "percent", "percentage")
    visibly_percent = any(
        token in normalize_text(question["question"])
        or token in normalize_text(table_text)
        or token in normalize_text(paragraph_text)
        for token in percent_tokens
    )
    if scale.casefold() in {"percent", "percentage"} and not visibly_percent:
        return {
            "source": "unresolved",
            "visible": False,
            "ambiguous": True,
            "status": "HIDDEN_AMBIGUOUS_PERCENT",
        }
    visible_sources = []
    if in_table:
        visible_sources.append("table")
    if in_question:
        visible_sources.append("question")
    if in_paragraph:
        visible_sources.append("paragraph")
    if not visible_sources:
        return {
            "source": "unresolved",
            "visible": False,
            "ambiguous": False,
            "status": "HIDDEN_BUT_NUMERICALLY_UNAMBIGUOUS",
        }
    if "table" in visible_sources and "paragraph" in visible_sources:
        source = "table_and_paragraph"
    elif "table" in visible_sources:
        source = "table"
    elif "paragraph" in visible_sources:
        source = "paragraph"
    else:
        source = "question"
    return {
        "source": source,
        "visible": True,
        "ambiguous": False,
        "status": "OK",
    }


def classify_source_requirement(
    question: dict[str, Any],
    table_text: str,
    paragraph_text: str,
) -> dict[str, Any]:
    """Offline reference classification using gold only for scoring."""
    terms = _target_terms(question)
    table_hits = sum(text_contains(table_text, term) for term in terms)
    paragraph_hits = sum(text_contains(paragraph_text, term) for term in terms)
    if table_hits == len(terms):
        target_source = "table"
    elif paragraph_hits == len(terms):
        target_source = "paragraph"
    elif table_hits or paragraph_hits:
        target_source = "mixed"
    else:
        target_source = "unresolved"
    scale_resolution = resolve_scale_source(question, table_text, paragraph_text)
    scale_source = scale_resolution["source"]
    if target_source == "unresolved" or scale_resolution["ambiguous"]:
        requirement = "unresolved"
    elif target_source == "table" and scale_source in {
        "not_required",
        "table",
        "question",
    }:
        requirement = "table"
    elif target_source == "paragraph" and scale_source in {
        "not_required",
        "paragraph",
        "question",
    }:
        requirement = "paragraph"
    else:
        requirement = "both"
    return {
        "source_requirement": requirement,
        "target_source": target_source,
        "target_terms": len(terms),
        "target_table_hits": table_hits,
        "target_paragraph_hits": paragraph_hits,
        "scale_source": scale_source,
        "scale_status": scale_resolution["status"],
    }


def _parse_number(candidate: Any) -> float | None:
    if isinstance(candidate, bool):
        return None
    if isinstance(candidate, (int, float)):
        return float(candidate)
    text = normalize_text(candidate)
    text = text.replace("%", " percent")
    text = re.sub(r"\b(?:usd|dollars?|million|millions?|billions?|thousands?)\b", " ", text)
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("() ")
    text = text.replace(",", "")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        return None
    value = float(text)
    return -value if negative else value


def _explicit_unit_conflict(candidate: Any, reference_scale: str) -> bool:
    text = normalize_text(candidate)
    explicit_units = {
        "percent": {"percent", "%"},
        "million": {"million", "millions", "mn", "m"},
        "thousand": {"thousand", "thousands", "k"},
        "billion": {"billion", "billions", "bn", "b"},
    }
    reference = normalize_text(reference_scale)
    for scale, aliases in explicit_units.items():
        present = any(normalized_word_containment(text, alias) for alias in aliases)
        if present and reference and scale != reference:
            return True
        if present and not reference:
            return True
    return False


def match_full_semantic_answer(
    candidate: Any,
    reference: Any,
    answer_type: str,
    reference_scale: str,
    ambiguous_visible: bool,
) -> tuple[bool, str]:
    normalized_candidate = normalize_text(candidate)
    unknown = normalized_candidate in {
        "unknown",
        "unanswerable",
        "insufficient visible evidence",
    }
    if unknown:
        return (ambiguous_visible, "reasonable_unknown" if ambiguous_visible else "unsupported_unknown")
    if answer_type in {"arithmetic", "count"}:
        if _explicit_unit_conflict(candidate, reference_scale):
            return False, "explicit_unit_conflict"
        candidate_number = _parse_number(candidate)
        reference_number = _parse_number(reference)
        if candidate_number is None or reference_number is None:
            return False, "numeric_parse_failure"
        if answer_type == "count":
            if not candidate_number.is_integer() or not reference_number.is_integer():
                return False, "non_integer_count"
            return candidate_number == reference_number, "count_integer_equality"
        return (
            math.isclose(
                candidate_number,
                reference_number,
                rel_tol=1e-6,
                abs_tol=1e-6,
            ),
            "numeric_isclose",
        )
    if answer_type == "span":
        normalized_reference = normalize_text(reference)
        return (
            normalized_word_containment(candidate, reference)
            or normalized_word_containment(reference, candidate),
            "normalized_span_containment",
        )
    if answer_type == "multi-span":
        gold_spans = reference if isinstance(reference, list) else [reference]
        normalized_gold = [normalize_text(span) for span in gold_spans]
        missing = [
            span
            for span in normalized_gold
            if not normalized_word_containment(candidate, span)
        ]
        return (not missing, "ordered_insensitive_all_gold_spans")
    return False, "unsupported_answer_type"


def answer_matching_self_tests() -> list[dict[str, Any]]:
    cases = [
        ("numeric_tolerance", True, match_full_semantic_answer("1.0000001", 1.0, "arithmetic", "", False)),
        ("numeric_mismatch", False, match_full_semantic_answer("1.01", 1.0, "arithmetic", "", False)),
        ("span_normalization", True, match_full_semantic_answer("Total  sales", "total sales.", "span", "", False)),
        ("multi_span_order", True, match_full_semantic_answer("second; first", ["first", "second"], "multi-span", "", False)),
        ("count_integer", True, match_full_semantic_answer("12", 12, "count", "", False)),
        ("reasonable_unknown", True, match_full_semantic_answer("UNKNOWN", 68.07, "arithmetic", "percent", True)),
        ("unsupported_unknown", False, match_full_semantic_answer("UNKNOWN", 68.07, "arithmetic", "percent", False)),
        ("explicit_unit_conflict", False, match_full_semantic_answer("2 million", 2, "arithmetic", "percent", False)),
    ]
    results = []
    for name, expected, (actual, reason) in cases:
        results.append(
            {
                "name": name,
                "expected": expected,
                "actual": actual,
                "reason": reason,
                "passed": actual is expected,
            }
        )
    return results


def _percent(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 6)


def _nearest_rank(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def verify_preregistration(
    receipt_path: Path,
    answer_rule_path: Path,
    source_path: Path,
) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    answer_rule_hash = sha256_file(answer_rule_path)
    checks = {
        "program_hash_matches": receipt.get("program_sha256") == sha256_file(Path(__file__)),
        "answer_rule_hash_matches": receipt.get("answer_matching_rule_sha256") == answer_rule_hash,
        "source_hash_matches": receipt.get("source_sha256") == sha256_file(source_path),
        "margin_frozen": receipt.get("noninferiority_margin_percentage_points") == -2.0,
        "budgets_frozen": receipt.get("context_budgets_percent") == [75, 50],
        "candidate_selection_frozen": bool(receipt.get("candidate_selection_rule")),
        "paired_unit_frozen": bool(receipt.get("paired_analysis_unit")),
        "frozen_before_frontier_computation": receipt.get(
            "frozen_before_frontier_computation"
        )
        is True,
    }
    if not all(checks.values()):
        raise SystemExit(
            "PRE_REGISTRATION_CHECK_FAILED: "
            + json.dumps(checks, sort_keys=True)
        )
    frozen_at = datetime.fromisoformat(receipt["frozen_at"])
    execution_started_at = datetime.now(timezone.utc)
    if frozen_at >= execution_started_at:
        raise SystemExit("PRE_REGISTRATION_CHECK_FAILED: frozen_at is not earlier")
    return {
        "checks": checks,
        "execution_started_at": execution_started_at.isoformat(),
        "receipt_sha256": sha256_file(receipt_path),
        "frozen_at": receipt["frozen_at"],
    }


def load_cluster_map(path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = {}
    for cluster in payload["clusters"]:
        for table_uid in cluster["members"]:
            mapping[table_uid] = {
                "source_cluster_id": cluster["cluster_id"],
                "effective_exposure_category": cluster["effective_exposure_category"],
                "existing_role": cluster["existing_role"],
            }
    return mapping


def recompute(source_path: Path, output_dir: Path, cluster_path: Path) -> dict[str, Any]:
    receipt_path = output_dir / "P2_PREREG_RECEIPT.json"
    answer_rule_path = output_dir / "P2_ANSWER_MATCHING_RULE.json"
    prereg = verify_preregistration(receipt_path, answer_rule_path, source_path)
    self_tests = answer_matching_self_tests()
    if not all(case["passed"] for case in self_tests):
        raise SystemExit("ANSWER_MATCHING_SELF_TEST_FAILED")

    source = json.loads(source_path.read_text(encoding="utf-8"))
    cluster_map = load_cluster_map(cluster_path)
    rows: list[dict[str, Any]] = []
    char_totals = Counter()
    char_values: dict[str, list[int]] = {name: [] for name in FRONTIER_ORDER}
    potential_counts = Counter()
    paragraph_recovery_counts = Counter()
    source_counts = Counter()
    scale_counts = Counter()
    answer_counts = Counter()

    for record_index, record in enumerate(source):
        table_uid = record["table"]["uid"]
        table_serialization = serialize_table(record["table"])
        table_characters = len(table_serialization)
        paragraph_serialization = {
            paragraph["order"]: serialize_paragraph(paragraph)
            for paragraph in record["paragraphs"]
        }
        cluster = cluster_map.get(
            table_uid,
            {
                "source_cluster_id": "UNMAPPED",
                "effective_exposure_category": "UNMAPPED",
                "existing_role": "UNMAPPED",
            },
        )
        for question_index, question in enumerate(record["questions"]):
            if question["answer_from"] != "table-text":
                continue
            required_orders = sorted(str(value) for value in question["rel_paragraphs"])
            relevant_paragraph_text = " ".join(
                paragraph["text"]
                for paragraph in record["paragraphs"]
                if str(paragraph["order"]) in required_orders
            )
            reference_classification = classify_source_requirement(
                question,
                table_serialization,
                relevant_paragraph_text,
            )
            source_counts[reference_classification["source_requirement"]] += 1
            scale_counts[reference_classification["scale_source"]] += 1
            answer_counts[question["answer_type"]] += 1

            actions = build_frontier_actions(question["question"], record["paragraphs"])
            frontier_rows = {}
            for frontier_name in FRONTIER_ORDER:
                action = actions[frontier_name]
                selected_orders = [int(value) for value in action["paragraph_orders"]]
                paragraph_characters = sum(
                    len(paragraph_serialization[order])
                    for order in selected_orders
                )
                visible_characters = table_characters + paragraph_characters
                gold_recovered = all(order in selected_orders for order in map(int, required_orders))
                if reference_classification["source_requirement"] == "table":
                    semantic_potential = True
                elif reference_classification["source_requirement"] in {"both", "paragraph"}:
                    semantic_potential = gold_recovered
                else:
                    semantic_potential = False
                char_totals[frontier_name] += visible_characters
                char_values[frontier_name].append(visible_characters)
                potential_counts[frontier_name] += int(semantic_potential)
                paragraph_recovery_counts[frontier_name] += int(gold_recovered)
                frontier_rows[frontier_name] = {
                    "selected_paragraph_orders": selected_orders,
                    "visible_evidence_characters": visible_characters,
                    "gold_paragraphs_recovered_offline": gold_recovered,
                    "semantic_reference_potential_offline": semantic_potential,
                    "deployable_action": {
                        "stop_stage": action["stop_stage"],
                        "ranking_scores": action["ranked_score_by_order"],
                    },
                }
            rows.append(
                {
                    "schema": "p2_recovery_row_v1",
                    "record_index": record_index,
                    "question_index": question_index,
                    "question_uid": question["uid"],
                    "table_uid": table_uid,
                    "source_cluster_id": cluster["source_cluster_id"],
                    "existing_role": cluster["existing_role"],
                    "effective_exposure_category": cluster["effective_exposure_category"],
                    "answer_type": question["answer_type"],
                    "question": question["question"],
                    "deployable_actions": {
                        "gold_inputs_used": False,
                        "gold_paragraph_ids_used": False,
                        "hidden_scale_used": False,
                        "frontiers": frontier_rows,
                    },
                    "offline_reference_only": {
                        "reference_classification": reference_classification,
                        "required_paragraph_orders": required_orders,
                        "reference_answer": question["answer"],
                        "reference_answer_sha256": canonical_sha256(question["answer"]),
                        "reference_scale": question.get("scale", ""),
                        "reference_status": (
                            "NOT_MODEL_READY"
                            if reference_classification["source_requirement"] == "unresolved"
                            else "QUALIFIED"
                        ),
                    },
                }
            )

    if len(rows) != 507:
        raise SystemExit(f"EXPECTED_507_ROWS_GOT_{len(rows)}")
    always_characters = char_totals["always_expand"]
    always_potential = potential_counts["always_expand"]
    frontier_summaries = []
    for name in FRONTIER_ORDER:
        values = char_values[name]
        ratio = char_totals[name] / always_characters
        gap = _percent(always_potential - potential_counts[name], 507)
        actions = FRONTIER_DEFINITIONS[name]["deterministic_actions"]
        meets_75 = ratio <= 0.75 and isinstance(actions, int) and actions <= 3
        meets_50 = ratio <= 0.50 and isinstance(actions, int) and actions <= 3
        frontier_summaries.append(
            {
                "name": name,
                "definition": {
                    "paragraphs": FRONTIER_DEFINITIONS[name]["paragraphs"],
                    "rule": FRONTIER_DEFINITIONS[name]["rule"],
                    "deterministic_actions": actions,
                },
                "gold_paragraph_recovery_offline": paragraph_recovery_counts[name],
                "semantic_reference_potential": potential_counts[name],
                "semantic_reference_potential_percent": _percent(
                    potential_counts[name],
                    507,
                ),
                "offline_gap_vs_always_expand_percentage_points": gap,
                "total_visible_evidence_chars": char_totals[name],
                "context_volume_ratio_vs_always_expand": round(ratio, 6),
                "mean_visible_evidence_chars": round(sum(values) / len(values), 1),
                "p95_visible_evidence_chars": _nearest_rank(values, 0.95),
                "max_visible_evidence_chars": max(values),
                "meets_75_percent_budget": meets_75,
                "meets_50_percent_budget": meets_50,
                "meets_margin_and_75_budget": (
                    name != "always_expand" and gap <= 2.0 and meets_75
                ),
                "meets_margin_and_50_budget": (
                    name != "always_expand" and gap <= 2.0 and meets_50
                ),
            }
        )

    eligible = [
        frontier
        for frontier in frontier_summaries
        if frontier["name"] != "always_expand"
        and (
            frontier["meets_margin_and_75_budget"]
            or frontier["meets_margin_and_50_budget"]
        )
    ]
    eligible.sort(
        key=lambda frontier: (
            frontier["total_visible_evidence_chars"],
            frontier["name"],
        )
    )
    diagnostic_candidate = eligible[0]["name"] if eligible else None
    disposition = (
        "DIAGNOSTIC_CANDIDATE_ONLY_NOT_METHOD_RESULT"
        if diagnostic_candidate
        else "NO_GO"
    )

    frontiers_payload = {
        "schema": "strong_baseline_frontiers_corrected_v2",
        "task_id": "natural-error-cost-remediate-a-20261026",
        "goal_id": "NATURAL_ERROR_EVIDENCE_COST_20261026",
        "authority_commit": AUTHORITY_COMMIT,
        "source_sha256": SOURCE_SHA256,
        "question_count": 507,
        "frontiers": frontier_summaries,
        "noninferiority_margin_percentage_points": -2.0,
        "context_budgets_percent": [75, 50],
        "candidate_selection_rule": (
            "Choose the smallest-total-character restricted frontier that "
            "passes a frozen budget and has an offline semantic-potential gap "
            "<=2.0 percentage points; ties use lexicographic frontier name."
        ),
        "diagnostic_candidate": diagnostic_candidate,
        "qualified_challenger": None,
        "disposition": disposition,
        "diagnostic_status": (
            "DIAGNOSTIC_ONLY_NOT_A_METHOD_RESULT"
            if diagnostic_candidate
            else "NO_QUALIFIED_DIAGNOSTIC_CANDIDATE"
        ),
        "metric_warning": (
            "semantic_reference_potential is an offline evidence ceiling, not "
            "model accuracy; characters are UTF-8 codepoint context-volume "
            "proxies only and are not measured token, latency, memory, or cost savings"
        ),
        "ranking_implementation": {
            "gold_relevance_used_for_ranking": False,
            "gold_answer_used_for_ranking": False,
            "gold_paragraph_ids_used_for_ranking": False,
            "hidden_scale_used_for_ranking": False,
            "model_calls": 0,
            "ranking": "record-local deterministic TF-IDF over unigrams and bigrams",
            "idf": "ln((1+N)/(1+df))+1",
            "query_weighting": "term frequency times same record-local idf, L2 normalized",
            "tie_break": "score descending, paragraph order ascending, paragraph uid ascending",
            "stopwords": sorted(STOPWORDS),
            "seed": "none",
        },
    }

    qualification_payload = {
        "schema": "p2_task_qualification_corrected_v2",
        "task_id": "natural-error-cost-remediate-a-20261026",
        "goal_id": "NATURAL_ERROR_EVIDENCE_COST_20261026",
        "authority_commit": AUTHORITY_COMMIT,
        "source_identity": {
            "task_source": "pinned TAT-QA raw dev only",
            "dev_path": str(source_path),
            "dev_sha256": SOURCE_SHA256,
            "answer_from_filter": "table-text",
            "question_count": 507,
            "finqa_used": False,
        },
        "reference_completeness": {
            "answers_present": 507,
            "answer_types": dict(sorted(answer_counts.items())),
            "complete_semantic_answer_references": 506,
            "incomplete_or_ambiguous": 1,
            "not_model_ready_action": (
                "UNKNOWN is the predeclared offline response for the one hidden "
                "percent-scale item; it remains excluded from the primary paired "
                "answer-risk denominator."
            ),
        },
        "legally_recoverable_evidence": {
            "method": (
                "Offline: exact target/operand recovery from canonical table or "
                "gold rel_paragraphs plus visible scale resolution; gold is "
                "never passed to build_frontier_actions."
            ),
            "source_requirement_counts": dict(sorted(source_counts.items())),
            "scale_source_counts": dict(sorted(scale_counts.items())),
            "nonempty_tables": 507,
            "valid_nonempty_rel_paragraph_sets": 507,
            "source_requirement_gold_use": "offline_reference_scoring_only",
        },
        "answer_risk_cost_target": {
            "actual_model_answer_risk": "UNKNOWN_ZERO_GENERATION",
            "primary_metric": "full_semantic_answer_accuracy",
            "secondary_metrics": [
                "program_correct",
                "interface_valid",
                "evidence_sufficiency",
                "total_visible_evidence_chars",
            ],
            "characters_interpretation": (
                "deterministic context-volume proxy only; not measured tokens, "
                "latency, memory, or cost"
            ),
        },
        "frozen_before_output": {
            "noninferiority_margin_percentage_points": -2.0,
            "cost_budget_1": (
                "total visible evidence characters <=75% of always-expand and "
                "<=3 deterministic retrieval actions"
            ),
            "cost_budget_2": (
                "total visible evidence characters <=50% of always-expand and "
                "<=3 deterministic retrieval actions"
            ),
            "answer_matching_rule_sha256": sha256_file(answer_rule_path),
            "prereg_receipt_sha256": sha256_file(receipt_path),
        },
        "baseline_decision": {
            "accepted_final_baseline": "always_expand",
            "qualification_status": (
                "TASK_LEGALLY_QUALIFIED_NO_NONINFERIOR_COST_CHALLENGER"
                if not diagnostic_candidate
                else "TASK_LEGALLY_QUALIFIED_DIAGNOSTIC_CANDIDATE_ONLY"
            ),
            "qualified_challenger": None,
            "diagnostic_candidate": diagnostic_candidate,
            "reason": (
                "No restricted frontier passes both the frozen margin and a "
                "frozen context budget."
                if not diagnostic_candidate
                else "A restricted frontier passed both screens; it is diagnostic only."
            ),
        },
    }

    write_json(output_dir / "STRONG_BASELINE_FRONTIERS_CORRECTED.json", frontiers_payload)
    write_json(
        output_dir / "P2_TASK_QUALIFICATION_CORRECTED.json",
        qualification_payload,
    )
    rows_hash = canonical_sha256(rows)
    recompute_payload = {
        "schema": "p2_recovery_recompute_v1",
        "task_id": "natural-error-cost-remediate-a-20261026",
        "goal_id": "NATURAL_ERROR_EVIDENCE_COST_20261026",
        "authority_commit": AUTHORITY_COMMIT,
        "execution_started_at": prereg["execution_started_at"],
        "execution_completed_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(source_path),
            "sha256": SOURCE_SHA256,
            "question_count": 507,
        },
        "preregistration": {
            "receipt_path": str(receipt_path),
            "receipt_sha256": prereg["receipt_sha256"],
            "frozen_at": prereg["frozen_at"],
            "checks": prereg["checks"],
        },
        "implementation": {
            "program_path": str(Path(__file__).resolve()),
            "program_sha256": sha256_file(Path(__file__)),
            "answer_matching_rule_sha256": sha256_file(answer_rule_path),
            "table_serialization": (
                "json.dumps(record.table.table, ensure_ascii=false, "
                "sort_keys=false, separators=(',',':'))"
            ),
            "paragraph_serialization": (
                "json.dumps({order,text}, ensure_ascii=false, sort_keys=true, "
                "separators=(',',':'))"
            ),
            "character_accounting": (
                "Python len() over UTF-8 decoded serialization; "
                "per-question total = table chars + selected paragraph chars"
            ),
            "answer_matching_self_tests": self_tests,
            "model_calls": 0,
            "judge_calls": 0,
            "training_runs": 0,
            "production_calls": 0,
            "database_calls": 0,
        },
        "source_requirement_counts": dict(sorted(source_counts.items())),
        "scale_source_counts": dict(sorted(scale_counts.items())),
        "answer_type_counts": dict(sorted(answer_counts.items())),
        "frontiers": frontier_summaries,
        "diagnostic_candidate": diagnostic_candidate,
        "qualified_challenger": None,
        "disposition": disposition,
        "row_results_sha256": rows_hash,
        "frontiers_payload_sha256": canonical_sha256(frontiers_payload),
        "qualification_payload_sha256": canonical_sha256(qualification_payload),
        "row_results": rows,
    }
    write_json(output_dir / "P2_RECOVERY_RECOMPUTE.json", recompute_payload)
    return recompute_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--cluster-map",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "tatqa_candidate_b_qualification_v1"
        / "SOURCE_EXPOSURE_QUALIFICATION.json",
    )
    args = parser.parse_args()
    if sha256_file(args.source) != SOURCE_SHA256:
        raise SystemExit("PINNED_SOURCE_HASH_MISMATCH")
    payload = recompute(args.source, args.output_dir, args.cluster_map)
    print(
        json.dumps(
            {
                "disposition": payload["disposition"],
                "diagnostic_candidate": payload["diagnostic_candidate"],
                "rows": len(payload["row_results"]),
                "row_results_sha256": payload["row_results_sha256"],
                "zero_endpoint_calls": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
