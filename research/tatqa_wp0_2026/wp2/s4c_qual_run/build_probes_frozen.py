#!/usr/bin/env python3
"""Build the frozen S4C online-qualification probe set from frozen S4B evidence.

Deterministic extraction (verbatim): three probe task prompts are built from
the frozen S4B bridge protocol receipt (probe contexts) and cross-checked
against the persisted final-failure prompt. No model calls.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WP2 = HERE.parent
OUT = HERE / "PROBES_FROZEN.json"

PLAN_INSTR = (
    "STAGE=plan\n"
    "Use the two exact numeric evidence cells for LEFT_NUMBER and RIGHT_NUMBER.\n"
    "Do not provide the final answer in this stage."
)
CONSUME_INSTR = "STAGE=consume\nUse the supplied tool trace and the evidence."


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


receipt_path = WP2 / "S4B_BRIDGE_PROTOCOL_RECEIPT.json"
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
probes = receipt["probes"]

ctx_q1 = probes[0]["prompt_full"].split("\n\nSTAGE=plan", 1)[0]
ctx_q3 = probes[2]["prompt_full"].split("\n\nSTAGE=plan", 1)[0]
ctx_q3_consume = probes[3]["prompt_full"].split("\n\nSTAGE=consume", 1)[0]
trace = probes[3]["prompt_full"].split("RESPONSE=", 1)[1].rstrip("\n")

assert ctx_q3 == ctx_q3_consume, "history-03 contexts differ between plan and consume probes"
assert trace.startswith("PREVIOUS_PLAN="), trace[:64]

plan3_path = WP2 / "s4b_run" / "attempts" / "S4_history-01-wp2_3ab739eb_r2_p0-plan-3" / "prompt.txt"
plan3_text = plan3_path.read_text(encoding="utf-8")
assert ctx_q1 in plan3_text, "history-01 context mismatch vs final failure prompt"

task_q1 = ctx_q1 + "\n\n" + PLAN_INSTR
task_q2 = ctx_q3 + "\n\n" + PLAN_INSTR
task_q3 = ctx_q3 + "\n\n" + CONSUME_INSTR + "\n" + trace

doc = {
    "schema": "tatqa_wp2_s4c_qual_probes_v1",
    "task": "tatqa-wp2-s4c-qual-20261014",
    "service_model_id": "tatqa-wp2-qwen3-8b-b968826d",
    "request_settings": {
        "max_tokens": 512,
        "temperature": 0,
        "n": 1,
        "transport_retries": 0,
    },
    "criterion": {
        "pass": (
            "all 3 probes: HTTP 200, validate_v2 route=strict_json and ok=true "
            "(schema-legal, no prose, complete fields)"
        ),
        "early_stop": (
            "stop on first criterion failure; qualification FAIL -> "
            "STOP_THIS_PANEL permanent (no fifth round)"
        ),
        "zero_transmission_startup_failures": (
            "engineering retry allowed once (max 2 service starts); frozen "
            "components/prompts/schema must not change; requests sent count"
        ),
    },
    "probes": [
        {
            "probe_id": "S4CQ-01-plan-history-01",
            "stage": "plan",
            "task_prompt": task_q1,
            "task_prompt_sha256": sha256_text(task_q1),
            "provenance": {
                "evidence": "S4B_BRIDGE_PROTOCOL_RECEIPT.json probes[0] context (item_c5d72f59a7d7)",
                "cross_check": "context verbatim-substring of final failure prompt.txt (plan-3)",
            },
        },
        {
            "probe_id": "S4CQ-02-plan-history-03",
            "stage": "plan",
            "task_prompt": task_q2,
            "task_prompt_sha256": sha256_text(task_q2),
            "provenance": {
                "evidence": "S4B_BRIDGE_PROTOCOL_RECEIPT.json probes[2] context (item_853ac256a93f)",
            },
        },
        {
            "probe_id": "S4CQ-03-consume-history-03",
            "stage": "consume",
            "task_prompt": task_q3,
            "task_prompt_sha256": sha256_text(task_q3),
            "provenance": {
                "evidence": "S4B_BRIDGE_PROTOCOL_RECEIPT.json probes[3] context + frozen tool trace",
            },
        },
    ],
    "source_receipt_sha256": sha256_file(receipt_path),
    "source_final_failure_prompt_sha256": sha256_file(plan3_path),
}

with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

print("wrote", OUT)
for probe in doc["probes"]:
    print("PROBE", probe["probe_id"], probe["stage"], probe["task_prompt_sha256"], len(probe["task_prompt"]))
print()
print("=== task_q3 tail (last 260 chars) ===")
print(task_q3[-260:])
print()
print("=== task_q1 tail (last 160 chars) ===")
print(task_q1[-160:])