"""Real-model query-policy scout on the frozen DEV_ONLY environment."""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from research.adaptive_revalidation_v2.environment import ThinEnvironment
from research.adaptive_revalidation_v2.fixtures import CHECKER_GRAPH, load_frozen_scenarios
from research.adaptive_revalidation_v2.metrics import evaluate_action
from research.adaptive_revalidation_v2.model import EvidenceBundle
from research.adaptive_revalidation_v2.repairer import FixedRepairer

BASE = Path(__file__).resolve().parent
SPEC = json.loads((BASE / "SCOUT_SPEC.json").read_text(encoding="utf-8"))
RAW = BASE / "raw"
LEDGER_PATH = BASE / "MODEL_QUERY_SCOUT_LEDGER.json"
RESULT_PATH = BASE / "MODEL_QUERY_SCOUT_RESULT.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def legal_queries(actor_input: Any) -> list[dict[str, Any]]:
    queries = [
        {"action": "inspect_dependency", "arguments": {"node_id": node_id}}
        for node_id in actor_input.node_ids
    ]
    queries.extend(
        {"action": "inspect_change", "arguments": {"change_id": change.change_id}}
        for change in actor_input.changes
    )
    queries.extend(
        {"action": "run_target_test", "arguments": {"output_id": output_id}}
        for output_id in actor_input.output_ids
    )
    return queries


def request_model(prompt: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    payload = {
        "model": SPEC["model"]["model"],
        "messages": [{"role": "user", "content": prompt}],
        **SPEC["generation"],
    }
    payload["chat_template_kwargs"] = {"enable_thinking": payload.pop("enable_thinking")}
    request_hash = payload_hash(payload)
    req = urllib.request.Request(
        SPEC["model"]["endpoint"],
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return payload, {"error": type(exc).__name__, "detail": str(exc)}, request_hash
    return payload, body, request_hash


def parse_decision(content: str, legal: list[dict[str, Any]]) -> dict[str, Any]:
    value = json.loads(content)
    if not isinstance(value, dict) or not isinstance(value.get("stop"), bool) or not isinstance(value.get("reason_code"), str):
        raise ValueError("decision_envelope")
    if value["stop"]:
        if set(value) != {"stop", "reason_code"}:
            raise ValueError("stop_keys")
        return value
    if set(value) != {"stop", "action", "arguments", "reason_code"}:
        raise ValueError("query_keys")
    decision = {"action": value["action"], "arguments": value["arguments"]}
    if decision not in legal:
        raise ValueError("illegal_query")
    return value


def main() -> int:
    scenarios = load_frozen_scenarios()
    if len(scenarios) != SPEC["scenarios"]:
        raise RuntimeError("scenario_count_mismatch")
    ledger = {
        "schema": "model_query_policy_scout_ledger_v1",
        "reserved_attempts": SPEC["reserved_attempts"],
        "reserved_accounting_tokens": SPEC["reserved_accounting_tokens"],
        "attempts_used": 0,
        "physical_http_calls": 0,
        "accounting_tokens_used": 0,
        "records": [],
    }
    rows: list[dict[str, Any]] = []
    result = {
        "schema": "model_query_policy_scout_result_v1",
        "evidence_identity": SPEC["evidence_identity"],
        "status": "IN_PROGRESS",
        "model_id": SPEC["model"]["id"],
        "rows": rows,
    }
    write_json(LEDGER_PATH, ledger)
    write_json(RESULT_PATH, result)
    repairer = FixedRepairer()
    stop_reason = None
    for fixture_index, fixture in enumerate(scenarios):
        actor_input = fixture.actor_input(CHECKER_GRAPH)
        environment = ThinEnvironment(fixture, actor_input, CHECKER_GRAPH)
        records = []
        decisions = []
        for step in range(SPEC["query_budget_per_scenario"]):
            legal = legal_queries(actor_input)
            prompt = (
                "You select public checks for a bounded revalidation task. "
                "Use only the actor-visible input and returned evidence. Do not infer a hidden graph or Gold. "
                "Return exactly one JSON object. To query, use keys stop=false, action, arguments, reason_code; "
                "the action and arguments must exactly match one legal query. To stop early, use exactly "
                "keys stop=true and reason_code. "
                f"ACTOR_INPUT={json.dumps(actor_input.as_dict(), sort_keys=True)} "
                f"CURRENT_EVIDENCE={json.dumps([record.as_dict() for record in records], sort_keys=True)} "
                f"LEGAL_QUERIES={json.dumps(legal, sort_keys=True)}"
            )
            payload, body, request_hash = request_model(prompt)
            ledger["attempts_used"] += 1
            ledger["physical_http_calls"] += 1
            record = {
                "scenario_id": fixture.scenario_id,
                "step": step,
                "request_sha256": request_hash,
                "status": "FAILED",
                "raw_request": f"raw/{fixture.scenario_id}/{step}/request.json",
                "raw_response": f"raw/{fixture.scenario_id}/{step}/response.json",
            }
            if "error" in body:
                record["error"] = body
            else:
                try:
                    content = body["choices"][0]["message"]["content"]
                    decision = parse_decision(content, legal)
                    usage = int(body.get("usage", {}).get("total_tokens", 0) or 0)
                    if usage <= 0:
                        raise ValueError("usage_missing")
                    record.update({"status": "OK", "usage_total_tokens": usage, "decision": decision})
                    ledger["accounting_tokens_used"] += usage
                    decisions.append(decision)
                    if not decision["stop"]:
                        tool = getattr(environment, decision["action"])
                        evidence = tool(**decision["arguments"])
                        records.append(evidence)
                except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    record["error"] = {"type": type(exc).__name__, "detail": str(exc)}
            write_json(BASE / record["raw_request"], payload)
            write_json(BASE / record["raw_response"], body)
            ledger["records"].append(record)
            write_json(LEDGER_PATH, ledger)
            if record["status"] != "OK":
                stop_reason = "INTERFACE_FAILURE"
                break
            if decision["stop"]:
                break
        evidence_bundle = EvidenceBundle(actor_input, tuple(records))
        action = repairer.repair(evidence_bundle)
        metrics = evaluate_action(fixture, action, evidence_bundle, CHECKER_GRAPH)
        rows.append(
            {
                "scenario_id": fixture.scenario_id,
                "family": fixture.family,
                "model_queries": len(records),
                "model_stopped_early": bool(decisions and decisions[-1]["stop"]),
                "decisions": decisions,
                "action": action.as_dict(),
                "metrics": metrics.as_dict(),
            }
        )
        write_json(RESULT_PATH, result)
        if stop_reason:
            break
    sweep = json.loads((BASE.parent / "ADAPTIVE_BUDGET_SWEEP.json").read_text(encoding="utf-8"))
    greedy = next(
        row for row in sweep["rows"]
        if row["policy"] == "unit_cost_greedy" and row["query_budget"] == SPEC["query_budget_per_scenario"]
    )
    if rows:
        model_summary = {
            key: sum(row["metrics"][key] for row in rows) / len(rows)
            for key in (
                "final_action_loss",
                "repair_loss",
                "query_cost",
                "recomputation_cost",
                "missed_invalidation",
                "over_invalidation",
                "regression_rate",
                "completion",
                "abstention",
            )
        }
    else:
        model_summary = None
    result.update(
        {
            "status": "COMPLETE" if not stop_reason and len(rows) == len(scenarios) else "STOPPED",
            "stop_reason": stop_reason,
            "model_summary": model_summary,
            "baseline": greedy,
            "development_decision": (
                "PROCEED_TO_EXTERNAL_ADAPTER"
                if not stop_reason
                and model_summary is not None
                and model_summary["final_action_loss"] - greedy["final_action_loss"] <= 0.10
                and model_summary["query_cost"] <= SPEC["reserved_attempts"]
                else "STOP_MODEL_QUERY_POLICY"
            ),
        }
    )
    write_json(RESULT_PATH, result)
    write_json(LEDGER_PATH, ledger)
    print(
        json.dumps(
            {
                "status": result["status"],
                "decision": result["development_decision"],
                "attempts": ledger["attempts_used"],
                "tokens": ledger["accounting_tokens_used"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
