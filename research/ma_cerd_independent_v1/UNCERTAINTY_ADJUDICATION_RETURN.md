# Uncertainty Queue Adjudication Return

Status: `FULL_UNCERTAINTY_QUEUE_MODEL_PROBE_COMPLETE`

## Scope

All 250 MA-CERD uncertainty-queue records were evaluated:

- `o1_only_disagrees`;
- or `blocking_requirements`.

The model received only public task evidence, O1/O3 relation signals,
changed-signature fields, and resource-graph impact candidates. No Gold, O2
judgment or O3 impact/preservation labels were exposed.

## Results

| Metric | Model | Transparent adjudicator + graph |
|---|---:|---:|
| Relation accuracy | 0.624 | 0.624 |
| Handling exact match | 0.012 | 0.552 |
| Impact-set F1 | 0.374 | 0.369 |
| Preserved-set F1 | 0.442 | 0.398 |
| Exact match | 0.000 | 0.000 |

All 250 model outputs were schema-valid. The model did not improve relation or
handling and only produced small, non-decisive changes in set F1.

## Scientific Meaning

The uncertainty queue is not solved by simply adding model adjudication:

- relation remains governed by disagreement/signature structure;
- handling semantics remain poorly inferred by the language model;
- graph candidates alone do not provide enough node-level justification;
- model output is not a substitute for explicit dependency propagation or
  adjudication policy.

The high-value architecture remains:

1. transparent signature rule for relation;
2. resource/dependency graph for impact and preservation;
3. calibrated handling policy;
4. explicit abstention or human escalation for the uncertainty queue.

## Ruling

`STOP_MODEL_ADJUDICATION_ON_THIS_QUEUE`.

Do not spend more requests on generic LLM feedback or monolithic prediction
for these cases. The next meaningful experiment would require a richer
dependency/simulator trace or a genuinely different model/tool interface.
