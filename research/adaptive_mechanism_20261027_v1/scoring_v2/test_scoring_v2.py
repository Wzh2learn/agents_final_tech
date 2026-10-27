from __future__ import annotations

import json
import unittest

from scorer import load_visible_context, score_response


def source_record(paragraphs: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {"paragraphs": paragraphs or []}


def reference(
    *,
    answer: object,
    answer_type: str,
    table_text: str = "",
    paragraphs: list[dict[str, object]] | None = None,
    source_requirement: str = "table",
    unit: str = "",
    program: str = "",
    question: str = "Synthetic scoring control",
) -> dict[str, object]:
    return {
        "answer": answer,
        "answer_type": answer_type,
        "table_text": table_text,
        "paragraphs": paragraphs or [],
        "source_requirement": source_requirement,
        "unit": unit,
        "program": program,
        "question": question,
    }


def visible(ref: dict[str, object], selected: list[str]) -> object:
    return load_visible_context(source_record(ref["paragraphs"]), ref, selected)


def response(
    answer: object,
    numeric_value: object,
    unit: str,
    refs: list[str],
    *,
    unknown: bool = False,
    clarification: str = "",
) -> str:
    return json.dumps(
        {
            "answer": answer,
            "numeric_value": numeric_value,
            "unit": unit,
            "evidence_refs": refs,
            "unknown": unknown,
            "clarification": clarification,
        },
        ensure_ascii=False,
    )


class ScoringV2Controls(unittest.TestCase):
    def test_semantically_equivalent_currency_display_accepts(self) -> None:
        ref = reference(
            answer=["1,289,962"],
            answer_type="span",
            table_text=(
                "columns: C0=Net sales (in thousands) | C1=2019\n"
                "R1 [Total] C0=Total | C1=$1,289,962"
            ),
            unit="thousand",
        )
        result = score_response(
            response(["$1,289,962"], 1289962, "thousands", ["TABLE:R1:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "ACCEPT")

    def test_exact_multi_span_set_accepts(self) -> None:
        ref = reference(
            answer=["155", "113"],
            answer_type="multi-span",
            table_text=(
                "columns: C0=(in thousands) | C1=2019 | C2=2018\n"
                "R1 [Payroll taxes] C0=Payroll taxes | C1=155 | C2=113"
            ),
            unit="thousand",
        )
        result = score_response(
            response(["155", "113"], None, "thousands", ["TABLE:R1:C1", "TABLE:R1:C2"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "ACCEPT")

    def test_correct_mean_typed_reduction_accepts(self) -> None:
        ref = reference(
            answer=10425.5,
            answer_type="arithmetic",
            table_text=(
                "columns: C0=(in thousands) | C1=2019 | C2=2018\n"
                "R1 [Trade receivables] C0=Trade receivables | C1=9,660 | C2=11,191"
            ),
            unit="thousand",
            program="(9,660+11,191)/2",
            question="What is the average trade receivables for 2019 and 2018?",
        )
        result = score_response(
            response("10,425.5", 10425.5, "thousands", ["TABLE:R1:C1", "TABLE:R1:C2"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "ACCEPT")

    def test_correct_count_typed_reduction_accepts(self) -> None:
        ref = reference(
            answer="3",
            answer_type="count",
            table_text=(
                "columns: C0= | C1=First | C2=Second | C3=Third | C4=Fourth\n"
                "R1 [Basic earnings per share] C0=Basic earnings per share | "
                "C1=$0.35 | C2=$0.36 | C3=$0.08 | C4=$0.31"
            ),
            unit="",
            program="first##second##fourth",
            question="How many quarters did basic earnings per share exceed $0.30?",
        )
        result = score_response(
            response(
                "3",
                3,
                "UNKNOWN",
                ["TABLE:R1:C1", "TABLE:R1:C2", "TABLE:R1:C4"],
            ),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "ACCEPT")

    def test_wrong_unit_rejects(self) -> None:
        ref = reference(
            answer=10,
            answer_type="arithmetic",
            table_text="columns: C0=(in thousands) | C1=V\nR1 [X] C0=X | C1=10",
            unit="thousand",
            program="10",
        )
        result = score_response(
            response("10", 10, "USD", ["TABLE:R1:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["numeric_unit"]["status"], "FAIL")

    def test_wrong_direction_rejects(self) -> None:
        ref = reference(
            answer=-10,
            answer_type="arithmetic",
            table_text="columns: C0=percent | C1=V\nR1 [X] C0=X | C1=-10",
            unit="percent",
            program="-10",
        )
        result = score_response(
            response("-10", 10, "%", ["TABLE:R1:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["numeric_unit"]["status"], "FAIL")

    def test_extra_span_rejects(self) -> None:
        ref = reference(
            answer=["beginning", "additions"],
            answer_type="multi-span",
            table_text=(
                "columns: C0=component | C1=2019\n"
                "R1 [beginning] C0=beginning | C1=1\n"
                "R2 [additions] C0=additions | C1=2\n"
                "R3 [end] C0=end | C1=3"
            ),
        )
        result = score_response(
            response(
                ["beginning", "additions", "end"],
                None,
                "UNKNOWN",
                ["TABLE:R1:C1", "TABLE:R2:C1"],
            ),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["answer"]["status"], "FAIL")

    def test_wrong_period_or_row_rejects(self) -> None:
        ref = reference(
            answer=["100"],
            answer_type="span",
            table_text=(
                "columns: C0=item | C1=2019\n"
                "R1 [wanted] C0=wanted | C1=100\n"
                "R2 [other] C0=other | C1=200"
            ),
            unit="thousand",
        )
        result = score_response(
            response(["100"], 100, "thousands", ["TABLE:R2:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["evidence"]["status"], "FAIL")

    def test_missing_reference_strict_fails(self) -> None:
        ref = reference(
            answer=["100"],
            answer_type="span",
            table_text="columns: C0=item | C1=2019\nR1 [x] C0=x | C1=100",
            unit="thousand",
        )
        result = score_response(
            response(["100"], 100, "thousands", []),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "STRICT_FAIL")

    def test_nonexistent_reference_rejects(self) -> None:
        ref = reference(
            answer=["100"],
            answer_type="span",
            table_text="columns: C0=item | C1=2019\nR1 [x] C0=x | C1=100",
            unit="thousand",
        )
        result = score_response(
            response(["100"], 100, "thousands", ["TABLE:R99:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["evidence"]["reason"], "nonexistent_reference")

    def test_out_of_range_paragraph_reference_rejects(self) -> None:
        paragraphs = [{"order": "1", "text": "visible", "uid": "p1"}]
        ref = reference(
            answer=["visible"],
            answer_type="span",
            paragraphs=paragraphs,
            source_requirement="paragraph",
        )
        result = score_response(
            response(["visible"], None, "UNKNOWN", ["P99"]),
            ref,
            visible(ref, ["1"]),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["evidence"]["reason"], "out_of_range_reference")

    def test_numeric_equal_wrong_role_rejects(self) -> None:
        ref = reference(
            answer=["100"],
            answer_type="span",
            table_text=(
                "columns: C0=item | C1=2019\n"
                "R1 [wanted role] C0=wanted role | C1=100\n"
                "R2 [wrong role] C0=wrong role | C1=100"
            ),
            unit="thousand",
        )
        result = score_response(
            response(["100"], 100, "thousands", ["TABLE:R2:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["evidence"]["status"], "FAIL")

    def test_negative_count_strict_fails(self) -> None:
        ref = reference(answer="3", answer_type="count", unit="")
        result = score_response(
            response("-1", -1, "UNKNOWN", ["TABLE:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "STRICT_FAIL")
        self.assertIn(
            "count_must_be_nonnegative_integer",
            result["layers"]["strict"]["reason"],
        )

    def test_numeric_array_contract_strict_fails(self) -> None:
        ref = reference(answer=["155", "113"], answer_type="multi-span")
        result = score_response(
            response(["155", "113"], [155, 113], "thousands", ["TABLE:R1:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "STRICT_FAIL")
        self.assertIn("invalid_numeric_value_type", result["layers"]["strict"]["reason"])

    def test_reasonable_unknown_when_required_evidence_missing(self) -> None:
        paragraphs = [{"order": "7", "text": "required scale", "uid": "p7"}]
        ref = reference(
            answer=["100"],
            answer_type="span",
            paragraphs=paragraphs,
            source_requirement="paragraph",
            unit="thousand",
        )
        result = score_response(
            response("UNKNOWN", None, "UNKNOWN", [], unknown=True, clarification="not visible"),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REASONABLE_UNKNOWN")

    def test_unknown_count_preserves_unknown_contract(self) -> None:
        paragraphs = [{"order": "7", "text": "required count list", "uid": "p7"}]
        ref = reference(
            answer="3",
            answer_type="count",
            paragraphs=paragraphs,
            source_requirement="paragraph",
        )
        result = score_response(
            response(
                "UNKNOWN",
                None,
                "UNKNOWN",
                [],
                unknown=True,
                clarification="count evidence not visible",
            ),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "REASONABLE_UNKNOWN")
        self.assertNotIn(
            "count_must_be_nonnegative_integer",
            result["layers"]["strict"]["reason"],
        )

    def test_unresolvable_legal_reference_is_pending_not_wrong(self) -> None:
        ref = reference(
            answer=["alpha"],
            answer_type="span",
            table_text="columns: C0=item | C1=2019\nR1 [other] C0=other | C1=beta",
        )
        result = score_response(
            response(["alpha"], None, "UNKNOWN", ["TABLE:C1"]),
            ref,
            visible(ref, []),
        )
        self.assertEqual(result["status"], "PENDING_ADJUDICATION")
        self.assertEqual(result["layers"]["evidence"]["status"], "PENDING_ADJUDICATION")


if __name__ == "__main__":
    unittest.main()
