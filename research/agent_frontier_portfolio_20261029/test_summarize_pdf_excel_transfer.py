import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent_frontier_portfolio_20261029.summarize_pdf_excel_transfer import summarize


class PdfExcelSummaryTest(unittest.TestCase):
    def test_missing_output_not_reported_as_zero_accuracy(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for condition in ("no_memory", "prior_experience", "task_skills"):
                case = root / ("pdf-excel-diff__" + condition)
                (case / "work").mkdir(parents=True)
                (case / "raw.jsonl").write_bytes(b"raw")
                (case / "verifier.txt").write_text("1 failed, 2 passed", encoding="utf-8")
                (case / "intervention.json").write_text(json.dumps({"condition": condition, "public_input_sha256": {}}))
                (case / "receipt.json").write_text(json.dumps({
                    "raw_sha256": hashlib.sha256(b"raw").hexdigest(), "agent_exit": 1,
                    "verifier_exit": 1, "elapsed_seconds": 1, "model_http_requests": [],
                    "step_finish_tokens": [], "post_content_lengths": []}))
            result = summarize(root, {"deleted_employees": [], "modified_employees": []})
            self.assertEqual(result["conditions"]["no_memory"]["evaluation"]["status"], "NO_OUTPUT")
            self.assertEqual(result["conditions"]["no_memory"]["verifier_passed"], 2)
            (root / "pdf-excel-diff__no_memory" / "raw.jsonl").write_bytes(b"altered")
            with self.assertRaises(ValueError):
                summarize(root, {"deleted_employees": [], "modified_employees": []})


if __name__ == "__main__":
    unittest.main()
