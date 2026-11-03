#!/usr/bin/env python3
"""Run a no-history SkillLearnBench geospatial episode via the existing harness.

The development task and original test are already researcher-exposed. The
agent container sees only the task instructions and three read-only datasets;
the test is mounted in a separate container after the agent has stopped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path("/home/testuser/wzh/research_evidence/agent_learning_20261030")
TASKS = ROOT / "SkillLearnBench/tasks/earthquake-plate-calculation"
QUAL = ROOT / "earthquake_geo_qualification_20261103"
BASE = Path("/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py")
BASE_HASH = "4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb"
OUTPUT = ROOT / "earthquake_geo_agent_20261103"
FILES = ("earthquakes_2024.json", "PB2002_boundaries.json", "PB2002_plates.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_fingerprint(directory):
    digest = hashlib.sha256()
    count = 0
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        relative = path.relative_to(directory).as_posix()
        digest.update(relative.encode("utf-8") + b"\0" + bytes.fromhex(sha(path)))
        count += 1
    if count == 0:
        raise ValueError("empty dependency directory")
    return {"sha256": digest.hexdigest(), "files": count}


def replace_once(source, old, new, count=1):
    if source.count(old) != count:
        raise ValueError(f"unexpected base-runner fragment: {old[:90]!r}")
    return source.replace(old, new)


def prepare(version, condition, source_episode=None, experience=None):
    if sha(BASE) != BASE_HASH:
        raise ValueError("base runner has changed")
    if version == 1 and condition != "no_history":
        raise ValueError("history arms are defined only for the target task")
    qualification_path = QUAL / "reference_controls/receipt.json"
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim",
                                     "--format", "{{.Id}}"], text=True).strip()
    if image != qualification["image"]:
        raise ValueError("container image differs from qualification")
    dependencies = dependency_fingerprint(QUAL / "deps")
    cases = qualification["cases"]
    if (cases["pacific_reference"]["verification"]["exit_code"] != 0
            or cases["africa_reference_unchanged"]["verification"]["exit_code"] == 0
            or cases["africa_transparent_adaptation"]["verification"]["exit_code"] != 0):
        raise ValueError("reference controls do not establish the expected development contract")
    task = TASKS / f"earthquake-plate-calculation-{version}"
    if sha(task / "instruction.md") != qualification["instructions_sha256"][str(version)]:
        raise ValueError("task instructions changed")
    for name in FILES:
        if sha(task / "environment" / name) != qualification["input_sha256"][name]:
            raise ValueError(f"input changed: {name}")
    test_key = "pacific_reference" if version == 1 else "africa_transparent_adaptation"
    if sha(task / "tests/test_outputs.py") != cases[test_key]["test_sha256"]:
        raise ValueError("upstream test changed")
    original = BASE.read_text(encoding="utf-8")
    edits = [
        ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029", str(OUTPUT), 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')",
         f"UP=Path({str(TASKS)!r})", 1),
        ("DEPS=Path('/home/testuser/wzh/projects/agents_final_tech/venv/lib/python3.12/site-packages')",
         f"DEPS=Path({str(QUAL / 'deps')!r})", 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection',"
         "'earthquake-plate-calculation-1','earthquake-plate-calculation-3') or arm", 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'instruction.md').read_text(encoding='utf8').strip()", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "Inspect only the data schema and a small sample; write and execute a program that processes the complete input without printing entire datasets.", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1200)", 1),
        ("len(calls)>=8", "len(calls)>=24", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>1500000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason=('method' if line not in allowed else 'request_cap' if len(calls)>=24 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); "
         "cmd[_at:_at]=['-e','PYTHONPATH=/deps','-e','PROJ_NETWORK=OFF',"
         "'-e','OPENBLAS_NUM_THREADS=1','--mount',f'type=bind,src={DEPS},dst=/deps,readonly'] + "
         "[z for n in GEO_FILES for z in ('--mount',f'type=bind,src={src / \"environment\" / n},dst=/root/{n},readonly')]; "
         "server=Server(str(sockpath),Handler);", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("verifier_command='python -m pytest -q -p no:cacheprovider /verifier/test_outputs.py'",
         "verifier_command='python /verifier/test_outputs.py'", 1),
        ("'--mount',f'type=bind,src={work},dst={target}', '--mount',f'type=bind,src={src / \"verifier\"},dst=/verifier,readonly'",
         "'--mount',f'type=bind,src={work},dst={target},readonly', '--mount',f'type=bind,src={src / \"tests\"},dst=/verifier,readonly'", 1),
    ]
    for old, new, count in edits:
        original = replace_once(original, old, new, count)
    history_mounts = []
    history_hashes = {}
    if condition != "no_history":
        if source_episode is None or experience is None:
            raise ValueError("source episode and prepared experience are required")
        source_receipt = json.loads((source_episode / "receipt.json").read_text(encoding="utf-8"))
        config = json.loads((experience / "config.json").read_text(encoding="utf-8"))
        if (source_receipt["task"] != "earthquake-plate-calculation-1"
                or sha(source_episode / "raw.jsonl") != source_receipt["raw_sha256"]
                or config["source_trace_sha256"] != source_receipt["raw_sha256"]
                or config["source_receipt_sha256"] != sha(source_episode / "receipt.json")
                or config["source_history_sha256"] != sha(experience / "source_history.json")
                or config["target_task_or_reference_seen_by_author"] is not False):
            raise ValueError("source provenance does not match prepared history")
        if condition in ("raw_history", "raw_history_required"):
            history_mounts = [(source_episode / "raw.jsonl", "/root/source_trace.jsonl"),
                              (experience / "source_history.json", "/root/source_history.json")]
            instructions = ("Source history and the complete tool trace from a previous related task are available at "
                            "/root/source_history.json and /root/source_trace.jsonl. The trace is long: inspect "
                            "specific events with a short Python program rather than printing it all. "
                            "Use them if helpful and always follow the current task. ")
            if condition == "raw_history_required":
                instructions = ("Before solving, read /root/source_history.json. The complete source trace "
                                "is also available at /root/source_trace.jsonl; inspect specific events with a "
                                "short Python program rather than printing it all. Follow the current task. ")
        else:
            ledger = json.loads((experience / "ledger.json").read_text(encoding="utf-8"))
            skill = experience / "skill.md"
            if ledger.get("status") != "RECEIVED" or sha(skill) != ledger.get("skill_sha256"):
                raise ValueError("source-generated skill is missing or inconsistent")
            history_mounts = [(skill, "/root/source_skill.md")]
            instructions = ("A skill generated from a previous related task is available at "
                            "/root/source_skill.md. Read it if useful, and follow the current task. ")
            if condition == "generated_skill_required":
                instructions = ("Before solving, read /root/source_skill.md, generated from a previous related task. "
                                "Follow the current task. ")
            history_hashes["author_ledger_sha256"] = sha(experience / "ledger.json")
        for path, destination in history_mounts:
            history_hashes[destination] = sha(path)
        original = replace_once(original, "Use available tools to implement and execute your solution.",
                                instructions + "Use available tools to implement and execute your solution.")
        original = replace_once(original, "case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
                                f"case=ROOT/(task+'__{condition}__'+str(os.getpid()))")
        original = replace_once(original, "receipt={'task':task,'arm':arm",
                                f"receipt={{'task':task,'arm':'{condition}'")
        original = replace_once(original,
                                "+ [z for n in GEO_FILES for z in ('--mount',f'type=bind,src={src / \"environment\" / n},dst=/root/{n},readonly')]; ",
                                "+ [z for n in GEO_FILES for z in ('--mount',f'type=bind,src={src / \"environment\" / n},dst=/root/{n},readonly')] "
                                "+ [z for source,dest in GEO_HISTORY_MOUNTS for z in ('--mount',f'type=bind,src={source},dst={dest},readonly')]; ")
    compile(original, str(BASE), "exec")
    provenance = {"status": "DEVELOPMENT_ONLY_NOT_OFFICIAL_BENCHMARK",
                  "task": version, "condition": condition,
                  "base_sha256": BASE_HASH,
                  "derived_sha256": hashlib.sha256(original.encode()).hexdigest(),
                  "qualification_receipt_sha256": sha(qualification_path),
                  "image": image, "dependency_tree": dependencies,
                  "instruction_sha256": qualification["instructions_sha256"][str(version)],
                  "input_sha256": qualification["input_sha256"],
                  "upstream_test_sha256": cases[test_key]["test_sha256"],
                  "model": "qwen3.6-35b-a3b (configured; deployed weight hash not independently checked)",
                  "max_http": 24, "max_post_body_bytes": 1500000,
                  "max_step_output_tokens_configured": 8192, "max_wall_seconds": 1200,
                  "sandbox": "network-free container; limited local model proxy; test mounted afterward",
                  "history_input_sha256": history_hashes}
    return original, provenance, history_mounts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=int, choices=(1, 3))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--condition", choices=("no_history", "raw_history", "generated_skill",
                                                "raw_history_required", "generated_skill_required"),
                        default="no_history")
    parser.add_argument("--source-episode", type=Path)
    parser.add_argument("--experience", type=Path)
    args = parser.parse_args()
    text, provenance, history_mounts = prepare(args.version, args.condition,
                                                args.source_episode, args.experience)
    print(json.dumps(provenance), flush=True)
    if args.check:
        return
    sys.argv = [str(BASE), f"earthquake-plate-calculation-{args.version}", "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(BASE), "GEO_FILES": FILES,
                 "GEO_HISTORY_MOUNTS": history_mounts}
    try:
        exec(compile(text, str(BASE), "exec"), namespace)
    finally:
        case = namespace.get("case")
        if case is not None and case.is_dir():
            (case / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
