from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "finqa_executor_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("finqa_executor_contract_v1", MODULE_PATH)
assert SPEC and SPEC.loader
EXECUTOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EXECUTOR
SPEC.loader.exec_module(EXECUTOR)


class ExecutorContractTests(unittest.TestCase):
    def test_official_arithmetic_and_terminal_rounding(self) -> None:
        result = EXECUTOR.execute_program(
            "add(1.234567, 2), divide(#0, 3)", [["ignored", "1"]]
        )
        self.assertEqual(result.step_values, (3.234567, 1.078189))
        self.assertEqual(result.terminal_execution_answer, 1.07819)

    def test_percent_and_constant_arguments(self) -> None:
        result = EXECUTOR.execute_program(
            "divide(50%, const_2), multiply(#0, const_m1)", [["ignored", "1"]]
        )
        self.assertEqual(result.step_values, (0.25, -0.25))

    def test_table_none_second_argument_is_officially_ignored(self) -> None:
        result = EXECUTOR.execute_program(
            "table_sum(Foo, none)", [["Foo", "$1", "$2"], ["Bar", "$9"]]
        )
        self.assertEqual(result.step_values, (3.0,))

    def test_greater_tie_is_no(self) -> None:
        result = EXECUTOR.execute_program("greater(2, 2)", [["ignored", "1"]])
        self.assertEqual(result.terminal_execution_answer, "no")

    def test_division_by_zero_fails_closed(self) -> None:
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.execute_program("divide(1, 0)", [["ignored", "1"]])
        self.assertEqual(caught.exception.code, "DIVISION_BY_ZERO")

    def test_unsupported_operator_fails_closed(self) -> None:
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.execute_program("average(1, 2)", [["ignored", "1"]])
        self.assertEqual(caught.exception.code, "UNSUPPORTED_OPERATOR")

    def test_unresolved_forward_reference_fails_closed(self) -> None:
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.execute_program("add(#1, 2)", [["ignored", "1"]])
        self.assertEqual(caught.exception.code, "ARGUMENT_REFERENCE_UNRESOLVED")

    def test_none_is_rejected_for_arithmetic(self) -> None:
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.execute_program("add(none, 2)", [["ignored", "1"]])
        self.assertEqual(caught.exception.code, "ARGUMENT_NON_NUMERIC")

    def test_table_dependency_fails_closed(self) -> None:
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.execute_program(
                "add(1, 2), table_sum(#0, none)", [["Foo", "$1"]]
            )
        self.assertEqual(caught.exception.code, "TABLE_REFERENCE_UNSUPPORTED")

    def test_legal_p_mutation_changes_only_operator_and_propagates(self) -> None:
        steps = EXECUTOR.parse_program("add(1, 2), multiply(#0, 3)")
        program, mutated, receipt = EXECUTOR.apply_mutation(
            steps, family="P", step_index=0, field="op", value="subtract"
        )
        self.assertEqual(receipt["changed_fields"], ["op"])
        execution = EXECUTOR.execute_program(program, [["ignored", "1"]])
        self.assertEqual(execution.terminal_execution_answer, -3.0)

    def test_legal_n_mutation_changes_only_argument_and_propagates(self) -> None:
        steps = EXECUTOR.parse_program("add(1, 2), multiply(#0, 3)")
        program, mutated, receipt = EXECUTOR.apply_mutation(
            steps, family="N", step_index=0, field="arg1", value="4"
        )
        self.assertEqual(receipt["changed_fields"], ["arg1"])
        execution = EXECUTOR.execute_program(program, [["ignored", "1"]])
        self.assertEqual(execution.terminal_execution_answer, 18.0)

    def test_manual_result_and_answer_edits_are_rejected(self) -> None:
        for field in ("res", "answer", "exe_ans", "terminal_execution_answer"):
            with self.subTest(field=field):
                with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
                    EXECUTOR.apply_manual_result_edit({"field": field, "value": "manual"})
                self.assertEqual(caught.exception.code, "MUTATION_RESULT_FIELD_FORBIDDEN")

    def test_direct_mutation_api_rejects_result_field(self) -> None:
        steps = EXECUTOR.parse_program("add(1, 2)")
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.apply_mutation(
                steps, family="P", step_index=0, field="res", value="manual"
            )
        self.assertEqual(caught.exception.code, "MUTATION_FIELD_ILLEGAL")

    def test_table_arg2_mutation_is_rejected_as_ignored(self) -> None:
        steps = EXECUTOR.parse_program("table_sum(Foo, none)")
        with self.assertRaises(EXECUTOR.ExecutorContractError) as caught:
            EXECUTOR.apply_mutation(
                steps, family="N", step_index=0, field="arg2", value="2"
            )
        self.assertEqual(caught.exception.code, "MUTATION_TARGET_TABLE_ARG2_IGNORED")

    def test_canonical_serialization_is_byte_stable(self) -> None:
        left = EXECUTOR.canonical_json_bytes({"b": 2, "a": [1, 3]})
        right = EXECUTOR.canonical_json_bytes({"a": [1, 3], "b": 2})
        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
