# STALE Oracle Diagnostic

Date: 2026-10-23, Asia/Shanghai

Status: `COMPLETE_DEV_DIAGNOSTIC`

Evidence identity: `ORACLE_DIAGNOSTIC_NOT_DEPLOYABLE`

## Question

When the actor already sees the selected relevant raw sessions and the target
query, are explicit `M_old`/`M_new` state values sufficient for stale-state
detection, or is the causal `explanation` necessary?

This is an oracle representation diagnostic. It is excluded from the main
STALE arms and cannot support a deployable performance claim.

## Contract

- Same four UIDs and `dim1_query` as the main probe.
- Arm A: oracle relevant raw sessions plus `M_old` and `M_new`, without
  `explanation`.
- Arm B: the same input plus `explanation`.
- Eight calls total, sequential, Qwen3.6-35B-A3B Q4, temperature 0,
  `max_tokens=256`, `enable_thinking=false`, zero retries.
- Same five-field strict JSON response contract as the main probe.
- Official STALE judge not run.

## Results

| Arm | Calls | STALE_DETECTED | Negative old-state answer | Tokens | Context chars/call |
|---|---:|---:|---:|---:|---:|
| M_old/M_new only | 4 | 4/4 | 4/4 | 14,794 | 16,389 |
| M_old/M_new + explanation | 4 | 4/4 | 4/4 | 14,991 | 16,662 |

All 8 HTTP calls returned 200, all 8 strict JSON objects validated, and all 8
answers began with a negative old-state polarity. The result hash is
`b8df1ccaa6dc09a4f7c46c6b50dbb7828b9847c674919d14d775c3f60b715496`.

## Interpretation

Explicitly labeling the prior and updated state was sufficient for this model
on all four development cases, including both Type II propagation examples.
Adding the causal explanation did not improve the 4/4 result and added about
197 accounting tokens across four calls.

Compared with the deployable main arms, the change is in representation rather
than answer reasoning:

- one-shot oracle raw sessions: 1/4 `STALE_DETECTED`;
- explicit state values: 4/4 `STALE_DETECTED`;
- explicit values plus explanation: 4/4 `STALE_DETECTED`.

This supports a narrower mechanism hypothesis: the model can decide that a
state is stale once a compact current-state representation is available, but
does not reliably construct or propagate that representation from raw
sessions. It does not prove that explanations are generally unnecessary, nor
that a two-stage state-card method will work without oracle fields.

## Evidence Integrity And Recovery

The first result-assembly attempt raised `NameError` after all eight model
responses had already been written to raw storage. No call was reissued. A
recovery path reconstructed the result from the preserved request/response
receipts. Pre/post SHA-256 manifests over all 32 raw files were identical.

## Limits

- Four instances, one query dimension, one model and one prompt form.
- `M_old`/`M_new` are hidden benchmark fields; this arm is intentionally
  non-deployable.
- Answer polarity is a deterministic lexical proxy, not the official judge.
- Latency differences are not interpreted because A preceded B and server
  state may differ.
