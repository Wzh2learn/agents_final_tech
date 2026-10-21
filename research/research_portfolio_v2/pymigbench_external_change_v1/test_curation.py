"""Focused contract tests for safe parsing and patch evaluation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from curate_pymigbench import (
    condition_contract,
    condition_facts,
    facts_prose,
    is_test_path,
    safe_load_yaml,
    select_test_paths,
)
from patch_protocol import (
    PatchProtocolError,
    apply_patch,
    evaluate_patch,
    validate_patch_paths,
)


class CurationContractTests(unittest.TestCase):
    """Verify the boundaries that protect the later model probe."""

    def test_safe_yaml_rejects_python_object_tag(self) -> None:
        with self.assertRaises(yaml.constructor.ConstructorError):
            safe_load_yaml("value: !!python/object/apply:os.system ['echo unsafe']")

    def test_safe_yaml_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(Exception, "duplicate key"):
            safe_load_yaml("repo: a\nrepo: b\n")

    def test_patch_paths_reject_binary_and_out_of_scope(self) -> None:
        patch = "diff --git a/ok.py b/ok.py\nGIT binary patch\n"
        with self.assertRaisesRegex(PatchProtocolError, "binary_patch"):
            validate_patch_paths(patch, ["ok.py"])
        patch = "diff --git a/../escape.py b/../escape.py\n"
        with self.assertRaisesRegex(PatchProtocolError, "unsafe_patch_path"):
            validate_patch_paths(patch, ["../escape.py"])

    def test_condition_facts_are_equal_information(self) -> None:
        record = {
            "source": "requests",
            "target": "aiohttp",
            "domain": "HTTP",
            "files": [
                {
                    "path": "app.py",
                    "code_changes": [
                        {
                            "cardinality": "one-to-one",
                            "properties": ["async transformation"],
                            "source_program_elements": ["function call"],
                        }
                    ],
                }
            ],
        }
        facts = condition_facts(record)
        prose = facts_prose(facts)
        prose_arm = {"facts": facts, "facts_text": prose}
        structured_arm = {"facts": facts}
        self.assertEqual(prose_arm["facts"], structured_arm["facts"])
        self.assertIn("requests", prose)
        self.assertIn("aiohttp", prose)
        self.assertEqual(facts["affected_file_count"], 1)
        self.assertEqual(facts["code_change_count"], 1)
        self.assertNotIn("target_apis", facts)
        self.assertNotIn("line", facts)

    def test_condition_contract_is_equal_information_and_oracle_safe(self) -> None:
        contract = condition_contract()
        prose = contract["PROSE_CHANGE_FACTS"]
        structured = contract["STRUCTURED_CHANGE_FACTS"]
        self.assertEqual(prose["facts_fields"], structured["facts_fields"])
        self.assertIn("facts_text", prose["actor_visible"])
        self.assertNotIn("facts_text", structured["actor_visible"])
        self.assertEqual(
            contract["forbidden_actor_visible"],
            ["target_apis", "line_maps", "gold_diff", "tests", "target_code"],
        )

    def test_test_selection_excludes_changed_tests_and_stays_bounded(self) -> None:
        selected = select_test_paths(
            ["tests/test_login.py", "tests/test_utils.py", "tests/test_other.py"],
            ["src/login.py"],
        )
        self.assertEqual(selected, ["tests/test_login.py"])
        with self.assertRaisesRegex(ValueError, "migration_changes_tests"):
            select_test_paths(
                ["tests/test_login.py"],
                ["tests/test_login.py"],
            )

    def test_test_path_detection_excludes_non_python_fixtures(self) -> None:
        self.assertFalse(is_test_path("tests/fixtures/profiles/01/History"))
        self.assertFalse(is_test_path("tests/log/log_test_SYS.pdf"))
        self.assertFalse(is_test_path("ironic/tests/drivers/pxe_config.template"))
        self.assertTrue(is_test_path("tests/test_login.py"))
        self.assertTrue(is_test_path("tests/helper.py"))

    def test_patch_applies_and_evaluation_command_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Curation Test"],
                cwd=repo,
                check=True,
            )
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial"],
                cwd=repo,
                check=True,
            )
            patch = (
                "diff --git a/app.py b/app.py\n"
                "--- a/app.py\n"
                "+++ b/app.py\n"
                "@@ -1 +1 @@\n"
                "-value = 1\n"
                "+value = 2\n"
            )
            applied = apply_patch(repo, patch, ["app.py"])
            self.assertEqual(applied["changed_paths"], ["app.py"])
            self.assertEqual(
                (repo / "app.py").read_text(encoding="utf-8"),
                "value = 2\n",
            )
            result = evaluate_patch(
                repo,
                [sys.executable, "-c", "assert open('app.py').read() == 'value = 2\\n'"],
            )
            self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
