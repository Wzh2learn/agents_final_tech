# STALE Real-Model Probe

Date: 2026-10-23, Asia/Shanghai

Status: `COMPLETE_DEV_PROBE`

Evidence identity: `DEV_ONLY_REAL_MODEL_OBSERVATIONS_WITH_STRUCTURED_REFERENCE_PROXIES`

## Contract

- Model: `Qwen3.6-35B-A3B-Q4_K_M.gguf` on GB10 `:8004`.
- Four deterministic public STALE instances: two T1 and two T2.
- Three queries per instance and three evidence arms:
  `query_only`, `lexical_top2`, `oracle_relevant_top2`.
- 36 planned and executed generation calls, sequential, temperature 0,
  `max_tokens=256`, `enable_thinking=false`, JSON object output, zero retries.
- Actor input contains selected raw session messages and the query only.
  `M_old`, `M_new`, `explanation`, and `relevant_session_index` are excluded.
- Official STALE LLM judge: not run and not used for the main result.

Raw requests and responses are under
`stale_model_run_20261023_v1/stale_model_raw/`. The result hash recorded in the
receipt is `120327279aac1df0709fbd95c3c7ef3a49202f002b451405c2dfeec6ea51933d`.

## Execution Evidence

| Quantity | Result |
|---|---:|
| Planned generation calls | 36 |
| Executed generation calls | 36 |
| Physical HTTP calls | 36 |
| HTTP 200 | 36 |
| Valid strict JSON/schema | 36 |
| Finish reason `stop` | 36 |
| Retries | 0 |
| Accounting tokens | 122,090 |
| Total model latency | 99.470 s |
| Official judge calls | 0 |

All 36 request bodies passed the forbidden-metadata scan. Every raw request,
response, and call receipt was preserved.

## Arm Results

| Arm | Calls | Decision | State resolution | Tokens | Mean prompt chars | Latency |
|---|---:|---|---|---:|---:|---:|
| query-only | 12 | 12 UNKNOWN | 12 UNKNOWN | 5,485 | 1,723 | 14.248 s |
| lexical top-2 | 12 | 5 ANSWER, 7 UNKNOWN | 5 stale-not-detected, 7 N/A | 71,325 | 26,224 | 52.349 s |
| oracle relevant top-2 | 12 | 7 ANSWER, 5 UNKNOWN | 1 stale-detected, 5 stale-not-detected, 6 N/A | 45,280 | 16,735 | 32.873 s |

For the four `dim1` state-resolution queries:

- Query-only returned UNKNOWN on 4/4.
- Lexical top-2 exposed only the old relevant session on 3/4 and the model
  accepted the old state on all three. The fourth retrieval missed both
  relevant sessions and returned UNKNOWN.
- Oracle relevant top-2 exposed both relevant sessions on 4/4. Only 1/4
  detected the stale state; 3/4 still answered in favor of the old state.
- The successful detection was T1. Both Type II propagation cases and the
  other T1 case failed to propagate the newer observation into the queried
  state.

The oracle arm used fewer tokens than lexical retrieval because lexical
selection placed large irrelevant sessions in context. Better evidence
selection therefore reduced cost while increasing useful evidence, but it did
not solve state propagation.

## Structured-Field Behavior

Strict schema parsing was 36/36, but semantic field use was incomplete:

- `decision`: 24 UNKNOWN, 12 ANSWER, 0 REFUSE.
- `state_resolution`: 12 UNKNOWN, 10 STALE_NOT_DETECTED, 1
  STALE_DETECTED, 13 NOT_APPLICABLE.
- `premise_resistance`: 9 UNKNOWN, 27 NOT_APPLICABLE; the model never emitted
  FALSE_PREMISE_REJECTED or FALSE_PREMISE_ACCEPTED.
- `action_adaptation`: 9 UNKNOWN, 11 CURRENT_STATE_ALIGNED, 16
  NOT_APPLICABLE; it never emitted STALE_STATE_ALIGNED.

This is a contract-use limitation as well as a model observation. The probe
must not convert the 20 `UNRESOLVED_NOT_APPLICABLE` proxy rows into semantic
failures or successes. In several dim2 answers the text nevertheless followed
the false premise while the structured field said `NOT_APPLICABLE`.

## Scientific Judgment

The result rejects the simple explanation that the task is only missing the
correct retrieved sessions. Complete relevant-session visibility improved
evidence coverage but yielded only one explicit stale-state detection on four
state queries. The current model/probe form does not reliably propagate a
later observation into an earlier state, especially for Type II conflicts.

This does not establish that STALE is unsolvable or that a structured memory
method is necessary. It shows that, under this fixed model and prompt schema,
oracle retrieval alone is insufficient. The next diagnostic should distinguish
explicit state values from causal change explanations; those inputs are oracle
development aids and cannot be used as deployable actor evidence.

## Limitations

- Four instances are a development probe, not an accuracy estimate.
- The structured proxy is not the official semantic STALE judge.
- Exact `M_old`/`M_new` text-presence checks are imperfect for paraphrased T2
  evidence; the raw outputs and relevant-index coverage remain authoritative.
- The prompt asks for all three semantic dimensions on every query, causing
  frequent `NOT_APPLICABLE`; this affects field interpretation.
- No claim is made about other models, full 400-item performance, or CUPMem.
