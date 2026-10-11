#!/usr/bin/env python3
"""Freeze outcome-blind FinQA v2 candidate sample IDs without running an experiment."""
from __future__ import annotations

import hashlib
import json
import re
import sys

from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.finqa_evidence_argument_resolver_v2 import (
    EvidenceArgumentResolverError,
    resolve_numeric_argument,
)
from research.finqa_numeric_token_canonicalization_v2 import (
    try_canonical_numeric_token,
)


ROOT = Path(__file__).resolve().parents[2]
STAGING = Path("/home/testuser/wzh/phase1a_staging_20260925/finqa")
FILES = (STAGING / "train.json", STAGING / "dev.json")
OUT_JSON = ROOT / "research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json"
OUT_MD = ROOT / "docs/research/finqa_v2_candidate_sample_manifest_v1.md"

SEED = 20261015
CLUSTERS_PER_STAGE = 24
INJECTIONS_PER_CLUSTER = 3
OP_RE = re.compile(r"^([A-Za-z_]+?)(\d*)-(\d+)$")
OP_REPLACEMENT = {"add": "minus", "minus": "add", "multiply": "divide", "divide": "multiply"}
EXPECTED_CHECKPOINT = {
    "E": "evidence.required_hit",
    "P": "program.operator_consistency",
    "N": "program.argument_consistency",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_rank(namespace: str, key: str) -> str:
    return sha256_text(f"{SEED}:{namespace}:{key}")


def op_parts(op: str) -> tuple[str, str, str]:
    match = OP_RE.match(str(op or ""))
    if not match:
        return "", "", ""
    return match.group(1), match.group(2), match.group(3)


def numeric_literal(value: Any) -> bool:
    return try_canonical_numeric_token(value) is not None


def load_records() -> list[dict[str, Any]]:
    rows = []
    for path in FILES:
        split = "train" if path.name == "train.json" else "dev"
        for record in json.loads(path.read_text(encoding="utf-8")):
            cluster = str(record.get("filename") or record.get("id") or "").split("/page_", 1)[0]
            rows.append({
                "record_id": str(record.get("id")),
                "source_split": split,
                "report_cluster": cluster,
                "record_sha256": sha256_text(canonical_json(record)),
                "question_sha256": sha256_text(canonical_json((record.get("qa") or {}).get("question"))),
                "qa": record.get("qa") or {},
            })
    return rows


def candidate_events(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {"E": [], "P": [], "N": []}
    for record in records:
        qa = record["qa"]
        steps = qa.get("steps") or []
        if len(steps) < 2:
            continue
        gold_inds = qa.get("gold_inds") or {}
        base = {
            "source_split": record["source_split"],
            "report_cluster": record["report_cluster"],
            "record_id": record["record_id"],
            "record_sha256": record["record_sha256"],
            "question_sha256": record["question_sha256"],
            "n_steps": len(steps),
        }
        for step_index, step in enumerate(steps):
            for arg_name in ("arg1", "arg2"):
                argument = step.get(arg_name)
                if not numeric_literal(argument):
                    continue
                try:
                    join = resolve_numeric_argument(argument, gold_inds)
                except EvidenceArgumentResolverError:
                    join = None
                if join is not None:
                    events["E"].append({
                        **base,
                        "event_key": f"E:{record['record_id']}:{step_index}:{arg_name}:{join['evidence_id']}",
                        "step_index": step_index,
                        "arg_name": arg_name,
                        "argument_before": str(argument),
                        "required_evidence_id": join["evidence_id"],
                        "operation": "remove_unique_required_evidence_block_from_candidate_bundle",
                        "expected_first_stage": "E",
                        "expected_first_checkpoint": EXPECTED_CHECKPOINT["E"],
                        "join": join,
                    })
                events["N"].append({
                    **base,
                    "event_key": f"N:{record['record_id']}:{step_index}:{arg_name}",
                    "step_index": step_index,
                    "arg_name": arg_name,
                    "argument_before": str(argument),
                    "operation": "mutate_numeric_literal_argument_by_fixed_nonzero_delta",
                    "expected_first_stage": "N",
                    "expected_first_checkpoint": EXPECTED_CHECKPOINT["N"],
                    "join_status": "UNIQUE" if join is not None else "NONE_OR_AMBIGUOUS",
                })
            family, variant, position = op_parts(step.get("op"))
            if family in OP_REPLACEMENT:
                replacement = f"{OP_REPLACEMENT[family]}{variant}-{position}"
                events["P"].append({
                    **base,
                    "event_key": f"P:{record['record_id']}:{step_index}",
                    "step_index": step_index,
                    "op_before": str(step.get("op")),
                    "op_after": replacement,
                    "operation": "replace_operator_with_fixed_same_arity_counterpart",
                    "expected_first_stage": "P",
                    "expected_first_checkpoint": EXPECTED_CHECKPOINT["P"],
                })
    return events


def select_manifest(events: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    by_cluster: dict[str, dict[str, list[dict[str, Any]]]] = {
        stage: defaultdict(list) for stage in ("E", "P", "N")
    }
    for stage, rows in events.items():
        for row in rows:
            by_cluster[stage][row["report_cluster"]].append(row)

    used_clusters: set[str] = set()
    selected: dict[str, list[dict[str, Any]]] = {"E": [], "P": [], "N": []}
    selection_counts = {}
    for stage in ("E", "P", "N"):
        eligible_clusters = [
            cluster for cluster, rows in by_cluster[stage].items()
            if cluster not in used_clusters and len(rows) >= INJECTIONS_PER_CLUSTER
        ]
        eligible_clusters.sort(key=lambda cluster: stable_rank(f"{stage}-cluster", cluster))
        chosen_clusters = eligible_clusters[:CLUSTERS_PER_STAGE]
        selection_counts[stage] = {
            "eligible_clusters_after_disjointness": len(eligible_clusters),
            "selected_clusters": len(chosen_clusters),
        }
        used_clusters.update(chosen_clusters)
        for cluster in chosen_clusters:
            rows = sorted(by_cluster[stage][cluster], key=lambda row: stable_rank(f"{stage}-event", row["event_key"]))
            for repeat, event in enumerate(rows[:INJECTIONS_PER_CLUSTER], start=1):
                sample_id = f"FINQA-V2-{stage}-{sha256_text(cluster)[:12]}-{sha256_text(event['event_key'])[:12]}"
                selected[stage].append({
                    **event,
                    "sample_id": sample_id,
                    "cluster_id": f"{stage}:{cluster}",
                    "repeat_within_cluster": repeat,
                    "split_role": "NOT_YET_FROZEN",
                    "id_provenance": "DERIVED_OUTCOME_BLIND_CANDIDATE",
                })
    return selected, selection_counts


def main() -> int:
    records = load_records()
    events = candidate_events(records)
    selected, selection_counts = select_manifest(events)
    counts = {
        stage: {
            "clusters": len({row["cluster_id"] for row in rows}),
            "injections": len(rows),
        }
        for stage, rows in selected.items()
    }
    complete = all(
        counts[stage]["clusters"] == CLUSTERS_PER_STAGE
        and counts[stage]["injections"] == CLUSTERS_PER_STAGE * INJECTIONS_PER_CLUSTER
        for stage in ("E", "P", "N")
    )
    payload = {
        "namespace": "FINQA_V2_CANDIDATE_SAMPLE_MANIFEST",
        "status": "CANDIDATE_SAMPLE_IDS_FROZEN_NOT_EXECUTION" if complete else "CANDIDATE_SAMPLE_IDS_INCOMPLETE",
        "seed": SEED,
        "selection_rule": "ascending SHA-256 rank; stages consume disjoint report clusters; no evaluator output is read",
        "source_files": {
            str(path): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in FILES
        },
        "target": {
            "clusters_per_stage": CLUSTERS_PER_STAGE,
            "injections_per_cluster": INJECTIONS_PER_CLUSTER,
        },
        "candidate_event_counts": {stage: len(rows) for stage, rows in events.items()},
        "selection_counts": selection_counts,
        "counts": counts,
        "samples": selected,
        "gate_interpretation": {
            "ID_GO": "PASS_CANDIDATE_IDS_FROZEN_NOT_EXECUTION" if complete else "BLOCKED_INCOMPLETE",
            "JOIN_GO": "PASS_RESOLVER_AND_CANDIDATES_NOT_FORMAL",
            "SPLIT_GO": "BLOCKED_SPLIT_ROLE_NOT_FROZEN",
            "PREREG_GO": "BLOCKED_UNTIL_SCORER_AND_SPLIT_FREEZE",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = "\n".join(
        f"| {stage} | {counts[stage]['clusters']} | {counts[stage]['injections']} | "
        f"{selection_counts[stage]['eligible_clusters_after_disjointness']} |"
        for stage in ("E", "P", "N")
    )
    OUT_MD.write_text(f"""# FinQA v2 Candidate Sample Manifest v1

> Status: `{payload['status']}` | Outcome-blind candidate IDs only | No formal FinQA execution

## 1. Counts

| Stage | Selected clusters | Selected injections | Eligible clusters after disjointness |
|---|---:|---:|---:|
{rows}

Stages consume disjoint report clusters. Each selected cluster has exactly three candidate injections.

## 2. Frozen operations

- `E`: remove the uniquely resolved required evidence block from the candidate evidence bundle.
- `P`: replace an add/minus/multiply/divide operator with its fixed same-arity counterpart.
- `N`: mutate one numeric literal argument by a fixed nonzero delta.

Expected first checkpoints are frozen as `evidence.required_hit`, `program.operator_consistency`, and `program.argument_consistency`.

## 3. Gate status

| Gate | Status |
|---|---|
| ID_GO | `{payload['gate_interpretation']['ID_GO']}` |
| JOIN_GO | `{payload['gate_interpretation']['JOIN_GO']}` |
| SPLIT_GO | `{payload['gate_interpretation']['SPLIT_GO']}` |
| PREREG_GO | `{payload['gate_interpretation']['PREREG_GO']}` |

`FACT`: exact candidate IDs and operations are frozen without reading evaluator output.

`BLOCKER`: split roles are not frozen. This manifest is not authorization to execute the second-flow experiment.

## 4. Mechanism boundary

These IDs do not create multiple mutation mechanisms per stage. Mechanism generalization remains `NOT_IDENTIFIED`.
""", encoding="utf-8", newline="\n")
    print(json.dumps({"status": payload["status"], "counts": counts, "output": str(OUT_MD)}, ensure_ascii=False, sort_keys=True))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
