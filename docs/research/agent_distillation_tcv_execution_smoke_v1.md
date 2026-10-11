# Agent Distillation TCV / Execution-Proxy Smoke v1

> Status: `TCV_PARTIAL_ADAPTER_SMOKE` | Deterministic adapter smoke only | No semantic correctness claim

## 1. Counts

| Quantity | Count |
|---|---:|
| Trajectory rows | 1928 |
| Parsed tool calls | 4444 |
| Tool responses | 4465 |
| Contract-pass calls | 4442 |
| TCV-pass rows | 1926 |
| Execution-proxy-pass rows | 1792 |
| Rows with error markers | 134 |
| Missing response calls | 0 |
| Orphan responses | 0 |

Tool names: `{'python_interpreter': 4444}`

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
