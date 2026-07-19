from __future__ import annotations

import sys

import pytest

from scripts import run_mcp_opencode_stability
from scripts.run_mcp_opencode_stability import run_once


def test_run_once_persists_only_sanitized_status_and_digest():
    record = run_once([sys.executable, "-c", "print('MCP_OK private-name')"], 1)
    assert record["status"] == "passed"
    assert set(record) == {"elapsed_sec", "status", "output_sha256"}
    assert "private-name" not in str(record)


def test_dry_run_does_not_require_output_dir(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run_mcp_opencode_stability.py", "--dry-run"])

    run_mcp_opencode_stability.main()

    assert '"valid": true' in capsys.readouterr().out


def test_live_run_requires_output_dir_before_environment_check(monkeypatch):
    monkeypatch.delenv("PGDATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["run_mcp_opencode_stability.py"])

    with pytest.raises(SystemExit, match="--output-dir is required for a live stability run"):
        run_mcp_opencode_stability.main()
