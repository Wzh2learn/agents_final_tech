# CONDITION_CHANGE_LOOP_A Return

Task: `condition_change_feedback_v1`

Evidence identity: `DEV_ONLY_CONTROLLED_MECHANISM`.

## Ruling

`PASS_LOCAL_DETERMINISTIC_V2_FIX_QUALIFICATION`; `STOP_BEFORE_REAL_MODEL`.
All V1 frozen inputs/results remain byte-for-byte unchanged, and no model,
judge, training, network, service, or production Memory request was sent.

## Bounded Revision

- Added actor-visible applicable policy text and explicit delta text keyed by
  `policy_version_id`, while excluding decisions, sufficient sets, reference
  facts, and adjudication fields.
- Recut the scope probe into a single-factor extra/clean pair with identical
  derived outcomes and minimal-set sufficiency; the frozen clean fixture
  differs by exactly one out-of-scope fact.
- Appended `CC013` with an invariant decision but changed minimal sufficient
  set; both stage references derive from `reference_builder_v2`.
- Separated independent diagnostic codes for answer mismatch, insufficient
  plan, scope impurity, and in-scope over-selection from contract reason codes.
- Replaced binary-float precision averaging with integer/Fraction aggregation
  and a 12-place deterministic fixed-decimal string.
- Stabilized package provenance at `task_id=condition_change_feedback_v1`;
  launcher IDs exist only in the V2 run manifest.

## Results

- Population: 13 paired cases, 26 actor tasks, 40 facts, 5 source clusters.
- Condition change: 3 decision flips, 10 invariant pairs, and 1 invariant
  pair with a changed minimal sufficient set.
- Composite dispositions: alternate `RETAIN`; out-of-scope extra `REVISE`;
  clean counterfactual `RETAIN`.
- `plan_precision_mean`: `0.948717948718` for pre, post, and overall
  (`37/39`), stored as a deterministic fixed-decimal string.
- Deterministic headroom: 14/26 composite rejections; rejection rate
  `0.538461538462`.

## Verification

Exact commands, run from `condition_change_feedback_v1/`:

```text
python3 -B build_condition_change_inputs.py --freeze
python3 -B run_feedback_probe.py --freeze
python3 -B run_feedback_probe.py --run
python3 -B -m unittest -v test_condition_change.py
python3 -B verify_condition_change.py
```

- Runtime: CPython `3.12.3` at `/usr/bin/python3`.
- Focused tests: 15 passed, 0 failed, 0 skipped.
- Machine verification: `PASS`, 0 verification errors.
- V2 probe SHA-256:
  `8d4b4293bef221a41bd1c0f35782de0080cf9163d1e14245d9f456c0ad2a5089`.
- V2 actor SHA-256:
  `02d16e44801ee091392f4b1e551f25b3f79ef7e404178149ae21ad7cea2ec7f1`.
- V2 reference SHA-256:
  `74a98f87a597bda53a2db923992c4ffe9a0ab96d4c009578a574a7766af4015e`.
- V2 fixture SHA-256:
  `b8b60700c595d97938baf74a9cb81b549913500a772e5350d488efbd8b13ec53`.
- V2 machine receipt SHA-256:
  `6f110f20b555b81b097454c5e48836744df283cbeb8e9076c789538c47ef96f9`.
- Preserved V1 probe SHA-256:
  `13c14b5a2a06d0e91aa8640b012bfb4c5b39f116df5df25c07194ff1d94670c4`.
- Preserved V1 machine receipt SHA-256:
  `e9ba595d6200efcf4c41dc12741827ac285bd0a1a3916220a421d863d89e585b`.
- Zero-request accounting: all six counters are `0`.

## Remaining Blockers

1. CPython 3.11 is unavailable in this runtime, so literal 3.11 execution was
   not run; compatibility is enforced by rational/fixed-decimal aggregation.
2. The sprint stop rule still forbids starting a real-model phase.

The package-local receipt is
`condition_change_feedback_v1/MACHINE_VERIFICATION_V2.json`. Existing
`GB10_LOOP_A_RETURN.md` and `GB10_LOOP_A_VERIFICATION.json` were not written.
