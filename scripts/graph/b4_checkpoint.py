#!/usr/bin/env python3
"""B4 observation-window checkpoint reporter.

Computes segment stats from logs/graph/b4_ask_log.jsonl starting at a given
line (1-indexed, default: DSpark switch point 3092). Used for the 24h
post-switch checkpoint and periodic B4 reviews.

Output: prints summary + writes logs/graph/b4_checkpoint_<stamp>.md
Pure read-only; no service interaction.
"""
import json, sys, datetime, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
LOG = REPO / "logs" / "graph" / "b4_ask_log.jsonl"

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 3092
    lines = LOG.read_text(encoding="utf-8").splitlines()
    seg = lines[start:]
    total = ok = fb = agent_completed = agent_fb = direct = 0
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
        if route == "agent" and not fell:
            agent_completed += 1
        if route == "agent" and fell:
            agent_fb += 1
        if route == "direct":
            direct += 1
        if fell:
            fb += 1
        # test-traffic heuristic: sub-100ms wall time cannot be a real LLM roundtrip
        if lat < 100:
            suspect.append((lineno, d.get("ts"), route, lat))
        else:
            lat_real.append(lat)
        if st == "ok":
            ok += 1
    lat_real.sort()
    def pct(p):
        return lat_real[min(len(lat_real) - 1, int(len(lat_real) * p))] if lat_real else 0
    fb_rate = round(100.0 * fb / total, 1) if total else 0.0
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out = REPO / "logs" / "graph" / f"b4_checkpoint_{stamp}.md"
    real_agent = [s for s in [] ]  # placeholder kept simple
    report = [
        f"# B4 checkpoint {stamp}",
        f"",
        f"- segment: line {start + 1} .. {len(lines)} (n={total})",
        f"- route distribution: direct={direct}, agent-completed(no-fallback)={agent_completed}, agent-fell-back={agent_fb}",
        f"- fallback rows: {fb} ({fb_rate}% of segment)",
        f"- status: {statuses}",
        f"- latency (rows >=100ms): p50={pct(0.5)}ms p95={pct(0.95)}ms n={len(lat_real)}",
        f"- suspect test/cache rows (<100ms): {len(suspect)}",
    ]
    for s in suspect[:20]:
        report.append(f"  - line {s[0]} {s[1]} route={s[2]} lat={s[3]}ms")
    report.append("")
    report.append("Judgment rule (user approval 08-20 #3): fallback rate >60% -> first suspect content=null; investigate before rollback decision.")
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\nreport written: {out}")

if __name__ == "__main__":
    main()