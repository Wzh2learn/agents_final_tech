# Task Contract: Graph Loop Meta-Retrospective and Governance Audit - Loop C

- Task ID: `graph-loop-meta-retrospective-c-20261010`
- Role: Loop C / GB10 fresh-context independent audit
- Window: zero-endpoint, non-training
- Scope: governance audit plus binding-v3 engineering qualification
- Skills: audit-cycle, self-eval-bias, verify-before-done, systematic-debugging, experiment-autopsy, neat-freak, jinrong-docs-sync, offline-eval-playbook

## Objective

Independently audit the governance diagnosis and determine whether the system is ready for the next formal run. Do not run or authorize a formal scientific experiment.

## Independence Order

1. Read Graph Loop rules, STATE/THREADS/Dispatch/INDEX, existing harness audit and authority conventions.
2. Inspect raw FinQA artifacts, binding-v3 source and qualification rows before reading the meta-retrospective conclusions.
3. Run the preflight checker tests and binding-v3 integration tests.
4. Verify authority-map paths, hashes and supersession labels.
5. Verify pass-level vocabulary and handoff fields are complete and non-conflicting.
6. Compare with `docs/governance/audit/graph_loop_meta_retrospective_2026-10-10.md` only after first-hand conclusions are formed.

## Required Checks

1. Root-cause tree distinguishes scientific/data/contract/interface/test/documentation/state/handoff/governance causes.
2. Every FinQA failure is mapped to the correct family and supported by a primary artifact or command.
3. Existing `harness_audit_20260905` findings are treated as baseline, not re-reported as new.
4. Authority map has one current authority per object and explicit supersession for old binding/invalid runs.
5. `STATE`, `THREADS`, `Dispatch`, `INDEX` identify the same current blocker and do not promote chat/log-only facts.
6. PASS levels distinguish UNIT/COMPONENT/CONTRACT/INTEGRATION/END_TO_END_PREFLIGHT/FORMAL_RUN.
7. `FORMAL_EXPERIMENT_PREFLIGHT_V1` covers authority version, hash domain, runtime metadata, IDs, split, scorer, analysis plan, seeds, integration dry-run, zero-output qualification and previous-run immutability.
8. `formal_experiment_preflight.py` rejects silent defaults and existing scientific outputs in positive-control tests.
9. Binding-v3 qualification independently confirms 89/89 runtime bindings, 420/420 evaluation trace rows, four explicit metadata fields, zero silent defaults, zero identity/group/split drift, zero leakage, zero scientific outputs and immutable previous runs.
10. No frozen FinQA scientific design, metrics, thresholds, split or source artifacts were modified.
11. A/C/D handoff gaps are documented and the reusable handoff template is updated.

## Output

Return the complete report in the task log. Include:

- independent root-cause corrections if any;
- authority-map and state consistency verdict;
- PASS-level verdict;
- binding-v3 `RUNTIME_BINDING_INTEGRATION_GO`;
- `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN`;
- exact commands, hashes, test counts and warning list;
- any remaining blocker and its single owner;
- `VERDICT: PASS | CONDITIONAL | FAIL`.

## Forbidden Actions

- Run formal FinQA, PRM, Stage D or any model training.
- Modify scientific artifacts or frozen contracts.
- Repair the binding or governance files during audit.
- Treat the meta-retrospective prose as evidence without first-hand verification.

## Success Exit

The report either confirms `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = YES` or identifies the single remaining governance/engineering blocker without overclaiming.
