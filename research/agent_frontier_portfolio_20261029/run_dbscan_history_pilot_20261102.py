#!/usr/bin/env python3
"""Repeat the target Agent episode with the actual source task and program."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from run_dbscan_agent_pilot_20261102 import INSTRUCTIONS, prepare, replace_once
from run_dbscan_metric_control_20261102 import SOURCE_HASH
from run_dbscan_reference_20261101 import sha


SOURCE_RAW_HASH = "7a0f85f6f20126fdc503d98b693692d02d99a5841056d46d910e1a067fd7bde2"


def add_history(text):
    text = replace_once(text, "case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
                        "case=ROOT/(task+'__prior_source_code__'+str(os.getpid()))")
    text = replace_once(text, "(work/'data').mkdir()", "(work/'data').mkdir()\n"
                        "shutil.copy2(Path(os.environ['DBSCAN_SOURCE_CODE']),work/'prior_solution.py')\n"
                        "shutil.copy2(Path(os.environ['DBSCAN_SOURCE_INSTRUCTIONS']),work/'prior_instructions.txt')")
    text = replace_once(text, "Use available tools to implement and execute your solution.",
                        "A previous related task and its agent-produced program are available at "
                        "/root/prior_instructions.txt and /root/prior_solution.py. Consult them if useful; "
                        "follow the current task instructions. Use available tools to implement and execute your solution.")
    return replace_once(text, "receipt={'task':task,'arm':arm", "receipt={'task':task,'arm':'prior_source_code'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source_instructions = args.tasks / "dbscan-parameter-tuning-1/instruction.md"
    source_receipt = json.loads(args.source_receipt.read_text(encoding="utf-8"))
    if (sha(args.source) != SOURCE_HASH or sha(source_instructions) != INSTRUCTIONS[1]
            or source_receipt.get("raw_sha256") != SOURCE_RAW_HASH
            or source_receipt.get("task") != "dbscan-parameter-tuning-1"
            or source_receipt.get("agent_exit") != 0):
        raise ValueError("source Agent history changed")
    text, provenance = prepare(args.base, args.tasks, args.projection, args.proof_root, 2)
    text = add_history(text)
    compile(text, str(args.base), "exec")
    provenance.update({"condition": "prior_source_code", "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                       "source_code_sha256": SOURCE_HASH, "source_instruction_sha256": INSTRUCTIONS[1],
                       "source_raw_sha256": SOURCE_RAW_HASH, "source_receipt_sha256": sha(args.source_receipt),
                       "limitation": "Post-hoc single target; source code and instructions give additional information."})
    print(json.dumps(provenance), flush=True)
    if args.check:
        return
    os.environ["DBSCAN_TASKS_ROOT"] = str(args.tasks.resolve())
    os.environ["DBSCAN_PROJECTED_DATA"] = str(args.projection.resolve())
    os.environ["DBSCAN_SOURCE_CODE"] = str(args.source.resolve())
    os.environ["DBSCAN_SOURCE_INSTRUCTIONS"] = str(source_instructions.resolve())
    sys.argv = [str(args.base), "dbscan-parameter-tuning-2", "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(args.base)}
    try:
        exec(compile(text, str(args.base), "exec"), namespace)
    finally:
        case = namespace.get("case")
        if case is not None and case.is_dir():
            (case / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
