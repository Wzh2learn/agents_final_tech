#!/usr/bin/env python3
"""Read-only feasibility audit for overlapping FinQA E/P/N signatures."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from research.finqa_numeric_token_canonicalization_v2 import (
    numeric_tokens as canonical_numeric_tokens,
)


ROOT = Path(__file__).resolve().parents[2]
STAGING = Path("/home/testuser/wzh/phase1a_staging_20260925/finqa")
OUT_JSON = ROOT / "research/stage_e_multileaf_20261010/finqa_v2_overlap_feasibility.json"
OUT_MD = ROOT / "docs/research/finqa_v2_overlap_feasibility_v1.md"

FILES = (STAGING / "train.json", STAGING / "dev.json")
TARGET_CLUSTERS_PER_STAGE = 24


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def op_family(op: str) -> str:
    match = re.match(r"^([A-Za-z_]+?)(?:\d*)-(?:\d+)$", str(op))
    return match.group(1) if match else str(op)


numeric_tokens = canonical_numeric_tokens


def report_cluster(record: dict[str, Any]) -> str:
    filename = str(record.get("filename") or record.get("id") or "")
    return filename.split("/page_", 1)[0]


def load_records() -> list[dict[str, Any]]:
    rows = []
    for path in FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload:
            source_split = "train" if path.name == "train.json" else "dev"
            rows.append({**record, "_source_split": source_split})
    return rows


def analyze() -> dict[str, Any]:
    rows = load_records()
    details = []
    for record in rows:
        qa = record.get("qa") or {}
        steps = qa.get("steps") or []
        gold_inds = qa.get("gold_inds") or {}
        evidence_text = " ".join(str(value) for value in gold_inds.values())
        evidence_tokens = numeric_tokens(evidence_text)
        cluster = report_cluster(record)
        families = [op_family(step.get("op", "")) for step in steps]
        p_candidates = [
            index for index, family in enumerate(families)
            if family in {"add", "minus", "multiply", "divide"}
        ]
        n_candidates = []
        e1_overlap = []
        for index, step in enumerate(steps):
            args = [step.get("arg1", ""), step.get("arg2", "")]
            arg_tokens = set().union(*(numeric_tokens(arg) for arg in args))
            if any(str(arg).startswith("#") or str(arg).startswith("const_") or numeric_tokens(arg) for arg in args):
                n_candidates.append(index)
            if arg_tokens & evidence_tokens:
                e1_overlap.append(index)
        e_candidate = bool(gold_inds) and bool(qa.get("model_input"))
        details.append({
            "id": str(record.get("id")),
            "source_split": record["_source_split"],
            "report_cluster": cluster,
            "n_steps": len(steps),
            "e_candidate": e_candidate,
            "p_candidate": bool(p_candidates),
            "n_candidate": bool(n_candidates),
            "e1_n_overlap": bool(e1_overlap),
            "p_n_overlap": bool(p_candidates and n_candidates),
            "op_families": families,
            "gold_evidence_count": len(gold_inds),
            "numeric_arg_evidence_overlap_count": len(e1_overlap),
        })

    def cluster_count(predicate) -> int:
        return len({row["report_cluster"] for row in details if predicate(row)})

    counts = {
        "records": len(details),
        "report_clusters": len({row["report_cluster"] for row in details}),
        "multi_step_records": sum(row["n_steps"] >= 2 for row in details),
        "E_records": sum(row["e_candidate"] for row in details),
        "P_records": sum(row["p_candidate"] for row in details),
        "N_records": sum(row["n_candidate"] for row in details),
        "E1_N_overlap_records": sum(row["e1_n_overlap"] for row in details),
        "P_N_overlap_records": sum(row["p_n_overlap"] for row in details),
        "E_clusters": cluster_count(lambda row: row["e_candidate"]),
        "P_clusters": cluster_count(lambda row: row["p_candidate"]),
        "N_clusters": cluster_count(lambda row: row["n_candidate"]),
        "E1_N_overlap_clusters": cluster_count(lambda row: row["e1_n_overlap"]),
        "P_N_overlap_clusters": cluster_count(lambda row: row["p_n_overlap"]),
        "E1_N_overlap_clusters_with_multi_step": cluster_count(
            lambda row: row["e1_n_overlap"] and row["n_steps"] >= 2
        ),
        "P_N_overlap_clusters_with_multi_step": cluster_count(
            lambda row: row["p_n_overlap"] and row["n_steps"] >= 2
        ),
    }
    status = (
        "OVERLAP_DESIGN_FEASIBLE"
        if counts["E1_N_overlap_clusters_with_multi_step"] >= TARGET_CLUSTERS_PER_STAGE
        and counts["P_N_overlap_clusters_with_multi_step"] >= TARGET_CLUSTERS_PER_STAGE
        else "NO_GO_FOR_TARGET_OVERLAP_DESIGN"
    )
    return {
        "namespace": "FINQA_V2_OVERLAP_FEASIBILITY",
        "status": status,
        "target_clusters_per_stage": TARGET_CLUSTERS_PER_STAGE,
        "source_files": {
            str(path): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in FILES
        },
        "counts": counts,
        "op_family_counts": dict(sorted(Counter(
            family for row in details for family in row["op_families"] if row["n_steps"] >= 2
        ).items())),
        "details_sample": details[:20],
        "interpretation": {
            "E1_definition": "a numeric token in a program argument also occurs in the gold evidence text",
            "P_N_overlap_definition": "at least one arithmetic step and one argument/reference candidate coexist",
            "warning": "numeric-string overlap is a feasibility proxy, not a causal evidence-to-argument join",
        },
    }


def render(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    return f"""# FinQA v2 Overlap Feasibility Audit v1

> Status: `{payload['status']}` | Read-only eligibility count; no adapter or evaluator execution

## 1. Counts

| Quantity | Count |
|---|---:|
| Records | {counts['records']} |
| Report clusters | {counts['report_clusters']} |
| Multi-step records | {counts['multi_step_records']} |
| E candidates | {counts['E_records']} |
| P candidates | {counts['P_records']} |
| N candidates | {counts['N_records']} |
| E1/N overlap records | {counts['E1_N_overlap_records']} |
| P/N overlap records | {counts['P_N_overlap_records']} |
| E1/N overlap clusters | {counts['E1_N_overlap_clusters']} |
| P/N overlap clusters | {counts['P_N_overlap_clusters']} |
| E1/N overlap multi-step clusters | {counts['E1_N_overlap_clusters_with_multi_step']} |
| P/N overlap multi-step clusters | {counts['P_N_overlap_clusters_with_multi_step']} |

## 2. Decision

Target is at least {payload['target_clusters_per_stage']} independent report clusters per stage with overlapping signatures.

`{payload['status']}`.

The E1 join rule is only a numeric-token feasibility proxy. A causal evidence-to-argument mapping must be frozen separately before any v2 execution. If the overlap counts are below target, do not weaken the overlap criterion or remove ambiguous samples.

## 3. Op families in multi-step subset

`{payload['op_family_counts']}`

## 4. Boundary

This is not a FinQA performance result, not a Stage E replication, and not a second-flow experiment. It only determines whether the proposed overlapping design is constructible from the approved staging data.
"""


def main() -> int:
    payload = analyze()
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": payload["status"],
        "counts": payload["counts"],
        "output": str(OUT_MD),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if payload["status"] == "OVERLAP_DESIGN_FEASIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
