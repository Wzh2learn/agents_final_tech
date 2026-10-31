#!/usr/bin/env python3
"""Bind one real source-agent output to two observed checker results."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_count(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"count"} or type(value["count"]) is not int:
        raise ValueError("source agent did not provide the strict integer contract")
    return value["count"]


def upstream_verdict(log, count, expected):
    if count == expected and "2 passed" in log and "failed" not in log.lower():
        return "accepted"
    if count != expected and "1 failed, 1 passed" in log and f"assert {count} == {expected}" in log:
        return "rejected"
    raise ValueError("original test log does not isolate the q2 comparison")


def prepare(source_case, task_root, original_expected, output):
    count_path = source_case / "work/count.json"
    count = read_count(count_path)
    receipt = json.loads((source_case / "receipt.json").read_text(encoding="utf-8"))
    if sha(source_case / "raw.jsonl") != receipt["raw_sha256"]:
        raise ValueError("source raw receipt mismatch")
    contract = json.loads((task_root / "tasks/financial-feedback-t1/verifier/expected.json").read_text(encoding="utf-8"))["count"]
    if receipt["verifier_exit"] != (0 if count == contract else 1):
        raise ValueError("source checker result differs from strict count contract")
    expected = json.loads(original_expected.read_text(encoding="utf-8"))
    original_count = expected["q2_answer"]
    fixture = dict(expected)
    fixture["q2_answer"] = count
    output.mkdir(parents=True, exist_ok=False)
    (output / "answers.json").write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    meta = {"previous_count": count, "contract_expected": contract,
            "source_contract_verifier_exit": receipt["verifier_exit"],
            "upstream_expected": original_count, "source_raw_sha256": receipt["raw_sha256"],
            "source_output_sha256": sha(count_path), "upstream_expected_sha256": sha(original_expected)}
    (output / "source_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def finalize(root, output):
    meta = json.loads((root / "source_meta.json").read_text(encoding="utf-8"))
    log_path = root / "upstream_verifier.log"
    log = log_path.read_text(encoding="utf-8", errors="replace")
    upstream = upstream_verdict(log, meta["previous_count"], meta["upstream_expected"])
    contract = "accepted" if meta["source_contract_verifier_exit"] == 0 else "rejected"
    history = {"status": "ACTUAL_AGENT_OUTPUT_WITH_OBSERVED_CHECKERS",
               "previous_count": meta["previous_count"],
               "contract_checker": {"verdict": contract, "expected": meta["contract_expected"]},
               "upstream_checker": {"verdict": upstream, "expected": meta["upstream_expected"]},
               "source_raw_sha256": meta["source_raw_sha256"],
               "source_output_sha256": meta["source_output_sha256"],
               "upstream_verifier_log_sha256": sha(log_path)}
    if output.exists():
        raise ValueError("history output already exists")
    output.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    return history


def main():
    ap = argparse.ArgumentParser()
    commands = ap.add_subparsers(dest="command", required=True)
    first = commands.add_parser("prepare")
    first.add_argument("source_case", type=Path)
    first.add_argument("task_root", type=Path)
    first.add_argument("original_expected", type=Path)
    first.add_argument("output", type=Path)
    second = commands.add_parser("finalize")
    second.add_argument("feedback_root", type=Path)
    second.add_argument("history_output", type=Path)
    args = ap.parse_args()
    result = (prepare(args.source_case, args.task_root, args.original_expected, args.output)
              if args.command == "prepare" else finalize(args.feedback_root, args.history_output))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
