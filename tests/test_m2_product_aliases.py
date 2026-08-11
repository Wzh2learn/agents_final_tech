"""Q2 (2026-08-12): 甲方映射表确定性别名表 — resolver + compare 链路测试。

新测试文件 (不碰冻结的 test_m1_service.py)。覆盖:
- normalize 口径 (NFKC/空白)
- resolve_product_query 三态 (exact / normalized / unchanged)
- _query_collection_chunks 的 精确→别名→LIKE 三级链 (mock DB)
- 别名表缺失时优雅降级
"""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import biz.m2_service as m2

FAKE_ALIASES = {
    "products": {
        "MM-A一号": {"canonical": "MM-A一号", "aliases": ["MM-A一号"],
                  "position_count": 2, "security_codes": ["000001"]},
        "测试产品": {"canonical": "测试产品（全称）", "aliases": ["测试产品", "测试产品（全称）"],
                  "position_count": 1, "security_codes": []},
    },
    "securities": {"000001": {"name": "平安银行", "holder_count": 1}},
    "issuers": ["平安银行"],
}


def _set_cache(monkeypatch, value):
    monkeypatch.setattr(m2, "_PRODUCT_ALIASES_CACHE", value)


class TestNormalize:
    def test_nfkc_and_whitespace(self):
        assert m2._normalize_product("ＭＭ-Ａ一号") == "MM-A一号"
        assert m2._normalize_product(" MM-A 一号 ") == "MM-A一号"

    def test_empty(self):
        assert m2._normalize_product("") == ""
        assert m2._normalize_product(None) == ""


class TestResolveProductQuery:
    def test_exact(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        assert m2.resolve_product_query("MM-A一号") == ("MM-A一号", "alias-exact")

    def test_normalized_variant(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        name, via = m2.resolve_product_query("测试产品")
        assert name == "测试产品（全称）"
        assert via == "alias-exact"  # 归一化键命中 products 表

    def test_alias_member(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        name, via = m2.resolve_product_query("测试产品（全称）")
        assert name == "测试产品（全称）"
        assert via in ("alias-exact", "alias-normalized")

    def test_miss_unchanged(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        assert m2.resolve_product_query("不存在的产品X") == ("不存在的产品X", "unchanged")

    def test_empty_table_graceful(self, monkeypatch):
        _set_cache(monkeypatch, {})
        assert m2.resolve_product_query("MM-A一号") == ("MM-A一号", "unchanged")


class TestQueryChainAliasStep:
    """精确 miss → 别名解析命中 → 不再走 LIKE。"""

    def _mock_db(self, results_by_call):
        db = MagicMock()
        chain = db.query.return_value.join.return_value
        chain.filter.return_value = chain
        chain.all.side_effect = results_by_call
        return db

    def test_alias_hit_between_exact_and_like(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        hit_row = [("doc-text", {"product_name": "测试产品（全称）"})]
        db = self._mock_db([[], hit_row])  # exact 空, 别名解析命中
        with patch.object(m2, "_get_db_session", return_value=db), \
             patch.object(m2, "collection_name", return_value="m1_parsed_statements"):
            rows = m2._query_collection_chunks(product_name="测试产品")
        assert len(rows) == 1
        assert rows[0]["metadata"]["product_name"] == "测试产品（全称）"
        # exact + alias = 2 次查询 (未走 LIKE 第 3 次)
        assert db.query.return_value.join.return_value.all.call_count == 2

    def test_fallback_like_when_alias_misses(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        fuzzy_row = [("doc2", {"product_name": "嘉兴民安投资合伙企业（有限合伙）"})]
        db = self._mock_db([[], fuzzy_row])  # exact 空; 别名 unchanged → LIKE
        with patch.object(m2, "_get_db_session", return_value=db), \
             patch.object(m2, "collection_name", return_value="m1_parsed_statements"):
            rows = m2._query_collection_chunks(product_name="嘉兴民安")
        assert len(rows) == 1
        assert db.query.return_value.join.return_value.all.call_count == 2

    def test_no_product_no_alias_call(self, monkeypatch):
        _set_cache(monkeypatch, FAKE_ALIASES)
        db = self._mock_db([[("d", {})]])
        with patch.object(m2, "_get_db_session", return_value=db), \
             patch.object(m2, "collection_name", return_value="m1_parsed_statements"):
            rows = m2._query_collection_chunks()
        assert len(rows) == 1


class TestAliasFileLoading:
    def test_missing_file_returns_empty(self, monkeypatch, tmp_path):
        monkeypatch.setattr(m2, "_PRODUCT_ALIASES_CACHE", None)
        monkeypatch.setattr(m2, "_product_aliases_path",
                            lambda: str(tmp_path / "nope.json"))
        assert m2._load_product_aliases() == {}
        # 缓存住空结果, 不反复读盘
        assert m2._PRODUCT_ALIASES_CACHE == {}

    def test_real_file_shape(self, monkeypatch):
        """仓库内真实别名表结构校验 (若存在)。"""
        monkeypatch.setattr(m2, "_PRODUCT_ALIASES_CACHE", None)
        path = m2._product_aliases_path()
        if not os.path.isfile(path):
            return
        data = m2._load_product_aliases()
        assert set(data) >= {"products", "securities", "issuers"}
        assert len(data["products"]) > 0
        for key, entry in list(data["products"].items())[:3]:
            assert entry.get("canonical")
            assert isinstance(entry.get("security_codes"), list)
