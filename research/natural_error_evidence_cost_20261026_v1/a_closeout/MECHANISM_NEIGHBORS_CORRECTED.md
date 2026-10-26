# Mechanism Neighbors — Corrected

Authority commit: `622b386986ca66c8119263e146f3d3e73c33e260`

## Supersessions

- `SUPERSEDED` — `a_prepare/MECHANISM_NEIGHBORS.md` row 2 says the visible-only resolver “repairs all five frozen natural failures.” The corrected replay is **4/5 overall / 4/4 genuine**, with 0 residual genuine failures after the single visible-axis policy.
- `SUPERSEDED` — the old row-2 limitation quotes `229/507`. The corrected table-only `semantic_reference_potential` is `197/507`, computed by the final row-level replay.
- `SUPERSEDED` — the old transparent-stop figure `293/507` is replaced by `481/507`.

The comparison set remains deliberately conventional. No novelty is claimed from `table+text+calculator`, constrained program generation, or generic adaptive retrieval.

| Neighbor | P1 semantic-use signal | P2 evidence-cost signal | Strongest deployable action | Limitation |
|---|---|---|---|---|
| Visible table plus fixed calculator | Rules out malformed JSON and arithmetic-engine defects | Table-only reaches 197/507 semantic references at 223082 visible characters | Keep as the execution layer | Does not bind the correct row, period, person, or unit |
| Visible-only label/period/unit resolver plus calculator | Deterministically replays 4/5 overall / 4/4 genuine | Transparent and auditable; no reference row IDs or gold labels enter the resolver | Use latest-minus-previous, inclusive-range, and section-row-plus-named-entity rules | The residual after this policy is 0, so this is not a mechanism result |
| Constrained program filter or reranker | Existing non-ordinary arm can change programs but is not a simple deterministic control | Generic constrained decoding is not an evidence-cost frontier | Reject nonnumeric operands before execution | Does not prove semantic-role binding and is not novelty |
| Record-internal top-k table-text retrieval plus calculator | Tests whether missing semantic roles are merely missing context | Small top-k reduces context volume but drops the offline semantic ceiling | Keep top-k only as a challenged baseline | Fixed neighbor and top-3 miss legally required paragraph/unit evidence |
| Always-expand plus calculator | Removes input-context loss before judging model use | Legal ceiling 506/507; total 927751 characters; mean 1829.9, p95 5153, max 9111 | Accept as the final strong baseline | Does not establish a cheaper non-inferior frontier |

## Corrected P2 Replay Figures

| Frontier | semantic_reference_potential | total visible characters | gap vs always-expand (pp) |
|---|---:|---:|---:|
| table_only | 197/507 | 223082 | 60.946746 |
| small_topk_3 | 452/507 | 619687 | 10.650888 |
| fixed_top1_neighbor | 414/507 | 547954 | 18.145957 |
| larger_topk_5 | 486/507 | 773767 | 3.944773 |
| always_expand | 506/507 | 927751 | 0.000000 |
| transparent_stop_expand | 481/507 | 784932 | 4.930966 |

The executed screen's primary proxy is `semantic_reference_potential` over 507 questions. Future model evaluation uses `full_semantic_answer_accuracy` over the 506 complete semantic references.

P1 and P2 must not be merged into one novelty claim. P1 asks whether a model uses already-visible semantic roles; P2 asks whether record-internal text acquisition can reduce evidence volume without unacceptable answer risk.
