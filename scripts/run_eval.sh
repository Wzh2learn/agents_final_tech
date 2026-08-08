#!/usr/bin/env bash
# 一键 eval (P2.3 沉淀, 2026-08-09): M1 回归门禁 + M2 确定性检验 + AI judge。
# 用法:
#   bash scripts/run_eval.sh             # M1 quick 门禁 + M2 全集 + judge
#   bash scripts/run_eval.sh --full-m1   # M1 全量门禁 (含 OCR 样本)
# 产出: logs/graph/eval/{scenario1_regression_report,m2_deterministic_report,
#       m2_judge_report,eval_summary}.{json,md}
# 退出码: M1 门禁或 M2 确定性检验失败 -> 1; judge 分数不阻塞 (参考性)。
set -uo pipefail
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ"
PY=./venv/bin/python
EVAL_DIR=logs/graph/eval
mkdir -p "$EVAL_DIR"

M1_MODE="--quick"
[ "${1:-}" = "--full-m1" ] && M1_MODE=""

echo "== [1/3] M1 scenario1 回归门禁 ${M1_MODE:-full} =="
$PY scripts/m1_scenario1_regression.py $M1_MODE \
    --report "$EVAL_DIR/scenario1_regression_report.json"
M1_RC=$?

echo "== [2/3] M2 确定性检验 =="
$PY scripts/m2_eval_deterministic.py \
    --report "$EVAL_DIR/m2_deterministic_report.json"
M2_RC=$?

echo "== [3/3] AI judge (:8004, temperature=0) =="
$PY scripts/m2_eval_judge.py \
    --input "$EVAL_DIR/m2_deterministic_report.json" \
    --report "$EVAL_DIR/m2_judge_report.json"
JD_RC=$?

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

echo "[run_eval] M1_RC=$M1_RC M2_RC=$M2_RC JUDGE_RC=$JD_RC"
[ $M1_RC -ne 0 ] || [ $M2_RC -ne 0 ] && exit 1
exit 0
