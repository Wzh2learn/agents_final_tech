#!/usr/bin/env python3
"""S3⑤ judge 分流交叉一致性 (2026-08-13)。

比较两份 judge report (同答案集、不同 judge 端点/模型) 的打分一致性:
- 逐题逐维 exact match 率
- 平均分差 (绝对值)
- 分歧 >=2 分的题项列表
用法: venv/bin/python scripts/m2_eval_judge_crosscheck.py <report_a> <report_b>
"""
import json
import sys

DIMS = ("faithfulness", "numeric_correctness", "citation_quality",
        "refusal_appropriateness")


def load(path: str) -> dict:
    d = json.load(open(path, encoding="utf-8"))
    return {r["id"]: r for r in d.get("results", [])}, d


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    ra, da = load(sys.argv[1])
    rb, db = load(sys.argv[2])
    ids = sorted(set(ra) & set(rb))
    total, exact, diffs, big = 0, 0, [], []
    for qid in ids:
        for dim in DIMS:
            sa = ra[qid]["scores"][dim]["score"]
            sb = rb[qid]["scores"][dim]["score"]
            if sa is None or sb is None:
                continue
            total += 1
            if sa == sb:
                exact += 1
            else:
                diffs.append(abs(sa - sb))
                if abs(sa - sb) >= 2:
                    big.append((qid, dim, sa, sb))
    print(f"judge A: {da.get('judge_endpoint')} ({da.get('judge_model')})")
    print(f"judge B: {db.get('judge_endpoint')} ({db.get('judge_model')})")
    print(f"共同题数: {len(ids)} | 维度判定数: {total}")
    if total:
        print(f"exact match: {exact}/{total} = {exact/total:.1%}")
        print(f"平均分差(绝对): {sum(diffs)/total:.2f}" if diffs else "平均分差(绝对): 0.00")
    for qid, dim, sa, sb in big:
        print(f"  [big-diff] {qid} {dim}: A={sa} B={sb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
