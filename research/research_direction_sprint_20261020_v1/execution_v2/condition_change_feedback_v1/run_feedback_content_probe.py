"""Post-hoc mechanism probe: matched REVISE state, varying reason code."""

import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent / "finrank_dev"))
from finrank_contract import HttpChatAdapter, ImmutableRawStore, SharedGenerationLedger, load_object, parse_chat_response, sha256_text, write_json
from run_feedback_probe import feedback_disposition

RUN_ID = "FEEDBACK_CONTENT_PROBE_20261020"
TASKS = ("CC003:post", "CC003:pre", "CC010:pre", "CC012:post")
ARMS = ("exact_match", "sufficiency_only", "composite")
REASONS = {"exact_match": "CANONICAL_SET_MISMATCH", "sufficiency_only": "INSUFFICIENT_PLAN", "composite": "ANSWER_MISMATCH"}
LEDGER = P.parent.parent / "execution_v1" / "RESEARCH_GENERATION_LEDGER.json"
RAW = P / "raw" / "FEEDBACK_CONTENT_PROBE_V1"


def main():
    actors = {x["task_id"]: x for x in load_object(P / "ACTOR_TASKS_V2.json")["tasks"]}
    refs = {x["task_id"]: x for x in load_object(P / "REFERENCE_TASKS_V2.json")["references"]}
    prior = {x["task_id"]: x for x in load_object(P / "BOUNDED_REAL_MODEL_RESULT.json")["results"]}
    runtime = load_object(P.parents[3] / "research" / "tatqa_wp0_2026" / "history_collection_execution_v1" / "RUNTIME_IDENTITY_SNAPSHOT.json")["identity"]
    ledger = SharedGenerationLedger(LEDGER)
    if load_object(LEDGER)["new_generation_budget"]["requests_used"] != 168:
        raise RuntimeError("ledger_start_mismatch")
    adapter, raw, rows, tokens = HttpChatAdapter("http://127.0.0.1:8004", 120), ImmutableRawStore(RAW), [], 0
    for arm in ARMS:
        for task_id in TASKS:
            old, ref, actor = prior[task_id], refs[task_id], actors[task_id]
            feedback = f"{arm}: REVISE; reason={REASONS[arm]}"
            text = f"Return only direct JSON with task_id,outcome,evidence_ids. TASK={json.dumps(actor,sort_keys=True)} PRIOR={json.dumps(old.get('submission'),sort_keys=True)} FEEDBACK={feedback}"
            payload = {"model": runtime["model"]["model_id"], "messages": [{"role": "user", "content": text}], "chat_template_kwargs": {"enable_thinking": False}, **runtime["generation"]}
            key = f"{arm}|{task_id}"
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
            tokens += int(parsed["usage"]["total_tokens"])
            try:
                submission = json.loads(parsed["content"])
                valid = set(submission) == {"task_id", "outcome", "evidence_ids"} and submission["task_id"] == task_id
            except Exception:
                submission, valid = None, False
            score = feedback_disposition("composite", submission["evidence_ids"] if valid else [], submission["outcome"] if valid else "", ref)
            rows.append({"arm": arm, "task_id": task_id, "valid": valid, "submission": submission, "composite": score, "reason": REASONS[arm], "total_tokens": int(parsed["usage"]["total_tokens"])})
            write_json(P / "FEEDBACK_CONTENT_PROBE_PARTIAL.json", {"rows": rows, "tokens": tokens})
    summary = {arm: {"answer": sum(x["composite"]["answer_coverage"] for x in rows if x["arm"] == arm), "composite": sum(x["composite"]["accepted"] for x in rows if x["arm"] == arm), "valid": sum(x["valid"] for x in rows if x["arm"] == arm)} for arm in ARMS}
    out = {"evidence_identity": "POSTHOC_MECHANISM_PROBE", "generation_requests": 12, "rows": rows, "run_accounting_tokens": tokens, "schema": "feedback_content_probe_result_v1", "status": "COMPLETE", "summary": summary}
    write_json(P / "FEEDBACK_CONTENT_PROBE_RESULT.json", out)
    print(json.dumps({"summary": summary, "tokens": tokens}, sort_keys=True))


if __name__ == "__main__":
    main()
