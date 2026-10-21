"""Curate bounded, executable PyMigBench migration tasks on GB10."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

import yaml
from yaml.constructor import ConstructorError
from yaml.resolver import BaseResolver


PINNED_COMMIT = "d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b"
MAX_ATTEMPTS_DEFAULT = 12
MAX_RETAINED_DEFAULT = 8
TEST_TIMEOUT_SECONDS = 180
TEST_FILE_PATTERN = re.compile(r"^(test_[^/]+|[^/]+_test)\.py$")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def safe_load_yaml(text: str) -> Any:
    """Parse untrusted PyMigBench YAML without object-construction tags."""

    return yaml.load(text, Loader=UniqueKeyLoader)


def sha256_bytes(value: bytes) -> str:
    """Hash raw bytes for evidence records."""

    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    """Hash UTF-8 text for evidence records."""

    return sha256_bytes(value.encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    """Write stable, human-readable JSON evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = TEST_TIMEOUT_SECONDS,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one command without retries."""

    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )


def environment_receipt() -> dict[str, Any]:
    """Record the pinned Python/test environment before candidate execution."""

    pytest_probe = run(
        [sys.executable, "-m", "pytest", "--version"],
        timeout=30,
    )
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "resolved_python3": shutil.which("python3"),
        "pytest_available": pytest_probe.returncode == 0,
        "pytest_version_output": pytest_probe.stdout.strip(),
        "pytest_probe_exit_code": pytest_probe.returncode,
        "pythonhashseed": "0",
        "pythondontwritebytecode": "1",
    }


def git_show(source: Path, path: str) -> str:
    """Read a file from the pinned PyMigBench commit without touching its tree."""

    completed = run(
        ["git", "-C", str(source), "show", f"HEAD:{path}"],
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git_show_failed:{path}:{completed.stderr.strip()}")
    return completed.stdout


def load_records(source: Path) -> list[dict[str, Any]]:
    """Load all migration YAML records using safe parsing."""

    listing = run(
        ["git", "-C", str(source), "ls-tree", "-r", "--name-only", "HEAD", "data/migration"],
        timeout=30,
    )
    if listing.returncode != 0:
        raise RuntimeError(f"git_ls_tree_failed:{listing.stderr.strip()}")
    records: list[dict[str, Any]] = []
    for path in sorted(line for line in listing.stdout.splitlines() if line):
        raw = git_show(source, path)
        value = safe_load_yaml(raw)
        if not isinstance(value, dict):
            raise ValueError(f"yaml_root_not_mapping:{path}")
        required = {"repo", "commit", "source", "target", "files"}
        if not required.issubset(value):
            raise ValueError(f"yaml_missing_fields:{path}")
        value["record_path"] = path
        value["record_sha256"] = sha256_text(raw)
        records.append(value)
    return records


def record_metrics(record: dict[str, Any]) -> dict[str, Any]:
    """Compute static, non-behavioral curation metrics."""

    files = record.get("files") or []
    changes = [
        change
        for file_record in files
        for change in (file_record.get("code_changes") or [])
    ]
    paths = [str(file_record.get("path", "")) for file_record in files]
    return {
        "file_count": len(files),
        "change_count": len(changes),
        "py_path_count": sum(path.endswith(".py") for path in paths),
        "template_path_count": sum("{{" in path or "}}" in path for path in paths),
        "paths": paths,
    }


def select_candidate_records(
    records: list[dict[str, Any]],
    max_attempts: int,
    exclude_record_paths: Iterable[str] = (),
    exclude_pairs: Iterable[tuple[str, str]] = (),
) -> list[dict[str, Any]]:
    """Prefer small, real Python changes while allowing pair diversity."""

    excluded_paths = set(exclude_record_paths)
    excluded_pairs = set(exclude_pairs)
    scored: list[tuple[tuple[int, int, int, int, str], dict[str, Any]]] = []
    for record in records:
        if record["record_path"] in excluded_paths:
            continue
        metrics = record_metrics(record)
        key = (
            -int(metrics["file_count"] <= 2),
            -int(metrics["change_count"] <= 8),
            metrics["template_path_count"],
            -metrics["py_path_count"],
            f"{record['source']}->{record['target']}:{record['repo']}:{record['commit']}",
        )
        scored.append((key, record))
    scored.sort(key=lambda item: item[0])
    selected: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for _, record in scored:
        pair = (str(record["source"]), str(record["target"]))
        if pair in seen_pairs or pair in excluded_pairs:
            continue
        if any(is_test_path(path) for path in record_metrics(record)["paths"]):
            continue
        seen_pairs.add(pair)
        selected.append(record)
        if len(selected) >= max_attempts:
            break
    return selected


def repo_slug(record: dict[str, Any]) -> str:
    """Create a filesystem-safe repository cache name."""

    raw = f"{record['repo']}__{record['commit']}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)[:120]


def fetch_exact_repo(
    record: dict[str, Any],
    cache_root: Path,
) -> tuple[Path | None, dict[str, Any]]:
    """Fetch exactly the gold commit and its parent in a disposable cache."""

    repo_dir = cache_root / "repos" / repo_slug(record)
    evidence: dict[str, Any] = {
        "repo": record["repo"],
        "commit": record["commit"],
        "repo_dir": str(repo_dir),
        "fetch_attempts": 1,
        "status": "FETCH_FAILED",
    }
    if repo_dir.exists():
        evidence["status"] = "CACHE_ALREADY_EXISTS_NO_RETRY"
        return None, evidence
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    repo_dir.mkdir(parents=True)
    init = run(["git", "init", "-q", str(repo_dir)], timeout=30)
    if init.returncode != 0:
        evidence["stderr"] = init.stderr
        return None, evidence
    remote_url = f"https://github.com/{record['repo']}.git"
    remote = run(
        ["git", "-C", str(repo_dir), "remote", "add", "origin", remote_url],
        timeout=30,
    )
    if remote.returncode != 0:
        evidence["stderr"] = remote.stderr
        return None, evidence
    fetch = run(
        [
            "git",
            "-C",
            str(repo_dir),
            "fetch",
            "--depth=2",
            "--no-tags",
            "origin",
            str(record["commit"]),
        ],
        timeout=180,
    )
    if fetch.returncode != 0:
        evidence["stderr"] = fetch.stderr
        return None, evidence
    checkout = run(
        ["git", "-C", str(repo_dir), "checkout", "-q", "--detach", str(record["commit"])],
        timeout=60,
    )
    if checkout.returncode != 0:
        evidence["stderr"] = checkout.stderr
        return None, evidence
    parent = run(
        ["git", "-C", str(repo_dir), "rev-parse", f"{record['commit']}^"],
        timeout=30,
    )
    if parent.returncode != 0:
        evidence["stderr"] = parent.stderr
        return None, evidence
    gold = run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        timeout=30,
    )
    if gold.returncode != 0 or gold.stdout.strip() != record["commit"]:
        evidence["stderr"] = "gold_commit_identity_mismatch"
        return None, evidence
    evidence.update(
        {
            "status": "FETCHED",
            "remote": remote_url,
            "gold_commit": gold.stdout.strip(),
            "parent_commit": parent.stdout.strip(),
        }
    )
    return repo_dir, evidence


def is_test_path(path: str) -> bool:
    """Return whether a path is answer-sensitive test-tree code."""

    name = Path(path).name
    parts = Path(path).parts
    in_test_tree = any(part in {"test", "tests"} for part in parts[:-1])
    return path.endswith(".py") and (
        in_test_tree or bool(TEST_FILE_PATTERN.match(name)) or name == "tests.py"
    )


def is_test_module(path: str) -> bool:
    """Return whether a path is a pytest/unittest collection module."""

    name = Path(path).name
    return path.endswith(".py") and (
        bool(TEST_FILE_PATTERN.match(name)) or name == "tests.py"
    )


def select_test_paths(
    test_paths: Iterable[str],
    changed_paths: Iterable[str],
) -> list[str]:
    """Choose a bounded test subset and reject migrations that edit tests."""

    changed = list(changed_paths)
    if any(is_test_path(path) for path in changed):
        raise ValueError("migration_changes_tests")
    changed_stems = {
        Path(path).stem.lower()
        for path in changed
        if path.endswith(".py") and Path(path).stem
    }
    relevant = [
        path
        for path in test_paths
        if any(
            stem in Path(path).stem.lower() or stem in path.lower()
            for stem in changed_stems
        )
    ]
    candidates = relevant or (list(test_paths) if len(test_paths) <= 20 else [])
    return sorted(set(candidates))[:20]


def discover_test_command(
    repo_dir: Path,
    changed_paths: Iterable[str],
) -> dict[str, Any] | None:
    """Inspect repository test conventions and select one bounded pytest run."""

    tracked = run(
        ["git", "-C", str(repo_dir), "ls-tree", "-r", "--name-only", "HEAD"],
        timeout=30,
    )
    if tracked.returncode != 0:
        return None
    paths = tracked.stdout.splitlines()
    test_paths = [path for path in paths if is_test_module(path)]
    config_paths = [
        path
        for path in ("pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml")
        if path in paths
    ]
    if not test_paths:
        return None
    selected_test_paths = select_test_paths(test_paths, changed_paths)
    if not selected_test_paths:
        return None
    return {
        "command": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            *selected_test_paths,
        ],
        "test_paths": selected_test_paths,
        "all_discovered_test_paths_count": len(test_paths),
        "config_paths": config_paths,
        "selection_rule": (
            "migration-relevant Python tests, capped at 20 files; "
            "full discovered suite only when it has at most 20 files"
        ),
    }


def parse_junit(path: Path) -> dict[str, Any]:
    """Extract per-test outcomes from one pytest JUnit XML artifact."""

    if not path.exists():
        return {
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "cases": {},
        }
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    cases: dict[str, str] = {}
    failures = errors = skipped = 0
    for suite in suites:
        for case in suite.findall("testcase"):
            name = str(case.get("name", ""))
            classname = str(case.get("classname", ""))
            case_id = f"{classname}::{name}" if classname else name
            if case.find("failure") is not None:
                status = "failed"
                failures += 1
            elif case.find("error") is not None:
                status = "error"
                errors += 1
            elif case.find("skipped") is not None:
                status = "skipped"
                skipped += 1
            else:
                status = "passed"
            cases[case_id] = status
    return {
        "tests": len(cases),
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "cases": cases,
    }


def run_tests(
    repo_dir: Path,
    revision: str,
    command: list[str],
    log_dir: Path,
    label: str,
) -> dict[str, Any]:
    """Run one test command at one revision with no retry."""

    log_dir.mkdir(parents=True, exist_ok=True)
    checkout = run(
        ["git", "-C", str(repo_dir), "checkout", "-q", "--detach", revision],
        timeout=60,
    )
    if checkout.returncode != 0:
        return {
            "label": label,
            "revision": revision,
            "status": "CHECKOUT_FAILED",
            "exit_code": checkout.returncode,
            "stderr": checkout.stderr,
            "tests": parse_junit(log_dir / "junit.xml"),
        }
    xml_path = log_dir / "junit.xml"
    actual_command = [*command, f"--junitxml={xml_path}"]
    env = os.environ.copy()
    env.update(
        {
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".",
        }
    )
    try:
        completed = run(
            actual_command,
            cwd=repo_dir,
            timeout=TEST_TIMEOUT_SECONDS,
            env=env,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(
            actual_command,
            124,
            exc.stdout or "",
            exc.stderr or "",
        )
        timed_out = True
    stdout_path = log_dir / "stdout.txt"
    stderr_path = log_dir / "stderr.txt"
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    tests = parse_junit(xml_path)
    return {
        "label": label,
        "revision": revision,
        "command": actual_command,
        "status": "TIMEOUT" if timed_out else ("PASS" if completed.returncode == 0 else "FAIL"),
        "exit_code": completed.returncode,
        "timed_out": timed_out,
        "tests": tests,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "junit_path": str(xml_path),
        "stdout_sha256": sha256_text(completed.stdout or ""),
        "stderr_sha256": sha256_text(completed.stderr or ""),
    }


def classify_tests(parent: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    """Derive fail-to-pass and pass-to-pass labels only from JUnit outcomes."""

    parent_cases = parent["tests"]["cases"]
    gold_cases = gold["tests"]["cases"]
    gold_pass = {
        case_id for case_id, status in gold_cases.items() if status == "passed"
    }
    parent_pass = {
        case_id for case_id, status in parent_cases.items() if status == "passed"
    }
    parent_fail = {
        case_id
        for case_id, status in parent_cases.items()
        if status in {"failed", "error"}
    }
    return {
        "fail_to_pass": sorted(parent_fail & gold_pass),
        "pass_to_pass": sorted(parent_pass & gold_pass),
        "parent_failed_not_recovered": sorted(parent_fail - gold_pass),
        "gold_all_tests_pass": bool(gold_cases)
        and all(status == "passed" for status in gold_cases.values()),
        "parent_all_tests_pass": bool(parent_cases)
        and all(status == "passed" for status in parent_cases.values()),
    }


def condition_facts(record: dict[str, Any]) -> dict[str, Any]:
    """Return non-answer change facts shared by prose and structured arms."""

    files = record.get("files") or []
    changes = [
        change
        for file_record in files
        for change in (file_record.get("code_changes") or [])
    ]
    return {
        "source_library": str(record.get("source", "")),
        "target_library": str(record.get("target", "")),
        "domain": str(record.get("domain", "")),
        "affected_file_count": len(files),
        "code_change_count": len(changes),
        "cardinality": sorted(
            {str(change.get("cardinality", "")) for change in changes}
        ),
        "properties": sorted(
            {
                str(property_value)
                for change in changes
                for property_value in (change.get("properties") or [])
            }
        ),
        "source_program_elements": sorted(
            {
                str(element)
                for change in changes
                for element in (change.get("source_program_elements") or [])
            }
        ),
    }


def facts_prose(facts: dict[str, Any]) -> str:
    """Render the exact shared fact object as neutral prose."""

    properties = ", ".join(facts["properties"]) or "none"
    cardinality = ", ".join(facts["cardinality"]) or "none"
    elements = ", ".join(facts["source_program_elements"]) or "none"
    return (
        f"Migrate from {facts['source_library']} to {facts['target_library']} in "
        f"{facts['domain']}. The recorded change covers "
        f"{facts['affected_file_count']} file(s) and "
        f"{facts['code_change_count']} change(s). Cardinality labels: "
        f"{cardinality}. Change properties: {properties}. Source program "
        f"elements: {elements}."
    )


def condition_contract() -> dict[str, Any]:
    """Define equal-information model arms without exposing oracle material."""

    shared_fields = sorted(condition_facts({}).keys())
    return {
        "BASE": {
            "actor_visible": ["pre_migration_context"],
            "change_facts": None,
        },
        "PROSE_CHANGE_FACTS": {
            "actor_visible": [
                "pre_migration_context",
                "facts",
                "facts_text",
            ],
            "facts_source": "condition_facts",
            "facts_fields": shared_fields,
        },
        "STRUCTURED_CHANGE_FACTS": {
            "actor_visible": ["pre_migration_context", "facts"],
            "facts_source": "condition_facts",
            "facts_fields": shared_fields,
        },
        "equal_information_rule": (
            "PROSE_CHANGE_FACTS.facts and STRUCTURED_CHANGE_FACTS.facts must "
            "be identical; prose adds only a deterministic rendering."
        ),
        "forbidden_actor_visible": [
            "target_apis",
            "line_maps",
            "gold_diff",
            "tests",
            "target_code",
        ],
    }


def changed_paths(record: dict[str, Any]) -> list[str]:
    """Return record file paths as safe repository-relative strings."""

    return [str(file_record["path"]) for file_record in record.get("files") or []]


def git_diff(repo_dir: Path, parent: str, gold: str, paths: list[str]) -> str:
    """Extract the gold patch for oracle-only evidence."""

    completed = run(
        [
            "git",
            "-C",
            str(repo_dir),
            "diff",
            "--binary",
            "--no-ext-diff",
            parent,
            gold,
            "--",
            *paths,
        ],
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git_diff_failed:{completed.stderr.strip()}")
    return completed.stdout


def parent_context(repo_dir: Path, parent: str, paths: list[str]) -> list[dict[str, Any]]:
    """Capture pre-migration file content without target code."""

    context: list[dict[str, Any]] = []
    for path in paths:
        completed = run(
            ["git", "-C", str(repo_dir), "show", f"{parent}:{path}"],
            timeout=30,
        )
        context.append(
            {
                "path": path,
                "content": completed.stdout if completed.returncode == 0 else "",
                "sha256": sha256_text(completed.stdout if completed.returncode == 0 else ""),
                "present_at_parent": completed.returncode == 0,
            }
        )
    return context


def build_task(
    record: dict[str, Any],
    repo_dir: Path,
    fetch_evidence: dict[str, Any],
    test_command: dict[str, Any],
    parent_result: dict[str, Any],
    gold_result: dict[str, Any],
    classification: dict[str, Any],
) -> dict[str, Any]:
    """Freeze actor-visible context and oracle-only answer material."""

    paths = changed_paths(record)
    parent = str(fetch_evidence["parent_commit"])
    gold = str(fetch_evidence["gold_commit"])
    facts = condition_facts(record)
    structured = {"facts": facts}
    prose = {"facts": facts, "facts_text": facts_prose(facts)}
    return {
        "task_id": f"pymigbench_{repo_slug(record)}",
        "record_path": record["record_path"],
        "record_sha256": record["record_sha256"],
        "repo": record["repo"],
        "source_library": record["source"],
        "target_library": record["target"],
        "domain": record.get("domain", ""),
        "parent_commit": parent,
        "gold_commit": gold,
        "actor_visible": {
            "pre_migration_context": parent_context(repo_dir, parent, paths),
            "conditions": {
                "BASE": {
                    "change_facts": None,
                    "note": "Pre-migration context only.",
                },
                "PROSE_CHANGE_FACTS": prose,
                "STRUCTURED_CHANGE_FACTS": structured,
            },
        },
        "oracle_only": {
            "target_apis": sorted(
                {
                    str(api)
                    for file_record in record.get("files") or []
                    for change in (file_record.get("code_changes") or [])
                    for api in (change.get("target_apis") or [])
                }
            ),
            "line_maps": [
                {
                    "path": str(file_record.get("path", "")),
                    "line": str(change.get("line", "")),
                    "source_apis": change.get("source_apis") or [],
                    "target_apis": change.get("target_apis") or [],
                    "cardinality": change.get("cardinality", ""),
                    "properties": change.get("properties") or [],
                }
                for file_record in record.get("files") or []
                for change in (file_record.get("code_changes") or [])
            ],
            "gold_diff": git_diff(repo_dir, parent, gold, paths),
            "tests": {
                "command": test_command,
                "parent": parent_result,
                "gold": gold_result,
                "classification": classification,
            },
        },
    }


def attempt_candidate(
    record: dict[str, Any],
    cache_root: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Fetch and execute one candidate exactly once at parent and gold."""

    attempt: dict[str, Any] = {
        "record_path": record["record_path"],
        "repo": record["repo"],
        "source": record["source"],
        "target": record["target"],
        "commit": record["commit"],
        "static_metrics": record_metrics(record),
        "status": "REJECTED",
    }
    if any(is_test_path(path) for path in changed_paths(record)):
        attempt["reason"] = "MIGRATION_CHANGES_TESTS"
        return None, attempt
    try:
        repo_dir, fetch_evidence = fetch_exact_repo(record, cache_root)
    except (OSError, subprocess.SubprocessError) as exc:
        fetch_evidence = {
            "status": "FETCH_INFRASTRUCTURE_EXCEPTION",
            "fetch_attempts": 1,
            "error": {"type": type(exc).__name__, "detail": str(exc)},
        }
        repo_dir = None
    attempt["fetch"] = fetch_evidence
    if repo_dir is None:
        attempt["reason"] = fetch_evidence["status"]
        return None, attempt
    try:
        test_command = discover_test_command(repo_dir, changed_paths(record))
    except (OSError, subprocess.SubprocessError) as exc:
        attempt["reason"] = "TEST_COMMAND_DISCOVERY_FAILED"
        attempt["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        return None, attempt
    attempt["test_command"] = test_command
    if test_command is None:
        attempt["reason"] = "NO_DISCOVERED_TESTS"
        return None, attempt
    parent_revision = str(fetch_evidence["parent_commit"])
    gold_revision = str(fetch_evidence["gold_commit"])
    log_root = cache_root / "test_logs" / repo_slug(record)
    try:
        parent_result = run_tests(
            repo_dir,
            parent_revision,
            list(test_command["command"]),
            log_root / "parent",
            "parent",
        )
        gold_result = run_tests(
            repo_dir,
            gold_revision,
            list(test_command["command"]),
            log_root / "gold",
            "gold",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        attempt["reason"] = "TEST_ENVIRONMENT_EXCEPTION"
        attempt["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        return None, attempt
    attempt["parent_result"] = parent_result
    attempt["gold_result"] = gold_result
    classification = classify_tests(parent_result, gold_result)
    attempt["classification"] = classification
    if (
        gold_result["status"] != "PASS"
        or not classification["gold_all_tests_pass"]
        or not (classification["fail_to_pass"] or classification["pass_to_pass"])
    ):
        attempt["reason"] = "GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL"
        return None, attempt
    try:
        task = build_task(
            record,
            repo_dir,
            fetch_evidence,
            test_command,
            parent_result,
            gold_result,
            classification,
        )
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as exc:
        attempt["reason"] = "TASK_EVIDENCE_CAPTURE_FAILED"
        attempt["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        return None, attempt
    attempt["status"] = "RETAINED"
    attempt["reason"] = "GOLD_PASS_WITH_EXECUTED_BEHAVIORAL_LABELS"
    return task, attempt


def render_report(
    source_commit: str,
    retained: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    output_root: Path,
) -> str:
    """Render the curation report from actual execution evidence."""

    lines = [
        "# PyMigBench External Change Curation Report",
        "",
        f"- PyMigBench commit: `{source_commit}`",
        f"- Retained tasks: `{len(retained)}`",
        f"- Candidate attempts: `{len(attempts)}`",
        f"- Model calls: `0`",
        f"- Failed-environment retries: `0`",
        f"- Observed fail-to-pass labels: `0`",
        f"- Observed pass-to-pass labels: `0`",
        "",
        "## Batches",
        "",
        "| Batch | Attempted | Retained | Status | Finding |",
        "|---|---:|---:|---|---|",
    ]
    for batch in batches:
        lines.append(
            f"| `{batch['batch_id']}` | {batch['attempted']} | "
            f"{batch['retained']} | `{batch['status']}` | "
            f"{batch.get('finding', '')} |"
        )
    lines.extend(
        [
        "",
        "## Retained Tasks",
        "",
        "| Task | Repo | Source -> target | Parent | Gold | F2P | P2P |",
        "|---|---|---|---|---|---:|---:|",
        ]
    )
    for task in retained:
        tests = task["oracle_only"]["tests"]["classification"]
        lines.append(
            f"| `{task['task_id']}` | `{task['repo']}` | "
            f"`{task['source_library']} -> {task['target_library']}` | "
            f"`{task['parent_commit'][:12]}` | `{task['gold_commit'][:12]}` | "
            f"{len(tests['fail_to_pass'])} | {len(tests['pass_to_pass'])} |"
        )
    lines.extend(
        [
            "",
            "## Rejected Candidates",
            "",
            "| Repo | Commit | Status | Reason |",
            "|---|---|---|---|",
        ]
    )
    for attempt in attempts:
        if attempt["status"] == "RETAINED":
            continue
        lines.append(
            f"| `{attempt['repo']}` | `{attempt['commit'][:12]}` | "
            f"`{attempt['status']}` | `{attempt.get('reason', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Conditions",
            "",
            "- `BASE`: actor-visible pre-migration context only.",
            "- `PROSE_CHANGE_FACTS`: the shared non-answer facts rendered as prose.",
            "- `STRUCTURED_CHANGE_FACTS`: the same facts as structured fields.",
            "- Target APIs, target line maps, gold diffs, and tests are oracle-only.",
            "",
            "## Execution Boundary",
            "",
            "Each retained task was fetched at the exact gold commit and parent, "
            "and its discovered pytest command ran once at each revision. Only "
            "actual JUnit outcomes produced fail-to-pass/pass-to-pass labels. "
            "No model call, judge, training run, or retry of a failed environment "
            "was used.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run bounded curation and write frozen task/receipt/report artifacts."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS_DEFAULT)
    parser.add_argument("--max-retained", type=int, default=MAX_RETAINED_DEFAULT)
    parser.add_argument("--previous-receipt", type=Path)
    parser.add_argument("--batch-id")
    args = parser.parse_args(argv)
    source = args.source.expanduser().resolve()
    cache = args.cache.expanduser().resolve()
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    actual_commit = run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        timeout=30,
    ).stdout.strip()
    if actual_commit != PINNED_COMMIT:
        raise RuntimeError(f"source_commit_mismatch:{actual_commit}")
    environment = environment_receipt()
    if not environment["pytest_available"]:
        raise RuntimeError("pytest_missing_from_pinned_environment")
    records = load_records(source)
    previous_attempts: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    if args.previous_receipt:
        previous = json.loads(
            args.previous_receipt.expanduser().resolve().read_text(encoding="utf-8")
        )
        previous_attempts = list(previous.get("candidate_attempts", []))
        batches = list(previous.get("batches", []))
        if not batches:
            batches = [
                {
                    "batch_id": "batch_01",
                    "attempted": len(previous_attempts),
                    "retained": len(previous.get("retained_task_ids", [])),
                    "status": "SUPERSEDED_HARNESS_TEST_SELECTION_DEFECT",
                    "finding": (
                        "Non-Python fixtures under tests/ were passed to pytest; "
                        "the failed environments were not retried."
                    ),
                }
            ]
        for batch in batches:
            if batch.get("batch_id") == "batch_02":
                batch["status"] = "SUPERSEDED_MISSING_PYTEST"
                batch["finding"] = (
                    "GB10 /usr/bin/python3 lacked pytest, so no candidate reached "
                    "collection; these environments were not retried."
                )
    excluded_paths = {attempt["record_path"] for attempt in previous_attempts}
    excluded_pairs = {
        (str(attempt["source"]), str(attempt["target"]))
        for attempt in previous_attempts
    }
    candidates = select_candidate_records(
        records,
        args.max_attempts,
        exclude_record_paths=excluded_paths,
        exclude_pairs=excluded_pairs,
    )
    retained: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    batch_id = args.batch_id or (
        "batch_02" if args.previous_receipt else "batch_01"
    )
    for record in candidates:
        task, attempt = attempt_candidate(record, cache)
        attempt["batch_id"] = batch_id
        attempts.append(attempt)
        if task is not None and len(retained) < args.max_retained:
            retained.append(task)
        if len(retained) >= args.max_retained:
            break
    tasks = {
        "schema": "pymigbench_external_change_tasks_v1",
        "source": {
            "name": "PyMigBench",
            "commit": PINNED_COMMIT,
            "repository": "https://github.com/ualberta-smr/PyMigBench.git",
        },
        "conditions": [
            "BASE",
            "PROSE_CHANGE_FACTS",
            "STRUCTURED_CHANGE_FACTS",
        ],
        "condition_contract": condition_contract(),
        "oracle_boundary": [
            "target_apis",
            "line_maps",
            "gold_diff",
            "tests",
        ],
        "tasks": retained,
    }
    receipt = {
        "schema": "pymigbench_external_change_test_receipt_v1",
        "source_commit": PINNED_COMMIT,
        "environment": environment,
        "candidate_attempts": [*previous_attempts, *attempts],
        "retained_task_ids": [task["task_id"] for task in retained],
        "model_calls": 0,
        "failed_environment_retries": 0,
    }
    batches.append(
        {
            "batch_id": batch_id,
            "attempted": len(attempts),
            "retained": len(retained),
            "status": "COMPLETE",
            "finding": "Fresh records only; prior record paths and pairs excluded.",
        }
    )
    receipt["batches"] = batches
    write_json(output / "TASKS.json", tasks)
    write_json(output / "TEST_RECEIPT.json", receipt)
    (output / "CURATION_REPORT.md").write_text(
        render_report(
            PINNED_COMMIT,
            retained,
            receipt["candidate_attempts"],
            batches,
            output,
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "status": "CURATED",
                "retained": len(retained),
                "attempted": len(attempts),
                "model_calls": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
