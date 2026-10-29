#!/usr/bin/env python3
"""Reuse the frozen isolated agent pilot with longer development timeouts.

The two original runs hit a model transport timeout. This changes timeout
limits only; it does not repair or rewrite either historical receipt. The
same task/skill conditions and model POST/output limits remain in the parent.
"""
from pathlib import Path
import hashlib
import json
import os
import sys

source = Path(os.environ.get("TICTOC_BASE_PILOT", str(Path(__file__).resolve().parent.parent / "agent_skill_method_20261029/run_skill_episode_output8192.py")))
text = source.read_text(encoding="utf-8")
changes = [
    ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029", "/home/testuser/wzh/research_evidence/agent_learning_20261030/agent_tictoc_extended"),
    ("'timeout':120000", "'timeout':300000"),
    ("[],[],120)", "[],[],300)"),
    ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)"),
]
for before, after in changes:
    count = text.count(before)
    if count == 0:
        raise ValueError("Expected source fragment missing: " + before)
    text = text.replace(before, after)
print(json.dumps({"base_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "timeout_ms": 300000, "episode_timeout_seconds": 600}), flush=True)
exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
