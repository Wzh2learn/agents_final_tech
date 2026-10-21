"""Test configuration: auto-skip tests with missing runtime dependencies."""
import os
import socket
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


FORBIDDEN_ENDPOINT_NODE_IDS = frozenset({
    "tests/test_vgmc_adversarial.py::test_adv_map_deterministic_nested_wrong_target",
    "tests/test_vgmc_collision_overlay.py::test_overlay_merge_adds_columns_and_entries",
    "tests/test_vgmc_collision_overlay.py::test_overlay_none_is_identity",
    "tests/test_vgmc_collision_overlay.py::test_real_overlay_artifact_loads",
})
FORBIDDEN_ENDPOINT_PORTS = frozenset({8004, 8006, 8007, 8008, 4096})


class ForbiddenEndpointConnection(RuntimeError):
    """Raised before a targeted test can attempt a forbidden endpoint connection."""


def _forbidden_port(address):
    if isinstance(address, tuple) and len(address) >= 2:
        try:
            return int(address[1])
        except (TypeError, ValueError):
            return None
    return None


def _reject_forbidden_port(address):
    port = _forbidden_port(address)
    if port in FORBIDDEN_ENDPOINT_PORTS:
        raise ForbiddenEndpointConnection(
            f"forbidden endpoint connection rejected by test isolation: port {port}"
        )


@pytest.fixture(autouse=True)
def hard_reject_forbidden_endpoints(request, monkeypatch):
    """Reject all five forbidden ports for only the four targeted acceptance tests."""
    if request.node.nodeid not in FORBIDDEN_ENDPOINT_NODE_IDS:
        return

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection

    def guarded_connect(sock, address):
        _reject_forbidden_port(address)
        return original_connect(sock, address)

    def guarded_connect_ex(sock, address):
        _reject_forbidden_port(address)
        return original_connect_ex(sock, address)

    def guarded_create_connection(address, *args, **kwargs):
        _reject_forbidden_port(address)
        return original_create_connection(address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)


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
    # D2 (2026-09-24, user ruling): integration-marked tests talk to live
    # production services. Concretely, test_m2_multiturn's TestMultiTurnIntegration
    # calls svc.ask() three times, which performs real RAG inference against the
    # production :8004 model endpoint. pytest.ini registers the `integration`
    # marker but sets no addopts, so those tests used to run on every full pytest
    # invocation -- meaning routine acceptance runs silently issued production
    # model calls and shared the stack Loop B monitors via qa_canary.
    #
    # They are deselected by default. The tests are NOT deleted; set
    # JINRONG_RUN_INTEGRATION=1 to run them, which requires explicit user
    # authorization plus a call budget and canary per decision 46 and
    # safety-gates section 4. Evidence and per-port strace attribution:
    # docs/experiments/2026-09-24_acceptance_worktree_fixture_gap_and_pytest_baseline.md
    if os.environ.get("JINRONG_RUN_INTEGRATION") != "1":
        deselected = [i for i in items if i.get_closest_marker("integration")]
        if deselected:
            items[:] = [i for i in items if not i.get_closest_marker("integration")]
            config.hook.pytest_deselected(items=deselected)

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


@pytest.fixture(autouse=True)
def _restore_socket_entrypoints():
    """Restore the socket connect entrypoints after every test.

    Several runners install a zero-connect guard by monkeypatching `socket.socket.connect`
    and `socket.create_connection`, and their CLI tests call `main()`, which installs the
    guard without restoring it. pytest collects files alphabetically, so a leak in an early
    file silently robs every later test of networking. Observed symptom: after adding
    tests/test_finqa_step_checkpoint_adapter.py, `test_health_embeddings_count.py` began
    skipping with "FastAPI server on :5050 not reachable" while :5050 answered HTTP 200 in
    0.13s, and full-suite wall time fell from ~130-167s to ~39s because endpoint probes
    raised instantly instead of waiting on timeouts.

    Restoring per test removes that hazard class for all seven guard-installing test modules
    without changing a single assertion: no test depends on the guard outliving itself.
    """
    original_connect = socket.socket.connect
    original_create = socket.create_connection
    yield
    socket.socket.connect = original_connect
    socket.create_connection = original_create
