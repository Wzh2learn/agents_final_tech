"""Focused acceptance tests for CONDITION_CHANGE_FEEDBACK_V1."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path
from typing import Any

from condition_change_common import (
    ACTOR_TASKS_PATH,
    FACTS_PATH,
    INPUT_MANIFEST_PATH,
    MACHINE_VERIFICATION_PATH,
    POLICY_PATH,
    PROBE_FIXTURES_PATH,
    PROBE_RESULTS_PATH,
    PROBE_RUN_MANIFEST_PATH,
    REFERENCE_TASKS_PATH,
    SCHEMA_PATH,
    SOURCE_CASES_V2_PATH,
    SOURCE_CASES_PATH,
    SOURCE_POLICY_PATH,
    SUPPORTED_PYTHON_VERSIONS,
    TASK_ID,
    V1_FROZEN_FILES,
    load_json,
    sha256_file,
)
from reference_builder import derive_all_references
from run_feedback_probe import (
    build_probe_result,
    deterministic_baseline,
    feedback_disposition,
    fixed_decimal,
)


def contains_key(payload: Any, key: str) -> bool:
    if isinstance(payload, dict):
        return key in payload or any(contains_key(value, key) for value in payload.values())
    if isinstance(payload, list):
        return any(contains_key(value, key) for value in payload)
    return False


class ConditionChangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_json(INPUT_MANIFEST_PATH)
        cls.policy = load_json(POLICY_PATH)
        cls.facts = load_json(FACTS_PATH)
        cls.actor_payload = load_json(ACTOR_TASKS_PATH)
        cls.actor_tasks = cls.actor_payload["tasks"]
        cls.reference_payload = load_json(REFERENCE_TASKS_PATH)
        cls.references = cls.reference_payload["references"]
        cls.fixture = load_json(PROBE_FIXTURES_PATH)
        cls.result = load_json(PROBE_RESULTS_PATH)

    def test_frozen_hashes_and_exact_runtime(self) -> None:
        self.assertEqual(self.manifest["task_id"], TASK_ID)
        self.assertEqual(self.manifest["python"]["implementation"], "CPython")
        self.assertIn(
            ".".join(self.manifest["python"]["version"].split(".")[:2]),
            SUPPORTED_PYTHON_VERSIONS,
        )
        for entry in self.manifest["canonical_input_files"]:
            path = Path(entry["path"])
            self.assertTrue(path.exists(), path)
            self.assertEqual(sha256_file(path), entry["sha256"])
        for path in V1_FROZEN_FILES:
            self.assertEqual(
                sha256_file(path), self.manifest["v1_frozen_hashes"][path.name]
            )

    def test_actor_input_is_separate_from_reference_data(self) -> None:
        self.assertTrue(self.actor_payload["actor_input_only"])
        for actor_task in self.actor_tasks:
            self.assertTrue(actor_task["actor_input_only"])
            self.assertNotIn("decision", actor_task)
            self.assertNotIn("minimal_sufficient_sets", actor_task)
            self.assertNotIn("canonical_sufficient_set", actor_task)
            self.assertNotIn("reference_facts", actor_task)
            self.assertNotIn("adjudication", actor_task)
            self.assertIn("policy_context", actor_task)
            context = actor_task["policy_context"]
            self.assertEqual(
                context["policy_version_id"], actor_task["policy_version_id"]
            )
            self.assertTrue(context["applicable_policy_text"])
            self.assertTrue(context["explicit_policy_delta_text"])
        self.assertFalse(contains_key(self.actor_tasks, "gold"))
        self.assertFalse(contains_key(self.actor_tasks, "reference"))
        self.assertFalse(contains_key(self.facts, "decision"))
        self.assertFalse(contains_key(self.facts, "minimal_sufficient_sets"))

    def test_counts_and_condition_change_opportunities(self) -> None:
        counts = self.result["reference_counts"]
        self.assertEqual(counts["paired_cases"], 13)
        self.assertEqual(counts["actor_tasks"], 26)
        self.assertGreaterEqual(counts["source_clusters"], 4)
        self.assertGreaterEqual(counts["decision_flips"], 3)
        self.assertGreaterEqual(counts["invariant_pairs"], 3)
        self.assertGreaterEqual(counts["reference_tasks_with_alternative_sets"], 2)
        self.assertGreaterEqual(counts["distinct_out_of_scope_fact_ids"], 2)
        self.assertGreaterEqual(
            counts["invariant_decision_minimal_set_change_pairs"], 1
        )
        self.assertEqual(
            counts["decision_flips"] + counts["invariant_pairs"],
            counts["paired_cases"],
        )

    def test_strict_task_and_tool_schema(self) -> None:
        schema = load_json(SCHEMA_PATH)
        self.assertEqual(schema["$id"], "condition_change_task_tool_schema_v2")
        self.assertFalse(schema["additionalProperties"])
        for definition in (
            "actor_task",
            "evidence_fact",
            "feedback_result",
            "reference_task",
            "submission_tool",
        ):
            self.assertFalse(schema["$defs"][definition]["additionalProperties"])
        tool = schema["$defs"]["submission_tool"]
        tool_properties = tool["properties"]
        self.assertEqual(
            tool_properties["name"]["const"],
            "submit_reimbursement_decision",
        )
        self.assertFalse(
            tool_properties["input_schema"]["properties"][
                "additionalProperties"
            ]["const"]
        )
        self.assertEqual(
            set(
                tool_properties["input_schema"]["properties"]["required"]
            ),
            {"task_id", "outcome", "evidence_ids"},
        )
        feedback = schema["$defs"]["feedback_result"]
        self.assertIn("reason_codes", feedback["required"])
        self.assertIn("contract_reason_code", feedback["required"])
        self.assertNotIn("reason_code", feedback["properties"])

    def test_reference_builder_rederives_without_actor_tasks(self) -> None:
        recomputed = derive_all_references(POLICY_PATH, FACTS_PATH)
        self.assertEqual(recomputed, self.reference_payload)
        for reference in recomputed["references"]:
            self.assertEqual(
                reference["derivation"]["gold_source"],
                "declarative_policy_and_evidence_facts",
            )
            self.assertGreaterEqual(len(reference["minimal_sufficient_sets"]), 1)
            self.assertIn(
                reference["canonical_sufficient_set"],
                reference["minimal_sufficient_sets"],
            )

    def test_contract_probe_separates_alternate_and_extra(self) -> None:
        dispositions = self.result["contract_probe"]["dispositions_by_case"]
        self.assertEqual(
            dispositions["VALID_ALTERNATE_SET"],
            {
                "exact_match": "REVISE",
                "sufficiency_only": "RETAIN",
                "composite": "RETAIN",
            },
        )
        self.assertEqual(
            dispositions["OUT_OF_SCOPE_ADDITION"],
            {
                "exact_match": "REVISE",
                "sufficiency_only": "RETAIN",
                "composite": "REVISE",
            },
        )
        self.assertEqual(
            dispositions["OUT_OF_SCOPE_COUNTERFACTUAL"],
            {
                "exact_match": "RETAIN",
                "sufficiency_only": "RETAIN",
                "composite": "RETAIN",
            },
        )
        rows = {
            row["probe_case_id"]: row
            for row in self.result["contract_probe"]["rows"]
        }
        self.assertEqual(
            rows["OUT_OF_SCOPE_ADDITION"]["contracts"]["composite"][
                "contract_reason_code"
            ],
            "SCOPE_PRECISION_FAILED",
        )
        self.assertEqual(
            rows["OUT_OF_SCOPE_ADDITION"]["contracts"]["composite"][
                "reason_codes"
            ],
            ["SCOPE_IMURITY"],
        )
        self.assertEqual(
            rows["OUT_OF_SCOPE_ADDITION"]["contracts"]["sufficiency_only"][
                "contract_reason_code"
            ],
            "SUFFICIENT_SET_RETAINED",
        )
        self.assertEqual(
            rows["OUT_OF_SCOPE_COUNTERFACTUAL"]["contracts"]["composite"][
                "reason_codes"
            ],
            [],
        )

    def test_scope_fixture_is_single_factor_with_clean_counterfactual(
        self,
    ) -> None:
        probes = {
            probe_case["probe_case_id"]: probe_case
            for probe_case in self.fixture["probe_cases"]
        }
        extra = probes["OUT_OF_SCOPE_ADDITION"]
        clean = probes["OUT_OF_SCOPE_COUNTERFACTUAL"]
        self.assertEqual(clean["counterfactual_for"], extra["probe_case_id"])
        self.assertEqual(clean["source_task_id"], extra["source_task_id"])
        self.assertEqual(
            clean["submitted_outcome"], extra["submitted_outcome"]
        )
        removed = set(extra["selected_evidence_ids"]) - set(
            clean["selected_evidence_ids"]
        )
        self.assertFalse(
            set(clean["selected_evidence_ids"])
            - set(extra["selected_evidence_ids"])
        )
        self.assertEqual(len(removed), 1)
        reference = next(
            reference
            for reference in self.references
            if reference["task_id"] == extra["source_task_id"]
        )
        self.assertTrue(removed.issubset(reference["out_of_scope_evidence_ids"]))
        for probe_case in (extra, clean):
            self.assertEqual(
                probe_case["submitted_outcome"], reference["decision"]["outcome"]
            )
            self.assertTrue(
                any(
                    set(minimal_set).issubset(probe_case["selected_evidence_ids"])
                    for minimal_set in reference["minimal_sufficient_sets"]
                )
            )

    def test_appended_invariant_pair_changes_minimal_set(self) -> None:
        references_by_stage = {
            reference["stage"]: reference
            for reference in self.references
            if reference["case_id"] == "CC013"
        }
        self.assertEqual(set(references_by_stage), {"pre", "post"})
        pre = references_by_stage["pre"]
        post = references_by_stage["post"]
        self.assertEqual(pre["decision"]["outcome"], post["decision"]["outcome"])
        self.assertNotEqual(
            pre["minimal_sufficient_sets"], post["minimal_sufficient_sets"]
        )
        self.assertEqual(pre["derivation"]["builder"], "reference_builder_v2")
        self.assertEqual(post["derivation"]["builder"], "reference_builder_v2")

    def test_stable_package_provenance_and_launcher_manifest_boundary(
        self,
    ) -> None:
        self.assertEqual(self.manifest["task_id"], "condition_change_feedback_v1")
        self.assertEqual(self.result["task_id"], "condition_change_feedback_v1")
        run_manifest = load_json(PROBE_RUN_MANIFEST_PATH)
        self.assertEqual(
            set(run_manifest["launcher_ids"]),
            {"implementation", "fix"},
        )
        for payload in (
            self.manifest,
            self.result,
            load_json(PROBE_FIXTURES_PATH),
            load_json(MACHINE_VERIFICATION_PATH)
            if MACHINE_VERIFICATION_PATH.exists()
            else {},
        ):
            self.assertNotIn("launcher_ids", payload)

    def test_alternative_sets_are_naturally_derived(self) -> None:
        alternatives = [
            reference
            for reference in self.references
            if len(reference["minimal_sufficient_sets"]) > 1
        ]
        self.assertGreaterEqual(len(alternatives), 2)
        self.assertTrue(
            any(
                any(len(minimal_set) > 1 for minimal_set in reference["minimal_sufficient_sets"])
                for reference in alternatives
            )
        )

    def test_diagnostic_reason_codes_are_independent(self) -> None:
        reference = {
            "canonical_sufficient_set": ["case:fact_1"],
            "decision": {"outcome": "approve"},
            "in_scope_evidence_ids": ["case:fact_1", "case:fact_2"],
            "minimal_sufficient_sets": [["case:fact_1"]],
            "out_of_scope_evidence_ids": ["case:note"],
        }
        cases = [
            (["case:fact_1"], "reject", ["ANSWER_MISMATCH"]),
            (["case:fact_2"], "approve", ["INSUFFICIENT_PLAN"]),
            (["case:fact_1", "case:note"], "approve", ["SCOPE_IMURITY"]),
            (
                ["case:fact_1", "case:fact_2"],
                "approve",
                ["IN_SCOPE_OVER_SELECTION"],
            ),
        ]
        for selected_ids, outcome, expected_codes in cases:
            with self.subTest(expected_codes=expected_codes):
                result = feedback_disposition(
                    "composite", selected_ids, outcome, reference
                )
                self.assertEqual(result["reason_codes"], expected_codes)
        self.assertNotIn("reason_code", result)
        self.assertIn("contract_reason_code", result)

    def test_baseline_is_deterministic_and_non_terminal(self) -> None:
        actor_by_id = {task["task_id"]: task for task in self.actor_tasks}
        rows_by_id = {
            row["task_id"]: row for row in self.result["baseline"]["rows"]
        }
        for task_id, row in rows_by_id.items():
            self.assertEqual(
                deterministic_baseline(actor_by_id[task_id])[
                    "selected_evidence_ids"
                ],
                row["actor_input_only"]["selected_evidence_ids"],
            )
        for stage_metrics in self.result["baseline"]["by_stage"].values():
            for metric in (
                "plan_sufficient_rate",
                "plan_precision_mean",
                "answer_coverage_rate",
                "composite_acceptance_rate",
            ):
                raw_value = stage_metrics[metric]
                value = (
                    float(raw_value)
                    if metric == "plan_precision_mean"
                    else raw_value
                )
                self.assertGreater(value, 0.0, metric)
                self.assertLess(value, 1.0, metric)
            precision_mean = stage_metrics["plan_precision_mean"]
            self.assertIsInstance(precision_mean, str)
            self.assertEqual(len(precision_mean.partition(".")[2]), 12)
            reconstructed = Fraction(
                stage_metrics["plan_precision_numerator"],
                stage_metrics["plan_precision_denominator"],
            )
            self.assertEqual(precision_mean, fixed_decimal(reconstructed))
        self.assertTrue(self.result["headroom"]["deterministic_nonzero_headroom"])
        self.assertEqual(
            self.result["headroom"]["stop_recommendation"],
            "STOP_BEFORE_REAL_MODEL",
        )
        self.assertFalse(self.result["headroom"]["real_model_phase_authorized"])

    def test_probe_result_is_reproducible(self) -> None:
        self.assertEqual(build_probe_result(), self.result)
        run_manifest = load_json(PROBE_RUN_MANIFEST_PATH)
        self.assertEqual(run_manifest["status"], "MATCH")
        self.assertEqual(
            run_manifest["frozen_result_sha256"],
            run_manifest["recomputed_result_sha256"],
        )

    def test_zero_request_accounting_everywhere(self) -> None:
        accounting_surfaces = [
            self.manifest["request_accounting"],
            self.result["request_accounting"],
            load_json(PROBE_RUN_MANIFEST_PATH)["request_accounting"],
        ]
        for accounting in accounting_surfaces:
            self.assertGreaterEqual(len(accounting), 5)
            self.assertEqual(set(accounting.values()), {0})

    def test_source_inputs_have_no_per_case_gold_answers(self) -> None:
        source_policy = load_json(SOURCE_POLICY_PATH)
        source_cases = load_json(SOURCE_CASES_PATH)
        self.assertTrue(source_policy["policy_versions"])
        self.assertEqual(
            source_policy["decision_semantics"],
            "first_match_in_declared_order",
        )
        self.assertIn("receipt", source_policy["in_scope_fact_kinds"])
        self.assertEqual(len(source_cases["cases"]), 12)
        self.assertFalse(contains_key(source_cases, "gold"))
        self.assertFalse(contains_key(source_cases, "minimal_sufficient_sets"))
        self.assertFalse(contains_key(source_cases, "canonical_sufficient_set"))
        self.assertFalse(contains_key(source_cases, "reference_decision"))
        source_cases_v2 = load_json(SOURCE_CASES_V2_PATH)
        self.assertEqual(len(source_cases_v2["cases"]), 13)
        self.assertEqual(
            source_cases_v2["cases"][: len(source_cases["cases"])],
            source_cases["cases"],
        )
        self.assertFalse(contains_key(source_cases_v2, "gold"))
        self.assertFalse(
            contains_key(source_cases_v2, "minimal_sufficient_sets")
        )


if __name__ == "__main__":
    unittest.main()
