from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from same_candidate_feedback_a_v1 import (
    binding_relation,
    enrich_row,
    execution_feedback,
    localizer_assessment,
    revision_prompt,
)
from run_oracle_localization_diagnostic_a_v3 import diagnostic_feedback


INSTANCE = {
    "prompt": (
        "Return one JSON object.\n\n"
        "Table:\n"
        "columns: C0= | C1=At December 31, | C2=\n"
        "R1 [] C0= | C1=2019 | C2=2018\n"
        "R2 [Cash] C0=Cash | C1=$437 | C2=$268\n\n"
        "Question: What was the change in cash between 2018 and 2019?"
    ),
    "table_text": (
        "columns: C0= | C1=At December 31, | C2=\n"
        "R1 [] C0= | C1=2019 | C2=2018\n"
        "R2 [Cash] C0=Cash | C1=$437 | C2=$268"
    ),
    "expected": {
        "answer": 169.0,
        "evidence_refs": ["R2:C1", "R2:C2"],
        "program": {
            "left": {"ref": "R2:C1"},
            "op": "sub",
            "right": {"ref": "R2:C2"},
        },
        "unit": "million",
    },
}


class SameCandidateFeedbackTests(unittest.TestCase):
    def test_feedback_prompts_do_not_include_hidden_target(self) -> None:
        previous = '{"evidence_refs":["R2:C1","R2:C2"],"program":{"left":{"ref":"R2:C1"},"op":"sub","right":{"ref":"R2:C2"}},"unit":"thousand"}'
        for condition in ("execution_feedback", "localization_feedback"):
            prompt = revision_prompt(INSTANCE, previous, condition)
            self.assertNotIn('"answer":169', prompt)
            self.assertNotIn("reference answer", prompt.lower().replace("does not contain a reference answer", ""))
            self.assertIn("Previous candidate", prompt)

    def test_neutral_revision_and_deterministic_control_are_distinct(self) -> None:
        previous = '{"evidence_refs":["R2:C1","R2:C2"],"program":{},"unit":"million"}'
        neutral = revision_prompt(INSTANCE, previous, "ordinary_retry")
        deterministic = revision_prompt(INSTANCE, previous, "deterministic_rerun_control")
        self.assertIn("Previous candidate", neutral)
        self.assertIn("at most one revision", neutral)
        self.assertGreater(
            neutral.index("at most one revision"),
            neutral.index("Previous candidate"),
        )
        self.assertEqual(deterministic, INSTANCE["prompt"])

    def test_execution_feedback_restores_multiline_period(self) -> None:
        previous = '{"evidence_refs":["R2:C1","R2:C2"],"program":{"left":{"ref":"R2:C1"},"op":"sub","right":{"ref":"R2:C2"}},"unit":"million"}'
        feedback = execution_feedback(INSTANCE, previous)
        self.assertIn('"period_labels": ["2019"]', feedback)
        self.assertIn('"period_labels": ["2018"]', feedback)
        self.assertIn("Executed value", feedback)

    def test_binding_relation_separates_exact_and_alternate(self) -> None:
        exact = '{"evidence_refs":["R2:C1","R2:C2"],"program":{},"unit":"million"}'
        alternate = '{"evidence_refs":["R2:C1","R2:C2","R3:C1"],"program":{},"unit":"million"}'
        self.assertTrue(binding_relation(exact, INSTANCE["expected"])["exact"])
        self.assertEqual(
            binding_relation(alternate, INSTANCE["expected"])["relation"],
            "EXPECTED_REFS_INCLUDED_WITH_EXTRAS",
        )

    def test_localizer_false_alarm_and_sufficiency_are_separate(self) -> None:
        discrepancy = {
            "categories": ["numeric_mismatch", "program_structure_mismatch"],
        }
        false_alarm = localizer_assessment(
            ["question_period_not_visible_in_program"],
            discrepancy,
            initial_correct=False,
        )
        sufficient = localizer_assessment(
            ["structural_average_denominator_misbound"],
            discrepancy,
            initial_correct=False,
        )
        self.assertTrue(false_alarm["feedback_error"])
        self.assertTrue(false_alarm["feedback_insufficient"])
        self.assertFalse(sufficient["feedback_error"])
        self.assertFalse(sufficient["feedback_insufficient"])

    def test_oracle_diagnostic_omits_answer_and_correct_program(self) -> None:
        feedback = diagnostic_feedback(
            INSTANCE,
            '{"evidence_refs":["R2:C1"],"program":{"ref":"R2:C1"},"unit":"million"}',
            initial_correct=False,
        )
        self.assertIn("oracle-assisted", feedback)
        self.assertNotIn("169", feedback)
        self.assertNotIn("R2:C2", feedback)
        self.assertIn("discrepancy classes", feedback)

    def test_feedback_assessment_uses_initial_candidate_not_revision(self) -> None:
        previous = '{"evidence_refs":["R2:C1"],"program":{"ref":"R2:C1"},"unit":"million"}'
        revised = '{"evidence_refs":["R2:C1","R2:C2"],"program":{"left":{"ref":"R2:C1"},"op":"sub","right":{"ref":"R2:C2"}},"unit":"million"}'
        row = enrich_row(
            {
                "generated_text": revised,
                "previous_candidate": previous,
                "program_correct": True,
                "interface_valid": True,
                "program_executable": True,
            },
            INSTANCE,
            "localization_feedback",
        )
        self.assertFalse(row["initial_correct"])
        self.assertTrue(row["feedback_assessment"]["feedback_insufficient"] or row["feedback_assessment"]["supported_categories"])
        self.assertIn("reference_set_mismatch", row["posthoc_discrepancies_initial"]["categories"])


if __name__ == "__main__":
    unittest.main()
