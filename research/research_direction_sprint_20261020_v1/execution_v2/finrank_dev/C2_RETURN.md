# C2 Return: Equal Visibility And ESD_006 Reference Scope

Status: `COMPLETE_WITH_C3_BLOCKERS; B0_V3_NOT_FINAL_BASELINE`

C2 was a targeted correction. It did not collect history, run a pilot, change
the model, raise `max_tokens`, retry, or alter any B0 V1/V2 raw or result.

Independent review after this return found two deterministic blockers, so B0
V3 is retained as an intermediate observation rather than the final
development baseline:

1. `_unit_matches("%", "percent")` is false because literal `%` tokenizes to
   the empty set. ESD_004's values, labels, periods, evidence, and tool
   consistency are correct, so V3 requires a preserved original score plus a
   versioned post-hoc scorer rescore.
2. ESD_012 consume reached `finish_reason=length` and the JSON was truncated.
   The raw must not be repaired. Under the same schema, model, and
   `max_tokens=256`, C3 adds a minified JSON/no-outer-whitespace output
   constraint and runs one complete B0 V4.
3. `answer_tool_consistency` accepted arbitrary two-number arithmetic, so an
   unrelated `10127/846` pair could falsely support `11.97`. C3 replaces this
   with literal-evidence support or explicit reference-gated derivations.

These blockers are handled in `C3_CORRECTION_SPEC.md` and
`C3_RETURN.md`. ESD_006 `UNKNOWN` remains a real non-success and is not
converted by the scorer correction.

Reproducibility limitation: C2 has no immutable source-code snapshot directory.
`BUNDLE_C2_B0_V3.json` preserves the original artifact hashes and bundle hash,
but current source files have drifted into C3. `C2_VERIFICATION.json` verifies
historical results and manifests while explicitly marking this limitation.

## Root Cause And Frozen Fixes

The comparison had two independent defects:

1. B0 plan saw only candidate IDs, page numbers, and source metadata, while the
   strong rule read full candidate text. Candidate text length in the B0 V2
   plan input was zero; the strong-rule input contained the full passages.
2. ESD_006 asked for gross profit and gross margin percentage, while reference
   V1 also required revenue and cost operands as answer atoms.

C2 froze `FULL_VISIBLE_CANDIDATES_AT_PLAN` before B0 V3. B0 and the strong rule
now consume the same candidate ID, text, page number, and visible source scope
at planning time. `evidence_lookup` still returns requested originals in order,
and consume can cite only returned IDs.

Reference V2 changes only ESD_006:

- Required answers: derived gross profit and gross margin percentage.
- Verification operands: Automotive revenue and Automotive and other cost of
  sales.
- All other task references and `REFERENCES_V1.json` remain unchanged.

Bundle:

```text
6b861dcfdbb8efd847b40652ad7abc90fde1cdf17686cc159b27b98d08e02b6e
```

Offline fixtures pass `17/17`, including equal plan-time visibility and an
ESD_006 differential fixture showing V1 misses the two operands while V2
accepts the two requested derived answers.

## B0 V3 Result

The frozen strict result is `4/7`, with `14/14` requests completed and no retry.

| Layer | Result |
|---|---:|
| Plan contains a minimal sufficient set | 7/7 |
| Consume cites a sufficient set | 6/7 |
| Frozen answer-reference match | 4/7 |
| HTTP/raw/tool-chain failures | 0 |
| Model output-format failures | 1 |
| Remaining semantic/contract non-successes | 2 |

Task outcomes:

| Task | Frozen outcome | Diagnosis |
|---|---|---|
| ESD_001 | SUCCESS | Full visibility resolved selection and answer facts |
| ESD_002 | SUCCESS | Selected the content-period evidence and answered |
| ESD_003 | SUCCESS | Joint `cand_006+cand_007` evidence used |
| ESD_004 | NON_SUCCESS | Returned 8.7% and 20.8%; checker does not normalize literal `%` as percent |
| ESD_006 | NON_SUCCESS | Evidence was sufficient, but actor returned `UNKNOWN` |
| ESD_010 | SUCCESS | Sufficient subset and both liabilities matched |
| ESD_012 | NON_SUCCESS | Correct-looking facts were truncated at `finish_reason=length`, so JSON was invalid |

ESD_004 is preserved as a frozen non-success. A post-hoc diagnostic identifies
a scorer unit-token limitation; it is not silently rescored in this return.
ESD_012 is a model output-format failure at the unchanged
`max_tokens=256`, not an HTTP, raw, or tool failure.

## Baseline Comparison

| Metric | B0 V2 | B0 V3 |
|---|---:|---:|
| Frozen success | 1/7 | 4/7 |
| Plan sufficient | 3/7 | 7/7 |
| Consume sufficient | 3/7 | 6/7 |

The deterministic strong rule under the same full candidate visibility selects
a sufficient plan for `7/7`; its extractive consume cites a sufficient set for
`6/7` but remains `0/7` on strict answer atoms. It is useful as a selection
control, not an answer-generation upper bound.

## Scientific Interpretation

Equal visibility closes the evidence-selection gap on this small development
panel: B0 now reaches `7/7` plan sufficiency. The remaining decision space is
in consumption and output reliability:

- whether sufficient evidence is used to form all requested facts;
- whether the actor abstains despite sufficient evidence;
- whether structured JSON remains complete under fixed output budget.

This does not establish historical-experience benefit. It says a future
experience study on this panel should target consumption/abstention/output
behavior, not evidence retrieval, and only after the ESD_004 scorer unit alias
is versioned and resolved.

## Accounting

| Run | Requests | Accounting tokens |
|---|---:|---:|
| B0 V1 | 14 | 19,034 |
| B0 V2 | 14 | 46,830 |
| B0 V3 | 14 | 196,038 |
| Total | 42/192 | 261,902/2,000,000 |

All 42 records are settled. Judge calls, training calls, production Memory
writes, and history collection requests are zero.

## Evidence

- Root cause and frozen choices: `C2_ROOT_CAUSE.md`
- Task/reference V2: `TASKS_ACTOR_V2.json`, `REFERENCES_V2.json`
- Fixtures: `FIXTURE_RECEIPT_C2.json`
- B0 V3 raw/result: `raw/B0_V3_EQUAL_VISIBILITY/`,
  `results/B0_V3_EQUAL_VISIBILITY/B0_RESULT.json`
- Strong rule: `results/STRONG_RULE_RESULT_C2.json`
- Machine verification: `C2_VERIFICATION.json`
- Shared ledger: `../execution_v1/RESEARCH_GENERATION_LEDGER.json`
