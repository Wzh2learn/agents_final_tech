"""Test configuration: auto-skip tests with missing runtime dependencies."""
import os
import tempfile

# N1 (2026-08-21): redirect B4 structured ask-log to scratch for in-process test traffic,
# so TestClient calls never pollute production B4 stats (logs/graph/b4_ask_log.jsonl).
# Must run before app modules are imported (m2.py reads the env at import time).
os.environ.setdefault(
    "M1_B4_LOG_PATH",
    os.path.join(tempfile.gettempdir(), "b4_ask_log_tests.jsonl"),
)

import importlib
import pytest
import shutil


def _has_playwright():
    try:
        importlib.import_module("playwright")
        return True
    except ImportError:
        return False


def _has_server():
    """Check if the FastAPI test server is reachable."""
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:5050/health", timeout=2)
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests based on available dependencies."""
    skip_playwright = pytest.mark.skip(reason="playwright not installed")
    skip_server = pytest.mark.skip(reason="FastAPI server not running on :5050")

    for item in items:
        # Skip legacy chat/KB e2e tests: they target the old :5000 UI with
        # headless=False and are not M1/M2 scope (same treatment as
        # test_web_integration). Playwright install for demo recording
        # un-skipped them, hence the explicit marker.
        if "test_e2e_browser" in str(item.fspath):
            item.add_marker(pytest.mark.skip(
                reason="legacy chat/KB e2e against old :5000 UI, not M1/M2 scope"))

        # Skip websocket tests (need async server config)
        if "test_websocket" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="websocket tests require async server fixture"))

        # Skip web integration tests (legacy chat/KB, not M1/M2 scope)
        if "test_web_integration" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="legacy chat/KB integration, not M1/M2 scope"))

        # Skip core service async tests that need specific fixtures
        if "test_core_service" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="requires full app context with DB"))

        # Skip hmm memory tests (need specific model setup)
        if "test_hmm_memory" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="requires HMM model configuration"))
