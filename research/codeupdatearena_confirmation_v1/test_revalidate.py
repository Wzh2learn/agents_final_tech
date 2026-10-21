import json
import unittest

from research.codeupdatearena_adapter_v2.run_adapter import (
    RESULT_MARKER,
    FrozenTask,
    build_test_program_v2,
    classify_execution_v2,
    validate_candidate_code,
    validate_execution_markers_v2,
)


class RevalidationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = FrozenTask(
            index=0,
            row={
                "prog_syn_id": "task-0",
                "update_id": "update-0",
                "imports": "import math",
                "unit_tests": "def test_ok():\n    assert math.comb(2, 1) == 2\n",
                "update": {
                    "api_path": "math.comb",
                    "implementation": "def comb(n, k=1):\n    return n\n",
                },
            },
        )

    def test_candidate_cannot_print_or_forge_marker(self) -> None:
        code = f"def f():\n    print({RESULT_MARKER!r} + '{{}}')\n"
        self.assertFalse(validate_candidate_code(code)["allowed"])

    def test_candidate_cannot_exit_before_tests(self) -> None:
        for code in (
            "import os\nos._exit(0)\n",
            "raise SystemExit(0)\n",
            "import sys\nsys.exit(0)\n",
            "def f():\n    E = SystemExit\n    raise E(0)\n",
            "def f():\n    import pprint\n    pprint.pprint('fake')\n",
            "def f():\n    setattr(globals(), 'x', 1)\n",
        ):
            self.assertFalse(validate_candidate_code(code)["allowed"], code)

    def test_redundant_top_level_old_alias_is_dropped(self) -> None:
        code = (
            "import math\n"
            "old_comb = math.comb\n"
            "setattr(math, 'old_comb', old_comb)\n"
            "def f(n):\n    return math.comb(n, 1)\n"
        )
        validated = validate_candidate_code(code)
        self.assertTrue(validated["allowed"])
        self.assertNotIn("old_comb", validated["prepared_code"])
        self.assertNotIn("setattr", validated["prepared_code"])

    def test_trusted_marker_requires_nonce_and_identity(self) -> None:
        program = build_test_program_v2(
            self.task,
            "def f():\n    return 1\n",
            {"name": "test_ok", "source": "def test_ok():\n    assert True\n"},
            "candidate",
            "nonce-123",
        )
        self.assertIn("nonce-123", program)
        expected = [
            {"stage": "test_start", "nonce": "nonce-123", "role": "candidate",
             "prog_syn_id": "task-0", "test_name": "test_ok"},
            {"stage": "test_pass", "nonce": "nonce-123", "role": "candidate",
             "prog_syn_id": "task-0", "test_name": "test_ok"},
            {"stage": "all_tests_complete", "nonce": "nonce-123", "role": "candidate",
             "prog_syn_id": "task-0", "test_name": "test_ok"},
        ]
        valid, _ = validate_execution_markers_v2(
            expected,
            self.task,
            {"name": "test_ok", "source": "def test_ok():\n    assert True\n"},
            "candidate",
            "nonce-123",
        )
        self.assertTrue(valid)
        tampered = [dict(item) for item in expected]
        tampered[0]["nonce"] = "forged"
        valid, error = validate_execution_markers_v2(
            tampered,
            self.task,
            {"name": "test_ok", "source": "def test_ok():\n    assert True\n"},
            "candidate",
            "nonce-123",
        )
        self.assertFalse(valid)
        self.assertEqual(error, "marker_sequence_mismatch")

    def test_assertion_failure_is_test_failure(self) -> None:
        start = {
            "stage": "test_start",
            "nonce": "n",
            "role": "candidate",
            "prog_syn_id": "task-0",
            "test_name": "test_ok",
        }
        self.assertEqual(
            classify_execution_v2([start], False, 1, False),
            ("test_failure", "test_failure"),
        )
        self.assertEqual(
            classify_execution_v2([start], False, 0, False),
            ("marker_violation", "marker_violation"),
        )


if __name__ == "__main__":
    unittest.main()
