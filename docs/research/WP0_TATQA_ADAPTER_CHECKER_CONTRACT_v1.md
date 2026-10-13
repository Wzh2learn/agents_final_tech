# WP-0 TAT-QA Adapter and Checker Contracts v1

> date: 2026-10-13 | author: Loop D (WP-0 item A5) | status: `SPECIFICATION_ONLY - NOT IMPLEMENTED`
> parents: [WP0_TATQA_PACKAGE_v1.md](WP0_TATQA_PACKAGE_v1.md), [task card](thesis_experience_v1_task_card.md), [blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md) §2
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