# Loop A Task: Formal Build, Valid Rescoring, Persistent Budget, Mechanism Diagnostic

Task ID: `adaptive-mechanism-a-20261027`
Date: 2026-10-27, Asia/Shanghai
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `17f6895e3f2734f5e597f1a1d7853af22ae2adf4`
Authority LF SHA256: `73da0c8a44512c4b47d677efa3a7c71b45fb7d15e582a77737c27c284f800d12`

## Boundary

Execute one bounded A task on GB10. Other loops may work in the repository;
do not revert or overwrite unrelated changes. Preserve all historical raw,
scores, manifests and reports. Do not edit frozen evidence, production
services, credentials, `memory/`, or the unique prompt.

Create and own only:

- `research/adaptive_mechanism_20261027_v1/`
- the existing thesis files
  `research/feedback_learning_phase_b_20261026_v1/thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md`
  and `research/feedback_learning_phase_b_20261026_v1/thesis_draft/EVIDENCE_TABLE.md`.

No training, LoRA/SFT, old R/E restart, judge, production probe, formal
submission, payment, public release or external contact is authorized.

## 1. Paper E Formal Build

Reuse `research/publication_proxy_calibration_20261026_v1/paper_e_sncs/` and
the existing two-case manuscript. Do not add P1/P2 results to Paper E.

Search only for an already-installed usable TeX toolchain. Do not repeat the
failed GitHub download chain, install system packages, bypass the Windows
sandbox, or call an external build service. If a usable local engine exists,
compile the canonical LaTeX and inspect:

- complete body, formulas, tables, figures, 24 references, cross-references
  and final page;
- source hash, exact engine/version, complete log, PDF hash and page count;
- bibliography rendering, author placeholders, structured abstract and
  declarations.

If no usable engine exists, mark `BUILD_BLOCKED` and create a directly
buildable source bundle under `paper_e_formal_build/` containing canonical
TeX, BibTeX, figures, a standard supported bibliography style or explicit
style dependency, build script, exact command and `BUILD_BLOCKED.md` with the
observed tool errors. Run all non-TeX source checks. A fallback PDF is not a
formal build.

Perform one substantive first-reviewer check of contribution/nearest-work
separation, the interpretation changed by the two cases, clustered/post-hoc
identity, claim boundaries and reference readability. Keep Owner identity,
patent, artifact and submission fields pending.

## 2. Scoring V2 And First-Batch Zero-Model Rescore

Historical results remain immutable. Build `scoring_v2/` and rescore only the
first immutable 40-call batch, selecting the final attempt for each of 12 UIDs
x 3 arms. Model loading and generation are forbidden in this phase.

The scoring contract must report separate layers:

1. strict JSON/schema/format;
2. answer content and exact set completeness;
3. numeric equivalence, unit/scale and direction;
4. evidence-reference existence and semantic support;
5. final delivery.

Use statuses such as `ACCEPT`, `REJECT`, `PENDING_ADJUDICATION`,
`STRICT_FAIL`, `REASONABLE_UNKNOWN`; do not collapse them. PENDING is not
WRONG. A correct number alone is not complete delivery.

Fix reference extraction for string/dict/list programs and visible paragraph
mapping. The actor never receives gold, expected refs, hidden units or UID
branches. If a legal reference/semantic support cannot be reconstructed,
return PENDING rather than inventing it.

Add positive and adversarial controls before trusting the new score:

- semantically equivalent currency display;
- exact multi-span set;
- correct mean/count typed reduction;
- wrong unit or direction;
- extra span;
- wrong period or row;
- missing/nonexistent/out-of-range reference;
- numerically equal answer in the wrong role;
- negative count and numeric-array contract violations.

Prove correct responses can reach ACCEPT and the listed errors cannot be
silently accepted. Record AI/automatic review identity; no human-gold claim.

Rescore all 36 primary results and produce per-layer counts, per-UID outcomes,
and paired arm summaries. Keep the historical `2/3/3` score visible beside the
new score. Correct the top-5 minus top-3 final-attempt input delta to 917 and
the all minus top-5 delta to 1604.

## 3. Persistent Physical Budget

Implement generation accounting outside any per-run output directory. Use an
append-only, atomic, locked ledger under
`/home/testuser/wzh/research_runs/persistent_budget/adaptive_mechanism_20261027/`.
The repository package must contain the schema, runner and a receipt pointing
to the external ledger hash.

Required behavior:

- separate `generate`, `resume` and `rescore` commands;
- logical call IDs separate from physical attempt IDs;
- persist a conservative reservation before every model call;
- append raw response and actual usage immediately after each call, fsync
  before scoring;
- score only after raw persistence;
- crash/timeout/restart/output-directory changes never reset cumulative use;
- an uncertain reserved attempt remains consumed;
- the first call beyond 36 physical attempts or 240,000 input+output tokens is
  rejected before model loading;
- `rescore` loads no model and creates no generation records;
- common normalization/calculator is shared across all applicable arms.

Verify without model loading by fault injection:

1. scoring throws after raw persistence and restart/rescore adds zero calls;
2. crash after reservation and before raw keeps the conservative reservation;
3. crash between calls preserves every earlier raw row;
4. changing output directory cannot reset the ledger;
5. attempt 37 and the token-cap successor are rejected before model load.

Do not call a real model merely to prove the guard.

## 4. Error Cards And Mechanism Selection

Before model output, create one error card for each of the nine old shared
REJECT UIDs and three non-shared controls. Use the real question, immutable
first-batch raw and visible context, not model self-labels. Allow multiple
labels: reference defect, visible information insufficient, fact/entity/row/
period binding, operation/reduction, unit/direction, format and citation
support.

After scoring V2, identify which failures remain. Prioritize the observed
signals:

- mean question with correct operands but no mean reduction;
- count question with the correct quarter set but no count.

Build a visible-only transparent typed reduction/calculator baseline. It may
use only deployed visible evidence and deterministic public parsing; no gold,
UID branch, expected program or hidden scale.

Select at most eight development UIDs before new outputs:

- real residual failures after scoring V2;
- at least one mean/count mechanism signal;
- at least two controls that were already correct or non-equivalent.

Freeze the UID list, hypotheses, arms, prompts, output contract, calculator,
model/checkpoint hash, decoding and stop rules in a preregistration receipt.

If an unexplained natural residual remains, compare exactly three arms on the
same fixed base model and matched resource budget:

1. direct answer;
2. neutral typed tool/program baseline with shared calculator;
3. one candidate mechanism, chosen from the actual cards, such as verified
   role/type binding, typed reduction, limited evidence retrieval or local
   correction.

Do not give only the candidate free tools or more reasoning. Do not change
model/checkpoint to manufacture a method gain. Report answer, unit/direction,
reference support, typed operation, strict contract and complete cost for
every attempt. If the transparent baseline explains the residual, accept it
and stop the panel method candidate.

## 5. Bounded Generation

Only after scoring V2, persistent budget fault tests and preregistration all
pass may `generate` run.

- At most eight UIDs x three arms = 24 primary physical attempts.
- At most 12 additional physical attempts for preregistered interface
  positives, preserved failures or bounded retries.
- Hard cap 36 physical attempts and 240,000 input+output tokens.
- Training remains zero.
- Every physical attempt counts, including failures, retries and interface
  positives.

The base actor is local base Qwen3-4B or another already-authorized local
checkpoint only if frozen before output and justified by interface
qualification. No old SFT/R/E checkpoint. Do not run confirmation or call the
new panel a new-source validation.

Return a continue/stop decision for this candidate only. If the strong simple
baseline explains the result, stop it. If a real signal remains, write one
short next-stage independent-source research card; do not run confirmation.

## Completion Evidence

Write `A_RETURN.md` and structured JSON receipts under
`research/adaptive_mechanism_20261027_v1/`. Include:

- Paper E build or `BUILD_BLOCKED` evidence;
- scoring V2 tests and zero-model first-batch rescore;
- per-layer and per-UID results;
- persistent-ledger schema/hash and all fault-injection commands;
- error cards and frozen diagnostic panel;
- raw model outputs and complete physical budget ledger if generation ran;
- exact calls, input/output tokens, retries and wall time;
- substantive Chinese thesis additions;
- A harness input/cache/output/reasoning usage separately;
- a commit containing only owned paths.

Do not claim C acceptance before the independent fixed-snapshot C task exists.
