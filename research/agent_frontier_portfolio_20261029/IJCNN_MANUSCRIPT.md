# Learning to Correct and Escalate from Shared Execution-State Feedback

> Writing draft v0 · 2026-11-18. Quantitative claims use frozen native executions and cached paired analyses. [Complete experiment tables](results/IJCNN_EXPERIMENT_TABLES.md) · [Implementation and historical evidence](results/FINQA_CORRECTION_METHOD.md). This is the current manuscript; the longer method record remains an evidence source.

## Abstract

Execution feedback can confirm that a program runs without establishing that it uses the correct quantities, periods or units. A correction agent must therefore learn both how to repair an answer and when to preserve existing progress. We study these decisions in a two-stage framework for financial document question answering. First, execution-validated program counterexamples supervise the same task before and after a successful recovery, with a fixed auxiliary-loss budget. Second, a separate utility predictor learns the gain or harm of teacher escalation by pairing one fixed-input teacher trajectory with multiple executed local states. On a source-isolated FinQA confirmation cohort, local correction improves ordinary supervised fine-tuning from 34/64 to 39/64 native successes; 18 teacher acquisitions reach 42/64. Eight acquisitions match the 41/64 successes of always invoking the raw teacher while using 84.0% fewer teacher tokens. Matched state-diversity controls show small gains, while an earlier confirmation cohort and prospective TAT-QA transfer expose limits. A paired teacher-information diagnostic further shows that fewer harmful revisions can coincide with fewer recoveries. The results connect correction learning, preservation and budgeted intervention through realized execution outcomes.

## I. Introduction

Financial document questions often require a model to select quantities from text and tables, bind them to the correct reporting period, and compose a numerical program. FinQA and TAT-QA provide concrete settings for studying these requirements [1, 2]. An execution tool can reject an invalid reference or evaluate an arithmetic expression. It usually cannot tell the acting model that a valid result came from the wrong year, a pretax rather than after-tax quantity, or an omitted unit conversion. Successful correction consequently requires semantic decisions beyond repairing syntax.

Correction also creates a preservation problem. Additional reasoning or a stronger model may repair an incorrect answer, but may replace an already correct one with an error. Error detection and intervention value therefore differ. Selective escalation has already been studied through confidence-based model switching and recoverability-aware routing [3, 4]. Our question concerns the learning signal available after an agent has produced and executed a local correction: how can execution experience teach both preservation and the value of further intervention?

We use two separately optimized components. A local corrector receives execution-validated counterexamples in paired pre-recovery and post-recovery contexts. A utility predictor then estimates the correctness change from acquiring a teacher answer relative to retaining that local result. Teacher labeling uses a deliberately fixed original snapshot. One realized teacher trajectory can consequently label multiple executed local states of the same source, with source-level averaging preventing a source with more views from receiving more optimizer updates.

The contribution lies in these supervision rules and their controlled evaluation. We compare the paired-state corrector with positive-only and one-sided controls, and compare multi-state utility supervision with repeated single-state supervision under the same teacher sources, optimizer updates and forward-pass counts. Frozen budget curves, prospective transfer and a teacher-information intervention locate where the learned policies help and where they fail. The resulting argument centers on learned correction and intervention, with successful task execution as the outcome.

## II. Related Work

**Learning correction and preservation.** SCoRe trains multi-turn self-correction with online reinforcement learning and identifies limitations of offline correction traces [5]. Yang et al. [8] separate confidence in correct answers from the ability to repair wrong ones. STeP trains agents using teacher-corrected trajectories and partial masking of error steps [9]. CRINGE develops token-level contrastive learning from undesirable outputs [6]. Within these established families, our stage-A comparison changes the allocation of the same execution-validated wrong-program counterexamples across witnessed pre-recovery and post-recovery contexts, keeping the positive demonstrations and total auxiliary weight fixed.

**Selective escalation.** AutoMix uses answer generation, self-verification and model routing [3]. RASER predicts whether additional retrieval is worthwhile using features of a one-shot answer [4]. These works establish that routing should consider potential benefit rather than simply invoke more expensive computation. Here, the decision conditions on an already executed local program, and its target explicitly distinguishes recovery, damage and unchanged correctness. Our risk control is a matched implementation of local-error prediction, rather than a reproduction of either full routing system.

**Supervision from multiple observations.** DARS constructs routing supervision from repeated query rewrites and decoding observations to estimate capability distributions [7]. We vary a different object: the executed local program state within a source, while sharing one fixed-input teacher trajectory. These views expose how intervention value changes with existing progress; they do not supply independent teacher samples or estimate teacher decoding variance. The single-state control repeats its one real state to match the multi-state model's number of forward passes.

## III. Problem and Method

### A. Public execution states and intervention value

Let $x$ contain a question and its public table/text evidence. The executor returns $E(p,x)$, comprising program validity and observed numerical results. A frozen first-pass actor produces $p^0$. The local corrector produces $L$, yielding a public decision state

$$
s=(x,p^0,E(p^0,x),L,E(L,x)).
\tag{1}
$$

Reference answers and correctness labels are absent from the acting model's input. During training, $C(p)$ denotes host-side execution correctness: a valid program whose result matches the dataset reference under its numerical and unit contract. Native evaluation additionally requires normal agent completion, as specified below.

The main teacher policy $T_0(x,p^0)$ starts from the original snapshot. A fixed controller $G$ combines its proposal with the existing local result. The realized intervention label is

$$
r(s,T_0)=C(G(L,T_0(x,p^0)))-C(L)\in\{-1,0,+1\}.
\tag{2}
$$

Following the correctness-transition view of [8], let $q(s)$ be the probability that the local result is wrong, $a(s)$ the recovery probability conditional on a wrong local result, and $b(s)$ the damage probability conditional on a correct local result. Expected correctness gain from teacher intervention then decomposes as

$$
V(s)=q(s)a(s)-[1-q(s)]b(s).
\tag{3}
$$

An error-risk predictor concerns $q$. A useful escalation policy must also account for recoverability and damage. Equation (3) motivates the outcome target; the implementation does not train three separate heads.

### B. Paired execution-state correction

For a successful training recovery, $s_i^-$ is the actual failed public state and $s_i^+$ is the state after the verified recovery. Positive targets retain the original financial explanation and executable declaration. Correct source episodes contribute preservation targets without a fabricated repair.

Counterexamples are formed by backsliding program edits from the successful program toward the original attempt. We execute each candidate, retain valid wrong-result programs, and exclude invalid or answer-equivalent candidates. For each context and wrong program, the positive and negative declarations share a prefix up to their first token disagreement. At that position, a token-margin loss is

$$
\ell_{\mathrm{neg}}(s,\mathcal B_i)=
\frac{1}{|\mathcal B_i(s)|}
\sum_{(h,u^+,u^-)\in\mathcal B_i(s)}
\operatorname{softplus}\!\left(m+z_\theta(u^-\mid h)-z_\theta(u^+\mid h)\right).
\tag{4}
$$

The set contains deduplicated context-specific disagreement points; an empty set contributes zero. The source objective is

$$
\mathcal L_i^A=\mathcal L_{\mathrm{CE},i}
+\lambda\left[\rho\ell_{\mathrm{neg}}(s_i^-,\mathcal B_i)
+(1-\rho)\ell_{\mathrm{neg}}(s_i^+,\mathcal B_i)\right],
\quad \lambda=0.1,\ \rho=0.5,\ m=1.
\tag{5}
$$

Positive cross-entropy averages supervised tokens within a source. The one-sided control uses $\rho=1$; ordinary SFT uses $\lambda=0$. Counterexample-bearing sources receive the same total auxiliary weight in both contrastive conditions. Since the disagreement tokens have an identical prefix, their log-probability difference equals their logit difference. The loss reuses the positive forward pass.

The stage-A comparison contains 88 source groups: 59 recovery pairs and 29 preservation sources, yielding 147 positive targets, with counterexamples in 54 groups. Demonstration formation includes reference-assisted TRAIN recoveries and successful execution witnesses. Student inputs contain only the public task, program and execution state. All three arms share initialization, demonstrations, token masks and 264 optimizer updates.

### C. Shared-teacher supervision over executed states

For each labeling source $i$, we collect one actual teacher trajectory $t_i=T_0(x_i,p_i^0)$. Its input does not depend on which local view is later chosen. Existing execution experience supplies distinct local programs $L_{iv}$, including original attempts, actual local corrections, failed proposals, successful witnesses and executed partial repairs. Duplicate programs within a source are removed.

Each view is executed and labeled by

$$
r_{iv}=C(G(L_{iv},t_i))-C(L_{iv}).
\tag{6}
$$

We encode damage, benefit and unchanged correctness as short JSON outcome sequences A, B and N. Let $\ell_\phi(s,t(y))$ be the mean negative log-likelihood over all supervised tokens of that sequence, including its formatting tokens. With $I$ labeling sources and $J$ replay sources,

$$
\mathcal L^B(\phi)=\frac{1}{I+J}
\left[
\sum_{i=1}^{I}\frac{1}{|\mathcal V_i|}
\sum_{v\in\mathcal V_i}\ell_\phi(s_{iv},t(y_{iv}))
+\sum_{j=1}^{J}\mathcal L_{\mathrm{replay},j}(\phi)
\right].
\tag{7}
$$

The labeling pool has 96 teacher trajectories and 252 distinct local-state views; 45 sources change outcome label across their views. Training also retains 121 replay groups. Source-group gradient accumulation gives 434 updates and 894 forward passes over two epochs. The single-state control repeats its one actual local view according to the original group size, matching these counts. Existing state formation and replay costs remain part of the recorded upstream work; sharing the labeling trajectory does not make those states free.

The utility adapter starts from the paired corrector but is optimized separately. At inference, one neural prefill reads logits at the common JSON class position. Renormalizing the A/B/N logits gives

$$
g_\phi(s)=\widetilde P_\phi(B\mid s)-\widetilde P_\phi(A\mid s).
\tag{8}
$$

For a task budget $K$, we rank states by $g_\phi$. The at-most-$K$ rule retains positive scores; fixed-quota comparisons take the first $K$ states. This maximizes the sum of predicted gains under an additive task-count constraint, rather than a predicted token-cost constraint. The raw response is obtained only for selected states.

The FinQA controller retains the local program if the teacher does not complete normally, submits an invalid program, or differs from the local program only by one terminal factor-of-100 conversion with the same parsed core. Otherwise it adopts the teacher proposal. TAT-QA additionally predicts a scale; the factor-of-100 retention rule applies only when the two predicted scales agree. G is a deterministic baseline component used by all selected-policy comparisons.

### D. Training and deployment algorithms

**Algorithm 1: Learning from execution experience**

~~~text
Input: TRAIN recovery/preservation witnesses, existing executed local states,
       common initialization, original-snapshot teacher T0
1. For each recovery source, execute candidate backslides and retain valid wrong ones.
2. Encode the same positive demonstration and wrong-program family in its
   pre-recovery and post-recovery public contexts.
3. Train the local corrector with source-averaged CE and Equation (5).
4. For each labeling source, execute T0 once from its original snapshot.
5. Pair that result with each deduplicated, executed local view; compute (6).
6. Train a separate utility adapter with the source-grouped objective (7).
Output: fixed local-correction and utility adapters, fixed controller G.
~~~

**Algorithm 2: Budgeted native correction and escalation**

~~~text
Input: N public tasks and saved first-pass states; frozen adapters; budget K
1. Run the local corrector on each saved state and execute its submitted program.
2. Form each public state s and obtain one utility readout g_phi(s).
3. Freeze the selected top-K set, using the declared fixed-quota/positive-score rule.
4. For each selected task, run T0 from the original snapshot under the common cap.
5. Return G(local, teacher) for selected tasks; preserve local results otherwise.
~~~

A deployment batch uses $N$ local correction episodes, $N$ utility prefills and at most $K$ teacher episodes; episodes can contain multiple HTTP requests. Sorting costs $O(N\log N)$. For an existing pool of $M=\sum_i|\mathcal V_i|$ states, label construction uses $I$ teacher trajectories and $M$ local executions. This count excludes the earlier work needed to form that state pool.

## IV. Experimental Protocol

We ask: RQ1, does paired-state supervision improve native correction relative to matched positive-only and one-sided training? RQ2, does state diversity improve utility learning at fixed teacher sources and update/forward counts? RQ3, how do the effects depend on acquisition budget, dataset and teacher information?

**Cohorts.** FinQA DEV64 is an internal development subset drawn from the official test snapshot and extensively exposed during development. An earlier 53-source confirmation uses the remaining eligible company/year groups from that snapshot. Both follow the original fixed source-hash order and eligibility rule requiring at least two annotated program steps, with one question per group. The prospective 57-source cohort comes from previously unused TRAIN sources at its execution time. These 57 were later used in a separate, non-adopted expansion; the reported results retain the earlier frozen checkpoints. The final confirmation64 is a project company/year holdout drawn from official TRAIN, isolated from the training construction and earlier exposure inventory. These names describe project roles, not the official benchmark's complete splits.

For TAT-QA, we evaluate 32 development table contexts and then 32 previously unexecuted contexts from official dev, one arithmetic question per table. The latter are selected by public UID order, excluding the earlier tables, before model execution. Prompts, checkpoints, controller and primary budget remain fixed. All 32 are retained regardless of interim results; TAT references and teacher outputs never enter training.

**Agents and scoring.** The actor is OpenCode with the frozen Qwen3-8B checkpoints and a common numerical-program tool. The native actor uses the HF-bound BF16 GGUF parent; the utility readout uses the HF model with its separate LoRA adapter. The actual adapter targets are q_proj and v_proj, rank 8, alpha 16, dropout 0, with learning rate $2\times10^{-4}$. Local sampling uses temperature 0.2, seed 17, a 32,768-token context and 8,192-token output cap. The remote teacher is the campus endpoint's deepseek-v4-flash model identifier. Main evaluation episodes share the same 12-POST/300-second cap; the separately labeled 12+8 feasibility probe used a 6-POST/90-second cap.

Native success requires normal agent completion, a valid final program and a correct executed answer. FinQA compares the executor result with the supplied execution answer after five-decimal canonicalization. TAT-QA uses official arithmetic exact match with the predicted scale; scale exactness is recorded separately. The actors observe their actual execution results, not correctness flags. The shared functional DSL permits earlier-step references and rejects nested function calls.

**Controls and costs.** We report ordinary SFT, one-sided counterexamples, paired-state correction, equal-weight positive-state SFT, and the half-weight one-sided control for stage A. Escalation controls use matched error-risk supervision, repeated single-state utility supervision, a frozen random allocation, raw always-teacher output, and always-teacher with G. Learned risk controls are mechanistic adaptations, rather than full reproductions of published routing pipelines.

Primary budgets are 18/16/18 for the three stage-B FinQA cohorts and 9 for each TAT cohort. The FinQA budget curves include every $K$, with original primary points retained. Selected policies share identical-input realized teacher responses, so their comparisons do not depend on separate teacher samples for overlapping tasks. Actual new teacher acquisition cost is charged once; each policy's deployment cost uses its selected subset.

We separate local generation, utility prefills, teacher requests/tokens, training and formation. Cached input is a subset of provider input, not an additional token total. Unknown usage is retained with its reserve. Classifier loading/preprocessing time and neural-forward time are reported separately. Earlier confirmation timing included a disclosed model-residency overlap; it is not treated as a clean end-to-end latency benchmark.

Paired intervals resample one frozen outcome difference per source, using 20,000 percentile-bootstrap draws. New summaries use seed 171118; the existing early53 analysis retains seed 17053. Intervals condition on the training fit and realized teacher pool, assume source-level independence, and are unadjusted across comparisons.

## V. Results

**Table 1. Native successes at the frozen primary task budgets.** SFT is ordinary correction, Pair is paired-state correction, and Value/Risk/Single/Random retain Pair on unselected tasks. Teacher columns use the same realized pool as the corresponding policy comparisons. A dash denotes an unmeasured condition.

| Panel (N) | K | SFT | Pair | Value | Risk | Single | Random | All T0 | All T0+G |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FinQA development (64) | 18 | 33 | 37 | 41 | 41 | 40 | 41 | 40 | 44 |
| FinQA early confirmation (53) | — | 30 | 30 | — | — | — | — | — | — |
| FinQA prospective (57) | 16 | 32 | 32 | 35 | 33 | 33 | 35 | 32 | 37 |
| FinQA final confirmation (64) | 18 | 34 | 39 | 42 | 43 | 41 | 41 | 41 | 44 |
| TAT-QA development transfer (32) | 9 | 5 | 7 | 11 | 13 | — | 13 | 19 | 19 |
| TAT-QA prospective transfer (32) | 9 | 12 | 9 | 11 | 10 | — | 12 | 15 | 15 |

**Local correction.** On DEV64, ordinary SFT, one-sided counterexamples and paired-state counterexamples obtain 33, 29 and 37 successes. The half-weight one-sided and equal-weight positive-state controls obtain 32 and 31. With fixed positive content and auxiliary weight, the results support changing where counterexample supervision is applied. On confirmation64, the paired corrector reaches 39 versus ordinary SFT's 34, with six paired-only successes and one ordinary-only success. The difference is 7.8 percentage points, with a conditional paired interval of [0.0, 15.6]. Earlier confirmation53 gives 30 versus 30; prospective57 gives 32 versus 32. The effect is therefore not consistent across all source cohorts.

**Utility learning and budget.** At the frozen primary budgets, multi-state utility yields 41/64, 35/57 and 42/64, compared with repeated single-state supervision's 40/64, 33/57 and 41/64. The confirmation difference of one task has interval [-4.7, 7.8] percentage points. Against ordinary SFT, the complete confirmation pipeline has eight paired-only successes and no ordinary-only success: +12.5 points [4.7, 21.9].

Matched error-risk escalation obtains 41, 33 and 43 at these primary points. Multi-state utility leads risk on all three FinQA panels at the common secondary $K=8$, but the full curves cross. At confirmation $K=18$, risk restores one additional task and reaches 43 versus 42. A fixed random allocation also sometimes ties the learned policy. The evidence supports budget-dependent benefits and small state-diversity gains, rather than uniform dominance over error risk or random allocation.

**Acquisition cost.** On confirmation64, eight acquisitions reach 41 successes using 85,971 teacher tokens; 18 acquisitions reach 42 using 192,213. Always invoking raw T0 reaches 41 using 538,488 teacher tokens, while T0 with G reaches 44. The selected policies reduce teacher tokens by 84.0% and 64.3% relative to the raw full-teacher reference. Their additional local computation remains explicit: paired correction uses 64 POST/262,576 tokens and 374.41 summed actor-seconds, while utility classification uses 64 prefills/107,988 input tokens and 41.25 neural-forward seconds, or 129.92 seconds for the complete classification stage. These quantities are not equated across models or summed into a measured wall-clock speedup.

**Transfer.** On the original TAT32, ordinary and paired correction reach 5 and 7; on the prospective frozen panel they reach 12 and 9. The new panel contains two paired-only successes and five ordinary-only successes. Three losses have identical arithmetic programs but omit the percent scale, one changes the formula, and one introduces invalid syntax. At primary $K=9$, multi-state utility, risk and fixed random allocation reach 11, 10 and 12; the full teacher reaches 15. The frozen transfer check therefore does not reproduce the original local-correction advantage. Legal DSL syntax and correct numerical-unit binding remain distinct learning requirements.

The [complete primary table](results/IJCNN_EXPERIMENT_TABLES.md) retains all measured controls, full-teacher/G references and the budget curves. No new checkpoint or primary budget is evaluated on sealed confirmation64.

## VI. Mechanism Analysis

**Table 2. Controlled component and mechanism comparisons.**

| Comparison | Kept fixed | Observation |
|---|---|---|
| Positive-only / one-sided / paired states | Positive data, warm start, update count; total auxiliary weight matched between contrastive arms | DEV33 / 29 / 37; half-weight one-sided32 and balanced positive-state SFT31 |
| Single / multiple local states | 96 teacher trajectories, 121 replay groups, 434 updates, 894 forwards | Primary outcomes40/41, 33/35, 41/42 on the three FinQA panels |
| Separate / inline generation and utility | Same 96-source/252-view supervision and replay | Local37/34 and post-escalation41/40 on DEV64 |
| Joint-edit credit | Fixed executed TRAIN repairs and available edit subsets | 19/29 valid errors require at least two available edits |
| T0 / state-informed T1 | Fixed local results, selected set, teacher, caps, workspace and G | Full32:14 recoveries/4 damages versus9/1; final17/15 |

### A. Joint repair requirements and separated objectives

A constrained execution study on 29 valid TRAIN errors found that 19 require at least two of the teacher repair's available edits before final correctness is recovered. A one-edit final-success reward can therefore be zero even when an edit is part of a successful joint repair. This supports retaining full corrective programs and witnessed recovery states in the learning signal; it does not establish that every local-edit method must fail.

An inline variant jointly trains correction generation and utility output using the same 96-source/252-view utility supervision and 121 replay groups. It reaches 34 local and 40 post-escalation successes on DEV64, versus 37 and 41 for the separated system. Selected-case cross-prompt diagnostics show both parameter and instruction effects. The observed generation tradeoff supports the separate-adapter design in this setting.

### B. Offline sharing and online teacher information

Shared labels have an informative boundary. If G adopts the same teacher candidate for two views, their difference satisfies

$$
r_i(s_a)-r_i(s_b)=C(L_{ib})-C(L_{ia}).
\tag{9}
$$

The teacher term cancels within that source. Additional views can consequently improve recognition of the local program's condition without adding independent evidence about teacher recoverability. Absolute utility still depends on the teacher outcome across sources. This property motivates the matched error-risk control and helps interpret its competitive budget curves.

Offline teacher sharing and online access to current progress are separable design choices. We fix the router, local results, selected set, teacher identifier, budget and G, then compare new executions of T0 with $T_1(x,p^0,L,E(L,x))$. T1 receives the actual current program, predicted scale and public execution feedback, explicitly described as an untrusted candidate. Both arms begin with the same original workspace. Arm order is interleaved according to a fixed random schedule.

On the original TAT panel's fixed nine selected tasks, T0 and T1 yield 11/32 and 9/32 overall successes. Across all 32 diagnostic tasks, T0 restores 14 wrong local states and damages four correct ones, while T1 restores nine and damages one. The resulting totals are 17 and 15. T1 wins five paired cases and loses seven; its difference interval is [-28.1, 15.6] percentage points. Each arm has one trajectory per task; the historical 19/32 teacher result is not substituted for the new T0 execution.

The decomposition in (3) makes the tradeoff explicit. With 25 wrong and seven correct local states, recovery changes from 14/25 to 9/25 and damage from 4/7 to 1/7. Three lost cases reproduce the wrong local candidate exactly. For example, both teachers use subtract(44.1, 56.7), but only T0 supplies the required million scale. In another case, T1 removes program backticks while T0 also repairs the sign and unit. This behavior is consistent with anchoring to incomplete local progress. We retain T0 for the main policy.

### C. Quantities, periods and financial definitions

**Table 3. Executed examples and their evidence roles.**

| Error type and evidence | Wrong attempt | Executed correction | Observed role |
|---|---|---|---|
| Period binding, RCL/2012/page_75.pdf-2, DEV10 | Growth from 398.0 to 459.8 | Growth from the matching prior-period 442.9 to 459.8 | Ordinary SFT fails; paired correction succeeds |
| Quantity and unit, PKG/2002/page_52.pdf-1, DEV9 | Subtracts later option movements before valuing the January balance; omits million conversion | multiply(6569200, 4.55), divide(#0, const_1000000) | Ordinary SFT fails; paired correction succeeds |
| After-tax definition, GPN/2010/page_87.pdf-2, DEV15 | Growth between pretax costs 18.1 and 14.6 | First subtract benefits 6.3 and 5.2, then compute growth | Both local correctors fail; a blind teacher diagnostic succeeds |

The first two examples are actual fixed stage-A executions. The tax example comes from a separately labeled, post-hoc 12-wrong/8-correct teacher diagnostic and does not count as a learned-method recovery or an independent test cohort. Together they distinguish correct arithmetic from correct binding and show what stronger corrective supervision can still contribute.

## VII. Scope and Reproducibility

The study concerns financial program agents, one training fit and small source-isolated cohorts. DEV64 informed development, and the bootstrap does not model variability across training seeds or repeated teacher decoding. Source-group averaging avoids counting views as independent tasks, but related company/year groups may still be correlated. The early53 tie, risk and random controls, and prospective TAT regression remain part of the reported evidence.

Stage-B sharing is conditional on a teacher that reads the original snapshot. Its labels cannot be reused as if the teacher had seen a different current state. T1 changes that teacher policy, so the frozen T0-trained router is not assumed to be calibrated or optimal for T1. G encodes a narrow numerical rule and is included in the strongest full-teacher reference. Teacher-token savings are not a claim of lower total compute, monetary cost or measured end-to-end latency.

The repository preserves code, protocols, summaries and the complete experiment table. Raw requests, candidate programs, executor traces and host-side scoring receipts remain in the private GB10 evidence store, with short receipts mirrored locally. Training references, evaluation answers, credentials and weights are excluded from public Git. The source-level bootstrap is reproducible through the existing forward runner's manuscript-evidence mode.

## VIII. Conclusion

Execution experience can supervise both correction and the decision to seek further correction. Pairing the same wrong-program counterexamples with witnessed pre-recovery and post-recovery states improves the chosen FinQA corrector, while shared-teacher supervision learns intervention outcomes over multiple local states. The gains depend on source cohort and acquisition budget. Prospective transfer and teacher-information diagnostics identify unit binding and anchoring as concrete boundaries. These results support evaluating learned correction and escalation together through recoveries, harmful revisions and separately measured computation costs.

## References

[1] Z. Chen et al., “FinQA: A Dataset of Numerical Reasoning over Financial Data,” EMNLP, 2021. [Primary record](https://arxiv.org/abs/2109.00122).

[2] F. Zhu et al., “TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance,” ACL, 2021. [Primary record](https://arxiv.org/abs/2105.07624).

[3] P. Aggarwal et al., “AutoMix: Automatically Mixing Language Models,” NeurIPS, 2024. [Primary text, v5](https://arxiv.org/html/2310.12963v5).

[4] Y. Li, Z. Yan, and T. Käfer, “RASER: Recoverability-Aware Selective Escalation Router for Multi-Hop Question Answering,” Findings of IJCNLP-AACL, 2026, pp. 4295–4311. [Primary record](https://aclanthology.org/2026.findings-aacl.219/).

[5] A. Kumar et al., “Training Language Models to Self-Correct via Reinforcement Learning,” 2024. [Primary text](https://arxiv.org/html/2409.12917v1).

[6] L. Adolphs et al., “The CRINGE Loss: Learning what language not to model,” ACL, 2023, pp. 8854–8874. [Primary record](https://aclanthology.org/2023.acl-long.493/).

[7] G. Lai et al., “From Sampled Outcomes to Capability Distributions: Rethinking Supervision for LLM Routing,” 2026. [Primary text, v2](https://arxiv.org/html/2606.06924v2).

[8] Z. Yang et al., “Confidence v.s. Critique: A Decomposition of Self-Correction Capability for LLMs,” ACL, 2025, pp. 3998–4014. [Primary record](https://aclanthology.org/2025.acl-long.203/).

[9] Y. Chen et al., “Training LLM-Based Agents with Synthetic Self-Reflected Trajectories and Partial Masking,” 2025. [Primary text](https://arxiv.org/html/2505.20023v1).

## Writing provenance

Equations (4)–(5) follow finqa_state_learning.prepare_paired_states and finqa_learning.edit_contrast_loss/contrast_weight; (6)–(8) follow finqa_acquisition_learning.prepare/request/predict and its source-grouped trainer. Main counts use the common teacher pools in the linked experiment tables. Early53 uses confirmation53_v1/ANALYSIS.json, whose training root is the same paired-state checkpoint. Inline34/40 uses inline_acquisition_v2/native_nonstream_v1/COMPARISON.json; the parent directory's zero-result receipt records the earlier rejected interface configuration and is retained separately. Intervals use PAPER_DRAFT_EVIDENCE_V1.json from frozen native outcomes, with zero model requests, neural forwards or training updates. The tax diagnostic uses FINQA_ZERO_TRAIN_ALIGNMENT_PROBE_SUMMARY.json and its original raw episode; it is separate from the scored method gains. Final author metadata, conference typesetting and a complete bibliographic export belong to the later submission pass.
