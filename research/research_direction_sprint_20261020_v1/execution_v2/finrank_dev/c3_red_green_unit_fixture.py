#!/usr/bin/env python3
"""Red/green fixture for the literal-percent scorer defect."""

from __future__ import annotations

import argparse
import json

from finrank_contract import (
    PACKAGE,
    answer_reference_match,
    load_object,
    write_json,
)


CONSUME = {
    "answer_status": "ANSWER",
    "facts": [
        {
            "label": "ROE 2024",
            "value": 8.7,
            "unit": "%",
            "period": "2024",
        },
        {
            "label": "ROIC-adjusted 2024",
            "value": 20.8,
            "unit": "%",
            "period": "2024",
        },
    ],
    "used_candidate_ids": ["cand_005", "cand_003"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("red", "green"), required=True)
    args = parser.parse_args()
    references = load_object(PACKAGE / "REFERENCES_V2.json")
    reference = next(
        item for item in references["tasks"] if item["task_id"] == "ESD_004"
    )
    result = answer_reference_match(CONSUME, reference)
    expected_match = args.phase == "green"
    passed = result["match"] == expected_match
    output = {
        "schema": "finrank_c3_unit_red_green_v1",
        "phase": args.phase,
        "status": "PASS" if passed else "FAIL",
        "expected_match": expected_match,
        "observed_match": result["match"],
        "missing_atoms": result["missing_atoms"],
        "generation_requests": 0,
    }
    write_json(PACKAGE / f"C3_UNIT_{args.phase.upper()}.json", output)
    print(json.dumps(output, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
