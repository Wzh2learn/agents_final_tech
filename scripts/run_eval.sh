#!/usr/bin/env bash
# 一键 eval (P2.3 沉淀, 2026-08-09): M1 回归门禁 + M2 确定性检验 + AI judge。
# 用法:
#   bash scripts/run_eval.sh             # M1 quick 门禁 + M2 全集 + judge
#   bash scripts/run_eval.sh --full-m1   # M1 全量门禁 (含 OCR 样本)
# 产出: logs/graph/eval/{scenario1_regression_report,m2_deterministic_report,
#       m2_judge_report,eval_summary}.{json,md}
# 退出码: M1 门禁 / M2 确定性检验 / 数值忠实度任一失败 -> 1; judge 分数不阻塞 (参考性)。
set -uo pipefail
# 数值忠实检验需直连 PG (RAGService), 载入 .env 兜底
if [ -f .env ]; then set -a; . ./.env; set +a; fi
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ"
PY=./venv/bin/python
EVAL_DIR=logs/graph/eval
mkdir -p "$EVAL_DIR"

M1_MODE="--quick"
[ "${1:-}" = "--full-m1" ] && M1_MODE=""

echo "== [1/5] M1 scenario1 回归门禁 ${M1_MODE:-full} =="
$PY scripts/m1_scenario1_regression.py $M1_MODE \
    --report "$EVAL_DIR/scenario1_regression_report.json"
M1_RC=$?

echo "== [2/5] M2 确定性检验 =="
$PY scripts/m2_eval_deterministic.py \
    --report "$EVAL_DIR/m2_deterministic_report.json"
M2_RC=$?

echo "== [3/5] M2 数值忠实度核验 (生产口径检索, 去 LLM 化) =="
$PY scripts/m2_eval_number_faithfulness.py \
    --top-k 5
NF_RC=$?

# F-J2 (08-26): judge 腿隔离闸 — 端点为 :8006 时等其在途请求归零,
# 防 NF/agent 路孤儿轨迹自我饱和 (08-25 01:51 事故根因); 非 :8006 端点无需闸。
wait_judge_idle() {
  local ep="${M2_JUDGE_ENDPOINT:-http://127.0.0.1:8004/v1/chat/completions}" st i
  case "$ep" in *":8006"*) ;; *)
    echo "[F-J2] judge 端点非 :8006 ($ep), 无需隔离闸"; return 0;; esac
  for i in $(seq 1 40); do
    st=$(curl -s --max-time 4 http://127.0.0.1:8006/metrics \
         | grep -E "^vllm:num_requests_(running|waiting)" \
         | awk "{s+=\$2} END {print s+0}")
    [ "${st:-1}" = "0" ] && { echo "[F-J2] :8006 idle (第 $i 次检查)"; return 0; }
    echo "[F-J2] 等 :8006 排空 in_flight=$st ($i/40)"; sleep 15
  done
  echo "[F-J2] :8006 10min 未 idle, judge 步显式跳过 (不静默打分)"
  return 3
}

echo "== [4/5] AI judge (endpoint=${M2_JUDGE_ENDPOINT:-default :8004}, temperature=0; JUDGE_RUNS=${JUDGE_RUNS:-1}) =="
if wait_judge_idle; then
  $PY scripts/m2_eval_judge.py \
      --input "$EVAL_DIR/m2_deterministic_report.json" \
      --report "$EVAL_DIR/m2_judge_report.json" \
      --runs "${JUDGE_RUNS:-1}"
  JD_RC=$?
else
  JD_RC=3
  echo "[run_eval] judge SKIPPED by F-J2 gate (JD_RC=3)"
fi

echo "== [5/5] Evidence cards (v1, 确定性聚合, 非阻塞) =="
$PY scripts/eval_evidence_cards.py --eval-dir "$EVAL_DIR" || echo "[warn] evidence cards 生成失败 (不影响 eval 退出码)"

$PY - "$EVAL_DIR" <<'PYEOF'
import json, os, sys, time
eval_dir = sys.argv[1]
def load(name):
    p = os.path.join(eval_dir, name)
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}
m1 = load("scenario1_regression_report.json")
m2 = load("m2_deterministic_report.json")
nf = load("number_faithfulness_report.json")
jd = load("m2_judge_report.json")
lines = [f"# Eval Summary — {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
lines.append(f"- M1 scenario1 门禁: **{m1.get('overall', 'N/A')}** "
             f"(quick={m1.get('quick')})")
fails1 = [r["label"] for r in m1.get("rows", []) if r["status"] == "FAIL"]
if fails1:
    lines.append(f"  - FAIL: {fails1}")
lines.append(f"- M2 确定性检验: **{m2.get('overall', 'N/A')}** "
             f"({m2.get('n_pass', '?')}/{m2.get('n_questions', '?')} 题全过)")
for r in m2.get("results", []):
    if not r.get("all_pass"):
        bad = [c["type"] for c in r.get("checks", []) if not c["pass"]]
        lines.append(f"  - FAIL {r['id']}: {bad}")
if nf:
    n_nf = len(nf.get("results", []))
    lines.append(f"- M2 数值忠实度: **{nf.get('n_fail', '?')}/{n_nf} 条数值未落地** "
                 f"(top_k={nf.get('top_k')})")
    for r in nf.get("results", []):
        if not r.get("pass"):
            lines.append(f"  - [ungrounded] {r['id']}: {r.get('ungrounded', [])}")
s = jd.get("summary", {})
if s:
    dims = ", ".join(f"{k}={v.get('avg')}" for k, v in s.items())
    lines.append(f"- AI judge 均分: {dims}")
low = [(r["id"], d, c["score"], c.get("reason", "")[:80])
       for r in jd.get("results", []) for d, c in r.get("scores", {}).items()
       if isinstance(c, dict) and c.get("score") is not None and c["score"] <= 2]
for qid, d, sc, why in low:
    lines.append(f"  - [judge low] {qid} {d}={sc}: {why}")
out = os.path.join(eval_dir, "eval_summary.md")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n" + "\n".join(lines))
print(f"\n[summary] {out}")
PYEOF

echo "[run_eval] M1_RC=$M1_RC M2_RC=$M2_RC NF_RC=$NF_RC JUDGE_RC=$JD_RC"
[ $M1_RC -ne 0 ] || [ $M2_RC -ne 0 ] || [ $NF_RC -ne 0 ] && exit 1
exit 0
