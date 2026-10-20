# Negative-Only Episodic Memory Design

Status: `SUPERSEDED / GATE_NOT_MET / DO_NOT_RUN`

Current ruling: the final task-matched collection produced no wrong-role
correction and no action change. H-negative/random is not identifiable with the
current real-history pool. See `ROLE_HISTORY_COLLECTION_RETURN.md`.

## Mechanism

For each historical task, store:

- the visible source/claim/candidate-role structure;
- the first failed plan or decision;
- the deterministic feedback category;
- the post-feedback action change, if any.

Do **not** store the final corrected answer in H. The H arm must use only the failure signature and feedback. The K arm continues to use ordinary solved examples with final plan/tool/consume outputs.

## Primary comparison

Use the same source-isolated role-binding panel:

- B0: no context;
- R: strong role rule;
- K: ordinary solved examples;
- H-negative: first failure plus feedback, no solution;
- optional random/no-guidance control.

The key contrast is `H-negative vs K`, not `H vs B0`.

## Primary metric

Cluster-equal role-decision accuracy on the same matched positive/wrong-role tasks.

Secondary metrics:

- plan validity;
- tool execution;
- numeric consistency;
- false accepts and false rejects;
- abstention/UNKNOWN calibration;
- context tokens and calls.

## Prediction

- If H-negative beats K on role decisions while plan validity is matched, historical failure information is non-redundant.
- If H-negative and K remain equal, the experience representation has no unique signal and should be stopped.
- If H-negative only improves plan/format, report interface learning, not role experience.

## Source and budget requirements

- Keep development and future source clusters disjoint.
- Use task-matched failure signatures from history clusters only.
- Freeze selection and feedback rules before any future model output.
- Require a new request authorization; the current 292-request ledger is exhausted.

No model request, pilot or training is authorized by this draft.
