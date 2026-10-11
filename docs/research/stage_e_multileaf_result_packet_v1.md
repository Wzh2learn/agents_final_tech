# Stage E Multi-Leaf Result Packet v1

> Evidence class: `CONFIRMATORY_WITH_CONSTRUCT_SENSITIVE_SCOPE` primary + `SECONDARY` structural + `EXPLORATORY` ablation/visualization | Generated after pre-result freeze and independent validation | Paper body not modified

## 1. Primary controlled stage-aligned observability

Primary RQ: **Do checkpoint visibility signatures contain stage-localizing information?**

| Item | Result |
|---|---|
| M/R/N contracts | PASS / PASS / PASS |
| Retained | 72 clusters / 216 injections |
| LOCO macro-F1 | `1.000000` on the explicitly instrumented controlled surface (construct-sensitive) |
| Top-1 accuracy | `1.000000` on the explicitly instrumented controlled surface (construct-sensitive) |
| Metric-specific baselines | chance top-1 `0.333333`; majority macro-F1 `0.166667` |
| Permutation p | `1/10001 = 9.999e-05` for macro-F1 and top-1 |
| Cluster bootstrap 95% CI | macro-F1 `[1.0,1.0]`, top-1 `[1.0,1.0]` |
| Ties / errors | `0 / 0` |
| Leakage audit | PASS |
| Result status | `POSITIVE` |

Allowed claim:

> Preregistered controlled perturbations at mapping, retrieval, and numeric stages induce perfectly separable stage-aligned checkpoint signatures on the explicitly instrumented observation surface.

Primary negative/boundary:

> After directly targeted checkpoints are removed, non-direct top-1 equals chance (`0.3333`), while non-direct macro-F1 equals the uniform-class macro-F1 baseline (`0.3333`) but remains above the plotted majority macro-F1 baseline (`0.1667`). This reflects explicit stage-aligned instrumentation rather than emergent localization from the remaining hierarchy.

Forbidden claims:

- The hierarchy localizes failures.
- Distributed downstream evidence is sufficient for localization.
- Hierarchy itself causes localization.
- The result establishes localization on natural long-horizon tasks.
- Every individual stage has a separately powered confirmatory result.
- The result establishes clean-only matched-FPR protocol superiority.

## 2. Confusion matrix

| True / Pred | M | R | N | Tie |
|---|---:|---:|---:|---:|
| M | 72 | 0 | 0 | 0 |
| R | 0 | 72 | 0 | 0 |
| N | 0 | 0 | 72 | 0 |

## 3. Per-stage visibility and response signatures

| Stage | Direct visibility | Any-response | Responsive leaves | Frozen signature |
|---|---:|---:|---:|---|
| M | 1.0000 | 1.0000 | 2 | `parse.field.hit_rate + parse.table.regression` |
| R | 1.0000 | 1.0000 | 1 | `qa.retrieval.source_required` |
| N | 1.0000 | 1.0000 | 1 | `parse.reconcile.equations` |

Global responsive leaves: `parse.field.hit_rate`, `parse.table.regression`, `qa.retrieval.source_required`, `parse.reconcile.equations`.

`CONFIRMATORY WITH CONSTRUCT-SENSITIVE SCOPE`: four leaf slots respond, but they form three disjoint contract-derived signatures and one of the R predicates is constant. The population breaks the old single-responsive-leaf construction without yet measuring natural visibility dynamics.

`SECONDARY`: all three repeated injections in every cluster share the same response signature; this is repeated-measure consistency, not 216 independent clusters.

## 4. Independent verification

- Independent metric recomputation: `22/22 PASS`.
- Independent deterministic contract audit without importing the formal runner: `216/216 PASS`.
- Numeric reconciliation reimplementation: `decimal.Decimal`.
- Pre-result manifest SHA-256: `15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163`.
- Formal runner SHA-256: `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4`.

These checks validate deterministic construction and metric accounting. They do not constitute an independent semantic scorer.

## 4.1 Loop C fresh-context audit and signature ablation

The independent Loop C audit is `ACCEPTED` for execution integrity, metric recomputation, leakage/repeated-measure accounting and claim scoping. Its strongest surviving attack is that the evaluator writes a disjoint stage codebook from contract/gold predicates, so nearest-centroid can decode stage regardless of natural sample quality.

Post-hoc exploratory ablation confirms the attack:

- full 12-leaf macro-F1: `1.0` on the explicitly instrumented controlled surface (construct-sensitive)
- fixed three-direct-leaf codebook macro-F1: `1.0` on the explicitly instrumented controlled surface (construct-sensitive)
- non-direct leaves only: macro-F1 `0.3333`, top-1 `0.3333`, tie rate `0.6667`
- non-direct top-1 equals the preregistered chance baseline `1/3`; non-direct macro-F1 equals uniform-class macro-F1 `1/3` but is above the plotted majority macro-F1 baseline `1/6`
- any-response scalar: macro-F1 `0.0`, tie rate `1.0`

The frozen key `incremental_information_from_non_direct_leaves=true` only records that direct-codebook macro-F1 is greater than non-direct macro-F1; despite its name, it does not establish incremental information from non-direct leaves. Thus the formal result is valid for the constructed codebook but supplies no demonstrated incremental information from general visibility dynamics. The scientific implication is: **Visibility requires appropriate instrumentation; hierarchy alone does not imply localization.**

## 5. Robustness and error analysis

`POSITIVE` branch checks:

1. **Metric-specific baseline identity:** on the construct-sensitive controlled surface, full-vector macro-F1 `1.0` is above majority macro-F1 `0.1667` and full-vector top-1 `1.0` is above chance top-1 `0.3333`; non-direct top-1 equals chance and non-direct macro-F1 equals uniform-class macro-F1 while remaining above the plotted majority baseline. The primary-result permutation p is at the finite-sample floor.
2. **Repeat consistency:** each cluster contributes three injections with the same stage signature.
3. **Class balance:** 24 clusters and 72 injections per stage.
4. **Tie sensitivity:** zero ties; the strict tie-is-incorrect rule does not change the result.
5. **Leakage:** sample IDs unique, one stage per cluster, M/N UIDs disjoint, expected stages fixed before results.
6. **Independent recomputation:** metrics and deterministic contracts reproduce from stored artifacts.

Primary limitation:

> Perfect separability is expected to a substantial degree because the controlled injections target distinct frozen direct leaves. The experiment validates stage-localizing information in the constructed checkpoint-response codebook, but it does not estimate natural-failure localization accuracy or incremental information beyond that codebook.

No conventional error rows exist in this run, so error taxonomy is `NOT AVAILABLE`; the key negative evidence is the absence of natural signature overlap rather than classifier mistakes.

## 6. Flat versus hierarchy secondary analysis

| Diagnostic | Result |
|---|---:|
| Pearson correlation | `0.931305` |
| Spearman ranking correlation | `0.866025` |
| Linear fit | `h = 1.409091 f - 0.075758` |
| R2 | `0.867329` |
| Max absolute residual | `0.265152` |
| Flat support | `{0.833333, 1.666667}` |
| Hierarchical support | `{0.833333, 1.363636, 2.272727}` |
| Flat / hierarchical AUROC | `1.0 / 1.0` |
| Clean-only matched operating point | `NOT_IDENTIFIABLE_CLEAN_SUPPORT_ZERO` |
| Single-leaf affine degeneracy broken | `YES` |

`SECONDARY`: multi-leaf responses break the exact single-leaf affine relation, but this does not establish hierarchical superiority. Both AUROCs remain perfect on the controlled clean-versus-injected separation, while clean score support remains zero and matched-FPR operating-point identification remains blocked.

## 7. Evidence grading

### PRIMARY: CONTROLLED STAGE-ALIGNED OBSERVABILITY

- Frozen M/R/N contract success.
- Preregistered mapping/retrieval/numeric perturbations induce perfectly separable stage-aligned signatures on the explicitly instrumented observation surface.
- This is a property of the controlled observation surface, not arbitrary production traces.
- LOCO full-vector macro-F1/top-1 `1.0` on the explicitly instrumented controlled surface, above the metric-specific majority/chance baselines; construct-sensitive scope retained.
- Permutation and cluster-bootstrap verification.

### SECONDARY

- Per-stage visibility profiles.
- Four responsive leaves and disjoint signatures.
- Flat/hierarchy non-affine structure under multi-leaf responses.
- Historical clean-only matched-FPR non-identifiability remains unchanged.

### EXPLORATORY

- Response-signature heatmap.
- Flat/hierarchy score scatter.
- Propagation depth, first-visible distance and silent absorption remain unexecuted.

### NEGATIVE / BOUNDARY

- After directly targeted checkpoints are removed, non-direct top-1 equals chance (`0.3333`), while non-direct macro-F1 equals uniform-class macro-F1 (`0.3333`) and remains above the plotted majority macro-F1 baseline (`0.1667`); the remaining hierarchy does not provide emergent localization.
- Perfect separation is design-sensitive and is reproduced by the direct-target codebook alone.
- R-stage response is contract-written and forms a disjoint constant signature; absence patterns also encode class under nearest-centroid.
- No natural cross-stage ambiguity is measured.
- Per-stage claims are descriptive at TARGET sample size.
- Clean-only matched operating point is still not identifiable.
- A deterministic independent observation-reproduction scorer prototype is unit-tested, but `SCORER_GO` is not frozen; semantic process correctness remains unmeasured.

## 8. Version-B Paper E evidence map

| Contribution component | Evidence status | Allowed wording |
|---|---|---|
| Construct separation | `CURRENTLY SUPPORTED` | visibility, detection and harmfulness are distinct |
| Quantified observation boundary | `CURRENTLY SUPPORTED` | family/overall/worst-case visibility and conditional detection |
| Structural protocol identifiability | `CURRENTLY SUPPORTED` | affine/rank result in old single-leaf case; clean-only equality unidentified |
| Multi-stage checkpoint signatures | `NEW CONFIRMATORY_WITH_CONSTRUCT_SENSITIVE_SCOPE` | M/R/N controlled codebook signatures are stage-specific |
| Stage-localizing information | `NEW CONFIRMATORY WITH SCOPE` | constructed checkpoint-response codebook contains stage-localizing information under frozen controlled injections |
| Hierarchy localization | `FORBIDDEN` | not supported |
| External/general natural-task localization | `FUTURE` | requires second dataflow and non-degenerate signatures |

## 9. Figure/table candidates

1. **Table:** M/R/N contract and retained-unit summary.
2. **Table:** per-stage direct visibility and responsive leaves.
3. **Figure:** binary response-signature heatmap ordered by frozen leaf tree.
4. **Table:** confusion matrix with tie column.
5. **Figure:** flat versus hierarchical multi-leaf score scatter, annotated with non-affine residual.
6. **Table:** primary metrics versus metric-specific chance/majority baselines with permutation p and cluster CI.

## 10. Reviewer-attack matrix

| Attack | Response | Residual limitation |
|---|---|---|
| Localization is tautological | Gold is fixed before results; predictor is frozen and outcome-blind | Direct leaves are stage-specific by construction; direct codebook alone is perfect |
| Perfect result implies generalization | Claim is restricted to frozen controlled injections | Natural-task performance unknown |
| Repeated injections inflate n | 72 clusters are independent units; 216 injections are repeated measures | Per-stage power remains limited |
| Hierarchy is claimed superior | Flat/hierarchy is secondary and no superiority claim is made | Matched operating point remains unidentified |
| Shared implementation bias | Independent metric and Decimal contract audits reproduce results | No semantic second scorer |
| Post-hoc tuning | Pre-result hash receipt precedes result creation | Any future changed contract needs a new namespace |

## 11. Graph-loop decision

`DECIDE NEXT LOOP: CONTINUE`

Stop analyzing the same perfect codebook. The next evidence must use a different dataflow or non-degenerate overlapping signatures, with feature extraction independent of the gold stage label. Do not tune the predictor, aggregation or mutation rules on this result.
