# Graph Resource Oracle Return

Status: `O1_ASSISTED_GRAPH_BASELINE_COMPLETE`

## Method

For every MA-CERD record, use only public task inputs plus the explicit O1
rule relation:

- relation: `oracle_bundle.rule_oracle.relation`;
- impact candidates: plan nodes whose `agent_id` appears in
  `team_state.candidate_features.resource_ids`;
- preserved nodes: all remaining plan nodes;
- handling: `repair/defer` for change and the base plan decision for invariant.

This is not O2 or O3 gold and does not use `labels`.

## Official Evaluation

| Metric | Result |
|---|---:|
| Relation accuracy | 0.831 |
| Handling exact match | 0.652 |
| Mean impact-set F1 | 0.626 |
| Mean preserved-set F1 | 0.614 |

For change-only records, the resource-chain impact heuristic reaches about
`0.795` impact F1 and `0.727` preserved F1. The all-record official scores are
lower because invariant records are included and O1 relation disagrees with
the adjudicated Gold relation on part of the release.

## Scientific Reading

The resource graph is useful for node localization, but public task inputs do
not determine the final Gold relation on all records. MA-CERD intentionally
contains substantial O1/O2/O3 disagreement; therefore a graph-only oracle
cannot be expected to reproduce the Gold labels without an explicit
adjudication layer.

The next architecture should separate:

1. graph propagation for impact/preserved candidates;
2. O1 rule comparison for initial relation;
3. an explicit adjudication policy for O1/O2/O3 disagreement;
4. model output limited to decision choice and explanation.

This avoids asking the language model to infer hidden dependency structure.

## Accounting

- Model requests: 0.
- Dataset validation: PASS.
- Predictions: `predictions/graph_resource_oracle.jsonl`.
- No judge, training, paid API or production Memory writes.
