"""Bounded behavioral model probe for the qualified NtripBrowser migration."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXPERIMENT_ID = "PYMIG_NTRIPBROWSER_BEHAVIORAL_PROBE_20261021"
EVIDENCE_IDENTITY = "PUBLIC_REAL_COMMIT_BEHAVIORAL_CASE_PROBE"
TEST_IDS = [
    "tests/test_ntripbrowser.py::test_reassign_parameters",
    "tests/test_ntripbrowser.py::test_invalid_data",
    "tests/test_ntripbrowser.py::test_valid_net_data",
    "tests/test_ntripbrowser.py::test_valid_str_data",
    "tests/test_ntripbrowser.py::test_valid_cas_data",
    "tests/test_ntripbrowser.py::test_valid_data",
    "tests/test_ntripbrowser.py::test_add_coordinates",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def json_hash(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def build_prompt(task: dict[str, Any], arm: str, parent_code: str) -> str:
    facts = task["conditions"][arm]["change_facts"]
    facts_text = (
        json.dumps(facts, ensure_ascii=False, indent=2)
        if facts is not None
        else "None"
    )
    return f"""You are maintaining a Python module after an external dependency change.

{task['actor_visible']['instruction']}

Module path: {task['actor_visible']['module_path']}

Current module:
```python
{parent_code}
```

Change evidence:
{facts_text}

Return exactly one JSON object:
{{"code": string}}

The code field must contain the complete migrated module with no markdown fences
or explanation.
"""


def validate_prompt(
    task: dict[str, Any], arm: str, prompt: str, gold_code: str
) -> None:
    if gold_code in prompt:
        raise ValueError("prompt_contains_gold_code_substring")
    if '{"code": string}' not in prompt:
        raise ValueError("prompt_missing_output_schema")
    if arm == "BASE":
        if "cchardet" in prompt:
            raise ValueError("base_prompt_contains_target_dependency")
    else:
        if "cchardet" not in prompt:
            raise ValueError("change_prompt_missing_target_dependency")


def verify_model_identity(endpoint: str, expected: str) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint, headers={"accept": "application/json"}, method="GET"
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    observed = [
        row["id"]
        for row in body.get("data", [])
        if isinstance(row, dict) and "id" in row
    ]
    if observed != [expected]:
        raise RuntimeError(f"model_identity_mismatch:{observed}")
    return {"expected": expected, "observed": observed, "status": "MATCH"}


def request_model(
    endpoint: str, payload: dict[str, Any], timeout_seconds: int
) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw), time.monotonic() - started


def parse_generation(
    body: dict[str, Any], expected_model: str
) -> tuple[str, dict[str, int]]:
    if body.get("model") != expected_model:
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
    keys = ("prompt_tokens", "completion_tokens", "total_tokens")
    if not all(isinstance(usage.get(key), int) for key in keys):
        raise ValueError("response_usage_types")
    if usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]:
        raise ValueError("response_usage_sum")
    return code, {key: int(usage[key]) for key in keys}


def structural_check(code: str) -> dict[str, Any]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "syntax_valid": False,
            "syntax_error": str(exc),
            "target_imported": False,
            "source_imported": False,
            "target_detect_called": False,
            "pass": False,
        }
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    target_imported = any(
        value == "cchardet" or value.startswith("cchardet.")
        for value in imported.values()
    )
    source_imported = any(
        value == "chardet" or value.startswith("chardet.")
        for value in imported.values()
    )
    target_aliases = {
        local
        for local, value in imported.items()
        if value == "cchardet" or value.startswith("cchardet.")
    }
    target_detect_called = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "detect":
            if isinstance(func.value, ast.Name) and func.value.id in target_aliases:
                target_detect_called = True
        elif isinstance(func, ast.Name):
            resolved = imported.get(func.id, "")
            if resolved == "cchardet.detect":
                target_detect_called = True
    result = {
        "syntax_valid": True,
        "syntax_error": None,
        "target_imported": target_imported,
        "source_imported": source_imported,
        "target_detect_called": target_detect_called,
    }
    result["pass"] = (
        target_imported
        and not source_imported
        and target_detect_called
    )
    return result


def run_hidden_tests(
    source_repo: Path,
    parent_commit: str,
    candidate_code: str,
    gold_env: Path,
    run_dir: Path,
) -> dict[str, Any]:
    candidate_root = run_dir / "candidate"
    if candidate_root.exists():
        shutil.rmtree(candidate_root)
    candidate_root.mkdir(parents=True)
    with tarfile.open(candidate_root / "snapshot.tar", "w") as archive:
        pass
    candidate_root.joinpath("snapshot.tar").unlink()
    subprocess.run(
        [
            "git",
            "-C",
            str(source_repo),
            "archive",
            parent_commit,
        ],
        check=True,
        stdout=(candidate_root / "snapshot.tar").open("wb"),
    )
    with tarfile.open(candidate_root / "snapshot.tar") as archive:
        archive.extractall(candidate_root)
    candidate_root.joinpath("snapshot.tar").unlink()
    target_file = candidate_root / "ntripbrowser" / "ntripbrowser.py"
    target_file.write_text(candidate_code, encoding="utf-8")
    command = [
        str(gold_env / "bin" / "python"),
        "-m",
        "pytest",
        "-q",
        "--disable-warnings",
        *TEST_IDS,
        f"--junitxml={run_dir / 'junit.xml'}",
    ]
    env = os.environ.copy()
    env["PYCURL_CURL_CONFIG"] = "/home/testuser/miniconda3/bin/curl-config"
    env["PYCURL_SSL_LIBRARY"] = "openssl"
    env["LD_LIBRARY_PATH"] = (
        "/home/testuser/miniconda3/lib"
        + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    )
    completed = subprocess.run(
        command,
        cwd=candidate_root,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    (run_dir / "pytest.stdout.txt").write_text(
        completed.stdout, encoding="utf-8"
    )
    (run_dir / "pytest.stderr.txt").write_text(
        completed.stderr, encoding="utf-8"
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "all_tests_pass": completed.returncode == 0,
        "stdout": str(run_dir / "pytest.stdout.txt"),
        "stderr": str(run_dir / "pytest.stderr.txt"),
        "junit": str(run_dir / "junit.xml"),
    }


def reserve_budget(ledger_path: Path, spec: dict[str, Any]) -> None:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    reservation_id = spec["reservation_id"]
    if any(row["id"] == reservation_id for row in ledger["reservations"]):
        raise RuntimeError("budget_reservation_already_exists")
    attempts = int(spec["global_limits"]["reserved_attempts"])
    tokens = int(spec["global_limits"]["reserved_accounting_tokens"])
    if int(ledger["new_budget"]["attempts_used"]) + attempts > int(
        ledger["new_budget"]["attempt_cap"]
    ):
        raise RuntimeError("attempt_cap_exceeded")
    if int(ledger["new_budget"]["accounting_tokens_used"]) + tokens > int(
        ledger["new_budget"]["accounting_tokens_cap"]
    ):
        raise RuntimeError("token_cap_exceeded")
    ledger["reservations"].append(
        {
            "id": reservation_id,
            "attempts": attempts,
            "accounting_tokens": tokens,
            "spec": (
                "research/research_portfolio_v2/pymigbench_external_change_v1/"
                "ntripbrowser_qualification_v2/BEHAVIORAL_PROBE_SPEC.json"
            ),
            "status": "RESERVED_NOT_RUN",
        }
    )
    write_json(ledger_path, ledger)


def settle_budget(
    ledger_path: Path,
    spec: dict[str, Any],
    attempts: int,
    physical_http_calls: int,
    tokens: int,
    status: str,
    raw_result: str,
    reason: str,
) -> None:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    reservation = next(
        row
        for row in ledger["reservations"]
        if row["id"] == spec["reservation_id"]
    )
    if reservation["status"] != "RESERVED_NOT_RUN":
        raise RuntimeError("reservation_already_settled")
    if attempts > int(reservation["attempts"]):
        raise RuntimeError("reserved_attempts_exceeded")
    if tokens > int(reservation["accounting_tokens"]):
        raise RuntimeError("reserved_tokens_exceeded")
    reservation["status"] = status
    ledger["new_budget"]["attempts_used"] = int(
        ledger["new_budget"]["attempts_used"]
    ) + attempts
    ledger["new_budget"]["physical_http_calls"] = int(
        ledger["new_budget"]["physical_http_calls"]
    ) + physical_http_calls
    ledger["new_budget"]["accounting_tokens_used"] = int(
        ledger["new_budget"]["accounting_tokens_used"]
    ) + tokens
    ledger["events"].append(
        {
            "id": f"{EXPERIMENT_ID}_001_{attempts:03d}",
            "attempts": attempts,
            "physical_http_calls": physical_http_calls,
            "accounting_tokens": tokens,
            "raw_result": raw_result,
            "status": status,
            "reason": reason,
        }
    )
    write_json(ledger_path, ledger)


def prepare(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    source_repo = Path(args.source_repo)
    parent_commit = task["source"]["parent_commit"]
    gold_commit = task["source"]["gold_commit"]
    parent_code = subprocess.run(
        [
            "git",
            "-C",
            str(source_repo),
            "show",
            f"{parent_commit}:ntripbrowser/ntripbrowser.py",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    gold_code = subprocess.run(
        [
            "git",
            "-C",
            str(source_repo),
            "show",
            f"{gold_commit}:ntripbrowser/ntripbrowser.py",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    planned = []
    for arm in spec["arms"]:
        prompt = build_prompt(task, arm, parent_code)
        validate_prompt(task, arm, prompt, gold_code)
        request = {
            "model": spec["model"]["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": spec["generation"]["temperature"],
            "top_p": spec["generation"]["top_p"],
            "max_tokens": spec["generation"]["max_tokens"],
            "response_format": {"type": spec["generation"]["response_format"]},
            "chat_template_kwargs": {
                "enable_thinking": spec["generation"]["enable_thinking"]
            },
        }
        planned.append(
            {
                "attempt_index": len(planned) + 1,
                "arm": arm,
                "prompt_sha256": json_hash(prompt),
                "request_sha256": json_hash(request),
                "prompt": prompt,
                "request": request,
            }
        )
    snapshot = {
        "schema": "pymigbench_behavioral_probe_snapshot_v1",
        "created_at": now_iso(),
        "evidence_identity": EVIDENCE_IDENTITY,
        "source": {
            "repository": task["source"]["repository"],
            "parent_commit": parent_commit,
            "gold_commit": gold_commit,
            "parent_code_sha256": hashlib.sha256(
                parent_code.encode("utf-8")
            ).hexdigest(),
            "gold_code_sha256": hashlib.sha256(
                gold_code.encode("utf-8")
            ).hexdigest(),
        },
        "planned_requests": planned,
    }
    write_json(output_dir / "REQUEST_SNAPSHOT.json", snapshot)
    write_json(output_dir / "MODEL_SPEC.json", spec)
    reserve_budget(Path(args.ledger), spec)
    report = [
        "# NtripBrowser Behavioral Probe Pre-Model Report",
        "",
        f"- Task: `{task['task_id']}`",
        "- Arms: `BASE`, `PROSE_CHANGE_FACTS`, `STRUCTURED_CHANGE_FACTS`",
        "- Planned requests: `3`; retries: `0`; concurrency: `1`",
        "- Hidden behavioral tests: `7` deterministic local/mocked tests.",
        "- Gold code is absent from prompts and reserved for evaluation.",
        "- BASE contains neither `chardet.detect` nor `cchardet` outside the source module's existing import.",
        "",
        "This is one real-commit behavioral case, not a population estimate.",
    ]
    (output_dir / "PRE_MODEL_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    return 0


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    spec = json.loads((output_dir / "MODEL_SPEC.json").read_text(encoding="utf-8"))
    snapshot = json.loads(
        (output_dir / "REQUEST_SNAPSHOT.json").read_text(encoding="utf-8")
    )
    identity = verify_model_identity(
        spec["model"]["models_endpoint"], spec["model"]["model"]
    )
    source_repo = Path(args.source_repo)
    gold_env = Path(args.gold_env)
    rows = []
    attempts = 0
    physical = 0
    tokens = 0
    stop_reason = None
    stop_detail = None
    started = now_iso()
    for planned in snapshot["planned_requests"]:
        raw_dir = output_dir / "raw" / f"attempt_{planned['attempt_index']:03d}_{planned['arm']}"
        raw_dir.mkdir(parents=True, exist_ok=True)
        write_json(raw_dir / "request.json", planned["request"])
        try:
            body, latency = request_model(
                spec["model"]["endpoint"],
                planned["request"],
                int(spec["generation"]["timeout_seconds"]),
            )
            attempts += 1
            physical += 1
            write_json(raw_dir / "response.json", body)
            code, usage = parse_generation(body, spec["model"]["model"])
            tokens += usage["total_tokens"]
            structural = structural_check(code)
            behavioral = run_hidden_tests(
                source_repo=source_repo,
                parent_commit=task["source"]["parent_commit"],
                candidate_code=code,
                gold_env=gold_env,
                run_dir=raw_dir,
            )
            row = {
                "attempt_index": planned["attempt_index"],
                "arm": planned["arm"],
                "request_sha256": planned["request_sha256"],
                "raw_request": str(raw_dir / "request.json"),
                "raw_response": str(raw_dir / "response.json"),
                "usage": usage,
                "latency_seconds": latency,
                "code": code,
                "structural": structural,
                "behavioral": behavioral,
                "status": "OK",
            }
        except Exception as exc:
            attempts += 1
            physical += 1
            conservative = int(spec["generation"]["max_tokens"]) + max(
                1, len(planned["prompt"]) // 4
            )
            tokens += conservative
            row = {
                "attempt_index": planned["attempt_index"],
                "arm": planned["arm"],
                "request_sha256": planned["request_sha256"],
                "raw_request": str(raw_dir / "request.json"),
                "raw_response": None,
                "conservative_accounting_tokens": conservative,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "status": "FAILED_STOP",
            }
            rows.append(row)
            stop_reason = "model_or_evaluation_failure"
            stop_detail = f"{type(exc).__name__}:{exc}"
            break
        rows.append(row)
        if tokens > int(spec["global_limits"]["reserved_accounting_tokens"]):
            stop_reason = "accounting_token_budget"
            stop_detail = "reserved_accounting_tokens_exceeded"
            break
        write_json(
            output_dir / "MODEL_LEDGER.json",
            {
                "schema": "pymigbench_behavioral_probe_ledger_v1",
                "started_at": started,
                "updated_at": now_iso(),
                "identity": identity,
                "attempts_used": attempts,
                "physical_http_calls": physical,
                "accounting_tokens_used": tokens,
                "stop_reason": stop_reason,
                "rows": rows,
            },
        )
    complete = attempts == len(snapshot["planned_requests"])
    status = "SETTLED_COMPLETE" if complete and not stop_reason else "SETTLED_STOPPED"
    result = {
        "schema": "pymigbench_behavioral_probe_result_v1",
        "created_at": now_iso(),
        "evidence_identity": EVIDENCE_IDENTITY,
        "status": status,
        "stop_reason": stop_reason,
        "stop_detail": stop_detail,
        "identity": identity,
        "rows": rows,
        "summary": {
            arm: {
                "attempts": sum(1 for row in rows if row["arm"] == arm),
                "structural_pass": sum(
                    1
                    for row in rows
                    if row["arm"] == arm
                    and row.get("structural", {}).get("pass") is True
                ),
                "behavioral_pass": sum(
                    1
                    for row in rows
                    if row["arm"] == arm
                    and row.get("behavioral", {}).get("all_tests_pass") is True
                ),
                "accounting_tokens": sum(
                    row.get("usage", {}).get("total_tokens", 0)
                    for row in rows
                    if row["arm"] == arm
                ),
            }
            for arm in spec["arms"]
        },
        "nonclaims": task["nonclaims"],
    }
    write_json(output_dir / "MODEL_LEDGER.json", result)
    write_json(output_dir / "PROBE_RESULT.json", result)
    settle_budget(
        Path(args.ledger),
        spec,
        attempts,
        physical,
        tokens,
        status,
        (
            "research/research_portfolio_v2/pymigbench_external_change_v1/"
            "ntripbrowser_qualification_v2/PROBE_RESULT.json"
        ),
        stop_reason or "completed_all_planned_attempts",
    )
    return 0 if complete and not stop_reason else 2


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--task", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--gold-env", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--ledger", required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    return prepare(args) if args.command == "prepare" else run(args)


if __name__ == "__main__":
    raise SystemExit(main())
