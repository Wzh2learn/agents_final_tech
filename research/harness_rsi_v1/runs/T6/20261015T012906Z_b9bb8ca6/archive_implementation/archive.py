#!/usr/bin/env python3
"""Deterministic, read-only archive mechanisms for the bounded T6 run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, Iterable


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_id(blob: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(blob)}\0".encode("ascii"))
    digest.update(blob)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            records.append(value)
    return records


def normalized_mode(raw_mode: str | int) -> str:
    value = int(str(raw_mode), 8)
    return "100755" if value & 0o111 else "100644"


def run_git(arguments: list[str]) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed rc={result.returncode}: {message}")
    return result.stdout


def git_tree(commit: str, root: Path) -> dict[str, tuple[str, str]]:
    output = run_git(["-C", str(root), "ls-tree", "-r", "-z", commit])
    tree: dict[str, tuple[str, str]] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode_text, object_type, object_id = metadata.decode("ascii").split()
        if object_type != "blob":
            continue
        tree[path.decode("utf-8")] = (mode_text, object_id)
    return tree


def content_group_id(members: Iterable[dict[str, str]]) -> str:
    normalized = sorted(
        (
            {
                "mode": normalized_mode(member["mode"]),
                "relative_path": member["relative_path"],
                "sha256": member["sha256"],
            }
            for member in members
        ),
        key=lambda item: item["relative_path"],
    )
    return "sha256:" + sha256_bytes(canonical_bytes(normalized))


def verify_parent(
    descriptor: dict[str, Any],
    repository_root: Path,
) -> dict[str, Any]:
    run_root = Path(descriptor["run_root"])
    manifest_path = run_root / "artifacts_manifest.json"
    manifest = load_json(manifest_path)
    artifacts = manifest["artifacts"]
    tree = git_tree(descriptor["git_commit"], repository_root)
    manifest_prefix = descriptor["manifest_prefix"]
    failures: list[str] = []
    members: list[dict[str, str]] = []
    raw_mode_matches = 0
    raw_mode_declared = 0

    def artifact_relative_path(artifact: dict[str, Any]) -> str:
        if "relative_path" in artifact:
            return artifact["relative_path"]
        absolute = Path(artifact["absolute_path"])
        return absolute.relative_to(run_root).as_posix()

    expected_paths = {artifact_relative_path(item) for item in artifacts}
    for artifact in artifacts:
        relative_path = artifact_relative_path(artifact)
        tree_entry = tree.get(manifest_prefix + relative_path)
        if tree_entry is None:
            failures.append(f"missing_at_commit:{relative_path}")
            continue
        commit_mode, commit_blob_id = tree_entry
        blob = run_git(
            ["-C", str(repository_root), "cat-file", "blob", commit_blob_id]
        )
        actual_sha256 = sha256_bytes(blob)
        if actual_sha256 != artifact["sha256"]:
            failures.append(f"sha256_mismatch:{relative_path}")
        worktree_path = run_root / relative_path
        if worktree_path.is_symlink() or not worktree_path.is_file():
            failures.append(f"missing_worktree:{relative_path}")
        else:
            if sha256_file(worktree_path) != actual_sha256:
                failures.append(f"worktree_sha256_mismatch:{relative_path}")
            if "mode" in artifact:
                raw_mode_declared += 1
                if oct(stat.S_IMODE(worktree_path.stat().st_mode))[2:].zfill(4) == str(artifact["mode"])[-4:]:
                    raw_mode_matches += 1
                else:
                    failures.append(f"declared_mode_mismatch:{relative_path}")
        members.append(
            {
                "mode": normalized_mode(commit_mode),
                "relative_path": relative_path,
                "sha256": actual_sha256,
            }
        )

    actual_group_id = content_group_id(members)
    if actual_group_id != descriptor["content_group_id"]:
        failures.append("content_group_id_mismatch")

    anchor_results = []
    for anchor in descriptor["tracked_anchors"]:
        relative_path = anchor["path"]
        tree_entry = tree.get(relative_path)
        actual = None if tree_entry is None else tree_entry[1]
        passed = actual == anchor["git_blob_id"]
        if not passed:
            failures.append(f"tracked_anchor_mismatch:{relative_path}")
        anchor_results.append(
            {
                "actual": actual,
                "expected": anchor["git_blob_id"],
                "passed": passed,
                "path": relative_path,
            }
        )

    return {
        "actual_content_group_id": actual_group_id,
        "actual_member_count": len(members),
        "anchor_results": anchor_results,
        "canonical_id": descriptor["canonical_id"],
        "declared_mode_count": raw_mode_declared,
        "expected_content_group_id": descriptor["content_group_id"],
        "failures": failures,
        "git_commit": descriptor["git_commit"],
        "manifest_declared_paths": len(expected_paths),
        "passed": not failures,
        "raw_mode_conformance": (
            None
            if raw_mode_declared == 0
            else {"declared": raw_mode_declared, "matched": raw_mode_matches}
        ),
        "run_id": descriptor["run_id"],
    }


def candidate_signature(candidate: dict[str, Any]) -> str:
    identity = candidate["identity"]
    entries = [
        {
            "current_registry_support": entry["current_registry_support"],
            "entry_id": entry["entry_id"],
            "intent": entry["intent"],
            "op_id": entry["op_id"],
            "parameterization": entry["parameterization"],
        }
        for entry in candidate["entries"]
    ]
    payload = {
        "changes": entries,
        "object": identity["object"],
        "parent_group_ids": sorted(identity["parent_group_ids"]),
        "problem_family": identity["problem_family"],
    }
    return "sha256:" + sha256_bytes(canonical_bytes(payload))


def candidate_id(candidate: dict[str, Any]) -> str:
    return "cand-" + sha256_bytes(canonical_bytes(candidate["identity"]))[:16]


def evaluation_id(evaluation: dict[str, Any]) -> str:
    return "eval-" + sha256_bytes(canonical_bytes(evaluation["identity"]))[:16]


def evaluate_candidate(candidate_path: Path, archive_root: Path) -> dict[str, Any]:
    candidate = load_json(candidate_path)
    declared_id = candidate_id(candidate)
    signature = candidate_signature(candidate)
    nogoods = load_jsonl(archive_root / "fixtures" / "nogoods.jsonl")
    matches = [record for record in nogoods if record["failure_signature"] == signature]
    future_authorizations = [
        entry["entry_id"]
        for entry in candidate["entries"]
        if entry["current_registry_support"] is False
    ]
    return {
        "activation_enabled": False,
        "candidate_id": declared_id,
        "candidate_id_matches": declared_id == candidate["candidate_id"],
        "failure_signature": signature,
        "nogood_matches": matches,
        "reason": (
            "REPEATED_PROVEN_FAILURE_PACKAGE"
            if matches
            else "PROPOSED_REQUIRES_INDEPENDENT_T7_REVIEW"
        ),
        "rejection_is_permanent": False,
        "status": "REJECTED_DUPLICATE_NOGOOD" if matches else "PROPOSED_NOT_ENABLED",
        "needs_future_authorization_entries": future_authorizations,
    }


def export_context(candidate_path: Path, archive_root: Path) -> dict[str, Any]:
    candidate = load_json(candidate_path)
    parents = load_json(archive_root / "fixtures" / "parent_versions.json")
    parent_lookup = {item["canonical_id"]: item for item in parents["parents"]}
    evidence_registry = load_json(archive_root / "fixtures" / "evidence_registry.json")
    evidence_lookup = {item["evidence_id"]: item for item in evidence_registry["evidence"]}
    lessons = load_jsonl(archive_root / "fixtures" / "lessons.jsonl")
    evaluation = evaluate_candidate(candidate_path, archive_root)
    selected_evidence_ids = sorted(
        {
            reference["evidence_id"]
            for reference in candidate["evidence_references"]
        }
    )
    selected_evidence = [
        {
            "anchor": evidence_lookup[item]["anchor"],
            "evidence_id": item,
            "git_blob_id": evidence_lookup[item]["git_blob_id"],
            "path": evidence_lookup[item]["path"],
            "sha256": evidence_lookup[item]["sha256"],
        }
        for item in selected_evidence_ids
    ]
    relevant_lessons = [
        record
        for record in lessons
        if record["problem_family"] == candidate["identity"]["problem_family"]
    ]
    parents_minimal = [
        {
            "canonical_id": canonical_id,
            "content_group_id": parent_lookup[canonical_id]["content_group_id"],
            "run_id": parent_lookup[canonical_id]["run_id"],
        }
        for canonical_id in candidate["identity"]["parent_canonical_ids"]
    ]
    return {
        "candidate": {
            "candidate_id": candidate["candidate_id"],
            "cost_record": candidate["cost_record"],
            "entries": [
                {
                    "current_registry_support": entry["current_registry_support"],
                    "entry_id": entry["entry_id"],
                    "intent": entry["intent"],
                    "needs_future_authorization": entry["needs_future_authorization"],
                    "op_id": entry["op_id"],
                    "parameterization": entry["parameterization"],
                }
                for entry in candidate["entries"]
            ],
            "evaluation_plan": candidate["evaluation_plan"],
            "object": candidate["identity"]["object"],
            "problem_family": candidate["identity"]["problem_family"],
            "status": evaluation["status"],
            "version_applicability": candidate["version_applicability"],
        },
        "evidence": selected_evidence,
        "mechanism_fields": {
            "candidate_status": "PROPOSAL_ONLY; activation_enabled=false",
            "evidence_selection": "Only evidence IDs declared by this candidate.",
            "parent_selection": "Only parent content-group IDs and canonical IDs.",
            "register_operation_selection": "Only referenced OP-T4-R-* operation identities and the minimum needed fields.",
            "rejection_is_permanent": False,
            "shared_buffers": "Local read-only lesson projections; full shared archives are not copied.",
        },
        "parents": parents_minimal,
        "relevant_lessons": relevant_lessons,
        "schema": "jinrong_t6_selective_context_v1",
        "omitted": [
            "Full parent packages",
            "Full lessons/nogoods archives",
            "Unreferenced evidence",
            "Repository and runtime state",
        ],
    }


def count_evidence(candidate_directory: Path) -> dict[str, Any]:
    candidate_paths = sorted(candidate_directory.glob("*/candidate.json"))
    raw_references: list[tuple[str, str]] = []
    for path in candidate_paths:
        candidate = load_json(path)
        for reference in candidate["evidence_references"]:
            raw_references.append((candidate["candidate_id"], reference["evidence_id"]))
    unique_evidence = sorted({evidence_id for _, evidence_id in raw_references})
    per_evidence = {
        evidence_id: {
            "candidate_reference_count": sum(
                1 for _, referenced_id in raw_references if referenced_id == evidence_id
            ),
            "counted_once_for_global_total": 1,
        }
        for evidence_id in unique_evidence
    }
    duplicate_candidate_pairs = [
        (left, right, evidence_id)
        for index, (left, evidence_id) in enumerate(raw_references)
        for right, other_evidence_id in raw_references[index + 1 :]
        if evidence_id == other_evidence_id and left != right
    ]
    return {
        "candidate_count": len(candidate_paths),
        "duplicate_candidate_pairs": duplicate_candidate_pairs,
        "global_unique_evidence_count": len(unique_evidence),
        "per_evidence": per_evidence,
        "raw_candidate_reference_count": len(raw_references),
        "references_suppressed_as_duplicates": (
            len(raw_references) - len(unique_evidence)
        ),
        "schema": "jinrong_t6_evidence_count_v1",
    }


def load_parent_descriptors(archive_root: Path) -> list[dict[str, Any]]:
    return load_json(archive_root / "fixtures" / "parent_versions.json")["parents"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "candidate-id",
            "count-evidence",
            "evaluate",
            "evaluation-id",
            "export-context",
            "validate-parents",
        ],
    )
    parser.add_argument("target", nargs="?")
    args = parser.parse_args()
    archive_root = Path(__file__).resolve().parent
    repository_root = archive_root.parents[5]

    if args.command == "validate-parents":
        descriptors = load_parent_descriptors(archive_root)
        results = [verify_parent(item, repository_root) for item in descriptors]
        output = {
            "parents": results,
            "passed": all(item["passed"] for item in results),
            "schema": "jinrong_t6_parent_validation_v1",
        }
    elif args.command == "evaluate":
        if not args.target:
            parser.error("evaluate requires a candidate.json path")
        output = evaluate_candidate(Path(args.target).resolve(), archive_root)
    elif args.command == "export-context":
        if not args.target:
            parser.error("export-context requires a candidate.json path")
        output = export_context(Path(args.target).resolve(), archive_root)
    elif args.command == "count-evidence":
        target = Path(args.target).resolve() if args.target else archive_root.parent / "candidate_packages"
        output = count_evidence(target)
    elif args.command == "candidate-id":
        candidate = load_json(Path(args.target).resolve())
        output = {"candidate_id": candidate_id(candidate)}
    elif args.command == "evaluation-id":
        evaluation = load_json(Path(args.target).resolve())
        output = {"evaluation_id": evaluation_id(evaluation)}
    else:
        raise AssertionError("unreachable")
    json.dump(output, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0 if output.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
