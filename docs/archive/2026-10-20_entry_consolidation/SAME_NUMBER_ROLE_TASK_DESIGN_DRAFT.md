# Same-Number Role-Binding Task Design

Status: `EXPLORATORY_H_K_COMPLETE / NO_UNIQUE_HISTORY_EFFECT`

## Research question

When the same numeric value or signed delta is compatible with multiple row, period or unit roles, does real history improve an actor's evidence-role binding and acceptance decision beyond no context, strong rules and general context?

## User need

An analyst, auditor or compliance reviewer receives a numeric claim and a candidate citation. The number may be arithmetically correct while citing the wrong row, entity, reporting period, status or unit. The useful action is to accept the claim only when the cited evidence has the requested role; reject wrong-role evidence even when the number matches; and abstain or ask for clarification when the requested role is ambiguous.

## Task contract

Input:

- a bounded financial table;
- a requested role tuple: row/entity, early period, late period and unit/scale;
- a claimed signed change;
- one candidate evidence citation expressed without hidden coordinates.

Actor actions:

1. bind the citation to actual row/period cells or mark it unresolved;
2. call `calc` on the bound operands;
3. compare the executed value with the claim;
4. return one role decision:
   - `SUPPORTED`;
   - `WRONG_ROLE`;
   - `UNKNOWN`;
   - `REFUSE`.

The numeric calculation is necessary but not sufficient. A same-number wrong-role citation must remain `WRONG_ROLE`.

## Candidate construction

Use only frozen source structure:

- positive case: the requested role and citation are correct;
- same-number swap: change the cited row or period while preserving the displayed value;
- same-delta swap: cite another row or period pair producing the identical delta;
- equivalent-fact control: retain a valid alternative citation only when the source establishes equivalence;
- ambiguous case: include only if human semantics are independently adjudicated before model access.

Candidate selection must never use model output, expected failure or observed B0 errors.

## Available source boundary

Current TAT-QA reserve scan:

- eligible unselected reserve clusters: 26;
- same-number role clusters: 5;
- same-delta role clusters: 4;
- union: 5 clusters.

This supports at most a development panel of 10 tasks under two tasks per cluster. It does not support the predeclared 8-cluster independent validation panel.

## Development panel proposal

- 5 source clusters x 2 matched tasks = 10 development tasks.
- Each cluster supplies one positive/negative or wrong-role matched pair.
- Primary metric: cluster-equal role-decision accuracy.
- Secondary metrics: numeric consistency, tool success, answer/tool agreement, false accepts, false rejects, abstention rate and cost.
- Independent unit: source cluster.

## Required controls

| arm | content | purpose |
|---|---|---|
| B0 | no added context | baseline role binding |
| R | strong role-checking rule | exclude generic instruction effects |
| C | general financial-table context | exclude extra-token/context effects |
| H | task-relevant real wrong-role/correction history | test the proposed experience channel |

The current 12 successful calculation histories are insufficient for H. They contain no wrong-role decision or correction. A new task-matched history collection would be required and separately authorized.

## Primary hypothesis

Real history improves role binding only if it changes the accepted/rejected/abstained decision for same-number or same-delta evidence while leaving numeric calculation controlled.

## Stop rules

- fewer than 8 independent future clusters remain unavailable: no confirmatory claim;
- strong R explains the same gains as H: stop experience mechanism work;
- H improves only formatting or numeric computation: report interface/calculation effect only;
- role labels require unresolved human semantics: stop before model access;
- any source leakage or cluster overlap: no validation claim.

## Exploratory result

The internal source supplement produced nine development clusters and three exploratory future clusters. A 24-task B0 was run under `SAME-NUMBER-B0-20261019-1035-48REQ-R2`.

- B0: 18/24 success after correcting the `WRONG_ROLE` output contract; 6 role/contract failures across 6 clusters.
- On the 12 matched tasks from those six failure clusters:
  - B0: 6/12 success, 6/12 decision matches;
  - R: 8/12 success, 9/12 decision matches;
  - C: 7/12 success, 7/12 decision matches.

The strong role rule helps, but residual errors remain across four clusters. General context is weaker and introduces plan failures. H was not run because the current histories contain no wrong-role corrections and the request budget reached 228/228.

## Current decision

The task-matched history collection and H arm were completed. H reached 6/6 on the three-cluster future panel, but an ordinary solved-example K control also reached 6/6 with identical role decisions. The current evidence therefore does not isolate a real-history or feedback-specific effect.

Keep the role-binding task as a useful evidence-decision testbed, but stop the current experience-mechanism claim. A future experience study needs a new representation whose information is absent from ordinary solved examples, with K and random/no-guidance controls. No further model run is authorized under the current budget.
