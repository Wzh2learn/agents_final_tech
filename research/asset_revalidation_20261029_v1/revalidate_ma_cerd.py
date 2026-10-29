#!/usr/bin/env python3
"""Recompute action-set metrics from saved MA-CERD gold and saved predictions."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

root = Path(sys.argv[1])
output = Path(sys.argv[2])
gold_path = root / "research/ma_cerd_independent_v1/release/data/ma_cerd_gold_public_v1.jsonl"
result_path = root / "research/ma_cerd_independent_v1/UNCERTAINTY_ADJUDICATION_RESULT.json"
gold_rows = [json.loads(line) for line in gold_path.read_text(encoding="utf-8").splitlines() if line]
by_id = {r["contract_id"]: r for r in gold_rows}
if len(by_id) != len(gold_rows):
    raise ValueError("duplicate gold contract id")
rows = json.loads(result_path.read_text(encoding="utf-8"))["rows"]
if len(rows) != 250 or len({r["contract_id"] for r in rows}) != len(rows):
    raise ValueError("unexpected or duplicated result ids")
if not all(r["valid"] and r["contract_id"] in by_id for r in rows):
    raise ValueError("invalid result or missing gold")

counts = Counter()
gold_distribution = Counter()
prediction_distribution = Counter()
for row in rows:
    gold = set(by_id[row["contract_id"]]["labels"]["acceptable_decisions"])
    pred = set(row["prediction"]["acceptable_decisions"])
    if not gold or not pred:
        raise ValueError("unexpected empty set")
    gold_distribution["+".join(sorted(gold))] += 1
    prediction_distribution["+".join(sorted(pred))] += 1
    counts["model_exact"] += pred == gold
    counts["model_subset"] += pred <= gold
    counts["model_intersects"] += bool(pred & gold)
    counts["model_only_defer"] += pred == {"defer"}
    counts["always_defer_exact"] += gold == {"defer"}
    counts["always_defer_admissible"] += "defer" in gold
    counts["model_can_suggest_non_defer"] += bool(pred & {"execute", "repair"})

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

result = {
    "evidence": "post-hoc recomputation on saved source-exposed queue; not an agent decision trial",
    "n": len(rows),
    "source_hashes_sha256": {"gold": digest(gold_path), "results": digest(result_path)},
    "counts": dict(counts),
    "gold_action_set_distribution": dict(sorted(gold_distribution.items())),
    "model_action_set_distribution": dict(sorted(prediction_distribution.items())),
    "limits": "Set admissibility is not task completion or safety. Results are not held out; model received simulator relation.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
