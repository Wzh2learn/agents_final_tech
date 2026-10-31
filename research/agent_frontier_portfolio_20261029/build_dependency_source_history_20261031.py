#!/usr/bin/env python3
"""Build one bounded history from an actual source Agent run and feedback."""

import argparse
import json
from pathlib import Path

from score_dependency_scope_20261031 import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--scanner-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    case = args.source_case
    intervention = json.loads((case / "intervention.json").read_text(encoding="utf-8"))
    if intervention.get("condition") != "source":
        raise ValueError("case is not the actual source Agent episode")
    report = json.loads(args.scanner_report.read_text(encoding="utf-8"))
    score = evaluate(case / "work/security_audit.csv", report, "high")
    (case / "scope_score.json").write_text(json.dumps(score, indent=2) + "\n", encoding="utf-8")
    selected = []
    for line in (case / "raw.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") in ("tool_use", "text"):
            part = event.get("part") or {}
            item = {"type": event["type"], "tool": part.get("tool"),
                    "state": part.get("state"), "text": part.get("text")}
            selected.append(json.dumps(item, ensure_ascii=False)[:1800])
    events = "\n".join(selected)
    if len(events) > 18000:
        events = events[:9000] + "\n[...middle tool-event excerpt omitted...]\n" + events[-9000:]
    result_path = case / "work/security_audit.csv"
    result = result_path.read_text(encoding="utf-8", errors="replace")[:6000] if result_path.is_file() else "[no CSV output]"
    original = (case / "verifier.txt").read_text(encoding="utf-8", errors="replace")[:4000]
    body = "\n\n".join([
        "# Earlier task\n" + (case / "work/instructions.txt").read_text(encoding="utf-8"),
        "# Actual source tool-event excerpt (per-event and overall length bounded)\n" + events,
        "# Actual source CSV, if any\n" + result,
        "# Original source verifier feedback\n" + original,
        "# Source-only scanner-identity feedback\n" + json.dumps(score, ensure_ascii=False, indent=2),
    ]) + "\n"
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(body)
    print(json.dumps({"source_case": str(case), "history_chars": len(body),
                      "source_score_status": score["status"],
                      "exact_identity_and_scope": score["exact_identity_and_scope"]}))


if __name__ == "__main__":
    main()
