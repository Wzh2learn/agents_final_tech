ROLE: Loop C / GB10 fresh-context independent recomputation
RESEARCH QUESTION:
Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

INPUTS:
- `research/finqa_v2_20261010/results_binding_v3_rerun/`
- frozen analysis plan and manifests
- binding-v3 runtime contract and trace map
- unchanged independent scorer source
- authority map and preflight certificate

ALLOWED ACTIONS:
1. Independently recompute scorer success/failure counts and V/D/O rows from frozen sample rows.
2. Recompute primary visibility/detection counts and rates.
3. Recompute the VxD 2x2 counts/rates.
4. Recompute `P(D=1|V=1)` and `P(D=1|V=0)` with frozen zero-denominator handling.
5. Recompute E/P/N profiles.
6. Independently re-run the frozen 10,000 report-cluster bootstrap at seed 20261017 and compare all intervals/valid/failed counts.
7. Verify 89 samples / 30 groups, exact denominators, no leakage, no exclusions after split and no threshold/metric changes.
8. Verify raw/normalized binding hashes and prior-run immutability.
9. Audit the allowed/forbidden claim boundary.

FORBIDDEN ACTIONS:
- Modify A outputs or any frozen artifact.
- Run a replacement formal experiment.
- Change metrics, thresholds, split, scorer or bootstrap.
- Start PRM/Stage D or modify Paper E.

OUTPUT:
Return a fresh-context report in the task log with:
- exact A/C comparison;
- `PASS`, `CONDITIONAL`, or `FAIL`;
- recommended `SECOND_FLOW_POSITIVE/MIXED/NULL/INVALID`;
- scientific reason;
- strongest positive and negative/boundary findings;
- any single blocker if not PASS.

STOP CONDITIONS:
- any A/C count or bootstrap mismatch;
- any denominator manipulation;
- any leakage or frozen-hash drift;
- any scorer/binding failure.

SUCCESS EXIT:
All primary and secondary recomputations match A, claim boundaries are valid, and the scientific class is supportable.
