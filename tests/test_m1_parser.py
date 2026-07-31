"""Unit tests for scripts/m1_statement_parser.py — parsing & schema mapping."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from m1_statement_parser import (
    Schema,
    SchemaField,
    SchemaTable,
    ParsedDoc,
    ParsedTable,
    normalize_header,
    edit_distance,
    map_headers,
    best_schema_match,
    normalize_rows,
    extract_header_meta,
    parse_txt,
    _split_cells,
    _parse_markdown_tables,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_schema_table(name: str = "证券持仓明细", fields=None) -> SchemaTable:
    if fields is None:
        fields = [
            SchemaField("证券名称", ["证券名称", "股票名称", "名称"]),
            SchemaField("市值", ["市值", "证券市值", "最新市值"]),
            SchemaField("持仓数量", ["持仓数量", "数量", "股数"]),
            SchemaField("币种", ["币种", "货币"]),
        ]
    return SchemaTable(name, "grid", [], fields)


def _make_schema() -> Schema:
    detail = _make_schema_table()
    meta_table = SchemaTable("表头信息", "kv", [], [
        SchemaField("客户名称", ["客户名称", "户名"]),
        SchemaField("资产账号", ["资产账号", "资金账号", "交易帐号"]),
        SchemaField("统计日期", ["统计日期", "对账日期"]),
    ])
    return Schema([detail, meta_table], {
        "客户名称": ["客户名称", "户名"],
        "资产账号": ["资产账号", "资金账号", "交易帐号"],
        "统计日期": ["统计日期", "对账日期"],
    })


# ---------------------------------------------------------------------------
# normalize_header
# ---------------------------------------------------------------------------

class TestNormalizeHeader:
    def test_strips_whitespace_and_punct(self):
        assert normalize_header("  证券名称（元） ") == "证券名称元"

    def test_lowercases_ascii(self):
        assert normalize_header("MarketValue") == "marketvalue"

    def test_none_returns_empty(self):
        assert normalize_header(None) == ""


# ---------------------------------------------------------------------------
# edit_distance
# ---------------------------------------------------------------------------

class TestEditDistance:
    def test_identical(self):
        assert edit_distance("abc", "abc") == 0

    def test_one_insert(self):
        assert edit_distance("abc", "abcd") == 1

    def test_empty(self):
        assert edit_distance("", "xyz") == 3


# ---------------------------------------------------------------------------
# _split_cells
# ---------------------------------------------------------------------------

class TestSplitCells:
    def test_basic(self):
        assert _split_cells("  证券名称   市值   数量  ") == ["证券名称", "市值", "数量"]

    def test_empty_line(self):
        assert _split_cells("   ") == []


# ---------------------------------------------------------------------------
# map_headers / schema matching
# ---------------------------------------------------------------------------

class TestSchemaMatching:
    def test_exact_synonym_mapping(self):
        st = _make_schema_table()
        mapping, unmapped = map_headers(["股票名称", "最新市值", "数量"], st)
        assert mapping["证券名称"] == "股票名称"
        assert mapping["市值"] == "最新市值"
        assert mapping["持仓数量"] == "数量"
        assert unmapped == []

    def test_unmapped_columns_tracked(self):
        st = _make_schema_table()
        mapping, unmapped = map_headers(["证券名称", "未知列X"], st)
        assert "证券名称" in mapping
        assert "未知列X" in unmapped

    def test_best_schema_match_picks_highest_hits(self):
        schema = _make_schema()
        result = best_schema_match(["证券名称", "市值", "持仓数量", "币种"], schema)
        assert result.schema_table == "证券持仓明细"
        assert result.hits == 4


# ---------------------------------------------------------------------------
# normalize_rows
# ---------------------------------------------------------------------------

class TestNormalizeRows:
    def test_maps_values_by_standard_fields(self):
        mapping = {"证券名称": "名称", "市值": "市值(元)"}
        headers = ["名称", "市值(元)", "备注"]
        rows = [["平安银行", "12345.67", "正常"]]
        result = normalize_rows(rows, mapping, headers)
        assert len(result) == 1
        assert result[0]["证券名称"] == "平安银行"
        assert result[0]["市值"] == "12345.67"


# ---------------------------------------------------------------------------
# parse_txt
# ---------------------------------------------------------------------------

class TestParseTxt:
    def test_basic_table(self):
        content = (
            "客户名称: 测试客户\n"
            "资产账号: 123456\n"
            "\n"
            "证券名称 市值 数量\n"
            "----------\n"
            "平安银行 100.00 200\n"
            "招商银行 200.00 300\n"
            "----------\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            doc = parse_txt(path)
            assert doc.ok
            assert len(doc.tables) == 1
            assert doc.tables[0].headers == ["证券名称", "市值", "数量"]
            assert len(doc.tables[0].rows) == 2
        finally:
            os.unlink(path)

    def test_empty_content(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("")
            path = fh.name
        try:
            doc = parse_txt(path)
            assert doc.ok
            assert len(doc.tables) == 0
        finally:
            os.unlink(path)

    def test_header_meta_extraction(self):
        content = "客户名称: 张三  资产账号: 888888\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            doc = parse_txt(path)
            schema = _make_schema()
            meta = extract_header_meta(doc.text, schema)
            assert meta.get("客户名称") == "张三"
            assert meta.get("资产账号") == "888888"
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# _parse_markdown_tables
# ---------------------------------------------------------------------------

class TestParseMarkdownTables:
    def test_pipe_table(self):
        md = (
            "| 证券名称 | 市值 |\n"
            "| --- | --- |\n"
            "| 平安银行 | 100 |\n"
            "| 招商银行 | 200 |\n"
        )
        tables = _parse_markdown_tables(md)
        assert len(tables) == 1
        assert tables[0].headers == ["证券名称", "市值"]
        assert len(tables[0].rows) == 2

    def test_no_tables(self):
        assert _parse_markdown_tables("just plain text\nno tables here") == []
