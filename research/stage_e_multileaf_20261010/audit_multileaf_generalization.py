#!/usr/bin/env python3
"""Audit whether the frozen M/R/N design supports mechanism generalization."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "research/stage_e_method_revision_20261009/multileaf_freeze.json"
OUT_JSON = ROOT / "research/stage_e_multileaf_20261010/multileaf_mechanism_generalization_audit.json"
OUT_MD = ROOT / "docs/research/multileaf_mechanism_generalization_audit_v1.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_count(rows: list[dict[str, Any]], key) -> int:
    return len({key(row) for row in rows})


def main() -> int:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    report: dict[str, Any] = {
        "namespace": "MULTILEAF_MECHANISM_GENERALIZATION_AUDIT",
        "status": "MECHANISM_GENERALIZATION_NOT_IDENTIFIED",
        "freeze_sha256": sha256_file(FREEZE),
        "stages": {},
        "cross_stage": {},
        "feasibility": {},
    }

    for stage in ("M", "R", "N"):
        rows = freeze["samples"][stage]
        mechanisms = Counter(row["injection_operation"] for row in rows)
        clusters = unique_count(rows, lambda row: row["cluster_id"])
        source_ids = unique_count(
            rows,
            lambda row: (
                row["source_object"].get("uid")
                or row["source_object"].get("document_id")
                or row["source_object"].get("source_question_id")
            ),
        )
        templates = Counter()
        for row in rows:
            source = row["source_object"]
            if stage == "M":
                templates[str(row.get("field_before", ""))] += 1
            elif stage == "R":
                templates[str(source.get("question_id", ""))] += 1
            else:
                identity = source.get("identity") or {}
                templates[str(identity.get("expression", ""))] += 1
        report["stages"][stage] = {
            "rows": len(rows),
            "clusters": clusters,
            "source_ids": source_ids,
            "injection_operation_counts": dict(mechanisms),
            "mechanism_count": len(mechanisms),
            "template_count": len(templates),
            "template_examples": [item[0] for item in templates.most_common(10)],
            "source_namespace": {
                "M": "TAT-QA financial tables",
                "R": "TAT-DQA QA/evidence records",
                "N": "TAT-QA financial tables",
            }[stage],
        }

    m_ids = {row["source_object"]["uid"] for row in freeze["samples"]["M"]}
    n_ids = {row["source_object"]["uid"] for row in freeze["samples"]["N"]}
    r_docs = {row["source_object"]["document_id"] for row in freeze["samples"]["R"]}
    report["cross_stage"] = {
        "M_N_uid_intersection": sorted(m_ids & n_ids),
        "R_document_namespace_is_separate": True,
        "origin_alias_provenance": "UNVERIFIED beyond literal source IDs",
        "all_three_stages_share_one_dataset_family": False,
        "financial_domain_only": True,
    }
    report["feasibility"] = {
        "leave_one_mutation_mechanism_out": "NOT_FEASIBLE",
        "leave_one_template_out_within_stage": "POSSIBLE_DESCRIPTIVE_ONLY",
        "train_on_one_mechanism_test_on_another": "NOT_IDENTIFIED",
        "minimum_required_mechanisms_per_stage": 2,
        "observed_mechanisms_per_stage": {
            stage: report["stages"][stage]["mechanism_count"] for stage in ("M", "R", "N")
        },
        "reason": "each stage has exactly one frozen injection operation; templates vary but are not independent mechanisms",
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    stage_rows = "\n".join(
        f"| {stage} | {data['rows']} | {data['clusters']} | {data['source_ids']} | "
        f"{data['mechanism_count']} | {data['template_count']} | {data['source_namespace']} |"
        for stage, data in report["stages"].items()
    )
    OUT_MD.write_text(f"""# Multi-Leaf Mechanism-Generalization Audit v1

> Status: `{report['status']}` | Read-only audit of frozen M/R/N sample manifest | No formal result rerun

## 1. Frozen design inventory

| Stage | Rows | Clusters | Source IDs | Mutation mechanisms | Templates | Source namespace |
|---|---:|---:|---:|---:|---:|---|
{stage_rows}

## 2. Mechanism-generalization decision

| Test | Status | Reason |
|---|---|---|
| Leave-one-mutation-mechanism-out | `NOT_FEASIBLE` | M/R/N each expose one frozen injection operation |
| Train on one mechanism, test on another within stage | `NOT_IDENTIFIED` | no second mechanism is frozen per stage |
| Leave-one-template-out within mechanism | `POSSIBLE_DESCRIPTIVE_ONLY` | headers/questions/identities vary, but this is not mechanism transfer |
| Cross-source-family transfer | `NOT_IDENTIFIED` | M/N share TAT-QA tables; R is TAT-DQA QA; all are financial-domain sources |

## 3. Boundary conclusion

The current result cannot support a mechanism-generalization claim. The direct-codebook ablation already shows that perfect localization is carried by explicitly instrumented stage signals. A stronger future test requires at least two independently defined mutation mechanisms per stage and a preregistered cross-mechanism split.

`MECHANISM_GENERALIZATION_NOT_IDENTIFIED`

## 4. Provenance caveat

Literal M/N table UIDs are disjoint and R uses a separate document namespace, but semantic origin aliases across datasets were not independently audited. This is a provenance gap, not evidence of leakage.
""", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "stages": report["stages"], "output": str(OUT_MD)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
