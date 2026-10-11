ROLE: Loop A / GB10 execution authorization
RESEARCH QUESTION:
Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

USER AUTHORIZATION:
The user explicitly approved execution of `research/finqa_v2_20261010/preflight_v1/FINQA_V2_FORMAL_RERUN_V3_TASK_CARD.md` in the current turn. This dispatch note only activates that frozen task card; it does not modify it.

INPUTS:
- `research/finqa_v2_20261010/preflight_v1/FINQA_V2_FORMAL_RERUN_V3_TASK_CARD.md`
- `research/finqa_v2_20261010/preflight_v1/finqa_v2_end_to_end_preflight_manifest.json`
- `research/finqa_v2_20261010/preflight_v1/finqa_v2_end_to_end_preflight_certificate.json`
- authorities hash-bound in `docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md`

ALLOWED ACTIONS:
Execute exactly the frozen task-card steps:
1. re-run the preflight checker and require PASS;
2. verify all authority and prior-run hashes;
3. run the unchanged scorer through binding-v3 on exactly 89 evaluation pairs;
4. materialize frozen V/D/O rows;
5. compute only frozen estimands and E/P/N profiles;
6. run only 10,000 report-cluster bootstrap replicates at seed 20261017;
7. write immutable outputs under `research/finqa_v2_20261010/results_binding_v3_rerun/`;
8. stop for Loop C independent recomputation.

FORBIDDEN ACTIONS:
- Modify the task card, preflight, authority map, analysis plan, sample IDs, split, join, scorer, thresholds or metrics.
- Add or remove samples, cases, estimands or tests after results.
- Start PRM, Stage D, model training, model/API/database calls.
- Overwrite prior invalid runs.
- Modify Paper E or paper text.

OUTPUTS:
- scorer rows with raw/normalized hashes;
- V/D/O rows;
- frozen primary/secondary estimands;
- E/P/N profiles with frozen bootstrap CIs;
- exact exclusions/failure accounting;
- immutable result receipt and logs.

STOP CONDITIONS:
- preflight checker is not PASS;
- any frozen hash mismatch;
- any scorer failure or missing retained record;
- any contract mismatch or scientific output path collision;
- any request to alter frozen definitions.

EVIDENCE CLASS:
CONFIRMATORY / SECONDARY / NEGATIVE according to the frozen analysis plan; result class remains for Loop D after Loop C.
