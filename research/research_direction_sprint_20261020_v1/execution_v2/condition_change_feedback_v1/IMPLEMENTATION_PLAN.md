# Condition Change Feedback V1 Implementation Plan

**Goal:** Build a frozen, deterministic reimbursement sandbox that derives
reference decisions and minimal evidence sets from declarative policy and
evidence facts, then separates exact-match, sufficiency-only, and composite
feedback behavior.

**Report paths:** Package-local reports are `RETURN.md` and
`MACHINE_VERIFICATION.json`. Unique execution-root reports are
`execution_v2/CONDITION_CHANGE_LOOP_A_RETURN.md` and
`execution_v2/CONDITION_CHANGE_LOOP_A_VERIFICATION.json`. Existing
`GB10_LOOP_A_RETURN.md` and `GB10_LOOP_A_VERIFICATION.json` are out of scope.

**Architecture:** The V1 source inputs remain frozen. A declarative V2 revision
appends one paired case and one policy rule; the builder emits separate V2
actor tasks, evidence facts, derived references, and actor-only probe
proposals. The V2 actor view includes applicable policy text/delta only. The
reference builder reads policy and evidence facts only.

**Tech Stack:** Python 3.12.3 standard library, JSON, `unittest`, SHA-256
receipts.

## Constraints

- Write only inside `condition_change_feedback_v1/` plus the two unique
  execution-root reports.
- Run the five commands exactly as declared in `SPRINT_CONTRACT.md`.
- Send zero model, judge, training, service, network, or production Memory
  requests.
- Do not edit FinRank, Paper E, frozen schema, or frozen repository nodes.
- Freeze 13 paired cases across at least four source clusters with at least
  three decision flips, three invariant pairs, two alternative sufficient
  sets, two out-of-scope additions, and one invariant-decision pair whose
  minimal set changes.
- Never encode per-case gold decisions or sufficient sets.

## Task 1: Freeze Inputs And Receipt

- [x] Separate actor views from reference facts in
  `build_condition_change_inputs.py`.
- [x] Hash V1 and V2 source/derived inputs in `FROZEN_INPUT_MANIFEST_V2.json`.
- [x] Enforce CPython 3.12.3 and zero-request accounting.
- [x] Freeze with `python3 -B build_condition_change_inputs.py --freeze`.

## Task 2: Derive References Without Gold

- [x] Evaluate first-match declarative rules in `reference_builder.py`.
- [x] Preserve policy alternative order while deriving Cartesian-minimal sets.
- [x] Derive references from `POLICY_SPEC_V2.json` and
  `EVIDENCE_FACTS_V2.json` only.

## Task 3: Run Baseline And Contract Probe

- [x] Implement the frozen historical prior-plan baseline.
- [x] Implement exact-match, sufficiency-only, and composite dispositions.
- [x] Freeze actor-only single-factor scope proposals and derived dispositions.
- [x] Require byte-equivalent recomputation on `--run`.

## Task 4: Verify Machine Acceptance

- [x] Add 15 focused acceptance tests in `test_condition_change.py`.
- [x] Implement hash, schema, count, disposition, baseline, headroom, and
  zero-request checks in `verify_condition_change.py`.
- [x] Write `MACHINE_VERIFICATION_V2.json`, `RETURN.md`, and both unique
  execution-root reports.

## Task 5: Adversarial Closeout

- [x] Re-run the exact five-command sequence from the package directory.
- [x] Confirm 15/15 tests pass and machine verification is `PASS`.
- [x] Confirm the deterministic baseline is non-terminal at both stages.
- [x] Recommend `STOP_BEFORE_REAL_MODEL` without starting a model phase.
