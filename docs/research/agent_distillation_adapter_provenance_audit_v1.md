# Agent Distillation Adapter and Provenance Audit v1

> Status: `NOT_SUITABLE_FOR_C2_C4` | Scope: adapter/provenance audit only; no C2/C4 pilot or training

## 1. Terminal outcome

- Raw score counts: `{'1': 597, 'True': 784, '': 547}`
- Normalized positive / negative / unknown: `1381` / `0` / `547`
- Blank diagnosis: `UNKNOWN_UNSORED_OR_PIPELINE_MISSING`
- Blank score count: `547`
- `True` versus `1`: raw encodings are not identical; both normalize to terminal positive. `released raw strings do not satisfy a numeric score==1 comparison without normalization`

`VERIFIED`: the released payload has no normalized negative terminal outcome. Blank rows cannot be interpreted as failed without additional provenance.

## 2. step_reward

- Rows with `step_reward`: `0`
- Steps with `step_reward`: `0`
- Producer found: `False`
- Consumer found: `True`
- Classification: `UNPROVEN_CONSUMER_ONLY_FIELD_OR_PLACEHOLDER`

`FACT`: `step_reward` is consumer-only/placeholder-like in inspected code and absent from the released payload. It cannot be used as native process supervision.

## 3. Derived identifiers

- Provenance: `DERIVED_NOT_NATIVE`
- Unique derived task IDs: `1928`
- Trajectory rows: `1928`
- Task group size min/median/max: `1` / `1.0` / `1`
- Derived split counts: `{'dev': 278, 'test': 299, 'train': 1351}`
- Manifest: `/home/testuser/wzh/projects/agents_final_tech/research/stage_e_method_revision_20261009/agent_distillation_derived_ids.jsonl`
- SHA-256: `1c96bcb24f28cc22a9e8c50d9307a50e0471197afb0644ac3053506b55532235`

These IDs are `DERIVED`, not native dataset identifiers.

## 4. Process-signal feasibility

| Signal | Status | Boundary |
|---|---|---|
| Tool Contract Validity | `DERIVABLE` | syntactic only |
| Execution-success proxy | `DERIVABLE_WITH_PROVENANCE` | error-marker proxy only |
| Observation consistency | `NOT_AVAILABLE` | requires replay/expected observation |
| State-transition consistency | `NOT_AVAILABLE` | requires state snapshots |
| Semantic step verifier | `NOT_AVAILABLE` | independent verifier absent |

Tool/error structure: `{'rows_with_tool_calls': 1928, 'rows_with_balanced_tool_call_response_counts': 1907, 'tool_calls': 4444, 'tool_responses': 4465, 'roles': {'MessageRole.ASSISTANT': 113, 'MessageRole.SYSTEM': 50, 'MessageRole.TOOL_CALL': 113, 'MessageRole.TOOL_RESPONSE': 113, 'MessageRole.USER': 50, 'assistant': 4352, 'system': 1878, 'tool-call': 4331, 'tool-response': 4352, 'user': 1878}}`

## 5. Pilot boundary

Reasons:

- terminal outcomes have 1381 positive and 0 negative rows
- step_reward is absent from 1928 released rows
- no independent semantic process signal is available
- native task/trajectory/origin IDs and split are absent; derived IDs do not close provenance

Allowed now:

- adapter development
- normalization smoke
- syntactic Tool Contract Validity
- execution-error proxy audit

Not allowed:

- calling derived IDs native
- calling syntactic validity semantic correctness
- formal C2/C4 pilot training

AGENT_DISTILLATION_PILOT_STATUS: NOT_SUITABLE_FOR_C2_C4
