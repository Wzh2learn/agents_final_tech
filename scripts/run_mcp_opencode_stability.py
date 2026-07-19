"""Run repeatable, read-only OpenCode/MCP stability checks.

Only elapsed time, status, and digests are persisted.  Model output, tool
output, collection names, endpoints, identifiers, and credentials stay in the
process memory and are never written by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


PROMPT = (
    "Use the knowledge_list_collections MCP tool exactly once. "
    "This is a read-only connectivity check. Do not disclose collection names. "
    "Do not include collection names in the response."
)
EXPECTED_TOOL = "jinrong-rag_knowledge_list_collections"
SUCCESSFUL_TOOL_STATES = {"completed", "success"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--model", default="gb10/qwen3-14b")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def normalized_json_status(output: str) -> str:
    """Classify an OpenCode JSON Lines transcript without retaining its content."""
    parsed_event = False
    expected_tool_seen = False
    expected_tool_error = False

    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        parsed_event = True
        part = event.get("part")
        if not isinstance(part, dict):
            continue
        if part.get("type") not in {"tool", "tool_use"}:
            continue
        if part.get("tool") != EXPECTED_TOOL:
            continue

        expected_tool_seen = True
        state = part.get("state")
        status = state.get("status") if isinstance(state, dict) else None
        if status in SUCCESSFUL_TOOL_STATES:
            return "passed"
        if status == "error":
            expected_tool_error = True

    if expected_tool_error:
        return "tool_error"
    if not parsed_event or not expected_tool_seen:
        return "malformed"
    return "malformed"


def terminate_process_group(process_group_id: int, grace_period: float = 5.0) -> None:
    """Terminate only the session/process group created for one attempt."""
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except ProcessLookupError:
        return

    deadline = time.monotonic() + grace_period
    while time.monotonic() < deadline:
        try:
            os.killpg(process_group_id, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)

    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_once(command: list[str], timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    # A temporary file avoids waiting on inherited stdout/stderr pipe descriptors
    # after OpenCode itself exits.  It is anonymous and never persisted as a result.
    with tempfile.TemporaryFile(mode="w+b") as output_file:
        process = subprocess.Popen(
            command,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # OpenCode starts MCP children.  Clean up only this attempt's process
            # group, including after normal parent exit when a child holds output.
            terminate_process_group(process.pid)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # SIGKILL is only directed at the process group created above.
                terminate_process_group(process.pid, grace_period=0)
                process.wait()

        output_file.seek(0)
        output = output_file.read().decode("utf-8", errors="replace")

    return {
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "status": "timed_out" if timed_out else normalized_json_status(output),
        "output_sha256": digest(output),
    }


def main() -> None:
    args = parse_args()
    if args.runs < 1 or args.timeout < 1:
        raise SystemExit("--runs and --timeout must be positive")
    if args.dry_run:
        print(json.dumps({"runs": args.runs, "valid": True, "writes_results": False, "read_only": True}))
        return
    if args.output_dir is None:
        raise SystemExit("--output-dir is required for a live stability run")
    if not os.getenv("PGDATABASE_URL"):
        raise SystemExit("PGDATABASE_URL must be exported; it is never read or logged by this script")

    args.output_dir.mkdir(parents=True, exist_ok=False)
    command = [
        "bash",
        "scripts/run_opencode_gb10.sh",
        "run",
        "--format",
        "json",
        "--model",
        args.model,
        PROMPT,
    ]
    records = [{"run": number, **run_once(command, args.timeout)} for number in range(1, args.runs + 1)]
    summary = {
        "runs": args.runs,
        "passed": sum(record["status"] == "passed" for record in records),
        "all_passed": all(record["status"] == "passed" for record in records),
        "sanitized": True,
        "records": records,
    }
    (args.output_dir / "stability_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("runs", "passed", "all_passed", "sanitized")}, indent=2))


if __name__ == "__main__":
    main()
