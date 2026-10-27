from __future__ import annotations

import json
import unittest

from research.adaptive_mechanism_20261027_v1.scoring_v2.scorer import (
    load_visible_context,
)
from research.word_scoring_new_family_20261027_v1.scoring_v3.scorer import (
    score_response,
)


def reference(
    *,
    answer: object,
    answer_type: str = "span",
    table_text: str = "",
    unit: str = "",
    question: str = "Synthetic Scoring V3 control",
    required_evidence: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "answer": answer,
        "answer_type": answer_type,
        "table_text": table_text,
        "paragraphs": [],
        "source_requirement": "table",
        "unit": unit,
        "program": "",
        "question": question,
    }
    if required_evidence is not None:
        payload["required_evidence"] = required_evidence
    return payload


def visible(ref: dict[str, object]) -> object:
    return load_visible_context({"paragraphs": []}, ref, [])


def response(
    answer: object,
    numeric_value: object,
    refs: list[str],
    *,
    unit: str = "",
) -> str:
    return json.dumps(
        {
            "answer": answer,
            "numeric_value": numeric_value,
            "unit": unit,
            "evidence_refs": refs,
            "unknown": False,
            "clarification": "",
        },
        ensure_ascii=False,
    )


class ScoringV3Controls(unittest.TestCase):
    def test_equal_values_correct_role_only_reference_accepts(self) -> None:
        ref = reference(
            answer=["100"],
            table_text=(
                "columns: C0=item | C1=value\n"
                "R1 [wanted role] C0=wanted role | C1=100\n"
                "R2 [wrong role] C0=wrong role | C1=100"
            ),
            required_evidence=[
                {
                    "operand_id": "answer",
                    "citation": "TABLE:R1",
                    "role": "wanted role",
                    "binding_source": "question_phrase+row_label+independent_review",
                }
            ],
        )
        result = score_response(
            response(["100"], 100, ["TABLE:R1"], unit="UNKNOWN"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "ACCEPT")
        self.assertEqual(result["layers"]["evidence"]["support"]["answer"], "exact")

    def test_equal_values_wrong_role_only_reference_rejects(self) -> None:
        ref = reference(
            answer=["100"],
            table_text=(
                "columns: C0=item | C1=value\n"
                "R1 [wanted role] C0=wanted role | C1=100\n"
                "R2 [wrong role] C0=wrong role | C1=100"
            ),
            required_evidence=[
                {
                    "operand_id": "answer",
                    "citation": "TABLE:R1",
                    "role": "wanted role",
                    "binding_source": "question_phrase+row_label+independent_review",
                }
            ],
        )
        result = score_response(
            response(["100"], 100, ["TABLE:R2"], unit="UNKNOWN"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["evidence"]["reason"], "required_evidence_operand_mismatch")

    def test_indistinguishable_role_reference_is_pending(self) -> None:
        ref = reference(
            answer=["100"],
            table_text=(
                "columns: C0=item | C1=value\n"
                "R1 [role one] C0=role one | C1=100\n"
                "R2 [role two] C0=role two | C1=100"
            ),
        )
        result = score_response(
            response(["100"], 100, ["TABLE:R1"], unit="UNKNOWN"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "PENDING_ADJUDICATION")
        self.assertEqual(
            result["layers"]["evidence"]["reason"],
            "role_reference_cannot_distinguish_rows",
        )

    def test_exact_plus_exact_required_evidence_passes(self) -> None:
        ref = reference(
            answer="10",
            answer_type="arithmetic",
            table_text="columns: C0=item | C1=2019 | C2=2018\nR1 [x] C0=x | C1=6 | C2=4",
            unit="thousand",
            required_evidence=[
                {"operand_id": "left", "citation": "TABLE:R1:C1"},
                {"operand_id": "right", "citation": "TABLE:R1:C2"},
            ],
        )
        result = score_response(
            response("10", 10, ["TABLE:R1:C1", "TABLE:R1:C2"], unit="thousands"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "ACCEPT")
        self.assertEqual(
            result["layers"]["evidence"]["support"],
            {"left": "exact", "right": "exact"},
        )

    def test_exact_plus_broad_required_evidence_is_pending(self) -> None:
        ref = reference(
            answer="10",
            answer_type="arithmetic",
            table_text="columns: C0=item | C1=2019 | C2=2018\nR1 [x] C0=x | C1=6 | C2=4",
            unit="thousand",
            required_evidence=[
                {"operand_id": "left", "citation": "TABLE:R1:C1"},
                {"operand_id": "right", "citation": "TABLE:R1:C2"},
            ],
        )
        result = score_response(
            response("10", 10, ["TABLE:R1:C1", "TABLE:C2"], unit="thousands"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "PENDING_ADJUDICATION")
        self.assertEqual(
            result["layers"]["evidence"]["reason"],
            "broad_evidence_not_role_bound",
        )
        self.assertEqual(
            result["layers"]["evidence"]["support"],
            {"left": "exact", "right": "broad"},
        )

    def test_single_element_numeric_span_legal_positive_accepts(self) -> None:
        ref = reference(
            answer=["123"],
            table_text="columns: C0=item | C1=2019\nR1 [x] C0=x | C1=123",
        )
        result = score_response(
            response(["123"], 123, ["TABLE:R1:C1"], unit="UNKNOWN"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "ACCEPT")
        self.assertEqual(
            result["layers"]["numeric_unit"]["numeric"]["expected_source"],
            "one_element_answer_list",
        )

    def test_single_element_numeric_span_contradiction_rejects(self) -> None:
        ref = reference(
            answer=["123"],
            table_text="columns: C0=item | C1=2019\nR1 [x] C0=x | C1=123",
        )
        result = score_response(
            response(["123"], -999999, ["TABLE:R1:C1"], unit="UNKNOWN"),
            ref,
            visible(ref),
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["layers"]["numeric_unit"]["status"], "FAIL")
        self.assertEqual(result["layers"]["numeric_unit"]["numeric"]["observed"], -999999)


if __name__ == "__main__":
    unittest.main()
