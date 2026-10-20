"""Regression tests for the frozen DEV_ONLY mechanism probes."""

from __future__ import annotations

import unittest

from active_evidence_probe import evaluate_strategy
from feedback_contract_probe import feedback_accepts, scope_truth
from probe_common import (
    RESULT_DIR,
    load_frozen_probe_inputs,
    read_json,
    verify_freeze_receipt,
)


class ProbeRegressionTests(unittest.TestCase):
    """Check the contracts most likely to fail silently."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load hash-verified frozen fixtures and completed results."""
        verify_freeze_receipt()
        cls.inputs, cls.feedback = load_frozen_probe_inputs()
        cls.tasks = {task["task_id"]: task for task in cls.inputs["tasks"]}
        cls.active_result = read_json(
            RESULT_DIR / "active_evidence_probe_results.json"
        )
        cls.feedback_result = read_json(
            RESULT_DIR / "feedback_contract_probe_results.json"
        )

    def test_frozen_scope(self) -> None:
        """The probe remains a 13-task, DEV_ONLY deterministic simulation."""
        self.assertEqual(len(self.tasks), 13)
        self.assertEqual(self.active_result["resource_accounting"]["model_requests"], 0)
        self.assertEqual(self.feedback_result["resource_accounting"]["model_requests"], 0)

    def test_esd_010_sufficient_subset(self) -> None:
        """ESD_010 cand_003 alone is sufficient despite optional cand_007."""
        task = self.tasks["ESD_010"]
        self.assertEqual(
            task["reference"]["minimal_sufficient_sets"],
            [["cand_003"]],
        )
        oracle = evaluate_strategy(task, "oracle", budget=1)
        self.assertEqual(oracle["lookup_ids"], ["cand_003"])
        self.assertTrue(oracle["sufficient_set_discovered"])

    def test_feedback_contract_separates_failure_modes(self) -> None:
        """Exact-match and set/coverage feedback fail in opposite directions."""
        cases = {case["case_id"]: case for case in self.feedback["cases"]}
        alternative = cases["valid_alternative_with_redundant_support"]
        unsupported = cases["unsupported_extra_with_complete_facts"]
        alternative_reference = self.tasks[alternative["task_id"]]["reference"]
        unsupported_reference = self.tasks[unsupported["task_id"]]["reference"]

        self.assertTrue(scope_truth(alternative["selection"], alternative_reference))
        self.assertFalse(
            feedback_accepts(
                "exact_match", alternative["selection"], alternative_reference
            )
        )
        self.assertTrue(
            feedback_accepts(
                "minimal_sufficient_set",
                alternative["selection"],
                alternative_reference,
            )
        )

        self.assertFalse(scope_truth(unsupported["selection"], unsupported_reference))
        self.assertTrue(
            feedback_accepts(
                "minimal_sufficient_set",
                unsupported["selection"],
                unsupported_reference,
            )
        )
        self.assertTrue(
            feedback_accepts(
                "fact_coverage",
                unsupported["selection"],
                unsupported_reference,
            )
        )

    def test_active_result_has_all_contracts(self) -> None:
        """All required strategies and lookup budgets are present."""
        aggregate = {
            (row["budget"], row["strategy"])
            for row in self.active_result["aggregate"]
        }
        for budget in (1, 2, 3):
            for strategy in (
                "direct",
                "fixed",
                "random",
                "lexical",
                "score_disagreement",
                "oracle",
            ):
                self.assertIn((budget, strategy), aggregate)


if __name__ == "__main__":
    unittest.main()
