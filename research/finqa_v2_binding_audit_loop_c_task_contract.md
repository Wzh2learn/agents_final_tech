# Task Contract: FinQA v2 Binding V2 Independent Audit - Loop C

- Task ID: `finqa-v2-binding-audit-c-20261010`
- Role: Loop C / GB10 fresh-context independent audit
- Window: zero-endpoint, non-training
- Skills: audit-cycle, self-eval-bias, verify-before-done, systematic-debugging, experiment-autopsy, offline-eval-playbook
- Advisory boundary: audit and report; do not repair

## Objective

Independently determine whether raw/normalized artifact hash mismatch is only a deterministic serialization/normalization contract mismatch and whether the binding-v2 repair is authorized for a minimal formal rerun.

## Independence Order

1. Read raw frozen paired artifacts and unchanged scorer source.
2. Independently recompute raw and normalized hashes and step mappings.
3. Exercise positive/negative controls.
4. Inspect source for identity/leakage/semantic effects.
5. Only then read Loop A's contract, mapping summary and receipt.
6. Compare and disclose any prior-conclusion ingestion.

## Inputs

- old invalid-run result files;
- frozen sample/split/paired-artifact/scorer-binding manifests;
- unchanged scorer source;
- `research/finqa_v2_20261010/binding_v2/` repair artifacts;
- binding-v2 tests and logs.

## Required First-Hand Checks

1. Recompute all old-run and binding-v2 hashes.
2. Independently derive raw and normalized pair payload hashes for all 215 pairs.
3. Independently map all 994 steps with stable trace keys.
4. Verify deterministic replay of `op -> op_family`.
5. Verify lossy op collapse is documented and not called bijective.
6. Verify raw identity remains traceable by artifact ID + side + step index.
7. Verify normalization does not alter:
   - sample identity;
   - raw stored artifacts;
   - task semantics/evidence/answers;
   - split/group membership;
   - scorer measurement object;
   - label/outcome/stage/result information.
8. Verify normalized payload excludes IDs, labels, outcomes, split/group and result fields.
9. Run binding-v2 focused tests independently.
10. Inject synthetic positive controls:
    - corrupted raw payload;
    - corrupted normalized payload;
    - missing trace key;
    - unexpected trace key;
    - changed sample/group ID.
   Each must fail closed.
11. Verify old invalid run remains unchanged and unsuperseded scientifically.
12. Verify no frozen-pair scorer output was produced during repair.

## Decision Flags

Independently assign true/false for:

- `DETERMINISTIC`
- `SEMANTICS_PRESERVING`
- `BIJECTIVE_OR_TRACEABLE`
- `NO_LEAKAGE`
- `NO_SAMPLE_ID_CHANGE`

## Output

Return the complete report in the task log. Do not modify artifacts.

Required fields:

- root-cause classification;
- engineering-binding-bug verdict;
- decision flags;
- exact 215-pair/994-step accounting;
- semantic-preservation evidence;
- positive-control results;
- inherited gates;
- gates requiring a new freeze;
- `SCORER_BINDING_GO = PASS | FAIL`;
- `VERDICT: PASS | CONDITIONAL | FAIL`;
- scientific reason;
- strongest counterexample or failure scenario.

## Forbidden Actions

- Repair or modify any artifact.
- Score frozen pairs as a formal experiment.
- Reopen SOURCE/ID/JOIN/SPLIT.
- Normalize stored payloads.
- Hide the old invalid run.
- Treat traceability as bijectivity.

## Stop Conditions

- Any of the five flags is false/unverified.
- Mapping accounting differs from 215/994.
- Positive control fails to fail closed.
- Raw/normalized content drift is found beyond frozen scorer normalization.
- Old artifacts change.

## Success Exit

All five flags pass, `SCORER_BINDING_GO = PASS`, and the report supports a minimal rerun limited to formal scorer, frozen estimands and bootstrap.
