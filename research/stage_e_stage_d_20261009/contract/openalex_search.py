#!/usr/bin/env python3
"""Query OpenAlex metadata without printing or persisting credentials."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

QUERIES = {
    "metric_precedent": "software testing mutation score fault detection rate diagnostic coverage observability silent failure",
    "fault_localization_metrics": "fault localization accuracy evaluation metrics software",
    "process_evaluation": "process evaluation step-level correctness outcome supervision",
    "lets_verify": "Let us Verify Step by Step process supervision PRM800K",
    "math_shepherd": "Math-Shepherd verify reinforce LLMs step-by-step",
    "diagnostic_coverage": "diagnostic coverage safety critical systems fault detection",
    "measurement_metaevaluation": "measurement validity meta-evaluation evaluation protocol",
    "observability_metrics": "software observability metrics failure visibility",
}


def load_key() -> str:
    path = Path.home() / ".config" / "openalex.env"
    if not path.exists():
        raise SystemExit("OPENALEX_CONFIG_MISSING")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("OPENALEX_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("OPENALEX_API_KEY_MISSING")


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sources/openalex")
    out.mkdir(parents=True, exist_ok=True)
    key = load_key()
    headers = {"Authorization": f"Bearer {key}", "User-Agent": "JinRongAgents-research/1.0"}
    for name, query in QUERIES.items():
        params = urllib.parse.urlencode({
            "search": query,
            "per-page": 10,
            "select": "id,doi,title,publication_year,publication_date,type,authorships,primary_location,open_access,cited_by_count",
        })
        req = urllib.request.Request(
            "https://api.openalex.org/works?" + params,
            headers=headers,
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        (out / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(name, payload.get("meta", {}).get("count"))
        time.sleep(0.25)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
