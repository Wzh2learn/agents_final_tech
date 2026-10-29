#!/usr/bin/env python3
"""Post-hoc, one-target counterfactual feedback-label development probe."""
import argparse
import datetime as dt
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = json.loads((args.benchmark / "Continual-Skill-Bench/tasks/finance-econ-100/environment/tasks_spec.json").read_text())
    rows = {r["task_id"]: r for r in rows}
    prior = json.loads((args.previous / "025_history_feedback_response.json").read_text())
    prior_response = prior["choices"][0]["message"]["content"]
    args.output.mkdir(parents=True, exist_ok=False)
    labels = ("incorrect", "uncertain", "correct")
    write(args.output / "frozen_config.json", {
        "status": "POSTHOC_SYNTHETIC_FEEDBACK_LABEL_INTERVENTION", "prior_task": 25,
        "target_task": 26, "prior_response_source": str(args.previous / "025_history_feedback_response.json"),
        "conditions": list(labels), "attempt_cap": 3, "retries": 0,
        "model": "Qwen3.6-35B-A3B-Q4_K_M.gguf", "temperature": 0, "max_tokens": 1024,
        "limitations": "one exposed task pair, artificial labels, no tool-using agent, no accuracy or training claim"})
    events = []
    for label in labels:
        history = [{"task": rows[25]["instruction"], "model_response": prior_response, "feedback": label}]
        messages = [
            {"role": "system", "content": "Solve the question. Return only a JSON object with one key answer, whose value is a string. Do not use external tools."},
            {"role": "user", "content": "Previous attempts and outcome feedback, for reference:\n" + json.dumps(history, ensure_ascii=False)},
            {"role": "user", "content": rows[26]["instruction"] + "\nReturn the requested answer as JSON in this response."},
        ]
        payload = {"model": "Qwen3.6-35B-A3B-Q4_K_M.gguf", "messages": messages,
                   "temperature": 0, "max_tokens": 1024, "chat_template_kwargs": {"enable_thinking": False}}
        write(args.output / (label + "_request.json"), payload)
        event = {"condition": label, "status": "ATTEMPT_STARTED", "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "usage": None}
        events.append(event)
        write(args.output / "ledger.json", events)
        started = time.monotonic()
        req = urllib.request.Request("http://127.0.0.1:8004/v1/chat/completions", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=150) as response:
                raw = response.read()
            (args.output / (label + "_response.json")).write_bytes(raw)
            data = json.loads(raw)
            event["usage"] = data.get("usage")
            choice = data["choices"][0]
            event["finish_reason"] = choice.get("finish_reason")
            answer = json.loads(choice["message"].get("content") or "")
            event["answer"] = str(answer["answer"])
            event["status"] = "PARSED"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as exc:
            event["status"] = "FAILED"
            event["error_type"] = type(exc).__name__
        event["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write(args.output / "ledger.json", events)
    print(json.dumps(events))


if __name__ == "__main__":
    main()
