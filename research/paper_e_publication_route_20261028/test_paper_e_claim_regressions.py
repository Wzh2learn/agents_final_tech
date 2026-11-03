"""Protect specific scientific attribution errors found during manuscript review."""
import json
from pathlib import Path
import re
import unittest

from research.paper_e_publication_route_20261028.recheck_lexical_holm import recheck


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "research/paper_e_publication_route_20261028/paper_e_icint_draft.md"
V1 = ROOT / "research/paper_e_public_eval_20261028/results/v1_uncorrected/BEIR_AUDIT_RESULT_20261028.json"
V2 = ROOT / "research/paper_e_public_eval_20261028/results/BEIR_AUDIT_RESULT_V2_20261028.json"
MC = ROOT / "research/paper_e_evidence_followup_20261028/mc_recheck.json"
VISIBILITY = ROOT / "logs/graph/eval/checkpoint_discrimination_tables_v2.json"
OPERATING_POINTS = ROOT / "logs/graph/eval/t1_eval_baseline_comparison.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PaperClaimRegressionTest(unittest.TestCase):
    def test_saved_scores_support_matched_threshold_claim(self):
        arm = load(OPERATING_POINTS)["arm_b"]
        for unit, expected_total, expected_detected in (
            ("tables", 95, 75), ("injections", 118, 85),
        ):
            rows = arm[unit]
            flat = {i for i, row in enumerate(rows) if row["drop10"] >= 2.0}
            matched = {i for i, row in enumerate(rows) if row["E1.3_root_drop"] >= 0.75}
            self.assertEqual((len(rows), len(flat)), (expected_total, expected_detected))
            self.assertEqual(flat, matched)

    def test_tfidf_map_values_belong_to_tfidf_not_bm25(self):
        first, second = (next(row for row in load(path)["datasets"] if row["dataset"] == "nfcorpus") for path in (V1, V2))
        old = first["systems"]["tfidf_cosine"]["map@10"]["mean"]
        corrected = second["systems"]["tfidf_cosine"]["map@10"]["mean"]
        phrase = f"TF-IDF's MAP@10 from approximately {old:.4f} to {corrected:.4f}"
        self.assertIn(phrase, PAPER.read_text(encoding="utf-8"))
        self.assertNotAlmostEqual(old, first["systems"]["bm25_k1=1.5_b=0.6"]["map@10"]["mean"], places=4)

    def test_200k_lexical_recheck_retains_supported_pair_identities(self):
        result = recheck(load(V2), load(MC))
        expected = {"scifact": {frozenset(("BM25_15_06", "TFIDF")), frozenset(("BM25_12_075", "TFIDF"))},
                    "nfcorpus": {frozenset(("BM25_15_06", "BM25_05_03"))}}
        for dataset, identities in expected.items():
            rows = result[dataset]["pairs"]
            self.assertEqual({frozenset((r["a"], r["b"])) for r in rows if r["significant_200k"]}, identities)
            self.assertEqual(result[dataset]["changed_classifications"], 0)

    def test_visible_count_is_frozen_injection_level_not_table_level(self):
        tables = load(VISIBILITY)["tables"]
        injections = [row for table in tables for row in table["injections"]]
        self.assertEqual((len(tables), len(injections), sum(row["visible"] for row in injections)), (95, 118, 96))
        self.assertTrue(all(row["canonical"] is not None for row in injections))

    def test_current_manuscripts_cite_every_reference_and_include_disclosure(self):
        directory = PAPER.parent
        variants = ((PAPER, directory / "icint_latex/main.tex", "Sections I--VI"),
                    (directory / "paper_e_icdar_working.md",
                     directory / "icdar_adapted_20261101/main.tex", "Sections 1--6"))
        for markdown, latex, section_label in variants:
            body, references = markdown.read_text(encoding="utf-8").split("# References", 1)
            declared = re.findall(r"(?m)^\[(\d+)\]", references)
            cited = set(re.findall(r"\[(\d+)\]", body))
            self.assertEqual(declared, [str(n) for n in range(1, len(declared) + 1)])
            self.assertEqual(cited, set(declared))
            rendered = latex.read_text(encoding="utf-8")
            self.assertEqual(re.findall(r"\\bibitem\{r(\d+)\}", rendered), declared)
            self.assertEqual(set(re.findall(r"\\cite\{r(\d+)\}", rendered)), cited)
            self.assertEqual(rendered.count(r"\section*{Acknowledgment}"), 1)
            self.assertIn(section_label, rendered)


if __name__ == "__main__":
    unittest.main()
