# Loop A Task: Natural Semantic Error And Evidence-Cost Preparation

Task ID: `natural-error-cost-prepare-a-20261026`

Goal ID: `NATURAL_ERROR_EVIDENCE_COST_20261026`

Role: A-EXP. File ownership:
`research/natural_error_evidence_cost_20261026_v1/a_prepare/`.

Bind to commit `622b386986ca66c8119263e146f3d3e73c33e260`, the current
research prompt and `D_STAGE_GATE.md`. Run on GB10 with zero scientific
generation, zero training, zero judge and zero production calls. Do not
modify frozen raw, prior reports, scores, old R/E or Paper E artifacts.

## P1: Natural Evidence-Use Diagnosis

Start from the 24 ordinary original questions in
`source_disjoint_confirmation_v4`; keep the 19 correct outputs as controls and
diagnose the 5 `program_correct=False` candidates. Related/irrelevant variants
are separate controls and cannot be called natural errors.

For every candidate reconstruct:

`visible_input -> legal_evidence -> sufficiency/applicability -> model_program/
unit/reference -> deterministic_execution -> full_semantic_answer`

Classify exactly one primary failure and any secondary conditions:

- reference/scoring defect;
- visible information insufficient or unobservable;
- input-processing information loss;
- semantic evidence binding error;
- arithmetic/operator/unit/direction error;
- strict-output/interface failure;
- reasonable UNKNOWN;
- unresolved multiple legal interpretations.

Use gold program/answer only for offline reference and scoring. Do not leak
reference row IDs, gold programs, answers or hidden unit scales into proposed
deployment features. Training references may contain full correct labels, but
the diagnosis must separate supervision from actor visibility.

Replay the strongest available simple controls without new generation:
full visible table/header/context restoration, fixed calculator, strict
normalization, label/period/unit rules, existing one-shot ordinary output and
existing neutral retry where present. A simple tool may be the final answer.

Keep at most one mechanism hypothesis for P1, such as semantic-role binding
loss after evidence is already visible. Provide a falsifier and the minimum
probe needed to distinguish information loss from model-use failure.

## P2: Table-Text Evidence-Cost Qualification

Use the pinned TAT-QA raw source and the 507 `answer_from=table-text`
questions. Do not use FinQA as a new task source. Determine:

- complete semantic answer/derivation availability;
- legally recoverable table and paragraph evidence;
- source-cluster and exposure identity;
- whether the task requires both table and text or only one source;
- strongest simple frontiers: table-only, small top-k, fixed neighbor,
  larger top-k, always-expand and transparent stop/expand.

The qualification target is answer-risk-cost, not pure evidence coverage.
Freeze a proposed non-inferiority margin and one or two cost budgets before any
model output. Characters may proxy context volume but must not be reported as
measured token/latency savings. If full context is cheap and sufficient, accept
always-expand as the final baseline.

## Shared Requirements

- Provide 3-5 real examples per surviving candidate with complete references
  and deployable actions.
- Add every selected development example to the exposure register.
- Compare 3-5 concrete mechanism neighbors. Do not claim novelty from
  `table+text+calculator` or generic adaptive retrieval.
- Return two candidate cards and one blocked probe contract per candidate.
  D and C will select one; do not generate.

## Outputs

- `a_prepare/A_PREPARE_RESULT.json`
- `a_prepare/NATURAL_ERROR_DIAGNOSIS.jsonl`
- `a_prepare/P1_SEMANTIC_LEDGER.json`
- `a_prepare/P2_TASK_QUALIFICATION.json`
- `a_prepare/STRONG_BASELINE_FRONTIERS.json`
- `a_prepare/REAL_EXAMPLES.jsonl`
- `a_prepare/MECHANISM_NEIGHBORS.md`
- `a_prepare/EXPOSURE_REGISTER.json`
- `a_prepare/P1_PROBE_CONTRACT_DRAFT.json`
- `a_prepare/P2_PROBE_CONTRACT_DRAFT.json`

If a candidate fails, record a specific missing condition rather than
fabricating examples. Final response must be compact JSON.
