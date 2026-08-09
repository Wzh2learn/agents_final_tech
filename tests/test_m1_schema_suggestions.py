"""Tests for M1 schema-suggestion endpoints (选择题体验 场景 A, docs/26).

Covers: GET suggestions, apply (success / retarget / no-match / gate-fail /
zero-merge), reject, and admin-token enforcement. The regression-gate
subprocess and the schema-merge helper are mocked so tests never touch the
real config/ files or run the scenario1 gate.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fastapi.testclient import TestClient

try:
    from main import app
    client = TestClient(app)
    HAS_APP = True
except Exception:
    HAS_APP = False

pytestmark = pytest.mark.skipif(not HAS_APP, reason="FastAPI app not importable")

_TEST_SCHEMA = {
    "tables": [
        {
            "table_name": "交易对账单",
            "layout": "grid",
            "header_region_keywords": ["交易"],
            "fields": [
                {"standard": "分红方式", "synonyms": ["分红方式"]},
                {"standard": "券商", "synonyms": ["券商"]},
                {"standard": "产品名称", "synonyms": ["产品名称"]},
            ],
        }
    ],
}


def _sg(raw, std, table="交易对账单", conf="high"):
    return {
        "raw_column": raw, "standard_field": std, "table": table,
        "confidence": conf, "reason": "test", "sample": "sample_x.pdf",
        "count": 1, "first_seen": "2026-08-10 00:00", "last_seen": "2026-08-10 00:00",
    }


class _FakeApplyMod:
    """Stands in for scripts/m1_apply_schema_suggestions.py."""

    def __init__(self, added=1, skips=None):
        self.added = added
        self.skips = skips if skips is not None else []
        self.calls = []

    def merge_into_schema(self, schema_path, suggestions, out_path):
        self.calls.append({"schema_path": schema_path,
                           "suggestions": json.loads(json.dumps(suggestions)),
                           "out_path": out_path})
        with open(schema_path, encoding="utf-8") as fh:
            schema = json.load(fh)
        for sg in suggestions:
            for t in schema.get("tables", []):
                if t["table_name"] != sg.get("table"):
                    continue
                for f in t.get("fields", []):
                    if f.get("standard") == sg.get("standard_field"):
                        f.setdefault("synonyms", []).append(sg["raw_column"])
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(schema, fh, ensure_ascii=False)
        return self.added, self.skips


class _FakeProc:
    def __init__(self, stdout):
        self.stdout = stdout
        self.stderr = ""


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    import m1_statement_parser as parser_mod
    from web.routers import m1 as m1_router_mod

    test_config = tmp_path / "config"
    test_config.mkdir()
    schema_file = test_config / "m1_table_schema.json"
    schema_file.write_text(json.dumps(_TEST_SCHEMA, ensure_ascii=False),
                           encoding="utf-8")

    monkeypatch.setattr(parser_mod, "LOCAL_SCHEMA", str(schema_file))
    monkeypatch.setattr(m1_router_mod, "_parser_mod", parser_mod)
    monkeypatch.setattr(m1_router_mod, "_ADMIN_TOKEN", None)

    fake = _FakeApplyMod()
    monkeypatch.setattr(m1_router_mod, "_apply_mod", fake)
    monkeypatch.setattr(m1_router_mod.subprocess, "run",
                        lambda *a, **k: _FakeProc("[scenario1-regression] PASS\n"))

    yield {"schema_file": schema_file, "router": m1_router_mod, "fake": fake,
           "sugg_file": test_config / "schema_suggestions.json"}


def _seed_suggestions(fixture, suggestions):
    fixture["sugg_file"].write_text(
        json.dumps({"suggestions": suggestions, "applied": [], "rejected": []},
                   ensure_ascii=False), encoding="utf-8")


def _read_sugg(fixture):
    return json.loads(fixture["sugg_file"].read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------
class TestGetSuggestions:
    def test_empty_when_no_file(self, _setup):
        resp = client.get("/api/m1/schema-suggestions")
        assert resp.status_code == 200
        assert resp.json() == {"suggestions": [], "applied_count": 0,
                               "rejected_count": 0}

    def test_lists_pending(self, _setup):
        _seed_suggestions(_setup, [_sg("销售机构", "券商"),
                                   _sg("产品份额①", "合计金额", conf="low")])
        resp = client.get("/api/m1/schema-suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["raw_column"] == "销售机构"


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
class TestApplySuggestions:
    def test_apply_success(self, _setup):
        _seed_suggestions(_setup, [_sg("销售机构", "券商")])
        resp = client.post("/api/m1/schema-suggestions/apply", json={
            "items": [{"raw_column": "销售机构", "table": "交易对账单",
                       "standard_field": "券商"}]})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["applied"] == 1 and body["added_synonyms"] == 1
        # merged synonym landed in the schema
        schema = json.loads(_setup["schema_file"].read_text(encoding="utf-8"))
        fields = schema["tables"][0]["fields"]
        assert "销售机构" in next(f for f in fields if f["standard"] == "券商")["synonyms"]
        # suggestion moved to applied
        data = _read_sugg(_setup)
        assert data["suggestions"] == []
        assert len(data["applied"]) == 1 and data["applied"][0]["raw_column"] == "销售机构"

    def test_apply_user_retargeted_field(self, _setup):
        """UI allows re-selecting the target field; apply must honor it."""
        _seed_suggestions(_setup, [_sg("产品代码", "券商", conf="low")])
        resp = client.post("/api/m1/schema-suggestions/apply", json={
            "items": [{"raw_column": "产品代码", "table": "交易对账单",
                       "standard_field": "产品名称"}]})  # user retargets
        assert resp.status_code == 200, resp.text
        calls = _setup["fake"].calls
        assert calls and calls[0]["suggestions"][0]["standard_field"] == "产品名称"
        schema = json.loads(_setup["schema_file"].read_text(encoding="utf-8"))
        fields = schema["tables"][0]["fields"]
        assert "产品代码" in next(f for f in fields if f["standard"] == "产品名称")["synonyms"]

    def test_apply_no_match_404(self, _setup):
        _seed_suggestions(_setup, [_sg("销售机构", "券商")])
        resp = client.post("/api/m1/schema-suggestions/apply", json={
            "items": [{"raw_column": "不存在列", "table": "交易对账单",
                       "standard_field": "券商"}]})
        assert resp.status_code == 404

    def test_apply_gate_fail_rolls_back(self, _setup, monkeypatch):
        _seed_suggestions(_setup, [_sg("销售机构", "券商")])
        before = _setup["schema_file"].read_text(encoding="utf-8")
        monkeypatch.setattr(_setup["router"].subprocess, "run",
                            lambda *a, **k: _FakeProc("[scenario1-regression] FAIL\n"))
        resp = client.post("/api/m1/schema-suggestions/apply", json={
            "items": [{"raw_column": "销售机构", "table": "交易对账单",
                       "standard_field": "券商"}]})
        assert resp.status_code == 409
        assert "rolled back" in resp.json()["detail"]
        # schema restored byte-for-byte, suggestion still pending
        assert _setup["schema_file"].read_text(encoding="utf-8") == before
        data = _read_sugg(_setup)
        assert len(data["suggestions"]) == 1 and data["applied"] == []

    def test_apply_zero_merge_409(self, _setup, monkeypatch):
        _seed_suggestions(_setup, [_sg("销售机构", "券商")])
        before = _setup["schema_file"].read_text(encoding="utf-8")
        monkeypatch.setattr(_setup["router"], "_apply_mod",
                            _FakeApplyMod(added=0, skips=["synonym already exists"]))
        resp = client.post("/api/m1/schema-suggestions/apply", json={
            "items": [{"raw_column": "销售机构", "table": "交易对账单",
                       "standard_field": "券商"}]})
        assert resp.status_code == 409
        assert _setup["schema_file"].read_text(encoding="utf-8") == before
        assert len(_read_sugg(_setup)["suggestions"]) == 1


# ---------------------------------------------------------------------------
# reject
# ---------------------------------------------------------------------------
class TestRejectSuggestions:
    def test_reject_moves_to_rejected(self, _setup):
        _seed_suggestions(_setup, [_sg("产品份额①", "合计金额", conf="low"),
                                   _sg("销售机构", "券商")])
        before_schema = _setup["schema_file"].read_text(encoding="utf-8")
        resp = client.post("/api/m1/schema-suggestions/reject", json={
            "items": [{"raw_column": "产品份额①", "table": "交易对账单",
                       "standard_field": "合计金额"}]})
        assert resp.status_code == 200
        assert resp.json()["rejected"] == 1
        data = _read_sugg(_setup)
        assert [s["raw_column"] for s in data["suggestions"]] == ["销售机构"]
        assert [s["raw_column"] for s in data["rejected"]] == ["产品份额①"]
        # reject never touches the schema
        assert _setup["schema_file"].read_text(encoding="utf-8") == before_schema

    def test_reject_no_match_zero(self, _setup):
        resp = client.post("/api/m1/schema-suggestions/reject", json={
            "items": [{"raw_column": "x", "table": "y", "standard_field": "z"}]})
        assert resp.status_code == 200
        assert resp.json()["rejected"] == 0


# ---------------------------------------------------------------------------
# admin token
# ---------------------------------------------------------------------------
class TestAdminGate:
    def test_apply_requires_token_when_set(self, _setup, monkeypatch):
        monkeypatch.setattr(_setup["router"], "_ADMIN_TOKEN", "sekrit")
        _seed_suggestions(_setup, [_sg("销售机构", "券商")])
        resp = client.post("/api/m1/schema-suggestions/apply", json={
            "items": [{"raw_column": "销售机构", "table": "交易对账单",
                       "standard_field": "券商"}]})
        assert resp.status_code == 401
        resp = client.post("/api/m1/schema-suggestions/apply",
                           headers={"X-Admin-Token": "sekrit"},
                           json={"items": [{"raw_column": "销售机构",
                                            "table": "交易对账单",
                                            "standard_field": "券商"}]})
        assert resp.status_code == 200
