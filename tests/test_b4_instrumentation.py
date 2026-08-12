"""S1/S2 仪表与延迟修复资产测试 (2026-08-12)。

覆盖: B4 结构化日志函数、/no_think 契约、sidecar warm-up 脚本、
status.sh 一页健康、opencode vision MCP 样本目录 env。
新文件, 不碰冻结的 test_m1_service.py。
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def test_b4_log_writes_jsonl(tmp_path, monkeypatch):
    from web.routers import m2 as m2r

    logp = tmp_path / "b4.jsonl"
    monkeypatch.setattr(m2r, "_B4_LOG", str(logp))
    m2r._b4_log("agent", 1234, 2, False)
    m2r._b4_log("direct", 900, 1, True, status="error")
    lines = logp.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["route"] == "agent"
    assert rec["latency_ms"] == 1234
    assert rec["sources_count"] == 2
    assert rec["fell_back"] is False
    assert rec["status"] == "ok"
    assert "ts" in rec
    rec2 = json.loads(lines[1])
    assert rec2["route"] == "direct"
    assert rec2["fell_back"] is True
    assert rec2["status"] == "error"


def test_format_hint_has_no_think():
    from biz import opencode_adapter

    assert "/no_think" in opencode_adapter._FORMAT_HINT


def test_restart_sidecar_has_warmup():
    text = open(os.path.join(REPO, "scripts", "restart_opencode_sidecar.sh"),
                encoding="utf-8").read()
    assert "warm-up" in text
    assert "WARM_SID" in text


def test_status_script_covers_required_sections():
    p = os.path.join(REPO, "scripts", "graph", "status.sh")
    assert os.path.isfile(p)
    text = open(p, encoding="utf-8").read()
    for key in ("ls-remote", "verify-report.json", "b4_ask_log",
                "dispatch_log", "frozen_hashes", "docs_lint"):
        assert key in text, key


def test_opencode_vision_mcp_allowed_roots():
    d = json.load(open(os.path.join(REPO, "opencode.json"), encoding="utf-8"))
    vis = d["mcp"]["jinrong-vision"]
    roots = vis.get("env", {}).get("JINRONG_VISION_ALLOWED_ROOTS", "")
    assert "m1_samples" in roots
