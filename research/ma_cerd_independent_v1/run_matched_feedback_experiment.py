"""Run the preregistered matched-feedback experiment on MA-CERD."""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

P = Path(__file__).resolve().parent
FINRANK = P.parent / "research_direction_sprint_20261020_v1/execution_v2/finrank_dev"
sys.path.insert(0, str(FINRANK))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json

RUN_ID = "MACERD_MATCHED_FEEDBACK_20261020"
DATA = P / "release/data/ma_cerd_gold_public_v1.jsonl"
LEDGER = P.parent / "research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json"
RUNTIME = P.parent / "tatqa_wp0_2026/history_collection_execution_v1/RUNTIME_IDENTITY_SNAPSHOT.json"
RAW = P / "raw/MACERD_MATCHED_FEEDBACK_V1"
ARMS = ("no_feedback", "exact_match", "sufficiency_only", "composite")
TEXTS = {
    "no_feedback": "revision_state={state}. Evaluate the task directly under the default criterion.",
    "exact_match": "revision_state={state}. Apply exact-match semantics: relation, decisions, impact set, and preserved set must all match the criterion.",
    "sufficiency_only": "revision_state={state}. Apply sufficiency semantics: retain all required relation, decision, impact and preservation elements; ignore extra elements.",
    "composite": "revision_state={state}. Apply composite semantics: require correct relation, an admissible decision, complete impact and preservation coverage, and no out-of-scope nodes.",
}


def f1(gold, pred):
    gold, pred = set(gold), set(pred)
    if not gold and not pred: return 1.0
    if not gold or not pred: return 0.0
    precision, recall = len(gold & pred) / len(pred), len(gold & pred) / len(gold)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def exact(pred, row):
    labels = row["labels"]
    return (
        pred["relation"] == labels["relation"]
        and set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"])
        and set(pred["impact_node_ids"]) == set(labels["impact_node_ids"])
        and set(pred["preserved_node_ids"]) == set(labels["preserved_node_ids"])
    )


def make_prior(row, kind):
    labels = row["labels"]
    nodes = [x["node_id"] for x in row["base_snapshot"]["joint_plan"]["nodes"]]
    if kind == "correct":
        return {
            "relation": labels["relation"],
            "acceptable_decisions": labels["acceptable_decisions"],
            "impact_node_ids": labels["impact_node_ids"],
            "preserved_node_ids": labels["preserved_node_ids"],
        }
    return {
        "relation": "invariant" if labels["relation"] == "change" else "change",
        "acceptable_decisions": ["defer"],
        "impact_node_ids": nodes,
        "preserved_node_ids": [],
    }


def select(rows):
    selected = []
    targets = {"change": 8, "invariant": 7}
    counts = {"change": 0, "invariant": 0}
    used = set()
    pool = [r for r in rows if r["partition"] == "test"]
    pool.sort(key=lambda r: hashlib.sha256((r["labels"]["relation"] + ":" + r["contract_id"]).encode()).hexdigest())
    for row in pool:
        relation = row["labels"]["relation"]
        if row["family_id"] in used or counts[relation] >= targets[relation]:
            continue
        selected.append(row)
        used.add(row["family_id"])
        counts[relation] += 1
        if sum(counts.values()) == 15:
            break
    selected.sort(key=lambda r: r["contract_id"])
    assert len({r["family_id"] for r in selected}) == 15
    assert counts == targets
    return selected


def main():
    rows = [json.loads(x) for x in DATA.read_text().splitlines()]
    selected = select(rows)
    runtime = load_object(RUNTIME)["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 228:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw, out = HttpChatAdapter("http://127.0.0.1:8004", 120), ImmutableRawStore(RAW), []
    for row in selected:
        compact = {
            "requirements": row["base_snapshot"]["requirements"],
            "evidence": row["base_snapshot"]["evidence"],
            "team_state": row["base_snapshot"]["team_state"],
            "plan_nodes": row["base_snapshot"]["joint_plan"]["nodes"],
            "intervention": row["intervention"],
            "counterfactual_requirements": row["counterfactual_snapshot"]["requirements"],
            "counterfactual_evidence": row["counterfactual_snapshot"]["evidence"],
        }
        for prior_kind in ("correct", "wrong"):
            prior = make_prior(row, prior_kind)
            state = "RETAIN" if prior_kind == "correct" else "REVISE"
            for arm in ARMS:
                feedback = TEXTS[arm].format(state=state)
                prompt = f"Return only JSON with relation,acceptable_decisions,impact_node_ids,preserved_node_ids. TASK={json.dumps(compact,sort_keys=True)} PRIOR={json.dumps(prior,sort_keys=True)} FEEDBACK={feedback}"
                payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": prompt}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
                key = f"{prior_kind}|{arm}|{row['contract_id']}"
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
                labels = row["labels"]
                scores = {
                    "relation": pred["relation"] == labels["relation"] if valid else False,
                    "handling": set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]) if valid else False,
                    "impact_f1": f1(labels["impact_node_ids"], pred["impact_node_ids"]) if valid else 0.0,
                    "preserved_f1": f1(labels["preserved_node_ids"], pred["preserved_node_ids"]) if valid else 0.0,
                    "exact": exact(pred,row) if valid else False,
                }
                out.append({"arm":arm,"contract_id":row["contract_id"],"family_id":row["family_id"],"prior_kind":prior_kind,"prediction":pred,"scores":scores,"valid":valid,"total_tokens":int(parsed["usage"]["total_tokens"])})
                write_json(P/"MATCHED_FEEDBACK_PARTIAL.json",{"rows":out,"selected":[r["contract_id"] for r in selected]})
    summary = {}
    for prior_kind in ("correct","wrong"):
        for arm in ARMS:
            subset = [x for x in out if x["prior_kind"] == prior_kind and x["arm"] == arm]
            summary[f"{prior_kind}:{arm}"] = {
                "valid": sum(x["valid"] for x in subset),
                "relation": sum(x["scores"]["relation"] for x in subset),
                "handling": sum(x["scores"]["handling"] for x in subset),
                "impact_f1": sum(x["scores"]["impact_f1"] for x in subset)/15,
                "preserved_f1": sum(x["scores"]["preserved_f1"] for x in subset)/15,
                "exact": sum(x["scores"]["exact"] for x in subset),
                "repair_or_preserve_rate": sum(x["scores"]["exact"] for x in subset)/15,
            }
    result = {
        "evidence_identity":"INDEPENDENT_MACERD_DEVELOPMENT",
        "generation_requests":120,
        "rows":out,
        "run_accounting_tokens":sum(x["total_tokens"] for x in out),
        "schema":"macerd_matched_feedback_result_v1",
        "selected_contract_ids":[r["contract_id"] for r in selected],
        "status":"COMPLETE",
        "summary":summary,
    }
    write_json(P/"MATCHED_FEEDBACK_RESULT.json",result)
    print(json.dumps({"summary":summary,"tokens":result["run_accounting_tokens"]},sort_keys=True))


if __name__ == "__main__":
    main()
