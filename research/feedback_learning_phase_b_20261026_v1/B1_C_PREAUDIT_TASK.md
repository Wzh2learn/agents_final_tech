# Loop C Task: B1 Pre-Audit of Supervision Qualification

Task ID: `phaseb-b1-preaudit-c-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md` at commit
`caa18102bdbbcfe99a889bcf82a125dcc20fdcca`, SHA-256
`c23ec144fe778d1ea8b36ab35def58a13b59d9682f1da4adf6005c2ea378e922`.

Role: C independent audit. File ownership:
`research/feedback_learning_phase_b_20261026_v1/audits/B1_C_PREAUDIT.md`
and `research/feedback_learning_phase_b_20261026_v1/audits/TASK_RESULT_C.json`.
Do not modify code, labels, manifests, raw data or A-owned files.

## Audit Scope

Independently inspect the frozen natural tasks/outputs and the B1 task
contract before accepting A's implementation:

1. Label visibility: unit scales, row/period/reference evidence, legal
   equivalence and `UNRESOLVED` cases.
2. Natural-error qualification: at least two eligible natural error types;
   correct and no-op samples are required.
3. Source/exposure union and the difference between table/question identity and
   report/company independence.
4. R/E information parity and deployment contracts. E must not receive the
   correct path/unit through feedback while R does not.
5. Patch semantics, fail-closed application and the prohibition on hidden
   reference fallback.
6. Frozen estimands and thresholds in `B1_D_FREEZE_GATE.md`.

Scientific C may read frozen raw/reference/scorer files and independently
recompute. The business compact-summary whitelist does not apply to this task.
Run only deterministic offline commands; no model, judge, training or
production endpoint.

## Required Outputs

- `audits/B1_C_PREAUDIT.md`
- `audits/TASK_RESULT_C.json`

Use `FACT / INFERENCE / VALUE / UNVERIFIED` labels and an overall verdict
`ACCEPTED / CONDITIONAL / REJECTED`. Record commands, hashes and exact scope.

## Return Contract

Final response must be one compact JSON object with keys `verdict`,
`findings`, `evidence`, `excluded`, `next_gate`, `budget`. No prose outside
JSON.
