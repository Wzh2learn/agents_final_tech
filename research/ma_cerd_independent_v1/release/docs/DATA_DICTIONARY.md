# Data Dictionary

## Record identity and grouping

- `contract_id`: unique public benchmark record identifier.
- `base_case_id`: identifier shared by interventions derived from one base case.
- `family_id`: source family used as the statistical and leakage-control unit.
- `split_group_id`: connected grouping that must remain within one partition.
- `scenario_family`: scenario stratum.
- `partition`: `train`, `development`, or `test`.
- `split`: evaluation regime such as `id` or `compositional_ood`.

## Paired input

- `base_snapshot`: requirements, evidence, team state, and original joint plan.
- `intervention`: exactly one semantic change with target, path, before/after values, and generator metadata.
- `counterfactual_snapshot`: base snapshot after the declared intervention.

## Gold labels

- `labels.relation`: `change` or `invariant` in this release. The schema also supports `undetermined`.
- `labels.acceptable_decisions`: non-empty subset of `execute`, `repair`, and `defer`.
- `labels.impact_node_ids`: plan nodes affected by the intervention.
- `labels.preserved_node_ids`: plan nodes expected to remain unchanged.
- `labels.rationale_refs`: anonymized requirement, evidence, plan, or case references.

Impact and preserved sets are disjoint and together cover every base-plan node.

## Oracle bundle

- `rule_oracle`: deterministic O1 comparison and hashes.
- `independent_judgment`: anonymized O2 result. It retains reviewer count, blinding, final label, admissible handling, localization, and public adjudication ID; identities and raw responses are withheld.
- `simulator_outcome`: O3 paired shadow result, relation, outcome, seed, trace hash, and simulator version.
- `alignment`: relationship among O1, O2, and O3 (`all_agree`, `o1_only_disagrees`, `o2_only_disagrees`, or `o3_only_disagrees`).

## Provenance

- `provenance`: generator, requirement-library version, timestamp, seed, and source commit.
- `release_status`: `gold` for every released record.
