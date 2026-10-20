"""Run three feedback-revision arms."""

import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent / "finrank_dev"))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json
from run_feedback_probe import feedback_disposition

RUN_ID = "CONDITION_CHANGE_TIER2_20261020"
LEDGER = P.parent.parent / "execution_v1" / "RESEARCH_GENERATION_LEDGER.json"
RAW = P / "raw" / "FEEDBACK_TIER2_V1"
RESULT = P / "FEEDBACK_TIER2_RESULT.json"
CONTRACTS = ("exact_match", "sufficiency_only", "composite")


def main():
    actors = {x["task_id"]: x for x in load_object(P / "ACTOR_TASKS_V2.json")["tasks"]}
    refs = {x["task_id"]: x for x in load_object(P / "REFERENCE_TASKS_V2.json")["references"]}
    tier1 = load_object(P / "BOUNDED_REAL_MODEL_RESULT.json")
    prior = {x["task_id"]: x for x in tier1["results"]}
    runtime = load_object(P.parents[3] / "research" / "tatqa_wp0_2026" / "history_collection_execution_v1" / "RUNTIME_IDENTITY_SNAPSHOT.json")["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 90:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw, rows, tokens = HttpChatAdapter("http://127.0.0.1:8004", 120), ImmutableRawStore(RAW), [], 0
    for contract in CONTRACTS:
        for task_id, actor in actors.items():
            old, ref = prior[task_id], refs[task_id]
            feedback = f"{contract}: prior form invalid; submit a direct JSON object"
            if old["submission_status"] == "VALID":
                feedback = f"{contract}: {'RETAIN' if old['contracts'][contract]['accepted'] else 'REVISE'}; reason={old['contracts'][contract]['contract_reason_code']}"
            text = f"Return only direct JSON with task_id,outcome,evidence_ids. TASK={json.dumps(actor,sort_keys=True)} PRIOR={json.dumps(old.get('submission'),sort_keys=True)} FEEDBACK={feedback}"
            payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": text}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
            record = ledger.reserve(RUN_ID, f"{contract}|{task_id}", sha256_text(payload))
            root = None
            try:
                _, root = raw.begin_request(f"{contract}|{task_id}", payload)
                response = adapter.complete(payload)
                raw.persist_response(root, response)
                parsed = parse_chat_response(response)
            except Exception as exc:
                ledger.settle(record, "FAILED", None, str(exc))
                if root:
                    raw.mark_crash(root, str(exc))
                raise
            ledger.settle(record, "OK", int(parsed["usage"]["total_tokens"]))
            tokens += int(parsed["usage"]["total_tokens"])
            try:
                submission = json.loads(parsed["content"])
                valid = set(submission) == {"task_id", "outcome", "evidence_ids"} and submission["task_id"] == task_id
            except Exception:
                submission, valid = None, False
            scores = {name: feedback_disposition(name, submission["evidence_ids"] if valid else [], submission["outcome"] if valid else "", ref) for name in CONTRACTS}
            rows.append({"contract": contract, "task_id": task_id, "valid": valid, "submission": submission, "scores": scores, "total_tokens": int(parsed["usage"]["total_tokens"])})
            write_json(P / "FEEDBACK_TIER2_PARTIAL.json", {"rows": rows, "tokens": tokens})
    summary = {}
    for contract in CONTRACTS:
        arm = [x for x in rows if x["contract"] == contract]
        summary[contract] = {"valid": sum(x["valid"] for x in arm), "answer": sum(x["scores"]["composite"]["answer_coverage"] for x in arm), "sufficient": sum(x["scores"]["composite"]["plan_sufficient"] for x in arm), "composite": sum(x["scores"]["composite"]["accepted"] for x in arm), "exact": sum(x["scores"]["exact_match"]["accepted"] for x in arm)}
    out = {"by_contract": summary, "evidence_identity": "FEEDBACK_REVISION_DEVELOPMENT", "generation_requests": len(rows), "rows": rows, "run_accounting_tokens": tokens, "schema": "condition_change_feedback_tier2_result_v1", "status": "COMPLETE_TIER2"}
    write_json(RESULT, out)
    print(json.dumps({"status": out["status"], "summary": summary, "tokens": tokens}, sort_keys=True))


if __name__ == "__main__":
    main()
