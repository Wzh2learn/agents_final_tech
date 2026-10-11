#!/usr/bin/env python3
"""Deterministic Tool Contract Validity and execution-proxy smoke for Agent Distillation."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_method_revision_20261009"
DATA = Path(
    "/home/testuser/wzh/external_stage_d_repro/datasets/agent_distillation/"
    "Qwen2.5-32B-Instruct_agent_trajectories_2k.jsonl"
)
OUT_JSON = TASK / "agent_distillation_tcv_execution_smoke.json"
OUT_MD = ROOT / "docs/research/agent_distillation_tcv_execution_smoke_v1.md"

CALL_ID_RE = re.compile(r"Call id:\s*([A-Za-z0-9_\-]+)")
ERROR_MARKERS = {
    "parsing": "Error in code parsing",
    "max_steps": "Reached max steps",
    "execution": "Code execution failed",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_role(role: Any) -> str:
    text = str(role)
    text = text.split(".")[-1]
    return text.lower().replace("_", "-")


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or item.get("content") or "")
            for item in content
            if isinstance(item, dict)
        )
    return str(content or "")


def parse_tool_calls(message: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    text = message_text(message)
    marker = "Calling tools:"
    if marker not in text:
        return [], "missing_calling_tools_marker"
    literal = text.split(marker, 1)[1].strip()
    try:
        value = ast.literal_eval(literal)
    except (SyntaxError, ValueError) as exc:
        return [], f"unparseable_tool_call_literal:{type(exc).__name__}"
    if not isinstance(value, list):
        return [], "tool_call_literal_not_list"
    calls = [item for item in value if isinstance(item, dict)]
    if len(calls) != len(value):
        return calls, "non_dict_tool_call_item"
    return calls, None


def call_contract(call: dict[str, Any]) -> dict[str, Any]:
    function = call.get("function") if isinstance(call.get("function"), dict) else {}
    name = str(function.get("name") or "")
    arguments = str(function.get("arguments") or "")
    call_id = str(call.get("id") or "")
    syntax_ok = False
    syntax_error = ""
    if arguments.strip():
        try:
            ast.parse(arguments, mode="exec")
            syntax_ok = True
        except SyntaxError as exc:
            syntax_error = f"{type(exc).__name__}:{exc.lineno}"
    return {
        "call_id": call_id,
        "tool_name": name,
        "arguments_nonempty": bool(arguments.strip()),
        "arguments_python_syntax_ok": syntax_ok,
        "arguments_syntax_error": syntax_error,
        "pass": bool(call_id and name and arguments.strip() and syntax_ok),
    }


def main() -> int:
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = Counter()
    tool_names = Counter()
    row_results = []
    for index, row in enumerate(rows):
        log_data = row.get("log_data")
        if isinstance(log_data, str):
            log_data = json.loads(log_data)
        messages = [message for message in (log_data or {}).get("messages") or [] if isinstance(message, dict)]
        calls: list[dict[str, Any]] = []
        responses: list[tuple[str, str]] = []
        parse_errors = []
        for message in messages:
            role = normalize_role(message.get("role"))
            if role == "tool-call":
                parsed, error = parse_tool_calls(message)
                calls.extend(parsed)
                if error:
                    parse_errors.append(error)
            elif role == "tool-response":
                text = message_text(message)
                match = CALL_ID_RE.search(text)
                responses.append((match.group(1) if match else "", text))

        contracts = [call_contract(call) for call in calls]
        response_ids = [call_id for call_id, _ in responses if call_id]
        call_ids = [item["call_id"] for item in contracts]
        missing_responses = [call_id for call_id in call_ids if call_id not in response_ids]
        orphan_responses = [call_id for call_id in response_ids if call_id not in call_ids]
        response_texts = " ".join(text for _, text in responses)
        errors = [name for name, marker in ERROR_MARKERS.items() if marker in response_texts]

        tcv_pass = (
            bool(contracts)
            and not parse_errors
            and all(item["pass"] for item in contracts)
            and not missing_responses
            and not orphan_responses
            and len(call_ids) == len(set(call_ids))
        )
        execution_proxy_pass = tcv_pass and not errors
        tool_names.update(item["tool_name"] for item in contracts if item["tool_name"])
        summary.update({
            "rows": 1,
            "tool_calls": len(contracts),
            "tool_responses": len(responses),
            "parsed_tool_calls": len(contracts),
            "tool_call_parse_error_messages": len(parse_errors),
            "contract_pass_calls": sum(item["pass"] for item in contracts),
            "rows_tcv_pass": int(tcv_pass),
            "rows_execution_proxy_pass": int(execution_proxy_pass),
            "rows_with_error_markers": int(bool(errors)),
            "missing_response_calls": len(missing_responses),
            "orphan_responses": len(orphan_responses),
            "duplicate_call_ids": len(call_ids) - len(set(call_ids)),
        })
        row_results.append({
            "row_index": index,
            "tcv_pass": tcv_pass,
            "execution_proxy_pass": execution_proxy_pass,
            "calls": len(contracts),
            "responses": len(responses),
            "parse_errors": parse_errors,
            "missing_responses": missing_responses,
            "orphan_responses": orphan_responses,
            "execution_error_markers": errors,
            "call_contracts": contracts,
        })

    status = (
        "TCV_AND_EXECUTION_PROXY_DERIVABLE"
        if summary["rows_tcv_pass"] == len(rows)
        else "TCV_PARTIAL_ADAPTER_SMOKE"
    )
    payload = {
        "namespace": "AGENT_DISTILLATION_TCV_EXECUTION_SMOKE",
        "status": status,
        "semantic_claim": "NONE",
        "source": {
            "path": str(DATA),
            "sha256": sha256_file(DATA),
            "rows": len(rows),
        },
        "summary": dict(summary),
        "tool_name_counts": dict(sorted(tool_names.items())),
        "definitions": {
            "TCV": "call id present, tool name present, non-empty Python-parseable arguments, one matched tool response, no duplicate call id",
            "execution_success_proxy": "TCV passes and none of the three released error markers appears in tool responses",
            "not_established": "semantic action correctness, observation consistency, state-transition validity or task progress",
        },
        "row_results": row_results,
        "pilot_impact": {
            "status": "NOT_SUITABLE_FOR_C2_C4",
            "reason": "TCV/execution proxies are derived and do not supply independent semantic process evidence or terminal negatives",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(f"""# Agent Distillation TCV / Execution-Proxy Smoke v1

> Status: `{status}` | Deterministic adapter smoke only | No semantic correctness claim

## 1. Counts

| Quantity | Count |
|---|---:|
| Trajectory rows | {len(rows)} |
| Parsed tool calls | {summary['tool_calls']} |
| Tool responses | {summary['tool_responses']} |
| Contract-pass calls | {summary['contract_pass_calls']} |
| TCV-pass rows | {summary['rows_tcv_pass']} |
| Execution-proxy-pass rows | {summary['rows_execution_proxy_pass']} |
| Rows with error markers | {summary['rows_with_error_markers']} |
| Missing response calls | {summary['missing_response_calls']} |
| Orphan responses | {summary['orphan_responses']} |

Tool names: `{dict(sorted(tool_names.items()))}`

## 2. Definitions

TCV checks only:

- tool-call literal parsing;
- tool name and non-empty arguments;
- Python syntax of the serialized argument body;
- one-to-one call-id response matching;
- no duplicate call ids.

Execution-success proxy additionally rejects released error markers:

- `Error in code parsing`;
- `Reached max steps`;
- `Code execution failed`.

## 3. Boundary

`FACT`: these checks are syntactic/execution proxies.

`NOT ESTABLISHED`: semantic action correctness, observation consistency, state-transition validity, goal progress or independent process supervision.

`VALUE`: the adapter is useful for engineering smoke and error triage. It is insufficient for C4 and does not change the `NOT_SUITABLE_FOR_C2_C4` pilot decision, which is driven by zero terminal negatives, absent `step_reward`, and no independent semantic verifier.

AGENT_DISTILLATION_PILOT_STATUS: NOT_SUITABLE_FOR_C2_C4
""", encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": status,
        "rows": len(rows),
        "tcv_pass_rows": summary["rows_tcv_pass"],
        "execution_proxy_pass_rows": summary["rows_execution_proxy_pass"],
        "tool_calls": summary["tool_calls"],
        "output": str(OUT_MD),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
