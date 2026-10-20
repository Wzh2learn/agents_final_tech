#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from collection_chain import consume_answer, execute_tool, independent_reference, run_offline_episode, validate_plan
from exposure_classifier import (
    EXPOSURE_UNKNOWN,
    METHOD_DEVELOPMENT_OR_DIAGNOSTIC,
    MODEL_OR_FEEDBACK_EXPOSURE,
    PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW,
    STRUCTURAL_SCAN_ONLY,
    classify_cluster,
    classify_uid,
)
from offline_core import normalize_text, parse_numeric, task_eligibility
from prepare_collection_gate import (
    apply_wp2_designation_boundary,
    parse_program_exposure_review_text,
    review_category_counts,
    write_json,
)
from raw_capture import AtomicRawStore, BudgetLedger
from source_cluster_builder import association_reasons, build_clusters


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "fixtures" / "synthetic_offline_cases.json").read_text(encoding="utf-8"))


class OfflineTests(unittest.TestCase):
    def test_split_proposal_excludes_reviewed_unqualified_future_cluster(self) -> None:
        split = json.loads((ROOT / "SPLIT_PROPOSAL.json").read_text(encoding="utf-8"))
        future_ids = [row["cluster_id"] for row in split["future_test"]]
        self.assertEqual(future_ids, [
            "cluster_1340",
            "cluster_0306",
            "cluster_0615",
            "cluster_0978",
            "cluster_1724",
            "cluster_1628",
            "cluster_2060",
            "cluster_1642",
        ])
        self.assertEqual(
            [row["cluster_id"] for row in split["development"]],
            ["cluster_2010", "cluster_2096"],
        )
        self.assertNotIn("cluster_0599", future_ids)
        self.assertNotIn("cluster_2314", future_ids)
        self.assertTrue(all(
            row["program_exposure_review"]["category"] ==
            "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE"
            for row in split["future_test"]
        ))
        self.assertTrue(all(
            row["effective_exposure_category"] ==
            row["program_exposure_review"]["category"]
            for row in split["future_test"] + split["development"] +
            split["reserve"] + split["excluded_pending_review"]
        ))
        self.assertEqual(split["checks"]["clean_pending_clusters"], 141)
        self.assertEqual(split["checks"]["excluded_pending_review_clusters"], 24)
        self.assertEqual(len(split["revision"]["wp2_designated_cluster_ids"]), 19)
        self.assertEqual(split["revision"]["wp2_category_reclassified_count"], 17)
        self.assertEqual(
            split["revision"]["superseded_revision_2_development_ids"],
            ["cluster_1642", "cluster_2010"],
        )

    def test_json_writer_is_byte_reproducible_with_lf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.json"
            write_json(path, {"value": 1})
            payload = path.read_bytes()
            self.assertNotIn(b"\r\n", payload)
            self.assertEqual(json.loads(payload.decode("utf-8")), {"value": 1})

    def test_program_exposure_review_contract_and_count_error_path(self) -> None:
        review = parse_program_exposure_review_text(
            (ROOT / "LOOP_C_PROGRAM_EXPOSURE_REVIEW.md").read_text(encoding="utf-8")
        )
        counts = {}
        for row in review.values():
            counts[row["category"]] = counts.get(row["category"], 0) + 1
        self.assertEqual(counts, {
            "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE": 158,
            "EXPOSURE_UNKNOWN": 2,
            "MODEL_OR_FEEDBACK_EXPOSURE": 5,
        })
        adjusted = apply_wp2_designation_boundary(review)
        self.assertEqual(review_category_counts(adjusted), {
            "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE": 141,
            "EXPOSURE_UNKNOWN": 19,
            "METHOD_DEVELOPMENT_OR_DIAGNOSTIC": 0,
            "MODEL_OR_FEEDBACK_EXPOSURE": 5,
        })
        too_short = (
            "cluster_id=cluster_0001 | group=reserve | cluster_contract_tasks=2 | "
            "uid=00000000-0000-0000-0000-000000000001 | uid_contract_tasks=2 | "
            "category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=test\n"
        )
        with self.assertRaises(ValueError):
            parse_program_exposure_review_text(too_short)

    def test_normalization_preserves_signs_decimals_and_punctuation(self) -> None:
        self.assertEqual(normalize_text(" -1.25 (3.50) "), "-1.25 (3.50)")
        self.assertEqual(parse_numeric("−1.25"), -1.25)
        self.assertEqual(parse_numeric("–1.25"), -1.25)
        self.assertEqual(parse_numeric("—1.25"), -1.25)
        self.assertEqual(parse_numeric("(−1.25)"), -1.25)
        self.assertEqual(parse_numeric("(-1.25)"), -1.25)
        self.assertEqual(parse_numeric("(1.25)"), -1.25)
        self.assertIsNone(parse_numeric("(—)"))

    def test_full_cluster_graph_keeps_multiple_reasons(self) -> None:
        graph = build_clusters(FIXTURES["records"])
        by_members = {
            tuple(sorted((edge["left"], edge["right"]))): edge
            for edge in graph["edges"]
        }
        exact_table = by_members[("exact-table-a", "exact-table-b")]
        self.assertIn("exact_table", {reason["kind"] for reason in exact_table["reasons"]})
        conflict = by_members[("table-conflict-a", "table-conflict-b")]
        self.assertTrue(any(
            reason["kind"] == "table_reuse_paragraph_divergence"
            for reason in conflict["reasons"]
        ))
        paragraph_reuse = by_members[("paragraph-reuse-a", "paragraph-reuse-b")]
        self.assertTrue(any(
            reason["kind"] == "paragraph_reuse_table_divergence"
            for reason in paragraph_reuse["reasons"]
        ))

    def test_association_requires_reason(self) -> None:
        left, right = FIXTURES["records"][0], FIXTURES["records"][-1]
        self.assertEqual(
            association_reasons(
                left,
                right,
                ({"aaaaa"}, {"ccccc"}),
                ({"bbbbb"}, {"ddddd"}),
                ("left-table", "left-paragraphs", None),
                ("right-table", "right-paragraphs", None),
            ),
            [],
        )

    def test_exposure_precedence_uses_strongest_evidence(self) -> None:
        evidence = {
            "structural": {"u1", "u2", "u3", "u4"},
            "generated": {"u1", "u2", "u3"},
            "diagnostic": {"u1", "u2"},
            "model": {"u1"},
        }
        self.assertEqual(classify_uid("u1", evidence)[0], MODEL_OR_FEEDBACK_EXPOSURE)
        self.assertEqual(classify_uid("u2", evidence)[0], METHOD_DEVELOPMENT_OR_DIAGNOSTIC)
        self.assertEqual(classify_uid("u3", evidence)[0], PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW)
        self.assertEqual(classify_uid("u4", evidence)[0], STRUCTURAL_SCAN_ONLY)
        self.assertEqual(classify_uid("u5", evidence)[0], EXPOSURE_UNKNOWN)
        cluster = classify_cluster(["u1", "u4"], evidence)
        self.assertEqual(cluster["category"], MODEL_OR_FEEDBACK_EXPOSURE)
        self.assertEqual(cluster["future_test_state"], "EXCLUDE")

    def test_task_eligibility_requires_two_periods_and_units(self) -> None:
        record = FIXTURES["records"][0]
        result = task_eligibility(record)
        self.assertTrue(result["eligible"])
        self.assertEqual(len(result["usable_rows"]), 1)
        bad = {"table": {"uid": "bad", "table": [["x"], ["1"]]}, "paragraphs": []}
        self.assertFalse(task_eligibility(bad)["eligible"])

    def test_tool_uses_actor_parameters_without_gold_correction(self) -> None:
        task = next(item for item in FIXTURES["tasks"] if item["task_id"] == "fixture-valid")
        plan = validate_plan(task, task["plan"])
        tool = execute_tool(plan)
        self.assertEqual(tool["params"]["expression"], "10.5 - 8.25")
        self.assertEqual(tool["returned_value"], 2.25)
        consumption = consume_answer(task, tool, task["answer"])
        self.assertEqual(consumption["status"], "ANSWER_CONSUMES_TOOL_RESULT")
        wrong = dict(task["answer"], delta_target=999)
        self.assertEqual(consume_answer(task, tool, wrong)["status"], "ANSWER_TOOL_MISMATCH")

    def test_invalid_tool_plans_preserve_tool_error(self) -> None:
        task = next(item for item in FIXTURES["tasks"] if item["task_id"] == "fixture-valid")
        for expression in ("1/0", "1 +", "2**3"):
            result = run_offline_episode(
                task,
                {"tool": "calc", "params": {"expression": expression}},
                task["answer"],
            )
            self.assertEqual(result["tool_result"]["status"], "TOOL_ERROR")
            self.assertEqual(result["tool_result"]["error"], "INVALID_PLAN")

    def test_reference_checker_handles_units_and_unscorable(self) -> None:
        valid = next(item for item in FIXTURES["tasks"] if item["task_id"] == "fixture-unit-conversion")
        reference = independent_reference(valid)
        self.assertEqual(reference["status"], "REFERENCE_RECOMPUTED")
        self.assertAlmostEqual(reference["delta_target"], -0.00475)
        unscorable = next(item for item in FIXTURES["tasks"] if item["task_id"] == "fixture-unscorable")
        self.assertEqual(independent_reference(unscorable)["status"], "REFERENCE_UNSCORABLE")

    def test_raw_capture_is_unique_atomic_and_overwrite_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AtomicRawStore(Path(tmp))
            request_id = store.begin_request("fixture")
            store.persist_response(request_id, {"value": 1})
            with self.assertRaises(FileExistsError):
                store.persist_response(request_id, {"value": 2})
            self.assertTrue((Path(tmp) / request_id / "COMPLETE").exists())
            with self.assertRaises(RuntimeError):
                store.mark_crash(request_id, "late crash")
            second = store.begin_request("fixture")
            store.mark_crash(second, "synthetic crash")
            self.assertTrue((Path(tmp) / second / "CRASH").exists())
            with self.assertRaises(RuntimeError):
                store.persist_response(second, {"value": 3})

    def test_budget_stops_at_request_and_token_caps(self) -> None:
        request_budget = BudgetLedger(request_cap=1, token_cap=100)
        request_budget.reserve(1)
        with self.assertRaises(RuntimeError):
            request_budget.reserve(1)
        self.assertEqual(request_budget.snapshot()["stop_reason"], "REQUEST_CAP_REACHED")
        token_budget = BudgetLedger(request_cap=2, token_cap=10)
        with self.assertRaises(RuntimeError):
            token_budget.reserve(11)
        self.assertEqual(token_budget.snapshot()["stop_reason"], "TOKEN_CAP_REACHED")
        invalid_budget = BudgetLedger(request_cap=2, token_cap=10)
        for invalid in (-5, 0, 1.5, True):
            with self.assertRaises(ValueError):
                invalid_budget.reserve(invalid)

    def test_offline_episode_records_zero_model_calls(self) -> None:
        task = next(item for item in FIXTURES["tasks"] if item["task_id"] == "fixture-valid")
        result = run_offline_episode(task, task["plan"], task["answer"])
        self.assertEqual(result["model_calls"], 0)
        self.assertFalse(result["scientific_result"])
        self.assertEqual(result["consumption"]["status"], "ANSWER_CONSUMES_TOOL_RESULT")


if __name__ == "__main__":
    unittest.main()
