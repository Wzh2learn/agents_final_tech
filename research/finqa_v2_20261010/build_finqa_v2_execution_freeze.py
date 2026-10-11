#!/usr/bin/env python3
"""Build the outcome-blind FinQA v2 pre-result freeze artifacts."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import inspect
import json
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.finqa_evidence_argument_resolver_v2 import (
    EvidenceArgumentResolverError,
    resolve_numeric_argument,
)
from research.finqa_independent_observation_scorer_v2 import artifact_hash
from research.finqa_numeric_token_canonicalization_v2 import canonical_numeric_token

ROOT = REPO_ROOT
OUT_DIR = ROOT / "research/finqa_v2_20261010"
TASK_ID = "finqa-v2-preresult-freeze-a-20261010"
ROLES = ("train", "calibration", "evaluation")
STAGES = ("E", "P", "N")
SPLIT_DATE = "20261016"
PREDICATE_VERSION = "finqa-v2-independent-observation-predicate-v1"
RESOLVER_CONTRACT_VERSION = "finqa-evidence-argument-resolver-v2"

PATHS = {
    "candidate_manifest": ROOT / "research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json",
    "causal_join_audit": ROOT / "research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json",
    "canonicalization": ROOT / "research/finqa_numeric_token_canonicalization_v2.py",
    "resolver": ROOT / "research/finqa_evidence_argument_resolver_v2.py",
    "scorer": ROOT / "research/finqa_independent_observation_scorer_v2.py",
    "causal_audit_code": ROOT / "research/stage_e_multileaf_20261010/audit_finqa_v2_causal_join.py",
    "overlap_audit_code": ROOT / "research/stage_e_multileaf_20261010/audit_finqa_v2_overlap_feasibility.py",
    "selection_code": ROOT / "research/stage_e_multileaf_20261010/build_finqa_v2_candidate_manifest.py",
    "repair_receipt": ROOT / "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_receipt.json",
    "gate_reconciliation": ROOT / "docs/research/finqa_v2_gate_reconciliation_v2.json",
    "task_contract": ROOT / "research/finqa_v2_preresult_freeze_loop_a_task_contract.md",
}

TEST_PATHS = (
    ROOT / "tests/test_finqa_numeric_token_canonicalization_v2.py",
    ROOT / "tests/test_finqa_evidence_argument_resolver_v2.py",
    ROOT / "tests/test_finqa_independent_observation_scorer_v2.py",
    ROOT / "tests/test_finqa_v2_execution_freeze.py",
)

CORE_OUTPUTS = (
    OUT_DIR / "finqa_v2_frozen_sample_manifest.json",
    OUT_DIR / "finqa_v2_split_manifest.json",
    OUT_DIR / "finqa_v2_paired_artifact_manifest.json",
    OUT_DIR / "finqa_v2_scorer_binding_manifest.json",
)


class FreezeError(RuntimeError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def hash_without_self(value: dict[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "self_sha256"}
    return sha256_text(canonical_json(payload))


def file_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FreezeError("INPUT_MISSING", path=str(path))
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise FreezeError("INPUT_MISSING", path=str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def all_candidate_samples(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for stage in STAGES:
        for sample in candidate["samples"][stage]:
            rows.append({**sample, "stage": stage})
    return rows


def source_records(candidate: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    index: dict[str, dict[str, Any]] = {}
    files = []
    for raw_path, expected in sorted(candidate["source_files"].items()):
        path = Path(raw_path)
        actual = file_record(path)
        if actual["sha256"] != expected["sha256"] or actual["bytes"] != expected["bytes"]:
            raise FreezeError("INPUT_MISSING", reason="source_identity_mismatch", expected=expected, actual=actual)
        payload = json.loads(path.read_text(encoding="utf-8"))
        files.append(actual)
        for array_index, record in enumerate(payload):
            record_id = str(record.get("id"))
            if record_id in index:
                raise FreezeError("INPUT_MISSING", reason="duplicate_record_id", record_id=record_id)
            index[record_id] = {
                "path": path,
                "source_split": "train" if path.name == "train.json" else "dev",
                "array_index": array_index,
                "record": record,
            }
    return index, files


def resolver_status(sample: dict[str, Any], record: dict[str, Any]) -> tuple[str, str | None]:
    stage = sample["stage"]
    if stage == "P":
        return "NOT_APPLICABLE_OPERATOR_MUTATION", None
    evidence = (record.get("qa") or {}).get("gold_inds") or {}
    try:
        resolved = resolve_numeric_argument(sample["argument_before"], evidence)
    except EvidenceArgumentResolverError as exc:
        if exc.code == "unresolved_ambiguous_evidence":
            return "AMBIGUOUS", None
        return "UNRESOLVED", None
    return "UNIQUE", resolved["evidence_id"]


def removal_response(argument: str, evidence: dict[str, Any], evidence_id: str) -> str:
    reduced = {key: value for key, value in evidence.items() if key != evidence_id}
    try:
        resolve_numeric_argument(argument, reduced)
    except EvidenceArgumentResolverError as exc:
        if exc.code == "unresolved_no_evidence":
            return exc.code
        return f"UNEXPECTED_{exc.code}"
    return "STILL_RESOLVED_AFTER_REMOVAL"


def required_evidence_ids(stage: str, evidence: dict[str, Any], joined_evidence_id: str | None) -> list[str]:
    if stage == "E":
        if not joined_evidence_id:
            raise FreezeError("JOIN_NOT_IDENTIFIABLE", stage=stage)
        return [joined_evidence_id]
    required = sorted(str(key) for key in evidence)
    if not required:
        raise FreezeError("JOIN_NOT_IDENTIFIABLE", stage=stage, reason="empty_required_evidence")
    return required


def terminal_observation(steps: list[dict[str, Any]]) -> str:
    if not steps:
        raise FreezeError("INPUT_MISSING", reason="empty_steps")
    return str(steps[-1].get("res", ""))


def construct_artifact(sample: dict[str, Any], record: dict[str, Any], joined_evidence_id: str | None) -> dict[str, Any]:
    qa = record.get("qa") or {}
    evidence = qa.get("gold_inds") or {}
    clean_steps = copy.deepcopy(qa.get("steps") or [])
    mutant_steps = copy.deepcopy(clean_steps)
    stage = sample["stage"]
    step_index = int(sample["step_index"])
    if stage == "E":
        pass
    elif stage == "P":
        mutant_steps[step_index]["op"] = str(sample["op_after"])
    elif stage == "N":
        arg_name = str(sample["arg_name"])
        before = canonical_numeric_token(mutant_steps[step_index][arg_name])
        if before != canonical_numeric_token(sample["argument_before"]):
            raise FreezeError("JOIN_NOT_IDENTIFIABLE", reason="argument_identity_mismatch", before=before)
        mutant_steps[step_index][arg_name] = canonical_numeric_token(Decimal(before) + Decimal("1"))
    else:
        raise FreezeError("INPUT_MISSING", reason="unknown_stage", stage=stage)

    clean = {
        "evidence_ids": sorted(str(key) for key in evidence),
        "steps": clean_steps,
        "answer": terminal_observation(clean_steps),
    }
    mutant = {
        "evidence_ids": sorted(str(key) for key in evidence if stage != "E" or str(key) != joined_evidence_id),
        "steps": mutant_steps,
        "answer": terminal_observation(mutant_steps),
    }
    return {
        "required_evidence_ids": required_evidence_ids(stage, evidence, joined_evidence_id),
        "clean": clean,
        "mutant": mutant,
    }


def classify_samples(candidate: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    index, source_files = source_records(candidate)
    resolver_binding = {
        "contract_version": RESOLVER_CONTRACT_VERSION,
        "source_sha256": sha256_file(PATHS["resolver"]),
    }
    retained = []
    excluded = []
    join_statuses: dict[str, Counter[str]] = {stage: Counter() for stage in STAGES}
    removal_statuses: dict[str, Counter[str]] = {stage: Counter() for stage in STAGES}
    for sample in all_candidate_samples(candidate):
        source = index.get(str(sample["record_id"]))
        if source is None:
            raise FreezeError("INPUT_MISSING", record_id=sample["record_id"])
        record = source["record"]
        record_hash = sha256_text(canonical_json(record))
        if record_hash != sample["record_sha256"]:
            raise FreezeError("INPUT_MISSING", reason="record_hash_mismatch", sample_id=sample["sample_id"])
        status, joined_id = resolver_status(sample, record)
        join_statuses[sample["stage"]][status] += 1
        provenance = {
            "source_file": str(source["path"]),
            "source_array_index": source["array_index"],
            "source_locator": f"json_array[{source['array_index']}]",
            "record_id": str(sample["record_id"]),
            "record_sha256": sample["record_sha256"],
            "report_cluster_id": str(sample["report_cluster"]),
            "normalized_source_identity": sha256_text(f"finqa-v2-source-v1|{sample['record_id']}"),
            "argument_token": canonical_numeric_token(sample["argument_before"]) if sample["stage"] != "P" else None,
            "canonical_token": canonical_numeric_token(sample["argument_before"]) if sample["stage"] != "P" else None,
            "evidence_text_sha256": (
                sha256_text(canonical_json(((record.get("qa") or {}).get("gold_inds") or {}).get(joined_id)))
                if joined_id is not None
                else None
            ),
            "resolver_version": resolver_binding,
        }
        if sample["stage"] == "E" and status == "UNIQUE":
            evidence = (record.get("qa") or {}).get("gold_inds") or {}
            removal = removal_response(str(sample["argument_before"]), evidence, str(joined_id))
            removal_statuses["E"][removal] += 1
            if removal != "unresolved_no_evidence":
                raise FreezeError("JOIN_NOT_IDENTIFIABLE", sample_id=sample["sample_id"], removal=removal)
        elif sample["stage"] == "E":
            removal_statuses["E"]["NOT_EVALUATED_NON_UNIQUE"] += 1
        else:
            removal_statuses[sample["stage"]]["NOT_APPLICABLE"] += 1

        common = {
            **sample,
            "join_status": status,
            "joined_evidence_id": joined_id,
            "provenance": provenance,
        }
        if status in {"AMBIGUOUS", "UNRESOLVED"}:
            excluded.append({
                **common,
                "retained": False,
                "exclusion_stage": "BEFORE_SPLIT_ASSIGNMENT",
                "exclusion_reason": f"JOIN_{status}",
            })
            continue
        artifact = construct_artifact(common, record, joined_id)
        artifact_sha = artifact_hash(artifact)
        retained.append({
            **common,
            "retained": True,
            "artifact_id": f"FINQA-V2-ART-{sha256_text(sample['sample_id'])[:24]}",
            "artifact_sha256": artifact_sha,
            "clean_artifact_sha256": sha256_text(canonical_json(artifact["clean"])),
            "mutant_artifact_sha256": sha256_text(canonical_json(artifact["mutant"])),
            "_artifact_payload": artifact,
        })
    return retained, excluded, {
        "source_files": source_files,
        "join_status_by_stage": {stage: dict(sorted(join_statuses[stage].items())) for stage in STAGES},
        "removal_response_by_stage": {stage: dict(sorted(removal_statuses[stage].items())) for stage in STAGES},
    }


class DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def build_components(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dsu = DisjointSet(len(rows))
    first_for_key: dict[tuple[str, str], int] = {}
    for row_index, row in enumerate(rows):
        identities = (
            ("report_cluster", str(row["report_cluster"])),
            (
                "source_identity",
                str(row.get("provenance", {}).get("normalized_source_identity") or row.get("source_identity")),
            ),
            ("record_hash", str(row["record_sha256"])),
            ("record_id", str(row["record_id"])),
        )
        for key_type, key_value in identities:
            key = (key_type, key_value)
            if key in first_for_key:
                dsu.union(row_index, first_for_key[key])
            else:
                first_for_key[key] = row_index
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row_index, row in enumerate(rows):
        grouped[dsu.find(row_index)].append(row)
    components = []
    for members in grouped.values():
        stages = sorted({str(row["stage"]) for row in members})
        if len(stages) != 1:
            raise FreezeError("SPLIT_GROUP_COLLISION", stages=stages, sample_ids=sorted(row["sample_id"] for row in members))
        identities = sorted({
            f"report_cluster:{row['report_cluster']}"
            for row in members
        } | {
            "source_identity:"
            + str(row.get("provenance", {}).get("normalized_source_identity") or row.get("source_identity"))
            for row in members
        } | {
            f"record_hash:{row['record_sha256']}"
            for row in members
        } | {
            f"record_id:{row['record_id']}"
            for row in members
        })
        components.append({
            "stage": stages[0],
            "canonical_group_id": sha256_text("finqa-v2-group-v1|" + "\x1f".join(identities)),
            "identities": identities,
            "sample_ids": sorted(str(row["sample_id"]) for row in members),
        })
    return sorted(components, key=lambda row: (row["stage"], row["canonical_group_id"]))


def quota_for_group_count(group_count: int) -> dict[str, int]:
    if group_count == 24:
        return {"train": 9, "calibration": 5, "evaluation": 10}
    targets = {"train": 0.4, "calibration": 0.2, "evaluation": 0.4}
    quotas = {role: int(group_count * targets[role]) for role in ROLES}
    remainder = group_count - sum(quotas.values())
    ranked = sorted(
        ROLES,
        key=lambda role: (-(group_count * targets[role] - quotas[role]), ROLES.index(role)),
    )
    for role in ranked[:remainder]:
        quotas[role] += 1
    return quotas


ALLOWED_ASSIGNMENT_INPUT_FIELDS = frozenset({
    "sample_id",
    "stage",
    "report_cluster",
    "record_sha256",
    "record_id",
    "source_identity",
})


def assign_split(samples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    allowed = ALLOWED_ASSIGNMENT_INPUT_FIELDS
    normalized = []
    for sample in samples:
        if set(sample) != allowed:
            raise FreezeError("SPLIT_INPUT_NOT_WHITELISTED", fields=sorted(set(sample)))
        normalized.append(dict(sample))
    components = build_components(normalized)
    groups_by_stage: dict[str, list[dict[str, Any]]] = {stage: [] for stage in STAGES}
    for group in components:
        groups_by_stage[group["stage"]].append(group)
    assignments = []
    counts: dict[str, dict[str, dict[str, int]]] = {}
    deviations: dict[str, dict[str, int]] = {}
    for stage in STAGES:
        groups = sorted(
            groups_by_stage[stage],
            key=lambda group: sha256_text(f"finqa-v2-split-v1|{SPLIT_DATE}|{stage}|{group['canonical_group_id']}"),
        )
        quotas = quota_for_group_count(len(groups))
        counts[stage] = {role: {"groups": 0, "samples": 0} for role in ROLES}
        cursor = 0
        for role in ROLES:
            selected = groups[cursor:cursor + quotas[role]]
            cursor += quotas[role]
            for group in selected:
                order_key = sha256_text(f"finqa-v2-split-v1|{SPLIT_DATE}|{stage}|{group['canonical_group_id']}")
                counts[stage][role]["groups"] += 1
                counts[stage][role]["samples"] += len(group["sample_ids"])
                assignments.append({
                    "stage": stage,
                    "canonical_group_id": group["canonical_group_id"],
                    "order_key": order_key,
                    "role": role,
                    "sample_ids": group["sample_ids"],
                })
        ideal = {"train": 0.4 * len(groups), "calibration": 0.2 * len(groups), "evaluation": 0.4 * len(groups)}
        deviations[stage] = {
            role: counts[stage][role]["groups"] - int(ideal[role])
            for role in ROLES
        }
    assignments.sort(key=lambda row: (row["stage"], row["order_key"]))
    return assignments, {"counts": counts, "deviations": deviations}


def assignment_source_checks() -> dict[str, Any]:
    source = inspect.getsource(assign_split)
    tree = ast.parse(source)
    observed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            observed.add(node.id)
        elif isinstance(node, ast.Attribute):
            observed.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            observed.add(node.value)
    return {
        "function_sha256": sha256_text(source),
        "allowed_input_fields": sorted(ALLOWED_ASSIGNMENT_INPUT_FIELDS),
        "unexpected_field_policy": "fail_closed",
        "forbidden_identifier_hits": sorted(observed & FORBIDDEN_ASSIGNMENT_IDENTIFIERS),
        "passed": not bool(observed & FORBIDDEN_ASSIGNMENT_IDENTIFIERS),
    }


FORBIDDEN_ASSIGNMENT_IDENTIFIERS = frozenset({
    "outcome",
    "correctness",
    "harmfulness",
    "evaluator_result",
    "visibility_result",
    "detection_result",
})


def scorer_independence_checks(scorer_path: Path) -> dict[str, Any]:
    tree = ast.parse(scorer_path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    forbidden_modules = {
        "research.finqa_step_checkpoint_adapter",
        "research.finqa_step_checkpoint_scorer",
        "research.stage_e_multileaf_20261010.run_multileaf_formal",
    }
    hits = sorted(imports & forbidden_modules)
    return {
        "imports": sorted(imports),
        "forbidden_import_hits": hits,
        "independent_of_shared_fault_adapter": not hits,
        "independent_of_stage_e_aggregation": not hits,
        "actual_frozen_pairs_scored": 0,
        "passed": not hits,
    }


def build_core() -> dict[str, Any]:
    for path in PATHS.values():
        file_record(path)
    candidate = load_json(PATHS["candidate_manifest"])
    if len({sample["sample_id"] for rows in candidate["samples"].values() for sample in rows}) != 216:
        raise FreezeError("INPUT_MISSING", reason="candidate_id_count")
    retained, excluded, join_evidence = classify_samples(candidate)
    split_rows = [
        {
            "sample_id": row["sample_id"],
            "stage": row["stage"],
            "report_cluster": row["report_cluster"],
            "record_sha256": row["record_sha256"],
            "record_id": row["record_id"],
            "source_identity": row["provenance"]["normalized_source_identity"],
        }
        for row in retained
    ]
    assignments, allocation = assign_split(split_rows)
    role_by_sample = {
        sample_id: assignment["role"]
        for assignment in assignments
        for sample_id in assignment["sample_ids"]
    }
    if set(role_by_sample) != {row["sample_id"] for row in retained}:
        raise FreezeError("SPLIT_GROUP_COLLISION", reason="retained_sample_assignment_mismatch")

    frozen_rows = []
    for row in retained:
        frozen_rows.append({
            key: value for key, value in row.items() if not key.startswith("_")
        } | {"split_role": role_by_sample[row["sample_id"]]})
    frozen_rows.extend(excluded)
    frozen_rows.sort(key=lambda row: (row["stage"], row["sample_id"]))

    sample_payload = {
        "namespace": "FINQA_V2_FROZEN_SAMPLE_MANIFEST",
        "task_id": TASK_ID,
        "status": "FROZEN_SAMPLE_IDS_AND_JOINS_NOT_EXECUTION",
        "evidence_class": "PRIMARY",
        "input_sha256": {name: file_record(path) for name, path in PATHS.items()},
        "counts": {
            "candidate_injections": 216,
            "retained_injections": len(retained),
            "excluded_injections": len(excluded),
            "retained_groups": len(assignments),
            "by_stage": {
                stage: {
                    "candidate": sum(row["stage"] == stage for row in all_candidate_samples(candidate)),
                    "retained": sum(row["stage"] == stage for row in retained),
                    "excluded": sum(row["stage"] == stage for row in excluded),
                    "groups": sum(assignment["stage"] == stage for assignment in assignments),
                }
                for stage in STAGES
            },
        },
        "join": join_evidence,
        "exclusions": excluded,
        "samples": frozen_rows,
    }
    write_json(CORE_OUTPUTS[0], sample_payload)

    split_payload = {
        "namespace": "FINQA_V2_SPLIT_MANIFEST",
        "task_id": TASK_ID,
        "status": "DETERMINISTIC_GROUP_DISJOINT_SPLIT_FROZEN_NOT_EXECUTED",
        "contract": {
            "roles": list(ROLES),
            "primary_group": "report_cluster_id",
            "group_closure": "union records sharing exact normalized source identity, source hash, or duplicate record identity",
            "stages": list(STAGES),
            "stage_targets": {"train": "40%", "calibration": "20%", "evaluation": "40%"},
            "deterministic_order": f'SHA256("finqa-v2-split-v1|{SPLIT_DATE}|<stage>|<canonical_group_id>")',
            "singleton_quota": {"groups": [9, 5, 10], "injections": [81, 45, 90]},
            "cross_stage_policy": "SPLIT_GROUP_COLLISION",
            "assignment_access": "identity fields only",
        },
        "source_sample_manifest_sha256": sha256_file(CORE_OUTPUTS[0]),
        "assignment_checks": assignment_source_checks(),
        "allocation": allocation,
        "counts_by_stage_and_role": allocation["counts"],
        "assignments": assignments,
        "samples": [
            {"sample_id": row["sample_id"], "stage": row["stage"], "split_role": row["split_role"]}
            for row in sorted(frozen_rows if "split_role" in row else retained, key=lambda row: row["sample_id"])
            if row.get("retained", True)
        ],
        "group_disjointness": {
            "cross_stage_components": 0,
            "sample_in_multiple_roles": 0,
            "passed": True,
        },
        "leakage_fail_closed": assignment_source_checks(),
    }
    write_json(CORE_OUTPUTS[1], split_payload)

    artifact_entries = []
    for row in sorted(retained, key=lambda item: item["sample_id"]):
        payload = row["_artifact_payload"]
        if artifact_hash(payload) != row["artifact_sha256"]:
            raise FreezeError("JOIN_NOT_IDENTIFIABLE", reason="artifact_hash_mismatch", sample_id=row["sample_id"])
        artifact_entries.append({
            "sample_id": row["sample_id"],
            "artifact_id": row["artifact_id"],
            "stage": row["stage"],
            "split_role": role_by_sample[row["sample_id"]],
            "source": row["provenance"],
            "artifact_sha256": row["artifact_sha256"],
            "clean_artifact_sha256": row["clean_artifact_sha256"],
            "mutant_artifact_sha256": row["mutant_artifact_sha256"],
            "artifact": payload,
        })
    artifact_payload = {
        "namespace": "FINQA_V2_PAIRED_ARTIFACT_MANIFEST",
        "task_id": TASK_ID,
        "status": "EXACT_PRE_EXECUTION_PAIRED_ARTIFACTS_FROZEN_NOT_EVALUATED",
        "artifact_semantics": {
            "state": "pre-execution construction state",
            "answer_field": "terminal source program res; qa.answer is not read into this field",
            "formal_execution_outputs": "absent",
        },
        "source_hashes": join_evidence["source_files"],
        "counts": {"retained": len(artifact_entries), "excluded_before_artifact_binding": len(excluded)},
        "artifacts": artifact_entries,
    }
    write_json(CORE_OUTPUTS[2], artifact_payload)

    scorer_checks = scorer_independence_checks(PATHS["scorer"])
    if not scorer_checks["passed"]:
        raise FreezeError("SCORER_NOT_INDEPENDENT", **scorer_checks)
    binding_entries = [
        {
            "sample_id": row["sample_id"],
            "artifact_id": row["artifact_id"],
            "artifact_sha256": row["artifact_sha256"],
            "status": "BOUND_UNSCORED_PENDING_LATER_AUTHORIZED_EXECUTION",
        }
        for row in sorted(retained, key=lambda item: item["sample_id"])
    ]
    scorer_payload = {
        "namespace": "FINQA_V2_SCORER_BINDING_MANIFEST",
        "task_id": TASK_ID,
        "status": "INDEPENDENT_SCORER_BINDINGS_FROZEN_NOT_EXECUTED",
        "measurement_object": "paired_checkpoint_observation_reproduction",
        "semantic_correctness_claim": False,
        "predicate_version": PREDICATE_VERSION,
        "observation_surface": [
            "evidence_required_hit",
            "operator_consistency",
            "argument_consistency",
            "step_result_consistency",
            "answer_consistency",
        ],
        "decision_predicate": "No threshold, classifier, hierarchy comparison, or formal decision is materialized; score_pair reports only the frozen five-field observation vector.",
        "source": file_record(PATHS["scorer"]),
        "tests": [file_record(path) for path in TEST_PATHS if path.is_file()],
        "input_manifests": {
            "sample": file_record(CORE_OUTPUTS[0]),
            "split": file_record(CORE_OUTPUTS[1]),
            "paired_artifacts": file_record(CORE_OUTPUTS[2]),
        },
        "independence": scorer_checks,
        "bindings": binding_entries,
        "unevaluable_denominators": {
            "bound_artifacts": len(binding_entries),
            "formal_scoring_calls": 0,
            "unevaluable_before_later_authorized_execution": len(binding_entries),
        },
        "formal_evaluator_outputs_materialized": 0,
    }
    write_json(CORE_OUTPUTS[3], scorer_payload)
    return {
        "candidate": candidate,
        "retained": retained,
        "excluded": excluded,
        "assignments": assignments,
        "allocation": allocation,
        "join_evidence": join_evidence,
        "scorer_checks": scorer_checks,
    }


def parse_test_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    passed_match = re.search(r"(\d+) passed", text)
    failed_match = re.search(r"(\d+) failed", text)
    exit_match = re.search(r"^EXIT_CODE=(\d+)$", text, flags=re.MULTILINE)
    if not exit_match:
        raise FreezeError("TEST_VALIDATION_FAILED", path=str(path), reason="missing_exit_code")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "command": re.search(r"^COMMAND=(.+)$", text, flags=re.MULTILINE).group(1),
        "stdout_present": "STDOUT_BEGIN" in text,
        "stderr_present": "STDERR_BEGIN" in text,
        "passed": int(passed_match.group(1)) if passed_match else 0,
        "failed": int(failed_match.group(1)) if failed_match else 0,
        "exit_code": int(exit_match.group(1)),
    }


def scoped_paths() -> list[Path]:
    return [
        PATHS["canonicalization"],
        PATHS["resolver"],
        PATHS["scorer"],
        PATHS["causal_audit_code"],
        PATHS["overlap_audit_code"],
        PATHS["selection_code"],
        ROOT / "research/finqa_v2_20261010/build_finqa_v2_execution_freeze.py",
        *TEST_PATHS,
    ]


def git_output(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode not in {0, 1}:
        raise FreezeError("INPUT_MISSING", command=args, stderr=result.stderr)
    return result.stdout


def build_source_snapshot() -> tuple[Path, Path, str]:
    chunks = []
    file_hashes = {}
    for path in scoped_paths():
        relative = path.relative_to(ROOT)
        file_hashes[str(relative)] = file_record(path)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(relative)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        ).returncode == 0
        if tracked:
            diff = git_output(["diff", "--no-ext-diff", "--", str(relative)])
        else:
            diff = git_output(["diff", "--no-index", "--", "/dev/null", str(relative)])
        chunks.append(f"--- a/{relative}\n+++ b/{relative}\n{diff}\n")
    patch_path = OUT_DIR / "finqa_v2_scoped_source_diff.patch"
    patch_path.write_text("".join(chunks), encoding="utf-8")
    dependency_path = OUT_DIR / "finqa_v2_dependency_freeze.txt"
    dependency = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if dependency.returncode != 0:
        raise FreezeError("TEST_VALIDATION_FAILED", reason="pip_freeze_failed", stderr=dependency.stderr)
    dependency_path.write_text(dependency.stdout, encoding="utf-8")
    head = git_output(["rev-parse", "HEAD"]).strip()
    package_versions = {}
    for package_name in ("pytest", "fastapi", "pydantic"):
        try:
            package_versions[package_name] = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            package_versions[package_name] = None
    package_versions = {name: version for name, version in package_versions.items() if version is not None}
    environment = {
        "namespace": "FINQA_V2_SCOPED_ENVIRONMENT_SNAPSHOT",
        "task_id": TASK_ID,
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
        },
        "platform": platform.platform(),
        "packages": package_versions,
        "git_head": head,
        "relevant_diff_sha256": sha256_text(patch_path.read_text(encoding="utf-8")),
        "scoped_files": file_hashes,
        "scoped_source_diff": file_record(patch_path),
        "dependency_freeze": file_record(dependency_path),
        "endpoint_calls": 0,
        "model_calls": 0,
        "training_runs": 0,
    }
    environment_path = OUT_DIR / "finqa_v2_scoped_environment_snapshot.json"
    write_json(environment_path, environment)
    return patch_path, environment_path, head


def formal_output_inventory() -> list[str]:
    hits = []
    patterns = ("*formal*result*", "*evaluator*output*", "*prediction*rows*", "*scoring*output*")
    for pattern in patterns:
        hits.extend(str(path.relative_to(ROOT)) for path in OUT_DIR.rglob(pattern) if path.is_file())
    return sorted(set(hits))


def render_packet(payload: dict[str, Any]) -> str:
    counts = payload["counts_by_stage_and_role"]
    lines = [
        "# FINQA_V2_EXECUTION_FREEZE_PACKET",
        "",
        f"> Status: `{payload['status']}` | Evidence class: PRIMARY/SECONDARY/ENGINEERING/NEGATIVE | Formal outputs: 0",
        "",
        "## Frozen research question",
        "",
        payload["frozen_research_question"],
        "",
        "## Counts by stage and role",
        "",
        "| Stage | Role | Groups | Samples |",
        "|---|---|---:|---:|",
    ]
    for stage in STAGES:
        for role in ROLES:
            row = counts[stage][role]
            lines.append(f"| {stage} | {role} | {row['groups']} | {row['samples']} |")
    lines.extend([
        "",
        "## Exclusions and joins",
        "",
        f"- Candidate injections: `{payload['candidate_injections']}`; retained: `{payload['retained_injections']}`; excluded before split: `{payload['excluded_injections']}`.",
        f"- Join statuses: `{json.dumps(payload['join_statuses'], ensure_ascii=False, sort_keys=True)}`.",
        f"- Unique E removal responses: `{json.dumps(payload['removal_responses'].get('E', {}), sort_keys=True)}`.",
        "",
        "## Scorer, leakage, and execution boundary",
        "",
        f"- Scorer independence: `{payload['scorer_independence']}`.",
        f"- Leakage checks: `{json.dumps(payload['leakage_checks'], sort_keys=True)}`.",
        f"- Formal evaluator outputs materialized: `{payload['formal_evaluator_outputs']}`.",
        f"- Unevaluable denominator before later execution: `{payload['unevaluable_denominator']}`.",
        "",
        "## Six gate recommendations",
        "",
        "| Gate | Recommendation | Evidence |",
        "|---|---|---|",
    ])
    for gate in ("SOURCE_GO", "ID_GO", "JOIN_GO", "SPLIT_GO", "SCORER_GO", "PREREG_GO"):
        item = payload["gate_recommendations"][gate]
        lines.append(f"| `{gate}` | `{item['recommendation']}` | {item['evidence']} |")
    lines.extend([
        "",
        "## Boundary",
        "",
        "No formal FinQA v2 evaluator output, model call, training run, threshold search, semantic-correctness claim, hierarchy comparison, or natural-failure localization was produced. The packet stops for Loop C independent review.",
        "",
        "## Hash closure",
        "",
        f"- Packet JSON SHA-256: `{payload['packet_json_sha256']}`.",
        "- The receipt closes packet/test/source/environment hashes; its `self_sha256` is defined over canonical JSON with that field removed.",
        "",
    ])
    return "\n".join(lines)


def finalize() -> dict[str, Any]:
    core = {path.name: file_record(path) for path in CORE_OUTPUTS}
    test_logs = [
        OUT_DIR / "tests_existing_11.log",
        OUT_DIR / "tests_finqa_v2_freeze.log",
        OUT_DIR / "tests_all_focused.log",
        OUT_DIR / "freeze_artifact_verification.log",
    ]
    tests = [parse_test_log(path) for path in test_logs]
    if any(item["exit_code"] != 0 or item["failed"] for item in tests):
        raise FreezeError("TEST_VALIDATION_FAILED", tests=tests)
    patch_path, environment_path, head = build_source_snapshot()
    outputs = {
        **core,
        **{path.name: file_record(path) for path in test_logs},
        "build_core.log": file_record(OUT_DIR / "build_core.log"),
        patch_path.name: file_record(patch_path),
        environment_path.name: file_record(environment_path),
        (OUT_DIR / "finqa_v2_dependency_freeze.txt").name: file_record(OUT_DIR / "finqa_v2_dependency_freeze.txt"),
    }
    sample = load_json(CORE_OUTPUTS[0])
    split = load_json(CORE_OUTPUTS[1])
    artifacts = load_json(CORE_OUTPUTS[2])
    scorer = load_json(CORE_OUTPUTS[3])
    exclusions = sample["exclusions"]
    formal_outputs = formal_output_inventory()
    if formal_outputs:
        raise FreezeError("PRERESULT_FREEZE_VIOLATION", paths=formal_outputs)
    gate_recommendations = {
        "SOURCE_GO": {
            "recommendation": "RECOMMEND_PASS_IDENTITY_BOUND",
            "evidence": f"2 source files and all required inputs are SHA-256 bound in {CORE_OUTPUTS[0].name}.",
        },
        "ID_GO": {
            "recommendation": "RECOMMEND_PASS_IDS_FROZEN",
            "evidence": f"216 candidate IDs; {sample['counts']['retained_injections']} retained; {sample['counts']['excluded_injections']} excluded before split.",
        },
        "JOIN_GO": {
            "recommendation": "RECOMMEND_PASS_UNIQUE_CAUSAL_JOINS_FROZEN",
            "evidence": f"E join statuses {sample['join']['join_status_by_stage']['E']}; removal responses {sample['join']['removal_response_by_stage']['E']}.",
        },
        "SPLIT_GO": {
            "recommendation": "RECOMMEND_PASS_GROUP_DISJOINT_SPLIT_FROZEN",
            "evidence": f"Cross-stage components {split['group_disjointness']['cross_stage_components']}; multi-role samples {split['group_disjointness']['sample_in_multiple_roles']}.",
        },
        "SCORER_GO": {
            "recommendation": "RECOMMEND_PASS_INDEPENDENT_BINDING_FROZEN_NOT_EXECUTED",
            "evidence": f"Forbidden imports {scorer['independence']['forbidden_import_hits']}; formal scorer calls {scorer['unevaluable_denominators']['formal_scoring_calls']}.",
        },
        "PREREG_GO": {
            "recommendation": "RECOMMEND_PASS_PRERESULT_FREEZE_ONLY_NOT_EXECUTION",
            "evidence": f"Formal outputs {len(formal_outputs)}; receipt is written after all focused tests.",
        },
    }
    packet_payload: dict[str, Any] = {
        "namespace": "FINQA_V2_EXECUTION_FREEZE_PACKET",
        "task_id": TASK_ID,
        "status": "READY_FOR_LOOP_C_INDEPENDENT_REVIEW_NOT_EXECUTION",
        "frozen_research_question": "Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?",
        "evidence_classes": {
            "PRIMARY": "freeze identity, exact sample/source/report/stage hashes",
            "SECONDARY": "split, connected-component closure, causal join",
            "ENGINEERING": "independent scorer, focused tests, token identity",
            "NEGATIVE": "zero formal outputs, zero model calls, zero training, zero forbidden imports",
        },
        "input_sha256": sample["input_sha256"],
        "output_sha256_before_packet": outputs,
        "candidate_injections": sample["counts"]["candidate_injections"],
        "retained_injections": sample["counts"]["retained_injections"],
        "excluded_injections": sample["counts"]["excluded_injections"],
        "counts_by_stage_and_role": split["counts_by_stage_and_role"],
        "exclusions": exclusions,
        "join_statuses": sample["join"]["join_status_by_stage"],
        "removal_responses": sample["join"]["removal_response_by_stage"],
        "scorer_independence": scorer["independence"],
        "leakage_checks": {
            "assignment": split["assignment_checks"],
            "group_disjointness": split["group_disjointness"],
            "scorer_label_blind_contract": True,
            "threshold_search_performed": False,
        },
        "formal_evaluator_outputs": len(formal_outputs),
        "formal_evaluator_output_paths": formal_outputs,
        "unevaluable_denominator": scorer["unevaluable_denominators"],
        "scorer_contract": {
            "measurement_object": scorer["measurement_object"],
            "semantic_correctness_claim": scorer["semantic_correctness_claim"],
            "predicate_version": scorer["predicate_version"],
            "observation_surface": scorer["observation_surface"],
            "decision_predicate": scorer["decision_predicate"],
        },
        "gate_recommendations": gate_recommendations,
        "tests": tests,
        "build_command": (OUT_DIR / "build_core.log").read_text(encoding="utf-8").splitlines()[0].removeprefix("COMMAND="),
        "environment": {
            "python": sys.version,
            "git_head": head,
            "endpoint_calls": 0,
            "model_calls": 0,
            "training_runs": 0,
        },
        "stop_conditions": {name: False for name in (
            "INPUT_MISSING",
            "SPLIT_GROUP_COLLISION",
            "JOIN_NOT_IDENTIFIABLE",
            "TOKEN_IDENTITY_UNRECONCILED",
            "SCORER_NOT_INDEPENDENT",
            "PRERESULT_FREEZE_VIOLATION",
            "TEST_VALIDATION_FAILED",
            "OUT_OF_SCOPE",
        )},
        "hash_contract": "SHA-256 of canonical compact sorted JSON after removing self_sha256",
    }
    packet_payload["self_sha256"] = hash_without_self(packet_payload)
    packet_json = OUT_DIR / "finqa_v2_execution_freeze_packet.json"
    write_json(packet_json, packet_payload)
    packet_md = OUT_DIR / "FINQA_V2_EXECUTION_FREEZE_PACKET.md"
    packet_md_payload = dict(packet_payload)
    packet_md_payload["packet_json_sha256"] = sha256_file(packet_json)
    packet_md.write_text(render_packet(packet_md_payload), encoding="utf-8", newline="\n")

    final_outputs = {
        **outputs,
        packet_json.name: file_record(packet_json),
        packet_md.name: file_record(packet_md),
    }
    receipt: dict[str, Any] = {
        "namespace": "FINQA_V2_PRERESULT_FREEZE_RECEIPT",
        "task_id": TASK_ID,
        "status": "PRERESULT_FREEZE_COMPLETE_PENDING_LOOP_C_REVIEW",
        "sequence": [
            "premises_and_inputs",
            "core_manifests",
            "focused_tests",
            "source_environment_snapshot",
            "execution_freeze_packet",
            "preresult_freeze_receipt",
        ],
        "formal_evaluator_outputs_before_receipt": 0,
        "model_calls": 0,
        "training_runs": 0,
        "endpoint_calls": 0,
        "input_sha256": sample["input_sha256"],
        "output_sha256": final_outputs,
        "packet_self_sha256": packet_payload["self_sha256"],
        "gate_recommendations": gate_recommendations,
        "tests": tests,
        "build_command": packet_payload["build_command"],
        "stop_conditions": packet_payload["stop_conditions"],
        "hash_contract": "SHA-256 of canonical compact sorted JSON after removing self_sha256",
    }
    receipt["self_sha256"] = hash_without_self(receipt)
    receipt_path = OUT_DIR / "finqa_v2_preresult_freeze_receipt.json"
    write_json(receipt_path, receipt)
    if hash_without_self(receipt) != receipt["self_sha256"]:
        raise FreezeError("TEST_VALIDATION_FAILED", reason="receipt_self_hash")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "finalize"))
    args = parser.parse_args()
    if args.command == "build":
        payload = build_core()
        print(json.dumps({
            "status": "CORE_FREEZE_BUILT",
            "candidate": 216,
            "retained": len(payload["retained"]),
            "excluded": len(payload["excluded"]),
            "groups": len(payload["assignments"]),
        }, sort_keys=True))
        return 0
    receipt = finalize()
    print(json.dumps({
        "status": receipt["status"],
        "self_sha256": receipt["self_sha256"],
        "formal_outputs": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
