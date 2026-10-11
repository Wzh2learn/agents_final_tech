# Task Contract: Certify End-to-End Preflight - Loop C

- Task ID: `finqa-v2-end-to-end-preflight-c-20261010`
- Role: Loop C / GB10 independent certification
- Window: zero-endpoint, non-training, zero scientific output
- Scope: certify the existing preflight certificate only

## Objective

Independently determine whether `END_TO_END_PREFLIGHT_PASS` is valid and whether `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN` may be set to YES.

## Required Independent Checks

1. Recompute all authority paths and SHA-256 values in the materialized authority map.
2. Run `scripts/graph/formal_experiment_preflight.py` against the frozen preflight manifest.
3. Independently run positive controls for:
   - empty hash bindings;
   - empty scientific-output scan;
   - empty previous-run set;
   - empty/incomplete population;
   - empty qualification expectations;
   - missing authority file;
   - non-empty metadata fallback;
   - keyword default;
   - or-fallback;
   - setdefault fallback;
   - missing/null/empty required metadata;
   - existing scientific output.
4. Verify the full zero-output chain stops before V/D/O.
5. Independently verify `89/89` runtime bindings, `420/420` traces, `30/30` groups.
6. Verify zero silent defaults, missing metadata, identity drift, split drift, leakage and scientific outputs.
7. Verify both previous INVALID runs are byte-identical.
8. Verify the certificate's counts and hashes are not self-attested only.

## Output

Return the complete report in the task log. Required fields:

- corruption-control results;
- authority-map materialization verdict;
- exact counts;
- `END_TO_END_PREFLIGHT_PASS = PASS|FAIL`;
- `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = YES|NO`;
- `VERDICT: PASS|CONDITIONAL|FAIL`;
- one blocker if not PASS.

## Forbidden Actions

- Modify checker, certificate, authority map or any artifact.
- Run formal scorer, V/D/O, estimands, bootstrap, PRM or training.
- Add governance layers or new metrics.

## Success Exit

All corruption controls fail closed, all counts match, the certificate is independently reproducible and `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = YES`.
