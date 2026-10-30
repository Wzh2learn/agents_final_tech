#!/usr/bin/env python3
"""Summarize completed invoice episodes and post-agent benchmark diagnostics."""
from pathlib import Path
import hashlib
import json
import re
import sys

from score_invoice_output import score


def main(root, reference):
    reference = json.loads(Path(reference).read_text(encoding="utf8"))
    rows = []
    for receipt_path in sorted(Path(root).glob("invoice-fraud-detection__*/receipt.json")):
        case = receipt_path.parent
        r = json.loads(receipt_path.read_text(encoding="utf8"))
        meta = json.loads((case / "intervention.json").read_text(encoding="utf8"))
        verifier = (case / "verifier.txt").read_text(encoding="utf8", errors="replace")
        counts = {name: int(n) for n, name in re.findall(r"(\d+) (passed|failed|skipped)", verifier)}
        output = case / "work" / "fraud_report.json"
        if output.is_file():
            try:
                assessment = score(reference, json.loads(output.read_text(encoding="utf8")))
            except (ValueError, KeyError, TypeError) as exc:
                assessment = {"status": "MALFORMED_OUTPUT", "error": type(exc).__name__}
        else:
            assessment = {"status": "MISSING_OUTPUT"}
        rows.append({"directory": str(case), "intervention": meta,
                     "agent_exit": r["agent_exit"], "verifier_exit": r["verifier_exit"],
                     "verifier_counts": counts, "post_agent_diagnostic": assessment,
                     "seconds": r["elapsed_seconds"],
                     "posts": sum(x.startswith("POST ") for x in r["model_http_requests"]),
                     "reported_tokens_including_cache": sum(x.get("total", 0) for x in r["step_finish_tokens"]),
                     "recorded_steps": len(r["step_finish_tokens"]), "raw_sha256": r["raw_sha256"],
                     "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest()})
    print(json.dumps({"status": "DEVELOPMENT_ONLY", "episodes": rows,
                      "caveat": "Reference-derived diagnostics run only after agents finish."
                                " Step totals include cache; missing usage remains unknown."}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: summarize_invoice_agent.py episode-root ground-truth.json")
    main(*sys.argv[1:])
