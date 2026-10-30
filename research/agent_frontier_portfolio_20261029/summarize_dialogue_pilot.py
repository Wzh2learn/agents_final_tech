#!/usr/bin/env python3
"""Summarize saved receipts and verifier counts without reading raw prompts."""
from pathlib import Path
import hashlib
import json
import re
import sys


def main(root):
    root = Path(root)
    paths = list((root / "agent_tictoc_extended").glob("dialogue-parser__*/receipt.json"))
    paths += list((root / "dialogue_repair").glob("dialogue-parser__*/receipt.json"))
    rows = []
    for path in sorted(paths):
        r = json.loads(path.read_text(encoding="utf8"))
        provenance_path = path.parent / "intervention.json"
        prov = json.loads(provenance_path.read_text(encoding="utf8")) if provenance_path.is_file() else None
        verifier = (path.parent / "verifier.txt").read_text(encoding="utf8", errors="replace")
        counts = {name: int(n) for n, name in re.findall(r"(\d+) (passed|failed|skipped)", verifier)}
        rows.append({"directory": str(path.parent), "arm": r["arm"], "repair": prov,
                     "agent_exit": r["agent_exit"], "verifier_exit": r["verifier_exit"],
                     "verifier_counts": counts, "seconds": r["elapsed_seconds"],
                     "physical_posts": sum(x.startswith("POST ") for x in r["model_http_requests"]),
                     "reported_tokens_including_cache": sum(x.get("total", 0) for x in r["step_finish_tokens"]),
                     "recorded_steps": len(r["step_finish_tokens"]), "raw_sha256": r["raw_sha256"],
                     "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    print(json.dumps({"status": "DEVELOPMENT_ONLY", "episodes": rows,
                      "usage_caveat": "Reported step totals include cache; a missing step has unknown usage.",
                      "verification_caveat": "pytest counts are not a general semantic success score."}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
