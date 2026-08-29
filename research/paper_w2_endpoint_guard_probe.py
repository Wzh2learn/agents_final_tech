#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W2 端点护栏仪表自证（零模型调用, 零预算消耗）。

背景: E1.5 的 `endpoint_assert.ports_touched` 在缓存命中的复算跑里必然为空
（复算不建连接）, 于是"护栏是否真的在记录/拦截"无法从工件本身判断——空集既可能是
"没连过", 也可能是"护栏根本没生效"。本脚本用纯 TCP 层实验把这件事独立钉死:

  A 正向记录  : 允许端口 :8004 建连 -> 护栏必须把 8004 记进 PORTS_TOUCHED 且放行
  B 负向拦截  : :8006/:8008/:5050/:8100 -> 必须抛 ENDPOINT_GUARD, 且抛错发生在
                socket 系统调用之前（异常类型即证据, 不是 ConnectionRefused/Timeout）
  C 零外联证明: 临时监听套接字 accept 队列为空 -> 被拦连接根本没到达对端
  D 预算不变  : 本脚本只做 TCP 握手, 从不发 HTTP 请求 -> call_counter 必须不增

红线: 只连 127.0.0.1; 被拦端口在 raise 前不产生任何报文; 不向 :8006/:8008 发请求。
"""
from __future__ import annotations

import io
import json
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "src"))

import paper_w2_e15_full_judge as e15  # noqa: E402  复用同一份护栏实现, 不复制粘贴

OUT = ROOT / "logs" / "graph" / "eval" / "w2_endpoint_guard_probe.json"
PROTECTED = [8006, 8008, 5050, 8100]     # 卡红线点名的零触碰端口
TIMEOUT = 1.5


def _counter() -> int:
    return int(e15.ledger_load().get("call_counter", 0))


def probe_positive() -> dict:
    """A: 允许端口建连必须被记录且放行（不发送任何 HTTP 字节）。"""
    before = set(e15.PORTS_TOUCHED)
    err = None
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(TIMEOUT)
        sk.connect(("127.0.0.1", e15.ALLOWED_PORT))
        sk.close()
    except Exception as exc:  # noqa: BLE001
        err = "%s: %s" % (type(exc).__name__, exc)
    observed = sorted(set(e15.PORTS_TOUCHED) - before)
    return {"port": e15.ALLOWED_PORT, "connect_error": err,
            "ports_recorded_by_guard": observed,
            "pass": err is None and observed == [e15.ALLOWED_PORT]}


def probe_blocked() -> list:
    """B: 受保护端口必须在系统调用前被拦（异常类型 = 证据）。"""
    out = []
    for port in PROTECTED:
        viol_before = len(e15.ENDPOINT_VIOLATIONS)
        kind, msg, guard_raised = None, None, False
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.settimeout(TIMEOUT)
            sk.connect(("127.0.0.1", port))
            sk.close()
        except Exception as exc:  # noqa: BLE001
            kind = type(exc).__name__
            msg = str(exc)[:120]
            guard_raised = kind == "RuntimeError" and "ENDPOINT_GUARD" in msg
        out.append({"port": port, "exception_type": kind, "message": msg,
                    "blocked_by_guard": guard_raised,
                    "no_os_level_connect_attempted": guard_raised,
                    "violation_logged": len(e15.ENDPOINT_VIOLATIONS) > viol_before})
    return out


def probe_zero_wire_contact() -> dict:
    """C: 被拦连接不得到达对端 -> 临时监听器的 accept 队列必须为空。"""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    ephemeral = listener.getsockname()[1]
    listener.settimeout(0.3)
    guard_err = None
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(TIMEOUT)
        sk.connect(("127.0.0.1", ephemeral))
        sk.close()
    except Exception as exc:  # noqa: BLE001
        guard_err = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    peer_got_connection = True
    try:
        conn, _ = listener.accept()
        conn.close()
    except (socket.timeout, TimeoutError, OSError):
        peer_got_connection = False
    finally:
        listener.close()
    return {"ephemeral_port_used": ephemeral, "guard_error": guard_err,
            "peer_accepted_connection": peer_got_connection,
            "pass": guard_err is not None and peer_got_connection is False}


def main() -> int:
    counter_before = _counter()
    e15.install_endpoint_guard()
    pos = probe_positive()
    blocked = probe_blocked()
    zero_wire = probe_zero_wire_contact()
    counter_after = _counter()

    doc = {
        "meta": {
            "purpose": "W2 端点护栏仪表自证: 记录/拦截能力独立验证（弥补 ports_touched 在缓存复算跑为空导致的证据缺口）",
            "card": "TASK-20260830-04 §4 红线自查",
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model_calls_made": 0,
            "guard_source": "research/paper_w2_e15_full_judge.py::install_endpoint_guard",
        },
        "A_positive_recording": pos,
        "B_protected_ports_blocked": blocked,
        "C_zero_wire_contact": zero_wire,
        "D_budget_invariance": {
            "call_counter_before": counter_before, "call_counter_after": counter_after,
            "pass": counter_before == counter_after,
            "note": "只做 TCP 握手, 从不发 HTTP 请求, 不进 ledger_take 计数路径",
        },
        "gates": {
            "positive_recording": pos["pass"],
            "all_protected_ports_blocked": all(b["blocked_by_guard"] for b in blocked),
            "violations_recorded_for_each_block": all(b["violation_logged"] for b in blocked),
            "zero_wire_contact": zero_wire["pass"],
            "budget_unchanged": counter_after == counter_before,
        },
    }
    doc["gates"]["all_pass"] = all(doc["gates"].values())
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(doc["gates"], ensure_ascii=False))
    print("A ports_recorded=%s err=%s | C peer_accepted=%s | D %d->%d -> %s"
          % (pos["ports_recorded_by_guard"], pos["connect_error"],
             zero_wire["peer_accepted_connection"], counter_before, counter_after, OUT))
    return 0 if doc["gates"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
