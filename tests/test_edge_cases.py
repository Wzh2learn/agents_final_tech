"""Fixture-driven edge case robustness tests for the M1 parse-file endpoint.

Each file in ``tests/fixtures/edge/`` is uploaded through the FastAPI
TestClient. The contract under test is *robustness*, not correctness:

- the endpoint must never return HTTP 500 (always 200),
- the body must always be valid JSON,
- ``status`` must always be present and be ``"success"`` or ``"error"``,
- error responses must carry a non-empty error message,
- success responses must report ``table_count >= 0``.

These tests complement ``test_m1_edge_cases.py`` (inline byte literals) by
exercising real on-disk fixtures with exotic encodings and corrupt content.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient

try:
    from main import app

    client = TestClient(app)
    HAS_APP = True
except Exception:  # pragma: no cover - environment without full app deps
    HAS_APP = False

pytestmark = pytest.mark.skipif(not HAS_APP, reason="FastAPI app not importable")

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "edge")

# Map fixture filename -> multipart content-type (best effort; the endpoint
# routes on file extension, so the MIME type is informational only).
CONTENT_TYPES = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
}


def _fixture_files():
    if not os.path.isdir(FIXTURE_DIR):
        return []
    return sorted(
        os.path.join(FIXTURE_DIR, fn)
        for fn in os.listdir(FIXTURE_DIR)
        if os.path.isfile(os.path.join(FIXTURE_DIR, fn))
    )


FIXTURES = _fixture_files()


@pytest.mark.parametrize("path", FIXTURES, ids=[os.path.basename(p) for p in FIXTURES])
def test_fixture_never_500(path):
    """Every edge fixture must be handled gracefully (no HTTP 500)."""
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()
    ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
    with open(path, "rb") as fh:
        payload = fh.read()

    resp = client.post(
        "/api/m1/parse-file",
        files={"file": (fname, payload, ctype)},
    )

    # 1. Never a server error.
    assert resp.status_code == 200, (
        f"{fname}: expected 200, got {resp.status_code}: {resp.text[:300]}"
    )

    # 2. Always valid JSON.
    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"{fname}: response is not valid JSON: {exc}")

    # 3. status field always present and well-formed.
    assert "status" in data, f"{fname}: missing 'status' field"
    assert data["status"] in ("success", "error"), (
        f"{fname}: unexpected status {data['status']!r}"
    )

    # 4/5. Per-status contract.
    if data["status"] == "error":
        err = data.get("error") or (data.get("result") or {}).get("error")
        assert err, f"{fname}: error response has empty error message"
    else:  # success
        result = data.get("result") or {}
        assert "table_count" in result, f"{fname}: success missing table_count"
        assert result["table_count"] >= 0, (
            f"{fname}: negative table_count {result['table_count']}"
        )


def test_fixture_directory_present():
    """Guard: the fixture directory must exist and contain the 10 cases."""
    assert os.path.isdir(FIXTURE_DIR), "tests/fixtures/edge/ missing"
    assert len(FIXTURES) >= 10, f"expected >=10 fixtures, found {len(FIXTURES)}"
