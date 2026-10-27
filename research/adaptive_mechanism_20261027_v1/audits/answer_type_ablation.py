from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict

REPO_ROOT = "/home/testuser/wzh/adaptive_mechanism_worktree_20261027"
sys.path.insert(0, REPO_ROOT)

from research.adaptive_mechanism_20261027_v1.diagnostics import visible_typed_baseline as vtb
from research.adaptive_mechanism_20261027_v1.scoring_v2 import scorer as sc


def read_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def build_cases():
    raw_rows = read_jsonl(vtb.DEFAULT_RAW)
    annotated = {r["call_id"]: r for r in read_jsonl(vtb.DEFAULT_ANNOTATED)}
    refs = json.loads(vtb.DEFAULT_REFERENCE.read_text(encoding="utf-8"))["rows"]
    uid_by_hash = {hashlib.sha256(r["question_uid"].encode("utf-8")).hexdigest(): r["question_uid"] for r in refs}
    ref_by_uid = {r["question_uid"]: r for r in refs}
    srcs = sc.load_source_records(vtb.DEFAULT_SOURCE)
    grouped = defaultdict(list)
    for row in raw_rows:
        grouped[(row["question_uid_sha256"], row["arm"])].append(row)
    cases = []
    for (uid_hash, arm), attempts in sorted(grouped.items()):
        raw = max(attempts, key=lambda i: int(i["call_number"]))
        uid = uid_by_hash[uid_hash]
        reference = ref_by_uid[uid]
        so = raw.get("selected_paragraph_orders", annotated[raw["call_id"]]["selected_paragraph_orders"])
        vis = sc.load_visible_context(srcs[reference["table_uid"]], reference, so)
        cases.append((uid, arm, reference, vis))
    return cases


def run(cases, blank):
    out = {}
    for uid, arm, reference, vis in cases:
        at = "" if blank else reference["answer_type"]
        rt = vtb.answer_from_visible(reference["question"], at, vis)
        score = sc.score_response(rt, reference, vis)
        out[(uid[:8], arm)] = (score["status"], reference["answer_type"])
    return out

def main():
    cases = build_cases()
    oracle = run(cases, False)
    ablation = run(cases, True)
    print("ORACLE_COUNTS", dict(Counter(v[0] for v in oracle.values())))
    print("ABLATION_COUNTS", dict(Counter(v[0] for v in ablation.values())))
    print("ANSWER_TYPE_DIST", dict(Counter(v[1] for v in oracle.values())))
    print("FLIPS:")
    for k in sorted(oracle):
        if oracle[k][0] != ablation[k][0]:
            print("  ", k[0], k[1], oracle[k][0], "->", ablation[k][0], "atype", oracle[k][1])
    print("ABLATION_PER_UID:")
    buid = defaultdict(dict)
    for (u, a), v in ablation.items():
        buid[u][a] = v[0]
    for u in sorted(buid):
        x = buid[u]
        print("  ", u, x.get("table_top3"), "|", x.get("table_top5"), "|", x.get("table_all"))


if __name__ == "__main__":
    main()
