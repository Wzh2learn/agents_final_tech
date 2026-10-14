#!/usr/bin/env python3
"""Smoke: load validate_v2 through the runner's load_validator() and exercise
positive/negative validation cases. Zero model calls, read-only."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_s4c_qualification.py"

CASES = {
    "plan_ok": ("plan", '{"tool":"calc","params":{"expression":"12 - 4"}}'),
    "plan_commas_rejected": ("plan", '{"tool":"calc","params":{"expression":"1,801.5 - 1,661.1"}}'),
    "consume_ok": ("consume", '{"row":"ASG","periods":["2019","2018"],"delta_source":-98.9,"delta_target":-98.9,"unit":"unit"}'),
    "consume_placeholder_rejected": ("consume", '{"row":"ASG","periods":["2019","2018"],"delta_source":"<calc result>","delta_target":"<x>","unit":"unit"}'),
    "prose_rejected": ("plan", "Okay, let us think step by step."),
}
EXPECTED_OK = {
    "plan_ok": True,
    "plan_commas_rejected": False,
    "consume_ok": True,
    "consume_placeholder_rejected": False,
    "prose_rejected": False,
}


def main() -> int:
    spec = importlib.util.spec_from_file_location("runner_smoke", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["runner_smoke"] = module
    spec.loader.exec_module(module)
    validator = module.load_validator()

    results = {}
    for name, (stage, text) in CASES.items():
        result = validator.validate_stage_response(stage, text)
        results[name] = {
            "stage": stage,
            "ok": result.ok,
            "route": result.route,
            "schema_error": result.schema_error,
            "expected_ok": EXPECTED_OK[name],
            "as_expected": bool(result.ok) == EXPECTED_OK[name],
        }
    summary = {
        "module_registered": "validate_v2_frozen" in sys.modules,
        "validator_sha256": module.sha256_file(module.BRIDGE_V2 / "validate_v2.py"),
        "cases": results,
        "all_as_expected": all(row["as_expected"] for row in results.values()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_as_expected"] and summary["module_registered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())