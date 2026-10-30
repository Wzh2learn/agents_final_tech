#!/usr/bin/env python3
"""Controlled repair of one saved output; isolated adaptation, not official harness."""
from pathlib import Path
import hashlib
import json
import os
import sys

if len(sys.argv) != 2 or sys.argv[1] not in ("neutral", "diagnostic"):
    raise SystemExit("usage: run_dialogue_repair_probe.py neutral|diagnostic")
condition = sys.argv[1]
limit = int(os.environ.get("DIALOGUE_REQUEST_LIMIT", "8"))
if limit not in (8, 16):
    raise ValueError("Only the documented 8- and 16-request conditions are supported")
base = Path(os.environ["DIALOGUE_BASE_PILOT"])
initial = Path(os.environ["DIALOGUE_INITIAL_WORK"])
artifacts = ("solution.py", "dialogue.json", "dialogue.dot")
hashes = {n: hashlib.sha256((initial / n).read_bytes()).hexdigest() for n in artifacts}
text = base.read_text(encoding="utf8")
changes = [
    ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029",
     "/home/testuser/wzh/research_evidence/agent_learning_20261030/dialogue_repair"),
    ("'timeout':120000", "'timeout':300000"),
    ("[],[],120)", "[],[],300)"),
    ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)"),
    ("(work/'instructions.txt').write_text(body,encoding='utf8')",
     "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
     + "for _n in ('solution.py','dialogue.json','dialogue.dot'):\n"
     + "    shutil.copy2(Path(os.environ['DIALOGUE_INITIAL_WORK'])/_n, work/_n)\n"
     + "    (work/_n).chmod(0o666)"),
    ("+ 'Use available tools to implement and execute your solution. Do not access network.",
     "+ '" + ("The previous output did not satisfy all verifier checks. " if condition == "neutral" else
                 "The previous output did not satisfy all verifier checks. Choice nodes should be visualized as diamonds. ")
     + "Edit the existing files and regenerate the outputs. ' + 'Use available tools to implement and execute your solution. Do not access network."),
]
if limit == 16:
    changes.extend([("len(calls)>=8", "len(calls)>=16"),
                    ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>900000")])
for before, after in changes:
    expected = 2 if before == "[],[],120)" else 1
    if text.count(before) != expected:
        raise ValueError("Unexpected source fragment count: " + before)
    text = text.replace(before, after)
provenance = {"condition": condition, "request_limit": limit,
              "post_body_byte_limit": 900000 if limit == 16 else 450000,
              "initial_hashes": hashes,
              "base_sha256": hashlib.sha256(base.read_bytes()).hexdigest(),
              "derived_sha256": hashlib.sha256(text.encode()).hexdigest()}
print(json.dumps(provenance), flush=True)
sys.argv = [str(base), "dialogue-parser", "no_skill"]
namespace = {"__name__": "__main__", "__file__": str(base)}
exec(compile(text, str(base), "exec"), namespace)
(namespace["case"] / "intervention.json").write_text(json.dumps(provenance, indent=2), encoding="utf8")
