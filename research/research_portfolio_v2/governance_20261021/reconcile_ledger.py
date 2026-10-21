"""Reconcile this 101-generation snapshot without modifying frozen run evidence.

Only --output writes a derived receipt. No network or model calls are performed.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


PORTFOLIO = "research/research_portfolio_v2"
LEDGER = f"{PORTFOLIO}/COST_AND_CANDIDATES.json"
RECEIPT = f"{PORTFOLIO}/governance_20261021/LEDGER_RECONCILIATION.json"
BATCHES = {
    "MODEL_QUALIFICATION_V1_CANARY_001": f"{PORTFOLIO}/model_qualification_v1/raw",
    "MODEL_QUALIFICATION_V2_001_024": f"{PORTFOLIO}/model_qualification_v2/raw",
    "MODEL_QUERY_SCOUT_V1_001_003": f"{PORTFOLIO}/model_query_scout_v1/raw",
    "MODEL_QUERY_SCOUT_V2_001_006": f"{PORTFOLIO}/model_query_scout_v2/raw",
    "CODEUPDATEARENA_ADAPTER_001_016": "research/codeupdatearena_adapter_v1/evidence/model",
    "CODEUPDATEARENA_CONFIRMATION_001_016": "research/codeupdatearena_confirmation_v1/evidence/revalidation",
    "VERSICODE_OBSERVABILITY_V1_20261021_001_032": f"{PORTFOLIO}/versicode_observability_v1/raw",
    "PYMIG_NTRIPBROWSER_BEHAVIORAL_PROBE_20261021_001_003": f"{PORTFOLIO}/pymigbench_external_change_v1/ntripbrowser_qualification_v2/raw",
}
ZERO_REPLAY = "CODEUPDATEARENA_ADAPTER_V2_ZERO_REQUEST_REVALIDATION"
FAILED_RESPONSES = (
    f"{PORTFOLIO}/model_qualification_v1/raw/llama_cpp_qwen36_35b_a3b_q4/dependency_plan/plan/response.json",
    f"{PORTFOLIO}/model_query_scout_v2/raw/benign_change/2/response.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect(root: Path) -> tuple[dict, list[dict], dict[str, str]]:
    inputs: dict[str, str] = {}

    def read_json(relative: str) -> dict:
        data = (root / relative).read_bytes()
        inputs[relative] = sha256(data)
        return json.loads(data)

    ledger = json.loads((root / LEDGER).read_text(encoding="utf-8"))
    rows = []
    for event_id, directory in BATCHES.items():
        for response_path in sorted((root / directory).rglob("response.json")):
            relative = response_path.relative_to(root).as_posix()
            request_relative = response_path.with_name("request.json").relative_to(root).as_posix()
            response = read_json(relative)
            request = read_json(request_relative)
            usage = response.get("usage", {})
            require(isinstance(usage.get("total_tokens"), int), f"Missing usage: {relative}")
            rows.append({
                "event_id": event_id,
                "raw_request": request_relative,
                "raw_response": relative,
                "request_sha256": inputs[request_relative],
                "canonical_request_sha256": sha256(json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()),
                "response_sha256": inputs[relative],
                "response_id": response.get("id"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage["total_tokens"],
                "known_validation_failure": relative in FAILED_RESPONSES,
            })
    for event in ledger["events"]:
        read_json(event["raw_result"])
    for directory, filename in [
        ("model_qualification_v1", "QUALIFICATION_LEDGER.json"),
        ("model_qualification_v2", "QUALIFICATION_LEDGER.json"),
        ("model_query_scout_v1", "MODEL_QUERY_SCOUT_LEDGER.json"),
        ("model_query_scout_v2", "MODEL_QUERY_SCOUT_LEDGER.json"),
        ("model_qualification_v1", "run_qualification.py"),
        ("model_query_scout_v2", "run_scout.py"),
    ]:
        relative = f"{PORTFOLIO}/{directory}/{filename}"
        inputs[relative] = sha256((root / relative).read_bytes())
    return ledger, rows, inputs


def validate(ledger: dict, rows: list[dict]) -> dict:
    events = {event["id"]: event for event in ledger["events"]}
    require(len(events) == len(ledger["events"]), "Duplicate aggregate event ID")
    require(set(events) == set(BATCHES) | {ZERO_REPLAY}, "Unreconciled event set: extend this bounded audit before reuse")
    require(len({row["raw_response"] for row in rows}) == len(rows), "Duplicate response path")
    adjustments = ledger.get("post_hoc_adjustments", [])
    require(len({item["id"] for item in adjustments}) == len(adjustments), "Duplicate adjustment ID")
    summaries = []
    for event_id in BATCHES:
        event = events[event_id]
        batch = [row for row in rows if row["event_id"] == event_id]
        require(len(batch) == event["attempts"] == event["physical_http_calls"], f"Missing request/response pairs: {event_id}")
        for row in batch:
            require(row["total_tokens"] > 0, f"Unsettled response usage: {row['raw_response']}")
            require(row["prompt_tokens"] + row["completion_tokens"] == row["total_tokens"], f"Usage decomposition mismatch: {row['raw_response']}")
        actual = sum(row["total_tokens"] for row in batch)
        matching = [item for item in adjustments if item["event_id"] == event_id]
        for item in matching:
            require(item["attempts_delta"] == item["physical_http_calls_delta"] == 0, "Usage correction must not create model calls")
            evidence = [row for row in batch if row["raw_response"] == item["raw_response"]]
            require(len(evidence) == 1, f"Adjustment response missing: {item['id']}")
            require(evidence[0]["response_sha256"] == item["raw_response_sha256"], f"Adjustment evidence hash mismatch: {item['id']}")
            require(evidence[0]["total_tokens"] == item["accounting_tokens_delta"], f"Adjustment usage mismatch: {item['id']}")
        delta = sum(item["accounting_tokens_delta"] for item in matching)
        require(event["accounting_tokens"] + delta == actual, f"Batch accounting mismatch: {event_id}")
        summaries.append({"event_id": event_id, "attempts": len(batch), "frozen_event_tokens": event["accounting_tokens"], "post_hoc_delta": delta, "raw_usage_tokens": actual})
    replay = events[ZERO_REPLAY]
    require(replay["attempts"] == replay["physical_http_calls"] == replay["accounting_tokens"] == 0, "Reused generations counted as new requests")
    require(all(item["event_id"] in BATCHES for item in adjustments), "Orphan adjustment")
    total = sum(row["total_tokens"] for row in rows)
    attempts = sum(event["attempts"] for event in events.values())
    calls = sum(event["physical_http_calls"] for event in events.values())
    budget = ledger["new_budget"]
    require(budget["accounting_tokens_used"] == total, "Current aggregate token total differs from raw usage")
    require(budget["attempts_used"] == attempts == len(rows), "Current attempt total differs from evidence pairs")
    require(budget["physical_http_calls"] == calls == len(rows), "Current generation POST count differs from evidence pairs")
    require(attempts <= budget["attempt_cap"] and total <= budget["accounting_tokens_cap"], "Budget cap exceeded")
    return {"attempts": attempts, "recorded_generation_post_calls": calls, "accounting_tokens": total, "frozen_event_tokens": sum(event["accounting_tokens"] for event in events.values()), "post_hoc_tokens_delta": sum(item["accounting_tokens_delta"] for item in adjustments), "batch_summaries": summaries}


def negative_controls(ledger: dict, rows: list[dict]) -> list[dict]:
    cases = []
    wrong = deepcopy(ledger)
    wrong["new_budget"]["accounting_tokens_used"] -= 1
    cases.append(("aggregate_minus_one", wrong, rows))
    for failed in FAILED_RESPONSES:
        cases.append(("omit_failed_response:" + failed, ledger, [row for row in rows if row["raw_response"] != failed]))
        zeroed = deepcopy(rows)
        next(row for row in zeroed if row["raw_response"] == failed)["total_tokens"] = 0
        cases.append(("zero_failed_usage:" + failed, ledger, zeroed))
    cases.append(("omit_post_hoc_adjustments", {**ledger, "post_hoc_adjustments": []}, rows))
    outcomes = []
    for name, candidate, candidate_rows in cases:
        try:
            validate(candidate, candidate_rows)
        except (ValueError, KeyError, TypeError) as error:
            outcomes.append({"case": name, "status": "REJECTED_AS_REQUIRED", "reason": str(error)})
        else:
            raise ValueError(f"Negative control incorrectly passed: {name}")
    return outcomes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, help="Write a derived audit receipt; frozen evidence is read-only")
    parser.add_argument("--negative-controls", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    ledger, rows, inputs = collect(root)
    summary = validate(ledger, rows)
    existing = root / RECEIPT
    if existing.exists():
        pins = json.loads(existing.read_text(encoding="utf-8"))["frozen_input_sha256"]
        require(pins == inputs, "Frozen evidence changed or is incomplete since the audit receipt")
    controls = negative_controls(ledger, rows) if args.negative_controls else []
    result = {"schema": "portfolio_generation_usage_reconciliation_v1", "date": "2026-10-21", "status": "PASS", "evidence_identity": "POST_HOC_ACCOUNTING_RECONCILIATION_NOT_NEW_MODEL_EXPERIMENT", "summary": summary, "negative_controls": controls, "frozen_input_sha256": inputs, "requests": rows, "model_calls_by_audit": 0, "network_calls_by_audit": 0, "nonclaims": ["Recorded generation POST pairs are not an independent network trace.", "Physical generation calls exclude separately reported model-identity GETs.", "Frozen result/ledger scores and original token values are preserved.", "This audit covers the explicitly listed 101-generation snapshot; new batches need an explicit audit extension."]}
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", **{k: v for k, v in summary.items() if k != "batch_summaries"}, "negative_controls_rejected": len(controls), "frozen_inputs": len(inputs), "model_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
