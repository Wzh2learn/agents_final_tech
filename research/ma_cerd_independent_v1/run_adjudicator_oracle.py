"""Train-calibrated transparent relation adjudicator plus resource graph."""

import json
from collections import Counter, defaultdict
from pathlib import Path

P = Path(__file__).resolve().parent
GOLD = P / "release/data/ma_cerd_gold_public_v1.jsonl"
OUT = P / "predictions/adjudicator_resource_oracle.jsonl"


def signature(row):
    return tuple(row["oracle_bundle"]["rule_oracle"].get("changed_signature_fields", []))


def fit_relation(rows):
    counts = defaultdict(Counter)
    for row in rows:
        if row["partition"] != "train":
            continue
        counts[signature(row)][row["labels"]["relation"]] += 1
    return {key: value.most_common(1)[0][0] for key, value in counts.items()}


def fit_handling(rows):
    counts = defaultdict(Counter)
    for row in rows:
        if row["partition"] != "train":
            continue
        counts[signature(row)][tuple(sorted(row["labels"]["acceptable_decisions"]))] += 1
    return {key: list(value.most_common(1)[0][0]) for key, value in counts.items()}


def main():
    rows = [json.loads(x) for x in GOLD.read_text().splitlines()]
    relation_rule = fit_relation(rows)
    handling_rule = fit_handling(rows)
    predictions = []
    for row in rows:
        nodes = {n["node_id"]: n for n in row["base_snapshot"]["joint_plan"]["nodes"]}
        resources = set(row["base_snapshot"]["team_state"]["candidate_features"].get("resource_ids", []))
        relation = relation_rule[signature(row)]
        impact = [nid for nid, node in nodes.items() if node.get("agent_id") in resources] if relation == "change" else []
        preserved = [nid for nid in nodes if nid not in impact]
        predictions.append({
            "contract_id": row["contract_id"],
            "relation": relation,
            "acceptable_decisions": handling_rule[signature(row)],
            "impact_node_ids": impact,
            "preserved_node_ids": preserved,
        })
    OUT.write_text("\n".join(json.dumps(x, sort_keys=True) for x in predictions) + "\n")
    print(json.dumps({"relation_rule": {str(k): v for k,v in relation_rule.items()}, "handling_rule": {str(k): v for k,v in handling_rule.items()}, "records": len(predictions), "path": str(OUT)}))


if __name__ == "__main__":
    main()
