"""Read-only recomputation of existing research artifacts; no model or network I/O."""

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MA = ROOT / "research/ma_cerd_independent_v1"
INPUTS = {
    "gold": MA / "release/data/ma_cerd_gold_public_v1.jsonl",
    "adjudicator": MA / "predictions/adjudicator_resource_oracle.jsonl",
    "uncertainty": MA / "UNCERTAINTY_ADJUDICATION_RESULT.json",
    "ledger": ROOT / "research/research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json",
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def f1(expected, predicted):
    expected, predicted = set(expected), set(predicted)
    if not expected and not predicted:
        return 1.0
    return 2 * len(expected & predicted) / (len(expected) + len(predicted))


def is_queue(row):
    return (
        row["oracle_bundle"]["alignment"] == "o1_only_disagrees"
        or row["oracle_bundle"]["rule_oracle"].get("changed_signature_fields", []) == ["blocking_requirements"]
    )


def summarize(rows, predictions):
    if not rows:
        return {"records": 0}
    sums = Counter()
    for row in rows:
        labels, pred = row["labels"], predictions[row["contract_id"]]
        sums["relation"] += pred["relation"] == labels["relation"]
        sums["handling_exact"] += set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"])
        sums["impact_f1"] += f1(labels["impact_node_ids"], pred["impact_node_ids"])
        sums["preserved_f1"] += f1(labels["preserved_node_ids"], pred["preserved_node_ids"])
    return {
        "records": len(rows),
        "families": len({r["family_id"] for r in rows}),
        **{name: value / len(rows) for name, value in sums.items()},
    }


def main():
    gold = read_jsonl(INPUTS["gold"])
    by_id = {r["contract_id"]: r for r in gold}
    preds = {r["contract_id"]: r for r in read_jsonl(INPUTS["adjudicator"])}
    uncertainty = json.loads(INPUTS["uncertainty"].read_text(encoding="utf-8"))
    ledger = json.loads(INPUTS["ledger"].read_text(encoding="utf-8"))
    assert len(gold) == len(by_id) == len(preds) == 1000
    assert len({r["family_id"] for r in gold}) == 100
    assert {r["contract_id"] for r in gold if is_queue(r)} == {
        r["contract_id"] for r in gold
        if r["oracle_bundle"]["rule_oracle"].get("changed_signature_fields", []) == ["blocking_requirements"]
    }
    partitions = {}
    for partition in ["all", "train", "development", "test"]:
        rows = gold if partition == "all" else [r for r in gold if r["partition"] == partition]
        partitions[partition] = {
            "all": summarize(rows, preds),
            "queue": summarize([r for r in rows if is_queue(r)], preds),
            "non_queue": summarize([r for r in rows if not is_queue(r)], preds),
        }
    decision_counts, gold_counts = Counter(), Counter()
    exact = subset = intersects = defer_only = defer_admissible = 0
    precision_sum = recall_sum = 0.0
    uncertainty_preds = {}
    for record in uncertainty["rows"]:
        row = by_id[record["contract_id"]]
        pred = record["prediction"]
        uncertainty_preds[record["contract_id"]] = pred
        actual, expected = set(pred["acceptable_decisions"]), set(row["labels"]["acceptable_decisions"])
        decision_counts[",".join(sorted(actual))] += 1
        gold_counts[",".join(sorted(expected))] += 1
        exact += actual == expected
        subset += bool(actual) and actual <= expected
        intersects += bool(actual & expected)
        defer_only += actual == {"defer"}
        defer_admissible += actual == {"defer"} and "defer" in expected
        precision_sum += len(actual & expected) / len(actual) if actual else 0.0
        recall_sum += len(actual & expected) / len(expected)
    assert len(uncertainty_preds) == 250
    assert exact == 3 and defer_only == defer_admissible == 241
    budget = ledger["new_generation_budget"]
    records = ledger["request_records"]
    assert len(records) == budget["requests_used"] == 747
    tokens = sum(r["accounting_tokens"] for r in records)
    assert tokens == budget["accounting_tokens_used"] == 1564176
    result = {
        "identity": "OWNER_REVIEW_POST_HOC_RECOMPUTATION_NOT_NEW_EXPERIMENT",
        "review_date": "2026-10-21",
        "model_requests_made_by_this_script": 0,
        "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in INPUTS.items()},
        "adjudicator_by_partition": partitions,
        "queue_equivalent_to_public_blocking_signature_in_this_release": True,
        "model_queue_original_metrics": summarize([r for r in gold if is_queue(r)], uncertainty_preds),
        "handling_post_hoc_diagnostics": {
            "records": len(uncertainty_preds),
            "prediction_sets": dict(decision_counts),
            "gold_sets": dict(gold_counts),
            "exact_sets": exact,
            "nonempty_gold_subset": subset,
            "nonempty_gold_intersection": intersects,
            "defer_only": defer_only,
            "defer_only_admissible": defer_admissible,
            "macro_set_precision": precision_sum / len(uncertainty_preds),
            "macro_set_recall": recall_sum / len(uncertainty_preds),
            "warning": "Admissibility and set overlap do not establish task completion or utility; no action-selection policy is evaluated here.",
        },
        "ledger": {
            "accounting_events": len(records),
            "statuses": dict(Counter(r["status"] for r in records)),
            "accounting_tokens": tokens,
            "requests_remaining": budget["request_cap"] - budget["requests_used"],
            "tokens_remaining": budget["token_cap"] - tokens,
            "warning": "Budget events do not necessarily equal physical HTTP requests; authorization provenance needs separate review.",
        },
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional new review receipt; source artifacts stay untouched.")
    args = parser.parse_args()
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(json.dumps({"receipt": str(args.output), "checks": "PASS", "model_requests": 0}))
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
