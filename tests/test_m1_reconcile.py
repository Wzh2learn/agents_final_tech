"""Unit tests for reconcile logic in scripts/m1_statement_parser.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from m1_statement_parser import (
    Schema,
    SchemaField,
    SchemaTable,
    reconcile,
    _parse_number,
    _is_total_row,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_schema() -> Schema:
    detail = SchemaTable("证券持仓明细", "grid", [], [
        SchemaField("证券名称", ["证券名称"]),
        SchemaField("市值", ["市值"]),
        SchemaField("币种", ["币种"]),
    ])
    summary = SchemaTable("资金资产汇总", "grid", [], [
        SchemaField("资产市值", ["资产市值", "证券市值"]),
        SchemaField("资产总值", ["资产总值"]),
    ])
    return Schema([detail, summary], {})


def _detail_report(records: list[dict], mapping=None) -> dict:
    return {
        "matched_schema": "证券持仓明细",
        "mapping": mapping or {"证券名称": "证券名称", "市值": "市值", "币种": "币种"},
        "_records": records,
    }


def _summary_report(records: list[dict]) -> dict:
    return {
        "matched_schema": "资金资产汇总",
        "mapping": {"资产市值": "资产市值"},
        "_records": records,
    }


# ---------------------------------------------------------------------------
# _parse_number
# ---------------------------------------------------------------------------

class TestParseNumber:
    def test_plain_number(self):
        assert _parse_number("12345.67") == 12345.67

    def test_comma_separated(self):
        assert _parse_number("1,234,567.89") == 1234567.89

    def test_empty_returns_none(self):
        assert _parse_number("") is None

    def test_non_numeric_returns_none(self):
        assert _parse_number("N/A") is None


# ---------------------------------------------------------------------------
# _is_total_row
# ---------------------------------------------------------------------------

class TestIsTotalRow:
    def test_total_marker(self):
        assert _is_total_row({"证券名称": "合计", "市值": "999"}) is True

    def test_normal_row(self):
        assert _is_total_row({"证券名称": "平安银行", "市值": "100"}) is False


# ---------------------------------------------------------------------------
# reconcile: market value
# ---------------------------------------------------------------------------

class TestReconcileMarketValue:
    def test_pass_when_sum_matches(self):
        schema = _make_schema()
        detail = _detail_report([
            {"证券名称": "A", "市值": "100.00", "币种": "人民币"},
            {"证券名称": "B", "市值": "200.00", "币种": "人民币"},
        ])
        summary = _summary_report([{"资产市值": "300.00"}])
        checks = reconcile([detail, summary], {}, schema)
        mv_check = next(c for c in checks if c["check"] == "市值勾稽")
        assert mv_check["pass"] is True
        assert mv_check["disposition"] == "real_pass"

    def test_fail_when_sum_mismatches(self):
        schema = _make_schema()
        detail = _detail_report([
            {"证券名称": "A", "市值": "100.00", "币种": "人民币"},
        ])
        summary = _summary_report([{"资产市值": "999.00"}])
        checks = reconcile([detail, summary], {}, schema)
        mv_check = next(c for c in checks if c["check"] == "市值勾稽")
        assert mv_check["pass"] is False
        assert mv_check["disposition"] == "fail"

    def test_total_row_excluded_from_sum(self):
        """合计 rows must not be double-counted in the detail sum."""
        schema = _make_schema()
        detail = _detail_report([
            {"证券名称": "A", "市值": "100.00", "币种": "人民币"},
            {"证券名称": "合计", "市值": "100.00", "币种": ""},
        ])
        summary = _summary_report([{"资产市值": "100.00"}])
        checks = reconcile([detail, summary], {}, schema)
        mv_check = next(c for c in checks if c["check"] == "市值勾稽")
        assert mv_check["pass"] is True


# ---------------------------------------------------------------------------
# reconcile: currency
# ---------------------------------------------------------------------------

class TestReconcileCurrency:
    def test_single_currency_passes(self):
        schema = _make_schema()
        detail = _detail_report([
            {"证券名称": "A", "市值": "100", "币种": "人民币"},
            {"证券名称": "B", "市值": "200", "币种": "人民币"},
        ])
        checks = reconcile([detail], {}, schema)
        cur_check = next(c for c in checks if c["check"] == "币种一致")
        assert cur_check["pass"] is True

    def test_mixed_currency_fails(self):
        schema = _make_schema()
        detail = _detail_report([
            {"证券名称": "A", "市值": "100", "币种": "人民币"},
            {"证券名称": "B", "市值": "200", "币种": "美元"},
        ])
        checks = reconcile([detail], {}, schema)
        cur_check = next(c for c in checks if c["check"] == "币种一致")
        assert cur_check["pass"] is False


# ---------------------------------------------------------------------------
# reconcile: date format
# ---------------------------------------------------------------------------

class TestReconcileDate:
    def test_valid_date_formats(self):
        schema = _make_schema()
        header_kv = {"统计日期": "2026-07-31"}
        checks = reconcile([], header_kv, schema)
        date_check = next(c for c in checks if c["check"] == "日期格式")
        assert date_check["pass"] is True

    def test_yyyymmdd_format(self):
        schema = _make_schema()
        header_kv = {"统计日期": "20260731"}
        checks = reconcile([], header_kv, schema)
        date_check = next(c for c in checks if c["check"] == "日期格式")
        assert date_check["pass"] is True


# ---------------------------------------------------------------------------
# reconcile: disposition labeling
# ---------------------------------------------------------------------------

class TestReconcileDisposition:
    def test_skipped_when_insufficient_data(self):
        schema = _make_schema()
        checks = reconcile([], {}, schema)
        mv_check = next(c for c in checks if c["check"] == "市值勾稽")
        assert mv_check["disposition"] == "skipped"

    def test_real_pass_labeling(self):
        schema = _make_schema()
        detail = _detail_report([
            {"证券名称": "A", "市值": "500", "币种": "人民币"},
        ])
        summary = _summary_report([{"资产市值": "500"}])
        checks = reconcile([detail, summary], {}, schema)
        mv_check = next(c for c in checks if c["check"] == "市值勾稽")
        assert mv_check["disposition"] == "real_pass"
