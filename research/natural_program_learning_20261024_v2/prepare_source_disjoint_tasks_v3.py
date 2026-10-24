"""Prepare a source-role-disjoint task pool for future confirmation runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from run_natural_program_experiment_v2 import training_rows
from source_role_contract_v3 import role_groups, select_source_disjoint_tasks, source_role


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--prior", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    tasks = load_jsonl(args.tasks)
    train_rows = training_rows(tasks, "ordinary_answer_execution_sft")
    train_tasks = [task for task in tasks if task["task_id"] in {row["task_id"] for row in train_rows}]
    prior_rows = [row for path in args.prior for row in load_jsonl(path)]
    prior_tasks = [
        task for task in tasks
        if task["task_id"] in {row.get("source_task_id") for row in prior_rows}
    ]
    excluded_keys = {
        key
        for task in train_tasks + prior_tasks
        for key in source_role(task).keys
    }
    candidates = [task for task in tasks if task.get("split") == "train"]
    selected = select_source_disjoint_tasks(
        candidates,
        excluded_task_ids={task["task_id"] for task in train_tasks + prior_tasks},
        excluded_source_keys=excluded_keys,
        count=96,
    )
    args.output.write_text(
        "".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in selected),
        encoding="utf-8",
    )
    manifest = {
        "schema": "source_disjoint_task_pool_v3",
        "input_task_sha256": sha256_file(args.tasks),
        "prior_inputs": [str(path) for path in args.prior],
        "training_task_count": len(train_tasks),
        "training_source_keys": sum(len(source_role(task).keys) for task in train_tasks),
        "prior_task_count": len(prior_tasks),
        "selected_task_count": len(selected),
        "selected_split_counts": dict(Counter(task["split"] for task in selected)),
        "excluded_source_key_count": len(excluded_keys),
        "selected_task_ids": [task["task_id"] for task in selected],
        "selected_source_key_count": len({
            key for task in selected for key in source_role(task).keys
        }),
        "selected_table_uids": sorted({task["table_uid"] for task in selected}),
    }
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
