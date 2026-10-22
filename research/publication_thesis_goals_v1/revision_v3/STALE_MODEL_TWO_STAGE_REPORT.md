# STALE Two-Stage State-Card Probe

Date: 2026-10-23, Asia/Shanghai

Status: `COMPLETE_DEV_MECHANISM_PROBE`

Evidence identity: `DEV_ONLY_TWO_STAGE_MECHANISM_PROBE`

Visibility: `DEV_ONLY_TWO_STAGE_MECHANISM_PROBE_ORACLE_RETRIEVAL`

## Question

Can a compact state card extracted from raw relevant sessions recover
stale-state detection without exposing hidden benchmark fields to the final
answer stage?

## Contract

- Same four UIDs and `dim1_query` as the main probe.
- Oracle relevant top-2 raw sessions are supplied, so retrieval is not tested.
- Stage 1 sees raw sessions plus query and returns exactly
  `{old_state,new_state,change_type}`.
- Stage 1 never sees `M_old`, `M_new`, `explanation`, or
  `relevant_session_index`.
- Stage 2 sees only the Stage 1 state-card output plus query and returns the
  existing five-field answer object.
- Eight sequential calls: four extraction and four answer calls.
- Qwen3.6-35B-A3B Q4, temperature 0, `max_tokens=256`,
  `enable_thinking=false`, JSON object output, zero retries.
- Stage 1 output is retained as-is if malformed or semantically wrong.
- Official STALE judge not run.

## Execution Evidence

| Quantity | Result |
|---|---:|
| Planned generation calls | 8 |
| Executed generation calls | 8 |
| Physical HTTP calls | 8 |
| HTTP 200 | 8 |
| Stage 1 strict state-card valid | 4/4 |
| Stage 2 strict answer valid | 4/4 |
| State-card output leak count | 0 |
| Retries | 0 |
| Accounting tokens | 15,708 |
| Total model latency | 16.883 s |
| Official judge calls | 0 |

Stage 1 used 14,209 tokens; the compact Stage 2 used 1,499 tokens. Every stage's
exact request and response is under `stale_model_two_stage_raw/`. The result
hash is `c0ba756d035b75220e8e9658f1edce9b46d1b41ea7ba03c3c6e3b9568fa4254f`.

## Comparison

| Representation | Calls | STALE_DETECTED | Negative old-state answer | Identity |
|---|---:|---:|---:|---|
| One-shot oracle raw sessions | 4 | 1/4 | 1/4 | main dev probe |
| Two-stage raw sessions -> state card -> answer | 8 | 3/4 | 3/4 | deployable mechanism, oracle retrieval |
| Explicit `M_old/M_new` only | 4 | 4/4 | 4/4 | non-deployable oracle diagnostic |
| Explicit values plus explanation | 4 | 4/4 | 4/4 | non-deployable oracle diagnostic |

The two-stage representation improves over one-shot raw-session reasoning on
this fixed set while using approximately the same order of token cost. It does
not reach the explicit-state oracle ceiling.

## State-Card Outcomes

- `01f694b2` T1: correctly extracted an education-state change; answer was
  negative old-state and `STALE_DETECTED`.
- `04fea765` T1: failed extraction. It copied the old pressure-washer state as
  both old and new, missing the evidence that the item had been returned. The
  answer consequently remained positive old-state and
  `STALE_NOT_DETECTED`.
- `009b7c99` T2: extracted the walking-boot state and marked
  `PROPAGATED`; answer was negative old-state and `STALE_DETECTED`.
- `012f090e` T2: extracted the brokerage-transfer state and answered
  correctly, but labeled the relation `CO_REFERENTIAL` rather than the
  benchmark's propagated relation. The final state decision was still correct.

Observed `change_type` counts were three `CO_REFERENTIAL` and one `PROPAGATED`.
These are model-produced descriptions, not gold labels.

## Mechanism Judgment

The result supports a limited two-stage mechanism claim:

> A compact state-card intermediate representation can recover two of the
> three stale-state detections lost by one-shot raw-session prompting, without
> exposing hidden state labels to the answer stage.

The residual failure is upstream state extraction, not final answer polarity
once the correct change is represented. The Type II case also shows that final
state detection can be correct even when causal `change_type` is mislabeled.

This is not yet evidence for a full method contribution. Retrieval is oracle,
the sample is four development cases, and no independent confirmation set has
been run. The next scientifically useful step is a frozen non-oracle retrieval
condition on new instances, comparing one-shot versus two-stage state cards at
matched retrieval and token budgets. If the gain disappears under realistic
retrieval or a simple extraction rule matches it, stop the method claim.

## Oracle Diagnostic Recovery Root Cause

Systematic-debugging root cause: `stale_model_oracle_diagnostic.py` omitted
`sha256_bytes` from its import list and raised `NameError` at the exact
expression `"preflight_response_sha256": sha256_bytes(preflight_raw),` while
assembling `results` after `run_rows()` had already completed and persisted all
eight calls. This was a post-generation bookkeeping defect, not a model/API
failure. The source fix imported `sha256_bytes`; the no-retransmission repair
added `--recover-existing`, reconstructing rows only from preserved raw
requests/responses. Regression coverage is
`test_raw_recovery_is_order_and_identity_checked`; the full command
`python3 -m unittest -v stale_model_probe_test.py stale_model_oracle_diagnostic_test.py stale_model_two_stage_probe_test.py`
passed 18/18, and pre/post manifests for all 32 diagnostic raw files were
identical with `generation_calls_reexecuted=false`.

## Limits

- Four instances and one query dimension.
- Oracle relevant raw sessions isolate representation but do not test retrieval.
- State cards are generated text, not human or executable semantic gold.
- Answer polarity is a lexical proxy, not the official STALE judge.
- No claim is made about full 400-item accuracy, other models, or CUPMem.

## Frozen New-UID Paired Check

After the four-case development probe, the prompt, metrics and comparison were
fixed before selecting eight additional, unused UIDs from the same public STALE
release: four T1 and four T2, sorted by UID and excluding the development UIDs.
Only `dim1_query` and oracle relevant top-2 raw sessions were used. The paired
comparison retained the existing one-shot prompt and the existing two-stage
state-card prompts without further tuning.

The primary pair success requires both `state_resolution == STALE_DETECTED`
and `answer_polarity == NEGATIVE_OLD_STATE`.

| Arm | Calls | Pair success | T1 | T2 | Tokens |
|---|---:|---:|---:|---:|---:|
| One-shot raw oracle sessions | 8 | 0/8 | 0/4 | 0/4 | 23,953 |
| Two-stage state card | 16 | 4/8 | 2/4 | 2/4 | 25,560 |

The paired difference is `+4/8 = +0.50` for two-stage over one-shot. Four cases
improved and four were failures under both representations; there were no
one-shot-only successes. One-shot produced one `UNKNOWN`; two-stage produced
one final `UNKNOWN`. All 24 calls returned HTTP 200 and valid strict JSON, with
zero retries and zero hidden-field output leaks.

This check supports a bounded representation hypothesis:

> Under oracle retrieval on new UIDs from the same public STALE release, a
> raw-session-to-state-card intermediate step improves paired stale-state
> handling over one-shot prompting at the tested model and budget.

It is not an independent external confirmation. Retrieval remains oracle,
the eight UIDs come from the same release and query dimension, state cards are
model outputs rather than semantic gold, and answer polarity is a deterministic
lexical proxy rather than the official judge. The result does not establish
full benchmark accuracy, a retrieval method, or a general memory mechanism.

Evidence:

- `stale_model_new_uid_confirmation_20261023_v1/STALE_MODEL_NEW_UID_CONFIRMATION_RESULTS_V1.json`
  SHA-256
  `b213d524534f0b8e1d5008344a4edf2fe4df8e53403bcc7fef06a73ab12ed83c`.
- Receipt SHA-256
  `c9db0eccccb6bfc08222e0a7fe75c1d03680287506ab62fc95e71b99c1365ed8`.
