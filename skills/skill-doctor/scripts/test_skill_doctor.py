from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("skill-doctor.py")


class SkillDoctorAdvisoryTests(unittest.TestCase):
    BACKTICK = chr(96)

    def make_catalog(self, model: str, body: str) -> Path:
        root = Path(self.temp.name)
        skill = root / "skills/demo"
        (skill / "agents").mkdir(parents=True)
        (root / "README.md").write_text(
            "# Catalog\n\n## Skills\n\n| Skill | Description |\n| ----- | ----------- |\n| demo | Demo |\n",
            encoding="utf-8",
        )
        (skill / "SKILL.md").write_text(
            "---\n"
            "disable-model-invocation: false\n"
            f"model: {model}\n"
            "name: demo\n"
            "description: Demo.\n"
            "---\n\n"
            f"# Demo\n\n{body}\n",
            encoding="utf-8",
        )
        (skill / "agents/openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        return root

    def run_doctor(self, root: Path) -> dict[str, object]:
        result = subprocess.run(
            ["uv", "run", str(SCRIPT), "--root", str(root), "--format", "json"],
            text=True,
            capture_output=True,
            check=False,
        )
        return json.loads(result.stdout)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_warns_for_stale_pin_and_missing_completion(self) -> None:
        report = self.run_doctor(self.make_catalog("opus", "Do the work."))
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("STALE_MODEL_PIN", codes)
        self.assertIn("COMPLETION_EVIDENCE_MISSING", codes)

    def test_accepts_current_pin_with_completion_contract(self) -> None:
        report = self.run_doctor(self.make_catalog("sonnet", "## Completion\n\nReport verified output."))
        self.assertEqual(report["counts"]["findings"], 0)


    def test_example_link_inside_code_span_is_not_a_missing_resource(self) -> None:
        """Decision 39 (F-2): a path shown as an example inside a code span is not a live reference."""
        body = "- full path reference (such as " + self.BACKTICK + "scripts/env_gpu-cluster.sh" + self.BACKTICK + ")"
        report = self.run_doctor(self.make_catalog("sonnet", body + "\n\n## Completion\n\nReport verified output."))
        codes = {item["code"] for item in report["findings"]}
        self.assertNotIn("RESOURCE_LINK_MISSING", codes)
        self.assertEqual(report["counts"]["errors"], 0)

    def test_live_markdown_link_to_missing_resource_still_fails(self) -> None:
        """Negative control: a real link (not inside a code span) must still be reported."""
        body = "- see [" + self.BACKTICK + "missing" + self.BACKTICK + "](scripts/env_gpu-cluster.sh)"
        report = self.run_doctor(self.make_catalog("sonnet", body + "\n\n## Completion\n\nReport verified output."))
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("RESOURCE_LINK_MISSING", codes)

    def test_live_uv_run_reference_to_missing_script_still_fails(self) -> None:
        """Negative control: a live `uv run scripts/...` reference must still be reported."""
        body = "Run " + self.BACKTICK + "uv run scripts/does-not-exist.py" + self.BACKTICK + " to start."
        report = self.run_doctor(self.make_catalog("sonnet", body + "\n\n## Completion\n\nReport verified output."))
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("RESOURCE_LINK_MISSING", codes)

if __name__ == "__main__":
    unittest.main()
