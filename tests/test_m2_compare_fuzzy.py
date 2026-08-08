"""Tests for M2 compare fuzzy product-name matching + product list noise filter.

Background (blocked_questions 2026-08-01): compare/positions for "嘉兴民安"
returned empty because metadata stores the full legal name
"嘉兴民安投资合伙企业（有限合伙）" and the query used exact equality.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import biz.m2_service as m2


class TestCleanProductName:
    def test_markdown_fragment_dropped(self):
        assert m2._clean_product_name("| ****金 |") == ""

    def test_label_line_dropped(self):
        assert m2._clean_product_name("账　****　号：") == ""
        assert m2._clean_product_name("note:") == ""

    def test_body_fragment_dropped(self):
        assert m2._clean_product_name("一、****1日）") == ""

    def test_real_names_kept(self):
        assert m2._clean_product_name("嘉兴民安投资合伙企业（有限合伙）") == "嘉兴民安投资合伙企业（有限合伙）"
        assert m2._clean_product_name("复熙混合25号") == "复熙混合25号"

    def test_empty_and_short(self):
        assert m2._clean_product_name(None) == ""
        assert m2._clean_product_name("") == ""
        assert m2._clean_product_name(" ") == ""
        assert m2._clean_product_name("A") == ""


class TestFuzzyProductFallback:
    def _mock_session(self, exact_rows, fuzzy_rows):
        db = MagicMock()
        chain = db.query.return_value.join.return_value
        chain.filter.return_value = chain
        # statement_date/table_name filters may add .filter calls; the final
        # product filter is the last one. .all() side effects distinguish runs.
        chain.all.side_effect = [exact_rows, fuzzy_rows]
        return db

    def test_fallback_used_when_exact_empty(self):
        row = ("doc", {"product_name": "嘉兴民安投资合伙企业（有限合伙）", "table_name": "t"})
        db = self._mock_session([], [row])
        with patch.object(m2, "_get_db_session", return_value=db):
            chunks = m2._query_collection_chunks(product_name="嘉兴民安")
        assert len(chunks) == 1
        assert chunks[0]["metadata"]["product_name"].startswith("嘉兴民安")
        assert db.query.return_value.join.return_value.all.call_count == 2

    def test_exact_match_skips_fuzzy(self):
        row = ("doc", {"product_name": "嘉兴民安"})
        db = self._mock_session([row], [])
        with patch.object(m2, "_get_db_session", return_value=db):
            chunks = m2._query_collection_chunks(product_name="嘉兴民安")
        assert len(chunks) == 1
        assert db.query.return_value.join.return_value.all.call_count == 1

    def test_no_product_no_fallback(self):
        row = ("doc", {"product_name": "x"})
        db = self._mock_session([row], [])
        with patch.object(m2, "_get_db_session", return_value=db):
            chunks = m2._query_collection_chunks()
        assert len(chunks) == 1
        assert db.query.return_value.join.return_value.all.call_count == 1


class TestListProductsNoiseFilter:
    def test_noise_filtered(self):
        db = MagicMock()
        rows = [("嘉兴民安投资合伙企业（有限合伙）",), ("| ****金 |",),
                ("账　****　号：",), ("一、****1日）",), ("复熙混合25号",), (None,)]
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.all.return_value = rows
        with patch.object(m2, "_get_db_session", return_value=db):
            products = m2.list_products()
        assert products == ["嘉兴民安投资合伙企业（有限合伙）", "复熙混合25号"]
