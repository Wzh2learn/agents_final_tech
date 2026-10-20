#!/usr/bin/env python3
"""Create a result-preserving TQ-5 analysis correction outside the frozen snapshot."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20261017T072340Z_5d8942bd"
SOURCE = ROOT / "runs" / RUN_ID / "RESULTS.json"
OUTPUT = ROOT / "reviews" / "TQ5_RESULTS_CORRECTED_v1.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    source_hash = sha256_file(SOURCE)
    results = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    corrected = copy.deepcopy(results)
    corrected["part1"]["summary"]["label"] = (
        "TQ-5 table-disjoint developmental source-separation panel "
        "(original public tasks; not TQ-4 and not pooled with TQ-4)"
    )
    corrected["analysis_corrections"] = [
        {
            "field": "part1.summary.label",
            "old": results["part1"]["summary"]["label"],
            "new": corrected["part1"]["summary"]["label"],
            "reason": "generic analyzer reused the TQ-4 Part 1 label",
            "result_values_changed": False,
        }
    ]
    corrected["source_results_sha256"] = source_hash
    OUTPUT.write_text(json.dumps(corrected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source": str(SOURCE),
        "source_sha256": source_hash,
        "output": str(OUTPUT),
        "output_sha256": sha256_file(OUTPUT),
        "changed_fields": ["part1.summary.label", "analysis_corrections", "source_results_sha256"],
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
