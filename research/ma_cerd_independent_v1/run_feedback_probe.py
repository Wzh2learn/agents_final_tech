"""Run matched and natural feedback probes on eight MA-CERD test cases."""

import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
FINRANK = P.parent / "research_direction_sprint_20261020_v1/execution_v2/finrank_dev"
sys.path.insert(0, str(FINRANK))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json

RUN_ID = "MACERD_FEEDBACK_PROBE_20261020"
SELECTED = ("ma-cerd-pair-0271", "ma-cerd-pair-0272", "ma-cerd-pair-0273", "ma-cerd-pair-0276", "ma-cerd-pair-0332", "ma-cerd-pair-0335", "ma-cerd-pair-0384", "ma-cerd-pair-0386")
ARMS = ("exact_match", "sufficiency_only", "composite")
MODES = ("natural", "matched_revise")
LEDGER = P.parent / "research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json"
RUNTIME = P.parent / "tatqa_wp0_2026/history_collection_execution_v1/RUNTIME_IDENTITY_SNAPSHOT.json"
DATA = P / "release/data/ma_cerd_gold_public_v1.jsonl"
RAW = P / "raw/MACERD_FEEDBACK_PROBE_V1"


def f1(gold, pred):
    gold, pred = set(gold), set(pred)
    if not gold and not pred: return 1.0
    if not gold or not pred: return 0.0
    p, r = len(gold & pred) / len(pred), len(gold & pred) / len(gold)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def score(pred, row):
    labels = row["labels"]
    return {
        "relation": pred["relation"] == labels["relation"],
        "handling": set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]),
        "impact_f1": f1(labels["impact_node_ids"], pred["impact_node_ids"]),
        "preserved_f1": f1(labels["preserved_node_ids"], pred["preserved_node_ids"]),
    }


def prior(row):
    nodes = [x["node_id"] for x in row["base_snapshot"]["joint_plan"]["nodes"]]
    return {"relation": "invariant", "acceptable_decisions": [row["base_snapshot"]["joint_plan"]["decision"]], "impact_node_ids": [], "preserved_node_ids": nodes}


def feedback(arm, old, row):
    s = score(old, row)
    if arm == "exact_match":
        accepted = all([s["relation"], s["handling"], s["impact_f1"] == 1, s["preserved_f1"] == 1])
        reason = "EXACT_MATCH" if accepted else "CONTRACT_MISMATCH"
    elif arm == "sufficiency_only":
        accepted = s["impact_f1"] >= 0.99 and s["preserved_f1"] >= 0.99 and set(row["labels"]["acceptable_decisions"]) & set(old["acceptable_decisions"])
        reason = "SUFFICIENT_SET_RETAINED" if accepted else "INSUFFICIENT_PLAN"
    else:
        accepted = s["relation"] and s["handling"] and s["impact_f1"] == 1 and s["preserved_f1"] == 1
        reason = "COMPOSITE_SATISFIED" if accepted else "COMPOSITE_REVISE"
    return f"{arm}: {'RETAIN' if accepted else 'REVISE'}; reason={reason}"


def main():
    rows = [json.loads(x) for x in DATA.read_text().splitlines()]
    by_id = {x["contract_id"]: x for x in rows}
    runtime = load_object(RUNTIME)["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 180:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw, out = HttpChatAdapter("http://127.0.0.1:8004", 120), ImmutableRawStore(RAW), []
    for mode in MODES:
        for arm in ARMS:
            for cid in SELECTED:
                row, old = by_id[cid], prior(by_id[cid])
                fb = "REVISE; reason=MATCHED_REVISION_CONTROL" if mode == "matched_revise" else feedback(arm, old, row)
                compact = {
                    "base_requirements": row["base_snapshot"]["requirements"],
                    "base_evidence": row["base_snapshot"]["evidence"],
                    "team_state": row["base_snapshot"]["team_state"],
                    "plan_nodes": row["base_snapshot"]["joint_plan"]["nodes"],
                    "intervention": row["intervention"],
                    "counterfactual_requirements": row["counterfactual_snapshot"]["requirements"],
                    "counterfactual_evidence": row["counterfactual_snapshot"]["evidence"],
                }
                prompt = f"Return only JSON with relation,acceptable_decisions,impact_node_ids,preserved_node_ids. TASK={json.dumps(compact,sort_keys=True)} PRIOR={json.dumps(old,sort_keys=True)} FEEDBACK={fb}"
                payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": prompt}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
                key = f"{mode}|{arm}|{cid}"
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
                    valid = set(pred) == {"relation","acceptable_decisions","impact_node_ids","preserved_node_ids"}
                except Exception:
                    pred, valid = None, False
                out.append({"mode": mode, "arm": arm, "contract_id": cid, "valid": valid, "prediction": pred, "scores": score(pred,row) if valid else None, "total_tokens": int(parsed["usage"]["total_tokens"])})
                write_json(P/"MACERD_FEEDBACK_PARTIAL.json",{"rows":out})
    summary = {}
    for mode in MODES:
        for arm in ARMS:
            subset = [x for x in out if x["mode"] == mode and x["arm"] == arm]
            summary[f"{mode}:{arm}"] = {"valid": sum(x["valid"] for x in subset), "relation": sum(x["scores"]["relation"] for x in subset if x["scores"]), "handling": sum(x["scores"]["handling"] for x in subset if x["scores"]), "impact_f1": sum(x["scores"]["impact_f1"] for x in subset if x["scores"])/8, "preserved_f1": sum(x["scores"]["preserved_f1"] for x in subset if x["scores"])/8}
    result = {"evidence_identity":"INDEPENDENT_MACERD_DEVELOPMENT","generation_requests":48,"rows":out,"run_accounting_tokens":sum(x["total_tokens"] for x in out),"schema":"macerd_feedback_probe_result_v1","status":"COMPLETE","summary":summary}
    write_json(P/"MACERD_FEEDBACK_RESULT.json",result)
    print(json.dumps({"summary":summary,"tokens":result["run_accounting_tokens"]},sort_keys=True))


if __name__ == "__main__":
    main()
