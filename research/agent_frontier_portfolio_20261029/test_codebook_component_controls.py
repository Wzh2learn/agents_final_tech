import unittest
import tempfile
from pathlib import Path

from research.agent_frontier_portfolio_20261029.run_codebook_component_controls import make_source
from research.agent_frontier_portfolio_20261029.summarize_codebook_component_controls import input_component_opportunities


SAMPLE = """def match(raw_segment, kw):
    seg_lower = raw_segment.lower()
    comp_refs = [r.upper() for r in re.findall(r'[A-Z]+[\\d]+', seg_lower)]
    if re.search(r'[A-Z]+[\\d]+', kw):
        for cr_upper in comp_refs:
            kw_upper = kw.upper()
            if cr_upper in kw_upper or kw_upper in cr_upper:
                return True
    return False
"""


class ComponentControlTest(unittest.TestCase):
    def test_case_repair_and_exact_match_are_distinct(self):
        import re
        functions = {}
        for variant in ("original_replay", "case_substring", "case_exact", "case_signal_exact"):
            namespace = {"re": re}
            exec(make_source(SAMPLE, variant), namespace)
            functions[variant] = namespace["match"]
        self.assertFalse(functions["original_replay"]("R1", "r10"))
        self.assertTrue(functions["case_substring"]("R1", "r10"))
        self.assertFalse(functions["case_exact"]("R1", "r10"))
        self.assertTrue(functions["case_exact"]("R10", "r10"))
        self.assertFalse(functions["case_exact"]("I2C_SCL", "i2c_scl"))
        self.assertTrue(functions["case_signal_exact"]("I2C_SCL", "i2c_scl"))

    def test_drift_in_frozen_program_is_rejected(self):
        with self.assertRaises(ValueError):
            make_source("print('unrelated')", "case_exact")

    def test_component_opportunities_distinguish_exact_and_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "codebook_P.csv").write_text("product_id,keywords_examples\nP,R10\n", encoding="utf-8")
            (root / "test_center_logs.csv").write_text("product_id,raw_reason_text\nP,R1 failed\nP,R10 failed\n", encoding="utf-8")
            result = input_component_opportunities(root)
            self.assertEqual(result["records_with_component_regex"], 2)
            self.assertEqual(result["records_with_regex_fragment_equal_keyword"], 1)
            self.assertEqual(result["records_with_partial_regex_fragment_candidate"], 1)


if __name__ == "__main__":
    unittest.main()
