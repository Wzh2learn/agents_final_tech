# V3 Audit Correction Return

Date: 2026-10-24, Asia/Shanghai

## Audit Findings

1. **Source-cluster overlap confirmed.** The historical confirmation panels
   contained 5/24 and 3/24 table-UID overlaps with the 512-task training set.
   This is a source isolation defect, not duplicate questions. The old panels
   remain preserved as historical evidence and post-hoc sensitivity only.
2. **Constant/reference defect confirmed.** At least one reference program
   divided by an unrelated numeric cell whose value happened to be `2`.
   Numeric equality did not establish evidence identity.
3. **Visible-filter interpretation narrowed.** Its candidate pool was built
   from reference programs and synthetic corruptions; only 253/512 selected
   targets passed the old numeric reference check. The negative result stops
   that weak filter, not all feedback learning.
4. **C3 information gap confirmed.** The old deployment features were nearly
   constant and did not distinguish semantic errors. The old complex-policy
   conclusion remains stopped; the problem is not solved.

## Corrections Implemented

- `source_role_contract_v3.py` enforces source-role disjointness using
  `table_uid` and available higher-level source IDs, with a regression test for
  same-table/different-question leakage.
- `prepare_source_disjoint_tasks_v3.py` selected 96 tasks whose source keys are
  disjoint from all reconstructed training tasks and prior confirmation tasks.
  Manifest: `research/feedback_learning_finance_20261024_v2/SOURCE_DISJOINT_TASK_MANIFEST_V4.json`.
- `semantic_constant_review_v3.py` reviewed all 38 suspicious denominators:
  33 `STRUCTURAL_CONSTANT_MISBOUND`, 3 `LEGAL_FINANCIAL_DENOMINATOR`,
  2 `UNRESOLVED_REFERENCE_QUESTION_MISMATCH`. In training: 8 structural,
  1 legal, 2 unresolved. The two unresolved cases are excluded from new
  supervision rather than silently repaired.
- The historical v2 results are retained. `VARIANT_RESCORE_V3.json` is a
  post-hoc prompt-table rescore and is explicitly separate from new runs.

## Corrected Scientific Interpretation

- The old `0% relevant-change adaptation` claim is withdrawn. The v2 scorer
  executed against stale task tables while expected answers used variant
  tables; 95/648 frozen rows flipped under prompt-table scoring.
- Ordinary answer/execution SFT remains a bounded strong baseline. On the
  source-disjoint 24-family panel its task-level intersections are 19/24
  original, 19/24 original-and-relevant, 17/24 original-and-irrelevant and
  17/24 paired all-three; visible filtering is 13/24, 13/24, 12/24 and 12/24.
  The direction is consistent with the earlier panels, but the
  ordinary-minus-visible bootstrap intervals include zero; this is a panel
  result, not a population-level superiority claim.
- The first natural-error repair run was over-specialized: both arms had only
  9 unique tasks and performed far below the 512-task ordinary baseline.
  The second run preserved 48 unique tasks and compared error weighting with a
  uniform mixed control. Weighted paired completion was 50.0%, uniform
  58.3%, ordinary 70.8%; this specific natural-error weighting is stopped.
- C3 semantic checking is informative but not a safe policy. On frozen
  outputs, semantic acceptance reduces the absolute number of accepted wrong
  answers but increases conditional wrong-delivery risk and removes substantial
  correct coverage; structural-denominator repair was not applicable to the
  confirmation outputs. No hidden reference is used by the checker.

## Evidence

- `research/feedback_learning_finance_20261024_v2/SEMANTIC_CONSTANT_REVIEW_V3.json`
- `research/feedback_learning_finance_20261024_v2/SOURCE_DISJOINT_TASK_MANIFEST_V4.json`
- `research/natural_program_learning_20261024_v2/SOURCE_DISJOINT_SUMMARY_V4.json`
- `research/natural_program_learning_20261024_v2/SOURCE_DISJOINT_ANALYSIS_V4.json`
- `research/natural_program_learning_20261024_v2/NATURAL_ERROR_REPAIR_SUMMARY_V4.json`
- `research/natural_program_learning_20261024_v2/WEIGHTED_ERROR_REPAIR_SUMMARY_V5.json`
- `research/natural_program_learning_20261024_v2/SEMANTIC_DELIVERY_CHECK_V5.json`
- `research/natural_program_learning_20261024_v2/SEMANTIC_REPAIR_DELIVERY_V5.json`

## Boundary

The new panels are same-source TAT-QA table families, not independent
benchmarks. Training references are executable reference programs, not human
gold. All new analyses are development/confirmation evidence within the
stated source boundary.
