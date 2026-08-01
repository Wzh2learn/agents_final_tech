"""Tests for Bearer token auth middleware.

Verifies:
1. No token required when M1_API_TOKEN env is not set.
2. Valid token passes.
3. Invalid/missing token returns 401.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture()
def app_no_token(monkeypatch):
    """App with M1_API_TOKEN unset."""
    monkeypatch.delenv("M1_API_TOKEN", raising=False)
    # Re-import to pick up env change
    import importlib
    import web.middleware as mw
    importlib.reload(mw)
    from main import app
    return app


@pytest.fixture()
def app_with_token(monkeypatch):
    """App with M1_API_TOKEN=test_secret."""
    monkeypatch.setenv("M1_API_TOKEN", "test_secret")
    import importlib
    import web.middleware as mw
    importlib.reload(mw)
    # Need fresh app to pick up new middleware token
    from fastapi import FastAPI
    from web.middleware import BearerAuthMiddleware
    from starlette.testclient import TestClient

    test_app = FastAPI()
    test_app.add_middleware(BearerAuthMiddleware, token="test_secret")

    @test_app.get("/health")
    async def health():
        return {"status": "ok"}

    @test_app.get("/api/test")
    async def api_test():
        return {"data": "secret"}

    return test_app


class TestAuthMiddleware:
    """Auth middleware behavior."""

    def test_no_token_when_env_not_set(self, app_no_token):
        """Requests pass without token when M1_API_TOKEN is not set."""
        from starlette.testclient import TestClient
        client = TestClient(app_no_token)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_valid_token(self, app_with_token):
        """Request with correct Bearer token passes."""
        from starlette.testclient import TestClient
        client = TestClient(app_with_token)
        resp = client.get("/api/test", headers={"Authorization": "Bearer test_secret"})
        assert resp.status_code == 200
        assert resp.json()["data"] == "secret"

    def test_invalid_token(self, app_with_token):
        """Request with wrong token returns 401."""
        from starlette.testclient import TestClient
        client = TestClient(app_with_token)
        resp = client.get("/api/test", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "Unauthorized"

    def test_missing_token(self, app_with_token):
        """Request without Authorization header returns 401."""
        from starlette.testclient import TestClient
        client = TestClient(app_with_token)
        resp = client.get("/api/test")
        assert resp.status_code == 401

    def test_exempt_paths_no_token_needed(self, app_with_token):
        """Exempt paths (/health) don't require token."""
        from starlette.testclient import TestClient
        client = TestClient(app_with_token)
        resp = client.get("/health")
        assert resp.status_code == 200
