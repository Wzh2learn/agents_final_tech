# Independent Behavioral Probe Review

Review date: 2026-10-21

Scope: `ntripbrowser_qualification_v2/` qualification evidence, frozen
behavioral snapshot, three raw request/response pairs, candidate test/JUnit
evidence, probe report/receipt, and the settled budget event. No run artifact
was edited and no model call was made.

## Verdict

**PASS for the bounded hybrid-oracle claim.**

The supported claim is exactly:

> For this `chardet -> cchardet` real-commit migration case, hidden behavioral
> tests alone can accept a candidate that violates the requested dependency
> change; the task therefore requires both behavioral tests and a structural
> dependency/API contract.

**Representation superiority: REJECTED.**

**General migration capability: REJECTED.**

## V4 Qualification

Direct JUnit and exit-code evidence verifies the V4 matrix:

| Snapshot | Environment | Exit | JUnit | Interpretation |
|---|---|---:|---:|---|
| parent `ed5f52b2...` | parent packages | 0 | 7 tests, 0 failures/errors | Parent behavior passes. |
| gold `9161c194...` | gold packages | 0 | 7 tests, 0 failures/errors | Gold behavior passes. |
| parent | gold packages | 4 | collection error | Missing `chardet`. |
| gold | parent packages | 4 | collection error | Missing `cchardet`. |

The cross-environment blocks are import/collection failures, not behavioral
test failures. They verify distinct dependency environments and the need for
each snapshot's matching detector package.

Seven live-network tests were excluded before execution. The behavioral oracle
therefore covers seven deterministic local/mocked tests only.

## Candidate Results

Independent JUnit and AST recomputation reproduces:

| Arm | Behavioral | Structural | Hybrid | Tokens |
|---|---:|---:|---:|---:|
| BASE | 7/7 | fail | fail | 4,224 |
| PROSE_CHANGE_FACTS | 7/7 | pass | pass | 4,176 |
| STRUCTURED_CHANGE_FACTS | 7/7 | pass | pass | 4,212 |

All three JUnit suites contain exactly seven tests with zero failures, errors,
or skips. All three raw responses match the frozen request snapshot and ledger
after normalizing the API-only `prompt_tokens_details` field.

### BASE False Positive

BASE does not import `chardet` or `cchardet`, but calls `chardet.detect` inside
a broad `try/except Exception`. The resulting `NameError` is swallowed, the
encoding becomes `None`, and `_decode_data` falls back to UTF-8.

The selected fixtures therefore pass despite all of the following:

- `cchardet` is not imported.
- `cchardet.detect` is not called.
- `chardet.detect` remains in the source.
- The requested dependency migration is not implemented.

This directly demonstrates a behavioral-only false positive.

### Explicit Change Arms

PROSE_CHANGE_FACTS and STRUCTURED_CHANGE_FACTS both import `cchardet`, do not
import `chardet`, call `cchardet.detect`, pass all seven tests, and pass the
structural contract.

Both explicit-change arms succeed identically. The run provides no evidence
that prose change facts are better or worse than structured change facts.

## Hybrid Oracle Judgment

The evidence supports adding the structural gate to behavioral evaluation:

1. Behavioral tests establish preserved behavior on the selected fixtures.
2. The structural contract establishes that the requested dependency/API
   replacement occurred.

The accurate conclusion is:

> Use a hybrid behavioral plus structural oracle for dependency-migration
> tasks where fixture behavior can be preserved through fallbacks or stale
> APIs. Do not infer representation effects from this run.

This proves behavioral-only evaluation is inadequate for this case. It does
not prove that the implemented import/call checker is universally sufficient
for semantic equivalence.

## Arithmetic And Settlement

- Raw attempts: 3.
- Physical generation calls: 3.
- BASE: 4,224 tokens.
- PROSE: 4,176 tokens.
- STRUCTURED: 4,212 tokens.
- Total: `4,224 + 4,176 + 4,212 = 12,612`.
- Reservation: 3 attempts / 30,000 tokens.
- Ledger event: 3 attempts / 3 calls / 12,612 tokens,
  `SETTLED_COMPLETE`.

`MODEL_LEDGER.json` and `PROBE_RESULT.json` are byte-identical and agree with
`PROBE_RECEIPT.json`. Focused contract tests pass: `3 passed`.

## Rejected Claims

This probe does not support:

- prose superiority over structured facts;
- structured superiority over prose;
- general model migration capability;
- population-level PyMigBench performance;
- natural production drift;
- live NTRIP correctness;
- semantic equivalence beyond the selected tests and structural rule;
- stability across repeated generations or other migration types.

There is one real commit/module and one model sample per arm. Both explicit
arms pass, so there is no representation contrast to adjudicate.

No model or network calls were made during this review.
