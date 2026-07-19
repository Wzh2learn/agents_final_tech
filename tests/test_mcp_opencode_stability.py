from __future__ import annotations

import sys

import pytest

from scripts import run_mcp_opencode_stability
from scripts.run_mcp_opencode_stability import normalized_json_status, run_once


def test_successful_expected_tool_event_passes():
    output = (
        '{"type":"tool_use","part":{"type":"tool","tool":'
        '"jinrong-rag_knowledge_list_collections","state":{"status":"completed"}}}'
    )

    assert normalized_json_status(output) == "passed"


def test_expected_tool_error_event_is_not_a_pass():
    output = (
        '{"type":"tool_use","part":{"type":"tool","tool":'
        '"jinrong-rag_knowledge_list_collections","state":{"status":"error",'
        '"error":"private detail"}}}'
    )

    assert normalized_json_status(output) == "tool_error"


def test_malformed_json_event_is_reported_without_retaining_output():
    assert normalized_json_status("not-json private-name") == "malformed"


def test_run_once_persists_only_sanitized_status_and_digest():
    event = (
        '{"type":"tool_use","part":{"type":"tool","tool":'
        '"jinrong-rag_knowledge_list_collections","state":{"status":"completed"}}}'
    )
    record = run_once([sys.executable, "-c", f"print({event!r})"], 1)
    assert record["status"] == "passed"
    assert set(record) == {"elapsed_sec", "status", "output_sha256"}
    assert "private-name" not in str(record)


def test_timeout_has_a_normalized_status():
    record = run_once([sys.executable, "-c", "import time; time.sleep(2)"], 1)

    assert record["status"] == "timed_out"
    assert set(record) == {"elapsed_sec", "status", "output_sha256"}


def test_parent_exit_does_not_wait_for_child_inherited_output_descriptor():
    event = (
        '{"type":"tool_use","part":{"type":"tool","tool":'
        '"jinrong-rag_knowledge_list_collections","state":{"status":"completed"}}}'
    )
    script = (
        "import os, sys, time; "
        "child = os.fork(); "
        "child == 0 and (time.sleep(10) or os._exit(0)); "
        f"print({event!r}, flush=True); "
        "os._exit(0)"
    )

    record = run_once([sys.executable, "-c", script], 1)

    assert record["status"] == "passed"
    assert record["elapsed_sec"] < 2


def test_dry_run_does_not_require_output_dir(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run_mcp_opencode_stability.py", "--dry-run"])

    run_mcp_opencode_stability.main()

    assert '"valid": true' in capsys.readouterr().out


def test_live_run_requires_output_dir_before_environment_check(monkeypatch):
    monkeypatch.delenv("PGDATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["run_mcp_opencode_stability.py"])

    with pytest.raises(SystemExit, match="--output-dir is required for a live stability run"):
        run_mcp_opencode_stability.main()
