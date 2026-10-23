"""Contract tests for G2 responsibility-separated evaluation."""

from __future__ import annotations

import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
CATEGORIES = {
    "GROUNDED_TASK_COMPLETION",
    "STALE_OR_UNSAFE_ADVICE",
    "REASONABLE_UNKNOWN_OR_CLARIFICATION",
    "UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE",
    "INTERFACE_FORMAT_FAILURE",
}


def load_json(name: str) -> dict[str, Any]:
    """Load one V5 JSON contract artifact."""
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    """Compute a file SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_variants(path: Path) -> set[str]:
    """Return raw and LF-normalized hashes for cross-platform source binding."""
    raw = path.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(lf).hexdigest(),
        hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest(),
    }


class G2EvaluationContractTests(unittest.TestCase):
    """Assert the measurement object, not a particular model or judge."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.review = load_json("G2_COUNTEREXAMPLE_REVIEW.json")
        cls.calibration = load_json("G2_CALIBRATION_CASES.json")
        cls.contract = (HERE / "G2_EVALUATION_CONTRACT.md").read_text(encoding="utf-8")

    def test_contract_defines_all_five_categories_and_separate_responsibilities(self) -> None:
        for category in CATEGORIES:
            self.assertIn(category, self.contract)
        self.assertIn("Historical Fact Responsibility", self.contract)
        self.assertIn("Action Responsibility", self.contract)
        self.assertIn("Multiple actions or paraphrases are allowed", self.contract)

    def test_review_identity_is_ai_advisory_not_human_reference(self) -> None:
        self.assertEqual(
            self.review["reviewer_identity"],
            "AI_ADVISORY_REVIEW_NOT_HUMAN_REFERENCE",
        )
        self.assertTrue(any("human" in note.lower() for note in self.review["nonclaims"]))

    def test_source_hashes_bind_to_existing_v4_files(self) -> None:
        for source in self.review["source_refs"].values():
            path = PROJECT_ROOT / source["path"]
            self.assertTrue(path.is_file(), source["path"])
            self.assertIn(source["sha256"], sha256_variants(path), source["path"])

    def test_three_uid_reviews_preserve_hidden_reference_and_raw_answers(self) -> None:
        expected_uids = {
            "0f806fbb-d8e6-4791-bcbf-2230e70877cc",
            "0af76ce2-d242-4deb-bd5c-a853338150bc",
            "17c4192e-ee5a-442a-b492-f69641d836c3",
        }
        self.assertEqual({case["uid"] for case in self.review["cases"]}, expected_uids)
        for case in self.review["cases"]:
            self.assertEqual(
                set(case["hidden_reference"]),
                {"M_old", "M_new", "explanation"},
            )
            self.assertEqual(len(case["responses"]), 2)
            evidence = case["selected_evidence"]
            self.assertEqual(len(evidence["selected_indices"]), 5)
            self.assertIn(
                evidence["retrieval_category"],
                {"BOTH_OLD_AND_NEW", "OLD_ONLY", "NEW_ONLY", "MISS"},
            )
            for response in case["responses"]:
                self.assertIn("raw_answer", response)
                self.assertEqual(
                    set(response["v4_judge"]),
                    {
                        "action_state_aligned",
                        "stale_action_rejected",
                        "evidence_consistent",
                        "non_generic",
                        "safe_unknown",
                        "pass",
                        "error_type",
                    },
                )
                self.assertIn("validated_action_pass", response["v4_gate"])
                self.assertIn(response["ai_review"]["primary_category"], CATEGORIES)

    def test_raw_judge_hashes_match_each_counterexample(self) -> None:
        for case in self.review["cases"]:
            evidence = case["selected_evidence"]
            request = PROJECT_ROOT / evidence["raw_judge_request_path"]
            response = PROJECT_ROOT / evidence["raw_judge_response_path"]
            self.assertEqual(sha256(request), evidence["raw_judge_request_sha256"])
            self.assertEqual(sha256(response), evidence["raw_judge_response_sha256"])

    def test_counterexample_categories_include_success_safety_and_interface(self) -> None:
        categories = [
            response["ai_review"]["primary_category"]
            for case in self.review["cases"]
            for response in case["responses"]
        ]
        counts = Counter(categories)
        self.assertEqual(counts["GROUNDED_TASK_COMPLETION"], 2)
        self.assertEqual(counts["STALE_OR_UNSAFE_ADVICE"], 2)
        self.assertEqual(counts["INTERFACE_FORMAT_FAILURE"], 2)
        expected_nonzero = Counter({
            key: value
            for key, value in self.review["summary"]["new_primary_category_counts"].items()
            if value
        })
        self.assertEqual(counts, expected_nonzero)

    def test_v4_false_accept_false_reject_and_inconsistency_are_reported(self) -> None:
        dispositions = [
            response["ai_review"]["v4_judge_disposition"]
            for case in self.review["cases"]
            for response in case["responses"]
        ]
        gate_dispositions = [
            response["ai_review"]["v4_gate_disposition"]
            for case in self.review["cases"]
            for response in case["responses"]
        ]
        self.assertEqual(Counter(dispositions), Counter(
            self.review["summary"]["v4_judge_disposition_counts"]
        ))
        self.assertEqual(Counter(gate_dispositions), Counter(
            self.review["summary"]["v4_gate_disposition_counts"]
        ))
        inconsistent = [
            response
            for case in self.review["cases"]
            for response in case["responses"]
            if response["ai_review"]["inconsistencies"]
        ]
        self.assertEqual(
            len(inconsistent),
            self.review["summary"]["inconsistent_nonempty_rows"],
        )
        self.assertGreaterEqual(len(inconsistent), 3)

    def test_judge_and_gate_disagree_without_being_collapsed(self) -> None:
        rows = [
            response
            for case in self.review["cases"]
            for response in case["responses"]
        ]
        judge_false_accepts = {
            row["ai_review"]["v4_judge_disposition"] == "FALSE_ACCEPT" for row in rows
        }
        gate_false_accepts = {
            row["ai_review"]["v4_gate_disposition"] == "FALSE_ACCEPT" for row in rows
        }
        self.assertIn(True, judge_false_accepts)
        self.assertIn(True, gate_false_accepts)
        self.assertNotEqual(
            Counter(row["ai_review"]["v4_judge_disposition"] for row in rows),
            Counter(row["ai_review"]["v4_gate_disposition"] for row in rows),
        )

    def test_calibration_covers_every_required_mechanism_control(self) -> None:
        required = {
            "fixed_No",
            "fixed_UNKNOWN",
            "empty",
            "cautious_generic",
            "old_fact",
            "new_fact",
            "correct_paraphrase",
            "unsupported_detail",
            "fact_correct_action_wrong",
            "unnecessary_refusal",
        }
        cases = {case["case_id"]: case for case in self.calibration["cases"]}
        self.assertTrue(required.issubset(cases))
        self.assertEqual(set(self.calibration["categories"]), CATEGORIES)

    def test_calibration_distinguishes_fact_and_action_failures(self) -> None:
        cases = {case["case_id"]: case for case in self.calibration["cases"]}
        self.assertEqual(
            cases["old_fact"]["expected_primary_category"],
            "STALE_OR_UNSAFE_ADVICE",
        )
        self.assertEqual(
            cases["new_fact"]["expected_primary_category"],
            "GROUNDED_TASK_COMPLETION",
        )
        self.assertEqual(
            cases["correct_paraphrase"]["expected_primary_category"],
            "GROUNDED_TASK_COMPLETION",
        )
        self.assertEqual(
            cases["unsupported_detail"]["expected_flags"]["unsupported_detail_status"],
            "CONSEQUENTIAL_INVENTION",
        )
        self.assertEqual(
            cases["fact_correct_action_wrong"]["expected_flags"]["historical_fact_status"],
            "SUPPORTED",
        )
        self.assertFalse(
            cases["fact_correct_action_wrong"]["expected_flags"]["action_constraints_respected"]
        )

    def test_calibration_accepts_multiple_action_wordings(self) -> None:
        generic = next(
            case for case in self.calibration["cases"]
            if case["case_id"] == "cautious_generic"
        )
        self.assertGreaterEqual(len(generic["acceptable_alternatives"]), 2)
        self.assertTrue(generic["acceptable_alternatives"])
        self.assertEqual(
            generic["expected_primary_category"],
            "GROUNDED_TASK_COMPLETION",
        )

    def test_calibration_separates_unknown_refusal_and_interface_failures(self) -> None:
        cases = {case["case_id"]: case for case in self.calibration["cases"]}
        self.assertEqual(
            cases["fixed_UNKNOWN"]["expected_primary_category"],
            "REASONABLE_UNKNOWN_OR_CLARIFICATION",
        )
        self.assertTrue(cases["fixed_UNKNOWN"]["expected_flags"]["reasonable_abstention"])
        self.assertEqual(
            cases["unnecessary_refusal"]["expected_primary_category"],
            "UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE",
        )
        self.assertTrue(cases["unnecessary_refusal"]["expected_flags"]["unnecessary_refusal"])
        for case_id in ("fixed_No", "empty"):
            self.assertEqual(
                cases[case_id]["expected_primary_category"],
                "INTERFACE_FORMAT_FAILURE",
            )

    def test_calibration_is_not_registered_as_research_data(self) -> None:
        self.assertEqual(
            self.calibration["evidence_identity"],
            "SYNTHETIC_MECHANISM_CONTROLS_NOT_RESEARCH_SAMPLES",
        )
        self.assertTrue(any("not stale benchmark" in note.lower() for note in self.calibration["nonclaims"]))


if __name__ == "__main__":
    unittest.main()
