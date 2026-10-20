# Dataset Card

## Dataset

MA-CERD Gold Public v1 contains 1,000 paired counterfactual contracts derived from 100 synthetic simulator-backed base cases. It evaluates relation, admissible handling, affected and preserved plan elements, and disagreement among explicit-rule, human-judgment, and simulator-shadow oracle layers.

## Composition

- 685 `change`, 315 `invariant`
- 600 train, 200 development, 200 test
- 600 ID and 400 compositional-OOD records
- 253 all-agree, 94 O1-only-disagrees, 75 O2-only-disagrees, 578 O3-only-disagrees
- 752 succeeded and 248 failed simulator-shadow outcomes

## Human evidence

Every record was reviewed by two blind reviewers; 391 relation disagreements were adjudicated by a third role before Gold promotion. The public package contains only structured final judgments and public sequential adjudication IDs. Reviewer identity, signatures, correspondence, raw free text, and private response collection hashes are controlled-access material.

Software verifies structure, hashes, completeness, and promotion rules. It does not independently authenticate human identity or collection circumstances.

## Limitations

The cases are synthetic and simulator-backed. The O3 layer is deterministic shadow-mode evidence and does not establish certified fidelity or physical behavior. The collection has two primary reviewers and one adjudication role, limiting reviewer-population generalizability. Oracle disagreement is substantial and should be reported rather than hidden.

No result from this dataset establishes live-command authority, operational deployment readiness, certified autonomy, weapon control, physical-flight validity, or real-world safety.
