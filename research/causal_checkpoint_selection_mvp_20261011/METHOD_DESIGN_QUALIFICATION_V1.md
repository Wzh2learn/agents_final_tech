# Causality-Aware Checkpoint Selection MVP — Method Design Qualification v1

> Status: `DESIGN_FROZEN_NOT_SCIENTIFICALLY_EXECUTED`
> Scope: six mechanisms, dependency subgraph, RIPR contract, cost-aware greedy, diagnosability and minimum decision rule
> Existing 216x12 data remains `ALGORITHM_SMOKE / DEV_ONLY`

## Frozen H1

Under a fixed observation budget, a checkpoint subset selected using failure-response plus causal-exposure information provides better held-out failure coverage and/or diagnosability than random, default or coverage-only selection.

## Six Mutation Mechanisms

| mechanism_id | stage | exact mutation operator | source state | expected causal path | candidate downstream checkpoints | distinction | automatic? | downstream state owner |
|---|---|---|---|---|---|---|---|---|
| `M1_FIELD_TOKEN_REPLACEMENT` | M | replace one canonical header/field token with a non-equivalent token, preserving table shape | `table[0][col]` | source token -> canonical header/mapping state -> mapping score | `parse.field.hit_rate`, `parse.table.regression` | lexical field mutation | YES: deterministic dictionary/operator | executor/mapper |
| `M2_TABLE_TOPOLOGY_TRANSPOSITION` | M | deterministically permute two complete table columns, preserving values and row count | full table grid and header order | table topology -> table-shape/header-order state -> structural regression score | `parse.table.regression`, `parse.field.hit_rate`, `parse.doc.ok` | structural/order mutation, not a string variant | YES: deterministic permutation | executor/table validator |
| `R1_REQUIRED_EVIDENCE_DELETION` | R | remove exactly one required evidence block from the retrieval candidate bundle | `required_evidence_ids` and candidate bundle | source bundle -> retrieved candidate/top-k set -> source-required oracle | `qa.retrieval.source_required`, `qa.numeric.number_grounding` | deletion mechanism | YES: deterministic bundle mutation | retrieval/checkpoint executor |
| `R2_DISTRACTOR_PROMOTION` | R | promote a non-required distractor into top-k or swap its rank with a required block without changing text | ranked evidence list and top-k membership | ranking state -> retrieved top-k set -> source-required oracle | `qa.retrieval.source_required`, `qa.numeric.number_grounding`, `qa.faithfulness.judge` | ranking/selection mutation, not deletion | YES: deterministic rank operator | retrieval/checkpoint executor |
| `N1_OPERAND_VALUE_PERTURBATION` | N | add fixed nonzero delta to one numeric operand/cell, preserving type and format | numeric cell/operand | numeric source -> identity operand state -> recomputed relation/result | `parse.reconcile.equations`, `qa.numeric.exact`, `qa.numeric.number_grounding` | operand-value mutation | YES: deterministic arithmetic | executor/reconciliation |
| `N2_OPERATOR_COEFFICIENT_PERTURBATION` | N | replace one arithmetic operator or flip one fixed coefficient/sign in the identity/program relation | relation operator/coefficient | relation definition -> recomputed identity/result -> reconciliation oracle | `parse.reconcile.equations`, `qa.numeric.exact`, `qa.numeric.number_grounding` | operator/semantics mutation, not operand value | YES: deterministic relation executor | executor/reconciliation |

Template/string/parameter variants do not count as separate mechanisms.

## Dependency Subgraph

Edges are marked `DESIGN_EDGE` until the new materialization executes them; existing direct checks may be `EXECUTION_CONFIRMED_EDGE`.

| edge | relation | evidence/source | type |
|---|---|---|---|
| source header token -> canonical header/mapping state | field normalization | `scripts/research/drift_inject.py`, `scripts/m1_statement_parser.py` | `EXECUTION_CONFIRMED_EDGE` for existing M field path |
| canonical mapping state -> `parse.field.hit_rate` | mapping score | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `EXECUTION_CONFIRMED_EDGE` |
| canonical mapping state -> `parse.table.regression` | table regression score | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `EXECUTION_CONFIRMED_EDGE` |
| table topology -> table-shape/header-order state | structural state | `scripts/research/drift_inject.py` + proposed M2 adapter | `DESIGN_EDGE` |
| table-shape state -> `parse.table.regression` | structural oracle | `config/eval_checkpoint_trees.json` | `DESIGN_EDGE` |
| evidence bundle -> retrieved candidate/top-k set | retrieval state | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `EXECUTION_CONFIRMED_EDGE` for R1-style bundle |
| retrieved top-k set -> `qa.retrieval.source_required` | retrieval oracle | `config/eval_checkpoint_trees.json` | `EXECUTION_CONFIRMED_EDGE` |
| ranked evidence list -> retrieved top-k set | ranking state | proposed R2 adapter | `DESIGN_EDGE` |
| numeric operand -> identity operand state | arithmetic input | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `EXECUTION_CONFIRMED_EDGE` |
| identity operand state -> `parse.reconcile.equations` | reconciliation oracle | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `EXECUTION_CONFIRMED_EDGE` |
| operator/coefficient -> identity relation state | arithmetic relation | proposed N2 executor | `DESIGN_EDGE` |
| identity relation/result state -> `qa.numeric.exact` / `qa.numeric.number_grounding` | downstream numeric oracle | `config/eval_checkpoint_trees.json` | `DESIGN_EDGE` |

Primary causal evidence prefers `EXECUTION_CONFIRMED_EDGE`; design edges must be confirmed during materialization before they can support H1.

## Anti-Tautology Contract

- `SOURCE_LOCAL_RESPONSE`: the mutation target or its direct source representation changes and the directly corresponding checkpoint flags it.
- `DOWNSTREAM_CAUSAL_RESPONSE`: a non-source state changes along at least one recorded dependency edge and reaches a checkpoint/oracle.
- `DIRECT_SOURCE_RESPONSE` is never sufficient for primary causal-method gain.
- Primary causal gain requires `mutation -> downstream edge -> descendant state change -> checkpoint/oracle response`.
- If the apparent advantage disappears after removing source-local-only cases, classify `MINIMUM_NO_INCREMENT` or method failure.
- The mutation generator cannot write checkpoint scores, oracle responses, RIPR flags or downstream states.

## RIPR Contract

For every injection x checkpoint:

- `REACHED`: source mutation is upstream in the frozen dependency graph.
- `INFECTED`: local input/state hash changes at the mutation target or first affected node.
- `PROPAGATED`: a descendant state hash changes along a recorded dependency path.
- `REVEALED`: frozen oracle/decision output changes or crosses its preregistered threshold.

Also record:

- `SOURCE_LOCAL_RESPONSE`
- `DOWNSTREAM_CAUSAL_RESPONSE`
- `oracle_response`
- `raw_state_pre_hash`
- `raw_state_post_hash`
- `dependency_path`

Missing state or missing path is `NOT_IDENTIFIABLE`, never zero. `checkpoint_changed` alone is not propagation.

## Corrected Cost-Aware Greedy

Hard budgets only:

```text
sum(check_count) <= B_check
sum(model_or_judge_calls) <= B_call
```

For every budget-feasible candidate, select the checkpoint with maximum marginal causal/diagnostic gain:

```text
marginal_gain =
    delta_downstream_causal_coverage
  + delta_stage_diagnosability
  + delta_family_diagnosability
```

No human cost weights. Tie order:

1. fewer model/judge calls;
2. lower check count;
3. lower measured runtime when available;
4. fixed checkpoint ID.

## Diagnosability Definition

Use a fixed nearest-centroid predictor:

- feature: selected checkpoint response signature plus RIPR flags;
- labels: frozen stage and family labels;
- centroids fit only on design mechanisms/groups;
- held-out mechanism/groups used only for evaluation;
- Euclidean distance;
- tie counts as incorrect;
- primary diagnosability: macro-F1 for stage and family separately.

The classifier and tie rule cannot be selected after results.

## MINIMUM Positive / Null Rule

MINIMUM has only two mechanisms per stage, so use both cross-mechanism directions:

- `A -> B`
- `B -> A`

For each direction, report:

- paired group-level effect size `ours - coverage-only`;
- direction consistency;
- group-level bootstrap 95% CI over held-out groups;
- budget usage.

Freeze bootstrap: 10,000 group resamples, seed `20261013`, percentile interval.

`MINIMUM_METHOD_PROMISING` requires all:

1. both directions non-negative for failure coverage and stage/family diagnosability;
2. at least one direction improves one primary metric by `>= 0.05` absolute;
3. pooled group-level CI lower bound is above zero for that improved metric;
4. result remains after removing source-local-only cases;
5. both budgets are satisfied.

`MINIMUM_NO_INCREMENT` if:

- both directions are within `+/-0.02` on every primary metric; or
- a direction reverses sign and no group-level CI excludes zero; or
- the advantage exists only in source-local responses.

## Baselines

- `random-K`
- `manual/default stage-aligned`
- `coverage-only greedy`
- `all-checkpoints`
- `ours = causal/diagnostic greedy`
- `terminal-only`: `NOT_AVAILABLE` unless a comparable final-output monitor already exists in authoritative artifacts; do not invent one.

## DEV Smoke Boundary

The old `216 x 12` matrix may be used only to validate:

- selector implementation;
- hard-budget enforcement;
- deterministic tie rule;
- split and baseline plumbing;
- result schema;
- source-local/downstream separation code paths.

It is `ALGORITHM_SMOKE / DEV_ONLY`, not scientific evidence.

## Materialization Requirements

A future MINIMUM dataset must contain 3 stages, 2 true mechanisms per stage, 8 independent report/table groups per mechanism per stage, 2 injections per mechanism/group, 12 candidate checkpoints, full pre/post state, RIPR flags, oracle response and cost proxies. TARGET is 3 mechanisms per stage, 12 groups per mechanism per stage, 2 injections per mechanism/group.

## Frozen Scope

No automatic checkpoint generation, automatic oracle generation, complete causal discovery, RL, PSO, Stage D training or new scientific claims in this qualification sprint.
