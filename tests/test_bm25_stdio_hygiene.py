"""P3 regression: bm25_retriever must not print to stdout.

These bare prints sit on the MCP stdio import chain (mcp_server/server.py ->
biz.rag_service -> tools.bm25_retriever); a stdout write during a JSON-RPC
request would corrupt the stdio frame. The expected behavior is that all
diagnostics go to stderr.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tools.bm25_retriever as bm25  # noqa: E402


def test_no_bare_stdout_print_statements():
    src = open(bm25.__file__).read()
    # Any print not routed to stderr would break the MCP stdio boundary.
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("print(") and "file=sys.stderr" not in stripped:
            raise AssertionError(f"bare stdout print in bm25_retriever.py: {stripped}")
