"""Run relation, node-localization and decision stages on MA-CERD."""

import json
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
FINRANK = P.parent / "research_direction_sprint_20261020_v1/execution_v2/finrank_dev"
sys.path.insert(0, str(FINRANK))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json

RUN_ID = "MACERD_STAGED_DERIVATION_20261020"
DATA = P / "release/data/ma_cerd_gold_public_v1.jsonl"
LEDGER = P.parent / "research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json"
RUNTIME = P.parent / "tatqa_wp0_2026/history_collection_execution_v1/RUNTIME_IDENTITY_SNAPSHOT.json"
RAW = P / "raw/MACERD_STAGED_DERIVATION_V1"


class ResumableRawStore:
    def __init__(self, root):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def begin_request(self, logical_id, payload):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", logical_id)[:120]
        request_id = f"{safe}_{sha256_text(payload)[:12]}"
        request_root = self.root / request_id
        if request_root.exists():
            raise FileExistsError(f"request_already_exists:{request_root}")
        request_root.mkdir()
        write_json(request_root / "request.json", payload)
        return request_id, request_root

    def existing_request(self, logical_id, payload):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", logical_id)[:120]
        suffix = f"_{sha256_text(payload)[:12]}"
        for path in self.root.glob(safe + "_*"):
            if path.name.endswith(suffix) and (path / "response.json").exists():
                return path
        return None

    @staticmethod
    def persist_response(request_root, response):
        path = request_root / "response.json"
        if path.exists():
            raise FileExistsError(f"response_already_exists:{path}")
        write_json(path, response)

    @staticmethod
    def mark_crash(request_root, error):
        write_json(request_root / "crash.json", {"error": error})


def f1(gold, pred):
    gold, pred = set(gold), set(pred)
    if not gold and not pred: return 1.0
    if not gold or not pred: return 0.0
    p, r = len(gold & pred) / len(pred), len(gold & pred) / len(gold)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def call(ledger, adapter, raw, key, prompt, runtime):
    payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": prompt}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
    existing = raw.existing_request(key, payload)
    if existing is not None:
        parsed = parse_chat_response(json.loads((existing / "response.json").read_text()))
        return json.loads(parsed["content"]), int(parsed["usage"]["total_tokens"])
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
    return json.loads(parsed["content"]), int(parsed["usage"]["total_tokens"])


def compact(row):
    return {
        "requirements": row["base_snapshot"]["requirements"],
        "evidence": row["base_snapshot"]["evidence"],
        "team_state": row["base_snapshot"]["team_state"],
        "plan_nodes": row["base_snapshot"]["joint_plan"]["nodes"],
        "intervention": row["intervention"],
        "counterfactual_requirements": row["counterfactual_snapshot"]["requirements"],
        "counterfactual_evidence": row["counterfactual_snapshot"]["evidence"],
    }


def main():
    matched = json.loads((P / "MATCHED_FEEDBACK_RESULT.json").read_text())
    ids = matched["selected_contract_ids"]
    rows = {x["contract_id"]: x for x in map(json.loads, DATA.read_text().splitlines())}
    runtime = load_object(RUNTIME)["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 496:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw = HttpChatAdapter("http://127.0.0.1:8004", 120), ResumableRawStore(RAW)
    partial_path = P / "STAGED_DERIVATION_PARTIAL.json"
    out = json.loads(partial_path.read_text())["rows"] if partial_path.exists() else []
    completed = {x["contract_id"] for x in out}
    for cid in ids:
        if cid in completed:
            continue
        row = rows[cid]
        task = json.dumps(compact(row), sort_keys=True)
        relation, tokens = call(ledger, adapter, raw, f"relation|{cid}", "Return only {\"relation\":\"change\" or \"invariant\"}. Derive from task only. TASK=" + task, runtime)
        node_classes = {}
        for node in row["base_snapshot"]["joint_plan"]["nodes"]:
            nid = node["node_id"]
            value, node_tokens = call(ledger, adapter, raw, f"node|{cid}|{nid}", "Return only {\"class\":\"impact\" or \"preserved\"} for the target plan node. Derive from task only. TARGET_NODE=" + json.dumps(node,sort_keys=True) + " TASK=" + task, runtime)
            node_classes[nid] = value.get("class")
        impact = [k for k,v in node_classes.items() if v == "impact"]
        preserved = [k for k,v in node_classes.items() if v == "preserved"]
        decision, decision_tokens = call(ledger, adapter, raw, f"decision|{cid}", "Return only {\"acceptable_decisions\":[...]} using a subset of execute,repair,defer. Derive from task and these fresh classifications. RELATION=" + json.dumps(relation,sort_keys=True) + " NODE_CLASSES=" + json.dumps(node_classes,sort_keys=True) + " TASK=" + task, runtime)
        pred = {"relation": relation.get("relation"), "acceptable_decisions": decision.get("acceptable_decisions",[]), "impact_node_ids": impact, "preserved_node_ids": preserved}
        labels = row["labels"]
        scores = {
            "relation": pred["relation"] == labels["relation"],
            "node_accuracy": sum((n in labels["impact_node_ids"]) == (node_classes[n] == "impact") for n in node_classes)/len(node_classes),
            "handling": set(pred["acceptable_decisions"]) == set(labels["acceptable_decisions"]),
            "impact_f1": f1(labels["impact_node_ids"], impact),
            "preserved_f1": f1(labels["preserved_node_ids"], preserved),
        }
        scores["exact"] = scores["relation"] and scores["handling"] and scores["impact_f1"] == 1 and scores["preserved_f1"] == 1
        out.append({"contract_id":cid,"family_id":row["family_id"],"prediction":pred,"node_classes":node_classes,"scores":scores,"tokens":tokens+node_tokens+decision_tokens})
        write_json(partial_path,{"rows":out})
    summary = {"relation":sum(x["scores"]["relation"] for x in out),"node_accuracy":sum(x["scores"]["node_accuracy"] for x in out)/15,"handling":sum(x["scores"]["handling"] for x in out),"impact_f1":sum(x["scores"]["impact_f1"] for x in out)/15,"preserved_f1":sum(x["scores"]["preserved_f1"] for x in out)/15,"exact":sum(x["scores"]["exact"] for x in out)}
    result = {"evidence_identity":"INDEPENDENT_MACERD_DEVELOPMENT","generation_requests":118,"rows":out,"run_accounting_tokens":sum(x["tokens"] for x in out),"schema":"macerd_staged_derivation_result_v1","status":"COMPLETE","summary":summary}
    write_json(P/"STAGED_DERIVATION_RESULT.json",result)
    print(json.dumps(summary,sort_keys=True))


if __name__ == "__main__":
    main()
