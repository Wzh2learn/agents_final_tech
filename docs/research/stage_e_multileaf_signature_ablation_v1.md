# Stage E Multi-Leaf Signature Ablation v1

> Status: `EXPLORATORY_POST_HOC` | Formal result unchanged | Purpose: quantify the codebook/tautology limitation identified by Loop C

## 1. Feature-set ablation

| Feature set | Macro-F1 | Top-1 | Tie rate |
|---|---:|---:|---:|
| full_vector | 1.0000 | 1.0000 | 0.0000 |
| direct_target_codebook | 1.0000 | 1.0000 | 0.0000 |
| full_without_parse_table_regression | 1.0000 | 1.0000 | 0.0000 |
| full_without_parse_field_hit_rate | 1.0000 | 1.0000 | 0.0000 |
| full_without_qa_source_required | 1.0000 | 1.0000 | 0.0000 |
| full_without_parse_reconcile | 1.0000 | 1.0000 | 0.0000 |
| non_direct_leaves_only | 0.3333 | 0.3333 | 0.6667 |
| any_response_scalar | 0.0000 | 0.0000 | 1.0000 |

## 2. Per-leaf information

| Leaf | M responses | R responses | N responses | Mutual information bits | Single-leaf macro-F1 |
|---|---:|---:|---:|---:|---:|
| parse.doc.ok | 0 | 0 | 0 | 0.0000 | 0.0000 |
| parse.doc.throughput | 0 | 0 | 0 | 0.0000 | 0.0000 |
| parse.field.hit_rate | 72 | 0 | 0 | 0.9183 | 0.3333 |
| parse.reconcile.equations | 0 | 0 | 72 | 0.9183 | 0.3333 |
| parse.table.regression | 72 | 0 | 0 | 0.9183 | 0.3333 |
| qa.citation.judge | 0 | 0 | 0 | 0.0000 | 0.0000 |
| qa.faithfulness.judge | 0 | 0 | 0 | 0.0000 | 0.0000 |
| qa.numeric.exact | 0 | 0 | 0 | 0.0000 | 0.0000 |
| qa.numeric.number_grounding | 0 | 0 | 0 | 0.0000 | 0.0000 |
| qa.refusal.deterministic | 0 | 0 | 0 | 0.0000 | 0.0000 |
| qa.refusal.judge | 0 | 0 | 0 | 0.0000 | 0.0000 |
| qa.retrieval.source_required | 0 | 72 | 0 | 0.9183 | 0.3333 |

## 3. Findings

1. The full 12-leaf vector and the fixed three-direct-leaf codebook both decode all stages perfectly.
2. Non-direct leaves alone identify only the M signature through `parse.table.regression`; R and N become tied/zero-pattern cases.
3. The perfect formal result is therefore driven by a constructed stage codebook, not incremental natural-trace information.
4. `qa.retrieval.source_required` is always 1 for R, while M and N are 0 on that coordinate. Conversely, absence patterns also identify classes under nearest-centroid.
5. This ablation does not invalidate the preregistered result; it narrows its interpretation.

## 4. Claim boundary

Allowed:

> Under the frozen M/R/N controlled injections, the evaluator's constructed checkpoint-response codebook contains stage-localizing information.

Stronger statement now explicitly unsupported:

> A production checkpoint trace or naturally occurring failure can be localized from generalizable visibility dynamics.

`DECIDE NEXT LOOP: STOP_BRANCH` for further analysis of this same perfect codebook. The next useful evidence must use a different dataflow or non-degenerate overlapping signatures.
