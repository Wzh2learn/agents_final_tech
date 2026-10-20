# Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and Evidence-Ranking Evaluation

## Abstract

Final-answer scores can hide the measurement boundary of a staged evaluation: a defect may be invisible to an instrument, ignored by a decision predicate, or harmless under the evaluation's equivalence contract. We audit two real evaluation constructions. In a frozen staged document evaluator, 96 of 118 controlled header injections are checkpoint-visible while the OCR-like family is unobserved on the frozen scored surface (0/13), but harmfulness remains contract-relative. In the single-responsive-leaf construction, flat and layered scores are affine/rank-equivalent, and the clean-only panel cannot identify a unique operating point. Stage-aligned instrumentation separates three constructed stages perfectly; a direct codebook does the same, while non-direct leaves retain only partial separation. We then audit FinRank at commit 916dc27e77b90e294ea1b3a2cc5b0abcf07392d1 under a preregistered question and materiality threshold, with one documented post-hoc identity correction after a wrong-identity application. Its documented tie-positive pairwise policy changes absolute random-negative accuracy by about 1.03-1.08 percentage points under strict-win scoring, but changes the hard-versus-random gap by only 0.34-0.36 points and preserves its direction. The released identity counts reproduce: 442 cross-record overlapping hard negatives across 305 records and metadata-filter gold loss in 33 records with all gold lost in 2. A reproducibility caveat remains: global and metadata-filtered values drift by up to 0.19 and 0.16 points in the declared deterministic environment, while in-record and pairwise metrics reproduce exactly. Together, the two cases show how observation surfaces, score contracts, ranking tie order and measurement-object binding determine what an evaluation can identify. The contribution is a bounded measurement audit and review discipline, not a universal validity theory, detector ranking, or claim that either benchmark is generally defective.

## 1. Introduction

Document-intelligence and evidence-ranking systems are evaluated through multi-stage pipelines: documents are parsed, candidate evidence is retrieved or mapped, calculations are executed, and final answers or rankings are produced. A final score does not say whether an intermediate instrument observed a defect, whether a decision predicate consumed that observation, or whether the outcome changed under the evaluation's equivalence contract. It also does not say whether equal scores, deduplicated texts and source identities preserve the construct the benchmark claims to measure.

We keep three constructs separate. *Visibility* asks whether an instrument observes a change. *Detection* asks whether a decision predicate consumes the observation under its threshold rule. *Harmfulness* asks whether the outcome changes under a stated equivalence contract. These are properties of different objects: instruments, decision rules and contracts. Confounding them makes a score gap look like protocol sensitivity, an unobserved family look like a harmful blind spot, and instrumentation-induced localization look like a property of hierarchical organization.

This paper audits two evaluation constructions. The first is a frozen staged document evaluator with controlled header perturbations and stage-aligned injections. It exposes family-dependent visibility, affine/rank score equivalence, a non-identifiable clean calibration point and an instrumentation attribution boundary. The second is FinRank, a public provenance-sensitive evidence-ranking benchmark. A source-informed implementation audit examines exact tie handling, first-occurrence text/source mapping, random-negative construction and numerical reproduction; its question and thresholds are preregistered, while the corrected source-identity branch is explicitly post-hoc. The FinRank hardness ordering remains stable under alternative tie policies, while absolute pairwise values and some ranking metrics are contract-sensitive. The same case also narrows a reproducibility claim: the released artifacts reproduce in-record and pairwise values exactly in the audited environment, but not every global or metadata-filtered value at raw precision.

Our contributions are:
1. A measurement-object separation for visibility, decision detection and contract-relative harmfulness in a staged evaluator, with deterministic evidence for score-structure and instrumentation identifiability.
2. A second, implementation-level audit of a real evidence-ranking benchmark showing that tie policy and identity construction can move absolute metrics without changing the qualitative hard-versus-random decision, with the post-hoc identity correction kept visible in the evidence status.
3. A bounded review sequence for evaluator authors: bind mutation, observation, score, ranking and reported claim to the same measurement object; report tie and identity contracts; and state the numerical tolerance and environment required for reproducibility.

The audit does not establish a universal method, a detector ranking, or a general failure rate. Its external value is narrower but concrete: it changes what should be reported and which comparisons can be interpreted before further experiments are commissioned.

## 2. Related Work

### 2.1 Measurement validity and construct validity

Meta-evaluation asks whether a metric measures what it claims. Machine-translation challenge sets such as ACES test whether a metric separates genuine errors from acceptable variants [Amrhein et al., 2022; Amrhein et al., 2023; Moghe et al., 2024], and contextual metric meta-evaluation extends this to local, context-dependent correctness [Deviyani and Diaz, 2025]. Rankings can change with protocol axes, prompt subsets, seeds, or the property a metric targets [Kendiukhov, 2026; Du et al., 2026; Ross et al., 2024]. Reliability work on LLM-as-a-judge documents position, verbosity, self-preference, and perturbation sensitivity [Zheng et al., 2023; Li et al., 2025a; Li et al., 2025b]. Construct-validity guidance frames the same concern normatively: NIST AI 100-1 asks that TEVV metrics and processes be appropriate and effective and that measurement types be reviewed for unique and meaningful information, and NIST AI 600-1 asks that construct validity be demonstrated for each metric [NIST, 2023; NIST, 2024]. We share the meta-evaluation aim but ask a prior question: whether the evaluation surface can observe a controlled defect at all. We keep visibility, detection, and harmfulness as separate constructs so that a protocol comparison is not read into counts that different decision rules produce.

Recent work broadens this umbrella. Caban models validity as compounding across task generation, simulator calibration and automated judgment [Caban, 2026]; Bean et al. audit 445 LLM benchmarks and derive construct-validity recommendations [Bean et al., 2025]. These works already cover general validity frameworks and checklists. FinRank is closer to our external case: it separates passage retrieval, reranking and hard-negative discrimination for provenance-sensitive financial evidence, while explicitly limiting its pool to a curated passage-ranking stress test [Mansouri et al., 2026]. Our contribution is therefore not another generic checklist. It examines whether score contracts, tie order and identity construction preserve the object a concrete evaluation claims to measure.

### 2.2 Testing, oracles, and diagnosability

Mutation testing and metamorphic testing introduce controlled changes to measure whether a test or metric notices them [Cho et al., 2025]; AgentChaos applies programmatic fault injection to agent systems [Tan et al., 2026]. Fault-based reasoning separates whether a fault is reached, whether it changes intermediate state, and whether its effect propagates to an observable output; non-detection can arise at any of these stages, and an oracle that does not respond to a propagated effect is insensitive by construction. Process-level work evaluates intermediate behavior rather than only final success [Fan et al., 2026; Chung et al., 2026], and GTA-2 aggregates checkpoints recursively [Wang et al., 2026]. We follow the mutation and fault-injection tradition but decompose non-detection into distinct mechanisms, and we treat a checkpoint forest as an evidence instrument whose diagnosability must be audited rather than assumed.

### 2.3 Verified SANER RENE precedent

The RENE track publishes reproducibility studies and negative results. Four recent papers define the surrounding practice; we describe each based on its abstract. The Limits of the Identifiable [Gerhold et al., 2024] extends deep-learning Python version identification to larger, realistic files and finds that accuracy falls from short snippets to longer segments, with import-statement analysis reaching only 30 percent, exposing limits of the approach. Does the Tool Matter? [Hoess et al., 2025] compares two mining tools across ten projects and finds that even simple metrics such as commit and developer counts can differ by up to 500 percent, often from minor technical details, and hypothesizes similar uncertainty in other analysis tools. Can We Classify Flaky Tests Using Only Test Code? [Berndt et al., 2026] evaluates three LLMs with three prompting techniques on two benchmarks and reports that classifiers are only marginally better than random, and that the test code alone does not necessarily carry enough information for a flakiness decision. Static Analysis Traces can Help Dynamic Symbolic Execution: a Replication Study [Kummita et al., 2026] replicates a prior study, extends it with PhASAR-based tools and a second benchmark, and reports a conclusion different from the original: traces let KLEE find vulnerabilities about 1.4 times faster, though KLEE also confirms fewer vulnerabilities on one benchmark. These papers share our concern with measurement validity and information sufficiency; we differ in scope, auditing the observation surface of a staged document-intelligence evaluator with controlled, family-resolved injections and an explicit boundary between visibility, detection, and harmfulness.

## 3. Method

The conceptual core is a three-way audit of visibility, detection, and harmfulness; the hierarchical checkpoint forest is the evidence instrument that makes the audit reproducible.

### 3.1 Evidence instrument: checkpoint forest

We model the pipeline as two checkpoint trees. The parsing tree covers document ingestion, table structure, field mapping, and arithmetic reconciliation. The QA tree covers retrieval grounding, faithfulness, numeric correctness, citation quality, and appropriate refusal. Together the trees contain 12 scored leaves.

The twelve scored nodes are five in the parsing tree (document status, document throughput, table regression, field hit-rate, reconciliation equations) and seven in the QA tree (retrieval contract, faithfulness judge, numeric contract, number grounding, citation judge, refusal judge, refusal contract), per the frozen checkpoint-tree configuration v0.1.0 (listed in the artifact manifest). The visibility audit exercises the parsing-tree leaves whose evidence is the mapping and regression artifacts; under the frozen drop rule (drop = (H_orig - H_inj) x 10, threshold 2.0) only the field hit-rate leaf responds to header drift, while QA-tree leaves keep their frozen evidence and the QA arm is reported separately (12 calls to the same judge). Additional localization value therefore remains unestablished in the current instantiation. In Table 1, the label *Pruned parsing-root drop* denotes exactly this operation: the parsing root is collapsed to its single input-responsive leaf (the field hit-rate leaf) and the drop rule above is applied there.

Each leaf receives a score in [0,10]. Contractible properties use deterministic checks; semantic properties use a 0–5 judge score mapped to [0,10]. Sibling weights are normalized locally before bottom-up aggregation. Missing evidence is explicit: the parsing tree assigns 0, whereas the QA tree assigns a neutral 5. Hinge leaves affect the stability verdict, not the missing-evidence score. Every leaf stores its evidence and degradation reason.

For node n with children C(n), the recursive score is

\[
S(n)=\sum_{c\in C(n)} \frac{w(c)}{\sum_{j\in C(n)}w(j)}S(c).
\]

For a leaf, S(n) is the mapped contract or judge score. A tree is stable only when at least 90% of its leaves exceed the selected threshold and every hinge leaf scores at least 7. The implementation is deterministic once the evidence artifacts are fixed.

### 3.2 Separating visibility, detection, and harmfulness

Visibility is defined relative to the selected checkpoint evidence surface, whereas protocol detection may use a different downstream signal.

The primary conceptual structure is the following visibility-by-detection matrix:

| Checkpoint evidence | Protocol detects | Protocol does not detect |
|---|---|---|
| Visible | Detected visible defect | Visible but undetected |
| Not visible | Detection through a different signal or predicate | Silently absorbed or unobservable |

Harmfulness is orthogonal to this matrix and is annotated separately as harmful, equivalent, or unresolved under the selected equivalence criterion.

For an injected defect d, visibility and protocol detection are separate observations:

- **Detected:** the selected protocol satisfies its detection predicate, which may test a mapping change or a score threshold.
- **Visible but not detected:** the checkpoint exposes a difference, but the selected protocol does not satisfy its detection predicate.
- **Silently absorbed:** normalization or matching preserves the canonical correspondence, so that the checkpoint does not expose the perturbation.

Harmfulness is a separate, **equivalence-dependent** judgment, not a mutually exclusive visibility outcome: canonical-form preservation and reader-referent recoverability need not agree.

The defect visibility profile reports visibility separately for each family. This preserves information lost by a single mutation score and distinguishes a missing checkpoint from a genuinely robust stage.

### 3.3 Evaluating the evaluator

We compare four protocols on frozen evidence: end-to-end roots, a flat leaf average, hierarchical expert weights, and hierarchical searched weights. We measure table-level detection, injection-level detection, mean separation between clean and perturbed states, worst-family behavior, localization, and evaluation cost. Because raw thresholds can manufacture differences, we separately audit (i) structural score/ranking equivalence and (ii) whether a matched-FPR operating point is identifiable from clean scores alone.

The audit further varies the injection seed, visibility threshold, matching algorithm, and scoring normalization. A semantic-judge arm is evaluated separately and never substituted for deterministic evidence when a contract exists.

### 3.4 Stage-aligned instrumentation and the second dataflow

The evaluation-track instrument is a two-root checkpoint forest whose twelve leaves map deterministic or judge-derived evidence to a 0–10 score (Section 3.1). To test whether stage-aligned instrumentation carries stage information, we preregister a separate controlled study on the same corpus. Each stage contract perturbs one operation: a header token is replaced (mapping stage M), required source blocks are removed from the retrieval bundle (retrieval stage R), or one numeric operand is broken while labels, schema and identity are preserved (numeric stage N). Every cluster contributes three deterministic injections, and each injection is scored on the same twelve-leaf surface, producing a binary response vector; 24 clusters per stage give 72 clusters and 216 injections. The study is frozen before results (hash receipt) and evaluated leave-one-cluster-out. The same document defines the protocol's deliberate boundary: response predicates are written from the stage contracts, so the construction is explicitly instrumented and its separability must be interpreted within that construction.

The second dataflow is a program-perturbation corpus built from FinQA reasoning steps. Perturbations act on a step's operator or argument fields while the downstream result fields are not recomputed; the observation objects are visibility (does the injected change appear in the observed source fields), detection (does the frozen detection predicate move), and outcome (does any downstream outcome field change). The execution contract binds artifact hashes before scoring, and no threshold or convention search is permitted. Section 4.5 states the execution boundary; Section 5.6 reports what happened and what it does and does not establish.

### 3.5 External evidence-ranking audit

The external case is FinRank at upstream revision `916dc27e77b90e294ea1b3a2cc5b0abcf07392d1`, with arXiv record `2608.07400v1`, 1,185 released records and the official deterministic baseline implementation. The repository license is CC BY-NC 4.0. The audit follows the complete chain: question and source identity, candidate construction, scoring, global and in-record ranking, pairwise comparison, random-negative sampling, metadata filtering and published claims.

The source code exposes two known, source-informed checkpoints before application: pairwise accuracy counts exact ties for the gold (`score(gold) >= score(negative)`), and pooled-corpus passage text is deduplicated in first-occurrence order so the first occurrence supplies metadata. These probes are not presented as prospective discoveries. The preregistered application recomputes all 1,185 records after synthetic positive, negative, tie, permutation and identity fixtures and a frozen materiality threshold. A first run used the wrong identity mapping; the corrected source-identity branch is retained as a transparent post-hoc correction and is not represented as a second blind application.

The audit compares ties-positive, strict-win and half-credit pairwise policies; gold-first and negative-first ordering for exact ties inside each record; forward and reverse corpus ordering for global ranking ties; the seed-42 random-negative draw; and source-identity loss under the metadata filter. Reproducibility is checked against the released result JSON under the declared dependency versions and a second available environment. The application is deterministic and source-informed, not blind.

## 4. Experimental Setup

### 4.1 Corpus and perturbations

The study uses a frozen public tabular base and contains no client data. It includes 95 tables and 118 synthetic injections across six header-drift families. Schema and header matching are the perturbation carrier here; the object of study is the evaluation protocol's observation boundary. Each injected record preserves its source table, family, seed, changed field, and expected observation surface.

Concretely, the base is the frozen drift-v0 table set derived from public TAT-QA tables (listed in the artifact manifest by content hash); the corpus was frozen before this study's data gates and no new TAT-QA use is introduced. The perturbations are the fully synthetic injection map (listed in the artifact manifest by content hash; deterministic, seed 42, ratio 0.3). The matcher used in the audited pipeline is the greedy header matcher (listed in the artifact manifest); the cross-matcher audit adds greedy-normalized, Hungarian, and Hungarian-normalized configurations. Semantic leaves are scored by the judge pipeline (listed in the artifact manifest), i.e. Qwen3.6-35B-A3B (Q4_K_M GGUF) served locally, with 0–5 dimension scores mapped to [0,10]. The primary threshold grid is

\[
\Gamma=\{0.2,0.3,0.5,0.7,0.9\}.
\]

The OCR-like family contains 13 single-token, lowercase Levenshtein-distance-one substitutions with unchanged column values. These properties are mechanically recomputed before interpretation.

### 4.2 Baselines and controls

The protocol baselines are end-to-end scoring, flat leaf scoring, and hierarchical scoring with expert weights. Weight-search controls include equal weights, expert weights, 30 random trials, greedy coordinate ascent, particle-swarm optimization (PSO), and a minimax objective. Assignment controls compare greedy matching with Hungarian global assignment and include a positive solver test.

### 4.3 Statistical discipline

We freeze inputs and decision criteria before reading each result. Confidence intervals are reported on table-level clustered units where available (percentile bootstrap over the 95 table units, seed 20260830; endpoints on the k/95 grid for the 95-table arm). Seed sensitivity uses three injection seeds. For the clean-only matched-FPR audit, threshold selection may use clean scores only; injected and harmful outcomes are prohibited from calibration. Because the frozen clean supports are degenerate, the registered deployment operating point is left unresolved rather than forced into an empirical equality. The 2,382 clean records are the usable (table_uid, column) rows of the non-injected source tables in the frozen clean-input set, with fold assignment = sorted(table UID) index modulo 5. Null and adverse findings are retained rather than relabeled as improvements.

### 4.4 Multi-leaf stage-aligned protocol

The stage-aligned study uses the same frozen tabular base and the same twelve-leaf surface. Stage contracts and injection generators are deterministic; clusters are selected by an outcome-blind hash rule (seed frozen before results), and the pre-result freeze receipt binds the corpus, the generator, the runner and the environment by hash. Response predicates are contract-derived: for M the directly targeted parse leaves move; for R the retrieval leaf moves; for N the reconciliation leaf moves. Baselines are the metric-specific chance top-1 (1/3) and majority macro-F1 (1/6); uncertainty uses leave-one-cluster-out evaluation with 10,000 cluster-bootstrap resamples and a 10,000-replicate permutation null, both seeds frozen. The ablation re-scores the same rows with (i) the full twelve-leaf vector, (ii) the fixed three-direct-leaf codebook, (iii) non-direct leaves only, and (iv) a single any-response scalar.

### 4.5 Second-dataflow execution boundary

The FinQA second flow executes a frozen step-perturbation corpus under a hash-bound binding contract: 89 rows over 30 clusters, with per-row runtime bindings and a full trace map verified before scoring. The perturbation writes operator/argument fields; the observation vector records visibility, detection and outcome per row. Because downstream result fields are not recomputed from the mutated program semantics by construction, a zero detection count in this execution is not an estimate of detection ability; Section 5.6 states the resulting measurement-object boundary and the alternatives the evidence does not exclude. No threshold search, convention selection, or source-operator substitution is permitted in this flow.

### 4.6 FinRank external audit setup

FinRank contains manually authored questions, reference answers, gold passages and curated hard negatives over 22 companies. The released global pool contains 5,230 unique raw passage texts. The audit uses only the released JSONL, repository code, split/random seed and result files. TF-IDF and BM25 are regenerated from the official script with its released parameters; neural baselines are outside this audit.

The primary proposition is fixed before pair-level outcomes: the tie-positive policy and first-occurrence identity mapping may change absolute metric interpretation, while the paper's narrow curated-pool contract may keep the hard-versus-random conclusion stable. Materiality thresholds are 1.0 percentage point for pairwise values or hardness-gap movement and 0.5 point for global tie-order movement. The outcome classes are interpretation changed, narrower contract stable, or no substantive impact.

## 5. Results

### 5.1 Visibility depends on defect family

Checkpoint-level analysis makes 96/118 injections visible, but the aggregate hides a large family effect. 0/13 OCR-like injections were visible across 11 table clusters under all five thresholds; all 13 were invisible under this observation criterion. Other families range from 0.81 to 1.00 visibility at the primary setting. For uncertainty, the injection-level reference estimand is 0/13 with an exact binomial 95% interval of [0, 24.71%] under an independent-injection assumption; the distinct table-level event estimand is 0/11 with an exact binomial interval of [0, 28.49%]. The latter is not a clustered confidence interval for injection-level visibility. Figure 2 reports the full family-by-threshold visibility profile.

![Figure 2. Defect family × checkpoint visibility. Cell values are visibility rates at each threshold, annotated with visible/injection counts; the OCR-like family is 0/13 across 11 clusters at every tested threshold. This is a visibility matrix, not a harmfulness matrix.](../docs/research/figures_saner/fig2_family_visibility_matrix.png)

The family unobserved on the frozen scored surface remains the same under four edit-distance matcher configurations. However, the ordering of visible families is not invariant: changing the score normalization causes five class flips, all within the date-variation family, whereas switching from greedy to global assignment causes no flips. Thus, the existence of a family unobserved on the frozen scored surface is stable within the tested matcher family, but the full ranking is protocol-dependent.

The harmfulness label is also criterion-dependent, and our record contains two comparison kinds that should not be pooled. In the first kind, seven paired judge-versus-standard comparisons yield four disagreements; the two standards differ in the criterion they apply, with the standard asking whether the canonical form and canonical truth survive and the judge asking whether a reader can recover the same referent. In the second kind, a single visibility-versus-equivalence comparison contrasts deterministic channel evidence with standard equivalence, and that case carries no judge call. Because the two kinds measure different objects, we keep the raw cases and report neither a pooled disagreement rate nor a mechanism that would exclude case-level noise. In particular, the existing single judge, applying its table-context reader-referent contract, classified all 13 OCR-like perturbations as referentially equivalent. That supports benign absorption as an alternative interpretation of the non-response; it is not independent ground truth, and non-response alone does not establish harmful false negatives. We therefore report that this family is unobserved on the frozen scored surface, while treating whether that absence is harmful as a boundary question.

### 5.2 The raw hierarchy gap is a threshold-placement artifact

The raw detection counts are not evidence of protocol discriminability. Table 1 compares three transferable protocols under different decision predicates: end-to-end detection tests whether the final mapping text changes, whereas flat and hierarchical scoring use frozen score-drop thresholds. A changed source-header string can therefore count as end-to-end detection even when the canonical match is preserved, explaining why 112/118 exceeds the 96/118 visibility count. Table-level counts apply all assigned injections together, whereas injection-level counts apply one perturbation at a time; the 20 detected tables and 13 individually detected injections are not nested counts. At the frozen threshold, hierarchical scoring is not a more sensitive detector.

**Table 1. Protocol-level detection under different decision predicates.**

| Protocol | Detection signal | Tables detected | Injections detected |
|---|---|---:|---:|
| End-to-end | Final mapping change | 95/95 (1.0000) | 112/118 (0.9492) |
| Flat | Field-hit-rate drop | 75/95 (0.7895; 95% CI [0.6947, 0.8737]) | 85/118 (0.7203) |
| Hierarchical, expert weights | Pruned parsing-root drop | 20/95 (0.2105; 95% CI [0.1263, 0.2947]) | 13/118 (0.1102) |

The raw flat-hierarchical gap does not establish inferior ranking quality. In the current single-responsive-leaf construction, the unrounded hierarchical contrastive score is a positive rescaling of the flat contrastive score, with fitted slope approximately 0.375, and the recorded scores retain identical ranks; corresponding decisions, and by implication their ROC geometry, therefore coincide, and corresponding thresholds satisfy theta_H = 0.375 theta_F. This is a structural equivalence of the two protocols' decisions, not a newly calibrated performance estimate; the diagnosis is deliberately narrow: it explains why the raw protocol gap cannot be read as a ranking difference, and it is not offered as a general algebraic result about hierarchical evaluation. Separately, the registered deployment operating point remains unresolved: the derived clean-only reanalysis contains 2,382 usable clean records whose score supports are exactly {0}, so every positive threshold has an observed FPR of zero and the clean panel cannot select a unique operating point. That calibration degeneracy does not negate the structural equivalence, and it is a statement about the current clean-only procedure, not a general claim that matched-FPR comparisons cannot be made; the registered strict predicate FPR = alpha and the tolerance predicate FPR <= alpha also remain distinct. Selecting a threshold by harmful TPR would violate the clean-only contract. Historical fixed-threshold sensitivity evidence is retained in Appendix A.4, but the old [0,0] interval is not a clean-calibrated confirmatory result. When more than one leaf varies with the input, neither affine nor ranking equivalence is guaranteed.

The 118 injections close at the checkpoint level as 96 visible plus 22 silently absorbed; by family (injections / visible / absorbed): alias variant 47/43/4, date variant 17/15/2, mixed language 20/20/0, OCR-like 13/0/13, prefix noise 16/13/3, unit suffix 5/5/0 (frozen artifact listed in the evidence ledger). The protocol-level counts in Table 1 are measured on different signals and are therefore not a partition of the 96.

We label the affine-equivalence observation a degenerate-case result: it fixes the interpretation of the raw gap under the current single-varying-leaf construction and does not establish affine equivalence of the protocols in general.

### 5.3 Sensitivity and reproducibility

The identity of the family unobserved on the frozen scored surface is stable across the threshold grid. The absolute between-family range shrinks at high thresholds, as expected when one changed header contributes at most 1/n for a table with n canonical headers. The literal preregistered range criterion fails at 0.7 and 0.9, and this failure is reported.

Across three injection seeds, flat table-detection rates are 75/95 = 0.7895, 76/97 = 0.7835, and 68/90 = 0.7556. Their spread is 0.0339; the denominator-weighted pooled rate is 219/282 = 0.7766 with a percentile bootstrap 95% interval of [0.7270, 0.8227] over the pooled 282 table units (seed 20260830; endpoints on the k/282 grid). The seed-42 run reproduces the frozen artifact byte-for-byte.

Judge calibration covers 120 leaf-state cells; this calibration window is distinct from the 28-case semantic boundary analysis reported in Section 6. In the control-state comparison, rejudged summaries of historical 0–5 judgments differ from the frozen dimension means by at most 0.5, meeting the preregistered consistency expectation. This checks reproduction of aggregate dimension scores, not agreement between judges re-evaluating the same original answers. On the derived 0–10 root scale, control roots differ by at most 0.22, while individual leaves can move by as much as 7.0. Agreement is therefore an aggregate observation, not evidence of cell-level interchangeability.

### 5.4 Weight search produces an informative null

PSO and greedy coordinate ascent reach the same mean separation of 1.432574. PSO repeats the result on all five seeds but requires 7,650 evaluations, compared with 67 for greedy search. A minimax variant improves worst-case separation to 0.35714 while reducing mean separation to 1.25605. We therefore do not claim PSO superiority. The result instead shows that objective choice matters more than optimizer sophistication in the present search space.

### 5.5 Stage-aligned instrumentation: separable signatures and their boundary

![Figure 3. Multi-leaf localization and ablation. Perfect full-vector and direct-codebook bars are construct-sensitive on the explicitly instrumented controlled M/R/N observation surface. After directly targeted checkpoints are removed, non-direct top-1 equals chance (0.3333); under the frozen tie-as-incorrect rule these leaves still separate mapping from the retrieval and numeric stages without separating retrieval from numeric. Non-direct macro-F1 equals the uniform-class macro-F1 baseline (0.3333); the majority-class macro-F1 reference (0.1667) is plotted. The result reflects stage-aligned instrumentation, not emergent localization from the remaining hierarchy.](../docs/research/figures_saner/fig3_localization_ablation.png)

The preregistered stage-aligned study separated the three controlled stages perfectly on the explicitly instrumented surface: leave-one-cluster-out macro-F1 and top-1 accuracy are 1.000 with cluster-bootstrap 95% intervals [1.0, 1.0] and permutation p = 1/10001 = 1e-4, with zero ties and zero errors, against metric-specific baselines (chance top-1 1/3; majority macro-F1 1/6). The per-stage response profiles are disjoint within the construction: M moves the field-hit and table-regression leaves, R moves the source-required leaf, and N moves the reconciliation leaf. Figure 3 reports the localization and ablation outcome.

That positive result carries its boundary in the same rows. Re-scoring the identical 216 injections with the fixed three-direct-leaf codebook also yields macro-F1 and top-1 of 1.000; the non-direct leaves alone fall to 0.3333 with a tie rate of 0.6667, which is the three-class chance level and the uniform-class macro-F1 baseline; under the frozen tie-as-incorrect rule they distinguish the mapping stage from the retrieval and numeric stages but do not distinguish retrieval from numeric, so they carry partial rather than no stage information. A single any-response scalar collapses to 0.0 with ties everywhere. Eight of the twelve leaf columns are identically zero over all injections. Perfect separability therefore reflects explicit stage-aligned instrumentation in a contract-derived construction, not emergent localization from the remaining hierarchy, and the positive result is reported together with this ablation. Per-stage estimates are descriptive at this sample size; the population is the frozen controlled injection set, not a natural-failure distribution.

### 5.6 A second dataflow: a failed transfer consistent with a measurement-object mismatch

The FinQA second flow produced V = 89/89, D = 0/89 and O = 0/89: every injected change was observable on the mutated source fields, the frozen detection predicate never moved, and no downstream outcome field changed. The detection predicate here is defined and executable, and these counts are reproducible; what the perturbation does not do is regenerate the downstream result fields that the predicate reads. The zero detection count therefore describes this carrier construction rather than an estimated detection ability, and the mismatch is one of measurement objects, not of predicate definition. The formal result class is a mixed second-flow outcome; the accepted interpretation is a measurement-object mismatch, recorded in a separate autopsy. We therefore treat causal alignment of measurement objects as a design requirement for future transfers, not as a validated law. Scorer non-portability, threshold non-transfer and corpus shift are not excluded by this evidence, and no transfer, blindness or semantic-correctness claim is made from this flow.

### 5.7 Boundary case outside the main contribution

This case is not part of the evaluation-track contribution; it only marks the boundary between evaluation-track evidence and the broader reasoning-step question.

In a compact feedback example, a gain–collateral gate rejects all 7 adversarial high-confidence mappings and all 5 expanded-collision candidates. Across 15 collision tables, the gated-minus-ungated mean paired difference is 0.05 with a 95% interval of [0, 0.1056], while the exploratory pooled comparison is 7/40 versus 4/40 with exact McNemar p=0.375. This is not an efficacy claim.


### 5.8 External audit: stable hardness gap, sensitive score contract

Exact ties occur in both deterministic score matrices. For TF-IDF, hard/random pairwise accuracy is 77.756/91.935 under ties-positive and 77.030/90.850 under strict wins; the random-minus-hard gap moves from 14.179 to 13.821 points. For BM25, the corresponding values are 74.780/87.789 and 74.094/86.760, with the gap moving from 13.009 to 12.666. Half-credit ties lies between these policies. The absolute random-negative score changes by about 1.03-1.08 points, but the gap changes by only 0.34-0.36 points and preserves its direction. Five of 11,790 seed-42 random draws equal a curated hard negative, too few to explain the gap.

Inside each record, concatenating gold before negatives makes exact ties gold-first. Reversing tie priority lowers MRR by 0.101-0.108 points and nDCG@5 by 0.572-0.573 points. Forward-versus-reverse corpus order changes global metrics by at most 0.287 point in the full tie-order probe. The qualitative ordering is therefore stable under reasonable tie alternatives, while absolute scores and small ranking differences are contract-sensitive.

The identity audit reproduces the authors' disclosed limitations: 442 hard-negative occurrences across 305 records share a canonical text identity with another record's gold; the first-occurrence metadata filter causes some gold loss in 33 records and all-gold loss in 2. This is not an undisclosed contradiction: the README and paper explicitly disclose the overlap and first-occurrence limitation. The audit finds one documentation inconsistency: the repository README states 5,270 pooled entries, whereas the paper, released data and result files give 5,230, which is the value recomputed from the data.

Reproduction is exact for in-record MRR/nDCG and all pairwise metrics. Global metrics differ from the bundled result JSON by up to 0.19 point and metadata-filtered metrics by up to 0.16 point in the declared deterministic environment; a second available environment changes some global values by as much as 0.47 point. Without the original score matrices or complete execution environment, the residual cannot be attributed uniquely to tie order or dependency drift. The correct conclusion is a reproducibility boundary, not a benchmark failure.

## 6. Discussion and Limitations

The two cases support one measurement discipline. First, final or aggregate scores cannot establish what an evaluator observed, detected or considered harmful. Second, score algebra, tie policy, candidate order and identity construction can change absolute metrics without changing the decision a benchmark was designed to support. Third, mutation, observation, score, ranking and reported claim must be bound to the same causally updated measurement object before a cross-system comparison is interpreted.

The original staged case remains narrow. It uses synthetic perturbations on one public tabular corpus; harmfulness is contract-relative; the OCR-like family is unobserved rather than proven harmful; perfect stage localization is explained by explicit stage-aligned instrumentation; and the FinQA transfer attempt fails because the perturbed program does not regenerate the result fields read by the detector.

The FinRank audit is also narrow. Its source-identity correction is post-hoc even though the question and materiality thresholds were frozen before the corrected analysis. It examines TF-IDF and BM25, not neural baselines; it is source-informed because the paper and code disclose tie and identity behavior before the application; and it does not evaluate answer generation. The hard-negative ordering is stable under tested tie alternatives, but absolute pairwise accuracy is tie-policy sensitive. The exact cause of residual global metric drift is unresolved without the original score cache or locked transitive environment. The README count inconsistency should be corrected, and an exact-reproduction claim should specify platform, dependencies and numerical tolerance or ship rankings and score matrices.

A later AI-assisted development review of 24 candidate evidence-selection tasks
adds post-hoc design observations, not preregistered FinRank results. Several
questions require entity, content-period, form or unit semantics to be stated
before evidence sufficiency is meaningful; one task has two sufficient evidence
subsets; and one locally extracted table conflicts with its source disclosure.
These cases reinforce the need to bind the measurement contract to the actual
question and returned evidence. They do not establish a new gold standard,
independent validation, or a defect in the original FinRank annotations.

This is not a universal audit method. Generic construct-validity reviews and metric-audit frameworks already cover much of the umbrella problem. The defensible residue is the concrete, two-case identification analysis: separating score-contract sensitivity from decision stability and exposing measurement-object or reproducibility boundaries before stronger claims are made.

The proposed review sequence is therefore an application-ready design proposal:
1. identify the observation surface and its instruments;
2. bind each perturbation to the recomputed measurement object;
3. inspect score algebra, tie policy and threshold identifiability;
4. preserve source identity and equivalence contracts;
5. test whether the result changes a real report, model-selection or measurement decision;
6. report negative or stable results and the exact reproducibility envelope.

## 7. Conclusion

Final correctness or aggregate ranking quality does not reveal whether a staged evaluation observed a defect, consumed an intermediate signal, or preserved the source identity its construct requires. Across a controlled document evaluator and a real evidence-ranking benchmark, we show that observation surfaces, score contracts and measurement-object binding determine what a comparison can identify. In the first case, family-level visibility, score equivalence and instrumentation attribution remove three tempting over-readings. In FinRank, tie policy moves absolute pairwise scores while the qualitative hard-versus-random conclusion remains stable; source-identity limitations reproduce; and a small residual reproducibility gap remains. The result is a bounded two-case measurement audit and a review discipline for evaluator authors, not a universal validity theory or a detector ranking.

## Data Availability

The staged evaluation corpus is derived from public TAT-QA tables. Frozen perturbation, checkpoint, aggregation and analysis artifacts, together with exact revisions and hashes, are prepared as an anonymized release package. The external audit uses FinRank revision `916dc27e77b90e294ea1b3a2cc5b0abcf07392d1`, arXiv `2608.07400v1`, the released `FinRank.jsonl`, baseline code and result JSON under CC BY-NC 4.0. The audit script, pre-registration, fixtures, full application rows and source manifest are included with the revision draft. No private data, model inference or paid research API is required to reproduce the deterministic audit.

## References

- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics. arXiv:2210.15615, 2022.
- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets at WMT 2023. arXiv:2311.01153, 2023.
- Berndt, A., Bekmyradov, V., Gemulla, R., Kessel, M., Bach, T., and Baltes, S. Can We Classify Flaky Tests Using Only Test Code? An LLM-Based Empirical Study. In Proc. IEEE Int. Conf. on Software Analysis, Evolution and Reengineering (SANER), RENE track, 2026. DOI: 10.1109/SANER67736.2026.00016.
- Bean, A. M., Kearns, R. O., Romanou, A., et al. Measuring what Matters: Construct Validity in Large Language Model Benchmarks. arXiv:2511.04703, 2025.
- Caban, W. Measurement Without Validity: The Compounding Reliability Problem in Agentic AI Evaluation. arXiv:2608.00794, 2026.
- Cho, S., Ruberto, S., and Terragni, V. Metamorphic Testing of Large Language Models for Natural Language Processing. arXiv:2511.02108, 2025.
- Chung, J., Byun, J., Vineet, V., and Kim, S. J. Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking. arXiv:2606.15673, 2026.
- Deviyani, A., and Diaz, F. Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy. arXiv:2503.19828, 2025.
- Du, S., Liang, P., Shen, Y., et al. On the Stability of Prompt Ranking in Large Language Model Evaluation. arXiv:2606.24381, 2026.
- Fan, S., Ye, X., Huo, Y., et al. AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents. arXiv:2603.14465, 2026.
- Gerhold, M., Solovyeva, L., and Zaytsev, V. The Limits of the Identifiable: Challenges in Python Version Identification with Deep Learning. In Proc. IEEE Int. Conf. on Software Analysis, Evolution and Reengineering (SANER), RENE track, 2024. DOI: 10.1109/SANER60148.2024.00022.
- Hoess, N., Paradis, C., Kazman, R., and Mauerer, W. Does the Tool Matter? Exploring Some Causes of Threats to Validity in Mining Software Repositories. In Proc. IEEE Int. Conf. on Software Analysis, Evolution and Reengineering (SANER), RENE track, 2025. DOI: 10.1109/SANER64311.2025.00067.
- Kendiukhov, I. Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking. arXiv:2603.03493, 2026.
- Kummita, S., Schiebel, F., Bodden, E., Miao, M., and Wei, S. Static Analysis Traces can Help Dynamic Symbolic Execution: a Replication Study. In Proc. IEEE Int. Conf. on Software Analysis, Evolution and Reengineering (SANER), RENE track, 2026. DOI: 10.1109/SANER67736.2026.00114.
- Mansouri, S., Saad, D., Wahrenburg, M., Weissel, M., and Woebbeking, F. FinRank: An Evidence-Grounded Benchmark for Financial Question Answering and Retrieval over SEC Filings. arXiv:2608.07400, 2026.
- Li, Q., Dou, S., Shao, K., Chen, C., and Hu, H. Evaluating Scoring Bias in LLM-as-a-Judge. arXiv:2506.22316, 2025.
- Li, S., Xu, C., Wang, J., et al. LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge. arXiv:2506.09443, 2025.
- Moghe, N., Fazla, A., Amrhein, C., et al. Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets. arXiv:2401.16313, 2024.
- National Institute of Standards and Technology. Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1, January 2023. https://doi.org/10.6028/NIST.AI.100-1.
- National Institute of Standards and Technology. Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile. NIST AI 600-1, July 2024. https://doi.org/10.6028/NIST.AI.600-1.
- Ross, C., Hall, M., Romero Soriano, A., and Williams, A. What Makes a Good Metric? Evaluating Automatic Metrics for Text-to-Image Consistency. arXiv:2412.13989, 2024.
- Tan, G., Sun, Z., Shi, J., et al. AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection. arXiv:2608.06790, 2026.
- Wang, J., et al. GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows. arXiv:2604.15715, 2026.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv:2306.05685, 2023.

## Appendix A. Deferred independent-evidence record

This appendix preserves the internal evidence and preregistration record for deferred extensions. These materials are boundary records, not evaluation-track results.

### A.1 Reinstatement criteria

Reinstatement criteria, not a timeline: the deferred arms return only when (i) a second dataflow with a table layer passes the source-identity and split gates with UID-disjoint layers, and (ii) a second scorer independent of the local judge reproduces the leaf-state cells; until both hold, the arms remain preregistered-but-unreported.

### A.2 Second-dataflow record

Progress against criterion (i) is now measurable, clause by clause. Three corpora answer different clauses and are named separately: the acquisition corpus (FinQA, taken under the approved minimal scope), the action corpus (a schema-matching benchmark of ten table pairs), and the transfer corpus whose missing table layer triggered the original deferral. The source-identity gate passed on 2026-09-25 for the acquisition corpus, with per-file digests recorded. Its table layer is present and uniform: all 7134 examples carry a non-empty rectangular table whose first row is entirely string-valued, with two to eleven columns, so the clause that deferred the transfer corpus, the absence of a table layer, does not apply to the acquisition corpus. A deterministic, label-blind split instrument now assigns layers whose independence clusters are report-level rather than dataset-level, and on the acquisition corpus the four role layers are geometrically fillable, with 2409 lineage UIDs over 768 report clusters at full population. The split gate is nonetheless not passed: the acquisition corpus has its own gate and sealed partitions withheld because its registered role list does not include them, while the action corpus, which is the one that carries an action vocabulary, contains ten table-pair clusters and under the frozen hash-threshold bucketing rule leaves the development layer empty, yielding ten independent units. The remaining gap is structural rather than incremental, and it belongs to the label gate, not to criterion (i): the acquisition corpus publishes no official canonical vocabulary for table columns, so action labels could only be constructed by inventing a schema. Here, a table layer makes samples definable; it does not supply the gold those samples need.

### A.3 Independent-scorer record

Criterion (ii) has not been tested, and one candidate route toward it was stopped by its own pre-registration. A model-free detector, independent of the local judge, was built over a corpus of 1970 frozen step-level records whose contents and fault families were fixed before any detector existed, and whose percent-convention stop threshold was pre-registered before the second detector run produced any output. Its pre-registration fixed a fidelity threshold in advance, and that threshold was not reached: fidelity of the reconstructed step semantics on percent-form results was 0.0298 under one percent convention and 0.2233 under the other (44 and 330 matches out of 1478 percent-form steps, respectively), both below the pre-set 0.5, so the route was stopped rather than re-parameterized. Because that detector measures reasoning-step checkpoints while criterion (ii) concerns reproduction of the frozen header-injection leaf-state cells, the two are different measurement objects; the leaf-state reproduction clause therefore remains untested rather than failed, and what the fired stop condition establishes is the boundary of the step-level route itself. The portion of that corpus with faithful reconstruction covers 322 records of 1970 under the convention yielding 0.0298, and 467 under the one yielding 0.2233, i.e. 16.3% to 23.7%, and is reported to bound the route, not as a capability.

### A.4 Historical matched-FPR sensitivity

The earlier fixed-threshold analysis reported 90/111 for both flat and hierarchical protocols and a zero-difference bootstrap interval under a historical fixed-threshold sensitivity setup. Those numbers remain archived evidence for that setup only. The newer clean-only cross-fitted audit found zero-valued clean score supports and therefore could not identify a unique FPR-constrained threshold. Accordingly, the historical equality is not promoted to a clean-calibrated confirmatory claim and is not used to rank the protocols.
