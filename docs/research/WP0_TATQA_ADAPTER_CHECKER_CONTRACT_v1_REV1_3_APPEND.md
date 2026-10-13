# WP-0 TAT-QA Adapter and Checker Contract v1 — Revision 1.3 Append

> date: 2026-10-13 | task: `tatqa-wp2-prefreeze-20261013` | status: `APPEND_ONLY_REVISION`
> base: [`WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md`](WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md) revisions 1.1-1.2, base SHA-256 `681c6f33c566d6e7efd50d1727072271c48f3a676dc18f746826de6483fc778f`
> control rule: the historical base file, WP-1 run-3 receipts, and run logs remain unchanged. This append is the rev 1.3 correction record under the task card's append-only constraint.

## 1. Revision 1.3 trigger

The WP-1 completion record filed two pre-freeze residuals:

1. `correct_other_form` accepted mathematically equivalent values without requiring the normalized answer unit to equal `gold.target_unit`, while `correct` required the unit conjunct;
2. the leak guard enumerated canonical and exact string forms but not alternate numeric renderings such as `1,300`, `1.3e3`, or `001300`.

## 2. Correct-class unit conjunction

This revision supersedes the scoring rows for `correct` and `correct_other_form` in Sec.2 of the base contract. Every other base and rev 1.2 rule remains unchanged.

- `correct`: row and periods match; `delta_source` and `delta_target` match gold; and `normalize_unit(answer.unit) == gold.target_unit`.
- `correct_other_form`: the periods express the equivalent early-minus-late form; both deltas are the exact negated gold values; and `normalize_unit(answer.unit) == gold.target_unit`.
- A reversed-period equivalent form with the correct deltas but an incorrect normalized unit is `wrong_unit`, not `correct_other_form`.
- `wrong_unit` remains available when source-unit arithmetic is correct but target-unit arithmetic or the normalized target-unit label is wrong.

The change is monotone: previously accepted correct-class cases remain correct only when their unit label also matches. No existing rejection is relaxed.

## 3. Alternate numeric-rendering needles

This revision supersedes only the finite list of rendered forms in Sec.5(a) of the rev 1.2 base contract. The boundary definition and the raw-table collision precondition remain unchanged. For each finite golden answer value, the guard searches all distinct forms generated from:

- the canonical plain decimal;
- Python's exact `Decimal` string form;
- the exact fixture string where supplied;
- comma-grouped integer rendering where applicable;
- normalized scientific notation where applicable;
- zero-padded signed integer rendering where applicable.

Positive controls must inject and catch at least the comma-grouped, scientific, zero-padded, and negative grouped/scientific variants. Adding needles can only increase guard sensitivity; it never excuses a fixture collision or weakens a prior check.

## 4. Implementation evidence

The append-only implementation is:

- `research/tatqa_wp0_2026/wp1/checker_v2.py`
- `research/tatqa_wp0_2026/wp1/leak_guard_v2.py`
- `research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py`
- `research/tatqa_wp0_2026/wp1/fixtures/s0_unit_gate_fixtures_v2.json`
- `research/tatqa_wp0_2026/wp1/fixtures/s0_numeric_rendering_fixtures_v2.json`

Executed evidence is pinned in `research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json`. The canonical evaluation protocol remains authoritative for the definition that correctness includes both unit and period.
