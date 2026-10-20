# Bounded Real Model V1 Preregistration

Status: `FROZEN_BEFORE_REQUESTS`
Date: 2026-10-20, Asia/Shanghai
Evidence identity: `DEV_ONLY_CONTROLLED_MECHANISM`

## Scope

Run Tier 1 only: one model submission for each of the 26 V2 actor tasks. This
phase measures feedback-contract discrimination on model output. It does not
show feedback to the model and cannot establish learning, adaptation, public
generalization, or human gold.

## Frozen Inputs

- `ACTOR_TASKS_V2.json`
- `TASK_TOOL_SCHEMA_V2.json`
- `POLICY_SPEC_V2.json`
- `EVIDENCE_FACTS_V2.json`
- `REFERENCE_TASKS_V2.json` for offline scoring only
- `FEEDBACK_PROBE_FIXTURES_V2.json`

The actor payload contains policy context and observations but no decisions,
minimal sufficient sets, reference facts, or adjudication fields.

## Runtime Identity

- Model: `Qwen3.6-35B-A3B-Q4_K_M.gguf`
- Model SHA-256:
  `4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d`
- Endpoint: `http://127.0.0.1:8004/v1/chat/completions` on GB10
- `enable_thinking=false`
- `temperature=0`, `top_p=1`, `top_k=1`, `seed=20261018`
- `max_tokens=256`
- JSON object output
- Single concurrency

No model, tokenizer, server binary, template, endpoint, or generation
parameter may change during the run.

## Submission Contract

The model must return one strict JSON object:

```json
{
  "task_id": "CC001:pre",
  "outcome": "approve",
  "evidence_ids": ["CC001:receipt"]
}
```

`outcome` is `approve` or `reject`. `evidence_ids` contains between one and
four IDs from the current actor task. Unknown keys, wrong task IDs, invalid
outcomes, absent IDs, duplicate IDs, and out-of-range IDs are hard failures.
No silent coercion or raw repair is allowed.

## Request And Token Bounds

| Bound | Value |
|---|---:|
| Logical tasks | 26 |
| Physical model requests | 26 |
| Samples per task | 1 |
| Retries | 0 |
| Input cap per request | 4,096 tokens |
| Output cap per request | 256 tokens |
| Combined per-request cap | 4,352 tokens |
| Total input cap | 106,496 tokens |
| Total output cap | 6,656 tokens |
| Total accounting cap | 113,152 tokens |

Every physical request is entered in
`../execution_v1/RESEARCH_GENERATION_LEDGER.json` before execution. Starting
ledger is `56/192` requests and `458,650/2,000,000` tokens. This run may reach
at most `82/192` requests and `571,802/2,000,000` cumulative accounting
tokens.

Invalid or missing model output is scored as failure and is never re-run.
Transport failure also settles the request and stops the run if request
correspondence or raw capture is not trustworthy.

## Frozen Estimand

For each actor task, score the single submission under:

1. exact match;
2. sufficiency only;
3. composite sufficiency + scope precision + answer coverage.

Report separately for 13 pre and 13 post tasks:

- plan sufficiency;
- plan precision macro and micro;
- answer coverage;
- composite acceptance;
- revision rate on the three decision flips;
- preservation rate on the ten invariant pairs.

Also report invalid schema, `NO_OUTPUT`, raw-pair completeness, actual
input/output/accounting tokens, and wall time.

## CC013 Alternate-Path Probe

| Probe | Outcome | Selected evidence | Pre reference | Post reference |
|---|---|---|---|---|
| clean canonical | approve | `manager_approval`, `receipt` | sufficient | sufficient |
| alternate path | approve | `card_statement`, `manager_approval`, `merchant_invoice` | sufficient | insufficient |

The alternate selection is the only manipulated factor. It demonstrates that
the decision remains invariant while the valid sufficient-set family changes.
This probe is scored offline and is not an additional model request.

## Stop Rules

- Stop on model identity or runtime drift.
- Stop on actor/reference leakage.
- Stop on raw request/response loss or request mismatch.
- Stop before exceeding 26 physical requests or 113,152 run accounting tokens.
- Preserve partial results on stop; do not restart under another raw root.
- Do not run Tier 2 feedback-revision arms.
- Do not change policy, cases, reference, output schema, or metrics after the
  first request.

## Explicit Non-Claims

- No feedback effect: feedback is not shown to the model.
- No learning or experience-retention claim.
- No independent generalization claim.
- No human gold or expert sign-off.
- No claim that composite precision is general selection tightness.
