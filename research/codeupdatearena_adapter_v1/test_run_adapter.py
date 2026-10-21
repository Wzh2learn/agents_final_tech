"""Focused contract tests for the bounded CodeUpdateArena adapter."""

from __future__ import annotations

import json
import unittest

from research.codeupdatearena_adapter_v1 import run_adapter


class AdapterContractTests(unittest.TestCase):
    """Verify frozen inputs, prompt boundaries, and execution assembly."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = run_adapter.load_frozen_tasks()

    def test_exact_frozen_families(self) -> None:
        self.assertEqual(len(self.tasks), 8)
        self.assertEqual(
            [task.row["update"]["update_type"] for task in self.tasks],
            [
                "add-argument",
                "add-argument-data_type",
                "add-argument-default_value(s)",
                "add-argument-semantics",
                "add-argument-supported_value(s)",
                "add-function",
                "add-output-data_type",
                "add-output-semantics",
            ],
        )

    def test_prompt_arm_allowlists(self) -> None:
        for task in self.tasks:
            for arm in run_adapter.SPEC["arms"]:
                fields = run_adapter.public_task_fields(task, arm)
                expected = (
                    run_adapter.PUBLIC_BASE_KEYS
                    if arm == "base"
                    else run_adapter.PUBLIC_BASE_KEYS
                    | run_adapter.PUBLIC_UPDATE_KEYS
                )
                self.assertEqual(set(fields), expected)
                prompt = run_adapter.build_prompt(task, arm)
                run_adapter.assert_prompt_not_leaking(task, arm, prompt)

    def test_prompt_does_not_contain_hidden_exact_content(self) -> None:
        for task in self.tasks:
            for arm in run_adapter.SPEC["arms"]:
                prompt = run_adapter.build_prompt(task, arm)
                for key in ("ref_solution", "unit_tests"):
                    self.assertNotIn(str(task.row[key]), prompt)
                self.assertNotIn(
                    str(task.row["update"]["implementation"]),
                    prompt,
                )
                self.assertNotIn(
                    run_adapter.build_enforcement_statement(task),
                    prompt,
                )

    def test_hidden_tests_are_extractable(self) -> None:
        for task in self.tasks:
            tests = run_adapter.extract_hidden_tests(task)
            self.assertGreater(len(tests), 0)
            self.assertEqual(
                len({test["name"] for test in tests}),
                len(tests),
            )

    def test_assembly_order_and_marker(self) -> None:
        task = self.tasks[0]
        test = run_adapter.extract_hidden_tests(task)[0]
        program = run_adapter.build_test_program(
            task,
            str(task.row["ref_solution"]),
            test,
            "reference_solution",
        )
        ordered = [
            "# Trusted import block",
            "# Trusted update implementation",
            "# Trusted update enforcement",
            "# Candidate solution",
            "# Hidden unit test",
            f"{test['name']}()",
            run_adapter.RESULT_MARKER,
        ]
        positions = [program.index(value) for value in ordered]
        self.assertEqual(positions, sorted(positions))

    def test_update_enforcement_matches_frozen_types(self) -> None:
        expected = {
            "itertools.compress = compress",
            "itertools.chain = chain",
            "math.comb = comb",
            "math.sin = sin",
            "itertools.product = product",
            "setattr(math, 'multicomb', multicomb)",
        }
        actual = {
            run_adapter.build_enforcement_statement(task)
            for task in self.tasks
        }
        self.assertEqual(actual, expected)

    def test_generation_envelope_contract(self) -> None:
        body = {
            "model": run_adapter.SPEC["model"]["model"],
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"code": "def f():\n    return 1\n"})
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": 3,
                "total_tokens": 5,
            },
        }
        code, usage = run_adapter.parse_generation_envelope(body)
        self.assertIn("def f", code)
        self.assertEqual(usage["total_tokens"], 5)
        body["choices"][0]["message"]["content"] = json.dumps(
            {"code": "def f():\n    return 1\n", "extra": True}
        )
        with self.assertRaisesRegex(ValueError, "response_envelope_keys"):
            run_adapter.parse_generation_envelope(body)


if __name__ == "__main__":
    unittest.main()
