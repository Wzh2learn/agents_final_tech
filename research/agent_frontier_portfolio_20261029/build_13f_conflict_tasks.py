#!/usr/bin/env python3
"""Freeze two explicit-contract development tasks from the exposed 13F case."""
import argparse
import json
from pathlib import Path

try:
    from .audit_13f_class_literals import class_literals, sha_file
except ImportError:
    from audit_13f_class_literals import class_literals, sha_file


TEST = '''import json
from pathlib import Path

OUTPUT = Path("/root/count.json")
EXPECTED = Path("/verifier/expected.json")

def test_output_contract():
    obj = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert isinstance(obj, dict) and set(obj) == {"count"}
    assert type(obj["count"]) is int

def test_count_matches_explicit_contract():
    obj = json.loads(OUTPUT.read_text(encoding="utf-8"))
    gold = json.loads(EXPECTED.read_text(encoding="utf-8"))
    assert obj["count"] == gold["count"]
'''

TASKS = {
    "financial-feedback-t1": ("financial-analysis-1", "RENAISSANCE TECHNOLOGIES LLC"),
    "financial-feedback-t2": ("financial-analysis-2", "Bridgewater Associates, LP"),
}


def make_instruction(manager, labels):
    policy = json.dumps(labels, ensure_ascii=False)
    return f'''---
schema_version: '1.0'
---
Analyze the provided public filing archive `/root/13f_q3.zip` using local tools.
It contains `SUBMISSION.tsv`, `COVERPAGE.tsv`, and `INFOTABLE.tsv`.
For this research task, use the following explicit definition, regardless of any
other definition of "stock": the allowed TITLEOFCLASS values are {policy}.
For each row, compare TITLEOFCLASS.lower() exactly to that list; do not perform
other whitespace or fuzzy normalization. Select the unique filing whose
SUBMISSION.PERIODOFREPORT is `30-SEP-2025` and whose
COVERPAGE.FILINGMANAGER_NAME equals `{manager}` ignoring case. Join the tables
by ACCESSION_NUMBER and count matching INFOTABLE rows, including all such rows
individually; do not count unique issuers or estimate assets under management.
Write `/root/count.json` containing exactly one key, `count`, with an integer.
Process the entire archive. Do not print the entire dataset to the conversation.
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_task_root", type=Path)
    ap.add_argument("literal_audit", type=Path)
    ap.add_argument("archive", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    audit = json.loads(args.literal_audit.read_text(encoding="utf-8"))
    if sha_file(args.archive) != audit["archive_sha256_raw"]:
        raise ValueError("archive differs from source qualification")
    all_labels = None
    for _, (source_task, _) in TASKS.items():
        solution = args.source_task_root / source_task / "solution/solve.sh"
        if sha_file(solution) != audit["tasks"][source_task]["solution_sha256_raw"]:
            raise ValueError("solution differs from source qualification")
        _, labels = class_literals(solution.read_text(encoding="utf-8"))
        if all_labels is not None and labels != all_labels:
            raise ValueError("source tasks use different literal policies")
        all_labels = labels
    if len(all_labels) != 25 or len(set(all_labels)) != 25:
        raise ValueError("unexpected class policy")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "CONTROLLED_DEVELOPMENT_NOT_OFFICIAL_BENCHMARK",
                "archive_sha256_raw": sha_file(args.archive), "task_assets": {}}
    for name, (source_task, manager) in TASKS.items():
        task = args.output / "tasks" / name
        (task / "verifier").mkdir(parents=True)
        (task / "task.md").write_text(make_instruction(manager, all_labels), encoding="utf-8")
        (task / "verifier/test_outputs.py").write_text(TEST, encoding="utf-8")
        (task / "verifier/expected.json").write_text(
            json.dumps({"count": audit["tasks"][source_task]["separate_literals_count"]}) + "\n", encoding="utf-8")
        manifest["task_assets"][name] = {"source_task": source_task,
            "task_sha256": sha_file(task / "task.md"),
            "verifier_sha256": sha_file(task / "verifier/test_outputs.py"),
            "expected_sha256": sha_file(task / "verifier/expected.json")}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
