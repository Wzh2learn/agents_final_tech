#!/usr/bin/env python3
"""Audit whether FinQA supports a causal evidence-to-argument join."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.finqa_numeric_token_canonicalization_v2 import (
    numeric_tokens,
    try_canonical_numeric_token,
)


STAGING = Path("/home/testuser/wzh/phase1a_staging_20260925/finqa")
FILES = (STAGING / "train.json", STAGING / "dev.json")
OUT_JSON = ROOT / "research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json"
OUT_MD = ROOT / "docs/research/finqa_v2_causal_join_audit_v1.md"
TARGET_CLUSTERS = 24


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal_arg(value: Any) -> str | None:
    return try_canonical_numeric_token(value)


def evidence_for_token(token: str, gold_inds: dict[str, Any]) -> list[str]:
    return sorted(
        evidence_id
        for evidence_id, text in gold_inds.items()
        if token in numeric_tokens(text)
    )


def load_records() -> list[dict[str, Any]]:
    rows = []
    for path in FILES:
        source_split = "train" if path.name == "train.json" else "dev"
        for record in json.loads(path.read_text(encoding="utf-8")):
            rows.append({**record, "_source_split": source_split})
    return rows


def analyze() -> dict[str, Any]:
    rows = load_records()
    details = []
    for record in rows:
        qa = record.get("qa") or {}
        steps = qa.get("steps") or []
        gold_inds = qa.get("gold_inds") or {}
        filename = str(record.get("filename") or record.get("id") or "")
        cluster = filename.split("/page_", 1)[0]
        joins = []
        for step_index, step in enumerate(steps):
            for arg_name in ("arg1", "arg2"):
                token = literal_arg(step.get(arg_name))
                if token is None:
                    continue
                evidence_ids = evidence_for_token(token, gold_inds)
                joins.append({
                    "step_index": step_index,
                    "arg_name": arg_name,
                    "token": token,
                    "evidence_ids": evidence_ids,
                    "unique_join": len(evidence_ids) == 1,
                    "join_evidence_id": evidence_ids[0] if len(evidence_ids) == 1 else None,
                })
        unique_joins = [join for join in joins if join["unique_join"]]
        details.append({
            "id": str(record.get("id")),
            "source_split": record["_source_split"],
            "report_cluster": cluster,
            "n_steps": len(steps),
            "gold_evidence_count": len(gold_inds),
            "literal_arg_count": len(joins),
            "unique_join_count": len(unique_joins),
            "joins": joins,
        })

    unique_rows = [row for row in details if row["unique_join_count"] > 0]
    unique_clusters = {row["report_cluster"] for row in unique_rows}
    multi_step_unique_rows = [row for row in unique_rows if row["n_steps"] >= 2]
    multi_step_unique_clusters = {row["report_cluster"] for row in multi_step_unique_rows}
    join_counts = Counter(
        join["unique_join"]
        for row in details
        for join in row["joins"]
    )
    status = "JOIN_CANDIDATE_IDENTIFIED_NOT_FROZEN" if len(multi_step_unique_clusters) >= TARGET_CLUSTERS else "JOIN_GO_BLOCKED"
    return {
        "namespace": "FINQA_V2_CAUSAL_JOIN_AUDIT",
        "status": status,
        "target_unique_clusters": TARGET_CLUSTERS,
        "source_files": {
            str(path): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in FILES
        },
        "counts": {
            "records": len(details),
            "report_clusters": len({row["report_cluster"] for row in details}),
            "rows_with_any_literal_arg": sum(row["literal_arg_count"] > 0 for row in details),
            "rows_with_unique_join": len(unique_rows),
            "rows_with_unique_join_and_multi_step": len(multi_step_unique_rows),
            "clusters_with_unique_join": len(unique_clusters),
            "clusters_with_unique_join_and_multi_step": len(multi_step_unique_clusters),
            "literal_join_events": sum(row["literal_arg_count"] for row in details),
            "unique_join_events": sum(row["unique_join_count"] for row in details),
            "unique_join_event_counts": dict(join_counts),
        },
        "join_rule": {
            "definition": "a numeric literal argument token occurs in exactly one qa.gold_inds evidence text",
            "causal_test": "the resolver returns that token with the evidence present and returns UNRESOLVED after removing that evidence",
            "limitation": "lexical evidence-to-argument join, not native pipeline provenance; resolver contract must be frozen",
        },
        "gate_interpretation": {
            "SOURCE_GO": "PASS_SOURCE_IDENTITY_AND_HASHES",
            "JOIN_GO": "PASS_CANDIDATE_NOT_FROZEN" if status.startswith("JOIN_CANDIDATE") else "BLOCKED",
            "ID_GO": "BLOCKED_EXACT_SAMPLE_IDS_NOT_FROZEN",
            "SPLIT_GO": "BLOCKED_ROLE_SCOPE_NOT_FROZEN",
            "SCORER_GO": "BLOCKED_INDEPENDENT_SCORER_NOT_LINKED_TO_EXACT_IDS",
            "PREREG_GO": "BLOCKED_PENDING_JOING_GO_ID_GO_SPLIT_GO_SCORER_GO",
        },
        "examples": details[:12],
    }


def render(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    gates = payload["gate_interpretation"]
    return f"""# FinQA v2 Causal Evidence-to-Argument Join Audit v1

> Status: `{payload['status']}` | Read-only feasibility audit | No FinQA adapter or formal experiment

## 1. Counts

| Quantity | Count |
|---|---:|
| Records | {counts['records']} |
| Report clusters | {counts['report_clusters']} |
| Rows with literal program arguments | {counts['rows_with_any_literal_arg']} |
| Rows with at least one unique evidence join | {counts['rows_with_unique_join']} |
| Multi-step rows with unique join | {counts['rows_with_unique_join_and_multi_step']} |
| Clusters with unique join | {counts['clusters_with_unique_join']} |
| Multi-step clusters with unique join | {counts['clusters_with_unique_join_and_multi_step']} |
| Literal argument events | {counts['literal_join_events']} |
| Unique evidence-join events | {counts['unique_join_events']} |

## 2. Join definition

A candidate causal join exists when a numeric literal program argument token occurs in exactly one `qa.gold_inds` evidence text. The future resolver contract must return that argument with the evidence present and return `UNRESOLVED` after removing that evidence.

This is a lexical, deterministic join candidate. It is not native pipeline provenance; the resolver semantics and exact sample manifest still need to be frozen.

## 3. Six-gate status

| Gate | Status |
|---|---|
| SOURCE_GO | `{gates['SOURCE_GO']}` |
| ID_GO | `{gates['ID_GO']}` |
| JOIN_GO | `{gates['JOIN_GO']}` |
| SPLIT_GO | `{gates['SPLIT_GO']}` |
| SCORER_GO | `{gates['SCORER_GO']}` |
| PREREG_GO | `{gates['PREREG_GO']}` |

## 4. Decision

`SECOND_FLOW_BLOCKED` until the causal resolver, exact IDs, role/split scope and independent scorer are frozen. Do not treat the numeric-token count as proof of semantic evidence use.
"""


def main() -> int:
    payload = analyze()
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({"status": payload["status"], "counts": payload["counts"], "output": str(OUT_MD)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
