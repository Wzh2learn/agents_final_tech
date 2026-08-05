#!/usr/bin/env python3
"""Purge OpenCode sidecar sessions.

Usage:
    ./venv/bin/python scripts/opencode_session_cleanup.py              # cap at OPENCODE_MAX_SESSIONS (default 50)
    ./venv/bin/python scripts/opencode_session_cleanup.py --max-keep 20
    ./venv/bin/python scripts/opencode_session_cleanup.py --purge-all
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request

BASE = os.environ.get("OPENCODE_SERVE_URL", "http://127.0.0.1:4096")


def req(method: str, path: str):
    r = urllib.request.Request(BASE + path, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=15) as resp:
        raw = resp.read().decode()
    try:
        return resp.status, json.loads(raw)
    except Exception:
        return resp.status, raw


def updated_key(s: dict) -> float:
    t = s.get("time") or {}
    return float(t.get("updated") or t.get("created") or 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--purge-all", action="store_true")
    ap.add_argument("--max-keep", type=int, default=int(os.environ.get("OPENCODE_MAX_SESSIONS", "50")))
    args = ap.parse_args()

    total_before = 0
    total_deleted = 0
    while True:
        _, sessions = req("GET", "/session")
        if not isinstance(sessions, list):
            raise SystemExit(f"unexpected list response: {sessions!r}")
        if not sessions:
            break
        total_before += len(sessions)
        # list endpoint is capped (~100); purge-all loops until empty,
        # cap mode only trims the visible page (enough for orphan control)
        doomed = sessions if args.purge_all else sorted(sessions, key=updated_key, reverse=True)[args.max_keep:]
        if not doomed:
            break
        for s in doomed:
            st, _ = req("DELETE", f"/session/{s.get('id')}")
            total_deleted += 1 if st < 300 else 0
        if not args.purge_all:
            break
    print(json.dumps({"before": total_before, "deleted": total_deleted, "kept": total_before - total_deleted}))


if __name__ == "__main__":
    main()
