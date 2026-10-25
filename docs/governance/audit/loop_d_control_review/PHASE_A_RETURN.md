# Loop D Phase A Governance Return

Date: 2026-10-26, Asia/Shanghai

Status: `GOVERNANCE_RETURNED_AWAITING_REVIEW`

Scope: Phase A only. No model generation, judge, training, service probe,
submission, payment, public release, or Phase B execution was performed.

## 1. Changes And Unfinished Work

**同意:** The latest `0abc0935` consolidation is the active authority. The
local repository, Origin and GB10 were identical and clean at the start of
Phase A. G1/C1 is a mature but unsubmitted two-case Paper E; G2/C2 and G3/C3
remain candidate research lines rather than established contributions.

**纠正及证据:** The prior diagnostic return over-collected two unequal cases.
The unit case lacks a visible `million/thousand` scale in its input. Its
reference unit cannot be treated as a visible repair target. The only eligible
visible repair case is the row/period/reference error. Counts and raw rows
remain unchanged in `PHASE_A_RECOMPUTE_V1.json`.

**未核实及影响:** No evidence yet establishes a second independent thesis
contribution or cross-source transfer. The old V4/V5 error-pool replay remains
development evidence only.

## 2. Current Diagnostic

**同意:** The standardized wrapper eliminated runaway instruction repetition;
all historical diagnostic rows stop at EOS and have per-row non-padding lengths.

**纠正及证据:** The old generic adapter could corrupt content by converting
`1)0` to `10`. The corrected adapter only replaces a terminal `\"...)}` tail
and requires strict whole-JSON parsing. The counterexample remains unchanged
under the corrected adapter. `strict_format_valid` and `embedded_format_valid`
are separate fields.

**未核实及影响:** The safe adapter is a format boundary, not proof of semantic
correctness. Existing raw outputs and old scores remain historical evidence.

## 3. Reusable Assets

**同意:** The following assets are directly reusable for a later authorized
experiment:

1. Frozen ordinary Qwen3-4B checkpoint and PEFT adapter:
   `/home/testuser/wzh/research_runs/natural_program_finance_20261024_v2/training/ordinary_answer_execution_sft/final_adapter`.
2. Frozen natural task/output pairs and the V4/V5 source-disjoint task pool:
   `/home/testuser/wzh/research_runs/weighted_error_repair_v5/weighted_confirmation_instances_v5.jsonl`
   and `weighted_confirmation_results_v5.jsonl`.
3. Visible table, unit, row, period and execution helpers:
   `analyze_binding_residual_v3.py`, `natural_program_contract_v2.py`,
   `semantic_delivery_check_v3.py`.
4. Pre-generation exposure-union guard and source manifest:
   `exposure_union_guard_v1.py` and `EXPOSURE_UNION_SOURCES_V1.json`.
5. Existing Qwen/PEFT/TRL training chain:
   `run_natural_program_experiment_v2.py`.

These assets save data preparation and environment setup; they do not provide
unseen sources or qualified correction labels.

## 4. Research Judgment

**同意:** The cheapest primary question is whether a qualified local edit
representation improves correction over an information-matched full-program
revision and neutral retry.

**纠正及证据:** The current evidence does not support a unified
diagnosis-to-edit failure claim. The unit case is unobservable for the intended
unit; on the one eligible visible error, neutral, category and localization
all remain target-exact 0/1. Explicit reference-assisted edits are executable
2/2, so the missing piece is not generic command execution.

**未核实及影响:** It remains unknown whether the gap is feedback granularity,
learned revision policy, or source/task transfer. C2 is not established; C3 is
not established.

**Primary C2 candidate:** Teacher/tool-verified local-edit learning versus
matched full-program revision, with O/N/R/E controls and exposure-clean
confirmation.

**Backup C3 candidate:** Keep only if deployment-visible checks and bounded
actions produce a distinct delivery improvement over neutral retry and
always-accept without paying for it mainly through abstention. If C2 and C3
continue to share the same repair mechanism and metric, merge them and replace
one contribution.

## 5. Concrete Follow-Up

**Paper E:** Keep the two-case boundary. Recommended primary remains ICAART
2027 Regular only if Owner authorizes before 2026-10-29 AoE, accepts
presentation/travel exposure, and confirms school recognition. Otherwise use
SN Computer Science subscription as the sequential backup. For the current
12-page manuscript, known ICAART venue cost is EUR 680 as Full or EUR 880 as
Short with four paid extra pages; optional social event is EUR 80 and travel
is unknown. SNCS subscription charges are zero; optional OA is GBP 2,390 /
USD 3,290 / EUR 2,690 plus tax.

**Phase B proposal:** A single non-additive budget request is recorded in
`research/feedback_delivery_continuation_20261025_v1/NEXT_PHASE_BUDGET_REQUEST_V1.json`:
96 qualification + 108 development O/N/R/E + 288 exposure-clean confirmation
+ 144 second seed + 36 reserve = 672 generation attempts, 2.8M generation
tokens, four training runs and 4.0M training tokens. The request is
`REQUESTED_NOT_AUTHORIZED`; the remaining 32 attempts are not a new stage.

**Stop conditions:** Stop local-edit C2 if it does not beat matched R after
teacher/training cost and exposure-clean confirmation, or if only format and
length improve. Stop C3 if risk reduction comes only from abstention or if it
duplicates C2's mechanism without an independent action/utility question.

## Ledger

**未核实及影响:** Independent event arithmetic gives 35 events, 4,064
attempts, 5,673,908 generation tokens, 3,495,424 training tokens and
9,169,332 total. The aggregate ledger states 9,169,672, leaving 340 tokens
unattributed. The conservative aggregate remains unchanged and the difference
is not released.

Phase A re-generation attempts: 0. Phase A training runs: 0.
