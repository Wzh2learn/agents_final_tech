"""Model adjudication on the MA-CERD uncertainty queue."""

import json
import sys
from collections import Counter
from pathlib import Path

P = Path(__file__).resolve().parent
FINRANK = P.parent / "research_direction_sprint_20261020_v1/execution_v2/finrank_dev"
sys.path.insert(0, str(FINRANK))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json

RUN_ID = "MACERD_UNCERTAINTY_ADJUDICATION_20261020"
DATA = P / "release/data/ma_cerd_gold_public_v1.jsonl"
LEDGER = P.parent / "research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json"
RUNTIME = P.parent / "tatqa_wp0_2026/history_collection_execution_v1/RUNTIME_IDENTITY_SNAPSHOT.json"
RAW = P / "raw/MACERD_UNCERTAINTY_ADJUDICATION_V1"


def f1(gold, pred):
    gold, pred = set(gold), set(pred)
    if not gold and not pred: return 1.0
    if not gold or not pred: return 0.0
    p, r = len(gold & pred) / len(pred), len(gold & pred) / len(gold)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def compact(row):
    nodes = row["base_snapshot"]["joint_plan"]["nodes"]
    resources = set(row["base_snapshot"]["team_state"]["candidate_features"].get("resource_ids", []))
    return {
        "requirements": row["base_snapshot"]["requirements"],
        "evidence": row["base_snapshot"]["evidence"],
        "team_state": row["base_snapshot"]["team_state"],
        "plan_nodes": nodes,
        "intervention": row["intervention"],
        "counterfactual_requirements": row["counterfactual_snapshot"]["requirements"],
        "counterfactual_evidence": row["counterfactual_snapshot"]["evidence"],
        "o1_relation": row["oracle_bundle"]["rule_oracle"]["relation"],
        "o3_relation": row["oracle_bundle"]["simulator_outcome"]["relation"],
        "changed_signature_fields": row["oracle_bundle"]["rule_oracle"].get("changed_signature_fields", []),
        "graph_impact_candidates": [n["node_id"] for n in nodes if n.get("agent_id") in resources],
    }


def main():
    rows = [json.loads(x) for x in DATA.read_text().splitlines()]
    queue = [
        row for row in rows
        if row["oracle_bundle"]["alignment"] == "o1_only_disagrees"
        or tuple(row["oracle_bundle"]["rule_oracle"].get("changed_signature_fields", [])) == ("blocking_requirements",)
    ]
    assert len(queue) == 250
    runtime = load_object(RUNTIME)["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 497:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw, out = HttpChatAdapter("http://127.0.0.1:8004", 120), ImmutableRawStore(RAW), []
    for row in queue:
        prompt = (
            "Adjudicate the uncertain case using only the public evidence layers and graph candidates. "
            "Return only JSON with relation,acceptable_decisions,impact_node_ids,preserved_node_ids. "
            "relation must be change or invariant; decisions must be a subset of execute,repair,defer. "
            "TASK=" + json.dumps(compact(row), sort_keys=True)
        )
        payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": prompt}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
        key = row["contract_id"]
        record = ledger.reserve(RUN_ID, key, sha256_text(payload))
        root = None
        try:
            _, root = raw.begin_request(key, payload)
            response = adapter.complete(payload)
            raw.persist_response(root, response)
            parsed = parse_chat_response(response)
        except Exception as exc:
            ledger.settle(record, "FAILED", None, str(exc))
            if root: raw.mark_crash(root, str(exc))
            raise
        ledger.settle(record, "OK", int(parsed["usage"]["total_tokens"]))
        try:
            pred = json.loads(parsed["content"])
            valid = set(pred) == {"relation", "acceptable_decisions", "impact_node_ids", "preserved_node_ids"}
        except Exception:
            pred, valid = None, False
        labels = row["labels"]
        scores = {
            "relation": valid and pred["relation"] == labels["relation"],
            "handling": valid and set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]),
            "impact_f1": f1(labels["impact_node_ids"], pred["impact_node_ids"]) if valid else 0.0,
            "preserved_f1": f1(labels["preserved_node_ids"], pred["preserved_node_ids"]) if valid else 0.0,
        }
        scores["exact"] = all([scores["relation"], scores["handling"], scores["impact_f1"] == 1.0, scores["preserved_f1"] == 1.0])
        out.append({"contract_id": row["contract_id"], "family_id": row["family_id"], "alignment": row["oracle_bundle"]["alignment"], "prediction": pred, "scores": scores, "valid": valid, "total_tokens": int(parsed["usage"]["total_tokens"])})
        write_json(P / "UNCERTAINTY_ADJUDICATION_PARTIAL.json", {"rows": out})
    summary = {
        "valid": sum(x["valid"] for x in out),
        "relation": sum(x["scores"]["relation"] for x in out) / len(out),
        "handling": sum(x["scores"]["handling"] for x in out) / len(out),
        "impact_f1": sum(x["scores"]["impact_f1"] for x in out) / len(out),
        "preserved_f1": sum(x["scores"]["preserved_f1"] for x in out) / len(out),
        "exact": sum(x["scores"]["exact"] for x in out) / len(out),
    }
    result = {
        "evidence_identity": "INDEPENDENT_MACERD_UNCERTAINTY_DEVELOPMENT",
        "generation_requests": len(queue),
        "rows": out,
        "run_accounting_tokens": sum(x["total_tokens"] for x in out),
        "schema": "macerd_uncertainty_adjudication_result_v1",
        "status": "COMPLETE",
        "summary": summary,
    }
    write_json(P / "UNCERTAINTY_ADJUDICATION_RESULT.json", result)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
