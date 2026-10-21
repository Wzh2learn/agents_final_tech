import json
from pathlib import Path

P = Path(__file__).resolve().parent
ledger = json.loads((P.parent.parent / "execution_v1" / "RESEARCH_GENERATION_LEDGER.json").read_text())
result = json.loads((P / "FORM_CANARY_RESULT.json").read_text())
contract = json.loads((P / "INTERFACE_CONTRACT_V3.json").read_text())
raw = P / "raw"
records = [x for x in ledger["request_records"] if x["run_id"] == "INTERFACE_FORM_CANARY_V3_20261020"]
tokens = sum(x["usage_total_tokens"] for x in records)
checks = {
    "direct": contract["representation"] == "DIRECT_OBJECT",
    "records": len(records) == 8,
    "statuses": all(x["status"] == "OK" for x in records),
    "tokens": tokens == 616,
    "raw": len(list(raw.rglob("request.json"))) == 8 and len(list(raw.rglob("response.json"))) == 8,
    "tie": result["summary"]["DIRECT_OBJECT"]["valid"] == result["summary"]["TOOL_WRAPPER"]["valid"] == 4,
}
out = {"checks": checks, "ledger_slice": records, "ledger_slice_tokens": tokens, "status": "PASS" if all(checks.values()) else "FAIL"}
(P / "FORM_CANARY_VERIFICATION.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": out["status"], "tokens": tokens}))

