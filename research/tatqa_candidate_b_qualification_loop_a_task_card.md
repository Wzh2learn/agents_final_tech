# Candidate B Offline Qualification - Loop A

Task ID: `tatqa-candidate-b-qualification-a-20261019`

Role: Loop A / GB10 offline source, exposure, task and reference qualification

Status: `AUTHORIZED_OFFLINE_ONLY`

## Scientific question this package supports

Can a new TAT-QA development and future-validation panel create a genuine actor decision at **evidence binding before calculation**:

select row, early/late periods, sign direction and unit/scale before calling `calc`?

This task does not run the actor or estimate experience effects.

## Inputs

- `research/paper_e_contribution_reassessment_v1/REUSE_TASK_REDESIGN.md`
- `docs/archive/2026-10-19_NEXT_DEVELOPMENT_RUN_CARD_DRAFT.md`
- existing TAT-QA source, origin, split and exposure artifacts under `research/tatqa_wp0_2026/`
- existing history collection qualification and execution manifests
- raw fixed-revision TAT-QA files:
  - `data/research/tatqa_raw_2026/tatqa_dataset_train.json`
  - `data/research/tatqa_raw_2026/tatqa_dataset_dev.json`

Preserve all old tasks, references, raw responses and exposure judgments. Do not relabel the existing 16 B0 tasks or 12 histories as unseen material.

## Required work

### 1. Source and exposure qualification

- Verify raw file identity and hashes against existing source records.
- Reuse verified source-cluster evidence where available; do not reopen settled source decisions without a concrete conflict.
- Build a machine-readable exposure manifest with evidence classes:
  `ID_SCAN_ONLY`, `PROGRAMMATIC_ONLY`, `DESIGN_OR_DIAGNOSTIC`, `MODEL_OR_FEEDBACK_EXPOSED`, `EXPOSURE_UNKNOWN`.
- Count development, history and future-validation clusters separately.
- Treat unknown exposure as temporarily ineligible.
- Report report-level identity as `UNRESOLVED` where it cannot be verified; do not claim report-disjointness.

### 2. Candidate B task construction

Use a frozen label-blind rule based only on source structure:

- candidate rows must be present in the same table;
- candidate early/late periods must be structurally identifiable;
- distractor rows/periods must come from the same frozen table;
- task difficulty and distractor count must not use model outputs, expected errors or observed failures;
- no model output may be inspected during selection or reference construction.

Target panel:

- 8 development source clusters × 2 tasks = 16 development tasks;
- 8 future-validation source clusters × 2 tasks = 16 future tasks;
- existing exposed clusters excluded.

If the source cannot supply these counts, report the exact shortfall and do not lower the rule to fill quotas.

### 3. Hidden reference and semantic gate

For every task, record hidden:

- row coordinate and canonical label;
- early/late period coordinates;
- source values and display strings;
- sign convention;
- source/target unit and scale;
- deterministic `late - early` reference;
- expected calculator expression.

Before model access, classify each item:

- `REFERENCE_VALID_DETERMINISTIC`;
- `REQUIRES_HUMAN_SEMANTIC_ADJUDICATION`;
- `UNSCORABLE_FOR_REFERENCE`;
- `EXCLUDE_SOURCE_OR_EXPOSURE`.

Loop A and Loop C are AI reviewers and cannot convert `REQUIRES_HUMAN_SEMANTIC_ADJUDICATION` into human gold.

### 4. Reference checker

Implement an isolated checker that:

- validates hidden coordinates against the frozen source;
- recomputes the signed difference and unit scale;
- detects wrong row, wrong period, reversed sign, wrong unit and answer/tool inconsistency;
- never exposes hidden coordinates or reference values to actor-facing task JSON;
- fails closed on ambiguity, missing cells, non-numeric values and inconsistent units.

## Outputs

Under `research/tatqa_candidate_b_qualification_v1/`:

1. `SOURCE_EXPOSURE_QUALIFICATION.json`
2. `CANDIDATE_B_TASKS_DRAFT.json`
3. `HIDDEN_REFERENCE_MANIFEST.json`
4. `candidate_b_reference_checker_v1.py`
5. `tests/test_candidate_b_reference_checker_v1.py`
6. `QUALIFICATION_SUMMARY.json`
7. `LOOP_A_RETURN.md`
8. `candidate_b_qualification_receipt.json`

The receipt must hash-bind raw sources, reused exposure/cluster artifacts, task selection rule, implementation, tests and summaries.

## Verification

Run and record:

- raw source hash verification;
- cluster/exposure count reconciliation;
- actor-facing/hidden-field separation tests;
- wrong row/period/sign/unit negative tests;
- deterministic reference recomputation;
- two-run task-manifest determinism;
- focused unittest or pytest;
- explicit count of human-adjudication-required items.

## Hard boundaries

- No actor, judge, model, collection, pilot, training, production memory or service calls.
- No current B0/R/C/H execution.
- No task selection based on model errors or expected headroom.
- No hidden reference in actor-facing files.
- No silent semantic adjudication by AI.
- No change to old tasks, frozen results, source splits or authorizations.
- No commit or push.

## Exit states

- `CANDIDATE_B_QUALIFIED_OFFLINE`: at least 8 development and 8 future source clusters are available, all selected tasks have deterministic or explicitly human-gated references, and the checker/tests pass.
- `CANDIDATE_B_CONDITIONAL`: source/exposure counts or semantic gates remain unresolved; report exact blockers and stop.
- `CANDIDATE_B_INSUFFICIENT_HEADROOM_PANEL`: fewer than 8 eligible clusters in either partition after frozen rules; stop and report the bound.
- `TECHNICAL_INVALID`: source identity, exposure or provenance checks fail.

This package remains `ONLINE_NOT_AUTHORIZED`.
