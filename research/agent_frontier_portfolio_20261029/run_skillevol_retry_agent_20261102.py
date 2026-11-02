#!/usr/bin/env python3
"""Run the SkillEvolBench retry acquisition task with a bounded local Agent.

Only task instructions and environment are given to the Agent. The released
solution and verifier are mounted in a separate container after execution.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from qualify_skillevol_retry_20261102 import COMMIT, embedded_verifier, validate
from run_dbscan_agent_pilot_20261102 import BASE_HASH, replace_once
from run_dbscan_reference_20261101 import sha


QUALIFICATION_HASH = "022c731ee609d60989e433653ebe0b0c35b180018868b41259e535afd8879f06"
OUTPUT_ROOT = "/home/testuser/wzh/research_evidence/agent_learning_20261030/skillevolbench_retry_agent_20261102"
TASK = "429-with-retry-after-header"


def derive(base_text):
    changes = [
        ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029", OUTPUT_ROOT, 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')",
         "UP=Path(os.environ['SKILLEVOL_TASKS_ROOT'])", 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection','429-with-retry-after-header') or arm", 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'instruction.md').read_text(encoding='utf8').strip()", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "shutil.copytree(src/'environment',work/'task')\n"
         "(work/'task'/'Dockerfile').unlink()\n"
         "(work/'task').chmod(0o777)\n"
         "for _p in (work/'task').rglob('*'): _p.chmod(0o777 if _p.is_dir() else 0o666)", 1),
        ("f'Work only inside {target}. Generate the required output files. Do not ask for user input. '",
         "f'Work only inside {target}/task. Follow the task deliverables. Do not ask for user input. '", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "Use the task files and observe the results of your changes.", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1200)", 1),
        ("len(calls)>=8", "len(calls)>=24", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>1500000", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
    ]
    text = base_text
    for old, new, count in changes:
        text = replace_once(text, old, new, count)
    start_marker = "verifier_command='python -m pytest -q -p no:cacheprovider /verifier/test_outputs.py'"
    end_marker = "\ntry:\n v=subprocess.run(verify,"
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError("base verification block changed")
    start, end = text.index(start_marker), text.index(end_marker)
    replacement = """from qualify_skillevol_retry_20261102 import embedded_verifier
(case/'upstream_embedded_verifier.py').write_text(embedded_verifier((src/'tests'/'test.sh').read_text(encoding='utf8')),encoding='utf8')
(case/'verifier_logs').mkdir()
verify=['docker','run','--rm','--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cpus','1','--memory','768m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=256m','-e','HOME=/tmp','-e','PROJECT_ROOT=/project','-e','SCRIPT_DIR=/asset/tests','-e','LOG_DIR=/logs','--mount',f'type=bind,src={work / "task"},dst=/project,readonly','--mount',f'type=bind,src={src},dst=/asset,readonly','--mount',f'type=bind,src={case / "verifier_logs"},dst=/logs','--mount',f'type=bind,src={case / "upstream_embedded_verifier.py"},dst=/verifier.py,readonly','python:3.12-slim','python3','/verifier.py']"""
    text = text[:start] + replacement + text[end:]
    compile(text, "derived_skillevol_retry_runner.py", "exec")
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sha(args.base) != BASE_HASH or sha(args.qualification) != QUALIFICATION_HASH:
        raise ValueError("base runner or prior qualification changed")
    qualification = json.loads(args.qualification.read_text(encoding="utf-8"))
    if (qualification.get("source_commit") != COMMIT
            or qualification["variants"]["released_solution"]["verification"]["exit_code"] != 0
            or qualification["variants"]["starter"]["verification"]["exit_code"] != 1
            or qualification["variants"]["empty_result_negative_control"]["verification"]["exit_code"] != 1):
        raise ValueError("source task has not passed qualification")
    validate(args.task, args.checkout)
    if args.task.name != TASK:
        raise ValueError("unexpected task")
    text = derive(args.base.read_text(encoding="utf-8"))
    provenance = {"status": "DEVELOPMENT_NOT_OFFICIAL_HARNESS", "task": TASK, "condition": "no_history",
                  "source_commit": COMMIT, "base_sha256": BASE_HASH,
                  "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "qualification_sha256": QUALIFICATION_HASH, "max_http": 24, "max_post_bytes": 1500000,
                  "max_step_output_tokens_configured": 8192, "max_agent_wall_seconds": 1200,
                  "cpus": 2, "memory": "3g", "agent_sees_tests_or_solution": False}
    print(json.dumps(provenance), flush=True)
    if args.check:
        return
    os.environ["SKILLEVOL_TASKS_ROOT"] = str(args.task.parent.resolve())
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
