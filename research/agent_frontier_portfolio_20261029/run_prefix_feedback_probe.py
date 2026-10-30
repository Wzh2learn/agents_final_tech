#!/usr/bin/env python3
"""Restart one public cache-replay task from identical saved outputs."""
from pathlib import Path
import hashlib
import json
import os
import sys

if len(sys.argv) != 2 or sys.argv[1] not in ("neutral", "diagnostic", "task_skill", "diagnostic_16k"):
    raise SystemExit("usage: run_prefix_feedback_probe.py neutral|diagnostic|task_skill|diagnostic_16k")
condition = sys.argv[1]
base = Path(os.environ["PREFIX_BASE_PILOT"])
initial = Path(os.environ["PREFIX_INITIAL_WORK"])
root = Path(os.environ["PREFIX_TASK_ROOT"])
artifacts = ("solve.py", "report.json")
inputs = ("trace.jsonl", "config.json")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {n: sha(initial / n) for n in artifacts}
for name in inputs:
    if sha(initial / name) != sha(root / "environment" / name):
        raise ValueError("saved public input differs from task source: " + name)
    hashes[name] = sha(initial / name)
text = base.read_text(encoding="utf8")
feedback = ("The previous output did not satisfy all verifier checks. " if not condition.startswith("diagnostic") else
            "The previous output did not satisfy all verifier checks. Check the prompt-token unit and "
            "the final resident-block count against the visible task specification. ")
changes = [
    ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029",
     "/home/testuser/wzh/research_evidence/agent_learning_20261030/prefix_feedback"),
    ("'timeout':120000", "'timeout':300000"),
    ("[],[],120)", "[],[],300)"),
    ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)"),
    ("len(calls)>=8", "len(calls)>=16"),
    ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>900000"),
    ("(work/'instructions.txt').write_text(body,encoding='utf8')",
     "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
     + "for _n in ('solve.py','report.json'):\n"
     + "    shutil.copy2(Path(os.environ['PREFIX_INITIAL_WORK'])/_n, work/_n)\n"
     + "    (work/_n).chmod(0o666)"),
    ("+ 'Use available tools to implement and execute your solution. Do not access network.",
     "+ " + repr(feedback + "Edit the existing files and regenerate the output. ")
     + " + 'Use available tools to implement and execute your solution. Do not access network."),
]
if condition == "diagnostic_16k":
    changes.append(("'output':8192", "'output':16384"))
for before, after in changes:
    expected = 2 if before == "[],[],120)" else 1
    if text.count(before) != expected:
        raise ValueError("Unexpected source fragment count: " + before)
    text = text.replace(before, after)
provenance = {"condition": condition, "request_limit": 16, "post_body_byte_limit": 900000,
              "per_step_output_limit": 16384 if condition == "diagnostic_16k" else 8192,
              "initial_hashes": hashes, "base_sha256": sha(base),
              "derived_sha256": hashlib.sha256(text.encode()).hexdigest()}
print(json.dumps(provenance), flush=True)
sys.argv = [str(base), "llm-prefix-cache-replay", "all_skill" if condition == "task_skill" else "no_skill"]
namespace = {"__name__": "__main__", "__file__": str(base)}
exec(compile(text, str(base), "exec"), namespace)
(namespace["case"] / "intervention.json").write_text(json.dumps(provenance, indent=2), encoding="utf8")
