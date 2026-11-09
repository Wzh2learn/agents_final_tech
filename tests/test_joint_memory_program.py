"""Boundary and attribution checks for the joint-program development contract."""
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

PATH = (Path(__file__).resolve().parents[1] / "research" /
        "agent_frontier_portfolio_20261029" / "joint_memory_program.py")
SPEC = importlib.util.spec_from_file_location("joint_memory_program_test_module", PATH)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


class JointProgramTests(unittest.TestCase):
    def record(self, **changes):
        values = dict(context_sha256="a" * 64, source_group="development/source1",
                      program=m.Program(("public witness",), ()), success=True,
                      reader_tokens=200, query_steps=2, budget_feasible=True,
                      receipt_sha256="b" * 64, formation_receipt_sha256="f" * 64)
        values.update(changes)
        # The constructor also rejects malformed supplied metadata.
        m.Execution(**values)
        value = dict(schema="joint_memory_execution_v1", status="EVALUATED",
                     context_sha256=values["context_sha256"],
                     source_group=values["source_group"],
                     program=json.loads(m.program_json(values["program"])),
                     outcome=values["success"],
                     costs=dict(reader_tokens=values["reader_tokens"],
                                query_steps=values["query_steps"]),
                     budget_feasible=values["budget_feasible"],
                     formation_receipt_sha256=values["formation_receipt_sha256"])
        raw = json.dumps(value).encode()
        return m.execution_from_receipt(raw, hashlib.sha256(raw).hexdigest(),
                                       context_sha256=values["context_sha256"],
                                       program=values["program"], allowed_queries=[])

    def other_record(self, **changes):
        return self.record(program=m.Program(("different public witness",), ()), **changes)

    def test_model_text_is_data_not_executable_queries(self):
        for raw in [
            '{"memory": [], "queries": ["../../gold.patch"]}',
            '{"memory": [], "queries": ["bash rm -rf /"]}',
            '{"memory": [], "queries": [], "command": "run"}',
            '{"memory": [], "memory": ["override"], "queries": []}',
            'prose {"memory": [], "queries": []}',
            '{"memory": [], "queries": []} trailing',
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                m.parse_program(raw, ["read_public_test"])

    def test_empty_memory_and_query_program_are_real_controls(self):
        self.assertEqual(m.parse_program('{"memory": [], "queries": []}', []),
                         m.Program((), ()))

    def test_budgets_and_exact_records(self):
        for raw in ['{"memory":["same","same"],"queries":[]}',
                    '{"memory":[""],"queries":[]}',
                    '{"memory":["long"],"queries":[]}',
                    '{"memory":[],"queries":["q","q"]}']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                m.parse_program(raw, ["q"], max_memory_chars=3, max_queries=1)

    def test_deletion_is_not_a_verified_recovery_label(self):
        p = m.Program(("past action", "old location"), ())
        self.assertEqual(m.delete_record(p, 1, ("search",), allowed_queries=["search"]),
                         m.Program(("past action",), ("search",)))
        with self.assertRaises(ValueError):
            m.delete_record(p, True, (), allowed_queries=[])
        with self.assertRaises(ValueError):
            m.delete_record(p, 1, ("private_gold",), allowed_queries=["search"])

    def test_unknown_or_infeasible_is_not_a_training_negative(self):
        for changes in [dict(success=None), dict(reader_tokens=None),
                        dict(query_steps=None), dict(budget_feasible=False)]:
            with self.subTest(changes=changes):
                self.assertIsNone(m.execution_preference(self.record(),
                                                        self.other_record(**changes)))

    def test_cost_tradeoff_and_tie_do_not_become_cherry_picked_preferences(self):
        self.assertIsNone(m.execution_preference(self.record(), self.other_record()))
        self.assertIsNone(m.execution_preference(
            self.record(reader_tokens=100, query_steps=3), self.other_record()))
        self.assertEqual(m.execution_preference(
            self.record(reader_tokens=100, query_steps=1), self.other_record()), 1)

    def test_failed_continuations_do_not_supply_efficiency_success(self):
        self.assertIsNone(m.execution_preference(self.record(success=False),
                                                self.other_record(success=False)))
        self.assertEqual(m.execution_preference(self.record(),
                                                self.other_record(success=False)), 1)

    def test_cannot_pair_different_reader_or_query_conditions(self):
        for changes in [dict(context_sha256="c" * 64), dict(source_group="other")]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                m.execution_preference(self.record(), self.other_record(**changes))

    def test_missing_or_invalid_provenance_is_rejected(self):
        for changes in [dict(receipt_sha256=""), dict(success=1),
                        dict(reader_tokens=True), dict(query_steps=-1),
                        dict(source_group=1)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.record(**changes)

    def test_same_receipt_and_same_program_cannot_supply_preferences(self):
        with self.assertRaises(ValueError):
            m.execution_preference(self.record(), self.record())
        self.assertIsNone(m.execution_preference(self.record(),
                                                self.record(reader_tokens=100)))

    def test_receipt_tampering_and_faults_remain_unknown(self):
        rec = self.record()
        value = dict(schema="joint_memory_execution_v1", status="INTERFACE_ERROR",
                     context_sha256=rec.context_sha256, source_group=rec.source_group,
                     program=json.loads(m.program_json(rec.program)), outcome=False,
                     costs=dict(reader_tokens=20, query_steps=1), budget_feasible=True,
                     formation_receipt_sha256=rec.formation_receipt_sha256)
        raw = json.dumps(value).encode()
        args = dict(context_sha256=rec.context_sha256, program=rec.program, allowed_queries=[])
        unknown = m.execution_from_receipt(raw, hashlib.sha256(raw).hexdigest(), **args)
        self.assertIsNone(unknown.success)
        self.assertIsNone(m.execution_preference(unknown, self.other_record()))
        with self.assertRaises(ValueError):
            m.execution_from_receipt(raw + b" ", hashlib.sha256(raw).hexdigest(), **args)
        with self.assertRaises(ValueError):
            m.execution_from_receipt(raw, hashlib.sha256(raw).hexdigest(),
                                    **dict(args, context_sha256="d" * 64))

    def test_scalar_reference_loss_and_stability(self):
        equal = m.pair_loss(0.0, 0.0)
        self.assertAlmostEqual(equal, math.log(2))
        self.assertLess(m.pair_loss(1.0, -1.0), equal)
        self.assertGreater(m.pair_loss(-1.0, 1.0), equal)
        self.assertTrue(math.isfinite(m.pair_loss(-1e6, 1e6)))
        # A shared additive baseline cancels; a distinct program likelihood does not.
        self.assertAlmostEqual(m.pair_loss(2.0, 1.0), m.pair_loss(102.0, 101.0))


if __name__ == "__main__":
    unittest.main()
