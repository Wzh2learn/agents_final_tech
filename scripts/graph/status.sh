#!/usr/bin/env bash
# status.sh — 一页健康 (Q4 L1 落地, 2026-08-12; 原 loop_d_monitor.sh 退役候选)
# 把辅助线 ad hoc 核验固化为一条命令: ssh jinrong-dev "bash .../scripts/graph/status.sh"
# 只读不写; 异常以 [!] 行标出。
# 2026-08-22 T3 增强: 端口加 8006/8007/8008; Loop B 加 loop_b.log 最近 PASS 行; B4 改两列口径（复用 b4_checkpoint.compute, 只读）。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
now=$(date +%s)

echo "== status.sh $(date '+%F %T') =="

echo "-- 三方对齐 --"
HEAD=$(git rev-parse --short HEAD 2>/dev/null)
echo "GB10 HEAD: $HEAD ($(git log -1 --format=%ci 2>/dev/null | cut -c1-16))"
GH=$(timeout 10 git ls-remote origin main 2>/dev/null | cut -c1-7)
if [ -n "$GH" ]; then
  if [ "$GH" = "$HEAD" ]; then echo "GitHub  : $GH (对齐)"; else echo "[!] GitHub: $GH (与 GB10 $HEAD 漂移)"; fi
else
  echo "[!] GitHub: ls-remote 超时/不可达"
fi
echo "(本机自查: git -C agents_final_tech fetch gb10 main && git log --oneline -1)"

echo "-- Loop B --"
if [ -f logs/graph/verify-report.json ]; then
  python3 -c "
import json
d = json.load(open('logs/graph/verify-report.json'))
print('verify-report:', d.get('timestamp','?'), 'overall=' + str(d.get('overall','?')), 'head=' + str(d.get('head_commit','?')))
" 2>/dev/null || echo "[!] verify-report.json 解析失败"
else
  echo "[!] verify-report.json 缺失"
fi
LASTB=$(tmux capture-pane -pt graph-loop-b -S -200 2>/dev/null | grep "REPORT: overall=" | tail -1)
echo "pane 尾行 : ${LASTB:-(graph-loop-b 未捕获)}"
LASTPASS=$(grep "REPORT: overall=PASS" logs/graph/loop_b.log 2>/dev/null | tail -1)
echo "log 最近 PASS : ${LASTPASS:-(无记录/loop_b.log 缺失)}"

echo "-- 端口快照 --"
LINE=""
for p in 5050 4096 8004 8005 8006 8007 8008 8100 15432; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then LINE="$LINE :$p=UP"; else LINE="$LINE :$p=down"; fi
done
echo "$LINE"
echo "tmux 禁杀: graph-loop-b(Loop B) / opencode-serve(sidecar)"
echo "-- PG 池 / opencode.db (T2 2026-08-24 夜增) --"
PGCNT=$(docker exec pgvector_15432 psql -U postgres -t -A -c "select count(*) from pg_stat_activity where datname is not null" 2>/dev/null | tr -d '[:space:]')
PGIDLE=$(docker exec pgvector_15432 psql -U postgres -t -A -c "select count(*) from pg_stat_activity where state='idle' and datname is not null" 2>/dev/null | tr -d '[:space:]')
echo "PG 池连接: total=${PGCNT:-?} idle=${PGIDLE:-?} (哨兵阈值 warn>80 / fail>95)"
./venv/bin/python - <<'PYDB' 2>/dev/null || echo "[!] opencode.db 读取失败"
import sqlite3, os
p = os.path.expanduser("~/.local/share/opencode/opencode.db")
c = sqlite3.connect(p)
s, pa, m = (c.execute("select count(*) from " + t).fetchone()[0] for t in ("session", "part", "message"))
print(f"opencode.db 三表: session={s} part={pa} message={m} (08-23 持久化恢复基线: 0/0/0 起步)")
PYDB


echo "-- B4 观察窗口 --"
B4=logs/graph/b4_ask_log.jsonl
if [ -f "$B4" ]; then
  ./venv/bin/python - "$B4" <<'PY'
import json, sys
sys.path.insert(0, "scripts/graph")
from b4_checkpoint import compute
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
n = len(lines)
rows = []
for l in lines:
    l = l.strip()
    if l:
        try: rows.append(json.loads(l))
        except Exception: pass
err = sum(1 for r in rows if r.get("status") == "error")
last = rows[-1].get("ts", "?") if rows else "-"
print(f"asks={n} (error={err}) last={last}")
def fmt(label, c):
    fr = f"{c['fb_rate']}%" if c["fb_rate"] is not None else "N/A"
    return (f"{label}: attempted={c['attempted']} completed={c['agent_completed']} fallback_rate={fr} "
            f"(timeout_fb={c['agent_timeout_fb']} fast_fb={c['fast_fallback']} direct={c['pure_direct']})")
ROLLBACK_POINT = 3294  # Phase 0 回滚点 (2026-08-21); lines[3294:] = 第 3295 行起（半开区间与 b4_checkpoint.py 一致）
print("两列口径 (尝试=完成+超时回落; route 字段记最终路径)")
print("  " + fmt(f"回滚点后 ({ROLLBACK_POINT + 1} 起)", compute(lines, ROLLBACK_POINT)))
print("  " + fmt("全量 (1 起)", compute(lines, 0)))
PY
else
  echo "asks=0 (日志未生成)"
fi
echo "-- dispatch_log --"
if [ -f logs/graph/dispatch_log.md ]; then
  LAST=$(tail -1 logs/graph/dispatch_log.md)
  AGE=$(( (now - $(stat -c %Y logs/graph/dispatch_log.md)) / 60 ))
  echo "末条: ${LAST:0:120}"
  echo "文件更新于 ${AGE} 分钟前"
fi

echo "-- 冻结节点 --"
FFAIL=0
while read -r sum path; do
  [ -z "${sum:-}" ] && continue
  if [ -f "$path" ]; then
    ACT=$(md5sum "$path" | cut -c1-32)
    if [ "$ACT" != "$sum" ]; then echo "[!] 冻结漂移: $path"; FFAIL=1; fi
  else
    echo "[!] 冻结缺失: $path"; FFAIL=1
  fi
done < <(grep -vE "^[[:space:]]*(#|$)" scripts/graph/frozen_hashes.txt)
[ "$FFAIL" = "0" ] && echo "frozen_hashes: PASS"

echo "-- docs 治理 --"
DL=$(./venv/bin/python scripts/docs_lint.py 2>&1 | head -1)
echo "docs_lint  : ${DL:-执行失败}"
SS=$(bash scripts/graph/sync_skills.sh --check 2>&1 | tail -1)
echo "sync_skills: ${SS:-执行失败}"
echo "== end =="
