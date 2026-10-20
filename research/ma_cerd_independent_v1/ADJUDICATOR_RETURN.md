# Transparent Adjudicator And Graph Return

Status: `TRAIN_CALIBRATED_PUBLIC_INPUT_BASELINE_COMPLETE`

## Method

Use only public MA-CERD inputs:

- `rule_oracle.changed_signature_fields` determines a transparent relation
  rule calibrated on train families;
- `team_state.candidate_features.resource_ids` determines graph impact
  candidates;
- acceptable decisions are the majority decision set for each signature,
  calibrated on train families.

No Gold labels, O2 independent judgment, or O3 simulator outcome are used as
prediction inputs.

## Official Evaluation

| Baseline | Relation | Handling | Impact F1 | Preserved F1 |
|---|---:|---:|---:|---:|
| Base copy | 0.315 | 0.000 | 0.315 | 0.724 |
| All change | 0.685 | 0.813 | 0.445 | 0.104 |
| O1 rule + resource graph | 0.831 | 0.652 | 0.626 | 0.614 |
| Transparent adjudicator + graph | **0.881** | **0.839** | **0.676** | **0.648** |

## Learned Public Rule

- `expired_evidence`, `threshold_violations`, `blocking_requirements` -> `change`
- `plan_decision`, no changed signature -> `invariant`

Handling sets are chosen by train-family majority per signature. This is a
calibrated transparent policy, not a neural or judge model.

## Scientific Meaning

The main bottleneck is now localized:

1. relation can be recovered substantially from explicit signature changes;
2. resource-graph propagation improves impact/preserved localization;
3. handling semantics are largely predictable from the same signature class;
4. residual error is concentrated in cases where O1/O2/O3 disagree or where
   impact propagation is not captured by the resource chain.

This supports a tool-first architecture: deterministic adjudication and graph
propagation should produce the structured plan, while a language model is used
for explanation or cases marked uncertain.

## Boundaries

- The rule was calibrated on MA-CERD train families and evaluated on the
  supplied full release; family-cluster uncertainty is still required for a
  publication claim.
- MA-CERD remains synthetic and simulator-backed.
- This is not a learned experience or feedback effect.
- No model requests, judge, training, paid API or Memory writes were made in
  this baseline.
