from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/ma_cerd_gold_public_v1.jsonl"


def f1(expected: set[str], predicted: set[str]) -> float:
    if not expected and not predicted:
        return 1.0
    if not expected or not predicted:
        return 0.0
    precision = len(expected & predicted) / len(predicted)
    recall = len(expected & predicted) / len(expected)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def main(path: str) -> int:
    gold = {row["contract_id"]: row for row in map(json.loads, GOLD.read_text(encoding="utf-8").splitlines())}
    predictions = {row["contract_id"]: row for row in map(json.loads, Path(path).read_text(encoding="utf-8").splitlines())}
    if set(predictions) != set(gold):
        raise SystemExit("predictions must contain exactly the released 1,000 contract IDs")
    relation_correct = 0
    handling_exact = 0
    impact_scores = []
    preserved_scores = []
    for contract_id, target in gold.items():
        prediction = predictions[contract_id]
        relation_correct += prediction["relation"] == target["labels"]["relation"]
        handling_exact += set(prediction["acceptable_decisions"]) == set(target["labels"]["acceptable_decisions"])
        impact_scores.append(f1(set(target["labels"]["impact_node_ids"]), set(prediction["impact_node_ids"])))
        preserved_scores.append(f1(set(target["labels"]["preserved_node_ids"]), set(prediction["preserved_node_ids"])))
    result = {
        "record_count": len(gold),
        "relation_accuracy": relation_correct / len(gold),
        "handling_exact_match": handling_exact / len(gold),
        "mean_impact_set_f1": sum(impact_scores) / len(impact_scores),
        "mean_preserved_set_f1": sum(preserved_scores) / len(preserved_scores),
        "note": "Reference evaluator only; preregistered family-cluster statistics remain required for publication claims.",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/evaluate_predictions.py predictions.jsonl")
    raise SystemExit(main(sys.argv[1]))
