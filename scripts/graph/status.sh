#!/usr/bin/env bash
# status.sh — 一页健康 (Q4 L1 落地, 2026-08-12; 原 loop_d_monitor.sh 退役候选)
# 把辅助线 ad hoc 核验固化为一条命令: ssh jinrong-dev "bash .../scripts/graph/status.sh"
# 只读不写; 异常以 [!] 行标出。
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

echo "-- 端口快照 --"
LINE=""
for p in 5050 4096 8004 8005 8100 15432; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then LINE="$LINE :$p=UP"; else LINE="$LINE :$p=down"; fi
done
echo "$LINE"
echo "tmux 禁杀: graph-loop-b(Loop B) / opencode-serve(sidecar)"

echo "-- B4 观察窗口 --"
B4=logs/graph/b4_ask_log.jsonl
if [ -f "$B4" ]; then
  python3 - "$B4" <<'PY'
import json, sys
rows = []
for l in open(sys.argv[1], encoding="utf-8"):
    l = l.strip()
    if l:
        try: rows.append(json.loads(l))
        except Exception: pass
n = len(rows)
agent = sum(1 for r in rows if r.get("route") == "agent")
fb = sum(1 for r in rows if r.get("fell_back"))
err = sum(1 for r in rows if r.get("status") == "error")
last = rows[-1].get("ts", "?") if rows else "-"
print(f"asks={n} (agent={agent}, fallback={fb}, error={err}) last={last}")
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
