#!/usr/bin/env python3
"""Create the immutable Stage E multi-leaf pre-result freeze receipt."""
from __future__ import annotations

import hashlib
import os
import json
import platform
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_multileaf_20261010"
FREEZE = ROOT / "research/stage_e_method_revision_20261009/multileaf_freeze.json"
PREREG = ROOT / "docs/research/stage_e_multileaf_preregistration_v1.md"
POWER_PLAN = ROOT / "docs/research/stage_e_multileaf_power_plan_v1.md"
RUNNER = TASK / "run_multileaf_formal.py"
BUILDER = TASK / "build_multileaf_preresult_freeze.py"
CONTRACT_TEST = ROOT / "tests/test_multileaf_formal_contract.py"
RESULTS_DIR = TASK / "results"

SAMPLE_MANIFEST = TASK / "multileaf_preresult_sample_manifest.json"
ENVIRONMENT = TASK / "multileaf_environment_snapshot.json"
GIT_DIFF = TASK / "multileaf_preresult_git_diff.patch"
MANIFEST = TASK / "multileaf_preresult_freeze_manifest.json"
MANIFEST_HASH = TASK / "multileaf_preresult_freeze_manifest.sha256"
RECEIPT = ROOT / "docs/research/multileaf_preresult_freeze_receipt_v1.md"

TATQA_FILES = (
    Path("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_train.json"),
    Path("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json"),
    Path("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_test_gold.json"),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout


def task_card_section(text: str) -> str:
    match = re.search(
        r"(## 8\. Formal execution task card.*?)(?=\n## 9\.)",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError("formal execution task card section not found")
    return match.group(1)


def freeze_file_record(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_sample_manifest(freeze: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for stage in ("M", "R", "N"):
        for sample in freeze["samples"][stage]:
            source = sample["source_object"]
            rows.append({
                "sample_id": sample["sample_id"],
                "cluster_id": sample["cluster_id"],
                "stage": stage,
                "repeat_within_cluster": sample["repeat_within_cluster"],
                "expected_first_affected_stage": sample["expected_first_affected_stage"],
                "expected_first_checkpoint": sample["expected_first_checkpoint"],
                "direct_target_leaf": sample["direct_target_leaf"],
                "injection_operation": sample["injection_operation"],
                "injection_location": sample["injection_location"],
                "source_uid": source.get("uid"),
                "source_document_id": source.get("document_id"),
                "source_question_id": source.get("question_id"),
                "source_cell": source.get("cell"),
                "source_table_sha256": source.get("table_sha256"),
                "identity_expression": (source.get("identity") or {}).get("expression"),
            })
    return {
        "namespace": "MULTILEAF_PRERESULT_SAMPLE_MANIFEST",
        "status": "FREEZE_COMPLETE",
        "selection_seed": freeze["selection_seed"],
        "selection_rule": freeze["selection_rule"],
        "counts": freeze["counts"],
        "rows": rows,
    }


def build_environment() -> dict[str, Any]:
    return {
        "captured_at": now_iso(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "packages": {
            "numpy": numpy.__version__,
        },
        "git": {
            "head": run_git("rev-parse", "HEAD").strip(),
            "status_porcelain_sha256": hashlib.sha256(
                run_git("status", "--porcelain=v1").encode("utf-8")
            ).hexdigest(),
        },
    }


def main() -> int:
    if RESULTS_DIR.exists():
        raise RuntimeError("formal results already exist; pre-result freeze is no longer possible")

    prereg_text = PREREG.read_text(encoding="utf-8")
    task_card = task_card_section(prereg_text)
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))

    sample_payload = build_sample_manifest(freeze)
    SAMPLE_MANIFEST.write_text(
        json.dumps(sample_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    environment = build_environment()
    ENVIRONMENT.write_text(
        json.dumps(environment, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    git_diff = run_git("diff", "--binary")
    GIT_DIFF.write_text(git_diff, encoding="utf-8", newline="\n")

    frozen_paths = [
        PREREG,
        POWER_PLAN,
        FREEZE,
        SAMPLE_MANIFEST,
        RUNNER,
        BUILDER,
        CONTRACT_TEST,
        ROOT / "config/eval_checkpoint_trees.json",
        ROOT / "data/research/drift_v0/input/tatqa_tables.json",
        *TATQA_FILES,
    ]
    frozen_files = {
        display_path(path): freeze_file_record(path)
        for path in frozen_paths
    }

    freeze_inputs = freeze["predictor_contract"]
    manifest = {
        "namespace": "MULTILEAF_PRERESULT_FREEZE",
        "status": "FREEZE_COMPLETE",
        "captured_at": now_iso(),
        "temporal_order": "FREEZE_COMPLETE -> materialize formal evaluator outputs",
        "result_artifacts_absent_at_freeze": True,
        "formal_runner": freeze_file_record(RUNNER),
        "task_card": {
            "source": display_path(PREREG),
            "section": "## 8. Formal execution task card",
            "sha256": hashlib.sha256(task_card.encode("utf-8")).hexdigest(),
            "text": task_card,
        },
        "sample_manifest": freeze_file_record(SAMPLE_MANIFEST),
        "expected_stage_rule": freeze["selection_rule"],
        "expected_checkpoint_contract": {
            stage: {
                "expected_first_checkpoint": freeze["samples"][stage][0]["expected_first_checkpoint"],
                "direct_target_leaf": freeze["samples"][stage][0]["direct_target_leaf"],
            }
            for stage in ("M", "R", "N")
        },
        "predictor_contract": {
            "input": freeze_inputs["input"],
            "classifier": freeze_inputs["classifier"],
            "classes": freeze_inputs["classes"],
            "primary_metrics": freeze_inputs["primary_metrics"],
            "tie_rule": freeze_inputs["tie_rule"],
            "loco_rule": "leave one stage-namespaced table/document/origin cluster out; all three repeated injections stay in the held-out fold",
            "chance_top1": freeze_inputs["chance_top1"],
            "majority_baseline": freeze_inputs["majority_baseline"],
            "signature_separability": freeze_inputs["signature_separability"],
            "permutation_seed": freeze_inputs["permutation_seed"],
            "permutation_replicates": freeze_inputs["permutation_replicates"],
            "bootstrap_seed": freeze_inputs["bootstrap_seed"],
            "bootstrap_replicates": freeze_inputs["bootstrap_replicates"],
        },
        "sample_size_tier": {
            "tier": "TARGET",
            "clusters_per_stage": 24,
            "injections_per_cluster": 3,
            "total_clusters": 72,
            "total_injections": 216,
            "claim_scope": "pooled/macro localization only",
        },
        "stop_conditions": [
            "Any M/R/N stage contract fails: STOP_THAT_STAGE and classify confirmatory result INVALID.",
            "Any UID/origin leakage or fold contamination: classify INVALID.",
            "Fewer than two population-responsive leaves: localization remains unestablished.",
            "Expected-stage or predictor definitions change after result access: classify INVALID.",
            "Any flat/hierarchy secondary result cannot overwrite the primary localization result.",
        ],
        "secondary_flat_hierarchy_contract": {
            "flat_score": "10 * mean(full binary response vector)",
            "hierarchical_score": "10 * weighted sum(full binary response vector) using effective checkpoint-tree leaf weights",
            "diagnostics": [
                "Pearson and Spearman relation",
                "linear affine fit and residual",
                "score supports",
                "clean-versus-injected AUROC",
                "clean-only matched operating-point feasibility",
            ],
            "claim_boundary": "secondary analysis only; aggregation is not changed after results",
        },
        "frozen_files": frozen_files,
        "environment": freeze_file_record(ENVIRONMENT),
        "git_state": {
            "head": environment["git"]["head"],
            "status_porcelain_sha256": environment["git"]["status_porcelain_sha256"],
            "diff_path": display_path(GIT_DIFF),
            "diff_sha256": sha256_file(GIT_DIFF),
            "diff_bytes": GIT_DIFF.stat().st_size,
        },
        "immutable_manifest_path": display_path(MANIFEST),
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_hash = sha256_file(MANIFEST)
    MANIFEST_HASH.write_text(f"{manifest_hash}  {display_path(MANIFEST)}\n", encoding="utf-8")

    receipt = f"""# Multi-Leaf Pre-Result Freeze Receipt v1

FREEZE COMPLETE

Captured: `{manifest['captured_at']}`

Temporal order enforced:

```text
FREEZE COMPLETE
-> materialize formal evaluator outputs
```

The formal result directory did not exist when this receipt was generated. No M/R/N formal evaluator output was read or created before this receipt.

## Immutable identities

- Git HEAD: `{manifest['git_state']['head']}`
- Git diff SHA-256: `{manifest['git_state']['diff_sha256']}`
- Git status SHA-256: `{manifest['git_state']['status_porcelain_sha256']}`
- Manifest SHA-256: `{manifest_hash}`
- Formal runner SHA-256: `{manifest['formal_runner']['sha256']}`
- Sample manifest SHA-256: `{manifest['sample_manifest']['sha256']}`
- Task-card section SHA-256: `{manifest['task_card']['sha256']}`
- Environment snapshot SHA-256: `{manifest['environment']['sha256']}`

## Frozen scientific contract

- Primary RQ: Do checkpoint visibility signatures contain stage-localizing information?
- Gold: expected first affected stage `M/R/N`.
- Predictor: `{manifest['predictor_contract']['classifier']}`.
- Response vector: `{manifest['predictor_contract']['input']}`.
- Tie rule: `{manifest['predictor_contract']['tie_rule']}`.
- LOCO rule: `{manifest['predictor_contract']['loco_rule']}`.
- Primary metrics: `{', '.join(manifest['predictor_contract']['primary_metrics'])}`.
- Chance top-1: `{manifest['predictor_contract']['chance_top1']}`.
- Majority baseline: `{manifest['predictor_contract']['majority_baseline']}`.
- Permutation: seed `{manifest['predictor_contract']['permutation_seed']}`, `{manifest['predictor_contract']['permutation_replicates']}` replicates.
- Bootstrap: seed `{manifest['predictor_contract']['bootstrap_seed']}`, `{manifest['predictor_contract']['bootstrap_replicates']}` replicates.
- Sample tier: `TARGET`, 24 clusters/stage x 3 injections = 72 clusters / 216 injections.
- Claim scope: `{manifest['sample_size_tier']['claim_scope']}`.

## Stop conditions

{chr(10).join('- ' + item for item in manifest['stop_conditions'])}

## Frozen files

{chr(10).join(f'- `{path}`: `{record['sha256']}` ({record['bytes']} bytes)' for path, record in sorted(manifest['frozen_files'].items()))}

## Post-freeze rule

After `FREEZE COMPLETE`, the listed files, sample IDs, expected stages/checkpoints, predictor, response-vector rule, tie/LOCO rules, baselines, metrics, seeds, sample-size tier, stop conditions and secondary aggregation contract must not be modified after any formal result is read. Any required correction invalidates this confirmatory run and requires a new preregistration namespace.
"""
    RECEIPT.write_text(receipt, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "FREEZE_COMPLETE",
        "receipt": display_path(RECEIPT),
        "manifest_sha256": manifest_hash,
        "formal_runner_sha256": manifest["formal_runner"]["sha256"],
        "git_head": manifest["git_state"]["head"],
        "result_artifacts_absent": True,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
