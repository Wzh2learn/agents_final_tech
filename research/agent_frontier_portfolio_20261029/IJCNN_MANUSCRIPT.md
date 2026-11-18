# Learning to Correct and Escalate from Shared Execution-State Feedback

> Writing draft v2 · 2026-11-18. [Complete experiment tables](results/IJCNN_EXPERIMENT_TABLES.md) · [Implementation and historical evidence](results/FINQA_CORRECTION_METHOD.md).

## Abstract

Financial document agents must repair executable but semantically wrong programs, preserve correct answers, and decide when to call a stronger teacher. Our local corrector allocates a fixed auxiliary loss across execution-validated counterexamples before and after recovery. An escalation predictor shares one fixed-input teacher trajectory across multiple executed local states and learns the expected gain from intervention. On a source-isolated FinQA cohort, paired-state correction raises native successes from 34/64 to 39/64. Eight and 18 teacher acquisitions reach 41/64 and 42/64 using 84.0% and 64.3% fewer teacher tokens than full raw-teacher execution, which reaches 41/64. In a paired TAT-QA development experiment, disclosing local progress reduces damage from 4/7 to 1/7 and reduces recovery from 14/25 to 9/25. On 48 new TAT-QA tables with a fixed budget of 14 acquisitions, either fixed disclosure mode reaches 14/48 and a frozen risk-based mixture reaches 13/48. Execution experience supports local correction and selective escalation on FinQA. The TAT-QA comparison shows why the decision to escalate and the decision to disclose local progress need separate tests.

## I. Introduction

Financial document questions often require a model to select quantities from text and tables, bind them to the correct reporting period, and compose a numerical program. FinQA and TAT-QA provide concrete settings for studying these requirements [1, 2]. An execution tool can reject an invalid reference or evaluate an arithmetic expression. It usually cannot tell the acting model that a valid result came from the wrong year, a pretax rather than after-tax quantity, or an omitted unit conversion. Successful correction consequently requires semantic decisions beyond repairing syntax.

Correction also creates a preservation problem. Additional reasoning or a stronger model may repair an incorrect answer, but may replace an already correct one with an error. Error detection and intervention value therefore differ. Selective escalation has already been studied through confidence-based model switching and recoverability-aware routing [3, 4]. Our question concerns the learning signal available after an agent has produced and executed a local correction: how can execution experience teach both preservation and the value of further intervention?

We use two separately optimized components. A local corrector receives execution-validated counterexamples in paired pre-recovery and post-recovery contexts. A utility predictor then estimates the correctness change from acquiring a teacher answer relative to retaining that local result. Teacher labeling uses a deliberately fixed original snapshot. One realized teacher trajectory can consequently label multiple executed local states of the same source, with source-level averaging preventing a source with more views from receiving more optimizer updates.

We make three contributions. First, we allocate the same executed wrong-program counterexamples across pre-recovery and post-recovery states to teach both repair and preservation. Second, we share teacher outcomes across executed local states and compare this supervision with repeated single-state examples under matched teacher sources, optimizer updates and forward-pass counts. Third, we decompose intervention value into local error, teacher recovery and damage to correct local answers. The frozen budget comparisons and paired disclosure experiment show how this tradeoff changes as the teacher receives more information about the current program.

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

Positive cross-entropy averages supervised tokens within a source. Ordinary SFT sets $\lambda=0$. The pre-recovery-only, post-recovery-only, and paired conditions set $\rho$ to $1$, $0$, and $0.5$, respectively, with $\lambda=0.1$ in all three. This holds total auxiliary weight fixed for each counterexample-bearing source while varying its allocation across recovery states. Since the disagreement tokens have an identical prefix, their log-probability difference equals their logit difference. The loss reuses the positive forward pass.

The stage-A comparison contains 88 source groups: 59 recovery pairs and 29 preservation sources, yielding 147 positive targets, with counterexamples in 54 groups. Demonstration formation includes reference-assisted TRAIN recoveries and successful execution witnesses. Student inputs contain only the public task, program and execution state. The four primary stage-A arms share initialization, positive demonstrations, token masks, 264 optimizer updates and 441 forward passes.

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

The labeling pool has 96 teacher trajectories and 252 distinct local-state views. Forty-five sources change outcome label across their views. Training also retains 121 replay groups. Source-group gradient accumulation gives 434 updates and 894 forward passes over two epochs. The single-state control repeats its one actual local view according to the original group size, matching these counts. The study accounts separately for forming the local states, collecting teacher labels and training the adapters.

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

We ask whether paired-state supervision improves native correction relative to positive-only training and either one-sided allocation (RQ1), whether state diversity improves utility learning at fixed teacher sources and update and forward counts (RQ2), and how these effects depend on acquisition budget, dataset and teacher information (RQ3).

**Cohorts.** FinQA DEV64 is an internal development subset drawn from the official test snapshot and extensively exposed during development. An earlier 53-source confirmation uses the remaining eligible company/year groups from that snapshot. Both follow the original fixed source-hash order and eligibility rule requiring at least two annotated program steps, with one question per group. The prospective 57-source cohort comes from previously unused TRAIN sources at its execution time. These 57 were later used in a separate, non-adopted expansion; the reported results retain the earlier frozen checkpoints. The final confirmation64 is a project company/year holdout drawn from official TRAIN, isolated from the training construction and earlier exposure inventory. These names describe project roles, not the official benchmark's complete splits.

For TAT-QA, we evaluate 32 development table contexts and then 32 previously unexecuted contexts from official dev, one arithmetic question per table. The latter are selected by public UID order, excluding the earlier tables, before model execution. Prompts, checkpoints, controller and primary budget remain fixed. All 32 are retained regardless of interim results; TAT references and teacher outputs never enter training.

The disclosure follow-up uses 48 additional official-dev table contexts. We select one arithmetic question per eligible table by a fixed hash ordering of public question identifiers and exclude all 64 earlier tables. The original value classifier ranks the 48 frozen local states and selects 14. Within these 14 cases, the original error-risk classifier assigns the lowest seven to T1 and the highest seven to T0, breaking ties by case index. The selected set and rule are recorded before teacher execution. Both teacher modes execute on each selected case, with their order randomized within each pair. We compare always-T0, always-T1 and the frozen mixed policy using those same paired outcomes and hold the 34 unselected local results fixed. Each policy uses 14 teacher tasks. The paired evaluation runs 28 teacher tasks.

**Agents and scoring.** The actor is OpenCode with the frozen Qwen3-8B checkpoints and a common numerical-program tool. The native actor uses the HF-bound BF16 GGUF parent; the utility readout uses the HF model with its separate LoRA adapter. The actual adapter targets are q_proj and v_proj, rank 8, alpha 16, dropout 0, with learning rate $2\times10^{-4}$. Local sampling uses temperature 0.2, seed 17, a 32,768-token context and 8,192-token output cap. The remote teacher is the campus endpoint's deepseek-v4-flash model identifier. Main evaluation episodes share the same 12-POST/300-second cap; the separately labeled 12+8 feasibility probe used a 6-POST/90-second cap.

Native success requires normal agent completion, a valid final program and a correct executed answer. FinQA compares the executor result with the supplied execution answer after five-decimal canonicalization. TAT-QA uses official arithmetic exact match with the predicted scale; scale exactness is recorded separately. The actors observe their actual execution results, not correctness flags. The shared functional DSL permits earlier-step references and rejects nested function calls.

**Controls and costs.** For stage A, we compare ordinary SFT, pre-recovery-only counterexamples ($\rho=1$), post-recovery-only counterexamples ($\rho=0$), and paired-state correction ($\rho=0.5$). Two additional controls use equal-weight positive-state SFT and a half-weight pre-recovery-only loss ($\lambda=0.05$, $\rho=1$). Escalation controls use an error-risk predictor with the same backbone and executed states, repeated single-state utility supervision, uniform random allocation, raw always-teacher output, and always-teacher with G. The risk arm uses task instructions and a binary readout specific to local error prediction. We report the exact expectation of a uniform draw and the original fixed-seed allocation.

Primary budgets are 18/16/18 for the three stage-B FinQA cohorts and 9 for each TAT cohort. The FinQA budget curves include every $K$, with original primary points retained. Selected policies share identical-input realized teacher responses, so their comparisons do not depend on separate teacher samples for overlapping tasks. Actual new teacher acquisition cost is charged once; each policy's deployment cost uses its selected subset.

We separate local generation, utility prefills, teacher requests/tokens, training and formation. Cached input is a subset of provider input, not an additional token total. Unknown usage is retained with its reserve. Classifier loading/preprocessing time and neural-forward time are reported separately. Earlier confirmation timing included a disclosed model-residency overlap; it is not treated as a clean end-to-end latency benchmark.

Paired intervals resample one frozen outcome difference per source, using 20,000 percentile-bootstrap draws. New summaries use seed 171118; the existing early53 analysis retains seed 17053. Intervals condition on the training fit and realized teacher pool, assume source-level independence, and are unadjusted across comparisons.

## V. Results

**Table 1. Native successes at low and primary teacher budgets.** Bold budgets mark the original primary points. SFT is ordinary correction and Pair is paired-state correction. Selective policies retain Pair on unselected tasks and share a pool of native teacher trajectories. All T0+G applies the controller to Pair on every task.

| Panel (N) | K | SFT | Pair | Value | Risk | Single | E[Random] | All T0 | All T0+G |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FinQA development (64) | 8 | 33 | 37 | 39 | 38 | 39 | 37.9 | 40 | 44 |
| FinQA development (64) | **18** | 33 | 37 | 41 | 41 | 40 | 39.0 | 40 | 44 |
| FinQA early confirmation (53) | — | 30 | 30 | — | — | — | — | — | — |
| FinQA prospective (57) | 7 | 32 | 32 | 35 | 33 | 35 | 32.6 | 32 | 37 |
| FinQA prospective (57) | **16** | 32 | 32 | 35 | 33 | 33 | 33.4 | 32 | 37 |
| FinQA final confirmation (64) | 8 | 34 | 39 | 41 | 40 | 40 | 39.6 | 41 | 44 |
| FinQA final confirmation (64) | **18** | 34 | 39 | 42 | 43 | 41 | 40.4 | 41 | 44 |
| TAT-QA development transfer (32) | **9** | 5 | 7 | 11 | 13 | — | 10.4 | 19 | 19 |
| TAT-QA prospective transfer (32) | **9** | 12 | 9 | 11 | 10 | — | 10.7 | 15 | 15 |

For a frozen pool with $R$ recoveries, $H$ harmful revisions and $B$ locally correct tasks, $E[\mathrm{Random}]=B+K(R-H)/N$. The central 95% intervals from the exact multivariate hypergeometric distribution are, in table order for the eight escalation rows, [37, 40], [37, 41], [31, 35], [31, 36], [37, 42], [37, 44], [7, 13] and [8, 14]. The corresponding original fixed draws are —, 41, 33, 35, 41, 41, 13 and 12. The intervals describe variability across random selections from each observed pool.

**Local correction.** On DEV64, ordinary SFT, pre-recovery-only, post-recovery-only and paired-state training yield 33/64, 29/64, 34/64 and 37/64 native successes. Relative to the common first pass, they record 0/0, 3/7, 1/0 and 4/0 recoveries and harmful revisions (R/H), respectively. Both the post-recovery-only arm and Pair preserve all 33 correct ordinary-SFT answers. Pair solves three tasks that the post-recovery-only arm misses and loses none, a gain of 4.7 percentage points (descriptive paired 95% interval [0.0, 10.9] from 20,000 source-level bootstrap draws). At fixed auxiliary weight, the paired allocation combines more recoveries with the preservation observed under post-recovery-only training. The half-weight pre-recovery-only control reaches 32/64, and equal-weight positive-state SFT reaches 31/64.

On confirmation64, Pair improves 34 to 39 with six recoveries and one harmful revision relative to ordinary SFT, a gain of 7.8 percentage points with a conditional paired interval of [0.0, 15.6]. Earlier confirmation53 and prospective57 show equal totals at 30 and 32, respectively.

**Utility learning and budget.** At the low budgets in Table 1, Value exceeds Risk by 1, 2 and 1 tasks across the three FinQA panels. It exceeds the random expectation by 1.1, 2.4 and 1.4 tasks. Value ties Single on development and prospective cohorts and leads by one task on confirmation64. At the original primary budgets, Value reaches 41/64, 35/57 and 42/64, gaining 1, 2 and 1 tasks over Single. The confirmation difference has an interval of [-4.7, 7.8] percentage points. Relative to ordinary SFT, the full confirmation pipeline yields eight paired-only successes, a gain of 12.5 points [4.7, 21.9].

The budget curves cross. At confirmation $K=18$, Risk restores one additional task and reaches 43 versus Value's 42. A few original fixed random draws equal the learned policy, including confirmation $K=8$. The analytic expectation provides the mean reference, while the original draws and their distribution show the spread at each budget.

**Acquisition cost.** On confirmation64, Value matches the raw full teacher's 41 successes at $K=8$ using 85,971 of its 538,488 teacher tokens (16.0%). At $K=18$, Value reaches 42 with 192,213 teacher tokens (35.7%). The fixed random draw at $K=8$ reaches 41 with 92,790 teacher tokens and requires no classifier. Full teacher with G reaches 44. The shared first pass uses 128 POST and 513,140 local tokens. Pair uses a further 64 POST, 262,576 tokens and 374.41 summed actor-seconds. Value classification processes 107,988 input tokens across 64 prefills, with 41.25 seconds of neural forwards and 129.92 seconds for the complete classification stage. Teacher tokens and local computation are reported in their own units.

**Transfer and scale compatibility.** On the prospective TAT-QA panel, Pair records two recoveries and five harmful revisions relative to ordinary SFT under official EM. Three of the five use the exact same arithmetic program as SFT, with a blank scale in place of the percent label. The other two change the formula or introduce invalid syntax. Isolating the three label-only cases leaves two recoveries and two losses in the remaining cases. Official EM can also accept an equivalent unscaled fraction.

We checked this explanation by replaying the saved programs with the official scorer. The structured rule fills a blank scale with percent when the question contains an explicit percentage cue and the parsed program multiplies its previous result by 100 at the last step. For average-percentage questions, it also accepts a table average or a sum divided by a numeric literal, with no percentage operands in the latter case. The rule excludes percentage-point questions and runs on final submissions after the frozen policy and G. The keyword-only control uses the same cue for parseable programs without checking the program shape.

| TAT-QA panel (32 each) | Official EM, SFT / Pair / Value K=9 | Official EM after structured completion | Official EM after keyword-only completion |
|---|---:|---:|---:|
| Development transfer | 5 / 7 / 11 | 6 / 8 / 12 | 3 / 3 / 8 |
| Prospective transfer | 12 / 9 / 11 | 13 / 12 / 14 | 8 / 6 / 8 |

Structured completion restores all three isolated label losses on the prospective panel without changing their programs. It also repairs one SFT submission, leaving prospective local correction at 13 for SFT and 12 for Pair. The keyword-only rule often turns an already correct fraction into an incorrect percentage. The replay distinguishes a scale-interface gap from genuine changes in arithmetic. Table 1 reports the original official scores. [Detailed replay and costs](results/IJCNN_EXPERIMENT_TABLES.md).

## VI. Mechanism Analysis

**Table 2. Controlled component and mechanism comparisons.**

| Comparison | Kept fixed | Observation |
|---|---|---|
| Ordinary SFT / pre-recovery-only ($\rho=1$) / post-recovery-only ($\rho=0$) / paired ($\rho=0.5$) | Positive data, warm start, masks, 264 updates and 441 forwards. The three contrastive arms share total auxiliary weight. | DEV64: 33 / 29 / 34 / 37 (R/H: 0/0, 3/7, 1/0, 4/0). Paired minus post-recovery-only: +4.7 pp [0.0, 10.9]. Half-weight pre-recovery-only: 32. Equal-weight positive-state SFT: 31. |
| Single / multiple local states | 96 teacher trajectories, 121 replay groups, 434 updates, 894 forwards | Primary outcomes40/41, 33/35, 41/42 on the three FinQA panels |
| Separate / inline generation and utility | Same 96-source/252-view supervision and replay | Local37/34 and post-escalation41/40 on DEV64 |
| Joint-edit credit | Fixed executed TRAIN repairs and available edit subsets | 19/29 valid errors require at least two available edits |
| T0 / state-informed T1 | Fixed local results, selected set, teacher, caps, workspace and G | Full32:14 recoveries/4 damages versus9/1; final17/15 |

### A. Joint repair requirements and separated objectives

A constrained execution study on 29 valid TRAIN errors found that 19 require at least two of the teacher repair's available edits before final correctness is recovered. A one-edit final-success reward can therefore be zero even when an edit is part of a successful joint repair. This supports retaining full corrective programs and witnessed recovery states in the learning signal; it does not establish that every local-edit method must fail.

An inline variant jointly trains correction generation and utility output using the same 96-source/252-view utility supervision and 121 replay groups. It reaches 34 local and 40 post-escalation successes on DEV64, versus 37 and 41 for the separated system. Selected-case cross-prompt diagnostics show both parameter and instruction effects. The observed generation tradeoff supports the separate-adapter design in this setting.

### B. The Anchoring–Preservation Tradeoff of State-Informed Escalation

Shared labels have an informative boundary. If G adopts the same teacher candidate for two views, their difference satisfies

$$
r_i(s_a)-r_i(s_b)=C(L_{ib})-C(L_{ia}).
\tag{9}
$$

The teacher term cancels within that source. Additional views can consequently improve recognition of the local program's condition without adding independent evidence about teacher recoverability. Absolute utility still depends on the teacher outcome across sources. This property motivates the matched error-risk control and helps interpret its competitive budget curves.

The three outcome classes identify expected gain, since $P(B)-P(A)=p_{01}-p_{10}$, where $p_{ij}$ gives the joint probability of local correctness $i$ and post-controller correctness $j$. The unchanged class combines $p_{00}$ with $p_{11}$. Separating them allows a direct estimate of recovery conditional on local failure, $a(s)=p_{01}/(p_{00}+p_{01})$. In the 252 training views, 92 are wrong both before and after intervention and 79 are correct both times. Source-normalized weights give those cases 32.67 and 37.87 source equivalents, respectively. Four-state supervision changes what can be read out about conditional recovery even though either label scheme represents the same population-level gain.

We train two four-state adapters with the same warm start, 96 sources, views and replay schedule. One sees public execution feedback from both states. The other sees the same question, report and programs, with those two feedback fields removed from its utility examples and classifier inputs. Each adapter performs 434 updates and 894 training forwards. We pair both classifiers' selections with the same native teacher outcomes on DEV64 and Forward57.

| FinQA panel | Recovery AUC, old value / feedback / static | Success at low K, old value / feedback / static | Success at primary K, old value / feedback / static |
|---|---:|---:|---:|
| DEV64 | .582 / .471 / .429 | 39 / 39 / 39 | 41 / 39 / 41 |
| Forward57 | .560 / .659 / .675 | 35 / 32 / 35 | 35 / 35 / 36 |

Recovery AUC uses the seven recoverable errors among 27 local errors on DEV64 and among 25 on Forward57. The old benefit-class probability gives AUCs of .504 and .615. We resample recoverable and unrecoverable errors separately, pairing classifier scores within each sampled task. The paired 95% intervals for the effect of showing execution feedback on four-state AUC are [-.257, .407] on DEV64 and [-.385, .353] on Forward57. Static inputs match or exceed feedback inputs at all four fixed budgets. At Forward57's primary budget, the static adapter gains one completion while selecting 9.5% fewer teacher tokens than the old classifier. The feedback adapter matches the old completion count at 21.8% fewer teacher tokens. These results locate a budget-dependent tradeoff in the utility stage and leave the three-state classifier as the primary method. The local correction and common replay stages continue to use their original execution information.

Offline outcome sharing and online state disclosure are separate choices. To isolate the effect of disclosure within the implemented protocol, we hold the router, local results, selected set, teacher identifier, budget, workspace and G fixed. T1 adds the current program, predicted scale and public execution feedback to T0's input, with instructions to treat local progress as provisional. Both teachers run anew on the original TAT-QA development panel, with one trajectory per task and interleaved arm order.

Across all 32 tasks, T0 restores 14 of 25 wrong local answers and damages four of seven correct ones. T1 restores nine and damages one. Equation (3) gives the difference in gain under disclosure as $q(s)(a_1(s)-a_0(s))+(1-q(s))(b_0(s)-b_1(s))$. The two terms favor different choices: disclosure costs five potential recoveries and saves three correct answers in this pool. Overall success is 17 for T0 and 15 for T1, with five paired wins and seven losses for T1 and an interval of [-28.1, 15.6] percentage points. At the original fixed $K=9$, the two options yield 11/32 and 9/32.

We split the panel at the median of the cached risk ranking, which uses public states and was produced before the teacher comparison. The lower half has 12 wrong and four correct local programs, and the upper half has 13 wrong and three correct ones.

| Cached risk rank | N | T0 recovery / damage | T1 recovery / damage | Success with T0 / T1 |
|---|---:|---:|---:|---:|
| Lower half | 16 | 6/12 · 3/4 | 6/12 · 0/4 | 7 / 10 |
| Upper half | 16 | 8/13 · 1/3 | 3/13 · 1/3 | 10 / 5 |

Program validity supplies a coarser diagnostic. Among seven invalid or missing local programs, T0 recovers six and T1 recovers three. In the 24 valid programs with a blank scale, T0 and T1 achieve 10 and 11 successes. The remaining one program carries an explicit scale and both teachers solve it. An explicit scale is too rare on this panel to establish it as a reliable indicator of unit binding.

Three of T1's seven paired losses exactly reproduce the wrong local candidate. For example, both teachers use subtract(44.1, 56.7), and T1 repeats the local blank scale while T0 adds million. In another case T1 removes program backticks, while T0 also repairs the sign and unit. These examples are consistent with anchoring to incomplete progress.

Retrospectively combining T1 in the lower-risk half with T0 in the upper half produces 20/32 on complete coverage (14 recoveries and one harmful revision). Seven of the original nine selected states fall in the upper half. The two states assigned to T1 fail under both modes, so the mixed policy has the same 11/32 as T0. Recomputing the split within those nine allocates four states to T1 and yields 10/32. The additional loss occurs when T1 retains a blank scale and T0 supplies the correct scale. Budget selection changes which states are exposed to either mode. These paired results distinguish the allocation of modes within the budget from the benefit of assigning a particular state to a mode.

**Prospective disclosure at K=14.** Across 48 fresh table contexts, the initial, ordinary and paired local agents solve 1, 10 and 9 tasks. The selected 14 include 12 local errors and two already correct answers. Each fixed teacher mode recovers five, preserves both correct answers and reaches 14/48. The frozen mixture recovers four, preserves both and reaches 13/48.

| Risk within selected 14 | Local wrong / correct | T0 recoveries / damage | T1 recoveries / damage | T1 minus T0 successes |
|---|---:|---:|---:|---:|
| Lower seven, assigned T1 | 5 / 2 | 2 / 0 | 1 / 0 | −1 |
| Upper seven, assigned T0 | 7 / 0 | 3 / 0 | 4 / 0 | +1 |

The two discordant pairs reverse the directions suggested by the development split. In the lower-risk case, T1 adds the percent scale but keeps the local subtraction order. T0 also reverses the operands and solves the question. In the higher-risk case, both modes submit the same arithmetic program and only T1 supplies the thousand scale. The failed directional transfer limits the case for using local risk alone to select a disclosure mode. Both fixed modes preserve the two selected correct answers, so this panel gives little information about the difference in damage rates. Applying the structured scale rule to all saved submissions leaves the policy scores unchanged.

T0, T1 and the mixture select teacher workloads of 129,967, 120,928 and 118,039 tokens, respectively. Teacher actor times are 143.3, 152.8 and 143.9 seconds. The modes share the same local generation and value readout. The mixture adds a risk readout across 48 states. The paired evaluation physically executes 28 teacher tasks, totaling 60 POSTs and 250,895 provider tokens, with complete usage reports. Conditional paired 95% intervals on full-panel success differences are [-6.25, 6.25] points for T1 minus T0 and [-6.25, 0] for the mixture minus either fixed mode. These intervals resample task outcomes at the fixed selections.

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

Paired execution states improve local correction on FinQA, and shared teacher trajectories provide a utility target for allocating a small intervention budget. Four-state supervision exposes conditional recoverability, with gains on the forward cohort and losses on the development cohort. The disclosure experiments show two effects of revealing local progress. It can help the teacher preserve an answer or anchor it to an error. The frozen risk split under a fixed budget does not reproduce the directional pattern seen at full coverage on the development panel. These results separate the evidence for acquiring a teacher from the evidence for showing it the current program.

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

Equations (4)–(5) follow finqa_state_learning.prepare_paired_states and finqa_learning.edit_contrast_loss/contrast_weight. Equations (6)–(8) follow finqa_acquisition_learning.prepare/request/predict and its source-grouped trainer. Main counts use the common teacher pools in the linked experiment tables. Early53 uses confirmation53_v1/ANALYSIS.json from the same paired-state checkpoint. Inline34/40 uses inline_acquisition_v2/native_nonstream_v1/COMPARISON.json. The parent directory retains the earlier rejected interface configuration. Intervals use PAPER_DRAFT_EVIDENCE_V1.json from frozen native outcomes. Scale and risk-stratified disclosure replays use TATQA_MANUSCRIPT_FOLLOWUP.py and MANUSCRIPT_FOLLOWUP_CPU_V1.json in the private evidence store. Both analyses use saved submissions and have zero model requests or updates. The tax diagnostic uses FINQA_ZERO_TRAIN_ALIGNMENT_PROBE_SUMMARY.json and its original raw episode. Final author metadata, conference typesetting and a complete bibliographic export belong to the submission pass.
