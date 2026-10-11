# Stage E Multi-Leaf Preregistration v1

> 状态: `MULTILEAF_READY_FOR_EXECUTION_NOT_AUTHORIZED` | 更新: 2026-10-10 | 取代/被取代: 本件冻结 M/R/N gold、样本生成、primary predictor 和 task card；旧 `stage_e_multileaf_protocol_v2.md` 保留为历史设计，不作为当前 primary；正式实验未运行

`FACT`: the current scientific question is **Do checkpoint visibility signatures contain stage-localizing information?** The first experiment does not claim that a hierarchy itself localizes failures.

## 1. Frozen estimand and unit

- Gold label: `expected first affected stage`, fixed from injection location plus pipeline consumption order before any checkpoint score or visibility result is read.
- Stage classes: `M` mapping/schema, `R` retrieval/grounding, `N` numeric/reconciliation.
- Independent unit: stage-namespaced table/document/origin cluster.
- Repeated unit: three deterministic injections within a cluster.
- Target population freeze: 24 clusters per stage, 3 injections per cluster, 216 injections total.
- Outcome-blind selection: ascending SHA-256 rank under seed `20261010`; the generator does not read Stage E visibility, detection, harmfulness or evaluator output.

Machine-readable freeze: [`multileaf_freeze.json`](../../research/stage_e_method_revision_20261009/multileaf_freeze.json). The JSON records source hashes, generator hash, exact sample IDs and generation smoke outcomes.

## 2. Stage M: mapping/schema

| Field | Frozen contract |
|---|---|
| Real input object | Full public table objects in `data/research/drift_v0/input/tatqa_tables.json`; table UID and table hash are recorded per sample |
| Injection operation | Replace one non-empty first-row header token with deterministic out-of-vocabulary token `__MUTANT_<hash8>__` |
| Injection location | Header/canonical mapping input before production `map_headers` |
| Expected first checkpoint | `parse.field.hit_rate` |
| Direct target leaf | `parse.field.hit_rate` |
| Potential downstream leaves | `parse.table.regression`; `parse.doc.ok` |
| Pipeline support | Production matcher is present in `scripts/m1_statement_parser.py`; the freeze generator materializes the mutation without inspecting scores |
| Adapter | Existing production mapping path; no LLM/judge |
| Deterministic generation | Yes; 24 distinct table UIDs and three distinct header cells per UID |
| Sample source | Outcome-blind stable-hash selection from the original table universe |
| Exclusion | Fewer than three eligible first-row header cells; malformed table; duplicate UID |
| Harmfulness | `NOT_YET_DEFINED_EQUIVALENCE_DEPENDENT`; old H/HI/E is not imported |
| Success | Direct leaf changes in the predeclared failure direction and M is predicted from the full response vector |
| Null | Leaves respond but M/R/N signatures do not separate above baseline |
| Failure | Contract violation, missing expected response, or fewer than two population-responsive leaves |

`FACT`: M does not reuse old Stage E results to select samples. It uses the original input table universe and ignores all result fields.

## 3. Stage R: retrieval/grounding

| Field | Frozen contract |
|---|---|
| Real input object | TAT-DQA raw question with `block_mapping` source-block IDs and line spans |
| Required source passage | The complete frozen `block_mapping` set for the selected question; no inferred or judge-selected passage |
| Injection operation | Remove all required source blocks from the retrieval candidate bundle |
| Injection location | Retrieval evidence bundle before answer generation |
| Expected first checkpoint | `qa.retrieval.source_required` |
| Why first | Pipeline contract first tests whether required source evidence is present; faithfulness/citation/numeric leaves consume later answer evidence |
| Direct target leaf | `qa.retrieval.source_required` |
| Potential downstream leaves | `qa.faithfulness.judge`; `qa.numeric.number_grounding`; `qa.citation.judge` |
| Task semantics | Question, answer, answer type and gold block IDs are hash-frozen and unchanged; only evidence availability changes |
| Pipeline support | `scripts/run_tat_dqa_m2_upper_bound.py` already computes expected block IDs and evidence-hit checks |
| Adapter | Deterministic evidence-bundle removal; no model or judge in generation |
| Leakage protection | Stable source-ID hash selection; no retrieval output is read; gold blocks are frozen before perturbation |
| Exclusion | Missing source bundle, empty/ambiguous `block_mapping`, question/answer change, or more than one required evidence interpretation |
| Harmfulness | `NOT_YET_DEFINED_DO_NOT_REUSE_STAGE_E_H_HI_E` |
| Success | `source_required` fails on the injected bundle while question/answer hashes remain unchanged |
| Null | Evidence is absent but R signatures do not separate above baseline |
| Failure | Any semantic mutation outside evidence availability or an ambiguous gold block set |

`VALUE`: removing required evidence is a retrieval-availability failure, not a relabeling of the answer. If a future implementation changes the question or gold answer instead, the sample is `R_STAGE_NO_GO`.

## 4. Stage N: numeric/reconciliation

| Field | Frozen contract |
|---|---|
| Real input object | Full public TAT-QA table object with a deterministic row-total or column-total identity |
| Numeric identity | A pre-mutation row/column sum whose operands and RHS all parse numerically and satisfy `abs(lhs-rhs)<=0.01` |
| Injection operation | Mutate one numeric operand by at least `max(1% of magnitude, 0.02)`, strictly exceeding the `0.01` identity tolerance while keeping labels, schema, row/column shape and identity definition unchanged |
| Injection location | Numeric table input before reconciliation |
| Expected first checkpoint | `parse.reconcile.equations` |
| Why first | `reconcile` consumes parsed numeric table records before numeric QA and final output |
| Direct target leaf | `parse.reconcile.equations` |
| Potential downstream leaves | `qa.numeric.exact`; `qa.numeric.number_grounding`; final output |
| Pipeline support | `src/biz/m1_statement_parser.py::reconcile` plus the frozen deterministic identity checker in `build_multileaf_freeze.py` |
| Deterministic checker | Yes; original identity must pass and mutated identity must fail in generation smoke |
| Final answer | May change if the operand is answer-relevant; final-answer change is not localization gold |
| Exclusion | No valid identity before mutation, mutation does not break identity, non-numeric target, shape change, or multiple equivalent identities |
| Harmfulness | `NOT_YET_DEFINED_EQUIVALENCE_AND_QUESTION_DEPENDENT` |
| Success | Original identity passes, mutated identity fails, and N is predicted from the full response vector |
| Null | Identity fails but N signatures do not separate above baseline |
| Failure | Any mutation-contract violation or an uninterpretable downstream answer effect |

`FACT`: N uses a deterministic derived reconciliation identity. It is not represented as a native human annotation.

## 5. Minimum mechanism requirement

- Two responsive leaves are required to break the current single-global-affine-signal degeneracy.
- Three independent stage classes are required to test stage localization.
- Every injection need not change multiple leaves; the population must contain responsive leaves across M/R/N.
- M/R/N are population-level signature classes. The experiment does not require each table to pass through all three stages.

## 6. Frozen primary predictor

Input vector:

1. Take all leaves from `config/eval_checkpoint_trees.json` in frozen tree order.
2. For each cluster/injection, encode `1` when the paired leaf response is nonzero in the preregistered direction and `0` otherwise.
3. Missing evidence is encoded `0` and separately counted; it is never silently treated as a successful response.

Classifier:

- Deterministic nearest-centroid.
- Euclidean distance on binary response vectors.
- Leave-one-origin/table-cluster-out validation.
- Training centroids use only the other clusters in the same fold.
- Classes are exactly `M/R/N`.

Tie rule:

- A distance tie is scored incorrect.
- Lexical `M/R/N` order is used only to serialize a deterministic output; it cannot rescue a tied prediction.

Baselines:

- Chance top-1: `1/3`, valid because the frozen sample is balanced.
- Majority-stage baseline: always predict frozen first class `M`; top-1 `1/3`, macro-F1 `1/6` on the balanced freeze.
- If any stage becomes unbalanced before execution, chance is recomputed from the observed class prior and `1/3` may not be claimed.

## 7. Metrics and claim boundary

Primary evidence for signature separability:

- Leave-one-cluster-out macro-F1.
- Compare with a cluster-label permutation null at two-sided `alpha=.05`, using seed `20261011` and 10,000 permutations.

Co-primary localization endpoint:

- Top-1 stage accuracy with a table/origin-cluster bootstrap 95% interval, using seed `20261012` and 10,000 replicates.
- The lower interval bound must exceed the frozen chance/majority baseline.

Descriptive:

- Per-stage visibility profile.
- Per-class confusion matrix.

Exploratory only:

- top-k localization;
- first-visible-stage distance;
- propagation depth;
- silent-absorption stage.

Allowed successful claim:

> Checkpoint visibility signatures contain stage-localizing information.

Not allowed from this experiment:

> The hierarchy localizes failures.

The latter requires a future explicit hierarchy-derived predictor and a separate validation.

Localization remains unestablished if either primary condition fails, if only one/two leaves respond, if gold changes after scoring, or if any leakage is found.

## 8. Formal execution task card

Status: `READY_TO_EXECUTE_NEEDS_USER_APPROVAL`; this preregistration does not authorize execution.

1. Verify `multileaf_freeze.json` source/generator hashes.
2. Materialize paired clean/injected artifacts from the frozen sample IDs only.
3. Run deterministic M/R/N target checks without model/judge calls.
4. Run the fixed checkpoint aggregation over the frozen leaf order.
5. Verify the already frozen permutation/bootstrap seeds and replicate counts before inspecting class performance.
6. Execute leave-one-cluster-out nearest-centroid analysis.
7. Report macro-F1, permutation p-value, top-1 accuracy and cluster interval, per-stage confusion matrix and contract failures.
8. Stop and report `MULTILEAF_BLOCKED` if fewer than two population-responsive leaves or any expected-stage contract fails.

GPU/API requirement for the deterministic fixture: `0/0`. Any judge-based downstream leaf requires a separately approved resource plan.

## 9. Gate

`MULTILEAF_READY_FOR_EXECUTION`

The sample freeze, gold, predictor and decision rules are complete before formal scoring. Formal execution remains unrun and requires explicit user approval.
