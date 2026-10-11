# Loop C Independent Audit: Stage E Method Revision and Stage D Reference Tracks

You are an independent read-only Loop C auditor. Do not modify files, run training, or use model/judge/production endpoints.

Audit the following packet:

- the twelve new Markdown deliverables under `docs/research/`;
- `research/stage_e_method_revision_20261009/stage_e_method_revision_receipt.json`;
- `matched_fpr_reanalysis.json`;
- `multileaf_power_analysis.json`;
- `prm_reference_smoke.json`;
- the three producing scripts;
- NIST/Math-Shepherd/PRM800K source files under `/home/testuser/wzh/research_stage_e_method_revision_20261009/sources/`;
- official PRM800K repository at `/home/testuser/wzh/external_stage_d_repro/repos/prm800k`.

Verify:

1. PRIMARY/SECONDARY/DIAGNOSTIC/FUTURE metrics are internally consistent;
2. semantic HBR is not claimed and operational H/HI/E limits are preserved;
3. OCR uncertainty separates injection and cluster-event estimands;
4. clean-only matched-FPR analysis does not use harmful outcomes for threshold selection and records the correct blocker;
5. structural affine/rank/ROC equivalence is separated from empirical matched-FPR equality;
6. NIST passages are exact and do not overclaim evaluator blind spots;
7. multi-leaf Stage M/R/N contracts fix expected first stage before results and define at least three stages;
8. power assumptions are labelled design assumptions and cluster units are not inflated;
9. PRM800K smoke is not training, distinguishes full grader from normalization subset, and preserves licence limits;
10. Math-Shepherd official repo/data status remains UNVERIFIED;
11. ToolAlpaca is only Tool Contract Validity;
12. no frozen artifact, claim manifest, harmfulness label or old D3 result is modified;
13. full pytest, docs lint, link/hash and protected-path evidence are current.

Return exactly one JSON object and no Markdown fence:

{
  "verdict": "PASS | CONDITIONAL | FAIL",
  "facts": [],
  "inferences": [],
  "values": [],
  "unverified": [],
  "redlines": [],
  "conditions": [],
  "forbidden_action_check": {},
  "status": "EXT_D_REPRO_METHOD_REVIEW_READY | EXT_D_REPRO_METHOD_BLOCKED"
}
