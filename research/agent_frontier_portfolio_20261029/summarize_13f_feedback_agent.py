#!/usr/bin/env python3
"""Rebuild aggregate 13F feedback-agent results from recorded episodes."""
import argparse
import json
from pathlib import Path
import re

try:
    from .run_13f_feedback_agent import CONDITIONS, history_message, sha_file
except ImportError:
    from run_13f_feedback_agent import CONDITIONS, history_message, sha_file


def trace_signals(path, history):
    commands, messages = [], []
    invalid_lines = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            continue
        part = event.get("part", {})
        if event.get("type") == "tool_use" and part.get("tool") == "bash":
            inputs = part.get("state", {}).get("input", {})
            if isinstance(inputs, dict):
                commands.append(str(inputs.get("command", "")))
        if event.get("type") == "text":
            messages.append(str(part.get("text", "")))
    previous_values = [] if history is None else [history["previous_count"], history["upstream_checker"]["expected"]]
    previous_pattern = (r"\b(?:" + "|".join(re.escape(str(value)) for value in previous_values) + r")\b") if previous_values else None
    return {"bash_commands": len(commands),
            "commands_mentioning_previous_manager": sum("renaissance" in cmd.lower() for cmd in commands),
            "commands_mentioning_previous_counts": sum(bool(previous_pattern and re.search(previous_pattern, cmd)) for cmd in commands),
            "text_messages_mentioning_feedback_or_conflict": sum(bool(re.search(r"feedback|checker|conflict|discrepan", msg, re.I)) for msg in messages),
            "invalid_raw_jsonl_lines": invalid_lines}


def summarize(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    history_path = root / "agent_history.json"
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else None
    if history is not None and not {"previous_count", "upstream_checker", "contract_checker", "source_raw_sha256"} <= history.keys():
        raise ValueError("history is missing its required provenance")
    cases = {}
    for case in sorted((root / "agent_runs").glob("financial-feedback-*__no_skill__*")):
        intervention = json.loads((case / "intervention.json").read_text(encoding="utf-8"))
        condition = intervention["condition"]
        if condition in cases or condition not in CONDITIONS:
            raise ValueError("repeated or unknown condition")
        receipt = json.loads((case / "receipt.json").read_text(encoding="utf-8"))
        if sha_file(case / "raw.jsonl") != receipt["raw_sha256"]:
            raise ValueError("raw hash mismatch")
        if sha_file(case / "work/13f_q3.zip") != manifest["archive_sha256_raw"]:
            raise ValueError("agent input archive changed")
        if condition not in ("source", "no_history"):
            if history is None or intervention["history_sha256"] != sha_file(history_path):
                raise ValueError("history binding mismatch")
            if intervention["history_message"] != history_message(condition, history):
                raise ValueError("history prompt mismatch")
        task = intervention["task"]
        expected_path = root / "tasks" / task / "verifier/expected.json"
        if sha_file(expected_path) != intervention["task_assets"]["expected_sha256"]:
            raise ValueError("frozen expected hash mismatch")
        expected = json.loads(expected_path.read_text(encoding="utf-8"))["count"]
        output_path = case / "work/count.json"
        value = None
        output_status = "NO_OUTPUT"
        if output_path.exists():
            try:
                data = json.loads(output_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and set(data) == {"count"} and type(data["count"]) is int:
                    value = data["count"]
                    output_status = "VALID"
                else:
                    output_status = "INVALID_STRUCTURE"
            except (json.JSONDecodeError, UnicodeDecodeError):
                output_status = "INVALID_JSON"
        calls = receipt["model_http_requests"]
        steps = receipt["step_finish_tokens"]
        cases[condition] = {"case_name": case.name, "task": task, "agent_exit": receipt["agent_exit"],
                            "contract_verifier_exit": receipt["verifier_exit"], "output_status": output_status,
                            "count": value, "expected_count": expected,
                            "correct_under_explicit_contract": output_status == "VALID" and value == expected,
                            "http_post_forwarded": sum(x == "POST /v1/chat/completions" for x in calls),
                            "http_rejected": [x for x in calls if x.startswith("DENIED")],
                            "post_body_bytes_forwarded": sum(receipt["post_content_lengths"]),
                            "reported_step_tokens_including_cache": sum(t.get("total", 0) or 0 for t in steps),
                            "reported_cache_read_tokens": sum((t.get("cache") or {}).get("read", 0) or 0 for t in steps),
                            "step_finish_events": len(steps), "elapsed_seconds_including_verifier": receipt["elapsed_seconds"],
                            "raw_sha256": receipt["raw_sha256"],
                            "trace_signals": trace_signals(case / "raw.jsonl", history),
                            "output_sha256": sha_file(output_path) if output_path.exists() else None}
    if "source" not in cases or "no_history" not in cases:
        raise ValueError("source or no-history condition missing")
    if history is not None and set(cases) != set(CONDITIONS):
        raise ValueError("expected every frozen history condition")
    if history is not None and (cases["source"]["raw_sha256"] != history["source_raw_sha256"]
                                or cases["source"]["count"] != history["previous_count"]):
        raise ValueError("history does not match actual source episode")
    baselines = {}
    for name in ("t1", "t2"):
        case = root / "deterministic_baselines" / name
        if not case.exists():
            continue
        task = "financial-feedback-" + name
        expected = json.loads((root / "tasks" / task / "verifier/expected.json").read_text(encoding="utf-8"))["count"]
        diagnostic = json.loads((case / "diagnostic.json").read_text(encoding="utf-8"))
        answer = json.loads((case / "count.json").read_text(encoding="utf-8"))
        log = (case / "verifier.log").read_text(encoding="utf-8", errors="replace")
        baselines[name] = {"count": answer.get("count"), "matches_contract": answer == {"count": expected},
                           "verifier_passed": "2 passed" in log and "failed" not in log.lower(),
                           "elapsed_seconds_program_only": diagnostic["elapsed_seconds"],
                           "model_calls": diagnostic["model_calls"], "verifier_log_sha256": sha_file(case / "verifier.log")}
    result = {"status": "CONTROLLED_SINGLE_FAMILY_DEVELOPMENT", "cases": cases,
              "deterministic_baselines": baselines,
              "total_forwarded_posts": sum(case["http_post_forwarded"] for case in cases.values()),
              "total_step_tokens_including_cache": sum(case["reported_step_tokens_including_cache"] for case in cases.values()),
              "total_cache_read_tokens": sum(case["reported_cache_read_tokens"] for case in cases.values()),
              "history_sha256": sha_file(history_path) if history is not None else None,
              "previous_checker_conflict": history is not None and history["contract_checker"]["verdict"] != history["upstream_checker"]["verdict"],
              "limitations": ["explicit class policy is a constructed contract, not financial ground truth",
                              "same public data and family, one episode per condition",
                              "history and feedback arms have different prompt information",
                              "step totals include cache reads; missing provider usage is unknown",
                              "literal trace markers do not prove whether the model used or ignored history"]}
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    result = summarize(args.root)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
