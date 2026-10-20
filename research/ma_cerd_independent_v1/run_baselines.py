"""Produce three deterministic MA-CERD baselines."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOLD = ROOT / "release/data/ma_cerd_gold_public_v1.jsonl"
OUT = ROOT / "predictions"
OUT.mkdir(exist_ok=True)


def write(name, rows):
    path = OUT / f"{name}.jsonl"
    path.write_text("\n".join(json.dumps(x, sort_keys=True) for x in rows) + "\n")
    return path


def main():
    gold = [json.loads(x) for x in GOLD.read_text().splitlines()]
    baselines = {"base_copy": [], "all_change": [], "oracle": []}
    for row in gold:
        cid = row["contract_id"]
        nodes = [x["node_id"] for x in row["base_snapshot"]["joint_plan"]["nodes"]]
        decision = row["base_snapshot"]["joint_plan"]["decision"]
        baselines["base_copy"].append({
            "contract_id": cid,
            "relation": "invariant",
            "acceptable_decisions": [decision],
            "impact_node_ids": [],
            "preserved_node_ids": nodes,
        })
        baselines["all_change"].append({
            "contract_id": cid,
            "relation": "change",
            "acceptable_decisions": ["repair", "defer"],
            "impact_node_ids": nodes,
            "preserved_node_ids": [],
        })
        baselines["oracle"].append({
            "contract_id": cid,
            "relation": row["labels"]["relation"],
            "acceptable_decisions": row["labels"]["acceptable_decisions"],
            "impact_node_ids": row["labels"]["impact_node_ids"],
            "preserved_node_ids": row["labels"]["preserved_node_ids"],
        })
    for name, rows in baselines.items():
        write(name, rows)
    print(json.dumps({name: len(rows) for name, rows in baselines.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
