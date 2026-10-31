#!/usr/bin/env python3
"""Adapt the project's pinned isolated Agent runner to a scope-shift pilot."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


CONDITIONS = {
    "source": ("dependency-scope-source", "no_skill"),
    "learn": ("dependency-scope-learn", "no_skill"),
    "target_none": ("dependency-scope-target", "no_skill"),
    "target_history": ("dependency-scope-target", "no_skill"),
    "target_generated_skill": ("dependency-scope-target", "no_skill"),
    "target_native_skills": ("dependency-scope-target", "all_skill"),
}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare(args):
    task, arm = CONDITIONS[args.condition]
    manifest = json.loads((args.pilot / "manifest.json").read_text(encoding="utf-8"))
    if sha(args.base) != manifest["assets_sha256"]["base"]:
        raise ValueError("base runner changed")
    if sha(args.lock) != manifest["assets_sha256"]["lock"]:
        raise ValueError("dependency input changed")
    if sha(args.assets / "trivy") != manifest["assets_sha256"]["binary"]:
        raise ValueError("scanner binary changed")
    if sha(args.assets / "trivy-cache/db/trivy.db") != manifest["assets_sha256"]["db"]:
        raise ValueError("scanner database changed")
    for rel, expected in manifest["tasks"].items():
        if sha(args.pilot / "tasks" / rel) != expected:
            raise ValueError("frozen task/skill file changed: " + rel)
    if args.condition in ("learn", "target_history") and (not args.history or not args.history.is_file()):
        raise ValueError("actual source history required")
    if args.condition == "target_generated_skill" and (not args.skill or not args.skill.is_file()):
        raise ValueError("actual generated skill required")
    text = args.base.read_text(encoding="utf-8")
    changes = [
        ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029",
         "/home/testuser/wzh/research_evidence/agent_learning_20261030/dependency_scope_agent_pilot_20261031/agent_runs", 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')",
         "UP=Path(os.environ['SCOPE_TASKS_ROOT'])", 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection',"
         "'dependency-scope-source','dependency-scope-target','dependency-scope-learn') or arm", 1),
        ("'transaction-concurrency-control-foundations']}[task]",
         "'transaction-concurrency-control-foundations'], "
         "'dependency-scope-target':['trivy-offline-vulnerability-scanning',"
         "'cvss-score-extraction','vulnerability-csv-reporting']}[task]", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "if task != 'dependency-scope-learn':\n"
         " shutil.copy2(Path(os.environ['SCOPE_LOCK']),work/'package-lock.json')\n"
         " (work/'trivy-cache').mkdir()\n"
         " subprocess.run(['cp','--reflink=auto','-a',str(Path(os.environ['SCOPE_ASSETS'])/'trivy-cache/db'),str(work/'trivy-cache/db')],check=True)\n"
         "if os.environ.get('SCOPE_HISTORY'): shutil.copy2(Path(os.environ['SCOPE_HISTORY']),work/'previous_history.md')\n"
         "if os.environ.get('SCOPE_SKILL'): shutil.copy2(Path(os.environ['SCOPE_SKILL']),work/'experience.md')", 1),
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
         "Use local tools and do not print an entire database or large report into the conversation.", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); "
         "cmd[_at:_at]=['--mount',f'type=bind,src={Path(os.environ[\"SCOPE_ASSETS\"])/\"trivy\"},dst=/usr/local/bin/trivy,readonly']; "
         "server=Server(str(sockpath),Handler);", 1),
    ]
    hint = ""
    if args.condition == "target_history":
        hint = "Read /root/previous_history.md for the earlier task and observed feedback. "
    elif args.condition == "target_generated_skill":
        hint = "Read /root/experience.md, a skill written from a previous task and its feedback. "
    if hint:
        changes.append(("+ 'Use available tools to implement and execute your solution. Do not access network.",
                        "+ " + repr(hint) + " + 'Use available tools to implement and execute your solution. Do not access network.", 1))
    for old, new, count in changes:
        if text.count(old) != count:
            raise ValueError("base runner fragment changed: " + old[:100])
        text = text.replace(old, new)
    compile(text, str(args.base), "exec")
    receipt = {"condition": args.condition, "task": task, "arm": arm,
               "status": "DEVELOPMENT_NOT_OFFICIAL_HARNESS",
               "base_sha256": sha(args.base), "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
               "history_sha256": sha(args.history) if args.history else None,
               "skill_sha256": sha(args.skill) if args.skill else None,
               "max_forwarded_http": 16, "max_post_bytes": 900000,
               "max_step_output_tokens": 8192, "agent_timeout_seconds": 600}
    return text, receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("condition", choices=tuple(CONDITIONS))
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--skill", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text, receipt = prepare(args)
    print(json.dumps(receipt), flush=True)
    if args.check:
        return
    os.environ["SCOPE_TASKS_ROOT"] = str(args.pilot / "tasks")
    os.environ["SCOPE_ASSETS"] = str(args.assets)
    os.environ["SCOPE_LOCK"] = str(args.lock)
    if args.history:
        os.environ["SCOPE_HISTORY"] = str(args.history)
    else:
        os.environ.pop("SCOPE_HISTORY", None)
    if args.skill:
        os.environ["SCOPE_SKILL"] = str(args.skill)
    else:
        os.environ.pop("SCOPE_SKILL", None)
    sys.argv = [str(args.base), receipt["task"], receipt["arm"]]
    namespace = {"__name__": "__main__", "__file__": str(args.base)}
    exec(compile(text, str(args.base), "exec"), namespace)
    case = namespace["case"]
    (case / "intervention.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"condition": args.condition, "case_path": str(case)}), flush=True)


if __name__ == "__main__":
    main()
