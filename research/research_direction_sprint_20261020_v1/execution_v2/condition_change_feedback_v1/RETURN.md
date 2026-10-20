# CONDITION_CHANGE_FEEDBACK_V1 Return

Task: `condition_change_feedback_v1`

Evidence identity: `DEV_ONLY_CONTROLLED_MECHANISM`.

## Disposition

`PASS_LOCAL_DETERMINISTIC_V2_FIX_QUALIFICATION`; stop before any real-model
phase. The bounded revision preserves every V1 frozen input/result and changes
only actor policy visibility, paired-case/reference coverage, probe fixtures,
diagnostic reason-code separation, fixed-decimal aggregation, and package
provenance. It does not establish learning, public generalization, or human
gold.

## Exact Changes

1. Actor V2 input now includes `policy_context` with the applicable policy
   text and explicit delta text for each `policy_version_id`; gold decisions,
   sufficient sets, reference facts, and adjudication fields remain excluded.
2. The out-of-scope probe is now a single-factor pair: both selections satisfy
   a minimal set and submit the derived outcome, while the extra fixture adds
   exactly one out-of-scope fact. The frozen counterfactual removes only that
   fact.
3. `CC013` is appended without changing any of the 12 V1 cases. Its decision
   is invariant across the policy delta while its minimal sufficient set
   changes; both stages are derived by `reference_builder_v2`.
4. Feedback results independently report `ANSWER_MISMATCH`,
   `INSUFFICIENT_PLAN`, `SCOPE_IMURITY`, and `IN_SCOPE_OVER_SELECTION` through
   `reason_codes`; contract-specific outcomes use `contract_reason_code`.
5. `plan_precision_mean` uses integer/Fraction aggregation and a deterministic
   12-place fixed-decimal string, avoiding binary-float mean drift.
6. All V2 package provenance uses `task_id=condition_change_feedback_v1`;
   launcher IDs appear only in `PROBE_RUN_MANIFEST_V2.json`.

## Frozen Population

- 13 paired pre/post cases, 26 actor tasks, and 40 evidence facts.
- 5 source clusters: conference, meals, travel, office, and lodging.
- 3 decision flips and 10 invariant pairs.
- 1 invariant-decision pair whose minimal sufficient set changes.
- 4 reference tasks with naturally derived alternative sufficient sets.
- 2 distinct out-of-scope fact IDs.

The reference builder derives decisions and Cartesian-minimal sufficient sets
from the V2 declarative policy and evidence-fact records only. It does not read
actor plans, model output, or hand-coded per-case answers.

## Contract Dispositions

| Probe | Exact match | Sufficiency only | Composite |
|---|---|---|---|
| Valid alternate sufficient set | REVISE | RETAIN | RETAIN |
| Single-factor out-of-scope addition | REVISE | RETAIN | REVISE |
| Frozen clean counterfactual | RETAIN | RETAIN | RETAIN |

The added fact is the only `SCOPE_IMURITY` reason in the scope pair. The
composite retains the clean selection and revises only the extra-fact
selection because its scope precision is below `1.0`.

## Deterministic Baseline

| Stage | Plan sufficiency | Plan precision | Answer coverage | Composite acceptance |
|---|---:|---:|---:|---:|
| Pre-change | 12/13 | 37/39 = `0.948717948718` | 10/13 | 7/13 |
| Post-change | 11/13 | 37/39 = `0.948717948718` | 7/13 | 5/13 |
| Overall | 23/26 | 37/39 = `0.948717948718` | 17/26 | 12/26 |

Headroom is 14/26 composite rejections, a rejection rate of
`0.538461538462`. Every stage metric remains strictly between zero and one.

## Verification

Exact commands, run from this directory:

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
- Frozen/recomputed V2 probe SHA-256:
  `8d4b4293bef221a41bd1c0f35782de0080cf9163d1e14245d9f456c0ad2a5089`.
- V2 actor SHA-256:
  `02d16e44801ee091392f4b1e551f25b3f79ef7e404178149ae21ad7cea2ec7f1`.
- V2 reference SHA-256:
  `74a98f87a597bda53a2db923992c4ffe9a0ab96d4c009578a574a7766af4015e`.
- V2 fixture SHA-256:
  `b8b60700c595d97938baf74a9cb81b549913500a772e5350d488efbd8b13ec53`.
- V2 input-manifest SHA-256:
  `9600521871bf2b9a32efda4065a46412ac6a67011876317075221729102c03a6`.
- V2 machine receipt SHA-256:
  `6f110f20b555b81b097454c5e48836744df283cbeb8e9076c789538c47ef96f9`.
- Preserved V1 probe SHA-256:
  `13c14b5a2a06d0e91aa8640b012bfb4c5b39f116df5df25c07194ff1d94670c4`.
- Preserved V1 actor SHA-256:
  `5eed6e6d19fd540cf292eb15abe4a5baa937bac8fdd6d3ab4f9328a73d773104`.
- Preserved V1 reference SHA-256:
  `98c253cc298adf18bd056b5434ef8476b2207b06198370101970ce45365aab37`.
- Preserved V1 fixture SHA-256:
  `ab7f0e72407534cf6933b962325d2b8bb59b7181d4cf090e0c4699140296eda0`.
- Preserved V1 machine receipt SHA-256:
  `e9ba595d6200efcf4c41dc12741827ac285bd0a1a3916220a421d863d89e585b`.
- Model requests: 0.
- Judge calls: 0.
- Training calls: 0.
- Network requests: 0.
- Service requests: 0.
- Production Memory writes: 0.

## Stop Recommendation

`STOP_BEFORE_REAL_MODEL`. The contract separates the intended failure modes
and retains nonzero deterministic headroom, but the sprint stop rule still
forbids automatically starting a real-model phase.

Remaining blocker: no CPython 3.11 executable is installed in this runtime, so
the cross-version claim is implemented with integer/Fraction aggregation and
fixed-decimal formatting but was executed only on CPython 3.12.3.

The execution-root reports are `CONDITION_CHANGE_LOOP_A_RETURN.md` and
`CONDITION_CHANGE_LOOP_A_VERIFICATION.json`. Existing `GB10_LOOP_A_*`
artifacts were not written.
