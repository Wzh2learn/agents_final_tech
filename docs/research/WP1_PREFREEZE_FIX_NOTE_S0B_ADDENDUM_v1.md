# WP-1 Pre-Freeze Fix Note — S0b Addendum v1

> date: 2026-10-13 | task: `tatqa-wp2-s0b-20261013` | status: `PASS`
> boundary: closes Loop C round-1 F-2/F-3/F-4/F-8 only; no model, endpoint, judge, training, network, or S4+ action.

## 1. Why this is a separate S0b document

The original `WP1_PREFREEZE_FIX_NOTE_v1.md` and `S0_FIX_RECEIPT.json` are historical v1 artifacts. A separate S0b addendum preserves both byte-for-byte while keeping the Loop C closure auditable. Exact before/after hashes and the complete rerun payload are recorded in `S0B_FIX_RECEIPT.json`; the addendum itself is also hashed in that receipt.

## 2. Minimal changes

1. F-2/F-3: `checker_v2.py` now returns `wrong_unit` on the direct form when source delta, target delta, and period are correct but the normalized answer-unit label differs from `gold.target_unit`. The equivalent-form behavior is unchanged. No existing outcome can flip from not-correct to correct because this branch still returns a non-correct class.
2. F-4: `s0_run_fixtures_v2.py` emits each `preservation_check` boolean through the repository's existing `_safety_claim` contract: `{basis, evidence, value}`. The underlying preservation facts are unchanged.
3. F-8: protocol §5 now includes `wrong`, aligning its eight-class list with `OUTCOME_CLASSES` in the implementation.

## 3. Dedicated regression evidence

The new `fixtures/s0b_direct_form_fixtures_v2.json` fixture has the exact reported shape: direct periods, correct source and target deltas, correct scale conversion, and an incorrect unit label. Before the fix it produced `wrong`; after the fix it must produce `wrong_unit`.

Command:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py
```

Output:

```text
S0_FIXTURES_PASS obligations=7 unit_gate_cases=3 direct_form_cases=1 numeric_rendering_cases=5
receipt=research/tatqa_wp0_2026/wp1/S0B_FIX_RECEIPT.json
```

The runner executes all seven existing obligations, the original three unit-gate cases, the new direct-form case, the five numeric-rendering cases, and a protocol/implementation taxonomy-alignment check. It writes only the new S0b receipt and refuses to proceed if the original S0 receipt hash changes.

## 4. Deliberately unchanged

- F-5 remains an owner/advisor decision. This addendum does not change `normalize_unit`, `UNIT_ALIASES`, source-unit null/currency semantics, candidate items, or any target-unit scientific rule.
- Historical WP-1 code, receipts, run logs, and `S0_FIX_RECEIPT.json` remain unchanged.
- No S4+ step, actor selection, experience construction, pilot, model call, judge call, training, or external network action occurred.
