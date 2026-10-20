"""O1-assisted resource-graph impact baseline for MA-CERD."""

import json
from pathlib import Path

P = Path(__file__).resolve().parent
GOLD = P / "release/data/ma_cerd_gold_public_v1.jsonl"
OUT = P / "predictions/graph_resource_oracle.jsonl"


def main():
    rows = [json.loads(x) for x in GOLD.read_text().splitlines()]
    predictions = []
    for row in rows:
        nodes = {n["node_id"]: n for n in row["base_snapshot"]["joint_plan"]["nodes"]}
        resources = set(row["base_snapshot"]["team_state"]["candidate_features"].get("resource_ids", []))
        relation = row["oracle_bundle"]["rule_oracle"]["relation"]
        impact = [nid for nid, node in nodes.items() if node.get("agent_id") in resources] if relation == "change" else []
        preserved = [nid for nid in nodes if nid not in impact]
        predictions.append({
            "contract_id": row["contract_id"],
            "relation": relation,
            "acceptable_decisions": ["repair", "defer"] if relation == "change" else [row["base_snapshot"]["joint_plan"]["decision"]],
            "impact_node_ids": impact,
            "preserved_node_ids": preserved,
        })
    OUT.write_text("\n".join(json.dumps(x, sort_keys=True) for x in predictions) + "\n")
    print(json.dumps({"records": len(predictions), "path": str(OUT)}))


if __name__ == "__main__":
    main()
