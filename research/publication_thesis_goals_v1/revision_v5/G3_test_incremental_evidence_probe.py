from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from G3_incremental_evidence_probe import (
    build_decision_prompt,
    expansion_value,
    parse_decision,
    policy_row,
    visible_gap_rule,
)


def sample_item() -> dict[str, object]:
    return {
        "uid": "test-uid",
        "type": "T1",
        "timestamps": ["2020", "2021", "2022", "2023", "2024"],
        "haystack_session": [
            [{"role": "user", "content": "I used to live in Paris."}],
            [{"role": "user", "content": "I moved to Rome."}],
            [{"role": "assistant", "content": "Travel can change plans."}],
            [{"role": "user", "content": "The plan changed."}],
            [{"role": "user", "content": "I now live in Rome."}],
        ],
        "probing_queries": {"dim1_query": "Where does the user live now?"},
        "relevant_session_index": [1, 4],
    }


class IncrementalEvidenceProbeTests(unittest.TestCase):
    def test_expansion_value_distinguishes_gain_and_pair_completion(self) -> None:
        item = sample_item()
        value = expansion_value(item, [0, 1, 2], [0, 1, 4])
        self.assertEqual(value["added_relevant_count"], 1)
        self.assertTrue(value["useful_expansion"])
        self.assertTrue(value["completes_pair"])

    def test_policy_row_does_not_hide_no_gain_expansion(self) -> None:
        item = sample_item()
        row = policy_row(item, "candidate", "EXPAND", [1, 4, 0], [1, 4, 0])
        self.assertEqual(row["action_quality"], "NO_GAIN_EXPAND")
        self.assertFalse(row["expansion_value"]["useful_expansion"])

    def test_visible_rule_is_invariant_to_hidden_reference(self) -> None:
        item = sample_item()
        query = str(item["probing_queries"]["dim1_query"])
        ranked = [(0, 3.0), (1, 2.5), (2, 2.0), (3, 1.0), (4, 0.5)]
        first, first_diag = visible_gap_rule(query, item, [0, 1, 2], ranked)
        item["relevant_session_index"] = [3, 4]
        second, second_diag = visible_gap_rule(query, item, [0, 1, 2], ranked)
        self.assertEqual(first, second)
        self.assertEqual(first_diag, second_diag)

    def test_prompt_excludes_hidden_reference_fields(self) -> None:
        prompt = build_decision_prompt(sample_item(), [0, 1, 2])
        self.assertNotIn("relevant_session_index", prompt)
        self.assertNotIn("M_old", prompt)
        self.assertNotIn("M_new", prompt)
        self.assertNotIn("explanation", prompt)

    def test_decision_contract_rejects_extra_keys_and_aliases(self) -> None:
        valid = (
            '{"action":"KEEP","confidence":"HIGH","evidence_anchors":["Paris"],'
            '"missing_information":[],"reason":"sufficient"}'
        )
        self.assertEqual(parse_decision(valid)["action"], "KEEP")
        with self.assertRaises(ValueError):
            parse_decision(valid[:-1] + ',"extra":1}')
        with self.assertRaises(ValueError):
            parse_decision(valid.replace('"KEEP"', '"KEEP_AND_EXPAND"'))


if __name__ == "__main__":
    unittest.main()
