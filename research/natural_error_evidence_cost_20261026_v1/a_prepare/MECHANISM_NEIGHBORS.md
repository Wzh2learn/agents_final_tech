# Mechanism Neighbors

The comparison set is deliberately conventional. No novelty is claimed from `table+text+calculator`, constrained program generation, or generic adaptive retrieval.

| Neighbor | P1 semantic-use signal | P2 evidence-cost signal | Strongest deployable action | Limitation |
|---|---|---|---|---|
| Visible table plus fixed calculator | Rules out malformed JSON and arithmetic-engine defects | Table-only is the cheapest frontier but reaches only 229/507 semantic references | Keep as the execution layer | Does not bind the correct row, period, person, or unit |
| Visible-only label/period/unit resolver plus calculator | Deterministically repairs all five frozen natural failures | Transparent and auditable; no reference row IDs or gold labels enter the resolver | Use latest-minus-previous, inclusive-range, and section-row-plus-named-entity rules | Repairing five examples is not a residual mechanism result |
| Constrained program filter or reranker | Existing non-ordinary arm can change programs but is not a simple deterministic control | Generic constrained decoding is not an evidence-cost frontier | Reject nonnumeric operands before execution | Does not prove semantic-role binding and is not novelty |
| Record-internal top-k table-text retrieval plus calculator | Tests whether missing semantic roles are merely missing context | Small top-k reduces mean context volume but drops the offline semantic ceiling | Keep top-k only as a challenged baseline | Fixed neighbor and top-3 miss legally required paragraph/unit evidence |
| Always-expand plus calculator | Removes input-context loss before judging model use | Legal ceiling 506/507; mean 1866.8 characters, p95 5204, max 9255 | Accept as the final strong baseline | Does not establish a cheaper non-inferior frontier |

Transparent stop/expand was also compared. Its token-coverage rule saves context volume but retains only 293/507 semantic-reference potential, so it is dominated and not a qualified challenger.

P1 and P2 should not be merged into one novelty claim. P1 asks whether a model uses already-visible semantic roles; P2 asks whether record-internal text acquisition can reduce evidence volume without unacceptable answer risk.
