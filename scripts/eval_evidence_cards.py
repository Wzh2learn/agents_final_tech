#!/usr/bin/env python3
"""(v1, 批复 ⑤) per-case evidence card — 评测证据卡合成器。

把既有评测工件合成每题一张结构化证据卡 + leaderboard（K1.5 对照文档 §6.4
立项, 用户批复 ⑤ 并入 v1, 不单独立项）:
  输入(全部只读): m2_deterministic_report.json / m2_judge_report.json /
                  number_faithfulness_report.json /
                  checkpoint_aggregate_report.json(可选) /
                  tests/fixtures/m2_eval_questions.json(冻结, 只读取题面)
  输出: <eval-dir>/evidence_cards.json + evidence_cards_leaderboard.md

确定性聚合, 无推理, 不调服务。卡片 = 确定性契约逐项 pass+证据 + judge
四维分+理由 + NF 落地 + route/延迟 + 所属检查点叶子, 供论文 B 附录与
审计追溯。综合等级: A = 全契约过且 judge 各维 >=4; B = 契约全过但 judge
有维 <4 或 judge 缺; C = 任一契约失败。

用法: python scripts/eval_evidence_cards.py [--eval-dir logs/graph/eval]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "m2_eval_questions.json")

# 契约 -> 检查点叶子 (config/eval_checkpoint_trees.json 的 contract 映射)
CONTRACT_LEAF = {
    "source_required": "qa.retrieval.source_required",
    "exact_numeric": "qa.numeric.exact",
    "contains_keyword": "qa.numeric.exact",
    "refusal_expected": "qa.refusal.deterministic",
}
JUDGE_LEAF = {
    "faithfulness": "qa.faithfulness.judge",
    "citation_quality": "qa.citation.judge",
    "refusal_appropriateness": "qa.refusal.judge",
    "numeric_correctness": "qa.numeric.exact",
}


def _load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def grade_of(card: dict) -> str:
    checks = card.get("checks", [])
    all_pass = bool(checks) and all(c.get("pass") for c in checks)
    js = card.get("judge_scores", {})
    vals = [c.get("score") for c in js.values()
            if isinstance(c, dict) and c.get("score") is not None]
    if not all_pass:
        return "C"
    if vals and min(vals) >= 4:
        return "A"
    return "B"


def build_cards(eval_dir: str, fixture_path: str = FIXTURE) -> list[dict]:
    det = _load(os.path.join(eval_dir, "m2_deterministic_report.json"))
    jd = _load(os.path.join(eval_dir, "m2_judge_report.json"))
    nf = _load(os.path.join(eval_dir, "number_faithfulness_report.json"))
    fx = _load(fixture_path)
    fx_by_id = {q["id"]: q for q in fx.get("questions", [])}
    jd_by_id = {r["id"]: r for r in jd.get("results", [])}
    nf_by_id = {r.get("id"): r for r in nf.get("results", [])}

    cards = []
    for r in det.get("results", []):
        qid = r.get("id")
        fxq = fx_by_id.get(qid, {})
        checks = []
        for ch in r.get("checks", []):
            checks.append({
                "type": ch.get("type"),
                "pass": bool(ch.get("pass")),
                "evidence": str(ch.get("evidence") or ch.get("detail")
                                or "")[:300],
                "checkpoint_leaf": CONTRACT_LEAF.get(ch.get("type"), ""),
            })
        jrow = jd_by_id.get(qid, {})
        jscores = {}
        for dim, cell in (jrow.get("scores") or {}).items():
            if isinstance(cell, dict):
                jscores[dim] = {"score": cell.get("score"),
                                "reason": str(cell.get("reason", ""))[:200],
                                "checkpoint_leaf": JUDGE_LEAF.get(dim, "")}
        nfrow = nf_by_id.get(qid)
        card = {
            "id": qid,
            "question": (fxq.get("question") or (r.get("turns") or [""])[-1]),
            "turns": r.get("turns", []),
            "route": r.get("route"),
            "latency_ms": r.get("latency_ms"),
            "sources_count": len(r.get("sources", []) or []),
            "checks": checks,
            "judge_scores": jscores,
            "number_faithfulness": (
                {"pass": bool(nfrow.get("pass")),
                 "ungrounded": nfrow.get("ungrounded", [])}
                if nfrow else None),
        }
        card["grade"] = grade_of(card)
        cards.append(card)
    order = {"A": 0, "B": 1, "C": 2}
    cards.sort(key=lambda c: (
        order.get(c["grade"], 9),
        -sum(1 for ch in c["checks"] if ch["pass"]),
        -len(c["checks"])))
    return cards


def _format_leaderboard(cards: list[dict], meta: dict) -> str:
    n = len(cards)
    cnt = {g: sum(1 for c in cards if c["grade"] == g) for g in "ABC"}
    L = ["# Evidence Cards Leaderboard (v1)", "",
         f"> 生成: {meta['generated']} | n={n} | A={cnt['A']} B={cnt['B']} "
         f"C={cnt['C']}",
         "> 口径: A=全契约过且 judge 各维>=4; B=契约全过 judge 有缺/低; "
         "C=任一契约失败", "",
         "| # | id | 级 | 契约 pass | judge 均分 | route | NF |",
         "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(cards, 1):
        npass = sum(1 for ch in c["checks"] if ch["pass"])
        vals = [v["score"] for v in c["judge_scores"].values()
                if isinstance(v, dict) and v.get("score") is not None]
        javg = f"{sum(vals)/len(vals):.2f}" if vals else "-"
        nf = c.get("number_faithfulness")
        nf_s = ("pass" if nf.get("pass") else "FAIL") if nf else "-"
        L.append(f"| {i} | {c['id']} | {c['grade']} | "
                 f"{npass}/{len(c['checks'])} | {javg} | "
                 f"{c.get('route') or '-'} | {nf_s} |")
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-dir", default="logs/graph/eval")
    ap.add_argument("--fixture", default=FIXTURE)
    args = ap.parse_args(argv)

    det_path = os.path.join(args.eval_dir, "m2_deterministic_report.json")
    if not os.path.exists(det_path):
        print(f"[fatal] 缺确定性报告: {det_path}", file=sys.stderr)
        return 2
    cards = build_cards(args.eval_dir, args.fixture)
    meta = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "v1", "eval_dir": args.eval_dir}
    out_json = os.path.join(args.eval_dir, "evidence_cards.json")
    out_md = os.path.join(args.eval_dir, "evidence_cards_leaderboard.md")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "cards": cards}, fh,
                  ensure_ascii=False, indent=1)
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(_format_leaderboard(cards, meta))
    print(f"[evidence-cards] n={len(cards)} -> {out_json}")
    print(f"[evidence-cards] leaderboard -> {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
