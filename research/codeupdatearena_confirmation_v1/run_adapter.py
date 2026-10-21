"""Bounded CodeUpdateArena adapter for the frozen local :8004 model."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


ADAPTER_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ADAPTER_ROOT.parents[1]
PORTFOLIO_ROOT = PROJECT_ROOT / "research" / "research_portfolio_v2"
V1_ROOT = PROJECT_ROOT / "research" / "codeupdatearena_adapter_v1"
SPEC_PATH = ADAPTER_ROOT / "ADAPTER_SPEC.json"
SPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

SOURCE_ROOT = Path(
    os.environ.get("CODEUPDATEARENA_SOURCE_ROOT", SPEC["source"]["root"])
)
DATASET_PATH = SOURCE_ROOT / SPEC["source"]["dataset_relative_path"]
FAMILIES_PATH = Path(
    os.environ.get(
        "CODEUPDATEARENA_FAMILIES_PATH",
        SPEC["source"]["families_manifest"],
    )
)
SNAPSHOT_PATH = ADAPTER_ROOT / "TASK_SNAPSHOT.json"
PRE_MODEL_REPORT_PATH = ADAPTER_ROOT / "PRE_MODEL_REPORT.md"
FREEZE_RECEIPT_PATH = ADAPTER_ROOT / "FREEZE_RECEIPT.json"
MODEL_LEDGER_PATH = ADAPTER_ROOT / "CONFIRMATION_MODEL_LEDGER.json"
MODEL_RESULT_PATH = ADAPTER_ROOT / "CONFIRMATION_MODEL_RESULT.json"
FINAL_RESULT_PATH = PORTFOLIO_ROOT / "CODEUPDATEARENA_CONFIRMATION_RESULT.json"
FINAL_REPORT_PATH = PORTFOLIO_ROOT / "CODEUPDATEARENA_CONFIRMATION_REPORT.md"
BUDGET_LEDGER_PATH = PORTFOLIO_ROOT / "COST_AND_CANDIDATES.json"
ORACLE_ROOT = ADAPTER_ROOT / "evidence" / "oracle"
RAW_ROOT = ADAPTER_ROOT / "evidence" / "revalidation"
TZ = ZoneInfo("Asia/Shanghai")

RESULT_MARKER = "__CODEUPDATEARENA_EXEC_RESULT__"
PUBLIC_BASE_KEYS = {"scenario", "problem", "solution_signature", "imports"}
PUBLIC_UPDATE_KEYS = {
    "update_description",
    "update_rationale",
    "update_docstring",
    "update_signature",
}


@dataclass(frozen=True)
class FrozenTask:
    """One preregistered CodeUpdateArena program-synthesis task."""

    index: int
    row: dict[str, Any]

    @property
    def prog_syn_id(self) -> str:
        return str(self.row["prog_syn_id"])

    @property
    def update_id(self) -> str:
        return str(self.row["update_id"])

    @property
    def slug(self) -> str:
        return f"{self.index:02d}"


def now_iso() -> str:
    """Return an Asia/Shanghai timestamp with offset."""

    return datetime.now(TZ).isoformat()


def write_json(path: Path, value: Any) -> None:
    """Write deterministic, human-readable JSON evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    """Write UTF-8 evidence text."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def json_hash(value: Any) -> str:
    """Hash a JSON-compatible value canonically."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    """Hash a file without reading it into memory at once."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_output(argv: list[str], timeout: int = 20) -> str:
    """Run a small read-only command and return trimmed stdout."""

    completed = subprocess.run(
        argv,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return completed.stdout.strip()


def load_frozen_tasks() -> list[FrozenTask]:
    """Load exactly the eight frozen families from the pinned JSONL source."""

    manifest = json.loads(FAMILIES_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema") != "external_adapter_dev_families_v1":
        raise RuntimeError("families_manifest_schema")
    if manifest.get("source_commit") != SPEC["source"]["commit"]:
        raise RuntimeError("families_manifest_commit")
    families = manifest.get("families")
    if not isinstance(families, list) or len(families) != SPEC["families"]:
        raise RuntimeError("families_count")

    actual_commit = command_output(
        ["git", "-C", str(SOURCE_ROOT), "rev-parse", "HEAD"]
    )
    if actual_commit != SPEC["source"]["commit"]:
        raise RuntimeError("source_commit_mismatch")
    actual_hash = file_hash(DATASET_PATH)
    if actual_hash != SPEC["source"]["dataset_sha256"]:
        raise RuntimeError("dataset_hash_mismatch")

    wanted = [str(row["prog_syn_id"]) for row in families]
    if len(set(wanted)) != len(wanted):
        raise RuntimeError("duplicate_prog_syn_id")
    rows_by_id: dict[str, dict[str, Any]] = {}
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            prog_syn_id = row.get("prog_syn_id")
            if prog_syn_id in wanted:
                if prog_syn_id in rows_by_id:
                    raise RuntimeError(f"duplicate_source_row:{line_number}")
                rows_by_id[str(prog_syn_id)] = row

    if set(rows_by_id) != set(wanted):
        missing = sorted(set(wanted) - set(rows_by_id))
        raise RuntimeError(f"missing_frozen_rows:{missing}")

    tasks: list[FrozenTask] = []
    for index, family in enumerate(families):
        row = rows_by_id[str(family["prog_syn_id"])]
        if row.get("update_id") != family.get("update_id"):
            raise RuntimeError(f"update_id_mismatch:{family['prog_syn_id']}")
        if row.get("update", {}).get("update_type") != family.get("update_type"):
            raise RuntimeError(f"update_type_mismatch:{family['prog_syn_id']}")
        if row.get("update", {}).get("api_path") != family.get("api_path"):
            raise RuntimeError(f"api_path_mismatch:{family['prog_syn_id']}")
        if row.get("imports") != row.get("update", {}).get("imports"):
            raise RuntimeError(f"imports_mismatch:{family['prog_syn_id']}")
        tasks.append(FrozenTask(index=index, row=row))
    return tasks


def public_task_fields(task: FrozenTask, arm: str) -> dict[str, str]:
    """Return only the preregistered public fields for a prompt arm."""

    if arm not in {"base", "update_info"}:
        raise ValueError("unknown_arm")
    row = task.row
    values = {
        "scenario": str(row["scenario"]),
        "problem": str(row["problem"]),
        "solution_signature": str(row["solution_signature"]),
        "imports": str(row["imports"]),
    }
    if arm == "update_info":
        update = row["update"]
        values.update(
            {
                "update_description": str(update["description"]),
                "update_rationale": str(update["rationale"]),
                "update_docstring": str(update["docstring"]),
                "update_signature": str(update["signature"]),
            }
        )
    expected = PUBLIC_BASE_KEYS if arm == "base" else PUBLIC_BASE_KEYS | PUBLIC_UPDATE_KEYS
    if set(values) != expected:
        raise RuntimeError(f"prompt_field_keys:{task.prog_syn_id}:{arm}")
    return values


def build_prompt(task: FrozenTask, arm: str) -> str:
    """Build a prompt that exposes no reference, test, or update implementation."""

    fields = public_task_fields(task, arm)
    task_json = json.dumps(fields, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        "Implement the requested Python function from the supplied public task "
        "data. Return exactly one JSON object with exactly one key named "
        "\"code\" whose value is a Python source string. The source must define "
        "the requested function and may include necessary imports and helpers. "
        "Do not return Markdown or any other JSON keys.\n\n"
        "Public task data:\n"
        f"{task_json}"
    )


def assert_prompt_not_leaking(task: FrozenTask, arm: str, prompt: str) -> None:
    """Fail if hidden source material appears in a model prompt."""

    forbidden_exact = [
        str(task.row["ref_solution"]),
        str(task.row["unit_tests"]),
        str(task.row["update"]["implementation"]),
        build_enforcement_statement(task),
    ]
    if any(value and value in prompt for value in forbidden_exact):
        raise RuntimeError(f"prompt_leak:{task.prog_syn_id}:{arm}")
    if re.search(r"\b(ref_solution|unit_tests|update\.implementation)\b", prompt):
        raise RuntimeError(f"prompt_forbidden_label:{task.prog_syn_id}:{arm}")


def first_defined_function_name(code: str) -> str:
    """Return the first top-level function name in trusted or generated code."""

    tree = ast.parse(code)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return str(node.name)
    raise ValueError("no_function_definition")


def build_enforcement_statement(task: FrozenTask) -> str:
    """Mirror CodeUpdateArena's trusted update-enforcement rules."""

    api_path = str(task.row["update"]["api_path"])
    new_name = first_defined_function_name(str(task.row["update"]["implementation"]))
    old_name = api_path.rsplit(".", 1)[-1]
    if new_name == old_name:
        return f"{api_path} = {new_name}"
    parent_path = api_path.rsplit(".", 1)[0]
    return f"setattr({parent_path}, '{new_name}', {new_name})"


def extract_hidden_tests(task: FrozenTask) -> list[dict[str, str]]:
    """Extract top-level hidden test functions with preserved source text."""

    source = str(task.row["unit_tests"])
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    tests: list[dict[str, str]] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        start_line = node.lineno - 1
        end_line = node.end_lineno
        test_source = "".join(lines[start_line:end_line]).rstrip() + "\n"
        ast.parse(test_source)
        tests.append({"name": node.name, "source": test_source})
    if not tests:
        raise RuntimeError(f"no_hidden_tests:{task.prog_syn_id}")
    return tests


def build_test_program(
    task: FrozenTask,
    solution_code: str,
    test: dict[str, str],
    role: str,
) -> str:
    """Assemble imports, trusted update, solution, and one hidden test."""

    update = task.row["update"]
    enforcement = build_enforcement_statement(task)
    marker_payload = json.dumps(
        {
            "role": role,
            "prog_syn_id": task.prog_syn_id,
            "test_name": test["name"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        "# Trusted import block\n"
        f"{str(task.row['imports']).rstrip()}\n\n"
        "# Trusted update implementation\n"
        f"{str(update['implementation']).rstrip()}\n\n"
        "# Trusted update enforcement\n"
        f"{enforcement}\n\n"
        "# Candidate solution\n"
        f"{solution_code.rstrip()}\n\n"
        "# Hidden unit test\n"
        f"{test['source'].rstrip()}\n\n"
        f"{test['name']}()\n"
        f"print({RESULT_MARKER!r} + {marker_payload!r})\n"
    )


def docker_command(
    program_dir: Path,
    output_dir: Path,
    container_name: str,
) -> list[str]:
    """Build the bounded, network-disabled Docker execution command."""

    execution = SPEC["execution"]
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        str(execution["network"]),
        "--cpus",
        str(execution["cpus"]),
        "--memory",
        str(execution["memory"]),
        "--memory-swap",
        str(execution["memory_swap"]),
        "--pids-limit",
        str(execution["pids_limit"]),
        "--read-only",
        "--tmpfs",
        str(execution["tmpfs"]),
        "--cap-drop",
        str(execution["cap_drop"]),
        "--security-opt",
        "no-new-privileges",
        "--stop-timeout",
        "1",
        "--mount",
        f"type=bind,source={program_dir},target=/task,readonly",
        "--mount",
        f"type=bind,source={output_dir},target=/output",
        "--workdir",
        "/output",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "OMP_NUM_THREADS=1",
        str(execution["image"]),
        "python",
        "/task/program.py",
    ]


def parse_execution_marker(stdout: str) -> dict[str, Any] | None:
    """Parse the last execution marker emitted by a test program."""

    for line in reversed(stdout.splitlines()):
        if not line.startswith(RESULT_MARKER):
            continue
        payload = line[len(RESULT_MARKER) :]
        value = json.loads(payload)
        return value if isinstance(value, dict) else None
    return None


def run_one_program(
    task: FrozenTask,
    solution_code: str,
    test: dict[str, str],
    role: str,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Execute one assembled hidden test in the pinned Docker image."""

    program = build_test_program(task, solution_code, test, role)
    program_dir = evidence_dir / "task_input"
    program_dir.mkdir(parents=True, exist_ok=True)
    write_text(program_dir / "program.py", program)

    container_name = f"codeupdatearena-{uuid.uuid4().hex[:16]}"
    with tempfile.TemporaryDirectory(prefix="codeupdatearena-output-") as temp_output:
        output_dir = Path(temp_output)
        argv = docker_command(program_dir, output_dir, container_name)
        command_record = {
            "argv": argv,
            "container_name": container_name,
            "image": SPEC["execution"]["image"],
            "network": SPEC["execution"]["network"],
            "cpus": SPEC["execution"]["cpus"],
            "memory": SPEC["execution"]["memory"],
            "memory_swap": SPEC["execution"]["memory_swap"],
            "pids_limit": SPEC["execution"]["pids_limit"],
            "read_only_root": SPEC["execution"]["read_only_root"],
            "task_input_mount": SPEC["execution"]["task_input_mount"],
            "output_mount": SPEC["execution"]["output_mount"],
            "tmpfs": SPEC["execution"]["tmpfs"],
            "cap_drop": SPEC["execution"]["cap_drop"],
            "no_new_privileges": SPEC["execution"]["no_new_privileges"],
            "wall_clock_timeout_seconds": SPEC["execution"][
                "wall_clock_timeout_seconds"
            ],
        }
        write_json(evidence_dir / "command.json", command_record)
        started = time.monotonic()
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        timed_out = False
        try:
            stdout, stderr = process.communicate(
                timeout=int(SPEC["execution"]["wall_clock_timeout_seconds"])
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            stdout, stderr = process.communicate()
        elapsed = time.monotonic() - started

    write_text(evidence_dir / "stdout.txt", stdout)
    write_text(evidence_dir / "stderr.txt", stderr)
    marker = parse_execution_marker(stdout)
    if process.returncode == 125:
        status = "infrastructure_failure"
    elif timed_out:
        status = "timeout"
    elif marker is None:
        status = "runtime_failure"
    elif process.returncode != 0:
        status = "runtime_failure"
    else:
        status = "passed"
    result = {
        "role": role,
        "prog_syn_id": task.prog_syn_id,
        "test_name": test["name"],
        "status": status,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "wall_seconds": elapsed,
        "marker": marker,
        "program_sha256": file_hash(program_dir / "program.py"),
        "stdout_sha256": file_hash(evidence_dir / "stdout.txt"),
        "stderr_sha256": file_hash(evidence_dir / "stderr.txt"),
    }
    write_json(evidence_dir / "result.json", result)
    return result


def execute_solution(
    task: FrozenTask,
    solution_code: str,
    role: str,
    evidence_root: Path,
) -> dict[str, Any]:
    """Execute every hidden test for one solution and aggregate results."""

    tests = extract_hidden_tests(task)
    records: list[dict[str, Any]] = []
    for index, test in enumerate(tests):
        test_dir = evidence_root / f"test_{index:02d}"
        record = run_one_program(
            task,
            solution_code,
            test,
            role,
            test_dir,
        )
        records.append(record)
        if record["status"] == "infrastructure_failure":
            break
    passed = sum(record["status"] == "passed" for record in records)
    all_tests_pass = len(records) == len(tests) and passed == len(tests)
    if any(record["status"] == "timeout" for record in records):
        failure_kind = "runtime_timeout"
    elif any(record["status"] == "runtime_failure" for record in records):
        failure_kind = "runtime_failure"
    elif not all_tests_pass:
        failure_kind = "test_failure"
    else:
        failure_kind = None
    return {
        "role": role,
        "prog_syn_id": task.prog_syn_id,
        "test_total": len(tests),
        "test_executed": len(records),
        "tests_passed": passed,
        "all_tests_pass": all_tests_pass,
        "failure_kind": failure_kind,
        "infrastructure_failure": any(
            record["status"] == "infrastructure_failure" for record in records
        ),
        "wall_seconds": sum(float(record["wall_seconds"]) for record in records),
        "records": records,
    }


BANNED_MODULE_ROOTS = {
    "asyncio",
    "builtins",
    "ctypes",
    "importlib",
    "inspect",
    "multiprocessing",
    "os",
    "signal",
    "subprocess",
    "sys",
    "threading",
}
ALLOWED_MODULE_ROOTS = {
    "bisect",
    "collections",
    "decimal",
    "fractions",
    "functools",
    "heapq",
    "itertools",
    "math",
    "operator",
    "re",
    "statistics",
    "string",
    "typing",
}
BANNED_NAMES = {
    "__builtins__",
    "__import__",
    "compile",
    "dir",
    "eval",
    "exec",
    "exit",
    "getattr",
    "globals",
    "hasattr",
    "KeyboardInterrupt",
    "GeneratorExit",
    "locals",
    "open",
    "pprint",
    "print",
    "quit",
    "setattr",
    "SystemExit",
    "vars",
}
BANNED_ATTRIBUTES = {
    "_exit",
    "abort",
    "exit",
    "kill",
    "print",
    "stdout",
    "stderr",
    "terminate",
    "write",
    "writelines",
}


def validate_candidate_code(code: str) -> dict[str, Any]:
    """Validate and retain only side-effect-free candidate definitions."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "allowed": False,
            "reason": "candidate_syntax_error",
            "detail": str(exc),
        }
    retained = []
    dropped = []
    for node in tree.body:
        if isinstance(
            node,
            (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.decorator_list:
                return {
                    "allowed": False,
                    "reason": "decorated_definition",
                    "detail": node.name,
                }
            start = node.lineno - 1
            end = node.end_lineno
            retained.append(
                "".join(code.splitlines(keepends=True)[start:end]).rstrip() + "\n"
            )
            continue
        source = ast.get_source_segment(code, node) or ""
        safe_old_alias = (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id.startswith("old_")
            and isinstance(node.value, ast.Attribute)
        )
        safe_old_setattr = (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "setattr"
            and len(node.value.args) == 3
            and isinstance(node.value.args[1], ast.Constant)
            and str(node.value.args[1].value).startswith("old_")
        )
        if not (safe_old_alias or safe_old_setattr):
            return {
                "allowed": False,
                "reason": "unsafe_top_level_statement",
                "detail": type(node).__name__,
            }
        dropped.append({"kind": type(node).__name__, "source": source})
    prepared_code = "\n".join(retained)
    prepared_tree = ast.parse(prepared_code)
    for node in ast.walk(prepared_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in BANNED_MODULE_ROOTS or root not in ALLOWED_MODULE_ROOTS:
                    return {
                        "allowed": False,
                        "reason": "banned_import",
                        "detail": alias.name,
                    }
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in BANNED_MODULE_ROOTS or root not in ALLOWED_MODULE_ROOTS:
                return {
                    "allowed": False,
                    "reason": "banned_import",
                    "detail": node.module or "",
                }
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            return {
                "allowed": False,
                "reason": "banned_name",
                "detail": node.id,
            }
        elif isinstance(node, ast.Name) and node.id.startswith("__v2_"):
            return {
                "allowed": False,
                "reason": "trusted_namespace_access",
                "detail": node.id,
            }
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRIBUTES:
            return {
                "allowed": False,
                "reason": "banned_attribute",
                "detail": node.attr,
            }
        elif isinstance(node, ast.FunctionDef) and node.name in BANNED_NAMES:
            return {
                "allowed": False,
                "reason": "banned_function_name",
                "detail": node.name,
            }
        elif isinstance(node, ast.Raise):
            exception = node.exc
            if isinstance(exception, ast.Name) and exception.id == "SystemExit":
                return {
                    "allowed": False,
                    "reason": "system_exit",
                    "detail": "SystemExit",
                }
            if (
                isinstance(exception, ast.Call)
                and isinstance(exception.func, ast.Name)
                and exception.func.id == "SystemExit"
            ):
                return {
                    "allowed": False,
                    "reason": "system_exit",
                    "detail": "SystemExit()",
                }
    return {
        "allowed": True,
        "reason": "accepted",
        "detail": "",
        "prepared_code": prepared_code,
        "dropped_top_level_nodes": dropped,
    }


def build_test_program_v2(
    task: FrozenTask,
    solution_code: str,
    test: dict[str, str],
    role: str,
    nonce: str,
) -> str:
    """Assemble candidate code and trusted per-test marker emission."""

    update = task.row["update"]
    enforcement = build_enforcement_statement(task)
    return (
        "# Trusted import block\n"
        f"{str(task.row['imports']).rstrip()}\n\n"
        "# Trusted update implementation\n"
        f"{str(update['implementation']).rstrip()}\n\n"
        "# Trusted update enforcement\n"
        f"{enforcement}\n\n"
        "# Candidate solution\n"
        f"{solution_code.rstrip()}\n\n"
        "# Hidden unit test\n"
        f"{test['source'].rstrip()}\n\n"
        "# Trusted marker harness\n"
        "import json as __v2_json\n"
        f"__v2_nonce = {nonce!r}\n"
        f"__v2_role = {role!r}\n"
        f"__v2_prog_syn_id = {task.prog_syn_id!r}\n"
        f"__v2_test_name = {test['name']!r}\n"
        "def __v2_emit(stage):\n"
        f"    print({RESULT_MARKER!r} + __v2_json.dumps({{'stage': stage, "
        "'nonce': __v2_nonce, 'role': __v2_role, "
        "'prog_syn_id': __v2_prog_syn_id, "
        "'test_name': __v2_test_name}, sort_keys=True, separators=(',', ':')))\n"
        "__v2_emit('test_start')\n"
        f"{test['name']}()\n"
        "__v2_emit('test_pass')\n"
        "__v2_emit('all_tests_complete')\n"
    )


def docker_command_v2(
    program_dir: Path,
    output_dir: Path,
    container_name: str,
    image_id: str,
) -> list[str]:
    """Run one program with the frozen image ID and bounded resources."""

    execution = SPEC["execution"]
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        str(execution["network"]),
        "--cpus",
        str(execution["cpus"]),
        "--memory",
        str(execution["memory"]),
        "--memory-swap",
        str(execution["memory_swap"]),
        "--pids-limit",
        str(execution["pids_limit"]),
        "--read-only",
        "--tmpfs",
        str(execution["tmpfs"]),
        "--cap-drop",
        str(execution["cap_drop"]),
        "--security-opt",
        "no-new-privileges",
        "--stop-timeout",
        "1",
        "--mount",
        f"type=bind,source={program_dir},target=/task,readonly",
        "--mount",
        f"type=bind,source={output_dir},target=/output",
        "--workdir",
        "/output",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "OMP_NUM_THREADS=1",
        image_id,
        "python",
        "/task/program.py",
    ]


def parse_execution_markers_v2(stdout: str) -> list[dict[str, Any]]:
    """Parse every trusted marker line and reject malformed output."""

    markers: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.startswith(RESULT_MARKER):
            continue
        value = json.loads(line[len(RESULT_MARKER) :])
        if not isinstance(value, dict):
            raise ValueError("marker_not_object")
        markers.append(value)
    return markers


def validate_execution_markers_v2(
    markers: list[dict[str, Any]],
    task: FrozenTask,
    test: dict[str, str],
    role: str,
    nonce: str,
) -> tuple[bool, str]:
    """Require the exact trusted test lifecycle and marker identity."""

    expected = [
        {"stage": "test_start", "nonce": nonce, "role": role,
         "prog_syn_id": task.prog_syn_id, "test_name": test["name"]},
        {"stage": "test_pass", "nonce": nonce, "role": role,
         "prog_syn_id": task.prog_syn_id, "test_name": test["name"]},
        {"stage": "all_tests_complete", "nonce": nonce, "role": role,
         "prog_syn_id": task.prog_syn_id, "test_name": test["name"]},
    ]
    return markers == expected, "ok" if markers == expected else "marker_sequence_mismatch"


def classify_execution_v2(
    markers: list[dict[str, Any]],
    marker_valid: bool,
    return_code: int,
    timed_out: bool,
) -> tuple[str, str | None]:
    """Classify trusted execution state without collapsing test failures."""

    if return_code == 125:
        return "infrastructure_failure", "infrastructure_failure"
    if timed_out:
        return "timeout", "runtime_timeout"
    if (
        not marker_valid
        and any(marker.get("stage") == "test_start" for marker in markers)
        and not any(marker.get("stage") == "test_pass" for marker in markers)
        and return_code != 0
    ):
        return "test_failure", "test_failure"
    if not marker_valid:
        return "marker_violation", "marker_violation"
    if return_code == 0:
        return "passed", None
    return "runtime_failure", "runtime_failure"


def run_one_program_v2(
    task: FrozenTask,
    solution_code: str,
    test: dict[str, str],
    role: str,
    evidence_dir: Path,
    image_id: str,
) -> dict[str, Any]:
    """Execute one candidate or reference test with trusted lifecycle markers."""

    validation = validate_candidate_code(solution_code) if role == "candidate" else {
        "allowed": True,
        "reason": "trusted_reference",
        "detail": "",
    }
    if not validation["allowed"]:
        return {
            "role": role,
            "prog_syn_id": task.prog_syn_id,
            "test_name": test["name"],
            "status": "syntax_failure",
            "failure_kind": "syntax_failure",
            "exit_code": None,
            "timed_out": False,
            "candidate_validation": validation,
        }
    nonce = uuid.uuid4().hex
    prepared_code = (
        validation.get("prepared_code", solution_code)
        if role == "candidate"
        else solution_code
    )
    program = build_test_program_v2(task, prepared_code, test, role, nonce)
    program_dir = evidence_dir / "task_input"
    program_dir.mkdir(parents=True, exist_ok=True)
    write_text(program_dir / "program.py", program)
    container_name = f"codeupdatearena-v2-{uuid.uuid4().hex[:16]}"
    with tempfile.TemporaryDirectory(prefix="codeupdatearena-v2-output-") as temp_output:
        output_dir = Path(temp_output)
        argv = docker_command_v2(program_dir, output_dir, container_name, image_id)
        write_json(
            evidence_dir / "command.json",
            {
                "argv": argv,
                "container_name": container_name,
                "image_id": image_id,
                "network": SPEC["execution"]["network"],
                "cpus": SPEC["execution"]["cpus"],
                "memory": SPEC["execution"]["memory"],
                "memory_swap": SPEC["execution"]["memory_swap"],
                "pids_limit": SPEC["execution"]["pids_limit"],
                "read_only_root": SPEC["execution"]["read_only_root"],
                "task_input_mount": SPEC["execution"]["task_input_mount"],
                "output_mount": SPEC["execution"]["output_mount"],
                "tmpfs": SPEC["execution"]["tmpfs"],
                "cap_drop": SPEC["execution"]["cap_drop"],
                "no_new_privileges": SPEC["execution"]["no_new_privileges"],
                "wall_clock_timeout_seconds": SPEC["execution"][
                    "wall_clock_timeout_seconds"
                ],
            },
        )
        started = time.monotonic()
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        timed_out = False
        try:
            stdout, stderr = process.communicate(
                timeout=int(SPEC["execution"]["wall_clock_timeout_seconds"])
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            stdout, stderr = process.communicate()
        elapsed = time.monotonic() - started
    write_text(evidence_dir / "stdout.txt", stdout)
    write_text(evidence_dir / "stderr.txt", stderr)
    try:
        markers = parse_execution_markers_v2(stdout)
        marker_valid, marker_error = validate_execution_markers_v2(
            markers, task, test, role, nonce
        )
    except (ValueError, json.JSONDecodeError) as exc:
        markers, marker_valid, marker_error = [], False, str(exc)
    status, failure_kind = classify_execution_v2(
        markers, marker_valid, process.returncode, timed_out
    )
    result = {
        "role": role,
        "prog_syn_id": task.prog_syn_id,
        "test_name": test["name"],
        "status": status,
        "failure_kind": failure_kind,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "wall_seconds": elapsed,
        "markers": markers,
        "marker_valid": marker_valid,
        "marker_error": marker_error,
        "candidate_validation": validation,
        "program_sha256": file_hash(program_dir / "program.py"),
        "stdout_sha256": file_hash(evidence_dir / "stdout.txt"),
        "stderr_sha256": file_hash(evidence_dir / "stderr.txt"),
    }
    write_json(evidence_dir / "result.json", result)
    return result


def execute_solution_v2(
    task: FrozenTask,
    solution_code: str,
    role: str,
    evidence_root: Path,
    image_id: str,
) -> dict[str, Any]:
    """Execute all hidden tests with strict candidate and marker validation."""

    validation = validate_candidate_code(solution_code) if role == "candidate" else {
        "allowed": True,
        "reason": "trusted_reference",
        "detail": "",
    }
    if not validation["allowed"]:
        return {
            "role": role,
            "prog_syn_id": task.prog_syn_id,
            "test_total": 0,
            "test_executed": 0,
            "tests_passed": 0,
            "all_tests_pass": False,
            "failure_kind": "syntax_failure",
            "infrastructure_failure": False,
            "candidate_validation": validation,
            "records": [],
        }
    tests = extract_hidden_tests(task)
    records = []
    for index, test in enumerate(tests):
        test_dir = evidence_root / f"test_{index:02d}"
        record = run_one_program_v2(
            task, solution_code, test, role, test_dir, image_id
        )
        records.append(record)
        if record["status"] == "infrastructure_failure":
            break
    passed = sum(record["status"] == "passed" for record in records)
    all_tests_pass = len(records) == len(tests) and passed == len(tests)
    if any(record["status"] == "infrastructure_failure" for record in records):
        failure_kind = "infrastructure_failure"
    elif any(record["status"] == "timeout" for record in records):
        failure_kind = "runtime_timeout"
    elif any(record["status"] == "marker_violation" for record in records):
        failure_kind = "marker_violation"
    elif any(record["status"] == "test_failure" for record in records):
        failure_kind = "test_failure"
    elif any(record["status"] == "runtime_failure" for record in records):
        failure_kind = "runtime_failure"
    elif not all_tests_pass:
        failure_kind = "test_failure"
    else:
        failure_kind = None
    return {
        "role": role,
        "prog_syn_id": task.prog_syn_id,
        "test_total": len(tests),
        "test_executed": len(records),
        "tests_passed": passed,
        "all_tests_pass": all_tests_pass,
        "failure_kind": failure_kind,
        "infrastructure_failure": failure_kind == "infrastructure_failure",
        "candidate_validation": validation,
        "records": records,
        "wall_seconds": sum(float(record.get("wall_seconds", 0.0)) for record in records),
    }


def verify_docker_image() -> dict[str, Any]:
    """Verify the existing sandbox image before any task execution."""

    image = SPEC["execution"]["image"]
    raw = command_output(["docker", "image", "inspect", image])
    parsed = json.loads(raw)
    if not isinstance(parsed, list) or not parsed:
        raise RuntimeError("docker_image_missing")
    item = parsed[0]
    return {
        "image": image,
        "id": item.get("Id"),
        "sha256": item.get("Digest"),
        "created": item.get("Created"),
        "architecture": item.get("Architecture"),
        "os": item.get("Os"),
    }


def create_snapshot(tasks: list[FrozenTask]) -> dict[str, Any]:
    """Create the exact pre-model task and request snapshot."""

    planned: list[dict[str, Any]] = []
    for task in tasks:
        for arm in SPEC["arms"]:
            prompt = build_prompt(task, arm)
            assert_prompt_not_leaking(task, arm, prompt)
            payload = {
                "model": SPEC["model"]["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": SPEC["generation"]["temperature"],
                "top_p": SPEC["generation"]["top_p"],
                "max_tokens": SPEC["generation"]["max_tokens"],
                "response_format": {
                    "type": SPEC["generation"]["response_format"]
                },
                "chat_template_kwargs": {
                    "enable_thinking": SPEC["generation"]["enable_thinking"]
                },
            }
            planned.append(
                {
                    "attempt_index": len(planned) + 1,
                    "family_index": task.index,
                    "prog_syn_id": task.prog_syn_id,
                    "arm": arm,
                    "prompt_sha256": json_hash(prompt),
                    "request_sha256": json_hash(payload),
                    "prompt": prompt,
                    "request": payload,
                }
            )
    return {
        "schema": "codeupdatearena_adapter_task_snapshot_v1",
        "created_at": now_iso(),
        "evidence_identity": SPEC["evidence_identity"],
        "source": {
            "repository": SPEC["source"]["repository"],
            "commit": SPEC["source"]["commit"],
            "dataset_path": str(DATASET_PATH),
            "dataset_sha256": file_hash(DATASET_PATH),
            "families_manifest": str(FAMILIES_PATH),
            "families_manifest_sha256": file_hash(FAMILIES_PATH),
        },
        "model": SPEC["model"],
        "generation": SPEC["generation"],
        "execution": SPEC["execution"],
        "arms": SPEC["arms"],
        "attempt_order": [
            {
                "attempt_index": row["attempt_index"],
                "family_index": row["family_index"],
                "prog_syn_id": row["prog_syn_id"],
                "arm": row["arm"],
            }
            for row in planned
        ],
        "planned_requests": planned,
        "selected_rows": [task.row for task in tasks],
        "source_row_sha256": {
            task.prog_syn_id: json_hash(task.row) for task in tasks
        },
    }


def render_pre_model_report(
    tasks: list[FrozenTask],
    docker_identity: dict[str, Any],
    oracle: list[dict[str, Any]],
    snapshot: dict[str, Any],
) -> str:
    """Render the report that must exist before the first model call."""

    oracle_total = sum(int(row["test_total"]) for row in oracle)
    oracle_passed = sum(int(row["tests_passed"]) for row in oracle)
    all_oracles_pass = all(bool(row["all_tests_pass"]) for row in oracle)
    lines = [
        "# CodeUpdateArena Adapter Pre-Model Report",
        "",
        f"- Frozen at: `{snapshot['created_at']}`",
        f"- Evidence identity: `{SPEC['evidence_identity']}`",
        f"- Source commit: `{SPEC['source']['commit']}`",
        f"- Dataset SHA-256: `{snapshot['source']['dataset_sha256']}`",
        f"- Docker image: `{docker_identity['image']}`",
        f"- Docker image ID: `{docker_identity['id']}`",
        f"- Planned model attempts: `{len(snapshot['planned_requests'])}`",
        f"- Reserved accounting tokens: `{SPEC['reserved_accounting_tokens']}`",
        "",
        "## Prompt Boundary",
        "",
        "The `base` arm contains only scenario, problem, solution signature, and "
        "imports. The `update_info` arm adds only the public update description, "
        "rationale, docstring, and new signature. Reference solutions, hidden unit "
        "tests, update implementations, and update-enforcement statements are "
        "absent from every planned request.",
        "",
        "## Docker Oracle",
        "",
        f"- Reference all-tests-pass families: `{sum(bool(row['all_tests_pass']) for row in oracle)}/{len(tasks)}`",
        f"- Reference hidden tests passed: `{oracle_passed}/{oracle_total}`",
        f"- Oracle gate: `{'PASS' if all_oracles_pass else 'FAIL'}`",
        "",
        "| # | Family | Tests | Passed | All pass | Wall s | Status |",
        "|---:|---|---:|---:|---|---:|---|",
    ]
    for row in oracle:
        lines.append(
            f"| {row['family_index'] + 1} | `{row['prog_syn_id']}` | "
            f"{row['test_total']} | {row['tests_passed']} | "
            f"{str(row['all_tests_pass']).lower()} | {row['wall_seconds']:.3f} | "
            f"`{row['failure_kind'] or 'pass'}` |"
        )
    lines.extend(
        [
            "",
            "## Frozen Attempt Order",
            "",
            "| Attempt | Family | Arm | Request SHA-256 |",
            "|---:|---|---|---|",
        ]
    )
    for row in snapshot["planned_requests"]:
        lines.append(
            f"| {row['attempt_index']} | `{row['prog_syn_id']}` | "
            f"`{row['arm']}` | `{row['request_sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Stop Rules",
            "",
            "- No retry and one generation per task and arm.",
            "- Generated syntax, runtime, timeout, and hidden-test failures remain "
            "model results and do not stop the batch.",
            "- Model-identity mismatch, malformed JSON envelope, missing usage, "
            "HTTP failure, or sandbox infrastructure failure stops the batch.",
            "- No official paid GPT-4 script, judge, training call, external "
            "network access, or production-memory write is permitted.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_freeze() -> dict[str, Any]:
    """Validate pre-model freeze hashes before any generation request."""

    if not FREEZE_RECEIPT_PATH.exists():
        raise RuntimeError("freeze_receipt_missing")
    receipt = json.loads(FREEZE_RECEIPT_PATH.read_text(encoding="utf-8"))
    expected = receipt.get("sha256", {})
    files = {
        "task_snapshot": SNAPSHOT_PATH,
        "pre_model_report": PRE_MODEL_REPORT_PATH,
        "adapter_spec": SPEC_PATH,
        "runner": Path(__file__).resolve(),
    }
    for key, path in files.items():
        if file_hash(path) != expected.get(key):
            raise RuntimeError(f"freeze_hash_mismatch:{key}")
    if receipt.get("model_calls_at_freeze") != 0:
        raise RuntimeError("freeze_model_call_count")
    return receipt


def prepare() -> int:
    """Freeze the exact task snapshot and run all reference oracles."""

    if MODEL_LEDGER_PATH.exists() or MODEL_RESULT_PATH.exists():
        raise RuntimeError("model_evidence_already_exists")
    tasks = load_frozen_tasks()
    docker_identity = verify_docker_image()
    oracle: list[dict[str, Any]] = []
    for task in tasks:
        row = execute_solution_v2(
            task,
            str(task.row["ref_solution"]),
            "reference_solution",
            ORACLE_ROOT / task.slug,
            docker_identity["id"],
        )
        row["family_index"] = task.index
        row["update_id"] = task.update_id
        oracle.append(row)
        if row["infrastructure_failure"]:
            raise RuntimeError(f"oracle_infrastructure_failure:{task.prog_syn_id}")
    if not all(row["all_tests_pass"] for row in oracle):
        raise RuntimeError("oracle_not_all_pass")

    snapshot = create_snapshot(tasks)
    snapshot["oracle"] = oracle
    snapshot["docker_identity"] = docker_identity
    write_json(SNAPSHOT_PATH, snapshot)
    report = render_pre_model_report(tasks, docker_identity, oracle, snapshot)
    write_text(PRE_MODEL_REPORT_PATH, report)
    receipt = {
        "schema": "codeupdatearena_adapter_freeze_receipt_v1",
        "frozen_at": now_iso(),
        "model_calls_at_freeze": 0,
        "oracle_status": "PASS",
        "planned_attempts": SPEC["reserved_attempts"],
        "sha256": {
            "task_snapshot": file_hash(SNAPSHOT_PATH),
            "pre_model_report": file_hash(PRE_MODEL_REPORT_PATH),
            "adapter_spec": file_hash(SPEC_PATH),
            "runner": file_hash(Path(__file__).resolve()),
        },
    }
    write_json(FREEZE_RECEIPT_PATH, receipt)
    print(
        json.dumps(
            {
                "status": "FROZEN_BEFORE_MODEL_CALLS",
                "oracle_families": len(tasks),
                "oracle_tests": sum(row["test_total"] for row in oracle),
                "planned_attempts": SPEC["reserved_attempts"],
            },
            sort_keys=True,
        )
    )
    return 0


def request_model(payload: dict[str, Any]) -> tuple[dict[str, Any], float]:
    """POST one request to the existing local model endpoint."""

    request = urllib.request.Request(
        SPEC["model"]["endpoint"],
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(
        request,
        timeout=int(SPEC["generation"]["timeout_seconds"]),
    ) as response:
        raw = response.read().decode("utf-8")
    elapsed = time.monotonic() - started
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("response_not_object")
    return body, elapsed


def verify_model_identity() -> dict[str, Any]:
    """Verify the exact frozen local model identity before generation."""

    request = urllib.request.Request(
        SPEC["model"]["models_endpoint"],
        headers={"accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    ids: list[str] = []
    if isinstance(body, dict) and isinstance(body.get("data"), list):
        ids = [
            str(row.get("id"))
            for row in body["data"]
            if isinstance(row, dict) and row.get("id") is not None
        ]
    expected = SPEC["model"]["model"]
    if ids != [expected]:
        raise RuntimeError(f"model_identity_mismatch:{ids!r}")
    return {
        "endpoint": SPEC["model"]["models_endpoint"],
        "expected": expected,
        "observed_ids": ids,
        "status": "MATCH",
    }


def parse_generation_envelope(body: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate the JSON-object response without judging generated syntax."""

    if body.get("model") != SPEC["model"]["model"]:
        raise ValueError("response_model_mismatch")
    choices = body.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response_choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("response_content")
    value = json.loads(message["content"])
    if not isinstance(value, dict) or set(value) != {"code"}:
        raise ValueError("response_envelope_keys")
    code = value["code"]
    if not isinstance(code, str) or not code.strip():
        raise ValueError("response_code_type")
    usage = body.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("response_usage_missing")
    total_tokens = usage.get("total_tokens")
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    if not all(isinstance(item, int) for item in (total_tokens, prompt_tokens, completion_tokens)):
        raise ValueError("response_usage_types")
    if total_tokens <= 0 or prompt_tokens < 0 or completion_tokens < 0:
        raise ValueError("response_usage_values")
    if total_tokens != prompt_tokens + completion_tokens:
        raise ValueError("response_usage_sum")
    return code, {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def summarize_generation_result(
    execution: dict[str, Any],
    parse_failures: int,
) -> dict[str, Any]:
    """Map execution state to preregistered model-result categories."""

    if parse_failures:
        status = "malformed_json"
    elif execution.get("infrastructure_failure"):
        status = "infrastructure_failure"
    elif execution.get("failure_kind") == "syntax_failure":
        status = "syntax_failure"
    elif execution.get("failure_kind") == "runtime_timeout":
        status = "runtime_failure"
    elif execution.get("failure_kind") == "runtime_failure":
        status = "runtime_failure"
    elif not execution.get("all_tests_pass"):
        status = "test_failure"
    else:
        status = "all_tests_pass"
    return {
        "status": status,
        "all_tests_pass": bool(execution.get("all_tests_pass")),
        "tests_passed": int(execution.get("tests_passed", 0)),
        "test_total": int(execution.get("test_total", 0)),
        "failure_kind": execution.get("failure_kind"),
        "wall_seconds": float(execution.get("wall_seconds", 0.0)),
    }


def aggregate_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate family-level paired metrics and accounting tokens."""

    complete_pairs: list[dict[str, Any]] = []
    by_family: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_family.setdefault(row["prog_syn_id"], {})[row["arm"]] = row
    for prog_syn_id, arms in by_family.items():
        if set(arms) != {"base", "update_info"}:
            continue
        base = arms["base"]
        update_info = arms["update_info"]
        complete_pairs.append(
            {
                "prog_syn_id": prog_syn_id,
                "base_all_tests_pass": bool(base["all_tests_pass"]),
                "update_info_all_tests_pass": bool(update_info["all_tests_pass"]),
                "paired_all_tests_pass_difference": int(
                    update_info["all_tests_pass"]
                )
                - int(base["all_tests_pass"]),
                "base_passed_total_tests": [
                    base["tests_passed"],
                    base["test_total"],
                ],
                "update_info_passed_total_tests": [
                    update_info["tests_passed"],
                    update_info["test_total"],
                ],
            }
        )
    arm_metrics: dict[str, Any] = {}
    for arm in SPEC["arms"]:
        arm_rows = [row for row in rows if row["arm"] == arm]
        latencies = [float(row["model_latency_seconds"]) for row in arm_rows]
        arm_metrics[arm] = {
            "attempts": len(arm_rows),
            "all_tests_pass_families": sum(
                bool(row["all_tests_pass"]) for row in arm_rows
            ),
            "hidden_tests_passed": sum(int(row["tests_passed"]) for row in arm_rows),
            "hidden_tests_total": sum(int(row["test_total"]) for row in arm_rows),
            "malformed_json_failures": sum(
                row["status"] == "malformed_json" for row in arm_rows
            ),
            "syntax_failures": sum(
                row["status"] == "syntax_failure" for row in arm_rows
            ),
            "runtime_failures": sum(
                row["status"] == "runtime_failure" for row in arm_rows
            ),
            "test_failures": sum(row["status"] == "test_failure" for row in arm_rows),
            "infrastructure_failures": sum(
                row["status"] == "infrastructure_failure" for row in arm_rows
            ),
            "model_latency_seconds": {
                "total": sum(latencies),
                "mean": sum(latencies) / len(latencies) if latencies else 0.0,
                "max": max(latencies) if latencies else 0.0,
            },
            "execution_wall_seconds": sum(
                float(row["execution_wall_seconds"]) for row in arm_rows
            ),
            "accounting_tokens": {
                key: sum(int(row["usage"][key]) for row in arm_rows)
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
            },
        }
    paired_difference = sum(
        int(row["paired_all_tests_pass_difference"]) for row in complete_pairs
    )
    base_infra = arm_metrics["base"]["infrastructure_failures"] / max(
        1,
        arm_metrics["base"]["attempts"],
    )
    update_infra = arm_metrics["update_info"]["infrastructure_failures"] / max(
        1,
        arm_metrics["update_info"]["attempts"],
    )
    return {
        "family_pairs": complete_pairs,
        "paired_all_tests_pass_difference": paired_difference,
        "arms": arm_metrics,
        "infrastructure_failure_rate": {
            "base": base_infra,
            "update_info": update_infra,
        },
    }


def settle_budget_ledger(
    attempts_used: int,
    accounting_tokens_used: int,
    status: str,
    reason: str,
) -> dict[str, Any]:
    """Settle only the reserved CodeUpdateArena row in the shared ledger."""

    ledger = json.loads(BUDGET_LEDGER_PATH.read_text(encoding="utf-8"))
    reservation_id = SPEC.get(
        "reservation_id",
        "CODEUPDATEARENA_CONFIRMATION_V1_20261021",
    )
    reservation = next(
        row for row in ledger["reservations"] if row["id"] == reservation_id
    )
    if reservation["status"] != "RESERVED_NOT_RUN":
        raise RuntimeError("budget_reservation_already_settled")
    if attempts_used > int(reservation["attempts"]):
        raise RuntimeError("attempt_budget_exceeded")
    tokens_used = int(accounting_tokens_used)
    if tokens_used > int(reservation["accounting_tokens"]):
        raise RuntimeError("token_budget_exceeded")
    reservation["status"] = status
    ledger["new_budget"]["attempts_used"] = int(
        ledger["new_budget"]["attempts_used"]
    ) + attempts_used
    ledger["new_budget"]["physical_http_calls"] = int(
        ledger["new_budget"]["physical_http_calls"]
    ) + attempts_used
    ledger["new_budget"]["accounting_tokens_used"] = int(
        ledger["new_budget"]["accounting_tokens_used"]
    ) + tokens_used
    ledger["events"].append(
        {
            "id": "CODEUPDATEARENA_CONFIRMATION_001_016",
            "attempts": attempts_used,
            "physical_http_calls": attempts_used,
            "accounting_tokens": tokens_used,
            "status": status,
            "reason": reason,
            "raw_result": (
                "research/research_portfolio_v2/CODEUPDATEARENA_CONFIRMATION_RESULT.json"
            ),
        }
    )
    write_json(BUDGET_LEDGER_PATH, ledger)
    return ledger


def render_final_report(result: dict[str, Any]) -> str:
    """Render the bounded external-adapter result report."""

    metrics = result["metrics"]
    arms = metrics["arms"]
    lines = [
        "# CodeUpdateArena Independent-New-Family Confirmation",
        "",
        f"- Status: `{result['status']}`",
        f"- Evidence identity: `{result['evidence_identity']}`",
        f"- Decision: `{result['decision']}`",
        f"- Source commit: `{result['source_commit']}`",
        f"- Attempts used: `{result['budget']['attempts_used']}/16`",
        f"- Accounting tokens used: `{result['budget']['accounting_tokens_used']}/50000`",
        f"- Physical generation HTTP calls: `{result['budget']['physical_http_calls']}`",
        f"- Model identity probe calls: `{result['budget']['model_identity_probe_calls']}`",
        "",
        "## Scope",
        "",
        "This is an independent new-family confirmation on the same public "
        "synthetic CodeUpdateArena source. It measures one local model on eight "
        "disjoint frozen update families. It is not evidence about natural "
        "production drift and is not a general model-capability benchmark.",
        "",
        "## Paired Result",
        "",
        f"- Primary paired difference `update_info - base`: "
        f"`{metrics['paired_all_tests_pass_difference']:+d}` all-tests-pass families",
        f"- Base all-tests-pass families: `{arms['base']['all_tests_pass_families']}/8`",
        f"- Update-info all-tests-pass families: "
        f"`{arms['update_info']['all_tests_pass_families']}/8`",
        f"- Base hidden tests passed: "
        f"`{arms['base']['hidden_tests_passed']}/{arms['base']['hidden_tests_total']}`",
        f"- Update-info hidden tests passed: "
        f"`{arms['update_info']['hidden_tests_passed']}/"
        f"{arms['update_info']['hidden_tests_total']}`",
        "",
        "| Family | Base | Update info | Paired delta |",
        "|---|---:|---:|---:|",
    ]
    for row in metrics["family_pairs"]:
        lines.append(
            f"| `{row['prog_syn_id']}` | "
            f"{str(row['base_all_tests_pass']).lower()} | "
            f"{str(row['update_info_all_tests_pass']).lower()} | "
            f"{row['paired_all_tests_pass_difference']:+d} |"
        )
    lines.extend(
        [
            "",
            "## Secondary Metrics",
            "",
            "| Arm | Parse | Syntax | Runtime | Test | Infra | Mean model s | Prompt tok | Completion tok | Total tok |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for arm in SPEC["arms"]:
        row = arms[arm]
        tokens = row["accounting_tokens"]
        lines.append(
            f"| `{arm}` | {row['malformed_json_failures']} | "
            f"{row['syntax_failures']} | {row['runtime_failures']} | "
            f"{row['test_failures']} | {row['infrastructure_failures']} | "
            f"{row['model_latency_seconds']['mean']:.3f} | "
            f"{tokens['prompt_tokens']} | {tokens['completion_tokens']} | "
            f"{tokens['total_tokens']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "- Frozen snapshot: `research/codeupdatearena_confirmation_v1/TASK_SNAPSHOT.json`",
            "- Pre-model report: `research/codeupdatearena_confirmation_v1/PRE_MODEL_REPORT.md`",
            "- Model ledger: `research/codeupdatearena_confirmation_v1/CONFIRMATION_MODEL_LEDGER.json`",
            "- Raw request/response pairs and Docker evidence: "
            "`research/codeupdatearena_confirmation_v1/evidence/`",
            "- Machine-readable result: "
            "`research/research_portfolio_v2/CODEUPDATEARENA_CONFIRMATION_RESULT.json`",
            "",
            "## Nonclaims",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in SPEC["nonclaims"])
    lines.append("")
    return "\n".join(lines)


def run_model_batch() -> int:
    """Run exactly the frozen 16-attempt paired comparison with no retries."""

    validate_freeze()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    tasks = {str(task.prog_syn_id): task for task in load_frozen_tasks()}
    planned = snapshot["planned_requests"]
    if len(planned) != SPEC["reserved_attempts"]:
        raise RuntimeError("planned_attempt_count")

    identity = verify_model_identity()
    docker_identity = verify_docker_image()
    ledger: dict[str, Any] = {
        "schema": "codeupdatearena_adapter_model_ledger_v1",
        "started_at": now_iso(),
        "status": "IN_PROGRESS",
        "reserved_attempts": SPEC["reserved_attempts"],
        "reserved_accounting_tokens": SPEC["reserved_accounting_tokens"],
        "attempts_used": 0,
        "physical_http_calls": 0,
        "model_identity_probe_calls": 1,
        "accounting_tokens_used": 0,
        "model_identity": identity,
        "docker_identity": docker_identity,
        "records": [],
    }
    rows: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "schema": "codeupdatearena_adapter_result_v1",
        "created_at": now_iso(),
        "evidence_identity": SPEC["evidence_identity"],
        "status": "IN_PROGRESS",
        "decision": "NOT_READY",
        "source_commit": SPEC["source"]["commit"],
        "budget": {
            "reserved_attempts": SPEC["reserved_attempts"],
            "reserved_accounting_tokens": SPEC["reserved_accounting_tokens"],
            "attempts_used": 0,
            "physical_http_calls": 0,
            "model_identity_probe_calls": 1,
            "accounting_tokens_used": 0,
            "docker_identity": docker_identity,
        },
        "rows": rows,
        "metrics": aggregate_metrics(rows),
        "nonclaims": SPEC["nonclaims"],
    }
    write_json(MODEL_LEDGER_PATH, ledger)
    write_json(MODEL_RESULT_PATH, result)

    stop_reason: str | None = None
    stop_detail: str | None = None
    for planned_row in planned:
        task = tasks[str(planned_row["prog_syn_id"])]
        arm = str(planned_row["arm"])
        attempt_index = int(planned_row["attempt_index"])
        attempt_dir = RAW_ROOT / f"attempt_{attempt_index:02d}_{arm}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        payload = planned_row["request"]
        write_json(attempt_dir / "request.json", payload)
        record: dict[str, Any] = {
            "attempt_index": attempt_index,
            "family_index": task.index,
            "prog_syn_id": task.prog_syn_id,
            "update_id": task.update_id,
            "arm": arm,
            "request_sha256": json_hash(payload),
            "raw_request": str(
                (attempt_dir / "request.json").relative_to(ADAPTER_ROOT)
            ).replace("\\", "/"),
            "raw_response": str(
                (attempt_dir / "response.json").relative_to(ADAPTER_ROOT)
            ).replace("\\", "/"),
            "status": "INFRASTRUCTURE_FAILURE",
        }
        started = time.monotonic()
        try:
            body, model_latency = request_model(payload)
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            body = {
                "error": {
                    "type": type(exc).__name__,
                    "detail": str(exc),
                }
            }
            model_latency = time.monotonic() - started
            stop_reason = "INFRASTRUCTURE_FAILURE"
            stop_detail = f"http:{type(exc).__name__}"
        write_json(attempt_dir / "response.json", body)
        ledger["attempts_used"] += 1
        ledger["physical_http_calls"] += 1

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        if stop_reason is None:
            try:
                code, usage = parse_generation_envelope(body)
            except (
                KeyError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ) as exc:
                record["status"] = "MALFORMED_JSON"
                record["error"] = {
                    "type": type(exc).__name__,
                    "detail": str(exc),
                }
                stop_reason = "MALFORMED_JSON"
                stop_detail = f"envelope:{type(exc).__name__}:{exc}"
            else:
                try:
                    ast.parse(code)
                except (SyntaxError, ValueError) as exc:
                    execution = {
                        "role": "generated_solution",
                        "prog_syn_id": task.prog_syn_id,
                        "test_total": len(extract_hidden_tests(task)),
                        "test_executed": 0,
                        "tests_passed": 0,
                        "all_tests_pass": False,
                        "failure_kind": "syntax_failure",
                        "infrastructure_failure": False,
                        "wall_seconds": 0.0,
                        "records": [],
                        "syntax_error": {
                            "type": type(exc).__name__,
                            "detail": str(exc),
                        },
                    }
                else:
                    execution = execute_solution_v2(
                        task,
                        code,
                        "generated_solution",
                        attempt_dir / "execution",
                        docker_identity["id"],
                    )
                write_json(attempt_dir / "execution_summary.json", execution)
                row_summary = summarize_generation_result(execution, parse_failures=0)
                record.update(row_summary)
                record["code_sha256"] = json_hash(code)
                record["model_latency_seconds"] = model_latency
                record["execution_wall_seconds"] = float(
                    execution["wall_seconds"]
                )
                record["usage"] = usage
                record["finish_reason"] = body.get("choices", [{}])[0].get(
                    "finish_reason"
                )
                if execution["infrastructure_failure"]:
                    stop_reason = "INFRASTRUCTURE_FAILURE"
                    stop_detail = f"docker:{task.prog_syn_id}:{arm}"

        if "usage" not in record:
            record["usage"] = usage
        if "model_latency_seconds" not in record:
            record["model_latency_seconds"] = model_latency
        if "execution_wall_seconds" not in record:
            record["execution_wall_seconds"] = 0.0
        ledger["accounting_tokens_used"] += int(record["usage"]["total_tokens"])
        if ledger["accounting_tokens_used"] > SPEC["reserved_accounting_tokens"]:
            stop_reason = "TOKEN_BUDGET_EXHAUSTED"
            stop_detail = "accounting_token_budget"
        ledger["records"].append(record)
        rows.append(record)
        result["budget"] = {
            "reserved_attempts": SPEC["reserved_attempts"],
            "reserved_accounting_tokens": SPEC["reserved_accounting_tokens"],
            "attempts_used": ledger["attempts_used"],
            "physical_http_calls": ledger["physical_http_calls"],
            "model_identity_probe_calls": 1,
            "accounting_tokens_used": ledger["accounting_tokens_used"],
        }
        result["metrics"] = aggregate_metrics(rows)
        write_json(MODEL_LEDGER_PATH, ledger)
        write_json(MODEL_RESULT_PATH, result)
        if stop_reason:
            break

    complete = ledger["attempts_used"] == SPEC["reserved_attempts"]
    if complete and stop_reason is None:
        status = "COMPLETE_16_ATTEMPTS"
        paired = result["metrics"]["paired_all_tests_pass_difference"]
        base_infra = result["metrics"]["infrastructure_failure_rate"]["base"]
        update_infra = result["metrics"]["infrastructure_failure_rate"][
            "update_info"
        ]
        decision = (
            "PROCEED_TO_CROSS_MODEL_REPLICATION"
            if paired >= 2 and update_infra <= base_infra
            else "BOUNDED_NEGATIVE_STOP"
        )
        settlement_status = (
            "SETTLED_PASS_GATE"
            if decision == "PROCEED_TO_CROSS_MODEL_REPLICATION"
            else "SETTLED_BOUNDED_NEGATIVE"
        )
        reason = (
            f"Completed all 16 frozen attempts; paired all-tests-pass difference "
            f"was {paired:+d} families."
        )
    else:
        status = f"STOPPED_{stop_reason or 'INCOMPLETE'}"
        decision = "STOP_ADAPTER"
        settlement_status = "SETTLED_STOPPED"
        reason = stop_detail or "batch_incomplete"

    result.update(
        {
            "finished_at": now_iso(),
            "status": status,
            "decision": decision,
            "stop_reason": stop_reason,
            "stop_detail": stop_detail,
        }
    )
    result["metrics"] = aggregate_metrics(rows)
    ledger["status"] = status
    ledger["stop_reason"] = stop_reason
    ledger["stop_detail"] = stop_detail
    write_json(MODEL_LEDGER_PATH, ledger)
    write_json(MODEL_RESULT_PATH, result)
    write_json(FINAL_RESULT_PATH, result)
    write_text(FINAL_REPORT_PATH, render_final_report(result))
    settle_budget_ledger(
        attempts_used=int(ledger["attempts_used"]),
        accounting_tokens_used=int(ledger["accounting_tokens_used"]),
        status=settlement_status,
        reason=reason,
    )
    print(
        json.dumps(
            {
                "status": status,
                "decision": decision,
                "attempts": ledger["attempts_used"],
                "tokens": ledger["accounting_tokens_used"],
                "paired_difference": result["metrics"][
                    "paired_all_tests_pass_difference"
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if status == "COMPLETE_16_ATTEMPTS" else 1


def main(argv: Iterable[str] | None = None) -> int:
    """Dispatch the explicit prepare or run phase."""

    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "run"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.phase == "prepare":
        return prepare()
    return run_model_batch()


if __name__ == "__main__":
    raise SystemExit(main())
