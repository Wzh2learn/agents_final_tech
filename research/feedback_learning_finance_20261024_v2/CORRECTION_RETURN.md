# Stage A Correction Return

Date: 2026-10-24, Asia/Shanghai

Status: `CORRECTED_RECOMPUTE_COMPLETE / OLD_RESULTS_PRESERVED`

## 1. Evidence And Lineage

The first-run raw files remain unchanged under
`/home/testuser/wzh/research_runs/feedback_learning_finance_20261023_v1`:

- `generation_results.jsonl`, SHA-256
  `9e9ba35f2f76de718f2485099e0088abbe342d87054c7564cf414a1a17abea9e`;
- six immutable `training/*/training_receipt.json` files;
- old `RESULT_SUMMARY.json`, retained as a historical mixed-scorer result.

Versioned corrections are in `CORRECTED_METRICS_V2.json`,
`TRAINING_SUMMARY_V2.json`, and `COMMON_CONTRACT_EVALUATION_V2.json`.
The scorer identity is `financial_feedback_corrected_scorer_v2`.

## 2. Corrected Scientific Judgments

1. The previous `tool-paired` metric mixed model-written numeric invariance with
   tool execution. It is renamed `legacy_mixed_pair` and retained only for
   lineage.
2. `legacy_formula_only_pair` reproduces the independent audit: `exec_cf` and
   `evidence_cf` each solve 13/14 three-variant pairs on the same-source test
   slice. This executes numeric formula constants and is not strict delivery.
3. `current_table_tool_pair` executes candidate refs and operator on the exact
   prompt-visible variant table. After correcting the old cached
   `evaluation_instances.jsonl` table identity, `exec_cf` and `evidence_cf` also
   reach 13/14 on test and 11/14 on the same-benchmark dev-file holdout.
4. The cached instance file stored original `table_text` for all variants, while
   model prompts contained the relevant mutation. V2 extracts the exact prompt
   table. This cache mismatch affects 392 generation instances and is a scoring
   lineage defect, not a model failure.
5. The old C2 comparison is therefore a controlled-supervision experiment:
   evidence filtering has no confirmed cross-source increment. The old external
   direct paired result remains zero; formula/program capability is separate.
6. Twenty-two natural percent-change tasks inherit `reported` rather than
   `percent` units. The old instances are preserved; v2 semantics require
   `percent_change -> percent` and `percentage_point_change -> percentage_points`.

## 3. Task And Source Boundary

The old test slice contains 12 difference and 2 percent-change tasks; the
same-benchmark dev-file holdout contains 4 difference and 10 percent-change
tasks. Numeric scale also differs. TAT-QA train/dev are same-benchmark source
files, not independent dataset families, and table UID is not full
report/company identity.

DocMath-Eval code was acquired at commit
`ee3a6de3236447b14835432574dd312f6f67008f`, and HF metadata declares MIT at
revision `bd0380d2cd0b6fa260d37d2f65c40b92eceef43f`. The dataset body remained
gated/403 through both direct HF and mirror retrieval, so it is not used for
training or evaluation in this stage.

## 4. Deployment Visibility

The v2 policy features are computed only from question, visible table, candidate
program, refs and public output contract. Hidden expected values are used only
for final offline scoring and labeled oracle/teacher supervision. Regression
tests keep visible inputs and candidates fixed while changing hidden expected
refs and answers; features and policy decisions remain unchanged.

Risk-model failure now fails closed. It never synthesizes probabilities from
`answer_correct`. Acceptance rate and retention/clarification rate are separate
metrics; `0/0` conditional risk is reported as unestimable, not zero risk.

## 5. Transparent Common-Contract Baseline

The row-name/year calculator solves the uniquely specified old derived template
near ceiling, but fails when the same year has multiple visible subcolumns and
the question does not state which subcolumn is intended:

- dev: 29/32 instances;
- test: 39/42 instances;
- same-benchmark external: 36/42 instances.

On external paired tasks, the transparent baseline reaches 12/14. The remaining
two failures are visible period ambiguity, not evidence that a learned policy
should guess hidden gold. Old checkpoints that choose one hidden-preferred
subcolumn cannot be credited as generalizable deployment success.

## 6. Aggregate Receipt

The corrected training aggregate contains all six arms:

- 1,440 training rows;
- 525,944 training tokens;
- 506.6289 recorded GPU-seconds.

No new model, judge or training calls were made for Stage A correction.

## 7. Decision

The first-run evidence is preserved, but its mixed tool-pair explanation and
C3 reference-assisted policy interpretation are superseded by v2. The next
experiment uses natural TAT-QA questions with structured evidence programs,
strict unit semantics and a visible-program feedback comparison. The old
derived template is closed for method expansion except as a regression and
interface fixture.
