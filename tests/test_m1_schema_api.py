"""Tests for M1 Schema CRUD API (Phase 2).

Covers: GET/PUT schema, add/delete tables and fields, hot-reload,
and admin token enforcement.
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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
_TEST_SCHEMA = {
    "_comment": "test schema",
    "tables": [
        {
            "table_name": "测试表",
            "layout": "grid",
            "header_region_keywords": ["测试"],
            "fields": [
                {"standard": "证券名称", "synonyms": ["证券名称", "股票名称"]},
                {"standard": "市值", "synonyms": ["市值", "总市值"]},
            ],
        }
    ],
}

_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
_LOCAL_SCHEMA_PATH = os.path.join(_CONFIG_DIR, "m1_table_schema.json")


@pytest.fixture(autouse=True)
def _setup_schema(tmp_path, monkeypatch):
    """Write a test schema to config/ and patch parser paths."""
    import m1_statement_parser as parser_mod

    # Use a temp dir as config/ so we never touch the real config/
    test_config = tmp_path / "config"
    test_config.mkdir()
    test_schema_file = test_config / "m1_table_schema.json"
    test_schema_file.write_text(json.dumps(_TEST_SCHEMA, ensure_ascii=False), encoding="utf-8")

    # Patch the parser module's LOCAL_SCHEMA to point to our temp file
    monkeypatch.setattr(parser_mod, "LOCAL_SCHEMA", str(test_schema_file))

    # Also patch the router module's cached parser reference if needed
    from web.routers import m1 as m1_router_mod
    # Force re-read by clearing cached parser
    monkeypatch.setattr(m1_router_mod, "_parser_mod", parser_mod)
    # Patch admin token to None (unprotected) by default
    monkeypatch.setattr(m1_router_mod, "_ADMIN_TOKEN", None)

    yield test_schema_file


# ---------------------------------------------------------------------------
# 1. GET /api/m1/schema
# ---------------------------------------------------------------------------
class TestGetSchema:
    def test_get_schema(self):
        resp = client.get("/api/m1/schema")
        assert resp.status_code == 200
        data = resp.json()
        assert "tables" in data
        assert len(data["tables"]) >= 1
        assert data["tables"][0]["table_name"] == "测试表"


# ---------------------------------------------------------------------------
# 2. PUT /api/m1/schema (valid)
# ---------------------------------------------------------------------------
class TestPutSchemaValid:
    def test_put_schema_valid(self, _setup_schema):
        new_schema = {
            "tables": [
                {
                    "table_name": "新表",
                    "layout": "kv",
                    "header_region_keywords": [],
                    "fields": [{"standard": "字段A", "synonyms": ["A"]}],
                }
            ]
        }
        resp = client.put("/api/m1/schema", json=new_schema)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        # Verify persisted
        saved = json.loads(_setup_schema.read_text(encoding="utf-8"))
        assert saved["tables"][0]["table_name"] == "新表"


# ---------------------------------------------------------------------------
# 3. PUT /api/m1/schema (invalid)
# ---------------------------------------------------------------------------
class TestPutSchemaInvalid:
    def test_put_schema_invalid_structure(self):
        resp = client.put("/api/m1/schema", json={"bad": "data"})
        assert resp.status_code == 422

    def test_put_schema_invalid_json(self):
        resp = client.put(
            "/api/m1/schema",
            content=b"not json{{{",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. POST /api/m1/schema/tables
# ---------------------------------------------------------------------------
class TestAddTable:
    def test_add_table(self, _setup_schema):
        resp = client.post("/api/m1/schema/tables", json={
            "table_name": "新增表",
            "layout": "grid",
            "header_region_keywords": ["关键词"],
            "fields": [{"standard": "金额", "synonyms": ["金额", "总额"]}],
        })
        assert resp.status_code == 201
        saved = json.loads(_setup_schema.read_text(encoding="utf-8"))
        names = [t["table_name"] for t in saved["tables"]]
        assert "新增表" in names

    def test_add_table_duplicate(self):
        resp = client.post("/api/m1/schema/tables", json={
            "table_name": "测试表",
            "layout": "grid",
            "header_region_keywords": [],
            "fields": [],
        })
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# 5. POST /api/m1/schema/tables/{name}/fields
# ---------------------------------------------------------------------------
class TestAddField:
    def test_add_field(self, _setup_schema):
        resp = client.post("/api/m1/schema/tables/测试表/fields", json={
            "standard": "持仓数量",
            "synonyms": ["持仓数量", "数量"],
        })
        assert resp.status_code == 201
        saved = json.loads(_setup_schema.read_text(encoding="utf-8"))
        table = next(t for t in saved["tables"] if t["table_name"] == "测试表")
        standards = [f["standard"] for f in table["fields"]]
        assert "持仓数量" in standards

    def test_add_field_duplicate(self):
        resp = client.post("/api/m1/schema/tables/测试表/fields", json={
            "standard": "证券名称",
            "synonyms": [],
        })
        assert resp.status_code == 409

    def test_add_field_table_not_found(self):
        resp = client.post("/api/m1/schema/tables/不存在/fields", json={
            "standard": "X",
            "synonyms": [],
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 6. DELETE /api/m1/schema/tables/{name}/fields/{standard}
# ---------------------------------------------------------------------------
class TestDeleteField:
    def test_delete_field(self, _setup_schema):
        resp = client.delete("/api/m1/schema/tables/测试表/fields/市值")
        assert resp.status_code == 200
        saved = json.loads(_setup_schema.read_text(encoding="utf-8"))
        table = next(t for t in saved["tables"] if t["table_name"] == "测试表")
        standards = [f["standard"] for f in table["fields"]]
        assert "市值" not in standards

    def test_delete_field_not_found(self):
        resp = client.delete("/api/m1/schema/tables/测试表/fields/不存在字段")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 7. DELETE /api/m1/schema/tables/{name}
# ---------------------------------------------------------------------------
class TestDeleteTable:
    def test_delete_table(self, _setup_schema):
        resp = client.delete("/api/m1/schema/tables/测试表")
        assert resp.status_code == 200
        saved = json.loads(_setup_schema.read_text(encoding="utf-8"))
        names = [t["table_name"] for t in saved["tables"]]
        assert "测试表" not in names

    def test_delete_table_not_found(self):
        resp = client.delete("/api/m1/schema/tables/不存在")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 8. Hot reload: synonym added via API is used in next parse
# ---------------------------------------------------------------------------
class TestHotReload:
    def test_hot_reload(self, _setup_schema):
        """Add a synonym via API, then verify Schema.load picks it up."""
        import m1_statement_parser as parser_mod

        # Add a new synonym "测试近义词" for "证券名称"
        resp = client.post("/api/m1/schema/tables/测试表/fields", json={
            "standard": "测试字段",
            "synonyms": ["测试近义词"],
        })
        assert resp.status_code == 201

        # Now load schema fresh (simulating next parse)
        schema = parser_mod.Schema.load(str(_setup_schema))
        table = next(t for t in schema.tables if t.table_name == "测试表")
        field = next(f for f in table.fields if f.standard == "测试字段")
        assert "测试近义词" in field.synonyms

        # Verify mapping works: normalize_header("测试近义词") should match
        from m1_statement_parser import normalize_header, _best_field_for_header
        header_norm = normalize_header("测试近义词")
        result = _best_field_for_header(header_norm, table.fields)
        assert result is not None
        assert result[2] == "测试字段"  # tuple is (score, syn_len, standard)


# ---------------------------------------------------------------------------
# 9. Admin token enforcement
# ---------------------------------------------------------------------------
class TestAdminToken:
    def test_admin_token_required(self, _setup_schema, monkeypatch):
        from web.routers import m1 as m1_router_mod
        monkeypatch.setattr(m1_router_mod, "_ADMIN_TOKEN", "secret123")

        # Write without token -> 401
        resp = client.put("/api/m1/schema", json={"tables": []})
        assert resp.status_code == 401

        # Write with wrong token -> 401
        resp = client.put(
            "/api/m1/schema",
            json={"tables": []},
            headers={"X-Admin-Token": "wrong"},
        )
        assert resp.status_code == 401

        # Write with correct token -> 200
        resp = client.put(
            "/api/m1/schema",
            json={"tables": [{"table_name": "T", "layout": "grid", "header_region_keywords": [], "fields": []}]},
            headers={"X-Admin-Token": "secret123"},
        )
        assert resp.status_code == 200

    def test_get_schema_no_token_needed(self, _setup_schema, monkeypatch):
        from web.routers import m1 as m1_router_mod
        monkeypatch.setattr(m1_router_mod, "_ADMIN_TOKEN", "secret123")

        # GET should work without token
        resp = client.get("/api/m1/schema")
        assert resp.status_code == 200
