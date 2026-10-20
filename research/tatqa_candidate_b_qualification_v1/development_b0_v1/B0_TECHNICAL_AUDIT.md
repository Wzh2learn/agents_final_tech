# Candidate B Development B0 Technical Audit

Status: `VERSIONED_RESCORE_ACCEPTED_DEVELOPMENT_CEILING`

Authorization ID: `CANDIDATE-B-B0-20261019-0820-32REQ`

## Immutable run facts

- Request count: 32/32, no retry, single concurrency.
- Tasks: 16 development tasks across 8 source clusters.
- Actual accounting tokens: 18,477.
- Raw request directories: 32 complete, 0 crash, 0 response overwrite.
- Original runner result SHA-256: `ff558705fadc3490b95b78ad6eab4e92cd71468f158b58cce6d93b4875946e56`.
- Model/judge/pilot/training calls beyond the 32 actor requests: 0.

## Original runner outcome

The original runner reported `0/16` success and `CONTINUE_TO_ARM_DESIGN`. Decomposition showed:

- plan valid: 16/16;
- calculator execution successful: 16/16;
- consume contract valid: 16/16;
- numeric reference match: 16/16;
- answer/tool consistency: 16/16;
- exact unit-string match: 0/16.

This is a scoring implementation defect, not model headroom.

## Root cause

`candidate_b_b0_runner.py` compared `consume.unit` exactly with `hidden.deterministic_reference.unit`.

The task and output contract accept a bounded display unit such as `EUR millions`, `£m`, `$ million`, `€ thousands`, or `millions of EUR`. The frozen qualification checker already defines canonical unit/scale semantics through `infer_unit_context`, producing `EUR/GBP/USD` plus `million/thousand`.

The runner compared a display string to a canonical code. It therefore rejected semantically correct answers.

## Versioned correction

`candidate_b_b0_rescore_v1.py` reads the immutable raw response directories by `request.json.logical_id`, reparses plan and consume messages, recomputes the calculator result, and applies the already frozen `infer_unit_context` semantics. It does not alter tasks, references, raw responses, prompts, model outputs or request count.

Rescore result:

- success: 16/16;
- non-success: 0;
- semantic unit matches: 16/16;
- decision: `CEILING_ON_THIS_PANEL`;
- scientific label: `EXPLORATORY_POST_HOC_TECHNICAL_CORRECTION`.

## Interpretation boundary

The corrected development result is a ceiling for this fixed model/runtime and this Candidate B development panel. It does not prove that evidence binding is generally easy and does not authorize R/C/H.

Because the correction changes the original runner's decision, acceptance requires a targeted independent recheck of:

1. raw-to-response identity mapping;
2. frozen unit/scale semantics;
3. no post-hoc relaxation of numeric or contract checks;
4. no additional requests or task/reference changes.

Until that recheck is complete, retain both the original `B0_RESULT.json` and `B0_RESULT_RESCORE_V1.json` without overwriting either.

## Independent recheck

Loop C verdict: `ACCEPTED`.

- 32 raw request/response pairs were uniquely identified and complete.
- Rescore reparsed immutable raw responses and did not consume the original classification.
- Numeric, plan, tool and consume conditions were unchanged.
- Unit matching used the already frozen `infer_unit_context` semantics.
- No task, reference, prompt, model output or request changed.

Required caveat:

> `16/16` is an `EXPLORATORY_POST_HOC_TECHNICAL_CORRECTION` development ceiling for this fixed model/runtime and 16-task/8-cluster Candidate B development panel. Report it together with the original decision-flipping scorer defect and immutable `0/16` runner output. It does not show that evidence binding is generally easy and authorizes no R/C/H, new request or validation measurement without prospectively frozen unit semantics.
