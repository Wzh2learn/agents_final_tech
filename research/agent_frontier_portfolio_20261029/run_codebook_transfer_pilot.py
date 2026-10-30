#!/usr/bin/env python3
"""Run the frozen cross-task memory pilot using the isolated project agent runner.

The verifier is mounted only after the episode by the base runner.  A dry check
validates the patch against the precise recorded base without running a model.
"""
import hashlib
import json
import os
from pathlib import Path
import sys


MEMORY = (
    "A previous invoice-processing attempt confused identifiers when a partial "
    "fuzzy match gave a short vendor name the same score as a longer name. "
    "Its repair preferred a complete exact name before fuzzy matching. In the "
    "current task decide whether this experience applies; do not assume that "
    "similar text necessarily denotes the same category. "
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(base, task_root, condition):
    text = base.read_text(encoding="utf-8")
    original = "/home/testuser/wzh/research_evidence/agent_skill_method_20261029"
    result = "/home/testuser/wzh/research_evidence/agent_learning_20261030/codebook_transfer"
    old_map = "'transaction-concurrency-control-foundations']}[task]"
    new_map = ("'transaction-concurrency-control-foundations'], "
               "'manufacturing-codebook-normalization':"
               "['manufacturing-failure-reason-codebook-normalization']}[task]")
    changes = [
        (original, result, 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection',"
         "'manufacturing-codebook-normalization') or arm", 1),
        ("target='/app' if task=='dialogue-parser' else '/root'",
         "target='/app' if task in ('dialogue-parser','manufacturing-codebook-normalization') else '/root'", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "shutil.copytree(src/'environment'/'data', work/'data')\n"
         "(work/'output').mkdir(); (work/'output').chmod(0o777)", 1),
        (old_map, new_map, 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)", 1),
        ("stderr=subprocess.STDOUT,timeout=120)", "stderr=subprocess.STDOUT,timeout=180)", 1),
        ("len(calls)>=8", "len(calls)>=16", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>900000", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "Never read an entire large input into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified files.", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); "
         "cmd[_at:_at]=['-e','PYTHONPATH=/deps',"
         "'--mount',f'type=bind,src={DEPS},dst=/deps,readonly']; "
         "server=Server(str(sockpath),Handler);", 1),
    ]
    if condition == "transferred_memory":
        changes.append(("+ 'Use available tools to implement and execute your solution. Do not access network.",
                        "+ " + repr(MEMORY) + " + 'Use available tools to implement and execute your solution. Do not access network.", 1))
    for old, new, expected in changes:
        if text.count(old) != expected:
            raise ValueError(f"base runner differs: {old[:90]!r}: {text.count(old)} != {expected}")
        text = text.replace(old, new)
    inputs = [task_root / "task.md", task_root / "verifier/test_outputs.py",
              task_root / "environment/skills/manufacturing-failure-reason-codebook-normalization/SKILL.md"]
    inputs.extend(sorted((task_root / "environment/data").glob("*.csv")))
    if len(inputs) != 7 or not all(p.is_file() for p in inputs):
        raise ValueError("Unexpected input set")
    compile(text, str(base), "exec")
    return text, {
        "condition": condition, "base_sha256": sha(base),
        "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "files": {str(p.relative_to(task_root)): sha(p) for p in inputs},
        "model_post_upper_bound": 16, "body_bytes_upper_bound": 900000,
        "per_step_output_limit": 8192, "episode_timeout_seconds": 600,
        "protocol": "development; public benchmark; hidden verifier mounted after episode",
    }


def main():
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ("no_memory", "transferred_memory", "task_skill"):
        raise SystemExit("usage: run_codebook_transfer_pilot.py no_memory|transferred_memory|task_skill [--check]")
    if len(sys.argv) == 3 and sys.argv[2] != "--check":
        raise SystemExit("unknown option")
    condition = sys.argv[1]
    base = Path(os.environ["TRANSFER_BASE_PILOT"])
    task = Path(os.environ["TRANSFER_TASK_ROOT"])
    text, provenance = prepare(base, task, condition)
    print(json.dumps(provenance), flush=True)
    if len(sys.argv) == 3:
        return
    sys.argv = [str(base), "manufacturing-codebook-normalization", "all_skill" if condition == "task_skill" else "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(base)}
    exec(compile(text, str(base), "exec"), namespace)
    (namespace["case"] / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
