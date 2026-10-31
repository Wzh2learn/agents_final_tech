#!/usr/bin/env python3
"""Quantify adjacent-string concatenation in a public task solution.

Replays the actual Python list and a separate-literal interpretation against
the two development filings. It does not decide the correct financial ontology.
"""
import argparse
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import tokenize
from zipfile import ZipFile

try:
    from .recompute_13f_fund_questions import MANAGERS, TARGET_PERIOD, iter_rows, select_unique
except ImportError:
    from recompute_13f_fund_questions import MANAGERS, TARGET_PERIOD, iter_rows, select_unique


def class_literals(source):
    marker = "cat > /tmp/solver.py << 'PYTHON_SCRIPT'\n"
    if marker not in source:
        raise ValueError("solver heredoc not found")
    python_source = source.split(marker, 1)[1].split("\nPYTHON_SCRIPT", 1)[0]
    tree = ast.parse(python_source)
    values = [node.value for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "title_class_of_stocks" for target in node.targets)]
    if len(values) != 1 or not isinstance(values[0], ast.List):
        raise ValueError("stock class list not unique")
    runtime = ast.literal_eval(values[0])
    fragment = ast.get_source_segment(python_source, values[0])
    separated = [ast.literal_eval(token.string) for token in tokenize.generate_tokens(io.StringIO(fragment).readline)
                 if token.type == tokenize.STRING]
    return runtime, separated


def sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("task_root", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    source_inventory = {}
    for path in sorted(args.task_root.glob("financial-analysis-*/solution/solve.sh")):
        runtime, separated = class_literals(path.read_text(encoding="utf-8"))
        source_inventory[path.parent.parent.name] = {"runtime_list_elements": len(runtime),
                                                     "source_string_tokens": len(separated),
                                                     "solution_sha256_raw": sha_file(path)}
    classes = {}
    for task in MANAGERS:
        source_path = args.task_root / task / "solution/solve.sh"
        source = source_path.read_text(encoding="utf-8")
        runtime, separated = class_literals(source)
        classes[task] = {"runtime": runtime, "separated": separated,
                         "solution_sha256_raw": sha_file(source_path), "title_class_counts": Counter()}
    with ZipFile(args.archive) as archive:
        periods = {r["ACCESSION_NUMBER"]: r["PERIODOFREPORT"] for r in iter_rows(archive, "SUBMISSION.tsv")}
        covers = list(iter_rows(archive, "COVERPAGE.tsv"))
        selected = {select_unique(covers, periods, manager)["ACCESSION_NUMBER"]: task
                    for task, manager in MANAGERS.items()}
        for row in iter_rows(archive, "INFOTABLE.tsv"):
            task = selected.get(row["ACCESSION_NUMBER"])
            if task is not None:
                classes[task]["title_class_counts"][row["TITLEOFCLASS"].lower()] += 1
    result = {}
    for task, item in classes.items():
        runtime, separated, counts = item["runtime"], item["separated"], item["title_class_counts"]
        combined_count = sum(count for title, count in counts.items() if title in runtime)
        separated_count = sum(count for title, count in counts.items() if title in separated)
        newly_included = {title: counts[title] for title in separated if title not in runtime and counts[title]}
        expected_path = args.task_root / task / "tests/expected_output.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        result[task] = {"runtime_list_elements": len(runtime), "source_string_tokens": len(separated),
                        "solution_sha256_raw": item["solution_sha256_raw"],
                        "expected_sha256_raw": sha_file(expected_path),
                        "runtime_count": combined_count, "separate_literals_count": separated_count,
                        "additional_rows_under_separate_literals": separated_count - combined_count,
                        "newly_included_class_counts": newly_included,
                        "expected_q2": expected["q2_answer"],
                        "runtime_matches_reference": combined_count == expected["q2_answer"]}
    data = {"status": "POST_HOC_SOURCE_CONTRACT_DIAGNOSTIC", "period": TARGET_PERIOD,
            "archive_sha256_raw": sha_file(args.archive),
            "solution_inventory": source_inventory, "tasks": result,
            "limitations": ["separate literals are a syntactic counterfactual, not an independently validated stock ontology",
                                              "source code matching expected does not prove how expected was generated",
                                              "one public benchmark family; no agent or learning experiment",
                                              "source archive not matched byte-for-byte to SEC"]}
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data))


if __name__ == "__main__":
    main()
