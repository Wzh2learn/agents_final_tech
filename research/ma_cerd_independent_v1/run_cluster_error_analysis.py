"""Family-cluster uncertainty and error concentration analysis."""

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

P = Path(__file__).resolve().parent
GOLD = P / "release/data/ma_cerd_gold_public_v1.jsonl"
PRED = P / "predictions/adjudicator_resource_oracle.jsonl"


def f1(gold, pred):
    gold, pred = set(gold), set(pred)
    if not gold and not pred: return 1.0
    if not gold or not pred: return 0.0
    p, r = len(gold & pred) / len(pred), len(gold & pred) / len(gold)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def score(row, pred):
    labels = row["labels"]
    return {
        "relation": pred["relation"] == labels["relation"],
        "handling": set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]),
        "impact_f1": f1(labels["impact_node_ids"], pred["impact_node_ids"]),
        "preserved_f1": f1(labels["preserved_node_ids"], pred["preserved_node_ids"]),
    }


def summarize(rows):
    n = len(rows)
    return {
        "relation": sum(x["scores"]["relation"] for x in rows) / n,
        "handling": sum(x["scores"]["handling"] for x in rows) / n,
        "impact_f1": sum(x["scores"]["impact_f1"] for x in rows) / n,
        "preserved_f1": sum(x["scores"]["preserved_f1"] for x in rows) / n,
        "records": n,
    }


def bootstrap(rows, iterations=2000):
    families = defaultdict(list)
    for row in rows:
        families[row["family_id"]].append(row)
    keys = sorted(families)
    rng = random.Random(20261020)
    samples = []
    for _ in range(iterations):
        picked = [keys[rng.randrange(len(keys))] for _ in keys]
        sample = [x for key in picked for x in families[key]]
        samples.append(summarize(sample))
    out = {}
    for metric in ("relation", "handling", "impact_f1", "preserved_f1"):
        values = sorted(x[metric] for x in samples)
        out[metric] = {
            "ci95_low": values[int(0.025 * iterations)],
            "ci95_high": values[int(0.975 * iterations) - 1],
            "mean": sum(values) / iterations,
        }
    return out


def main():
    gold = [json.loads(x) for x in GOLD.read_text().splitlines()]
    preds = {x["contract_id"]: x for x in map(json.loads, PRED.read_text().splitlines())}
    rows = []
    for row in gold:
        pred = preds[row["contract_id"]]
        rows.append({
            "family_id": row["family_id"],
            "contract_id": row["contract_id"],
            "target_kind": row["intervention"]["target_kind"],
            "signature": tuple(row["oracle_bundle"]["rule_oracle"].get("changed_signature_fields", [])),
            "alignment": row["oracle_bundle"]["alignment"],
            "partition": row["partition"],
            "scores": score(row, pred),
        })
    groups = {}
    for key in ("target_kind", "alignment", "partition", "signature"):
        buckets = defaultdict(list)
        for row in rows:
            buckets[str(row[key])].append(row)
        groups[key] = {name: summarize(items) for name, items in sorted(buckets.items())}
    family_scores = []
    for family, items in defaultdict(list, {k: [x for x in rows if x["family_id"] == k] for k in {x["family_id"] for x in rows}}).items():
        family_scores.append((family, summarize(items)))
    output = {
        "bootstrap": bootstrap(rows),
        "family_count": len(family_scores),
        "groups": groups,
        "hard_families": sorted(
            [
                {"family_id": family, **metrics}
                for family, metrics in family_scores
                if metrics["relation"] < 0.8 or metrics["handling"] < 0.8
            ],
            key=lambda x: (x["relation"], x["handling"]),
        )[:20],
        "overall": summarize(rows),
        "schema": "macerd_cluster_error_analysis_v1",
    }
    (P / "CLUSTER_ERROR_ANALYSIS.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"overall": output["overall"], "bootstrap": output["bootstrap"]}, sort_keys=True))


if __name__ == "__main__":
    main()
