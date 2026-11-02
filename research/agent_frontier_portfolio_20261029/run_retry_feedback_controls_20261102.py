#!/usr/bin/env python3
"""Compare three feedback conditions from the same real source Agent state."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from qualify_skillevol_retry_20261102 import COMMIT, PINNED, validate
from retry_behavior_probe_20261102 import QUALIFICATION_HASH, SOURCE_RAW_HASH
from run_dbscan_agent_pilot_20261102 import BASE_HASH, replace_once
from run_dbscan_reference_20261101 import sha
from run_skillevol_retry_agent_20261102 import TASK, derive as derive_source


PROBE_HASH = "efce707f77a24d4eebb47344e896776cce09410d1061e4614f10ec1cab39b7f8"
SOURCE_POLICY_HASH = "6e0720b57283df8bfbfc2c5d1100ca0f0be2f48ecc8a67235bcfb187072e0998"
FEEDBACK = {
    "neutral": "An automated evaluation reported an issue with your previous attempt. Review the existing solution and improve it while preserving the task's intended behavior.\n",
    "diagnostic": "Automated feedback on your previous attempt: six behavior checks passed; one process check reported 'expected Retry-After header handling'. Investigate the issue and improve the solution while preserving the task's intended behavior.\n",
    "diagnostic_plus_behavior": "Automated feedback on your previous attempt: six behavior checks passed; one process check reported 'expected Retry-After header handling'. A separate local mock probe of six wait values and three retry limits passed 9/9. Investigate and improve the solution while preserving the task's intended behavior.\n",
}


def derive(base_text):
    text = derive_source(base_text)
    text = replace_once(text, "case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
                        "case=ROOT/(task+'__'+os.environ['RETRY_CONDITION']+'__'+str(os.getpid()))")
    old = "shutil.copytree(src/'environment',work/'task')\n(work/'task'/'Dockerfile').unlink()"
    new = ("shutil.copytree(Path(os.environ['RETRY_SOURCE_PROJECT']),work/'task',"
           "ignore=shutil.ignore_patterns('__pycache__','*.pyc'))\n"
           "(work/'feedback.txt').write_text(os.environ['RETRY_FEEDBACK'],encoding='utf8')")
    text = replace_once(text, old, new)
    text = replace_once(text, "f'Work only inside {target}/task. Follow the task deliverables. Do not ask for user input. '",
                        "f'Work only inside {target}/task. Read {target}/feedback.txt before revising the previous attempt. "
                        "Follow the task deliverables. Do not ask for user input. '")
    text = replace_once(text, "receipt={'task':task,'arm':arm", "receipt={'task':task,'arm':os.environ['RETRY_CONDITION']")
    compile(text, "derived_retry_feedback_runner.py", "exec")
    return text


def validate_source(task, agent_case, qualification, probe):
    if sha(qualification) != QUALIFICATION_HASH or sha(probe) != PROBE_HASH:
        raise ValueError("source qualification or behavior probe changed")
    receipt = json.loads((agent_case / "receipt.json").read_text(encoding="utf-8"))
    if (receipt.get("raw_sha256") != SOURCE_RAW_HASH or sha(agent_case / "raw.jsonl") != SOURCE_RAW_HASH
            or receipt.get("task") != TASK or receipt.get("verifier_exit") != 1):
        raise ValueError("source Agent receipt changed")
    probe_data = json.loads(probe.read_text(encoding="utf-8"))
    if probe_data["cases"]["agent_solution"]["checks"]["passed"] != 9:
        raise ValueError("source Agent did not pass the frozen post-hoc behavior probe")
    project, environment = agent_case / "work/task", task / "environment"
    original = {p.relative_to(environment) for p in environment.rglob("*") if p.is_file() and p.name != "Dockerfile"}
    actual = {p.relative_to(project) for p in project.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if actual != original:
        raise ValueError("source Agent project has unexpected files")
    hashes = {}
    for rel in sorted(original):
        expected = SOURCE_POLICY_HASH if rel.as_posix() == "rate_limit_policy.py" else sha(environment / rel)
        if sha(project / rel) != expected:
            raise ValueError("source Agent project changed: " + rel.as_posix())
        hashes[rel.as_posix()] = expected
    if hashes["retry_client.py"] != PINNED["environment/retry_client.py"]:
        raise ValueError("source Agent retry client changed")
    return hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=tuple(FEEDBACK))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sha(args.base) != BASE_HASH:
        raise ValueError("base Agent runner changed")
    validate(args.task, args.checkout)
    source_hashes = validate_source(args.task, args.source_case, args.qualification, args.probe)
    text = derive(args.base.read_text(encoding="utf-8"))
    provenance = {"status": "POSTHOC_FEEDBACK_DEVELOPMENT", "task": TASK, "condition": args.arm,
                  "source_commit": COMMIT, "source_raw_sha256": SOURCE_RAW_HASH,
                  "qualification_sha256": QUALIFICATION_HASH, "behavior_probe_sha256": PROBE_HASH,
                  "source_project_sha256": source_hashes,
                  "feedback_sha256": hashlib.sha256(FEEDBACK[args.arm].encode()).hexdigest(),
                  "base_sha256": BASE_HASH, "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "max_http": 24, "max_post_bytes": 1500000, "max_agent_wall_seconds": 1200,
                  "limitation": "Different feedback conditions; this is not an equal-information or independent confirmation."}
    print(json.dumps(provenance), flush=True)
    if args.check:
        return
    os.environ["SKILLEVOL_TASKS_ROOT"] = str(args.task.parent.resolve())
    os.environ["RETRY_SOURCE_PROJECT"] = str((args.source_case / "work/task").resolve())
    os.environ["RETRY_CONDITION"] = args.arm
    os.environ["RETRY_FEEDBACK"] = FEEDBACK[args.arm]
    sys.argv = [str(args.base), TASK, "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(args.base)}
    try:
        exec(compile(text, str(args.base), "exec"), namespace)
    finally:
        case = namespace.get("case")
        if case is not None and case.is_dir():
            (case / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
