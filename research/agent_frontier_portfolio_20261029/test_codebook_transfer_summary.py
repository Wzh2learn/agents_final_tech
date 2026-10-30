import csv
import json
from pathlib import Path
import tempfile
import unittest

from research.agent_frontier_portfolio_20261029.summarize_codebook_transfer import compare_assignments, inspect_output, inspect_visible_inputs


class CodebookSummaryTest(unittest.TestCase):
    def test_exact_label_unknown_and_station_are_separate_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root / "test_center_logs.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["record_id", "product_id", "station"])
                writer.writeheader()
                writer.writerows([{"record_id": "r1", "product_id": "P", "station": "B"},
                                  {"record_id": "r2", "product_id": "P", "station": "A"}])
            with (root / "codebook_P.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["product_id", "code", "standard_label", "station_scope"])
                writer.writeheader()
                writer.writerow({"product_id": "P", "code": "c1", "standard_label": "Open Circuit", "station_scope": "A"})
            out = root / "solution.json"
            out.write_text(json.dumps({"records": [
                {"record_id": "r1", "normalized": [{"segment_id": "r1-S1", "span_text": "open circuit", "pred_code": "c1"}]},
                {"record_id": "r2", "normalized": [{"segment_id": "r2-S1", "span_text": "noise", "pred_code": "UNKNOWN"}]},
            ]}), encoding="utf-8")
            result, assignments = inspect_output(root, out)
            self.assertEqual(result["input_ids_covered"], 2)
            self.assertEqual(result["counts"]["exact_label_selected"], 1)
            self.assertEqual(result["counts"]["known_station_mismatch"], 1)
            self.assertEqual(result["counts"]["unknown_segments"], 1)
            self.assertEqual(len(assignments), 2)

    def test_missing_output_is_not_a_zero_accuracy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test_center_logs.csv").write_text("record_id,product_id,station\nr1,P,A\n", encoding="utf-8")
            result, assignments = inspect_output(root, root / "missing.json")
            self.assertFalse(result["has_output"])
            self.assertNotIn("counts", result)
            self.assertEqual(assignments, {})

    def test_input_label_opportunity_is_product_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test_center_logs.csv").write_text(
                "record_id,product_id,station,raw_reason_text\nr1,P,A,OPEN CIRCUIT\nr2,Q,A,OPEN CIRCUIT\n", encoding="utf-8")
            (root / "codebook_P.csv").write_text("product_id,code,standard_label,station_scope\nP,c1,Open Circuit,A\n", encoding="utf-8")
            result = inspect_visible_inputs(root)
            self.assertEqual(result["input_records"], 2)
            self.assertEqual(result["exact_whole_label_in_raw_text"], 1)
            self.assertEqual(result["full_label_substring_in_raw_text"], 1)

    def test_shared_segment_id_with_different_span_is_not_same_prediction_unit(self):
        left = {("r1", "r1-S1"): ("c1", "first"), ("r2", "r2-S1"): ("c1", "same")}
        right = {("r1", "r1-S1"): ("c2", "different"), ("r2", "r2-S1"): ("c2", "same")}
        result = compare_assignments(left, right)
        self.assertEqual(result["shared_record_segment_ids"], 2)
        self.assertEqual(result["same_exact_span_with_shared_ids"], 1)
        self.assertEqual(result["different_assigned_codes_on_same_exact_span"], 1)


if __name__ == "__main__":
    unittest.main()
