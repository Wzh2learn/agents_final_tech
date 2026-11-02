#!/usr/bin/env python3
"""Development target episodes for a retry/authentication contract change."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from qualify_skillevol_retry_20261102 import COMMIT
from run_dbscan_agent_pilot_20261102 import BASE_HASH, replace_once
from run_dbscan_reference_20261101 import IMAGE, sha
from run_retry_feedback_controls_20261102 import PROBE_HASH, SOURCE_RAW_HASH, validate_source
from run_skillevol_retry_agent_20261102 import QUALIFICATION_HASH, derive as derive_source


TARGET = "retry-masks-auth-expiry-trap"
PINNED = {
    "instruction.md": "83734f82288a8b6a787e2e1d9cd4e34f757c1356f2cb3697617ee062b05d6569",
    "task-spec.yaml": "54796a91b50124e0163e62eed197aafa3cff1c9c17d46f5f6322b00ccb8bacc7",
    "environment/auth_client.py": "11dbc881730d90c17902b2bcc28b75261f08113fa4eb85c97f2f80935b89febe",
    "environment/auth_policy.py": "68ad5b1ad27876a310aa7c43952d1c33de26cf8bbc2534af2ddbe0977692bd26",
    "environment/mock_auth_api.py": "d8f8968aa412421b24050a397948c86fe4a7408307f661615f82b0aa9f085340",
    "environment/token_session.py": "df03026117ae1109e6ae0205c13da986d204d7dbc1621cca8ec0c4cef5026536",
    "solution/solve.sh": "5ff07da7cccefeebdcb36cde37cbd9cade375f4a1da8f75c074b69f1464e248a",
    "tests/test.sh": "e51f8c82a375e594c8e7e4350be722b56a3d1d159fef137e6405b9c1097181a2",
    "tests/test_outcome.py": "90feaab7736188bd0a11a6106bc29f06dc9a1c2a803129d89b15dd8e716224dc",
    "tests/test_process.py": "58850759f97b0e34fc7e18e2d3058c59c45d0b0e7af3e8a0393580922bc272ed",
}
SOURCE_FEEDBACK = ("The previous task's outcome checks passed 6/6. An additional process check reported missing "
                   "Retry-After handling in the client, while a separate nine-case mock behavior probe passed 9/9.\n")


def derive(base_text, arm):
    text = derive_source(base_text)
    text = replace_once(text, "'tictoc-unnecessary-abort-detection','429-with-retry-after-header') or arm",
                        "'tictoc-unnecessary-abort-detection','429-with-retry-after-header',"
                        "'retry-masks-auth-expiry-trap') or arm")
    if arm in ("source_program_plus_feedback", "source_program_required"):
        text = replace_once(text, "case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
                            "case=ROOT/(task+'__" + arm + "__'+str(os.getpid()))")
        marker = "(work/'instructions.txt').write_text(body,encoding='utf8')"
        extra = (marker + "\nshutil.copy2(Path(os.environ['RETRY_SOURCE_INSTRUCTION']),work/'prior_instructions.txt')"
                 "\nshutil.copy2(Path(os.environ['RETRY_SOURCE_PROJECT'])/'retry_client.py',work/'prior_retry_client.py')"
                 "\nshutil.copy2(Path(os.environ['RETRY_SOURCE_PROJECT'])/'rate_limit_policy.py',work/'prior_policy.py')"
                 "\n(work/'prior_feedback.txt').write_text(os.environ['RETRY_SOURCE_FEEDBACK'],encoding='utf8')"
                 "\nfor _n in ('prior_instructions.txt','prior_retry_client.py','prior_policy.py','prior_feedback.txt'): (work/_n).chmod(0o644)")
        text = replace_once(text, marker, extra)
        optional = ("f'Read the earlier task, program and feedback in {target}/prior_* if useful. "
                    "Work only inside {target}/task and follow the current task. Do not ask for user input. '")
        required = ("f'Before solving, use the read tool to inspect {target}/prior_instructions.txt, "
                    "{target}/prior_retry_client.py, {target}/prior_policy.py and {target}/prior_feedback.txt. "
                    "Compare them with the current task, and use only applicable experience. "
                    "Work only inside {target}/task and follow the current task. Do not ask for user input. '")
        text = replace_once(text, "f'Work only inside {target}/task. Follow the task deliverables. Do not ask for user input. '",
                            optional if arm == "source_program_plus_feedback" else required)
        text = replace_once(text, "receipt={'task':task,'arm':arm", "receipt={'task':task,'arm':'" + arm + "'")
    elif arm != "no_history":
        raise ValueError("unsupported condition")
    compile(text, "derived_skillevol_target_runner.py", "exec")
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=("no_history", "source_program_plus_feedback", "source_program_required"))
    for option in ("base", "task", "source-task", "source-case", "checkout", "qualification", "probe"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sha(args.base) != BASE_HASH or sha(args.qualification) != QUALIFICATION_HASH or sha(args.probe) != PROBE_HASH:
        raise ValueError("base or source evidence changed")
    if subprocess.check_output(["git", "-C", str(args.checkout), "rev-parse", "HEAD"], text=True).strip() != COMMIT:
        raise ValueError("source revision changed")
    for name, expected in PINNED.items():
        if sha(args.task / name) != expected:
            raise ValueError("target asset changed: " + name)
    if args.task.name != TARGET:
        raise ValueError("unexpected target task")
    image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"], text=True).strip()
    if image != IMAGE:
        raise ValueError("container image changed")
    source_hashes = validate_source(args.source_task, args.source_case, args.qualification, args.probe)
    text = derive(args.base.read_text(encoding="utf-8"), args.arm)
    provenance = {"status": "DEVELOPMENT_NOT_OFFICIAL_HARNESS", "task": TARGET, "condition": args.arm,
                  "source_commit": COMMIT, "target_assets_sha256": PINNED, "source_raw_sha256": SOURCE_RAW_HASH,
                  "source_project_sha256": source_hashes, "qualification_sha256": QUALIFICATION_HASH,
                  "source_behavior_probe_sha256": PROBE_HASH, "base_sha256": BASE_HASH,
                  "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "source_feedback_sha256": hashlib.sha256(SOURCE_FEEDBACK.encode()).hexdigest() if args.arm != "no_history" else None,
                  "max_http": 24, "max_post_bytes": 1500000, "max_agent_wall_seconds": 1200,
                  "agent_sees_target_tests_or_solution": False,
                  "limitation": "Same benchmark family and single episodes; source history adds information."}
    print(json.dumps(provenance), flush=True)
    if args.check:
        return
    os.environ["SKILLEVOL_TASKS_ROOT"] = str(args.task.parent.resolve())
    if args.arm != "no_history":
        os.environ["RETRY_SOURCE_INSTRUCTION"] = str((args.source_task / "instruction.md").resolve())
        os.environ["RETRY_SOURCE_PROJECT"] = str((args.source_case / "work/task").resolve())
        os.environ["RETRY_SOURCE_FEEDBACK"] = SOURCE_FEEDBACK
    sys.argv = [str(args.base), TARGET, "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(args.base)}
    try:
        exec(compile(text, str(args.base), "exec"), namespace)
    finally:
        case = namespace.get("case")
        if case is not None and case.is_dir():
            (case / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
