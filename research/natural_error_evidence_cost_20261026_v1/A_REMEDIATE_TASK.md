# Loop A Task: Correct Natural-Error Evidence And Publish P2 Recompute

Task ID: `natural-error-cost-remediate-a-20261026`

Goal ID: `NATURAL_ERROR_EVIDENCE_COST_20261026`

Role: A-EXP. File ownership:
`research/natural_error_evidence_cost_20261026_v1/a_remediate/`.

Bind to commit `622b386986ca66c8119263e146f3d3e73c33e260` and the current
research prompt. Zero scientific generation, zero training, zero judge and
zero production calls. Preserve `a_prepare/` as the prior version and do not
modify frozen raw or prior reports.

## Required Corrections

### P1

Implement C findings F1-F3:

- Reclassify `NAT_train_b7814ec0_7b6669a8` as a reference/scoring defect,
  not a natural model error. The gold direction conflicts with the dominant
  later-minus-earlier convention and with identically phrased controls.
- Recompute the natural error count as 4 genuine model semantic errors plus
  1 reference defect. Report both denominators explicitly.
- Publish one frozen, deployable, gold-free simple rule policy and replay it.
  Report `4/5` overall and `4/4` on genuine model errors; do not use per-case
  recipes that cannot be expressed as one visible policy.
- Align probe scoring with the frozen scorer or explicitly define and justify
  separate metrics. Do not call exact program identity the frozen numeric
  metric.

### P2

Implement C findings F4-F5:

- Publish the exact executable recovery/ranking program and serialization:
  source-requirement classification, scale-source resolution, TF-IDF ranking,
  paragraph indexing, neighbor construction, stop rule, semantic-potential
  calculation and character-volume accounting.
- Use no gold answer, gold paragraph ID or hidden scale to choose a deployable
  action. Gold/reference material may be used only for offline scoring.
- Re-run all 507 table-text questions from the pinned TAT-QA dev source and
  emit row-level results, hashes and aggregate frontiers.
- Freeze the full-semantic answer matching rule before any future generation:
  numeric tolerance, span/multi-span normalization, count handling and
  reasonable UNKNOWN.
- Freeze a pre-registration receipt containing the -2.0 percentage-point
  non-inferiority margin, 75%/50% context budgets, candidate selection rule
  and paired analysis unit.
- Re-evaluate whether any restricted frontier satisfies both margin and
  budget. If none does, preserve `NO_GO`; if one does, identify it as a
  diagnostic candidate only, not a method result.

## Required Outputs

- `a_remediate/A_REMEDIATION_RESULT.json`
- `a_remediate/NATURAL_ERROR_DIAGNOSIS_CORRECTED.jsonl`
- `a_remediate/P1_SEMANTIC_LEDGER_CORRECTED.json`
- `a_remediate/P2_RECOVERY_RECOMPUTE.py`
- `a_remediate/P2_RECOVERY_RECOMPUTE.json`
- `a_remediate/P2_TASK_QUALIFICATION_CORRECTED.json`
- `a_remediate/STRONG_BASELINE_FRONTIERS_CORRECTED.json`
- `a_remediate/P2_ANSWER_MATCHING_RULE.json`
- `a_remediate/P2_PREREG_RECEIPT.json`
- `a_remediate/EXPOSURE_REGISTER_CORRECTED.json`
- `a_remediate/P2_PROBE_CONTRACT_DRAFT_CORRECTED.json`

Final response must be compact JSON and must not authorize a model probe.
