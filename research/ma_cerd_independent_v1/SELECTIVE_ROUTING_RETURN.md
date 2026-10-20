# Selective Routing Analysis

Status: `OFFLINE_ERROR_STRATIFICATION_COMPLETE`

## Finding

The transparent adjudicator is highly reliable outside the
`blocking_requirements` and `o1_only_disagrees` strata.

| Subset | Records | Relation | Handling | Impact F1 | Preserved F1 |
|---|---:|---:|---:|---:|---:|
| High-confidence public-input subset | 750 | 0.967 | 0.935 | 0.779 | 0.731 |
| all_agree + o3_only_disagrees | 831 | 1.000 | 0.901 | 0.754 | 0.672 |
| Uncertainty queue: O1-only disagreement or blocking requirement | 250 | 0.624 | 0.552 | 0.369 | 0.398 |

The largest error concentration is `blocking_requirements`:

- relation accuracy 0.624;
- handling exact match 0.552;
- impact F1 0.369;
- preserved F1 0.398.

## Architecture Consequence

Use selective routing:

1. high-confidence signatures go directly to the transparent graph oracle;
2. `blocking_requirements` and `o1_only_disagrees` go to an uncertainty queue;
3. the next model experiment should spend capacity only on that queue;
4. report coverage and risk separately from full-set accuracy.

This is more valuable than adding another generic feedback arm. It also
matches the MA-CERD claim boundary: disagreement is meaningful evidence and
should be surfaced rather than hidden.

## Next Experiment

Run a small model adjudication study only on the 250-record uncertainty queue,
with the graph oracle output and explicit O1/O3 disagreement as context. The
primary question is whether the model can recover relation/impact decisions
on cases where transparent rules fail, not whether it beats the oracle on
already-solved cases.
