# WP-1 Pre-Freeze Fix Note v1

> date: 2026-10-13 | task: `tatqa-wp2-prefreeze-20261013` | status: `PASS / APPEND_ONLY_REVISION`
> protocol: zero model calls, zero judge calls, zero training, zero external network.

## 1. Trigger and policy

WP-1 completion-record residuals were resolved upward, as authorized: correctness now includes the target-unit conjunct for every correct-class result, and leak-guard needles include alternate finite numeric renderings. The historical WP-1 runner, run-3 receipts, and run logs were not modified.

Because the task card requires append-only new files and frozen receipts must remain byte-stable, rev 1.3 is recorded in `WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1_REV1_3_APPEND.md`. The evaluation protocol is unchanged because it already defines correctness as including unit and period.

## 2. Changes

1. `checker_v2.py` makes the equivalent-expression path require the normalized target unit.
2. `leak_guard_v2.py` adds grouped, scientific, exact-decimal, and zero-padded needle forms where applicable.
3. Dedicated synthetic fixtures cover equivalent-form unit mismatches and alternate numeric renderings.
4. `s0_run_fixtures_v2.py` executes every existing fixture obligation with v2 scoring and v2 needles, then runs the dedicated cases. It does not write historical receipts.

## 3. Verification

Command:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py
```

Output:

```text
S0_FIXTURES_PASS obligations=7 unit_gate_cases=3 numeric_rendering_cases=5
receipt=research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json
```

The receipt records all seven obligations as PASS, outcome-taxonomy and regression-helper checks as PASS, metric-pipeline PASS, and cost `model_calls=0 / endpoint_calls=0 / judge_calls=0`.

## 4. Preservation evidence

The S0 receipt pins the before/after artifact set. Historical run-3 code, receipts, and the run-3 log retain their pre-task SHA-256 values. The v2 implementation is additive and imports the frozen v1 modules read-only.

## 5. What remains pending

- `target_unit` assignment is only a draft in `WP2_TARGET_UNIT_RULES_DRAFT_v1.md`;
- candidate v2 and split rerun remain `DRAFT_NOT_FROZEN`;
- no actor, experience episode, model setting, pilot result, or scientific conclusion is frozen or verified by this note.
