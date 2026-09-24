# Independent Loop C audit of the phase1a label_ledger assembler (model qwen3.8-max)

> Dispatched 2026-09-24 against commit b35188a; evidence packet inline; no tools; 1 turn(s), cost $0.3195.
> Verdict: PASS_WITH_NOTES - independence rules and JSON Lines shape match; F1-F3 (coded malformed paths, rationale_ref enforcement, rejection-path tests) requested before gate use.
> Body verbatim.

# Loop C Independent Audit — phase1a label_ledger assembler (b35188a)

## Verdict: **PASS_WITH_NOTES**

No independence-rule gap from the audit checklist and no artifact-shape drift was found; both REJECT triggers are clear. Notes below concern robustness, validation depth, and test coverage.

---

## Check results

**(1) Independence rules — MATCH.** Every enumerated rule is enforced fail-closed in `assemble()`: generator excluded from both reviewers and adjudicator (`generator_in_reviewers`, stricter than protocol §1 which only bars R1/R2); reviewers distinct (`reviewers_not_distinct`); adjudicator ∉ reviewer_ids (`adjudicator_is_reviewer`); iteration over `set(j1) | set(j2)` forces any single-sided pair to raise `incomplete_review_pair` (double review); disagreement requires an adjudication entry and `gold` is *constructed from* the adjudicated choice, so the contract's `gold_adjudication_mismatch` cannot fire; agreement sets gold to the shared choice, satisfying `gold_review_mismatch`; `_valid_choice` is a byte-for-byte mirror of the contract's (map_to ⇒ non-empty str target, skip/hold ⇒ null target); `multiple_columns_per_sample` plus tuple-keyed dicts guarantee one labelled column and one row per sample_id, matching the contract's `duplicate_label` uniqueness. `uid_disagreement` adds an identity check the contract can only verify downstream.

**(2) Artifact shape — MATCH.** Pure JSON Lines, one object per line, `"\n"`-terminated with `newline="\n"`; each row dict has exactly the 8 `LABEL_FIELDS` keys (no `_choice` leakage — rows are rebuilt field-by-field); `quality_grade` hardcoded `"Q3"`; reviewer entries carry exactly `reviewer_id/action/target`; adjudication entries carry exactly `adjudicator_id/action/target/rationale_ref` and are `null` on agreement (contract only inspects adjudication on disagreement, so null is conformant). Carriers, template versions, generator id, agreement rate, and timestamp live solely in the sidecar meta. Emitted rows will pass the contract's row-level validation (with the col≥0 caveat in Finding 4).

**(3) Fail-closed — SUBSTANTIALLY MET.** All 12 `LabelAssemblyError` paths carry machine-readable codes; `main()` performs zero writes before `assemble()` returns, and the payload is fully serialized in memory before the single `write_text`, so no violation path can produce a partial artifact. However, some malformed-input paths crash with non-coded exceptions (Finding 1) — still fail-closed in effect, but violating the letter of "every violation path raises with a machine-readable code."

**(4) Determinism — MET.** Rows emitted in `sorted(set(j1) | set(j2))` order — tuple sort on (sample_id, col), which is sample_id order given one row per sample; `json.dumps(..., sort_keys=True, ensure_ascii=False)` for both artifact and meta. Only the sidecar's `assembled_at` varies across runs (Finding 8).

**(5) Test suite — PARTIAL.** Covers both positives (agreement, adjudicated disagreement), six rejection paths (generator-in-reviewers, reviewers-not-distinct, adjudicator-is-reviewer, incomplete pair, missing adjudication, invalid judgment), and JSONL shape. Six rejection codes are untested (Finding 3).

---

## Findings

1. **[MEDIUM] Non-coded crash paths on malformed input.** (a) A judgment missing the `target` key with action `skip`/`hold` passes `_valid_choice` (via `.get()` → None) but then raises bare `KeyError` at `a["target"]` in the reviewers construction. (b) A judgment missing `uid` raises `KeyError` inside the `uid_disagreement` condition before the isinstance guard. (c) Non-dict top-level docs, non-dict adjudication `entries` elements (`e.get` → `AttributeError`), non-dict judgments, and unparseable input files (`json.JSONDecodeError`) all escape as uncoded exceptions. No partial artifact is possible in any case, but these violate check (3)'s machine-readable-code requirement. Fix: validate key presence in `_judgments_by_pair`, type-check docs/entries, wrap `json.loads`.

2. **[MEDIUM] `rationale_ref` is carried but never validated.** `entry.get("rationale_ref")` silently yields `null`; neither the assembler nor the contract (`_valid_choice` ignores it) rejects an adjudication without a rationale reference, weakening protocol §2's required `{adjudicator_id, action, target, rationale_ref}` trail and §1.2's 留痕 intent. Key presence keeps the *shape* conformant (hence no REJECT), but a disagreement adjudicated with `rationale_ref: null` becomes gold unchallenged. Fix: require non-empty string on the disagreement path.

3. **[MEDIUM] Test coverage gaps on rejection paths.** No named tests for `duplicate_judgment`, `uid_disagreement`, `multiple_columns_per_sample`, `adjudication_col_mismatch`, `adjudication_invalid`, or `missing_carrier_ids`; no robustness tests for the Finding-1 crash shapes or negative `col`. Check (5)'s "each rejection path" criterion is only ~⅔ met.

4. **[LOW] `col < 0` not pre-validated.** `_judgments_by_pair` enforces `type(col) is int` (correctly excluding bool) but not non-negativity; a negative col emits a row the contract rejects as `label_identity_mismatch`. End-to-end fail-closed holds, but the assembler should mirror the contract here.

5. **[LOW] Carrier distinctness recorded, not enforced.** Protocol §1 requires different judgment carriers (different model + prompt template, or human + machine). The assembler only enforces id distinctness and copies `template_version` into meta without requiring presence or difference — `[null, null]` or identical versions pass silently. Not treated as an independence-rule gap because the audit checklist operationalizes "reviewers distinct" as id distinctness, template inequality is not a valid proxy for the human+machine option, and Loop C evidence review (§1.4) is the intended enforcement layer — but meta should at minimum require both template versions to be present.

6. **[LOW] Meta omits the per-row disagreement table** required by protocol §3 (逐行分歧表); only aggregate `pairs`/`agreed_pairs`/`agreement_rate` are recorded. Disagreements are fully recoverable from the artifact (`adjudication != null`), so this is a presentation gap, not a data loss.

7. **[INFO] Adjudication file leniencies.** Entries keyed by `sample_id` with last-wins on duplicates and no error for entries never consumed (agreed pairs) or entries with missing `sample_id` (keyed `None`). `entry.get("col", col)` treats an absent col as matching. Harmless under the one-column-per-sample invariant but worth tightening.

8. **[INFO] Minor determinism/validation edges.** `assembled_at` makes the sidecar non-deterministic (artifact unaffected); `--generator-id ""` is accepted (vacuously safe, since empty reviewer/adjudicator ids already fail `missing_carrier_ids`); zero judgments produce an empty artifact with `agreement_rate: null` — downstream contract fails `missing_label`, so the pipeline remains fail-closed overall.

---

**Disposition:** Ship-eligible for phase1a assembly. Findings 1–3 should be fixed before the ledger is used for a LABEL_GO gate decision (they degrade diagnosability and leave the rationale trail unenforced); Findings 4–6 are hardening items; none invalidates rows already assembled from well-formed inputs.
