#!/usr/bin/env python3
"""Summarize frozen single-episode PDF/Excel arms without exporting raw data."""
import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from .score_pdf_excel_transfer import score
except ImportError:
    from score_pdf_excel_transfer import score


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_summary(text, label):
    match = re.search(r"(\d+) " + label + r"\b", text)
    return int(match.group(1)) if match else 0


def score_file(path, expected):
    try:
        evaluation = score(json.loads(path.read_text(encoding="utf-8")), expected)
    except (UnicodeDecodeError, json.JSONDecodeError):
        evaluation = {"status": "INVALID_JSON"}
    evaluation["report_sha256"] = digest(path)
    return evaluation


def summarize(root, expected, baseline=None, normalized=None):
    arms = {}
    for case in sorted(root.glob("pdf-excel-diff__*")):
        intervention = json.loads((case / "intervention.json").read_text(encoding="utf-8"))
        condition = intervention["condition"]
        if condition in arms:
            raise ValueError("multiple episodes for a frozen single-episode condition")
        receipt = json.loads((case / "receipt.json").read_text(encoding="utf-8"))
        if digest(case / "raw.jsonl") != receipt["raw_sha256"]:
            raise ValueError("raw receipt hash mismatch")
        for name, expected_hash in intervention["public_input_sha256"].items():
            if digest(case / "work" / name) != expected_hash:
                raise ValueError("public input changed during execution: " + name)
        report = case / "work/diff_report.json"
        if report.exists():
            evaluation = score_file(report, expected)
        else:
            evaluation = {"status": "NO_OUTPUT"}
        verifier_text = (case / "verifier.txt").read_text(encoding="utf-8", errors="replace")
        calls = receipt["model_http_requests"]
        steps = receipt["step_finish_tokens"]
        arms[condition] = {
            "case_name": case.name,
            "agent_exit": receipt["agent_exit"], "verifier_exit": receipt["verifier_exit"],
            "verifier_passed": count_summary(verifier_text, "passed"),
            "verifier_failed": count_summary(verifier_text, "failed"),
            "verifier_errors": count_summary(verifier_text, "errors?"),
            "elapsed_seconds_including_verifier": receipt["elapsed_seconds"],
            "http_post_forwarded": sum(x == "POST /v1/chat/completions" for x in calls),
            "http_get_forwarded": sum(x == "GET /v1/models" for x in calls),
            "http_rejected": [x for x in calls if x.startswith("DENIED")],
            "post_body_bytes_forwarded": sum(receipt["post_content_lengths"]),
            "step_finish_events": len(steps),
            "reported_step_tokens_including_cache": sum(t.get("total", 0) or 0 for t in steps),
            "reported_cache_read_tokens": sum((t.get("cache") or {}).get("read", 0) or 0 for t in steps),
            "raw_sha256": receipt["raw_sha256"], "evaluation": evaluation,
        }
    required = {"no_memory", "prior_experience", "task_skills"}
    if set(arms) != required:
        raise ValueError("expected exactly the three frozen conditions")
    result = {"status": "DEVELOPMENT_ONLY_THREE_SINGLE_EPISODES", "conditions": arms,
              "limitations": ["one synthetic public task instance", "same benchmark as source invoice task",
                              "memory and skills have unequal information", "reported step totals include cache reads",
                              "no independent human gold and PDF field identity not independently verified"]}
    if normalized is not None:
        result["posthoc_no_memory_flattened"] = score_file(normalized, expected)
    if baseline is not None:
        result["posthoc_deterministic_baseline"] = {
            "diagnostic": json.loads((baseline / "diagnostic.json").read_text(encoding="utf-8")),
            "evaluation": score_file(baseline / "diff_report.json", expected)}
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("expected", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--normalized", type=Path)
    args = ap.parse_args()
    result = summarize(args.root, json.loads(args.expected.read_text(encoding="utf-8")), args.baseline, args.normalized)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
