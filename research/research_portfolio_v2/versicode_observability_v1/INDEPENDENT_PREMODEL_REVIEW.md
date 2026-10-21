# Independent Pre-Model Review

Review date: 2026-10-21

Review type: independent AI review, not human review.

Scope: `versicode_observability_v1/` and only the
`VERSICODE_OBSERVABILITY_V1_20261021` reservation in
`../COST_AND_CANDIDATES.json`.

## Go/No-Go Verdict

**NO-GO. Do not issue the first model request from the current frozen
`REQUEST_SNAPSHOT.json`.**

The snapshot violates the requirement that generated prompts never expose
oracle `new_code`.

## Blocking Finding

### Critical: exact oracle `new_code` is present in all four task-5 prompts

Task `old_to_new_3330` records:

- `public.old_code`:
  `_hash_file('/path/to/file.zip')` followed by a SHA-256 string.
- `oracle.new_code`:
  `hash_file('/path/to/file.zip')`.

Because `hash_file('/path/to/file.zip')` is a literal substring of
`_hash_file('/path/to/file.zip')`, the exact oracle target code appears inside
the shared old-code block. It is therefore present in BASE, PROSE_MAPPING,
STRUCTURED_MAPPING, and PROBE_EVIDENCE prompts, corresponding to attempts
17-20 in `REQUEST_SNAPSHOT.json`.

This is answer leakage, not merely the permitted presence of the old API name.

The validator misses it because `validate_prompt` compares only the AST of a
whole Python code block with the AST of `new_code`; it does not reject exact
`new_code` substring occurrence anywhere in a prompt
(`run_probe.py:449-453`). The synthetic leakage test uses a target that is not
a suffix substring of the old code and therefore does not reproduce this case
(`test_run_probe.py:50-57`).

Required before any request:

1. Exclude or replace `old_to_new_3330`. If the requirement remains "never
   expose oracle `new_code`," rewriting the old code would change the source
   task and is not an equivalent fix.
2. Reject exact `new_code` occurrence anywhere in the generated prompt, not
   only whole-block AST equality.
3. Add a regression case where the new call is a suffix substring of the old
   call, such as `_old_api(...)` changing to `old_api(...)`.
4. Regenerate `VERSICODE_TASKS.json`, `REQUEST_SNAPSHOT.json`, and
   `PRE_MODEL_REPORT.md`; then re-run the pre-model review.

## Targeted Check Results

| Check | Verdict | Evidence |
|---|---|---|
| No prompt exposes oracle `new_code` | **FAIL** | Exact `new_code` occurs in all four attempts for `old_to_new_3330`; 28 other prompts pass the exact-string audit. |
| BASE excludes exact target API outside old code | **PASS** | All eight BASE prompts pass the word-boundary check after removing Python code blocks. |
| PROSE_MAPPING and STRUCTURED_MAPPING contain the same mapping facts | **PASS** | All 8/8 pairs contain the same source and target API names; structured `change_type` is `name_change`, matching the prose replacement relation. |
| PROBE_EVIDENCE is derived without target name/gold | **PASS** | `query_symbols(symbols, row["old_name"])` builds the probe before `gold_rank` is computed from `new_name`; `new_code`/`new_name` are stored only under `oracle`. Candidate lists may naturally include the target symbol, but the ranking query does not use it. |
| Request payload preserves model and generation contract | **PASS** | 32/32 payloads use the exact model, `enable_thinking: false`, `response_format.type: json_object`, temperature 0, top-p 1, and max tokens 512. Each request message equals the frozen prompt. |
| No retry | **PASS** | The runner iterates each planned request once and stops on the first model/contract failure. `retry_cap` is 0 and concurrency is 1. |
| Budget reservation | **PASS** | Spec and reservation both contain 32 attempts and 80,000 accounting tokens; status is `RESERVED_NOT_RUN`. |
| Evaluation remains non-behavioral | **PASS** | `evaluate_code` performs syntax parsing and AST name checks only. The report/result state that no behavioral execution oracle is claimed. |
| Tests cover leakage and response parsing | **PARTIAL / INSUFFICIENT** | Five tests pass, including prompt/gold guards and exact response-envelope/usage parsing. The leakage test misses substring `new_code`; the parser test does not exercise model mismatch, missing usage, invalid usage types, or usage-sum failure. |

## Frozen Snapshot Integrity

- 32 planned attempts.
- 32 unique attempt indexes.
- 32 unique request hashes.
- Eight task IDs and eight source-record hashes.
- `tasks_sha256` is enforced by the runner before model execution.
- `pre_model_v0_unrequested/` is not used by the current runner.

The current `PRE_MODEL_REPORT.md` states that gold code is never in prompts.
That statement is false for `old_to_new_3330` and must not be relied on.

## Evaluation Scope

The planned metric is syntactic validity plus exact hidden target-symbol use
with old-symbol removal. It does not execute code or establish behavioral
correctness. This limitation is clearly stated in the experiment artifacts and
is acceptable for the observability ablation, but the metric must not be
described as behavioral or production migration validity.

No model or network calls were made during this review. No package files were
edited except this review document.

## Targeted Re-review

Re-review date: 2026-10-21

**GO. The prior blocking leakage is resolved in pre-model revision 3.**

- `old_to_new_3330` is absent and is replaced by exactly one
  `old_to_new_20751` task.
- The replacement's `oracle.new_code` is not a substring of its old code or
  any of its four frozen prompts. A strict scan of every prompt found zero
  exact `oracle.new_code` occurrences.
- `validate_prompt` now rejects exact `oracle.new_code` substring occurrence
  anywhere before the AST-equivalence check.
- The regression test covers the original suffix-substring failure mode
  (`_hash_file(...)` versus `hash_file(...)`).
- Local tests pass: `6 passed`.
- The strict validator passes all `32/32` frozen prompts.
- The specification and report identify pre-model revision `3`.
- The budget ledger contains exactly one matching reservation row:
  `VERSICODE_OBSERVABILITY_V1_20261021`, 32 attempts, 80,000 accounting
  tokens, status `RESERVED_NOT_RUN`.

No model or network calls were made during this targeted re-review.
