#!/usr/bin/env python3
"""Create a skill from a real source Agent episode and bounded test feedback.

Only source-task material is sent to the local research model. The future task,
its instructions, outputs, tests and reference are never read by this script.
Raw requests, responses, and a before-call event are preserved outside Git.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_episode", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--generate-prepared", action="store_true")
    args = parser.parse_args()
    if args.prepare_only and args.generate_prepared:
        raise ValueError("choose prepare-only or generate-prepared")
    episode = args.source_episode.resolve()
    receipt = json.loads((episode / "receipt.json").read_text(encoding="utf-8"))
    if receipt["task"] != "earthquake-plate-calculation-1":
        raise ValueError("expected the source task, not a target episode")
    raw = episode / "raw.jsonl"
    if sha(raw) != receipt["raw_sha256"]:
        raise ValueError("source trace does not match its receipt")
    events = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines() if line.strip()]
    actions = []
    for event in events:
        part = event.get("part", {})
        state = part.get("state", {})
        if event.get("type") == "tool_use" and part.get("tool") == "bash" and state.get("status") == "completed":
            command = state.get("input", {}).get("command", "")
            if command and "answer.json" in command:
                output = str(state.get("output", ""))
                actions.append({"command": command[:7000], "output_tail": output[-500:],
                                "original_command_chars": len(command), "original_output_chars": len(output)})
    if not actions:
        raise ValueError("source trace has no answer-writing bash action")
    feedback_text = (episode / "verifier.txt").read_text(encoding="utf-8")
    tests = re.findall(r"(?m)^(test_\w+)\s+\([^\n]+\)(?:\n[^\n]*)?\s*\.\.\.\s*(ok|FAIL|ERROR)\s*$", feedback_text)
    if len(tests) != 8:
        raise ValueError("could not extract all source test statuses without expected values")
    compact = {"source_instruction": (episode / "work/instructions.txt").read_text(encoding="utf-8"),
               "source_produced_answer": json.loads((episode / "work/answer.json").read_text(encoding="utf-8")),
               "source_test_statuses": [{"test": name, "status": status} for name, status in tests],
               "selected_actions": actions[-4:],
               "compaction": "last four completed bash actions mentioning answer.json; command capped at 7000 characters, output tail at 500 characters; no expected test values",
               "execution_status": {"agent_exit": receipt["agent_exit"],
                                    "verifier_exit": receipt["verifier_exit"]}}
    if args.generate_prepared:
        if not args.output.is_dir() or any((args.output / n).exists() for n in
                                           ("request.json", "ledger.json", "response.json", "skill.md")):
            raise ValueError("prepared output is missing or generation was already attempted")
        if json.loads((args.output / "source_history.json").read_text(encoding="utf-8")) != compact:
            raise ValueError("prepared source history changed")
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        write_json(args.output / "source_history.json", compact)
    config = {"status": "DEVELOPMENT_SOURCE_ONLY", "source_trace_sha256": sha(raw),
              "source_receipt_sha256": sha(episode / "receipt.json"),
              "source_instruction_sha256": sha(episode / "work/instructions.txt"),
              "source_feedback_sha256": sha(episode / "verifier.txt"),
              "source_history_sha256": sha(args.output / "source_history.json"),
              "target_task_or_reference_seen_by_author": False,
              "max_tokens": 2048, "temperature": 0, "max_http_attempts": 1}
    if args.generate_prepared:
        if json.loads((args.output / "config.json").read_text(encoding="utf-8")) != config:
            raise ValueError("prepared configuration changed")
    else:
        write_json(args.output / "config.json", config)
    if args.prepare_only:
        print(json.dumps(config), flush=True)
        return
    messages = [{"role": "system", "content": (
        "Create concise, reusable instructions from a past tool-using agent episode and its observed feedback. "
        "Separate general steps from task-specific choices, note failures and unresolved assumptions, "
        "and do not invent results or include the past answer as a future answer. Return only the skill text.")},
        {"role": "user", "content": json.dumps(compact, ensure_ascii=False)}]
    payload = {"model": "Qwen3.6-35B-A3B-Q4_K_M.gguf", "messages": messages,
               "temperature": 0, "max_tokens": 2048, "chat_template_kwargs": {"enable_thinking": False}}
    request_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (args.output / "request.json").write_bytes(request_bytes)
    event = {"status": "ATTEMPT_STARTED", "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "request_sha256": sha(args.output / "request.json"), "usage": None}
    write_json(args.output / "ledger.json", event)
    start = time.monotonic()
    request = urllib.request.Request("http://127.0.0.1:8004/v1/chat/completions",
                                     data=request_bytes,
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            raw_response = response.read()
        (args.output / "response.json").write_bytes(raw_response)
        data = json.loads(raw_response)
        event["usage"] = data.get("usage")
        event["response_model"] = data.get("model")
        choice = data["choices"][0]
        event["finish_reason"] = choice.get("finish_reason")
        content = choice["message"].get("content") or ""
        if not content.strip():
            raise ValueError("empty model content")
        (args.output / "skill.md").write_text(content, encoding="utf-8")
        event.update({"status": "RECEIVED", "response_sha256": sha(args.output / "response.json"),
                      "skill_sha256": sha(args.output / "skill.md")})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        event.update({"status": "FAILED_USAGE_MAY_BE_UNKNOWN", "error_type": type(exc).__name__})
    event["elapsed_seconds"] = time.monotonic() - start
    write_json(args.output / "ledger.json", event)
    print(json.dumps(event), flush=True)


if __name__ == "__main__":
    main()
