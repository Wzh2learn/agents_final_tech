#!/usr/bin/env python3
"""Summarize saved agent receipts and original verifier results."""
from pathlib import Path
import hashlib
import json
import re
import sys


def main(root):
    root = Path(root)
    episodes = []
    for path in sorted(root.glob("llm-prefix-cache-replay__*/receipt.json")):
        receipt = json.loads(path.read_text(encoding="utf8"))
        meta = json.loads((path.parent / "intervention.json").read_text(encoding="utf8"))
        text = (path.parent / "verifier.txt").read_text(encoding="utf8", errors="replace")
        counts = {name: int(n) for n, name in re.findall(r"(\d+) (passed|failed|skipped)", text)}
        episodes.append({"directory": str(path.parent), "intervention": meta,
                         "agent_exit": receipt["agent_exit"], "verifier_exit": receipt["verifier_exit"],
                         "verifier_counts": counts, "seconds": receipt["elapsed_seconds"],
                         "posts": sum(x.startswith("POST ") for x in receipt["model_http_requests"]),
                         "reported_tokens_including_cache": sum(x.get("total", 0) for x in receipt["step_finish_tokens"]),
                         "recorded_steps": len(receipt["step_finish_tokens"]), "raw_sha256": receipt["raw_sha256"],
                         "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    print(json.dumps({"status": "DEVELOPMENT_ONLY", "episodes": episodes,
                      "usage_caveat": "Step totals include cache; missing step usage remains unknown."}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
