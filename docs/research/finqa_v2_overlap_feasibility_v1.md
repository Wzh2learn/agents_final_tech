# FinQA v2 Overlap Feasibility Audit v1

> Status: `OVERLAP_DESIGN_FEASIBLE` | Read-only eligibility count; no adapter or evaluator execution

## 1. Counts

| Quantity | Count |
|---|---:|
| Records | 7134 |
| Report clusters | 768 |
| Multi-step records | 2894 |
| E candidates | 7134 |
| P candidates | 6794 |
| N candidates | 6929 |
| E1/N overlap records | 6915 |
| P/N overlap records | 6794 |
| E1/N overlap clusters | 768 |
| P/N overlap clusters | 767 |
| E1/N overlap multi-step clusters | 628 |
| P/N overlap multi-step clusters | 628 |

## 2. Decision

Target is at least 24 independent report clusters per stage with overlapping signatures.

`OVERLAP_DESIGN_FEASIBLE`.

The E1 join rule is only a numeric-token feasibility proxy. A causal evidence-to-argument mapping must be frozen separately before any v2 execution. If the overlap counts are below target, do not weaken the overlap criterion or remove ambiguous samples.

## 3. Op families in multi-step subset

`{'add': 1411, 'average': 6, 'compare_larger': 15, 'divide': 2665, 'exp': 6, 'max': 3, 'min': 2, 'minus': 2134, 'multiply': 466, 'sum': 12}`

## 4. Boundary

This is not a FinQA performance result, not a Stage E replication, and not a second-flow experiment. It only determines whether the proposed overlapping design is constructible from the approved staging data.
