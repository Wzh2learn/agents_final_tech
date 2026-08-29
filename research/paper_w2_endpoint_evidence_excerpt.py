# -*- coding: utf-8 -*-
"""W2 端点观测耐久件生成器。

动机: 实跑端口观测原本只活在进程内 PORTS_TOUCHED, 缓存命中的复算会把工件里的
观测覆盖成空集。本脚本从在制转写日志按逐字文本匹配抽取原始实跑行, 写入
logs/graph/eval/ 耐久件, 终工件以其 sha256 引用。权威判据是逐字文本而非行号
（logs/ 会被追加, 行号漂移）; 正文不含时间戳, 故重复生成字节稳定、可复算。
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "logs" / "graph" / "eval" / "w2_endpoint_evidence_excerpt.txt"
SRC = [REPO / "logs" / "graph" / "loop_a.log", Path("/tmp/w2_e15_full.log")]
NEEDLES = {
    "original_live_run": "cells_ok=120/120 call_counter=122/200 ports=[8004] violations=[]",
    "cache_hit_rerun":   "cells_ok=120/120 call_counter=122/200 ports=[] violations=[]",
    "last_live_cell":    "[120/120] ok M9_m1_all_rows_fail/qa.retrieval.source_required -> 10 (cache=False n=122)",
}

def scan(path):
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {k: [(i, ln.rstrip()) for i, ln in enumerate(lines, 1) if k and NEEDLES[k] in ln]
            for k in NEEDLES}

hits = {str(p.relative_to(REPO)) if str(p).startswith(str(REPO)) else str(p): scan(p) for p in SRC}

def one(src, key):
    for (lineno, text) in hits[src][key]:
        return lineno, text
    return None, None

parts = [
    "# W2 E1.5 端点观测证据摘录（耐久件）",
    "# 目的: 端点红线（仅 :8004）的实跑观测原本只存在于进程内集合 PORTS_TOUCHED,",
    "#       缓存命中的复算不建连接会把工件里的观测覆盖成空集。本件把原始实跑的",
    "#       逐字输出固化为可复核证据, 其 sha256 记入终工件 payload。",
    "# 权威判据 = 逐字文本匹配; 行号仅为生成时定位提示（logs/ 为在制转写, 行号会漂移）。",
    "# 正文不含时间戳: 重复生成字节一致, 终工件引用的 sha256 才谈得上可复算。",
    "",
]
for src in hits:
    parts.append("## source: %s" % src)
    for key in ("last_live_cell", "original_live_run", "cache_hit_rerun"):
        ln, text = one(src, key)
        if ln:
            parts.append("[%s @line %s]\n%s" % (key, ln, text))
        else:
            parts.append("[%s @line n/a]\n<not present in this source>" % key)
    parts.append("")
body = "\n".join(parts)
OUT.write_text(body, encoding="utf-8")
print(json.dumps({"path": str(OUT.relative_to(REPO)),
                  "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                  "sources": {s: {k: len(v) for k, v in d.items()} for s, d in hits.items()}},
                 ensure_ascii=False, indent=1))
print(body)
