"""DEV_ONLY headroom probe for selective evidence acquisition."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EVIDENCE_IDENTITY = "DEV_ONLY_MIXED_NATURAL_STATE_AND_SYNTHETIC_CONTROL_PROBE"


@dataclass(frozen=True)
class Case:
    case_id: str
    identity: str
    truth: str
    actor: dict[str, Any]
    outcomes: dict[str, Any]
    source: str


@dataclass(frozen=True)
class Action:
    name: str
    cost: int


ACTIONS = {
    "preflight": Action("preflight", 1),
    "simple_contract": Action("simple_contract", 1),
    "behavior": Action("behavior", 3),
    "enhanced_consumption": Action("enhanced_consumption", 4),
}


def cases() -> list[Case]:
    return [
        Case(
            "ntrip_base_fallback",
            "NATURAL_MODEL_OUTPUT",
            "INVALID",
            {
                "preflight_ok": True,
                "fallback_risk": True,
                "dependency_contract_gap": True,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": False,
                "behavior": True,
                "enhanced_consumption": False,
            },
            "NtripBrowser BASE output with swallowed old-API failure and UTF-8 fallback",
        ),
        Case(
            "ntrip_prose_valid",
            "NATURAL_MODEL_OUTPUT",
            "VALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": True,
                "behavior": True,
                "enhanced_consumption": True,
            },
            "NtripBrowser PROSE_CHANGE_FACTS output",
        ),
        Case(
            "ntrip_structured_valid",
            "NATURAL_MODEL_OUTPUT",
            "VALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": True,
                "behavior": True,
                "enhanced_consumption": True,
            },
            "NtripBrowser STRUCTURED_CHANGE_FACTS output",
        ),
        Case(
            "datetimerange_environment",
            "NATURAL_ENVIRONMENT_FAILURE",
            "ENVIRONMENT_INVALID",
            {
                "preflight_ok": False,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": False,
            },
            {
                "preflight": False,
                "simple_contract": False,
                "behavior": False,
                "enhanced_consumption": False,
            },
            "PyMigBench DateTimeRange gold environment failed before valid classification",
        ),
        Case(
            "control_valid_alias",
            "SYNTHETIC_CONTROL",
            "VALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": True,
            },
            {
                "preflight": True,
                "simple_contract": False,
                "behavior": True,
                "enhanced_consumption": True,
            },
            "Target dependency consumed through an alias",
        ),
        Case(
            "control_valid_wrapper",
            "SYNTHETIC_CONTROL",
            "VALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": True,
            },
            {
                "preflight": True,
                "simple_contract": False,
                "behavior": True,
                "enhanced_consumption": True,
            },
            "Target dependency consumed through a wrapper or adapter",
        ),
        Case(
            "control_fallback_masked",
            "SYNTHETIC_CONTROL",
            "INVALID",
            {
                "preflight_ok": True,
                "fallback_risk": True,
                "dependency_contract_gap": True,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": False,
                "behavior": True,
                "enhanced_consumption": False,
            },
            "Default or fallback preserves fixtures while target dependency is unused",
        ),
        Case(
            "control_dead_target_call",
            "SYNTHETIC_CONTROL",
            "INVALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": True,
                "behavior": True,
                "enhanced_consumption": False,
            },
            "Dead-code target call satisfies presence checks but result is not consumed",
        ),
        Case(
            "control_behavior_regression",
            "SYNTHETIC_CONTROL",
            "INVALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": False,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": True,
                "behavior": False,
                "enhanced_consumption": True,
            },
            "Target dependency is consumed but behavior regresses",
        ),
        Case(
            "control_clean_valid",
            "SYNTHETIC_CONTROL",
            "VALID",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": False,
                "dynamic_import_risk": False,
            },
            {
                "preflight": True,
                "simple_contract": True,
                "behavior": True,
                "enhanced_consumption": True,
            },
            "Ordinary valid migration without risk flags",
        ),
        Case(
            "control_dynamic_unresolved",
            "SYNTHETIC_CONTROL",
            "UNRESOLVED",
            {
                "preflight_ok": True,
                "fallback_risk": False,
                "dependency_contract_gap": True,
                "dynamic_import_risk": True,
            },
            {
                "preflight": True,
                "simple_contract": False,
                "behavior": True,
                "enhanced_consumption": None,
            },
            "Dynamic import cannot be resolved by the current evidence tools",
        ),
    ]


def decide_from_outcomes(
    observed: dict[str, Any], dynamic_import_risk: bool
) -> str:
    if observed.get("preflight") is False:
        return "DEFER_ENVIRONMENT"
    if observed.get("behavior") is False:
        return "REJECT"
    if observed.get("enhanced_consumption") is False:
        return "REJECT"
    if observed.get("enhanced_consumption") is True and observed.get("behavior") is True:
        return "ACCEPT"
    if observed.get("simple_contract") is True and observed.get("behavior") is True:
        return "ACCEPT"
    if observed.get("simple_contract") is False and dynamic_import_risk:
        return "DEFER"
    if observed.get("simple_contract") is False:
        return "REJECT"
    return "DEFER"


def run_strategy(case: Case, strategy: str) -> dict[str, Any]:
    observed: dict[str, Any] = {}
    used: list[str] = []

    def run(name: str) -> None:
        used.append(name)
        observed[name] = case.outcomes[name]

    if strategy == "no_revalidation":
        decision = "ACCEPT"
    elif strategy == "behavior_only":
        run("behavior")
        decision = "ACCEPT" if observed["behavior"] else "REJECT"
    elif strategy == "contract_only":
        run("simple_contract")
        decision = "ACCEPT" if observed["simple_contract"] else "REJECT"
    elif strategy == "hybrid_fixed":
        run("behavior")
        run("simple_contract")
        decision = "ACCEPT" if observed["behavior"] and observed["simple_contract"] else "REJECT"
    elif strategy == "full_revalidation":
        for name in ("preflight", "simple_contract", "behavior", "enhanced_consumption"):
            run(name)
        decision = decide_from_outcomes(observed, case.actor["dynamic_import_risk"])
    elif strategy == "fixed_order":
        run("preflight")
        if not observed["preflight"]:
            decision = "DEFER_ENVIRONMENT"
        else:
            run("behavior")
            run("simple_contract")
            decision = decide_from_outcomes(observed, case.actor["dynamic_import_risk"])
            if decision == "DEFER":
                run("enhanced_consumption")
                decision = decide_from_outcomes(
                    observed, case.actor["dynamic_import_risk"]
                )
    elif strategy == "risk_greedy":
        run("preflight")
        if not observed["preflight"]:
            decision = "DEFER_ENVIRONMENT"
        elif (
            case.actor["fallback_risk"]
            or case.actor["dependency_contract_gap"]
            or case.actor["dynamic_import_risk"]
        ):
            run("enhanced_consumption")
            if observed["enhanced_consumption"] is False:
                decision = "REJECT"
            elif observed["enhanced_consumption"] is None:
                decision = "DEFER"
            else:
                run("behavior")
                decision = decide_from_outcomes(
                    observed, case.actor["dynamic_import_risk"]
                )
        else:
            run("behavior")
            if not observed["behavior"]:
                decision = "REJECT"
            else:
                run("simple_contract")
                decision = decide_from_outcomes(
                    observed, case.actor["dynamic_import_risk"]
                )
    else:
        raise ValueError(f"unknown strategy: {strategy}")
    cost = sum(ACTIONS[name].cost for name in used)
    return {
        "decision": decision,
        "actions": used,
        "cost": cost,
        "observed": observed,
    }


def expected_decision(truth: str) -> str:
    return {
        "VALID": "ACCEPT",
        "INVALID": "REJECT",
        "UNRESOLVED": "DEFER",
        "ENVIRONMENT_INVALID": "DEFER_ENVIRONMENT",
    }[truth]


def evaluate(strategy: str, cases_: list[Case]) -> dict[str, Any]:
    rows = []
    for case in cases_:
        result = run_strategy(case, strategy)
        expected = expected_decision(case.truth)
        rows.append(
            {
                "case_id": case.case_id,
                "identity": case.identity,
                "truth": case.truth,
                "expected": expected,
                **result,
                "correct": result["decision"] == expected,
                "false_accept": case.truth == "INVALID" and result["decision"] == "ACCEPT",
                "false_reject": case.truth == "VALID" and result["decision"] == "REJECT",
                "unresolved": result["decision"].startswith("DEFER"),
            }
        )
    return {
        "strategy": strategy,
        "cases": len(rows),
        "correct": sum(row["correct"] for row in rows),
        "false_accept": sum(row["false_accept"] for row in rows),
        "false_reject": sum(row["false_reject"] for row in rows),
        "unresolved": sum(row["unresolved"] for row in rows),
        "coverage": round(
            sum(not row["unresolved"] for row in rows) / len(rows), 4
        ),
        "total_cost": sum(row["cost"] for row in rows),
        "rows": rows,
    }


def build_results() -> dict[str, Any]:
    strategies = [
        "no_revalidation",
        "behavior_only",
        "contract_only",
        "hybrid_fixed",
        "full_revalidation",
        "fixed_order",
        "risk_greedy",
    ]
    cases_ = cases()
    results = {name: evaluate(name, cases_) for name in strategies}
    full = results["hybrid_fixed"]
    greedy = results["risk_greedy"]
    return {
        "schema": "g3_decision_probe_results_v1",
        "evidence_identity": EVIDENCE_IDENTITY,
        "case_counts": {
            "natural_model_output": sum(
                case.identity == "NATURAL_MODEL_OUTPUT" for case in cases_
            ),
            "natural_environment_failure": sum(
                case.identity == "NATURAL_ENVIRONMENT_FAILURE" for case in cases_
            ),
            "synthetic_control": sum(
                case.identity == "SYNTHETIC_CONTROL" for case in cases_
            ),
        },
        "action_costs": {
            name: action.cost for name, action in ACTIONS.items()
        },
        "strategies": results,
        "headroom": {
            "greedy_same_errors_as_hybrid": (
                greedy["false_accept"] == full["false_accept"]
                and greedy["false_reject"] == full["false_reject"]
            ),
            "greedy_cost_delta_vs_hybrid": greedy["total_cost"] - full["total_cost"],
            "greedy_same_decisions_as_full": (
                [row["decision"] for row in greedy["rows"]]
                == [
                    row["decision"]
                    for row in results["full_revalidation"]["rows"]
                ]
            ),
            "greedy_cost_delta_vs_full": (
                greedy["total_cost"] - results["full_revalidation"]["total_cost"]
            ),
            "behavior_only_false_accepts": results["behavior_only"]["false_accept"],
            "contract_only_false_accepts": results["contract_only"]["false_accept"],
            "risk_greedy_has_cost_or_risk_space": (
                greedy["total_cost"] < full["total_cost"]
                or greedy["false_accept"] < full["false_accept"]
                or greedy["false_reject"] < full["false_reject"]
            ),
        },
        "nonclaims": [
            "Synthetic controls test mechanism coverage, not natural error prevalence.",
            "Three natural model outputs are one task, not independent tasks.",
            "The probe does not validate a learned policy or a general adaptive method.",
            "No LoRA/SFT or Memory learning target is established.",
        ],
    }


def write_results(path: Path) -> None:
    path.write_text(
        json.dumps(build_results(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    write_results(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
