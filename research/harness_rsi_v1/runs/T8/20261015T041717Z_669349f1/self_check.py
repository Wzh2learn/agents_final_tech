#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


RUN_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RUN_ROOT.parents[4]
RUN_REL = RUN_ROOT.relative_to(REPO_ROOT).as_posix()
SHADOW_STATUS = "NOT_SATISFIED_NO_THREE_TASK_WINDOWS"
COMPOSITE_GROUP = "sha256:e16cde27ff239da0c7b76f35272e0950e1cb9f0878d464b0ae6629e88d4c4f86"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalize_mode(value: int | str) -> str:
    mode = int(str(value), 8) if isinstance(value, str) else value
    return "100755" if mode & 0o111 else "100644"


def run_git(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def git_blob(path: Path) -> str:
    result = run_git(["rev-parse", f"HEAD:{path.relative_to(REPO_ROOT).as_posix()}"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def group_for(component: dict[str, object]) -> str:
    run_path = REPO_ROOT / str(component["path"])
    manifest = json.loads((run_path / "artifacts_manifest.json").read_text(encoding="utf-8"))
    members = []
    for artifact in manifest["artifacts"]:
        relative_path = artifact.get("relative_path")
        if not relative_path:
            relative_path = Path(artifact["absolute_path"]).relative_to(run_path).as_posix()
        file_path = run_path / relative_path
        actual = sha256_file(file_path)
        expected_key = "sha256_file" if "sha256_file" in artifact else "sha256"
        if actual != artifact[expected_key]:
            raise ValueError(f"component manifest mismatch: {file_path}")
        members.append(
            {
                "mode": normalize_mode(file_path.stat().st_mode & 0o777),
                "relative_path": relative_path,
                "sha256": actual,
            }
        )
    members.sort(key=lambda item: item["relative_path"])
    return "sha256:" + hashlib.sha256(canonical_bytes(members)).hexdigest()


def check(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"id": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def main() -> int:
    checks: list[dict[str, object]] = []
    json_files = sorted(RUN_ROOT.glob("*.json"))
    parsed = {}
    json_errors = []
    for path in json_files:
        try:
            parsed[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            json_errors.append(f"{path.name}: {exc}")
    jsonl_errors = []
    for line_number, line in enumerate((RUN_ROOT / "events.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        try:
            json.loads(line)
        except Exception as exc:
            jsonl_errors.append(f"line {line_number}: {exc}")
    checks.append(check("json_parse", not json_errors and not jsonl_errors, f"json={len(parsed)} errors={json_errors + jsonl_errors}"))

    receipt = parsed.get("receipt.json", {})
    required = {
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
    receipt_ok = (
        receipt.get("schema") == "receipt"
        and required <= set(receipt)
        and receipt.get("execution_status") == "DELIVERED"
        and receipt.get("acceptance_status") == "UNREVIEWED"
        and receipt.get("activation_status") == "NOT_ENABLED"
        and receipt.get("shadow_status") == SHADOW_STATUS
    )
    checks.append(check("receipt_contract", receipt_ok, f"required_missing={sorted(required - set(receipt))}"))

    shadow = parsed.get("shadow_comparison.json", {})
    results = shadow.get("task_results", [])
    a1 = (
        shadow.get("shadow_status") == SHADOW_STATUS
        and shadow.get("shadow_completed") is False
        and shadow.get("authorization_scope_check", {}).get("authorized_new_task_window_count") == 0
        and len(results) == 3
        and all(item.get("base_result") is None and item.get("candidate_result") is None for item in results)
        and all(item.get("status") == "NOT_EXECUTED_MISSING_APPROVED_WINDOW" for item in results)
    )
    checks.append(check("a1_three_real_new_task_evidence", a1, "status=NOT_SATISFIED; windows=0/3; results=3 empty unexecuted rows"))

    components = [
        {"path": "research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7", "commit": "115f396af6ea461c156d91ad9148414387724eb3", "group": "sha256:4f7d7af42ee6a1364e01c7b0e5213108025c9e69f1f212b65b11da03d3aa2f54", "task": "T5"},
        {"path": "research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6", "commit": "ef5e84edbd4fcd35cc287316c0e994cf72f6faa4", "group": "sha256:a123480270ebdfc1d9ecb8bf74928676810ba2507290f5708911774c1755a1b7", "task": "T6"},
        {"path": "research/harness_rsi_v1/runs/T7/20261015T025839Z_c94af776", "commit": "0579b64bbc4423b52055d37e0f81cd0715f453bb", "group": "sha256:363991a2cccccc4581ecafefdb73dc569dd2ab6333bd0514927e48ed7b2f5ff7", "task": "T7"},
    ]
    component_results = []
    for component in components:
        actual_group = group_for(component)
        diff = run_git(["diff", "--quiet", component["commit"], component["path"]])
        component_results.append(
            {
                "task": component["task"],
                "group_match": actual_group == component["group"],
                "commit_tree_match": diff.returncode == 0,
            }
        )
    composite = "sha256:" + hashlib.sha256(
        canonical_bytes(
            sorted(
                [
                    {
                        "content_group_id": component["group"],
                        "git_commit": component["commit"],
                        "member_count": 45 if component["task"] == "T5" else 30 if component["task"] == "T6" else 57,
                        "run_id": Path(component["path"]).name,
                        "task_id": component["task"],
                    }
                    for component in components
                ],
                key=lambda item: item["task_id"],
            )
        )
    ).hexdigest()
    t6_candidate = REPO_ROOT / "research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/candidate_packages/cand-d44c49dec4d95741/candidate.json"
    t7_candidate = REPO_ROOT / "research/harness_rsi_v1/runs/T7/20261015T025839Z_c94af776/amended_candidate.json"
    t6_review = json.loads((REPO_ROOT / "research/harness_rsi_v1/reviews/T6R-01/review_receipt.json").read_text(encoding="utf-8"))
    t7_review = json.loads((REPO_ROOT / "research/harness_rsi_v1/reviews/T7R-01/review_receipt.json").read_text(encoding="utf-8"))
    t6_accepted = next(item["sha256"] for item in t6_review["reviewed_artifact_sha256"] if item.get("relative_path") == "candidate_packages/cand-d44c49dec4d95741/candidate.json")
    t7_accepted = next(item["sha256_file"] for item in t7_review["reviewed_artifact_sha256"] if item["path"].endswith("/amended_candidate.json"))
    archive = REPO_ROOT / "research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/archive.py"
    descriptor = REPO_ROOT / "research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/fixtures/parent_versions.json"
    parent_validation = subprocess.run(
        [sys.executable, "-B", str(archive), "validate-parents", str(descriptor)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    parent_payload = json.loads(parent_validation.stdout)
    a2 = (
        all(item["group_match"] and item["commit_tree_match"] for item in component_results)
        and composite == COMPOSITE_GROUP
        and sha256_file(t6_candidate) == t6_accepted
        and sha256_file(t7_candidate) == t7_accepted
        and parent_validation.returncode == 0
        and parent_payload.get("passed") is True
        and shadow.get("candidate_hash_acceptance_consistency", {}).get("installation_state", "").startswith("NOT_ESTABLISHED")
        and shadow.get("candidate_hash_acceptance_consistency", {}).get("loading_state", "").startswith("NOT_ESTABLISHED")
    )
    checks.append(check("a2_candidate_hash_acceptance_consistency", a2, f"components={component_results} composite_match={composite == COMPOSITE_GROUP} parent_rc={parent_validation.returncode}"))

    rollback = parsed.get("rollback_receipt.json", {})
    before = rollback.get("old_evidence_before", {})
    after = rollback.get("old_evidence_after", {})
    evidence_failures = []
    for relative_path, expected in before.items():
        path = REPO_ROOT / relative_path
        actual = {
            "bytes": path.stat().st_size,
            "git_blob_id": git_blob(path),
            "mode": oct(path.stat().st_mode & 0o777),
            "sha256_file": sha256_file(path),
        }
        if expected != after.get(relative_path) or expected != actual:
            evidence_failures.append({"path": relative_path, "expected": expected, "actual": actual, "after": after.get(relative_path)})
    usage = receipt.get("usage", {})
    zero_keys = ["additional_cheap_requests", "additional_strong_requests", "automatic_retries", "model_calls", "network_calls", "remote_calls", "production_calls", "database_calls", "training_calls", "daemon_calls", "loop_b_calls"]
    a3 = (
        not evidence_failures
        and rollback.get("verification", {}).get("old_evidence_unchanged") is True
        and rollback.get("drill_status") == "PASS_SIMULATED_ONLY"
        and all(usage.get(key) == 0 for key in zero_keys)
        and usage.get("execution_chat_usage") == "UNRESOLVED"
        and shadow.get("candidate_enabled") is False
        and parsed.get("release_proposal.json", {}).get("enabled") is False
        and parsed.get("release_proposal.json", {}).get("distribution_started") is False
    )
    checks.append(check("a3_old_experiments_and_authority", a3, f"old_evidence_failures={evidence_failures} usage_zero={all(usage.get(key) == 0 for key in zero_keys)}"))

    manifest = parsed.get("artifacts_manifest.json", {})
    manifest_failures = []
    actual_files = {
        path
        for path in RUN_ROOT.rglob("*")
        if path.is_file() and path.name not in {"artifacts_manifest.json"} and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    declared_files = set()
    for item in manifest.get("artifacts", []):
        path = Path(item["absolute_path"])
        declared_files.add(path)
        if not str(path).startswith(str(RUN_ROOT) + os.sep):
            manifest_failures.append(f"allowlist:{path}")
            continue
        if not path.is_file() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"] or normalize_mode(path.stat().st_mode & 0o777) != item["mode"]:
            manifest_failures.append(f"identity:{path}")
    if actual_files != declared_files:
        manifest_failures.append(f"set_diff missing={sorted(str(p) for p in actual_files - declared_files)} extra={sorted(str(p) for p in declared_files - actual_files)}")

    status = run_git(["status", "--short", "--untracked-files=all"])
    allowed_modified = {
        "logs/graph/dispatch_log.md",
        "logs/graph/docs_lint_report.json",
        "logs/graph/governance_drift_latest.md",
        "logs/graph/verify-report.json",
    }
    outside_ok = True
    for line in status.stdout.splitlines():
        if line[3:].startswith(RUN_REL + "/"):
            continue
        kind, path = line[:2], line[3:]
        if kind.strip() == "M" and path in allowed_modified:
            continue
        if kind.strip() == "??" and path.startswith("research/harness_rsi_v1/runs/T4/20261014T174628Z_2cc25c92/"):
            continue
        outside_ok = False
    residue = [
        path.relative_to(RUN_ROOT).as_posix()
        for path in RUN_ROOT.rglob("*")
        if (path.is_dir() and path.name in {".omc", "__pycache__", "tmp"}) or (path.is_file() and path.suffix == ".pyc")
    ]
    ignored_failures = []
    for path in actual_files:
        result = run_git(["check-ignore", "-q", path.relative_to(REPO_ROOT).as_posix()])
        if result.returncode == 0:
            ignored_failures.append(path.relative_to(REPO_ROOT).as_posix())
    a_common = not json_errors and not jsonl_errors and required <= set(receipt) and not manifest_failures and outside_ok and not residue and not ignored_failures
    checks.append(check("a_common_json_required_paths_hashes_write_boundary", a_common, f"manifest_failures={manifest_failures} outside_ok={outside_ok} residue={residue} ignored={ignored_failures}"))

    prompt_equal = (RUN_ROOT / "TASK_PROMPT.md").read_bytes() == (REPO_ROOT / "research/harness_rsi_v1/runs/T8/_dispatch/loop_a_prompt_t8.md").read_bytes()
    checks.append(check("task_prompt_verbatim", prompt_equal, f"bytes={len((RUN_ROOT / 'TASK_PROMPT.md').read_bytes())}"))

    markdown_results = []
    for path in sorted(RUN_ROOT.glob("*.md")):
        result = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / "scripts/graph/hooks/summary_recompute_guard.py"), "check", str(path)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        markdown_results.append({"path": path.name, "rc": result.returncode, "stderr": result.stderr.strip()})
    g1_ok = bool(markdown_results) and all(item["rc"] == 0 for item in markdown_results)
    checks.append(check("g1_every_markdown_rc0", g1_ok, f"results={markdown_results}"))

    mode_failures = []
    for path in RUN_ROOT.rglob("*"):
        if path.is_file() and stat.S_IMODE(path.stat().st_mode) != 0o755:
            mode_failures.append(f"{path.relative_to(RUN_ROOT).as_posix()}:{oct(stat.S_IMODE(path.stat().st_mode))}")
    checks.append(check("mode_full_set_755", not mode_failures, f"failures={mode_failures}"))

    passed = all(item["status"] == "PASS" for item in checks)
    output = {
        "schema": "jinrong_t8_self_check_v1",
        "task_id": "T8",
        "run_id": RUN_ROOT.name,
        "overall": "CONTRACT_PASS" if passed else "CONTRACT_FAIL",
        "checks": checks,
        "g1_markdown": f"{sum(item['rc'] == 0 for item in markdown_results)}/{len(markdown_results)} rc=0",
        "usage": usage,
        "claim_scope": "Local deterministic contract only; no experiment, scientific success, installation, loading, production, endpoint, or independent-acceptance claim.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
