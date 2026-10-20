# WP-0 TAT-QA Adapter and Checker Contracts v1

> date: 2026-10-13 | author: Loop D (WP-0 item A5) | status: `SPECIFICATION_ONLY - NOT IMPLEMENTED` | revisions 1.1-1.2 (2026-10-13): hidden-gold search clarified and canonicalized (Sec.4-5)
> parents: [WP0_TATQA_PACKAGE_v1.md](WP0_TATQA_PACKAGE_v1.md), [task card](../archive/2026-10-20_entry_consolidation/thesis_experience_v1_task_card.md), [blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md) §2
> These contracts describe what Loop A must implement in WP-1. Nothing here is code, and nothing here authorises a run.

## 1. Task adapter contract

**Input:** one candidate item from `data/research/tatqa_wp0_2026/candidate_items_v1.json`.

**Actor-visible projection (what the model sees):**
- the table (all rows and columns, verbatim, no truncation per arm);
- the two period labels and the row label/identifier needed to name the row;
- the requested quantity and the requested target unit;
- the tool description (a deterministic calculator: `calc(expression) -> number`);
- the arm-specific context block (none for B; the experience block for E/C; the static rules for S).

**Hidden from the actor, always:** `gold_delta_source_unit`, `gold_recompute_rule`, any derived target value, the item's origin id where it would leak the answer, and the whole `candidate_items` file.

**Actor obligations:** choose the row, the two periods, the unit relation and the arithmetic parameter; call the calculator; the final answer must consume the calculator's returned value.

**Answer format (fixed):** `{row: <label>, periods: [<late>, <early>], delta_source: <number>, delta_target: <number>, unit: <target unit>}` in a single JSON object, or the literal token `REFUSED` / `UNKNOWN`.

**Determinism:** the adapter must produce byte-identical prompts for the same item and arm. No timestamps, no sampling, no arm-dependent table truncation.

## 2. Checker contract

**Gold recomputation (independent of the actor):** for the item's `row_index`, read `value(late)` and `value(early)` from the table cells with the stated parser (strip thousands separators, treat parentheses as negative), compute `delta_source = value(late) - value(early)`, then convert by the scale factor between `source_unit` and the requested target unit. The checker must never read the actor's output before the gold exists.

**Scoring (per item, per arm, per repeat):**
| Outcome | Rule |
|---|---|
| `correct` | `delta_source` and `delta_target` both match gold exactly (after the declared rounding); row and periods match |
| `correct_other_form` | same value via a mathematically equivalent expression (e.g., early-minus-late with a negated sign) - counted as correct, and recorded separately |
| `wrong_unit` | `delta_source` correct but `delta_target` wrong |
| `wrong_period` | the periods chosen differ from the item's |
| `regressed` | compared to arm B on the same item, a previously correct answer becomes incorrect |
| `refused` | the literal `REFUSED` |
| `unknown` | the literal `UNKNOWN`, a timeout, or an unparseable answer |

**Independent unit of analysis:** the origin (the raw record), not the item, not the repeat. Report per-origin paired differences `E-B`, `E-C`, `E-S`, `C-B`, with the origin-level differences listed explicitly.

**Anti-leakage obligations the checker must enforce:** (a) the item's gold appears nowhere in the actor-visible projection; (b) no item shares an origin with any experience episode used in the same arm run; (c) the C-arm context differs from the E-arm context by at most 5% in context tokens; (d) the S-arm rules are frozen at development time and never edited per item.

## 3. Fixture obligations (what Loop A must demonstrate without any model)

On synthetic fixtures only, Loop A must show:
1. the adapter emits the same prompt twice for the same item (byte equality);
2. the gold never appears in the projection (string search);
3. the checker's recomputation matches hand-computed values on at least 5 hand-built fixtures, including one with parentheses-negative cells and one with a thousands separator;
4. the scale conversion matches for thousand->unit, million->thousand, billion->million and percent->percent;
5. an `UNKNOWN` and a `REFUSED` answer are classified correctly;
6. the arm-context token delta between E and C is computed and reported.

**Stop:** if any fixture obligation cannot be met, WP-1 stops and reports `SOFTWARE_NOT_QUALIFIED`. No model is called to "try it out".

## 4. Revision 1.1 (2026-10-13): hidden-gold search clarified

**Trigger:** WP-1 run 1 (`tatqa-wp1-20261013`) stopped fail-closed with `SOFTWARE_NOT_QUALIFIED: hidden_gold_search`. Diagnosis: the check searched `late_value` and `early_value` (fields of the `expected_gold` object) inside the projection. Those are raw table cells that the actor must read to compute the delta, so the search necessarily hits the table itself - a false-positive class, not a leak. The fail-closed stop was correct behaviour; the check definition, as written, was over-broad and undecidable.

**Revision (supersedes Sec.3 obligation 2 only; every other obligation is unchanged):**

(a) Forbidden-name search: none of the hidden field names (`gold_delta_source_unit`, `gold_recompute_rule`, `gold_delta_target_unit`, `expected_gold`, `origin_id`, `item_id`) appears in the projection.
(b) Answer-value search: the derived answer strings - `delta_source` and `delta_target` exactly as the checker renders them (for example `60`, `-55`, `1.3`, `1300`) - have ZERO boundary-aware matches in the full serialized projection. A match counts only when flanked on both sides by characters outside the set {digits, `.`, `,`, `+`, `-`} (string start/end count as a boundary). No length filter; applies to EVERY fixture.
(c) `late_value` and `early_value` are excluded from the search set: they are actor-visible task inputs by design, not gold.
(d) Fixture-design precondition (makes (b) informative rather than vacuous): for every fixture, the same boundary-aware search over the raw table cells and period labels alone must also find zero matches; if a collision exists, the fixture's synthetic numbers must be adjusted (keeping the arithmetic correct) - never the check.

**Change control:** this revision does not weaken (a)-(d); it makes the search well-defined and extends its scope to all fixtures. Any further failure of this obligation after this revision is a genuine finding.

## 5. Revision 1.2 (2026-10-13): leak-guard canonicalization + taxonomy/receipt precision

**Trigger:** Loop C WP-1 audit (`tatqa-wp1-audit-20261013`, CONDITIONAL) found: (i) the hidden-gold needle rendered `1300.0` where 1.1(b) names `1300` (latent false-negative, positive-control proven); (ii) the emitted outcome vocabulary (`wrong`) is a superset of the declared taxonomy, and `regressed` excludes refused/unknown; (iii) safety booleans are recorded as literal self-attestation rather than derived evidence; (iv) `FIXTURE_RECEIPT` has no integrity pin and its canonical path needs stating; (v) `target_unit` is absent from all 60 frozen candidates (identity conversions only) and `gold_delta_source_unit` is a naming trap - both to be resolved at prereg/item-freeze.

**Revision (supersedes 1.1(b),(d); extends the taxonomy; nothing is weakened):**

(a) **Chosen form.** The answer-value needle is the canonical plain-decimal form of `delta_source` and `delta_target`: no trailing zeros, no exponent (for example `60`, `-55`, `1.3`, `3`, `1300`). Where the exact `str(value)` render differs (for example `1300.0`), BOTH forms are searched.
(b) **Positive control (mandatory).** The check must include a self-test that injects each needle into a synthetic projection and asserts the guard fires; a guard that cannot catch its own injected leak fails the obligation. At minimum cover the `1300`/`1300.0` pair and one negative value.
(c) **Coverage.** The byte-determinism obligation applies to EVERY fixture and ALL four arms (B/E/C/S), not one item and one arm.
(d) **Outcome vocabulary (eight classes).** `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong` (answered and parseable, neither correct nor a specific wrong_* class), `regressed`, `refused`, `unknown`. `regressed` is assigned by the B-vs-arm comparison when a B-correct outcome becomes non-correct other than `refused`/`unknown`; refusals and unknowns remain first-class.
(e) **Receipts.** Every safety boolean is either derived from executed behaviour or explicitly labelled `attested: true`; `scoring_inputs_all_synthetic` must be derived. `WP1_RECEIPT.artifact_hashes` must include the `FIXTURE_RECEIPT` hash. The canonical `FIXTURE_RECEIPT` path is `data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json`; the copy under `research/tatqa_wp0_2026/wp1/` is a byte-identical mirror for tracking.
(f) **Known traps recorded for the prereg.** `gold_delta_source_unit` stores a delta VALUE in source units (the name is not a unit string); `target_unit` is absent from the frozen candidate items, so every conversion is currently the identity - a target-unit assignment decision is PENDING at item freeze.