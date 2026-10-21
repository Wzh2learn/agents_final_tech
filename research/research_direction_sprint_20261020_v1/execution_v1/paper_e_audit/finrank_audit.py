#!/usr/bin/env python3
"""Deterministic audit probes for the pinned FinRank release.

The script imports the official FinRank metric and corpus functions. It does
not edit the vendored release and does not make model or judge requests.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor" / "FinRank"
DATA = VENDOR / "FinRank.jsonl"
OFFICIAL_RESULTS = VENDOR / "baselines" / "results" / "results.json"
REPRO = ROOT / "reproduced_official" / "skip_neural"
OUTPUTS = ROOT / "outputs"


def load_official() -> Any:
    """Load the pinned official run_baselines.py without modifying it."""
    path = VENDOR / "baselines" / "run_baselines.py"
    spec = importlib.util.spec_from_file_location("finrank_official_baselines", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pair_stats(
    gold_scores: Iterable[float], negative_scores: Iterable[float]
) -> dict[str, float | int | None]:
    """Count ordered gold-negative pairs under exact official score equality."""
    gold = [float(x) for x in gold_scores]
    negative = [float(x) for x in negative_scores]
    wins = ties = losses = 0
    for g in gold:
        for n in negative:
            if g > n:
                wins += 1
            elif g == n:
                ties += 1
            else:
                losses += 1
    total = wins + ties + losses
    strict_den = wins + losses
    return {
        "pairs": total,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "accuracy_ties_positive": (wins + ties) / total if total else float("nan"),
        "accuracy_strict": wins / total if total else float("nan"),
        "accuracy_ties_half": (wins + 0.5 * ties) / total if total else float("nan"),
        "accuracy_ties_excluded": wins / strict_den if strict_den else None,
    }


def ranked_metrics(gold_flags: np.ndarray) -> tuple[float, float]:
    """Compute the official MRR and nDCG@5 formulas for one ranking."""
    hits = np.asarray(gold_flags, dtype=bool)
    first = np.flatnonzero(hits)
    mrr = 1.0 / (first[0] + 1) if len(first) else 0.0
    dcg = sum(1.0 / np.log2(r + 2) for r in np.flatnonzero(hits[:5]))
    idcg = sum(1.0 / np.log2(r + 2) for r in range(min(int(hits.sum()), 5)))
    return float(mrr), float(dcg / idcg if idcg else 0.0)


def inrec_tie_variants(
    gold_scores: Iterable[float], negative_scores: Iterable[float]
) -> dict[str, float]:
    """Compare gold-first and negative-first ordering within exact ties."""
    gold = np.asarray(list(gold_scores), dtype=float)
    negative = np.asarray(list(negative_scores), dtype=float)

    def run(gold_first: bool) -> tuple[float, float]:
        candidates = [
            (float(score), 0 if gold_first else 1, True)
            for score in gold
        ] + [
            (float(score), 1 if gold_first else 0, False)
            for score in negative
        ]
        candidates.sort(key=lambda row: (-row[0], row[1]))
        return ranked_metrics(np.asarray([row[2] for row in candidates]))

    best_mrr, best_ndcg = run(True)
    worst_mrr, worst_ndcg = run(False)
    return {
        "mrr_gold_first_ties": best_mrr,
        "ndcg_gold_first_ties": best_ndcg,
        "mrr_negative_first_ties": worst_mrr,
        "ndcg_negative_first_ties": worst_ndcg,
        "mrr_tie_sensitivity": best_mrr - worst_mrr,
        "ndcg_tie_sensitivity": best_ndcg - worst_ndcg,
    }


def macro(values: Iterable[float | None]) -> float:
    clean = [
        float(value)
        for value in values
        if value is not None and np.isfinite(value)
    ]
    return float(np.mean(clean)) if clean else float("nan")


def fixture_results(official: Any) -> dict[str, Any]:
    """Run synthetic positive, negative, tie, permutation and identity fixtures."""
    positive = pair_stats([2.0], [1.0])
    negative = pair_stats([1.0], [2.0])
    tie = pair_stats([0.0], [0.0])
    all_tie = inrec_tie_variants([0.0], [0.0, 0.0])

    scores = np.asarray([0.0, 0.0, 0.0])
    candidate_order_a = np.asarray([0, 1, 2])
    candidate_order_b = np.asarray([2, 1, 0])
    ranking_a = candidate_order_a[np.argsort(-scores, kind="stable")]
    ranking_b = candidate_order_b[np.argsort(-scores, kind="stable")]
    gold_a = {2}
    gold_b = {2}
    global_a = official.per_record_metrics(ranking_a, gold_a)
    global_b = official.per_record_metrics(ranking_b, gold_b)

    source_fixture = [
        {
            "ticker": "AAA",
            "year": "2025",
            "doc_type": "10-K",
            "passages": [{"text": "shared text"}],
            "hard_negatives": [],
        },
        {
            "ticker": "BBB",
            "year": "2024",
            "doc_type": "10-Q",
            "passages": [{"text": "shared text"}],
            "hard_negatives": [],
        },
    ]
    texts, metadata, index = official.build_corpus(source_fixture)
    fixture = {
        "schema": "finrank-audit-fixtures-v1",
        "pairwise": {
            "positive_gold_above_negative": positive,
            "negative_gold_below_negative": negative,
            "equal_zero_scores": tie,
            "expectations": {
                "positive_ties_positive": 1.0,
                "negative_ties_positive": 0.0,
                "zero_tie_ties_positive": 1.0,
                "zero_tie_strict": 0.0,
                "zero_tie_half": 0.5,
            },
        },
        "inrecord_all_ties": all_tie,
        "global_candidate_permutation": {
            "forward": global_a,
            "reversed": global_b,
            "same_metrics": global_a == global_b,
        },
        "source_first_occurrence": {
            "unique_texts": len(texts),
            "metadata": [list(row) for row in metadata],
            "shared_text_index": index["shared text"],
            "both_records_map_to_first_metadata": (
                metadata[index["shared text"]] == ("AAA", "2025", "10-K")
            ),
        },
    }

    expected = fixture["pairwise"]["expectations"]
    checks = {
        "positive_pair": positive["accuracy_ties_positive"] == expected["positive_ties_positive"],
        "negative_pair": negative["accuracy_ties_positive"] == expected["negative_ties_positive"],
        "tie_positive_policy": tie["accuracy_ties_positive"] == expected["zero_tie_ties_positive"],
        "tie_strict_policy": tie["accuracy_strict"] == expected["zero_tie_strict"],
        "tie_half_policy": tie["accuracy_ties_half"] == expected["zero_tie_half"],
        "all_tie_inrecord_is_perfect_under_gold_first": all_tie["mrr_gold_first_ties"] == 1.0,
        "global_permutation_can_change_tied_ranking": not fixture["global_candidate_permutation"]["same_metrics"],
        "source_identity_collapses_to_first_metadata": fixture["source_first_occurrence"]["both_records_map_to_first_metadata"],
    }
    fixture["checks"] = checks
    fixture["all_checks_pass"] = all(checks.values())
    return fixture


def source_identity_audit(
    official: Any, records: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    texts, metadata, index = official.build_corpus(records)
    taxonomy = read_json(VENDOR / "hn_taxonomy.json")
    taxonomy_overlap = {
        row["passage_id"]: len(row.get("overlaps_gold_of", []))
        for row in taxonomy
        if row.get("overlaps_gold_of")
    }
    gold_ids = [
        {index[p["text"]] for p in record["passages"] if str(p["text"]).strip()}
        for record in records
    ]
    hn_ids = [
        [index[h["text"]] for h in record["hard_negatives"] if str(h["text"]).strip()]
        for record in records
    ]

    text_gold_records: dict[str, set[str]] = defaultdict(set)
    text_hn_records: dict[str, set[str]] = defaultdict(set)
    trimmed_gold_records: dict[str, set[str]] = defaultdict(set)
    trimmed_hn_records: dict[str, set[str]] = defaultdict(set)
    sha_gold_records: dict[str, set[str]] = defaultdict(set)
    sha_hn_records: dict[str, set[str]] = defaultdict(set)
    text_sources: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for record in records:
        record_key = (
            str(record.get("ticker", "")),
            str(record.get("year", "")),
            str(record.get("doc_type", "")),
        )
        for passage in record["passages"]:
            text_gold_records[passage["text"]].add(record["id"])
            trimmed_gold_records[str(passage["text"]).strip()].add(record["id"])
            sha_gold_records[str(passage.get("text_sha1", ""))].add(record["id"])
            text_sources[passage["text"]].add(record_key)
        for negative in record["hard_negatives"]:
            text_hn_records[negative["text"]].add(record["id"])
            trimmed_hn_records[str(negative["text"]).strip()].add(record["id"])
            sha_hn_records[str(negative.get("text_sha1", ""))].add(record["id"])
            text_sources[negative["text"]].add(
                (
                    str(negative.get("ticker", "")),
                    str(negative.get("year", "")),
                    str(negative.get("doc_type", "")),
                )
            )

    overlap_texts = set(text_gold_records) & set(text_hn_records)
    trimmed_overlap_texts = set(trimmed_gold_records) & set(trimmed_hn_records)
    sha_overlap_ids = set(sha_gold_records) & set(sha_hn_records)
    overlap_hn_occurrences = sum(
        1
        for record in records
        for negative in record["hard_negatives"]
        if negative["text"] in text_gold_records
    )
    overlap_hn_records = {
        record["id"]
        for record in records
        if any(negative["text"] in text_gold_records for negative in record["hard_negatives"])
    }
    trimmed_overlap_hn_occurrences = sum(
        1
        for record in records
        for negative in record["hard_negatives"]
        if str(negative["text"]).strip() in trimmed_gold_records
    )
    trimmed_overlap_hn_records = {
        record["id"]
        for record in records
        if any(
            str(negative["text"]).strip() in trimmed_gold_records
            for negative in record["hard_negatives"]
        )
    }
    sha_overlap_hn_occurrences = sum(
        1
        for record in records
        for negative in record["hard_negatives"]
        if str(negative.get("text_sha1", "")) in sha_gold_records
    )
    sha_overlap_hn_records = {
        record["id"]
        for record in records
        if any(
            str(negative.get("text_sha1", "")) in sha_gold_records
            for negative in record["hard_negatives"]
        )
    }

    record_rows: list[dict[str, Any]] = []
    for i, record in enumerate(records):
        key = (
            str(record.get("ticker", "")),
            str(record.get("year", "")),
            str(record.get("doc_type", "")),
        )
        allowed = {
            corpus_id
            for corpus_id, meta in enumerate(metadata)
            if tuple(meta) == key
        }
        gold = gold_ids[i]
        kept = gold & allowed
        hard = set(hn_ids[i])
        record_rows.append(
            {
                "record_id": record["id"],
                "gold_count": len(gold),
                "hard_negative_count": len(hard),
                "gold_lost_any": bool(gold - allowed),
                "gold_lost_all": bool(gold and not kept),
                "hard_negative_eliminated_fraction": (
                    1.0 - len(hard & allowed) / len(hard) if hard else None
                ),
                "first_occurrence_candidates": len(allowed),
                "shared_gold_hn_text_count": sum(
                    1
                    for negative in record["hard_negatives"]
                    if negative["text"] in text_gold_records
                ),
                "shared_gold_hn_trimmed_count": sum(
                    1
                    for negative in record["hard_negatives"]
                    if str(negative["text"]).strip() in trimmed_gold_records
                ),
                "shared_gold_hn_sha1_count": sum(
                    1
                    for negative in record["hard_negatives"]
                    if str(negative.get("text_sha1", "")) in sha_gold_records
                ),
                "taxonomy_overlap_gold_count": sum(
                    taxonomy_overlap.get(negative.get("passage_id", ""), 0)
                    for negative in record["hard_negatives"]
                ),
            }
        )

    lost_any = sum(row["gold_lost_any"] for row in record_rows)
    lost_all = sum(row["gold_lost_all"] for row in record_rows)
    eliminated = [
        row["hard_negative_eliminated_fraction"]
        for row in record_rows
        if row["hard_negative_eliminated_fraction"] is not None
    ]
    return (
        {
            "corpus_nonempty_occurrences": sum(
                len(record["passages"]) + len(record["hard_negatives"])
                for record in records
            ),
            "corpus_unique_raw_text": len(texts),
            "corpus_unique_trimmed_text": len(
                {str(text).strip() for text in text_texts(records)}
            ),
            "texts_with_multiple_source_identities": sum(
                len(sources) > 1 for sources in text_sources.values()
            ),
            "cross_role_raw_exact_text_count": len(overlap_texts),
            "cross_role_raw_exact_hn_occurrences": overlap_hn_occurrences,
            "cross_role_raw_exact_hn_record_count": len(overlap_hn_records),
            "cross_role_trimmed_text_count": len(trimmed_overlap_texts),
            "cross_role_trimmed_hn_occurrences": trimmed_overlap_hn_occurrences,
            "cross_role_trimmed_hn_record_count": len(trimmed_overlap_hn_records),
            "cross_role_sha1_text_count": len(sha_overlap_ids),
            "cross_role_sha1_hn_occurrences": sha_overlap_hn_occurrences,
            "cross_role_sha1_hn_record_count": len(sha_overlap_hn_records),
            "cross_role_taxonomy_hn_occurrences": len(taxonomy_overlap),
            "cross_role_taxonomy_hn_record_count": len(
                {row["record_id"] for row in taxonomy if row.get("overlaps_gold_of")}
            ),
            "records_losing_any_gold": lost_any,
            "records_losing_all_golds": lost_all,
            "mean_hard_negatives_eliminated_pct": 100.0 * macro(eliminated),
            "mean_first_occurrence_candidates": macro(
                row["first_occurrence_candidates"] for row in record_rows
            ),
        },
        record_rows,
    )


def text_texts(records: list[dict[str, Any]]) -> list[str]:
    return [
        item["text"]
        for record in records
        for item in record["passages"] + record["hard_negatives"]
    ]


def random_negatives(
    official: Any,
    records: list[dict[str, Any]],
    gold_ids: list[set[int]],
    hn_ids: list[list[int]],
    corpus_size: int,
) -> list[np.ndarray]:
    rng = np.random.default_rng(official.SEED)
    sampled: list[np.ndarray] = []
    for i in range(len(records)):
        pool = np.setdiff1d(
            np.arange(corpus_size), np.asarray(sorted(gold_ids[i]), dtype=int)
        )
        sampled.append(
            rng.choice(pool, size=max(len(hn_ids[i]), 1), replace=False)
        )
    return sampled


def global_tie_order_metrics(
    official: Any,
    scores: np.ndarray,
    gold_ids: list[set[int]],
) -> dict[str, Any]:
    corpus_size = scores.shape[1]
    base = np.arange(corpus_size)
    forward_rows = []
    reverse_rows = []
    changed = []
    for i, row in enumerate(scores):
        forward = np.lexsort((base, -row))
        reverse = np.lexsort((-base, -row))
        f_metrics = official.per_record_metrics(forward, gold_ids[i])
        r_metrics = official.per_record_metrics(reverse, gold_ids[i])
        forward_rows.append(f_metrics)
        reverse_rows.append(r_metrics)
        if f_metrics != r_metrics:
            changed.append(i)
    return {
        "records_changed": len(changed),
        "changed_record_indices": changed[:50],
        "forward": {
            key: official.aggregate(forward_rows, key) for key in forward_rows[0]
        },
        "reverse": {
            key: official.aggregate(reverse_rows, key) for key in reverse_rows[0]
        },
        "difference_reverse_minus_forward": {
            key: official.aggregate(reverse_rows, key)
            - official.aggregate(forward_rows, key)
            for key in forward_rows[0]
        },
    }


def application_results(official: Any) -> dict[str, Any]:
    records = official.load_records(DATA)
    texts, metadata, index = official.build_corpus(records)
    gold_ids = [
        {index[p["text"]] for p in record["passages"] if str(p["text"]).strip()}
        for record in records
    ]
    hn_ids = [
        [index[h["text"]] for h in record["hard_negatives"] if str(h["text"]).strip()]
        for record in records
    ]
    sampled = random_negatives(
        official, records, gold_ids, hn_ids, len(texts)
    )
    source, record_rows = source_identity_audit(official, records)

    repair_log = read_json(VENDOR / "repair_log.json")
    official_results = read_json(OFFICIAL_RESULTS)
    cache = np.load(REPRO / "score_cache.npz")
    models: dict[str, Any] = {}
    for model in ("tfidf", "bm25"):
        matrix = cache[f"s_{model}"]
        hard_stats = []
        random_stats = []
        inrecord_stats = []
        random_hard_overlap = []
        for i in range(len(records)):
            gold_scores = matrix[i, sorted(gold_ids[i])]
            hard_scores = matrix[i, hn_ids[i]] if hn_ids[i] else np.asarray([])
            random_scores = matrix[i, sampled[i]]
            hard_stats.append(pair_stats(gold_scores, hard_scores))
            random_stats.append(pair_stats(gold_scores, random_scores))
            inrecord_stats.append(
                {
                    **inrec_tie_variants(gold_scores, hard_scores),
                    **{
                        f"official_{key}": value
                        for key, value in zip(
                            ("mrr", "ndcg"),
                            official.inrec_metrics(gold_scores, hard_scores),
                        )
                    },
                }
            )
            random_hard_overlap.append(
                {
                    "record_id": records[i]["id"],
                    "sampled_random_count": len(set(sampled[i].tolist())),
                    "random_hard_overlap_ids": len(
                        set(sampled[i].tolist()) & set(hn_ids[i])
                    ),
                }
            )

        def aggregate_pair(rows: list[dict[str, Any]]) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for key in (
                "accuracy_ties_positive",
                "accuracy_strict",
                "accuracy_ties_half",
                "accuracy_ties_excluded",
            ):
                out[key] = 100.0 * macro(row[key] for row in rows)
            out["pairs"] = sum(row["pairs"] for row in rows)
            out["wins"] = sum(row["wins"] for row in rows)
            out["ties"] = sum(row["ties"] for row in rows)
            out["losses"] = sum(row["losses"] for row in rows)
            out["records_with_ties"] = sum(row["ties"] > 0 for row in rows)
            return out

        hard_aggregate = aggregate_pair(hard_stats)
        random_aggregate = aggregate_pair(random_stats)
        random_aggregate["gap_random_minus_hard_ties_positive"] = (
            random_aggregate["accuracy_ties_positive"]
            - hard_aggregate["accuracy_ties_positive"]
        )
        random_aggregate["gap_random_minus_hard_strict"] = (
            random_aggregate["accuracy_strict"]
            - hard_aggregate["accuracy_strict"]
        )
        random_aggregate["gap_random_minus_hard_ties_half"] = (
            random_aggregate["accuracy_ties_half"]
            - hard_aggregate["accuracy_ties_half"]
        )

        models[model] = {
            "hard_negative_pairwise": hard_aggregate,
            "random_negative_pairwise": random_aggregate,
            "inrecord": {
                key: 100.0 * macro(row[key] for row in inrecord_stats)
                for key in (
                    "official_mrr",
                    "official_ndcg",
                    "mrr_gold_first_ties",
                    "mrr_negative_first_ties",
                    "ndcg_gold_first_ties",
                    "ndcg_negative_first_ties",
                    "mrr_tie_sensitivity",
                    "ndcg_tie_sensitivity",
                )
            },
            "inrecord_records_with_gold_negative_ties": sum(
                row["mrr_tie_sensitivity"] > 0 or row["ndcg_tie_sensitivity"] > 0
                for row in inrecord_stats
            ),
            "global_tie_order": global_tie_order_metrics(
                official, matrix, gold_ids
            ),
            "random_sampling": {
                "records_with_random_hard_overlap": sum(
                    row["random_hard_overlap_ids"] > 0 for row in random_hard_overlap
                ),
                "random_draws_equal_to_hard_negative": sum(
                    row["random_hard_overlap_ids"] for row in random_hard_overlap
                ),
            },
            "official_result_subset": {
                key: official_results["models"][model][key]
                for key in (
                    "recall@1",
                    "recall@5",
                    "recall@10",
                    "recall@20",
                    "mrr",
                    "ndcg@10",
                    "inrec_mrr",
                    "inrec_ndcg@5",
                    "hn_acc",
                    "rand_acc",
                )
            },
        }

        for i, row in enumerate(record_rows):
            row[f"{model}_hard_pairs"] = hard_stats[i]
            row[f"{model}_random_pairs"] = random_stats[i]
            row[f"{model}_inrecord"] = inrecord_stats[i]
            row[f"{model}_random_hard_overlap_ids"] = random_hard_overlap[i][
                "random_hard_overlap_ids"
            ]

    result = {
        "schema": "finrank-external-audit-application-v1",
        "status": "DETERMINISTIC_OFFLINE_APPLICATION_COMPLETE",
        "model_requests": 0,
        "judge_requests": 0,
        "training_requests": 0,
        "records": len(records),
        "source_identity": source,
        "repair_log": {
            "change_entries": len(repair_log.get("changes", [])),
            "qid_label_mismatches": len(repair_log.get("qid_label_mismatches", [])),
            "removed_hard_negatives": len(repair_log.get("removed_hns", [])),
            "removed_records": len(repair_log.get("removed_records", [])),
        },
        "identity_document_discrepancies": {
            "paper_and_results_corpus_size": official_results["corpus_size"],
            "readme_claimed_corpus_entries": 5270,
            "readme_matches_recomputed_corpus": 5270 == len(texts),
        },
        "models": models,
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with (OUTPUTS / "APPLICATION_RECORDS.jsonl").open("w", encoding="utf-8") as handle:
        for row in record_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return result


def source_manifest() -> dict[str, Any]:
    paths = [
        DATA,
        VENDOR / "README.md",
        VENDOR / "LICENSE",
        VENDOR / "baselines" / "run_baselines.py",
        VENDOR / "baselines" / "run_extra_retrievers.py",
        VENDOR / "baselines" / "validate_release.py",
        VENDOR / "baselines" / "results" / "results.json",
        VENDOR / "baselines" / "results" / "extra_retrievers.json",
        VENDOR / "hn_taxonomy.json",
        VENDOR / "repair_log.json",
        VENDOR / "summary.json",
        ROOT / "evidence" / "finrank_2608.07400v1.pdf",
        ROOT / "evidence" / "finrank_arxiv_record.xml",
    ]
    return {
        "upstream": "https://github.com/datanxt/FinRank",
        "revision": "916dc27e77b90e294ea1b3a2cc5b0abcf07392d1",
        "arxiv_record": "2608.07400v1",
        "files": [
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in paths
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("manifest", "fixtures", "apply"))
    args = parser.parse_args()
    official = load_official()
    if args.mode == "manifest":
        result = source_manifest()
        path = OUTPUTS / "SOURCE_MANIFEST.json"
    elif args.mode == "fixtures":
        result = fixture_results(official)
        path = OUTPUTS / "FIXTURE_RESULTS.json"
    else:
        result = application_results(official)
        path = OUTPUTS / "APPLICATION_RESULTS.json"
    write_json(path, result)
    print(json.dumps({"output": str(path), "status": result.get("status", "COMPLETE")}, indent=2))


if __name__ == "__main__":
    main()
