from __future__ import annotations

import unittest

from .calculator import numeric_value
from .contracts import ARMS, PROMPT_TEMPLATE_SHA256, canonical_json, sha256_bytes
from .runner import load_sources, write_zero_output_dry_run
from .scorer_input_builder import build_scorer_input, evidence_visible
from .semantic_matcher import _normalize_candidate_refs, semantic_result
from .strict_parser import ParsedResponse, parse_response


class RawChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded = load_sources()

    def test_dry_run_all_items_all_arms_zero_output(self):
        payload = write_zero_output_dry_run()
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["dry_run_items"], 36)
        self.assertEqual(payload["dry_run_unique_question_uids"], 12)
        self.assertEqual(payload["model_calls"], 0)

    def test_prompt_template_hash_is_frozen(self):
        from .contracts import PROMPT_TEMPLATE
        self.assertEqual(PROMPT_TEMPLATE_SHA256, sha256_bytes(PROMPT_TEMPLATE.encode("utf-8")))

    def test_calculator_is_safe_decimal_only(self):
        self.assertEqual(numeric_value("1,496+4"), 1500.0)
        self.assertIsNone(numeric_value("__import__('os')"))

    def test_strict_parser_rejects_extra_key(self):
        with self.assertRaisesRegex(ValueError, "schema_keys_mismatch"):
            parse_response('{"answer":"1","numeric_value":1,"unit":"","evidence_refs":[],"unknown":false,"clarification":"","extra":true}')

    def test_strict_parser_accepts_table_column_reference(self):
        response = parse_response(
            '{"answer":"1","numeric_value":1,"unit":"x","evidence_refs":["TABLE:C1","TABLE:R2:C3"],"unknown":false,"clarification":""}'
        )
        self.assertEqual(_normalize_candidate_refs(response), {"C1", "R2:C3"})

    def test_tri_state_wrong_role_is_pending(self):
        uid = self.loaded["selection"]["selected_uids"][0]
        reference = self.loaded["reference_by_uid"][uid]
        response = ParsedResponse("10425.5", 10425.5, "thousand", ["P1"], False, "")
        self.assertEqual(semantic_result(response, reference, True)["outcome"], "PENDING_ADJUDICATION")

    def test_reference_chain_is_post_generation_only(self):
        uid = self.loaded["selection"]["selected_uids"][0]
        response = ParsedResponse.unknown_response()
        payload = build_scorer_input(response, self.loaded["reference_by_uid"][uid], set())
        self.assertEqual(payload["schema"], "p2_post_generation_scorer_input_v1")
        self.assertEqual(payload["scorer_input_sha256"], sha256_bytes(canonical_json(response.to_dict())))

    def test_evidence_visibility_requires_required_paragraphs(self):
        uid = self.loaded["selection"]["selected_uids"][0]
        self.assertFalse(evidence_visible(self.loaded["reference_by_uid"][uid], set()))

    def test_arm_definition_is_fixed(self):
        self.assertEqual(ARMS, {"table_top3": 3, "table_top5": 5, "table_all": None})


if __name__ == "__main__":
    unittest.main()
