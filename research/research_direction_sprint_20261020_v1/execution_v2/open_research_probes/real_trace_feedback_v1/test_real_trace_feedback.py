"""Contract tests for the post-hoc real-trace feedback analysis."""

from __future__ import annotations

import unittest

from real_trace_feedback import (
    RESULT_PATH,
    contract_accepts,
    read_json,
    verify_freeze,
)


class RealTraceFeedbackTests(unittest.TestCase):
    """Test the scientific boundaries most likely to be misreported."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load hash-verified fixture and completed result."""
        verify_freeze()
        cls.fixture = read_json(
            cls.fixture_path()
        )
        cls.result = read_json(RESULT_PATH)
        cls.traces = {
            trace["task_id"]: trace for trace in cls.fixture["traces"]
        }

    @staticmethod
    def fixture_path():
        """Return the frozen fixture path without duplicating constants."""
        from real_trace_feedback import FIXTURE_PATH

        return FIXTURE_PATH

    def test_real_trace_scope_and_zero_new_requests(self) -> None:
        """The analysis observes 14 requests but starts none."""
        self.assertEqual(len(self.traces), 7)
        self.assertEqual(self.result["non_success_count"], 6)
        self.assertEqual(
            self.result["resource_accounting"]["real_requests_observed"], 14
        )
        self.assertEqual(
            self.result["resource_accounting"]["new_model_requests"], 0
        )
        self.assertFalse(
            self.result["resource_accounting"]["shared_ledger_modified"]
        )

    def test_esd_010_exact_false_negative(self) -> None:
        """Optional redundant support is valid but not exact minimal-set match."""
        trace = self.traces["ESD_010"]
        self.assertFalse(contract_accepts("exact_match", trace))
        self.assertTrue(
            contract_accepts(
                "set_valued_sufficiency_scope_precision", trace
            )
        )
        self.assertTrue(contract_accepts("composite_trace", trace))

    def test_esd_006_reference_sensitivity(self) -> None:
        """C2 reduces answer scope without rewriting the V1 fixture."""
        trace = self.traces["ESD_006"]
        self.assertFalse(contract_accepts("composite_trace", trace))
        self.assertTrue(
            contract_accepts("composite_trace_c2_sensitivity", trace)
        )

    def test_esd_002_rejects_unsupported_selection(self) -> None:
        """The unsupported current selection is rejected, not repaired by label."""
        trace = self.traces["ESD_002"]
        for contract in (
            "exact_match",
            "minimal_sufficient_set",
            "fact_coverage",
            "set_valued_sufficiency_scope_precision",
            "composite_trace",
            "composite_trace_c2_sensitivity",
        ):
            self.assertFalse(contract_accepts(contract, trace))

    def test_non_success_composite_actions(self) -> None:
        """The final sensitivity action distinguishes revise/reject/repair."""
        actions = {
            row["task_id"]: row
            for row in self.result[
                "non_success_actions_under_composite_c2_sensitivity"
            ]
        }
        self.assertEqual(actions["ESD_001"]["status"], "REVISE")
        self.assertEqual(actions["ESD_002"]["status"], "REJECT")
        self.assertEqual(actions["ESD_003"]["status"], "REVISE")
        self.assertEqual(actions["ESD_004"]["status"], "REVISE")
        self.assertEqual(actions["ESD_006"]["status"], "RETAIN")
        self.assertEqual(
            actions["ESD_006"]["qualification"],
            "RETAIN_AFTER_REFERENCE_REVISION",
        )
        self.assertEqual(
            actions["ESD_006"]["revision_target"],
            "REFERENCE_SCOPE_V1_TO_C2_SENSITIVITY",
        )
        self.assertEqual(actions["ESD_012"]["status"], "REVISE")


if __name__ == "__main__":
    unittest.main()
