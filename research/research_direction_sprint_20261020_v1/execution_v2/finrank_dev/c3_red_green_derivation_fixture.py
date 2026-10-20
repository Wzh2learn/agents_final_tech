#!/usr/bin/env python3
"""Red/green fixture for false pair-derived tool support."""

from __future__ import annotations

import argparse
import inspect
import json

from finrank_contract import (
    PACKAGE,
    answer_tool_consistency,
    write_json,
)


REFERENCE = {
    "answer_atoms": [
        {
            "name": "derived_gross_margin",
            "label_patterns": ["gross margin"],
            "value": 11.97,
            "unit": "percent",
            "period": "FY2024",
            "tolerance": 0.01,
        }
    ],
    "operand_facts": [
        {
            "name": "automotive_revenue",
            "label_patterns": ["automotive revenue"],
            "value": 171606,
            "unit": "USD million",
            "period": "FY2024",
        },
        {
            "name": "automotive_other_cost",
            "label_patterns": ["automotive other cost"],
            "value": 151065,
            "unit": "USD million",
            "period": "FY2024",
        },
    ],
    "derivations": [
        {
            "target_atom": "derived_gross_margin",
            "operand_atoms": [
                "automotive_revenue",
                "automotive_other_cost",
            ],
            "operand_values": {
                "automotive_revenue": 171606,
                "automotive_other_cost": 151065,
            },
            "operator": "MARGIN_PERCENT_FROM_REVENUE_AND_COST",
            "formula": (
                "(automotive_revenue - "
                "automotive_other_cost) / "
                "automotive_revenue * 100"
            ),
        }
    ]
}
CONSUME = {
    "answer_status": "ANSWER",
    "facts": [
        {
            "label": "gross margin",
            "value": 11.97,
            "unit": "percent",
            "period": "FY2024",
        }
    ],
    "used_candidate_ids": ["cand_005"],
}


def tool_result(text: str) -> dict:
    return {
        "tool_status": "OK",
        "evidence": [
            {
                "candidate_id": "cand_005",
                "text": text,
                "page_number": "54-55",
                "visible_source_scope": {},
            }
        ],
    }


def consistency(consume: dict, result: dict, reference: dict) -> dict:
    parameters = inspect.signature(answer_tool_consistency).parameters
    if "reference" in parameters:
        return answer_tool_consistency(consume, result, reference)
    return answer_tool_consistency(consume, result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("red", "green"), required=True)
    args = parser.parse_args()
    false_pair = consistency(
        CONSUME,
        tool_result("Unrelated values 10127 and 846"),
        REFERENCE,
    )
    explicit = consistency(
        CONSUME,
        tool_result("Automotive revenue 171606 cost of sales 151065"),
        REFERENCE,
    )
    if args.phase == "red":
        passed = false_pair["consistent"] is True
        expected = {
            "false_pair_consistent": True,
            "explicit_derivation_consistent": "NOT_REQUIRED_RED",
        }
    else:
        passed = (
            false_pair["consistent"] is False
            and explicit["consistent"] is True
        )
        expected = {
            "false_pair_consistent": False,
            "explicit_derivation_consistent": True,
        }
    observed = {
        "false_pair_consistent": false_pair["consistent"],
        "explicit_derivation_consistent": explicit["consistent"],
    }
    output = {
        "schema": "finrank_c3_derivation_red_green_v1",
        "phase": args.phase,
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "observed": observed,
        "false_pair": false_pair,
        "explicit_derivation": explicit,
        "generation_requests": 0,
    }
    write_json(
        PACKAGE / f"C3_DERIVATION_{args.phase.upper()}.json",
        output,
    )
    print(json.dumps(output, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
