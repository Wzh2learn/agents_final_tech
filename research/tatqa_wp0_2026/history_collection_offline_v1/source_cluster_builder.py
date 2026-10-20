#!/usr/bin/env python3
"""Build conservative source clusters from complete TAT-QA raw records."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from offline_core import canonical_json, jaccard, record_vectors


THRESHOLDS = {
    "table_near_duplicate": 0.95,
    "paragraph_near_duplicate": 0.90,
    "joint_table": 0.85,
    "joint_paragraph": 0.75,
    "conflict_table": 0.95,
    "conflict_paragraph": 0.50,
    "paragraph_reuse_table_divergence": 0.50,
}


def load_raw_records(train_path: Path, dev_path: Path) -> list[dict[str, Any]]:
    records = []
    for split, path in (("train", train_path), ("dev", dev_path)):
        for record in json.loads(path.read_text(encoding="utf-8")):
            item = dict(record)
            item["_split"] = split
            records.append(item)
    return records


def record_id(record: dict[str, Any]) -> str:
    return str(record["table"]["uid"])


def report_identity(record: dict[str, Any]) -> str | None:
    table = record.get("table", {})
    return record.get("report_id") or table.get("report_id") or table.get("source_document_id")


def association_reasons(
    left: dict[str, Any],
    right: dict[str, Any],
    left_vectors: tuple[set[str], set[str]],
    right_vectors: tuple[set[str], set[str]],
    left_identity: tuple[str, str, str | None],
    right_identity: tuple[str, str, str | None],
) -> list[dict[str, Any]]:
    reasons = []
    left_table_json, left_paragraphs_json, left_report = left_identity
    right_table_json, right_paragraphs_json, right_report = right_identity
    if left_report and right_report and left_report == right_report:
        reasons.append({"kind": "report_id", "value": left_report})
    if left_table_json == right_table_json:
        reasons.append({"kind": "exact_table", "value": "canonical_json"})
    if left_paragraphs_json == right_paragraphs_json:
        reasons.append({"kind": "exact_paragraphs", "value": "canonical_json"})

    left_table, left_paragraphs = left_vectors
    right_table, right_paragraphs = right_vectors
    table_similarity = jaccard(left_table, right_table)
    paragraph_similarity = jaccard(left_paragraphs, right_paragraphs)
    if table_similarity >= THRESHOLDS["table_near_duplicate"]:
        reasons.append({"kind": "table_near_duplicate", "similarity": table_similarity})
    if paragraph_similarity >= THRESHOLDS["paragraph_near_duplicate"]:
        reasons.append({"kind": "paragraph_near_duplicate", "similarity": paragraph_similarity})
    if (
        table_similarity >= THRESHOLDS["joint_table"]
        and paragraph_similarity >= THRESHOLDS["joint_paragraph"]
    ):
        reasons.append({
            "kind": "joint_near_duplicate",
            "table_similarity": table_similarity,
            "paragraph_similarity": paragraph_similarity,
        })
    if (
        table_similarity >= THRESHOLDS["conflict_table"]
        and paragraph_similarity < THRESHOLDS["conflict_paragraph"]
    ):
        reasons.append({
            "kind": "table_reuse_paragraph_divergence",
            "table_similarity": table_similarity,
            "paragraph_similarity": paragraph_similarity,
        })
    if (
        paragraph_similarity >= THRESHOLDS["paragraph_near_duplicate"]
        and table_similarity < THRESHOLDS["paragraph_reuse_table_divergence"]
    ):
        reasons.append({
            "kind": "paragraph_reuse_table_divergence",
            "table_similarity": table_similarity,
            "paragraph_similarity": paragraph_similarity,
        })
    return reasons


def build_clusters(records: list[dict[str, Any]]) -> dict[str, Any]:
    identifiers = [record_id(record) for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate record uid")
    record_by_id = {record_id(record): record for record in records}
    vectors = {record_id(record): record_vectors(record) for record in records}
    identities = {
        record_id(record): (
            canonical_json(record["table"]["table"]),
            canonical_json(record.get("paragraphs", [])),
            report_identity(record),
        )
        for record in records
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    edges = []
    for left_index, left in enumerate(records):
        left_id = identifiers[left_index]
        for right_index in range(left_index):
            right_id = identifiers[right_index]
            reasons = association_reasons(
                left,
                records[right_index],
                vectors[left_id],
                vectors[right_id],
                identities[left_id],
                identities[right_id],
            )
            if not reasons:
                continue
            adjacency[left_id].add(right_id)
            adjacency[right_id].add(left_id)
            edges.append({
                "left": left_id,
                "right": right_id,
                "reasons": reasons,
            })

    components = []
    seen = set()
    for uid in identifiers:
        if uid in seen:
            continue
        stack = [uid]
        seen.add(uid)
        component = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbour in adjacency[current]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        components.append(sorted(component))
    components.sort(key=lambda members: members[0])
    clusters = []
    for index, members in enumerate(components, start=1):
        clusters.append({
            "cluster_id": f"cluster_{index:04d}",
            "member_count": len(members),
            "members": members,
            "report_identity_count": len({
                value for value in (
                    report_identity(record_by_id[uid]) for uid in members
                ) if value
            }),
        })
    return {
        "schema": "tq_source_cluster_graph_v1",
        "thresholds": THRESHOLDS,
        "normalization": {
            "unicode": "NFKC",
            "case": "lower",
            "whitespace": "collapse",
            "signs_and_punctuation": "preserved",
            "ngram_size": 5,
            "empty_text": "exact_identity_only",
            "text_shorter_than_ngram": "exact_whole_string_only",
        },
        "record_count": len(records),
        "edge_count": len(edges),
        "cluster_count": len(clusters),
        "edges": edges,
        "clusters": clusters,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    records = load_raw_records(args.train, args.dev)
    result = build_clusters(records)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "records": result["record_count"],
        "edges": result["edge_count"],
        "clusters": result["cluster_count"],
        "output": str(args.output),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
