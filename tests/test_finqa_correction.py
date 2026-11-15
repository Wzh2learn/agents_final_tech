"""Scientific controls for public feedback, native grading and correction weights."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / "research/agent_frontier_portfolio_20261029/finqa_correction.py"
spec = importlib.util.spec_from_file_location("finqa_correction", PATH)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class FinQACorrectionTests(unittest.TestCase):
    def setUp(self):
        self.public = {"id": "synthetic", "report": "fixture", "question": "Compute the sum",
                       "table": [["year", "2020", "2021"], ["revenue", "10", "20"]],
                       "pre_text": [], "post_text": []}

    def test_public_projection_has_no_labels(self):
        raw = {"id": "x", "filename": "report", "pre_text": [], "post_text": [],
               "table": [], "qa": {"question": "q", "program": "gold", "exe_ans": 5,
                                     "gold_inds": {"text_0": "gold evidence"}}}
        result = m.public_record(raw)
        self.assertEqual(set(result), m.PUBLIC_KEYS)
        self.assertNotIn("gold", repr(result))
        with self.assertRaises(ValueError):
            m.check_public({**result, "exe_ans": 5})

    def test_public_feedback_does_not_report_correctness(self):
        program = "add(10, 20), divide(#0, const_10)"
        before = m.execute_public(program, self.public)
        good = m.grade(program, self.public, 3)
        wrong = m.grade(program, self.public, 99)
        self.assertTrue(good["execution_correct"])
        self.assertFalse(wrong["execution_correct"])
        self.assertEqual(before, good["public_execution"])
        self.assertEqual(before, wrong["public_execution"])
        self.assertNotIn("execution_correct", before)

    def test_valid_wrong_and_invalid_are_distinct(self):
        wrong = m.grade("add(10, 20)", self.public, 10)
        invalid = m.grade("divide(1, 0)", self.public, 10)
        self.assertTrue(wrong["program_valid"])
        self.assertFalse(wrong["execution_correct"])
        self.assertFalse(invalid["program_valid"])
        self.assertFalse(invalid["execution_correct"])

    def test_backslides_distinguish_wrong_equivalent_and_invalid_edits(self):
        correct='add(10, 20), divide(#0, 100)'
        rows=m.execution_backslides('add(10, 20), divide(#0, const_100)',correct,self.public,.3)
        self.assertTrue(rows)
        self.assertTrue(all(r['program_valid'] and not r['semantic_negative'] for r in rows))
        rows=m.execution_backslides('add(10, 20), divide(#0, 0)',correct,self.public,.3)
        self.assertTrue(any(not r['program_valid'] for r in rows))
        rows=m.execution_backslides('add(10, 20), divide(#0, const_10)',correct,self.public,.3)
        self.assertTrue(any(r['semantic_negative'] for r in rows))

    def test_backslide_includes_missing_tail_and_rejects_wrong_teacher(self):
        rows=m.execution_backslides('add(10, 20)','add(10, 20), divide(#0, const_10)',self.public,3)
        self.assertTrue(any(r['kind']=='missing_tail' and r['semantic_negative'] for r in rows))
        with self.assertRaises(ValueError):
            m.execution_backslides('add(1, 2)','add(1, 3)',self.public,3)

    def test_reference_result_and_table_operation(self):
        result = m.grade("table_sum(revenue, none), divide(#0, const_10)", self.public, 3)
        self.assertTrue(result["execution_correct"])
        with self.assertRaises(ValueError):
            m.canonical_answer(float("nan"))

    def test_edit_impact_does_not_include_unrelated_step(self):
        region = m.correction_region("add(10, 20), add(5, 5), divide(#0, const_10)",
                                     "subtract(20, 10), add(5, 5), divide(#0, const_10)")
        self.assertEqual(region["changed"], [0])
        self.assertEqual(region["affected"], [0, 2])
        weights = m.normalized_step_weights(region, 3)
        self.assertAlmostEqual(sum(weights), 3)
        self.assertGreater(weights[0], weights[1])
        self.assertEqual(weights[0], weights[2])

    def test_no_edit_and_invalid_source_are_explicit(self):
        region = m.correction_region("add(1, 2)", "add(1, 2)")
        self.assertEqual(m.normalized_step_weights(region, 1), [1])
        region = m.correction_region("not a program", "add(1, 2)")
        self.assertEqual(region["fallback"], "unparseable_student_program")
        self.assertEqual(m.correction_region(None, "add(1, 2)")["fallback"],
                         "unparseable_student_program")

    def test_token_normalization_preserves_mass_and_protocol(self):
        ids = [0, None, 0, 0, 1, None]
        mask = [False, True, True, True, True, True]
        weights = m.normalized_token_weights(ids, {0}, mask)
        self.assertEqual(weights[0], 0)
        self.assertAlmostEqual(sum(weights), 5)
        self.assertGreater(weights[2], weights[4])
        self.assertGreater(weights[1], 0)
        self.assertGreater(weights[-1], 0)
        self.assertEqual(m.normalized_token_weights(ids, {0}, mask, 0),
                         [0, 1, 1, 1, 1, 1])

    def test_real_development_error_has_field_level_contrast(self):
        old = "subtract(604, 2063), divide(604, 2063), multiply(#0, 100)"
        fixed = "subtract(2063, 604), divide(#0, 604)"
        region = m.correction_fields(old, fixed)
        self.assertIn("0:arg1", region["fields"])
        self.assertIn("1:arg1", region["fields"])
        self.assertNotIn("0:op", region["fields"])
        ids = [None, "0:op", "0:arg1", "0:arg2", None]
        weights = m.field_token_weights(ids, region["fields"], [True]*5)
        self.assertEqual(weights[0], 1)
        self.assertEqual(weights[-1], 1)
        self.assertAlmostEqual(sum(weights), 5)
        self.assertGreater(weights[2], weights[1])

    def test_unparseable_feedback_keeps_uniform_recovery(self):
        region = m.correction_fields(None, "add(1, 2)")
        self.assertEqual(region["fields"], [])
        self.assertEqual(m.field_token_weights([None, "0:arg1", None], [], [False, True, True]),
                         [0, 1, 1])

    def test_residual_denominator_edit_is_smaller_than_all_operands(self):
        old = "subtract(344000, 43000), divide(#0, const_m1)"
        fixed = "subtract(344000, 43000), divide(#0, 43000)"
        region = m.correction_fields(old, fixed)
        self.assertEqual(region["fields"], ["1:arg2"])
        ids = [None, "0:op", "0:arg1", "0:arg2", "1:op", "1:arg1", "1:arg2", None]
        keep = [True]*len(ids)
        local = m.field_token_weights(ids, region["fields"], keep)
        operands = {f for f in ids if f and not f.endswith(":op")}
        broad = m.field_token_weights(ids, operands, keep)
        self.assertNotEqual(local, broad)
        self.assertGreater(local[6], local[2])
        self.assertAlmostEqual(sum(local), len(ids))
        self.assertEqual(local[0], broad[0])
        self.assertEqual(local[-1], broad[-1])


class FinQATerminalSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.public = {"id": "fixture", "report": "fixture", "question": "Compute the difference",
                       "table": [["year", "2020", "2021"], ["value", "10", "20"]],
                       "pre_text": [], "post_text": []}

    @staticmethod
    def event(text, message="last", part="text"):
        return {"type": "text", "part": {"type": "text", "messageID": message,
                "id": part, "text": text}}

    def test_declared_change_is_committed_by_actual_public_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);public = root / "public.json";events = root / "actor.jsonl"
            public.write_text(json.dumps(self.public))
            (root / "candidate.json").write_text(json.dumps({"program": "divide(20, 10)"}))
            events.write_text(json.dumps(self.event("Final program: subtract(20, 10)")) + "\n")
            result = subprocess.run([sys.executable, str(PATH), "--final-jsonl", str(events),
                "--public", str(public), "--work", str(root), "--executor", str(m.executor().__file__)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["status"], "submitted")
            self.assertEqual(receipt["execution"]["terminal_execution_answer"], 10)
            self.assertEqual(json.loads((root / "candidate.json").read_text()),
                             {"program": "subtract(20, 10)"})
            trace = json.loads((root / "executions.jsonl").read_text())
            self.assertEqual(trace["origin"], "terminal_declaration")
            self.assertNotIn("execution_correct", json.dumps(receipt))

    def test_only_latest_assistant_text_is_used_and_updated_parts_are_not_duplicated(self):
        events = [self.event("Final program: add(1, 2)", "old"),
                  self.event("The program", "last", "a"),
                  self.event("The program follows.", "last", "a"),
                  self.event("Final program: subtract(20, 10)", "last", "b")]
        self.assertEqual(m.terminal_proposal(events)["program"], "subtract(20, 10)")
        events.append({"type": "tool_use", "part": {"type": "tool", "messageID": "new",
                      "id": "tool", "text": "Final program: multiply(1, 9)"}})
        self.assertEqual(m.terminal_proposal(events)["status"], "absent")

    def test_absent_and_ambiguous_declarations_leave_the_workspace_unchanged(self):
        for text in ["No declaration.", "Final program: add(1, 2)\nFinal program: add(1, 3)"]:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temp:
                root = Path(temp);candidate = root / "candidate.json"
                candidate.write_text('{"program":"divide(20, 10)"}\n');before = candidate.read_bytes()
                result = m.submit_terminal_response([self.event(text)], self.public, root, m.executor())
                self.assertEqual(result["status"], "not_submitted")
                self.assertEqual(candidate.read_bytes(), before)
                self.assertFalse((root / "executions.jsonl").exists())

    def test_unchanged_program_still_has_a_real_execution_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);(root / "candidate.json").write_text('{"program":"subtract(20, 10)"}')
            result = m.submit_terminal_response([self.event("Final program: subtract(20, 10)")],
                                               self.public, root, m.executor())
            self.assertEqual(result["status"], "submitted")
            self.assertFalse(result["changed"])
            self.assertEqual(result["execution"]["terminal_execution_answer"], 10)
            self.assertEqual(json.loads((root / "executions.jsonl").read_text())["origin"],
                             "terminal_declaration")

    def test_execution_failure_is_retained_as_a_real_failed_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = m.submit_terminal_response([self.event("Final program: divide(20, 0)")],
                                               self.public, root, m.executor())
            self.assertEqual(result["status"], "submitted")
            self.assertEqual(result["execution"]["status"], "error")
            self.assertEqual(json.loads((root / "candidate.json").read_text())["program"], "divide(20, 0)")
            self.assertNotIn("execution_correct", json.dumps(result))

    def test_program_text_is_never_executed_as_a_shell_command(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);marker = root / "should_not_exist"
            program = "add(1, 2); touch " + str(marker)
            result = m.submit_terminal_response([self.event("Final program: " + program)],
                                               self.public, root, m.executor())
            self.assertEqual(result["execution"]["status"], "error")
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
