"""DEV_ONLY budget sweep over the frozen adaptive-revalidation fixtures."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.adaptive_revalidation_v2.fixtures import load_frozen_scenarios
from research.adaptive_revalidation_v2.model import PolicyKind, PolicySpec
from research.adaptive_revalidation_v2.runner import experiment_as_dict, run_experiment


OUTPUT = Path(__file__).resolve().parent / "ADAPTIVE_BUDGET_SWEEP.json"
SCENARIOS = load_frozen_scenarios()
POLICIES = (
    PolicySpec(PolicyKind.NO_CHECK),
    PolicySpec(PolicyKind.RANDOM_CHECK, seed=20261021),
    PolicySpec(PolicyKind.UNIT_COST_GREEDY),
    PolicySpec(PolicyKind.TWO_STEP_LOOKAHEAD),
    PolicySpec(PolicyKind.FULL_RECOMPUTE),
)


def main() -> int:
    rows: list[dict[str, Any]] = []
    for budget in range(10):
        scenarios = [dataclasses.replace(item, query_budget=budget) for item in SCENARIOS]
        result = experiment_as_dict(run_experiment(scenarios, POLICIES))
        for policy, summary in result["policy_aggregate"].items():
            metrics = summary["metrics"]
            rows.append(
                {
                    "query_budget": budget,
                    "policy": policy,
                    "final_action_loss": metrics["final_action_loss"],
                    "repair_loss": metrics["repair_loss"],
                    "query_cost": metrics["query_cost"],
                    "recomputation_cost": metrics["recomputation_cost"],
                    "missed_invalidation": metrics["missed_invalidation"],
                    "over_invalidation": metrics["over_invalidation"],
                    "regression_rate": metrics["regression_rate"],
                    "completion": metrics["completion"],
                    "abstention": metrics["abstention"],
                }
            )
    non_oracle = [row for row in rows if row["policy"] != "full_recompute"]
    frontier: list[dict[str, Any]] = []
    for row in sorted(non_oracle, key=lambda item: (item["query_cost"], item["final_action_loss"], item["policy"])):
        if not any(
            item["query_cost"] <= row["query_cost"]
            and item["final_action_loss"] <= row["final_action_loss"]
            and (
                item["query_cost"] < row["query_cost"]
                or item["final_action_loss"] < row["final_action_loss"]
            )
            for item in frontier
        ):
            frontier.append(row)
    payload = {
        "schema": "adaptive_revalidation_budget_sweep_v1",
        "evidence_identity": "DEV_ONLY_AUTHORED_MECHANISM_FIXTURES",
        "budgets": list(range(10)),
        "scenario_count": len(SCENARIOS),
        "rows": rows,
        "cost_action_frontier": frontier,
        "nonclaims": [
            "No model or external task was evaluated.",
            "The sweep identifies fixture headroom only.",
            "A frontier point is not evidence of general query-policy superiority.",
        ],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "rows": len(rows), "frontier": len(frontier)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
