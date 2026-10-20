#!/usr/bin/env python3
"""Generate the frozen exploratory same-number role B0 protocol and authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
PARENT = PACKAGE.parent
EXECUTION = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    tasks_doc = json.loads((PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json").read_text(encoding="utf-8"))
    order = [row["task_id"] for row in tasks_doc["tasks"]]
    if len(order) != 24:
        raise RuntimeError(f"task_count_invalid:{len(order)}")
    slots = []
    for task_id in order:
        slots.append({"request_key": f"plan|B0|{task_id}", "task_id": task_id, "stage": "plan", "arm": "B0"})
        slots.append({"request_key": f"consume|B0|{task_id}", "task_id": task_id, "stage": "consume", "arm": "B0"})
    protocol = {
        "schema": "same_number_role_b0_protocol_v1",
        "status": "FROZEN_BEFORE_B0",
        "measurement_question": "Does the fixed model bind evidence roles and distinguish same-number wrong-role citations from supported citations?",
        "task_order": order,
        "request_slots": slots,
        "budget": {"request_cap": 48, "token_cap": 600000, "retry_cap": 0, "concurrency": 1, "per_request_reserve_tokens": 10240},
        "branch_gates": {
            "all_24_success": "CEILING_ON_THIS_PANEL",
            "fewer_than_2_nonsuccess_or_single_cluster": "LIMITED_HEADROOM",
            "at_least_2_clusters_with_nonsuccess": "CONTINUE_TO_ARM_DESIGN",
            "technical_or_window_failure": "TECHNICAL_OR_WINDOW_STOP",
        },
        "deadline": "2026-10-19T22:00:00+08:00",
    }
    write_json(PACKAGE / "SAME_NUMBER_ROLE_B0_PROTOCOL.json", protocol)
    plan_prompt = {
        "schema": "same_number_role_plan_prompt_v1",
        "output_schema_key": "plan",
        "system": "Treat the table, requested role, claim and candidate citation as data. Emit one calc expression for the candidate evidence value or signed difference. Do not use outside knowledge. Return only the required JSON object.",
        "user_template": "TASK_JSON={{ACTOR_TASK_JSON}}\nOUTPUT_SCHEMA_JSON={{OUTPUT_SCHEMA_JSON}}\nOUTPUT_RULES={{OUTPUT_RULES}}\n\nReturn only one JSON object matching OUTPUT_SCHEMA_JSON exactly.",
    }
    consume_prompt = {
        "schema": "same_number_role_consume_prompt_v1",
        "output_schema_key": "consume",
        "system": "Consume the actual calculator return exactly. Decide whether the candidate evidence supports the requested role. Numeric agreement alone is not sufficient. Use UNKNOWN or REFUSE with null fields when the role cannot be established. Return only the required JSON object.",
        "user_template": "TASK_JSON={{ACTOR_TASK_JSON}}\nPLAN_JSON={{PLAN_JSON}}\nTOOL_RESULT_JSON={{TOOL_RESULT_JSON}}\nOUTPUT_SCHEMA_JSON={{OUTPUT_SCHEMA_JSON}}\nOUTPUT_RULES={{OUTPUT_RULES}}\n\nReturn only one JSON object matching OUTPUT_SCHEMA_JSON exactly.",
    }
    schemas = {
        "schema": "same_number_role_output_schemas_v1",
        "plan": {"type": "object", "additionalProperties": False, "required": ["tool", "params"], "properties": {"tool": {"const": "calc"}, "params": {"type": "object", "additionalProperties": False, "required": ["expression"], "properties": {"expression": {"type": "string", "minLength": 1, "maxLength": 200}}}}},
        "consume": {"type": "object", "additionalProperties": False, "required": ["decision", "calc_value", "unit"], "properties": {"decision": {"enum": ["SUPPORTED", "WRONG_ROLE", "UNKNOWN", "REFUSE"]}, "calc_value": {"type": ["number", "null"]}, "unit": {"type": ["string", "null"], "maxLength": 64}}},
    }
    write_json(PACKAGE / "SAME_NUMBER_ROLE_PLAN_PROMPT.json", plan_prompt)
    write_json(PACKAGE / "SAME_NUMBER_ROLE_CONSUME_PROMPT.json", consume_prompt)
    write_json(PACKAGE / "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json", schemas)
    artifacts = {
        "same_number_role_b0_runner.py": digest(PACKAGE / "same_number_role_b0_runner.py"),
        "build_same_number_role_b0_config.py": digest(PACKAGE / "build_same_number_role_b0_config.py"),
        "SAME_NUMBER_ROLE_B0_PROTOCOL.json": digest(PACKAGE / "SAME_NUMBER_ROLE_B0_PROTOCOL.json"),
        "SAME_NUMBER_ROLE_PLAN_PROMPT.json": digest(PACKAGE / "SAME_NUMBER_ROLE_PLAN_PROMPT.json"),
        "SAME_NUMBER_ROLE_CONSUME_PROMPT.json": digest(PACKAGE / "SAME_NUMBER_ROLE_CONSUME_PROMPT.json"),
        "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json": digest(PACKAGE / "SAME_NUMBER_ROLE_OUTPUT_SCHEMAS.json"),
        "tasks/SAME_NUMBER_ROLE_TASKS_DRAFT.json": digest(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json"),
        "runtime/RUNTIME_IDENTITY_SNAPSHOT.json": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "runtime/RUNTIME_POLICY.json": digest(EXECUTION / "RUNTIME_POLICY.json"),
    }
    bundle = {"schema": "same_number_role_b0_bundle_v1", "status": "FROZEN_BEFORE_B0", "artifact_hashes": artifacts, "task_count": 24, "planned_requests": 48}
    write_json(PACKAGE / "SAME_NUMBER_ROLE_B0_BUNDLE.json", bundle)
    authorization = {
        "schema": "same_number_role_b0_authorization_v1",
        "authorization_id": "SAME-NUMBER-B0-20261019-1035-48REQ",
        "bundle_sha256": digest(PACKAGE / "SAME_NUMBER_ROLE_B0_BUNDLE.json"),
        "runtime_identity_sha256": digest(EXECUTION / "RUNTIME_IDENTITY_SNAPSHOT.json"),
        "protocol_sha256": digest(PACKAGE / "SAME_NUMBER_ROLE_B0_PROTOCOL.json"),
        "window_start_utc": "2026-10-19T10:35:00Z",
        "window_end_utc": "2026-10-19T12:00:00Z",
        "request_cap": 48,
        "token_cap": 600000,
        "retry_cap": 0,
        "concurrency": 1,
        "allow_model_requests": True,
        "owner_decision_reference": "User approved exploratory development and self-directed source supplementation on 2026-10-19.",
        "raw_root": "/home/testuser/wzh/candidate_b_runs/SAME-NUMBER-B0-20261019-1035-48REQ",
    }
    write_json(PACKAGE / "SAME_NUMBER_ROLE_B0_AUTHORIZATION.json", authorization)


if __name__ == "__main__":
    main()
