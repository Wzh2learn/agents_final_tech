# Sprint Contracts

Status: `FROZEN_BEFORE_IMPLEMENTATION`
Date: 2026-10-20, Asia/Shanghai

## C1 — FinRank Tool Contract And Development Baseline

Deliverable: a runnable `plan -> evidence_lookup -> consume` contract and a
request-accounted B0/strong-rule baseline on the first seven retained
development tasks.

Acceptance predicates:

- The actor request exposes the complete tool schema and visible scope fields;
  it contains no reference answer, hidden passage ID or adjudication rationale.
- `plan` accepts only candidate IDs from the current task and records
  `APPLY / SKIP / ABSTAIN` only when a history card is present.
- `evidence_lookup` returns requested candidate text and visible source fields
  only, in request order, and rejects unknown IDs, cross-task IDs, duplicates,
  extra keys and out-of-range parameters.
- `consume` cites only returned IDs and emits structured facts plus citations;
  it cannot cite absent evidence.
- Fixtures pass for legal lookup, invalid parameters, same-year/different-period
  evidence, no reference leakage and ESD_010 sufficient-subset acceptance.
- The first seven task actor views and evaluation references are separately
  frozen from the AI adjudication; excluded and repair tasks are not included.
- B0 and the strong visible-rule baseline produce complete per-task outputs,
  request counts and error classes. Engineering/schema failures are separated
  from semantic selection errors.

Runtime path:

```text
python finrank_dev/qualify_runtime.py
python finrank_dev/run_fixtures.py
python finrank_dev/run_b0.py --ledger ../execution_v1/RESEARCH_GENERATION_LEDGER.json
python finrank_dev/run_strong_rule.py
```

Out of scope: history collection, H-U/H-S/K comparisons, task repair, neural
FinRank reruns, Paper E edits, training and production writes.

## C2 — Active Evidence Acquisition Probe

Deliverable: a deterministic development probe comparing evidence-check
policies on the frozen retained tasks.

Acceptance predicates:

- The probe freezes task inputs, minimal sufficient sets, lookup budgets and
  random seeds before computing outcomes.
- Strategies include direct answer, fixed check, random check, lexical
  relevance, score-disagreement and an oracle upper bound.
- Metrics report sufficient-set discovery, useful-fact coverage, lookup cost and
  regret to oracle at budgets 1, 2 and 3.
- The output distinguishes engineering fixtures from `DEV_ONLY` simulation and
  makes no model-effect or independent-generalization claim.
- ESD_010 is evaluated as a sufficient subset, not forced two-passage exact
  match.

Runtime path:

```text
python open_research_probes/active_evidence_probe.py --freeze
python open_research_probes/active_evidence_probe.py --run
```

Out of scope: changing FinRank references, selecting tasks from model errors,
claiming active collection improves a deployed agent, and consuming generation
budget.

## C3 — Feedback-Contract Mechanism Probe

Deliverable: a controlled `DEV_ONLY` comparison of exact-match, sufficient-set
and fact-coverage feedback for retaining/selecting evidence experiences.

Acceptance predicates:

- The same candidate selections are scored under all three feedback contracts.
- Valid alternative sufficient sets are counted separately from genuinely
  unsupported selections.
- A small deterministic update rule records which experiences are retained,
  revised or rejected; no language-model judgment is used as gold.
- Results report whether exact-match feedback creates false-negative updates
  and whether sufficient-set feedback admits unsupported selections.
- The probe explicitly states that it is a mechanism intervention on feedback
  semantics, not a natural experiment or validated learning method.

Runtime path:

```text
python open_research_probes/feedback_contract_probe.py --freeze
python open_research_probes/feedback_contract_probe.py --run
```

Out of scope: training, reward-model fitting, real-history claims and
independent validation.
