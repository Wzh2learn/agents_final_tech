from __future__ import annotations

import inspect
import json
import unittest

from research.adaptive_mechanism_20261027_v1.diagnostics.visible_typed_baseline import (
    VisibleContext,
    answer_from_visible,
    extract_service_list,
)
from research.adaptive_mechanism_20261027_v1.scoring_v2.scorer import parse_table


def visible(table_text: str, paragraphs: dict[int, dict[str, str]] | None = None) -> VisibleContext:
    return VisibleContext(
        paragraphs=paragraphs or {},
        raw_orders={item["raw_order"] for item in (paragraphs or {}).values()},
        table=parse_table(table_text),
    )


class VisibleTypedBaselineTests(unittest.TestCase):
    def test_actor_interface_has_no_gold_or_uid_inputs(self) -> None:
        parameters = inspect.signature(answer_from_visible).parameters
        self.assertEqual(
            list(parameters),
            ["question", "answer_type", "context"],
        )

    def test_mean_uses_closing_period_columns_and_shared_calculator(self) -> None:
        context = visible(
            "columns: C0=(in thousands) | C1=December 31, 2019 | C2=December 31, 2018 | "
            "C3=January 1, 2018\n"
            "R1 [Trade receivables] C0=Trade receivables | C1=9,660 | "
            "C2=11,191 | C3=7,073"
        )
        result = json.loads(
            answer_from_visible(
                "What is the average trade receivables for 2018 and 2019?",
                "arithmetic",
                context,
            )
        )
        self.assertEqual(result["numeric_value"], 10425.5)
        self.assertEqual(
            set(
                result["evidence_refs"]
            ),
            {"TABLE:R1:C1", "TABLE:R1:C2"},
        )
        self.assertEqual(
            len(result["evidence_refs"]),
            2,
        )

    def test_count_returns_typed_count_and_member_headers(self) -> None:
        context = visible(
            "columns: C0= | C1=First | C2=Second | C3=Third | C4=Fourth\n"
            "R1 [Basic earnings per share] C0=Basic earnings per share | "
            "C1=$0.35 | C2=$0.36 | C3=$0.08 | C4=$0.31"
        )
        result = json.loads(
            answer_from_visible(
                "How many quarters did basic earnings per share exceed $0.30?",
                "count",
                context,
            )
        )
        self.assertEqual(result["numeric_value"], 3)
        self.assertEqual(
            result["evidence_refs"],
            ["TABLE:C1", "TABLE:C2", "TABLE:C4"],
        )

    def test_service_list_strips_enum_connectors(self) -> None:
        services = extract_service_list(
            "(i) alpha service, (ii) beta service and (iii) gamma service. "
            "Additional text follows."
        )
        self.assertEqual(
            services,
            ["alpha service", "beta service", "gamma service"],
        )

    def test_missing_visible_service_list_is_reasonable_unknown(self) -> None:
        result = json.loads(
            answer_from_visible(
                "What services have their costs included within the audit fees?",
                "multi-span",
                visible("columns: C0= | C1=2019\nR1 [x] C0=x | C1=1"),
            )
        )
        self.assertTrue(result["unknown"])
        self.assertEqual(result["unit"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
