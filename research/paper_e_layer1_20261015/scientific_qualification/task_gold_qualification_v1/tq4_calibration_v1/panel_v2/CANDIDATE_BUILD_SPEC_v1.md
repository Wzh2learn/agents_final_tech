# TQ-4 Candidate Build Spec v1 (frozen)

> Frozen: 2026-10-16, before any TQ-4 model output exists.
> Scope: part 2 of the TQ-4 calibration run - three reference-clear tasks x four manual candidates = 12 candidates;
> B/C only (no actor). Separate accounting from part 1; never mixed into a single "natural error rate".

## Task selection rule (frozen)

- Source: TQ-3 `specs_rev1` tasks with status `REFERENCE_REPLAY_READY` (Q02, Q03, Q04, Q05, Q10, Q12).
- Take the first three by task_id order: **Q02, Q03, Q04** (list / numeric-difference / numeric-change coverage falls out; no output-based choice).

## Candidate matrix (frozen order)

For each task: C1 correct answer + legal evidence; C2 correct answer + illegal evidence;
C3 incorrect answer + legal evidence; C4 incorrect answer + illegal evidence.
`legal`/`illegal` refer to protocol v2 LOCATION legality only (`check_evidence_legality`); support is never judged here.

## Answer construction (frozen, auditable)

- Q02: correct = "accounts receivable, inventories, and net property, plant, and equipment";
  incorrect = "accounts receivable, inventories" (subset: first two items only).
- Q03: correct = 14054; incorrect = -14054 (reversed subtraction direction).
- Q04: correct = -3; incorrect = 3 (sign flip).

## Evidence construction (frozen)

- Q02 legal: `[{"kind":"paragraph","paragraph_uid":"5a443fa1-ad91-4454-8ba2-9992a29bd813"}]` (composition paragraph uid from the frozen input).
  Q02 illegal: `[{"kind":"paragraph","paragraph_uid":"00000000-0000-0000-0000-000000000000"}]` (unknown uid).
- Q03 legal: `[{"kind":"cell","table_row":2,"table_col":2},{"kind":"cell","table_row":3,"table_col":2}]` (Class A / Class B values, 0-based).
  Q03 illegal: `[{"kind":"cell","table_row":99,"table_col":0}]` (out of bounds).
- Q04 legal: `[{"kind":"cell","table_row":1,"table_col":1},{"kind":"cell","table_row":2,"table_col":1}]` (2021 / 2022 rows).
  Q04 illegal: `[{"kind":"cell","table_row":1,"table_col":9}]` (out of bounds).

## Model-visible variant (frozen)

- Candidate inputs = the perturbed variants (copied from TQ-3 `dev_panel/inputs_perturbed/` with pins; task_id preserved).

## Frozen design targets (hypotheses, not outcome guarantees; do not tune to achieve)

- C1: semantic target accept; C2: semantic target accept-in-substance while B may flag the illegal citation (C cannot see citations);
  C3/C4: semantic target alarm (answer contradicts the table).
- Primary observation: B vs C differences by (answer_kind x evidence_legality). Citation legality is visible to B and
  invisible to C by design.

## Freeze

- `candidates_v1.json` + `CANDIDATES_LOG.json` (hashes, legality verification results, freeze timestamp).
- After freeze, no modification or replacement based on B/C divergence; any change requires a NEW version.
