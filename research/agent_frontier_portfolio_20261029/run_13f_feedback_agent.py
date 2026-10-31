#!/usr/bin/env python3
"""Run one frozen explicit-contract agent episode with optional past feedback."""
import hashlib
import json
import os
from pathlib import Path
import sys


BASE_HASH = "4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb"
CONDITIONS = ("source", "no_history", "history_only", "history_contract_feedback",
              "history_upstream_feedback", "history_conflict_check")


def sha_file(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def history_message(condition, history):
    if condition in ("source", "no_history"):
        return ""
    if not isinstance(history.get("previous_count"), int) or isinstance(history.get("previous_count"), bool):
        raise ValueError("previous count is unavailable")
    msg = ("A prior agent solved a related task with the same 25-category rule and reporting period "
           "for RENAISSANCE TECHNOLOGIES LLC. Its final count was " + str(history["previous_count"]) + ". ")
    if condition == "history_contract_feedback":
        check = history["contract_checker"]
        msg += f"The explicit-contract checker {check['verdict']} that count; its reference was {check['expected']}. "
    elif condition in ("history_upstream_feedback", "history_conflict_check"):
        check = history["upstream_checker"]
        msg += f"The original benchmark checker {check['verdict']} that count; its reference was {check['expected']}. "
    if condition == "history_conflict_check":
        msg += "If past feedback and the current written task conflict, inspect the evidence before reusing either. "
    return msg


def prepare(base, root, archive, condition, history_path=None):
    if condition not in CONDITIONS or sha_file(base) != BASE_HASH:
        raise ValueError("unsupported condition or changed base runner")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if sha_file(archive) != manifest["archive_sha256_raw"]:
        raise ValueError("input archive differs from frozen task")
    task = "financial-feedback-t1" if condition == "source" else "financial-feedback-t2"
    task_dir = root / "tasks" / task
    asset = manifest["task_assets"][task]
    for relative, key in (("task.md", "task_sha256"), ("verifier/test_outputs.py", "verifier_sha256"),
                          ("verifier/expected.json", "expected_sha256")):
        if sha_file(task_dir / relative) != asset[key]:
            raise ValueError("frozen task or verifier changed: " + relative)
    history = {}
    if condition not in ("source", "no_history"):
        if history_path is None:
            raise ValueError("history condition requires recorded T1 history")
        history = json.loads(history_path.read_text(encoding="utf-8"))
    hint = history_message(condition, history)
    text = base.read_text(encoding="utf-8")
    changes = [
        ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029",
         "/home/testuser/wzh/research_evidence/agent_learning_20261030/13f_feedback_conflict_20261031/agent_runs", 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')",
         "UP=Path(os.environ['CONFLICT_TASKS_ROOT'])", 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection',"
         "'financial-feedback-t1','financial-feedback-t2') or arm", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "shutil.copy2(Path(os.environ['CONFLICT_ARCHIVE']), work/'13f_q3.zip')", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)", 1),
        ("len(calls)>=8", "len(calls)>=16", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>900000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason = ('method' if line not in allowed else 'request_cap' if len(calls)>=16 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "Never print the full archive or tables; inspect a small sample and process the complete files in code.", 1),
    ]
    if hint:
        changes.append(("+ 'Use available tools to implement and execute your solution. Do not access network.",
                        "+ " + repr(hint) + " + 'Use available tools to implement and execute your solution. Do not access network.", 1))
    for old, new, expected in changes:
        if text.count(old) != expected:
            raise ValueError("base runner fragment differs: " + old[:90])
        text = text.replace(old, new)
    compile(text, str(base), "exec")
    provenance = {"condition": condition, "task": task, "base_sha256": sha_file(base),
                  "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "archive_sha256": manifest["archive_sha256_raw"], "task_assets": asset,
                  "history_sha256": sha_file(history_path) if history_path else None,
                  "history_message": hint, "max_forwarded_http": 16,
                  "max_forwarded_post_bytes": 900000, "max_step_output_tokens": 8192,
                  "agent_timeout_seconds": 600, "status": "CONTROLLED_DEVELOPMENT"}
    return text, provenance


def main():
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in CONDITIONS or (len(sys.argv) == 3 and sys.argv[2] != "--check"):
        raise SystemExit("usage: run_13f_feedback_agent.py CONDITION [--check]")
    condition = sys.argv[1]
    root = Path(os.environ["CONFLICT_ROOT"])
    base = Path(os.environ["CONFLICT_BASE_PILOT"])
    archive = Path(os.environ["CONFLICT_ARCHIVE"])
    history_path = Path(os.environ["CONFLICT_HISTORY"]) if os.environ.get("CONFLICT_HISTORY") else None
    os.environ["CONFLICT_TASKS_ROOT"] = str(root / "tasks")
    text, provenance = prepare(base, root, archive, condition, history_path)
    print(json.dumps(provenance), flush=True)
    if len(sys.argv) == 3:
        return
    sys.argv = [str(base), provenance["task"], "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(base)}
    exec(compile(text, str(base), "exec"), namespace)
    (namespace["case"] / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
