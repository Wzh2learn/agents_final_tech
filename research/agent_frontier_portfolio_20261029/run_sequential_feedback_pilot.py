#!/usr/bin/env python3
"""Small direct-model development pilot; not an official agent benchmark run.

Reads a fixed public task stream on the host. Gold is used only by the local
scorer; it is never included in a model prompt or feedback. Every physical
attempt and raw result is retained. No retry, production API or training.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("benchmark", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    task_root = args.benchmark / "Continual-Skill-Bench/tasks/finance-econ-100"
    data_path = task_root / "environment/tasks_spec.json"
    helper_path = task_root / "tests/qa_eval.py"
    rows = {r["task_id"]: r for r in json.loads(data_path.read_text(encoding="utf-8"))}
    ids = [5, 25, 26]
    assert all(rows[n]["eval_type"] == "numeric" for n in ids)
    assert len({rows[n]["source_id"] for n in ids}) == len(ids)
    helper_spec = importlib.util.spec_from_file_location("qa_eval", helper_path)
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)

    args.output.mkdir(parents=True, exist_ok=False)
    model = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
    config = {"status": "DEVELOPMENT_ONLY_DIRECT_MODEL_NOT_AGENT", "model": model,
              "dataset_commit": "91c76f887c2a422d1f8d4c1adacc944c9c2ad6c1",
              "task_ids": ids, "arms": ["independent", "history_feedback"],
              "planned_physical_attempts": 6, "retries": 0, "max_output_tokens": 1024,
              "temperature": 0, "scoring": "upstream finance qa_eval numeric helper",
              "feedback": "parser outcome or correct/incorrect only; no expected answer",
              "spec_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
              "helper_sha256": hashlib.sha256(helper_path.read_bytes()).hexdigest(),
              "caveat": "Public exposed FinQA development data; no skill learning or causal confirmation."}
    dump(args.output / "frozen_config.json", config)
    history = []
    ledger = []
    for task_id in ids:
        task = rows[task_id]
        for arm in config["arms"]:
            messages = [{"role": "system", "content": "Solve the question. Return only a JSON object with one key answer, whose value is a string. Do not use external tools."}]
            if arm == "history_feedback" and history:
                messages.append({"role": "user", "content": "Previous attempts and outcome feedback, for reference:\n" + json.dumps(history, ensure_ascii=False)})
            messages.append({"role": "user", "content": task["instruction"] + "\nReturn the requested answer as JSON in this response."})
            request = {"model": model, "messages": messages, "temperature": 0,
                       "max_tokens": 1024, "chat_template_kwargs": {"enable_thinking": False}}
            stem = f"{task_id:03d}_{arm}"
            dump(args.output / (stem + "_request.json"), request)
            event = {"task_id": task_id, "source": task["source"], "source_id": task["source_id"],
                     "arm": arm, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "status": "ATTEMPT_STARTED", "tokens": None}
            ledger.append(event)
            dump(args.output / "ledger.json", ledger)
            started = time.monotonic()
            req = urllib.request.Request("http://127.0.0.1:8004/v1/chat/completions",
                                         data=json.dumps(request).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=150) as response:
                    raw = response.read()
                (args.output / (stem + "_response.json")).write_bytes(raw)
                body = json.loads(raw)
                event["tokens"] = body.get("usage")
                choice = body["choices"][0]
                event["finish_reason"] = choice.get("finish_reason")
                content = choice.get("message", {}).get("content") or ""
                try:
                    parsed = json.loads(content)
                    answer = str(parsed["answer"])
                    if not answer.strip():
                        raise ValueError("empty answer")
                    event["score"] = helper.qa_score(str(task["answer"]), answer, "numeric",
                                                      numeric_tolerance=float(task.get("numeric_tolerance") or 1e-4))
                    event["status"] = "SCORED"
                    feedback = "correct" if event["score"] == 1.0 else "incorrect"
                except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                    event["status"] = "OUTPUT_CONTRACT_FAILURE"
                    feedback = "output contract failure; correctness not evaluated"
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError) as exc:
                event["status"] = "REQUEST_OR_RESPONSE_FAILURE"
                event["error_type"] = type(exc).__name__
                feedback = "request or response failed; correctness not evaluated"
            event["elapsed_seconds"] = round(time.monotonic() - started, 3)
            dump(args.output / "ledger.json", ledger)
            if arm == "history_feedback":
                history.append({"task": task["instruction"], "model_response": content if event["status"] != "REQUEST_OR_RESPONSE_FAILURE" else "",
                                "feedback": feedback})
    summary = {"status": "DEVELOPMENT_ONLY", "physical_attempts": len(ledger),
               "counts": {arm: {status: sum(e["arm"] == arm and e["status"] == status for e in ledger)
                                  for status in ("SCORED", "OUTPUT_CONTRACT_FAILURE", "REQUEST_OR_RESPONSE_FAILURE")}
                          for arm in config["arms"]},
               "scores": {arm: [e.get("score") for e in ledger if e["arm"] == arm] for arm in config["arms"]},
               "known_usage": [e["tokens"] for e in ledger],
               "limitations": ["three exposed FinQA tasks", "direct model, not a tool-using agent", "upstream scorer has known semantic limitations", "no independent confirmation", "model pretraining exposure unknown"]}
    dump(args.output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
