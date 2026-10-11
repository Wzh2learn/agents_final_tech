# PR-EXP-08 Qualification v1 (read-only fact-check)

> date: 2026-10-11 | verdict: KEEP_BACKUP | qualification subagent: qual_pr08 (read-only; 3 incidental read-only ssh status checks disclosed; zero writes/model calls)

## Question
Do the current parse/QA missing defaults conflate MISSING / FAIL / NEUTRAL into one numeric state, and does this conflation affect real held-out coverage / diagnosability / aggregation? Could a tri-state repair qualify as INTERVENTION_REPAIR?

## Findings (FACT)
- Config: all 5 parse leaves `missing_score: 0`; all 7 qa leaves `5` (config/eval_checkpoint_trees.json).
- Absence semantics are SHAPE-DEPENDENT (executed the pure functions in-memory):
  - whole artifact missing -> leaf = missing_score (0 parse / 5 qa) + degraded + rc=1 (only shape whose trace is emitted).
  - contract type absent inside a present artifact -> rate 1.0 -> leaf 10.0 (FULL MARKS, including hinge routes); trace hidden.
  - NF results empty -> 1.0 -> 10.0; trace hidden.
  - judge dim key absent -> 0.0; trace hidden.
  - judge dim present but avg=null/n=0 (F-J1) -> 5.0 + degraded (reason recorded but not serialized).
- Conflation CONFIRMED and broader than filed: parse missing = FAIL = 0; qa missing = midpoint 5; un-filed sharper edge = absent contract/NF = FULL MARKS 10.0 on hinges; judge absence splits {0.0 / 5.0} by shape; per-leaf degraded traces are computed but never serialized (only scores leave the report).
- Frozen-surface scan: ZERO natural no-evidence cells anywhere (multileaf 216/216 complete, 0 nulls; cdt_v2/t1/t2/d3/DISC complete; M8 engineered file-missing already detected by current code). The 08-25 all-None judge artifact is not preserved.
- E1.3 20/95 = an exclusion caliber (2 N/A leaves excluded by design), not a missing_score case.

## Inference
- The conflation is real but LATENT on existing frozen surfaces: a tri-state repair cannot change any reported number/decision on existing held-out data; measurable flips require NEW absence panels (new populations).
- Same-budget comparison is mechanically feasible, but its measured delta on existing surfaces = 0 by construction.

## Verdict: KEEP_BACKUP
- Upgrade bar ("real held-out coverage / diagnosability impact") NOT met -> PR-EXP-08 remains backup / instrumentation hygiene; NOT added to first wave; never counts toward the synthesis gate.
- Recommended (separate authorization, future): fold the two latent defects into an aggregation-report revision — (1) absent-contract/NF -> full-marks on hinges; (2) hidden per-leaf traces.
- Revisit condition (owner's call): if engineered absence panels on held-out folds are elected as the population, re-qualify.