"""Compare fresh derivation against the prior-anchored wrong-prior result."""

import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
FINRANK = P.parent / "research_direction_sprint_20261020_v1/execution_v2/finrank_dev"
sys.path.insert(0, str(FINRANK))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json

RUN_ID = "MACERD_FRESH_DERIVATION_V2_20261020"
DATA = P / "release/data/ma_cerd_gold_public_v1.jsonl"
LEDGER = P.parent / "research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json"
RUNTIME = P.parent / "tatqa_wp0_2026/history_collection_execution_v1/RUNTIME_IDENTITY_SNAPSHOT.json"
RAW = P / "raw/MACERD_FRESH_DERIVATION_V2"


def f1(gold, pred):
    gold, pred = set(gold), set(pred)
    if not gold and not pred: return 1.0
    if not gold or not pred: return 0.0
    p, r = len(gold & pred) / len(pred), len(gold & pred) / len(gold)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def main():
    matched = load_json = json.loads((P / "MATCHED_FEEDBACK_RESULT.json").read_text())
    ids = matched["selected_contract_ids"]
    rows = {x["contract_id"]: x for x in map(json.loads, DATA.read_text().splitlines())}
    runtime = load_object(RUNTIME)["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 363:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw, out = HttpChatAdapter("http://127.0.0.1:8004", 120), ImmutableRawStore(RAW), []
    for cid in ids:
        row = rows[cid]
        compact = {
            "requirements": row["base_snapshot"]["requirements"],
            "evidence": row["base_snapshot"]["evidence"],
            "team_state": row["base_snapshot"]["team_state"],
            "plan_nodes": row["base_snapshot"]["joint_plan"]["nodes"],
            "intervention": row["intervention"],
            "counterfactual_requirements": row["counterfactual_snapshot"]["requirements"],
            "counterfactual_evidence": row["counterfactual_snapshot"]["evidence"],
        }
        prompt = (
            "Derive from the task only. Do not assume any prior answer. "
            "Return only JSON with relation,acceptable_decisions,impact_node_ids,preserved_node_ids. "
            "relation must be exactly change or invariant. acceptable_decisions must be a subset of execute, repair, defer. "
            "TASK=" + json.dumps(compact, sort_keys=True)
        )
        payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": prompt}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
        record = ledger.reserve(RUN_ID, cid, sha256_text(payload))
        root = None
        try:
            _, root = raw.begin_request(cid, payload)
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
            valid = set(pred) == {"relation","acceptable_decisions","impact_node_ids","preserved_node_ids"}
        except Exception:
            pred, valid = None, False
        labels = row["labels"]
        scores = {
            "relation": pred["relation"] == labels["relation"] if valid else False,
            "handling": set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]) if valid else False,
            "impact_f1": f1(labels["impact_node_ids"], pred["impact_node_ids"]) if valid else 0.0,
            "preserved_f1": f1(labels["preserved_node_ids"], pred["preserved_node_ids"]) if valid else 0.0,
            "exact": valid and pred["relation"] == labels["relation"] and set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]) and set(pred["impact_node_ids"]) == set(labels["impact_node_ids"]) and set(pred["preserved_node_ids"]) == set(labels["preserved_node_ids"]),
        }
        out.append({"contract_id":cid,"prediction":pred,"scores":scores,"valid":valid,"total_tokens":int(parsed["usage"]["total_tokens"])})
        write_json(P/"FRESH_DERIVATION_PARTIAL_V2.json",{"rows":out})
    summary = {"valid":sum(x["valid"] for x in out),"relation":sum(x["scores"]["relation"] for x in out),"handling":sum(x["scores"]["handling"] for x in out),"impact_f1":sum(x["scores"]["impact_f1"] for x in out)/15,"preserved_f1":sum(x["scores"]["preserved_f1"] for x in out)/15,"exact":sum(x["scores"]["exact"] for x in out)}
    result = {"evidence_identity":"INDEPENDENT_MACERD_DEVELOPMENT","generation_requests":15,"rows":out,"run_accounting_tokens":sum(x["total_tokens"] for x in out),"schema":"macerd_fresh_derivation_result_v1","status":"COMPLETE","summary":summary}
    write_json(P/"FRESH_DERIVATION_RESULT_V2.json",result)
    print(json.dumps(summary,sort_keys=True))


if __name__ == "__main__":
    main()
