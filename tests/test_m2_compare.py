"""Tests for M2 cross-document comparison (Phase 1).

Unit tests for comparison service functions + API contract tests.
All external dependencies (PGVector, LLM) are mocked.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import biz.m2_service as m2


# ---------------------------------------------------------------------------
# Unit tests: intent detection
# ---------------------------------------------------------------------------

class TestCompareIntentDetection:
    def test_detect_compare_keywords(self):
        assert m2.detect_compare_intent("复熙混合25号和博时的对比") is True
        assert m2.detect_compare_intent("资产有什么变化？") is True
        assert m2.detect_compare_intent("两个产品的差异") is True
        assert m2.detect_compare_intent("持仓增减情况") is True
        assert m2.detect_compare_intent("A vs B") is True

    def test_no_compare_intent(self):
        assert m2.detect_compare_intent("嘉兴民安的总资产是多少？") is False
        assert m2.detect_compare_intent("有哪些证券持仓？") is False


# ---------------------------------------------------------------------------
# Unit tests: chunk field parsing
# ---------------------------------------------------------------------------

class TestParseChunkFields:
    def test_parse_kv_line(self):
        text = "样本: s1\n表: 资金资产汇总\n字段: 总资产=401383291.83, 币种=人民币"
        fields = m2._parse_chunk_fields(text)
        assert fields["总资产"] == "401383291.83"
        assert fields["币种"] == "人民币"

    def test_parse_empty(self):
        assert m2._parse_chunk_fields("") == {}
        assert m2._parse_chunk_fields("no fields here") == {}

    def test_parse_desensitized(self):
        text = "字段: 总资产=4013****91.83, 证券名称=平安****行"
        fields = m2._parse_chunk_fields(text)
        assert fields["总资产"] == "4013****91.83"
        assert fields["证券名称"] == "平安****行"


# ---------------------------------------------------------------------------
# Unit tests: _try_float
# ---------------------------------------------------------------------------

class TestTryFloat:
    def test_valid_numbers(self):
        assert m2._try_float("123.45") == 123.45
        assert m2._try_float("1,234.56") == 1234.56
        assert m2._try_float("-42") == -42.0

    def test_desensitized_returns_none(self):
        assert m2._try_float("4013****91.83") is None

    def test_empty_returns_none(self):
        assert m2._try_float("") is None
        assert m2._try_float(None) is None


# ---------------------------------------------------------------------------
# Unit tests: _extract_compare_params
# ---------------------------------------------------------------------------

class TestExtractCompareParams:
    @patch.object(m2, "list_products", return_value=["复熙混合25号", "嘉兴民安"])
    def test_extracts_product_name(self, mock_lp):
        params = m2._extract_compare_params("复熙混合25号的对比分析")
        assert params["product"] == "复熙混合25号"

    @patch.object(m2, "list_products", return_value=["复熙混合25号"])
    def test_extracts_dates(self, mock_lp):
        params = m2._extract_compare_params("20231031和20231130对比")
        assert params["date_a"] == "20231031"
        assert params["date_b"] == "20231130"

    @patch.object(m2, "list_products", return_value=[])
    def test_extracts_fields(self, mock_lp):
        params = m2._extract_compare_params("总资产和市值的变化")
        assert "总资产" in params["fields"]
        assert "市值" in params["fields"]


# ---------------------------------------------------------------------------
# Unit tests: _format_compare_answer
# ---------------------------------------------------------------------------

class TestFormatCompareAnswer:
    def test_format_insufficient_data(self):
        result = {
            "status": "insufficient_data",
            "message": "该产品仅有一期对账单",
            "available_dates": ["20231031"],
        }
        answer = m2._format_compare_answer(result)
        assert "仅有一期" in answer
        assert "20231031" in answer

    def test_format_positions(self):
        result = {
            "product": "测试产品",
            "date": "20231031",
            "total_market_value": "1,000.00",
            "position_count": 2,
            "positions": [
                {"name": "平安银行", "market_value": "600", "pct_of_total": "60.00%"},
                {"name": "招商银行", "market_value": "400", "pct_of_total": "40.00%"},
            ],
        }
        answer = m2._format_compare_answer(result)
        assert "平安银行" in answer
        assert "60.00%" in answer

    def test_format_diffs(self):
        result = {
            "product": "测试",
            "date_a": "20231031",
            "date_b": "20231130",
            "status": "ok",
            "diffs": [
                {"field": "总资产", "value_a": "100", "value_b": "120",
                 "change": "+20.00", "change_pct": "+20.00%"},
            ],
        }
        answer = m2._format_compare_answer(result)
        assert "总资产" in answer
        assert "+20.00" in answer


# ---------------------------------------------------------------------------
# Service tests: comparison with mocked DB
# ---------------------------------------------------------------------------

class TestCompareService:
    @patch.object(m2, "list_products", return_value=["产品A", "产品B"])
    def test_list_products_mock(self, mock_lp):
        products = m2.list_products()
        assert len(products) == 2
        assert "产品A" in products

    @patch.object(m2, "_query_collection_chunks")
    def test_timeline_single_date(self, mock_chunks):
        mock_chunks.return_value = [
            {"document": "字段: 总资产=100, 币种=人民币",
             "metadata": {"statement_date": "20231031", "table_name": "资金资产汇总"}},
            {"document": "字段: 证券名称=平安银行, 市值=50",
             "metadata": {"statement_date": "20231031", "table_name": "证券持仓明细"}},
        ]
        result = m2.get_product_timeline("产品A")
        assert len(result["timeline"]) == 1
        assert result["timeline"][0]["date"] == "20231031"
        assert result["timeline"][0]["total_assets"] == "100"
        assert result["timeline"][0]["position_count"] == 1

    @patch.object(m2, "get_product_timeline")
    def test_compare_insufficient_data(self, mock_tl):
        mock_tl.return_value = {
            "product": "产品A",
            "timeline": [{"date": "20231031", "total_assets": "100",
                          "position_count": 1, "currency": "人民币"}],
        }
        result = m2.compare_dates("产品A", "20231031", "20231130")
        assert result["status"] == "insufficient_data"
        assert "仅有一期" in result["message"]

    @patch.object(m2, "_query_collection_chunks")
    def test_positions_compare(self, mock_chunks):
        mock_chunks.return_value = [
            {"document": "字段: 证券名称=平安银行, 市值=600",
             "metadata": {"table_name": "证券持仓明细", "statement_date": "20231031"}},
            {"document": "字段: 证券名称=招商银行, 市值=400",
             "metadata": {"table_name": "证券持仓明细", "statement_date": "20231031"}},
        ]
        result = m2.compare_positions("产品A", "20231031")
        assert result["position_count"] == 2
        assert result["positions"][0]["name"] == "平安银行"
        assert result["positions"][0]["pct_of_total"] == "60.00%"
        assert result["positions"][1]["name"] == "招商银行"

    @patch.object(m2, "handle_compare_query")
    @patch.object(m2, "collection_name", return_value="test_col")
    def test_nl_routing_compare(self, mock_col, mock_cmp):
        """ask() with '对比' keyword triggers comparison path."""
        mock_cmp.return_value = {
            "answer": "对比结果...",
            "sources": [],
            "model": "rule-based-compare",
            "compare_mode": True,
        }
        result = m2.ask("复熙混合25号的持仓对比")
        assert result.get("compare_mode") is True
        assert "对比结果" in result["answer"]
        mock_cmp.assert_called_once()


# ---------------------------------------------------------------------------
# API contract tests (FastAPI TestClient)
# ---------------------------------------------------------------------------

class TestCompareAPI:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from web.routers.m2 import router

        app = FastAPI()
        app.include_router(router, prefix="/api/m2")
        return TestClient(app)

    @patch("web.routers.m2.list_products", return_value=["复熙混合25号", "嘉兴民安"])
    def test_products_list(self, mock_lp, client):
        resp = client.get("/api/m2/products")
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert len(data["products"]) == 2
        assert "复熙混合25号" in data["products"]

    @patch("web.routers.m2.get_product_timeline")
    def test_timeline_single_date(self, mock_tl, client):
        mock_tl.return_value = {
            "product": "复熙混合25号",
            "timeline": [{"date": "20231031", "total_assets": "4013****91.83",
                          "position_count": 1, "currency": "人民币"}],
        }
        resp = client.get("/api/m2/products/复熙混合25号/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["timeline"]) == 1
        assert data["timeline"][0]["date"] == "20231031"

    @patch("web.routers.m2.compare_dates")
    def test_compare_insufficient_data(self, mock_cmp, client):
        mock_cmp.return_value = {
            "product": "复熙混合25号",
            "date_a": "20231031",
            "date_b": "20231130",
            "status": "insufficient_data",
            "message": "该产品仅有一期对账单，跨期对比需甲方提供多期数据",
            "available_dates": ["20231031"],
        }
        resp = client.post("/api/m2/compare", json={
            "product": "复熙混合25号",
            "date_a": "20231031",
            "date_b": "20231130",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "insufficient_data"

    @patch("web.routers.m2.compare_positions")
    def test_positions_compare(self, mock_pos, client):
        mock_pos.return_value = {
            "product": "复熙混合25号",
            "date": "20231031",
            "total_market_value": "1,000.00",
            "position_count": 2,
            "positions": [
                {"name": "平安银行", "market_value": "600", "pct_of_total": "60.00%", "fields": {}},
                {"name": "招商银行", "market_value": "400", "pct_of_total": "40.00%", "fields": {}},
            ],
        }
        resp = client.post("/api/m2/compare/positions", json={
            "product": "复熙混合25号",
            "date": "20231031",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["position_count"] == 2
        assert data["positions"][0]["name"] == "平安银行"

    @patch("biz.m2_service.handle_compare_query")
    @patch("biz.m2_service.collection_name", return_value="test_col")
    def test_nl_routing_compare_via_ask(self, mock_col, mock_cmp, client):
        mock_cmp.return_value = {
            "answer": "持仓对比结果...",
            "sources": [],
            "model": "rule-based-compare",
            "compare_mode": True,
        }
        resp = client.post("/api/m2/ask", json={
            "question": "复熙混合25号的持仓对比",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("compare_mode") is True
