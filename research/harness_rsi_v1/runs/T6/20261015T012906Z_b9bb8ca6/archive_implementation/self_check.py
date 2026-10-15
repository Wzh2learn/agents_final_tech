#!/usr/bin/env python3
"""Adversarial completion checks for the bounded T6 run."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[6]
ARCHIVE_ROOT = RUN_ROOT / "archive_implementation"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(arguments: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def normalized_mode(path: Path) -> str:
    raw_mode = stat.S_IMODE(path.stat().st_mode)
    return "100755" if raw_mode & 0o111 else "100644"


def load_archive_module() -> Any:
    path = ARCHIVE_ROOT / "archive.py"
    spec = importlib.util.spec_from_file_location("t6_archive", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load archive.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add(checks: list[dict[str, Any]], check_id: str, passed: bool, detail: str) -> None:
    checks.append({"check_id": check_id, "detail": detail, "passed": passed})


def main() -> int:
    checks: list[dict[str, Any]] = []
    archive = load_archive_module()

    json_files = sorted(RUN_ROOT.rglob("*.json"))
    json_failures = []
    for path in json_files:
        try:
            load_json(path)
        except Exception as exc:
            json_failures.append({"path": str(path), "error": str(exc)})
    add(checks, "json_parse", not json_failures, f"{len(json_files)} JSON files parsed")

    jsonl_failures = []
    for path in sorted(RUN_ROOT.rglob("*.jsonl")):
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.strip():
                    json.loads(line)
        except Exception as exc:
            jsonl_failures.append({"path": str(path), "error": str(exc)})
    add(checks, "jsonl_parse", not jsonl_failures, "all JSONL lines parsed")

    receipt = load_json(RUN_ROOT / "receipt.json")
    required_receipt_keys = {
        "task_id",
        "run_id",
        "scope",
        "execution_status",
        "acceptance_status",
        "activation_status",
        "input_bindings",
        "output_manifest",
        "checks",
        "usage",
        "unresolved",
        "authorization_ref",
    }
    add(
        checks,
        "receipt_schema_required",
        required_receipt_keys.issubset(receipt),
        f"required keys present={required_receipt_keys.issubset(receipt)}",
    )
    add(
        checks,
        "three_axis",
        receipt["execution_status"] == "DELIVERED"
        and receipt["acceptance_status"] == "UNREVIEWED"
        and receipt["activation_status"] == "NOT_ENABLED",
        "DELIVERED / UNREVIEWED / NOT_ENABLED",
    )

    binding_failures = []
    allowed_binding_prefixes = (
        "research/harness_rsi_v1/cards/",
        "research/harness_rsi_v1/contracts/",
        "research/harness_rsi_v1/meta/",
        "research/harness_rsi_v1/runs/T5/",
        "research/harness_rsi_v1/runs/T4/",
        "research/harness_rsi_v1/reviews/",
        "research/harness_rsi_v1/state/",
        "research/harness_rsi_v1/runs/T6/_dispatch/",
    )
    for binding in receipt["input_bindings"]:
        path = Path(binding["path"])
        try:
            relative = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            binding_failures.append({"path": str(path), "error": "outside repository"})
            continue
        if not relative.startswith(allowed_binding_prefixes):
            binding_failures.append({"path": relative, "error": "not allowlisted"})
        git_result = command(["git", "rev-parse", f"HEAD:{relative}"])
        actual_blob = git_result.stdout.decode().strip()
        if actual_blob != binding["git_blob_id"]:
            binding_failures.append({"path": relative, "error": "git blob drift"})
        if sha256_file(path) != binding["sha256"]:
            binding_failures.append({"path": relative, "error": "sha256 drift"})
    add(
        checks,
        "input_binding_drift",
        not binding_failures,
        f"{len(receipt['input_bindings'])} bindings recomputed",
    )

    prompt_source = REPO_ROOT / "research/harness_rsi_v1/runs/T6/_dispatch/loop_a_prompt_t6.md"
    add(
        checks,
        "task_prompt_verbatim",
        prompt_source.read_bytes() == (RUN_ROOT / "TASK_PROMPT.md").read_bytes(),
        "TASK_PROMPT.md is byte-identical to dispatch source",
    )

    parent_validation = command(
        [sys.executable, "-B", str(ARCHIVE_ROOT / "archive.py"), "validate-parents"]
    )
    parent_output = json.loads(parent_validation.stdout)
    add(
        checks,
        "parent_content_groups",
        parent_validation.returncode == 0
        and parent_output["passed"]
        and all(item["actual_member_count"] == item["actual_member_count"] for item in parent_output["parents"]),
        "T5 45 and T4 64 parent members recompute",
    )
    t5_result = next(item for item in parent_output["parents"] if item["run_id"] == "20261014T233742Z_cb132ce7")
    add(
        checks,
        "t5_declared_modes",
        t5_result["raw_mode_conformance"] == {"declared": 45, "matched": 45},
        "T5 manifest modes 45/45 match delivery",
    )

    registered = load_json(
        REPO_ROOT
        / "research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/registered_operations.json"
    )
    registered_ids = {operation["op_id"] for operation in registered["operations"]}
    gate_keys = {
        "severe_defect_miss",
        "legitimate_false_block",
        "evidence_completeness",
        "claim_overreach",
        "raw_record_integrity",
        "budget_integrity",
    }
    candidate_failures = []
    candidate_ids = []
    evaluations = []
    for candidate_path in sorted((RUN_ROOT / "candidate_packages").glob("*/candidate.json")):
        candidate = load_json(candidate_path)
        candidate_ids.append(candidate["candidate_id"])
        if archive.candidate_id(candidate) != candidate["candidate_id"]:
            candidate_failures.append(f"candidate id mismatch:{candidate_path}")
        if len(candidate["entries"]) != 3:
            candidate_failures.append(f"entry count !=3:{candidate_path}")
        if any(entry["op_id"] not in registered_ids for entry in candidate["entries"]):
            candidate_failures.append(f"unregistered operation:{candidate_path}")
        if set(candidate["six_gate_targets"]) != gate_keys:
            candidate_failures.append(f"six-gate keys mismatch:{candidate_path}")
        for field in ("identity", "selection_rationale", "entries", "six_gate_targets", "evaluation_plan", "cost_record", "version_applicability"):
            if field not in candidate:
                candidate_failures.append(f"missing A1 field {field}:{candidate_path}")
        evaluation_path = candidate_path.parent / "evaluation.json"
        evaluation = load_json(evaluation_path)
        evaluations.append(evaluation)
        if archive.evaluation_id(evaluation) != evaluation["evaluation_id"]:
            candidate_failures.append(f"evaluation id mismatch:{evaluation_path}")
        if evaluation["candidate_id"] != candidate["candidate_id"]:
            candidate_failures.append(f"evaluation/candidate mismatch:{evaluation_path}")
    add(
        checks,
        "a1_candidates",
        len(candidate_ids) == 2 and not candidate_failures,
        "two candidates: parents/changes/six gates/evaluation/cost complete; exactly three entries each",
    )

    rejected_path = RUN_ROOT / "candidate_packages/cand-20a78eae4dda3ca9/candidate.json"
    rejected = archive.evaluate_candidate(rejected_path, ARCHIVE_ROOT)
    proposed = archive.evaluate_candidate(
        RUN_ROOT / "candidate_packages/cand-d44c49dec4d95741/candidate.json",
        ARCHIVE_ROOT,
    )
    add(
        checks,
        "a2_rejected_not_enabled",
        rejected["status"] == "REJECTED_DUPLICATE_NOGOOD"
        and rejected["activation_enabled"] is False
        and rejected["rejection_is_permanent"] is False
        and proposed["activation_enabled"] is False,
        "duplicate no-good rejected and not enabled; all activation flags false",
    )

    evidence_count = archive.count_evidence(RUN_ROOT / "candidate_packages")
    add(
        checks,
        "a2_evidence_dedup",
        evidence_count["raw_candidate_reference_count"] == 6
        and evidence_count["global_unique_evidence_count"] == 5
        and evidence_count["references_suppressed_as_duplicates"] == 1
        and len(evidence_count["duplicate_candidate_pairs"]) == 1,
        "raw 6 / unique 5 / one cross-candidate duplicate",
    )

    usage = receipt["usage"]
    zero_keys = (
        "additional_cheap_requests",
        "additional_strong_requests",
        "model_calls",
        "network_calls",
        "remote_calls",
        "production_calls",
        "database_calls",
        "training_calls",
        "daemon_calls",
        "loop_b_calls",
        "automatic_retries",
    )
    add(
        checks,
        "a3_zero_calls",
        all(usage[key] == 0 for key in zero_keys)
        and usage["additional_cheap_requests_max"] == 4
        and usage["additional_strong_requests_max"] == 0,
        "usage 0/4 cheap, 0 strong, all external/model counters zero",
    )

    manifest = load_json(RUN_ROOT / "artifacts_manifest.json")
    manifest_failures = []
    manifest_paths = set()
    for artifact in manifest["artifacts"]:
        path = Path(artifact["absolute_path"])
        manifest_paths.add(path.resolve())
        if not path.is_file():
            manifest_failures.append(f"missing:{path}")
            continue
        if path.stat().st_size != artifact["bytes"]:
            manifest_failures.append(f"bytes:{path}")
        if sha256_file(path) != artifact["sha256"]:
            manifest_failures.append(f"sha256:{path}")
        if normalized_mode(path) != artifact["mode"]:
            manifest_failures.append(f"mode:{path}")
    actual_paths = {
        path.resolve()
        for path in RUN_ROOT.rglob("*")
        if path.is_file() and path.name != "artifacts_manifest.json"
    }
    if actual_paths != manifest_paths:
        manifest_failures.append("manifest file-set mismatch")
    add(
        checks,
        "artifact_manifest",
        not manifest_failures and manifest["artifact_count"] == len(manifest["artifacts"]),
        f"{manifest['artifact_count']} artifacts bytes/sha256/mode/file-set verified",
    )

    evidence_registry = load_json(ARCHIVE_ROOT / "fixtures/evidence_registry.json")
    evidence_failures = []
    for evidence in evidence_registry["evidence"]:
        path = REPO_ROOT / evidence["path"]
        if sha256_file(path) != evidence["sha256"]:
            evidence_failures.append(f"sha256:{evidence['evidence_id']}")
        blob = command(["git", "rev-parse", f"HEAD:{evidence['path']}"]).stdout.decode().strip()
        if blob != evidence["git_blob_id"]:
            evidence_failures.append(f"blob:{evidence['evidence_id']}")
    add(checks, "evidence_hashes", not evidence_failures, "five evidence files recompute")

    markdown_results = []
    for path in sorted(RUN_ROOT.rglob("*.md")):
        result = command(
            [
                sys.executable,
                "scripts/graph/hooks/summary_recompute_guard.py",
                "check",
                str(path),
            ]
        )
        markdown_results.append(
            {"path": path.relative_to(RUN_ROOT).as_posix(), "returncode": result.returncode}
        )
    add(
        checks,
        "g1_all_markdown",
        markdown_results and all(item["returncode"] == 0 for item in markdown_results),
        f"{len(markdown_results)} Markdown files rc=0",
    )

    with tempfile.TemporaryDirectory(prefix="t6_g1_negative_") as temporary:
        temporary_path = Path(temporary)
        negative = temporary_path / "mismatch.md"
        text = (RUN_ROOT / "summary.md").read_text(encoding="utf-8")
        text = text.replace("usage.additional_cheap_requests = 0", "usage.additional_cheap_requests = 1")
        negative.write_text(text, encoding="utf-8")
        mismatch = command(
            [
                sys.executable,
                "scripts/graph/hooks/summary_recompute_guard.py",
                "check",
                str(negative),
            ]
        )
    add(
        checks,
        "g1_runtime_negative_control",
        mismatch.returncode != 0,
        f"runtime-only mismatch guard rc={mismatch.returncode}; not persisted",
    )

    status = command(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    status_lines = status.stdout.decode("utf-8").splitlines()
    allowed_outside = (
        "logs/graph/dispatch_log.md",
        "logs/graph/docs_lint_report.json",
        "logs/graph/governance_drift_latest.md",
        "logs/graph/verify-report.json",
        "research/harness_rsi_v1/runs/T4/20261014T174628Z_2cc25c92/",
    )
    run_prefix = "research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/"
    boundary_failures = []
    for line in status_lines:
        entry = line[3:]
        if entry.startswith(run_prefix) or any(entry.startswith(prefix) for prefix in allowed_outside):
            continue
        boundary_failures.append(line)
    ignored = command(["git", "status", "--porcelain=v1", "--ignored=matching", "--untracked-files=all"])
    ignored_t6 = [
        line
        for line in ignored.stdout.decode("utf-8").splitlines()
        if line.startswith("!!")
        and "runs/T6/20261015T012906Z_b9bb8ca6" in line
    ]
    add(
        checks,
        "write_boundary",
        not boundary_failures and not ignored_t6,
        f"outside-run status matches pre-existing dirty set; ignored T6 entries={len(ignored_t6)}",
    )

    index = load_json(RUN_ROOT / "candidate_index.json")
    add(
        checks,
        "a_common_unknowns_and_index",
        index["batch"]["candidate_count"] == len(candidate_ids)
        and index["activation"]["enabled_candidate_count"] == 0
        and all("value" in item and "reason" in item for item in receipt["unresolved"]),
        "index totals match; unknowns explicit; no enabled candidate",
    )

    failed = [item for item in checks if not item["passed"]]
    output = {
        "checks": checks,
        "failed_count": len(failed),
        "markdown_results": markdown_results,
        "overall": "CONTRACT_PASS" if not failed else "FAIL",
        "schema": "jinrong_t6_self_check_v1",
    }
    json.dump(output, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
