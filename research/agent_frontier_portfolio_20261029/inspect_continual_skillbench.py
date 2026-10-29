#!/usr/bin/env python3
"""Read-only qualification of pinned ContinualSkillBench task metadata.

This inventories evaluation contracts and exercises the finance QA helper on
synthetic controls. It does not execute the benchmark agent or expose gold data.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Root of cloned benchmark")
    args = parser.parse_args()
    tasks = args.root / "Continual-Skill-Bench" / "tasks"
    domains = ("finance-econ", "healthcare", "law", "math", "office", "science")
    inventory = {}
    for domain in domains:
        path = tasks / (domain + "-100") / "environment" / "tasks_spec.json"
        if not path.is_file():
            inventory[domain] = {"status": "missing"}
            continue
        data = path.read_bytes()
        rows = json.loads(data)
        if not isinstance(rows, list):
            raise ValueError(f"Expected a task list: {path}")
        inventory[domain] = {
            "task_count": len(rows),
            "eval_types": dict(sorted(collections.Counter(str(r.get("eval_type", "MISSING")) for r in rows).items())),
            "sources": dict(sorted(collections.Counter(str(r.get("source", "MISSING")) for r in rows).items())),
            "spec_sha256": hashlib.sha256(data).hexdigest(),
        }

    helper = tasks / "finance-econ-100" / "tests" / "qa_eval.py"
    module_spec = importlib.util.spec_from_file_location("benchmark_qa_eval", helper)
    mod = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(mod)
    controls = []
    for expected, actual, evaluation in [
        ("12%", "$12", "numeric"),
        ("-5", "5", "numeric"),
        ("-5", "5", "f1"),
        ("12", "12", "numeric"),
    ]:
        controls.append({"expected": expected, "actual": actual, "eval_type": evaluation,
                         "score": mod.qa_score(expected, actual, evaluation)})
    print(json.dumps({"status": "OFFLINE_DEVELOPMENT_ONLY", "domains": inventory,
                      "synthetic_qa_helper_controls": controls,
                      "finance_qa_helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
                      "caveat": "Synthetic controls only; no claim that official judge runtime used this helper or that these strings occur in the dataset."}, indent=2))


if __name__ == "__main__":
    main()
