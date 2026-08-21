#!/usr/bin/env python3
"""B4 observation-window checkpoint reporter.

Computes segment stats from logs/graph/b4_ask_log.jsonl starting at a given
line (1-indexed, default: DSpark switch point 3092). Used for the 24h
post-switch checkpoint and periodic B4 reviews.

Caliber (2026-08-21 audit fix, THREADS 口径注记; 2026-08-22 T3 抽出 compute()
供 status.sh 复用, main() 输出保持逐字不变):
  B4 `route` field records the FINAL serving path. Agent-route attempts that
  time out are logged as route=direct + fell_back=true. Agent-path stats must
  therefore always use the two-column attempted/completed caliber:
    attempted = completed + timeout-fallbacks
      completed        := route=agent (latency>=100ms; <100ms rows are test
                          fabrications and excluded)
      timeout_fallback := route=direct AND fell_back=true AND latency>=45000ms
                          (full OPENCODE_ASK_TIMEOUT burned before fallback)
    fast_fallback (informational, NOT counted as attempts):
                          route=direct AND fell_back=true AND latency<45000ms
                          (sidecar unhealthy / instant fallback)
    fallback_rate = 1 - completed / attempted

Output: prints summary + writes logs/graph/b4_checkpoint_<stamp>.md
Pure read-only; no service interaction.
"""
import json, sys, datetime, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
LOG = REPO / "logs" / "graph" / "b4_ask_log.jsonl"
TIMEOUT_MS = 45000  # OPENCODE_ASK_TIMEOUT; rows at/above this burned the full agent budget


def compute(lines, start):
    """Aggregate segment lines[start:] into a stats dict.

    Read-only and side-effect free; reused by scripts/graph/status.sh for the
    realtime two-column B4 output. `lines` = splitlines() of the jsonl log,
    `start` = 0-based slice index (start=N means 1-indexed line N+1 onward).
    """
    seg = lines[start:]
    total = agent_completed = agent_timeout_fb = fast_fallback = pure_direct = 0
    suspect = []
    statuses = {}
    lat_real = []
    for i, l in enumerate(seg):
        try:
            d = json.loads(l)
        except Exception:
            continue
        lineno = start + i + 1
        total += 1
        route = d.get("route")
        lat = d.get("latency_ms", 0)
        fell = bool(d.get("fell_back"))
        st = d.get("status", "ok")
        statuses[st] = statuses.get(st, 0) + 1
        # test-traffic heuristic: sub-100ms wall time cannot be a real LLM roundtrip
        if lat < 100:
            suspect.append((lineno, d.get("ts"), route, lat, fell))
            continue
        lat_real.append(lat)
        if route == "agent" and not fell:
            agent_completed += 1
        elif route == "direct" and fell and lat >= TIMEOUT_MS:
            agent_timeout_fb += 1
        elif route == "direct" and fell:
            fast_fallback += 1
        elif route == "direct":
            pure_direct += 1
    attempted = agent_completed + agent_timeout_fb
    fb_rate = round(100.0 * (1 - agent_completed / attempted), 1) if attempted else None
    lat_real.sort()
    return {
        "total": total,
        "agent_completed": agent_completed,
        "agent_timeout_fb": agent_timeout_fb,
        "fast_fallback": fast_fallback,
        "pure_direct": pure_direct,
        "attempted": attempted,
        "fb_rate": fb_rate,
        "statuses": statuses,
        "lat_real": lat_real,
        "suspect": suspect,
    }


def pct(lat_real, p):
    return lat_real[min(len(lat_real) - 1, int(len(lat_real) * p))] if lat_real else 0


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 3092
    lines = LOG.read_text(encoding="utf-8").splitlines()
    c = compute(lines, start)
    lat_real = c["lat_real"]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out = REPO / "logs" / "graph" / f"b4_checkpoint_{stamp}.md"
    report = [
        f"# B4 checkpoint {stamp}",
        "",
        "## agent 路两列口径（判定主口径; route 字段记最终路径, 尝试=完成+超时回落）",
        f"- agent 尝试总数 (attempted): {c['attempted']}",
        f"- agent 完成数 (无回落): {c['agent_completed']}",
        f"- 回落率: {c['fb_rate']}%  (= 1 - 完成/尝试)" if c["fb_rate"] is not None else "- 回落率: N/A (无尝试)",
        f"  - 超时回落 (latency>={TIMEOUT_MS}ms): {c['agent_timeout_fb']}",
        f"  - 快速回落 (<{TIMEOUT_MS}ms, sidecar 不可用等, 不计入尝试): {c['fast_fallback']}",
        "",
        "## 全量分布",
        f"- segment: line {start + 1} .. {len(lines)} (n={c['total']})",
        f"- 最终路径分布: direct={c['pure_direct'] + c['agent_timeout_fb'] + c['fast_fallback']} (其中回落 {c['agent_timeout_fb'] + c['fast_fallback']}), agent={c['agent_completed']}",
        f"- status: {c['statuses']}",
        f"- latency (rows >=100ms): p50={pct(lat_real, 0.5)}ms p95={pct(lat_real, 0.95)}ms n={len(lat_real)}",
        f"- suspect test/cache rows (<100ms, 已排除出统计): {len(c['suspect'])}",
    ]
    for s in c["suspect"][:20]:
        report.append(f"  - line {s[0]} {s[1]} route={s[2]} lat={s[3]}ms fell={s[4]}")
    report.append("")
    report.append("Judgment rule (user approval 08-20 #3): 回落率 >60% -> 第一怀疑 content=null; 查无解释报用户拍板。")
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\nreport written: {out}")

if __name__ == "__main__":
    main()
