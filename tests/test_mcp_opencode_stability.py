from __future__ import annotations

import sys

from scripts.run_mcp_opencode_stability import run_once


def test_run_once_persists_only_sanitized_status_and_digest():
    record = run_once([sys.executable, "-c", "print('MCP_OK private-name')"], 1)
    assert record["status"] == "passed"
    assert set(record) == {"elapsed_sec", "status", "output_sha256"}
    assert "private-name" not in str(record)
