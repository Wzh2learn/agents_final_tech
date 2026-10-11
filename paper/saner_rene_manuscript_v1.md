# Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation

## Abstract

Long-horizon AI systems are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. We audit the observation surface of a staged document-intelligence evaluation using controlled perturbations. On a frozen public tabular corpus (95 tables, 118 controlled header perturbations in six families), 96 injections are checkpoint-visible, while the OCR-like family is unobserved on the frozen scored surface (0/13 injections across 11 clusters at every tested threshold). In the single-responsive-leaf construction, flat and layered contrastive scores are a positive affine/rank transform of one another, and a clean-only matched-FPR operating point is not identifiable, so the frozen evidence cannot rank the two protocols at matched FPR. A preregistered stage-aligned instrumentation study (mapping, retrieval and numeric perturbations; 72 clusters, 216 injections) yields perfectly separable stage signatures (leave-one-cluster-out macro-F1 and top-1 accuracy 1.0; permutation p = 1e-4). The same direct three-leaf codebook also reaches 1.0 while non-direct leaves fall to the three-class chance level (0.3333): the signatures reflect explicit stage-aligned instrumentation in a contract-derived construction, not emergent localisation from hierarchy. A second dataflow (FinQA program perturbations; 89 rows, 30 clusters) could not be transferred: everything was observable by construction and nothing was detected downstream (V=89/89, D=0/89, O=0/89), consistent with a measurement-object mismatch rather than protocol blindness. The contribution is a measurement-validity audit: visibility, detection and harmfulness are distinct constructs; the observation surface itself requires auditing per dataflow; and hierarchical organisation alone does not guarantee diagnosability.

## 1. Introduction

Document-intelligence systems are increasingly implemented as staged pipelines: a document is decoded, segmented into tables, mapped to a canonical schema, reconciled arithmetically, and queried. The same shift appears across tool-using agents and long-horizon workflows, where a final output is produced by a sequence of observable intermediate steps. Such systems are typically scored by final-answer correctness. Final correctness, however, cannot distinguish a defect that was observed at an intermediate checkpoint from one that was silently absorbed by the pipeline, and it cannot reveal a defect that the evaluation protocol is itself unable to observe. Aggregating a pipeline into a single score therefore hides the property we care about first: whether the evaluation can observe the failures it is supposed to assess.

We make that property explicit with three constructs, kept separate throughout. *Visibility* asks whether any instrument on the observation surface registers a defect. *Detection* asks whether the protocol's decision predicate consumes that observation under its stated threshold rule. *Harmfulness* asks whether the defect changes the outcome under a stated equivalence contract. These are different measurement objects: visibility is a property of instruments, detection a property of decision rules, and harmfulness a property of contracts. Confounding them produces comparisons that look quantitative but are not identified - for example, comparing protocols under different predicates and reading a sensitivity ordering into the counts.

![Figure 1. The measurement chain. An injected failure in a staged pipeline moves through checkpoint visibility (did any instrument observe it?), protocol detection (did the decision rule consume the observation under its threshold rule?), and outcome harm (does the outcome change under the stated equivalence contract?). NIST motivates measurement effectiveness, not this paper's blind-spot framework.](../docs/research/figures_saner/fig1_measurement_chain.svg)

We study these distinctions through controlled fault injection on a frozen public tabular corpus, and we carry the instrument to two further settings: a preregistered stage-aligned instrumentation study on the same corpus, and a second dataflow of program perturbations (FinQA) executed under a frozen binding contract. The paper answers three questions per setting: (RQ1) what boundaries does the observation surface have, and how do they vary by defect family; (RQ2) are protocol comparisons on that surface empirically identified; and (RQ3) what follows when stage-aligned instrumentation is added, and what happens when another dataflow's measurement objects do not causally align with its detection predicate. Our contributions are a construct separation with quantified family-level observation boundaries; a protocol-identifiability audit, including a clean-only matched-FPR non-identifiability result and a construction-bounded instrumentation result with its ablation; and a failed-transfer autopsy that is consistent with a measurement-object mismatch. We claim no universal blind spots, no hierarchy-localisation, and no causal-aware checkpoint-selection method; the evidence comes from one frozen corpus with synthetic perturbations and one failed second dataflow, and no natural-failure distribution is measured. Measurement-validity and construct-validity concerns motivate auditing an evaluation surface before trusting its scores [NIST AI 100-1, 2023]; that framing is motivation only, and NIST does not certify the metrics used here.

## 2. Related Work

### 2.1 Meta-evaluation

Machine-translation challenge sets such as ACES evaluate whether a metric can distinguish genuine errors from acceptable variants [Amrhein et al., 2022; Amrhein et al., 2023; Moghe et al., 2024]. Contextual metric meta-evaluation extends this view to local, context-dependent correctness [Deviyani and Diaz, 2025]. More recent studies show that rankings can change with protocol axes, prompt subsets, seeds, or the property a metric is intended to measure [Kendiukhov, 2026; Du et al., 2026; Ross et al., 2024]. We adopt the same meta-evaluation principle but focus on a prior question: whether a long-horizon protocol can observe an injected defect at all.

### 2.2 Process-level and hierarchical evaluation

Process-oriented benchmarks diagnose intermediate behavior in tool-using and web agents rather than scoring only final success [Fan et al., 2026; Chung et al., 2026]. GTA-2 represents a task as recursively aggregated checkpoints [Wang et al., 2026]. Our aggregation follows this structure, while adding deterministic contracts, explicit missing-evidence behavior, and controlled injections that expose the evaluator's sensitivity by defect family.

### 2.3 Mutation testing and fault injection

Mutation testing and metamorphic testing introduce controlled changes to measure whether a test or metric notices them [Cho et al., 2025]. AgentChaos applies programmatic fault injection to agent systems [Tan et al., 2026]. These traditions usually summarize each mutant as killed or surviving. We refine surviving or non-detected mutants by distinguishing silent absorption, unobservability at the scored layer, and equivalence-dependent interpretation, then report those mechanisms by defect family. We distinguish evaluator blindness from mutants whose intended effect is not represented on the scored observation surface. We reserve the term invalid mutant for cases that fail a separate validity audit.

### 2.4 Reliability of semantic judges

LLM judges are useful for open-semantic qualities but exhibit position, verbosity, self-preference, and perturbation sensitivity [Zheng et al., 2023; Li et al., 2025a; Li et al., 2025b]. We therefore reserve deterministic checks for contractible properties, use a judge only for semantic dimensions, hide injected ground truth from the judge prompt, and report the judge's resolution and sample limits explicitly. The distinction from prior process-level work is deliberate: those methods diagnose system behavior, whereas this paper first audits whether the evaluator can observe a controlled defect before interpreting that behavior.

## 3. Method

The conceptual core is a three-way audit of visibility, detection, and harmfulness; the hierarchical checkpoint forest is the evidence instrument that makes the audit reproducible.

### 3.1 Evidence instrument: checkpoint forest

We model the pipeline as two checkpoint trees. The parsing tree covers document ingestion, table structure, field mapping, and arithmetic reconciliation. The QA tree covers retrieval grounding, faithfulness, numeric correctness, citation quality, and appropriate refusal. Together the trees contain 12 scored leaves.

The twelve scored nodes are five in the parsing tree (document status, document throughput, table regression, field hit-rate, reconciliation equations) and seven in the QA tree (retrieval contract, faithfulness judge, numeric contract, number grounding, citation judge, refusal judge, refusal contract), per config/eval_checkpoint_trees.json v0.1.0. The visibility audit exercises the parsing-tree leaves whose evidence is the mapping and regression artifacts; under the frozen drop rule (drop = (H_orig - H_inj) x 10, threshold 2.0) only the field hit-rate leaf responds to header drift, while QA-tree leaves keep their frozen evidence and the QA arm is reported separately (12 calls at the same endpoint). This is precisely why additional localization value remains unestablished in the current instantiation. In Table 1, the label 'Pruned parsing-root drop' denotes exactly this operation: the parsing root is collapsed to its single input-responsive leaf (the field hit-rate leaf) and the drop rule above is applied there.

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
- **Silently absorbed:** normalization or matching preserves the canonical correspondence, so that checkpoint does not expose the perturbation.

Harmfulness is a separate, **equivalence-dependent** judgment, not a mutually exclusive visibility outcome: canonical-form preservation and reader-referent recoverability need not agree.

The defect visibility profile reports visibility separately for each family. This preserves information lost by a single mutation score and distinguishes a missing checkpoint from a genuinely robust stage.

### 3.3 Evaluating the evaluator

We compare four protocols on frozen evidence: end-to-end roots, a flat leaf average, hierarchical expert weights, and hierarchical searched weights. We measure table-level detection, injection-level detection, mean separation between clean and perturbed states, worst-family behavior, localization, and evaluation cost. Because raw thresholds can manufacture differences, we separately audit (i) structural score/ranking equivalence and (ii) whether a matched-FPR operating point is identifiable from clean scores alone.

The audit further varies the injection seed, visibility threshold, matching algorithm, and scoring normalization. A semantic-judge arm is evaluated separately and never substituted for deterministic evidence when a contract exists.

### 3.4 Stage-aligned instrumentation and the second dataflow

The evaluation-track instrument is a two-root checkpoint forest whose twelve leaves map deterministic or judge-derived evidence to a 0-10 score (Section 3.1). To test whether stage-aligned instrumentation carries stage information, we preregister a separate controlled study on the same corpus. Each stage contract perturbs one operation - a header token is replaced (mapping stage M), required source blocks are removed from the retrieval bundle (retrieval stage R), or one numeric operand is broken while labels, schema and identity are preserved (numeric stage N). Every cluster contributes three deterministic injections, and each injection is scored on the same twelve-leaf surface, producing a binary response vector; 24 clusters per stage give 72 clusters and 216 injections. The study is frozen before results (hash receipt) and evaluated leave-one-cluster-out. The same document defines the protocol's deliberate boundary: response predicates are written from the stage contracts, so the construction is explicitly instrumented and its separability must be interpreted within that construction.

The second dataflow is a program-perturbation corpus built from FinQA reasoning steps. Perturbations act on a step's operator or argument fields while the downstream result fields are not recomputed; the observation objects are visibility (does the injected change appear in the observed source fields), detection (does the frozen detection predicate move), and outcome (does any downstream outcome field change). The execution contract binds artifact hashes before scoring, and no threshold or convention search is permitted. Section 4.5 states the execution boundary; Section 5.6 reports what happened and what it does and does not establish.

## 4. Experimental Setup

### 4.1 Corpus and perturbations

The study uses a frozen public tabular base and contains no client data. It includes 95 tables and 118 synthetic injections across six header-drift families. Schema and header matching are the perturbation carrier in this instantiation; the object of study is the evaluation protocol's observation boundary. Each injected record preserves its source table, family, seed, changed field, and expected observation surface.

Concretely, the base is the frozen drift-v0 table set derived from public TAT-QA tables (data/research/drift_v0/input/tatqa_tables.json, sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302); the corpus was frozen before this study's data gates and no new TAT-QA use is introduced. The perturbations are the fully synthetic injection map (data/research/drift_v0/output/injection_map.json, sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e; deterministic, seed 42, ratio 0.3). The primary matcher is the production greedy header matcher (scripts/m1_statement_parser.py, map_headers); the cross-matcher audit adds greedy-normalized, hungarian-production, and hungarian-normalized configurations. Semantic leaves are scored by the M2 judge pipeline (source tag m2_judge in config/eval_checkpoint_trees.json), i.e. Qwen3.6-35B-A3B (Q4_K_M GGUF) served at 127.0.0.1:8004, with 0-5 dimension scores mapped to [0,10]. The primary threshold grid is

\[
\Gamma=\{0.2,0.3,0.5,0.7,0.9\}.
\]

The OCR-like family contains 13 single-token, lowercase Levenshtein-distance-one substitutions with unchanged column values. These properties are mechanically recomputed before interpretation.

### 4.2 Baselines and controls

The protocol baselines are end-to-end scoring, flat leaf scoring, and hierarchical scoring with expert weights. Weight-search controls include equal weights, expert weights, 30 random trials, greedy coordinate ascent, particle-swarm optimization (PSO), and a minimax objective. Assignment controls compare greedy matching with Hungarian global assignment and include a positive solver test.

### 4.3 Statistical discipline

We freeze inputs and decision criteria before reading each result. Confidence intervals are reported on table-level clustered units where available (percentile bootstrap over the 95 table units, seed 20260830; endpoints on the k/95 grid for the 95-table arm). Seed sensitivity uses three injection seeds. For the clean-only matched-FPR audit, threshold selection may use clean scores only; injected and harmful outcomes are prohibited from calibration. Because the frozen clean supports are degenerate, non-identifiability is reported rather than forced into an empirical equality. The 2,382 clean records are the usable (table_uid, column) rows of the non-injected source tables in the frozen D3 inputs, with fold assignment = sorted(table UID) index modulo 5. Null and adverse findings are retained rather than relabeled as improvements.

### 4.4 Multi-leaf stage-aligned protocol

The stage-aligned study uses the same frozen tabular base and the same twelve-leaf surface. Stage contracts and injection generators are deterministic; clusters are selected by an outcome-blind hash rule (seed frozen before results), and the pre-result freeze receipt binds the corpus, the generator, the runner and the environment by hash. Response predicates are contract-derived: for M the directly targeted parse leaves move; for R the retrieval leaf moves; for N the reconciliation leaf moves. Baselines are the metric-specific chance top-1 (1/3) and majority macro-F1 (1/6); uncertainty uses leave-one-cluster-out evaluation with 10,000 cluster-bootstrap resamples and a 10,000-replicate permutation null, both seeds frozen. The ablation re-scores the same rows with (i) the full twelve-leaf vector, (ii) the fixed three-direct-leaf codebook, (iii) non-direct leaves only, and (iv) a single any-response scalar.

### 4.5 Second-dataflow execution boundary

The FinQA second flow executes a frozen step-perturbation corpus under a hash-bound binding contract: 89 rows over 30 clusters, with per-row runtime bindings and a full trace map verified before scoring. The perturbation writes operator/argument fields; the observation vector records visibility, detection and outcome per row. Because downstream result fields are not recomputed from the mutated program semantics by construction, a zero detection count in this execution is not an estimate of detection ability; Section 5.6 states the resulting measurement-object boundary and the alternatives the evidence does not exclude. No threshold search, convention selection, or source-operator substitution is permitted in this flow.

## 5. Results

### 5.1 Visibility is strongly defect-type dependent

Checkpoint-level analysis makes 96/118 injections visible, but the aggregate hides a large family effect. 0/13 OCR-like injections were visible across 11 table clusters under all five thresholds; all 13 were invisible under this observation criterion. Other families range from 0.81 to 1.00 visibility at the primary setting. For uncertainty, the injection-level reference estimand is 0/13 with an exact binomial 95% interval of [0, 24.71%] under an independent-injection assumption; the distinct table-level event estimand is 0/11 with an exact binomial interval of [0, 28.49%]. The latter is not a clustered confidence interval for injection-level visibility.

![Figure 2. Defect family x checkpoint visibility. Cell values are visibility rates at each threshold, annotated with visible/injection counts; the OCR-like family is 0/13 across 11 clusters at every tested threshold. This is a visibility matrix, not a harmfulness matrix.](../docs/research/figures_saner/fig2_family_visibility_matrix.png)

The family unobserved on the frozen scored surface remains the same under four edit-distance matcher configurations. However, the ordering of visible families is not invariant: changing the score normalization causes five class flips, all within the date-variation family, whereas switching from greedy to global assignment causes no flips. Thus, the existence of a family unobserved on the frozen scored surface is stable within the tested matcher family, but the full ranking is protocol-dependent.

The harmfulness label is also criterion-dependent. An instance-level oracle rejects all seven members previously placed in a type-level equivalence class. Across eight paired comparisons, five disagree, and the disagreements align with criterion kind—canonical-form preservation versus reader-referent recoverability—rather than appearing as random case-level noise. We therefore report that this family is unobserved on the frozen scored surface, while treating whether that absence is harmful as a boundary question.

### 5.2 The raw hierarchy gap is a threshold-placement artifact

The raw detection counts are not evidence of protocol discriminability. Table 1 compares three transferable protocols under different decision predicates: end-to-end detection tests whether the final mapping text changes, whereas flat and hierarchical scoring use frozen score-drop thresholds. A changed source-header string can therefore count as end-to-end detection even when the canonical match is preserved, explaining why 112/118 exceeds the 96/118 visibility count. Table-level counts apply all assigned injections together, whereas injection-level counts apply one perturbation at a time; the 20 detected tables and 13 individually detected injections are not nested counts. At the frozen threshold, hierarchical scoring is not a more sensitive detector.

| Protocol | Detection signal | Tables detected | Injections detected |
|---|---|---:|---:|
| End-to-end | Final mapping change | 95/95 (1.0000) | 112/118 (0.9492) |
| Flat | Field-hit-rate drop | 75/95 (0.7895; 95% CI [0.6947, 0.8737]) | 85/118 (0.7203) |
| Hierarchical, expert weights | Pruned parsing-root drop | 20/95 (0.2105; 95% CI [0.1263, 0.2947]) | 13/118 (0.1102) |

The raw flat--hierarchical gap does not establish inferior ranking quality. In the current single-responsive-leaf construction, the hierarchical contrastive score is a positive affine transform of the flat contrastive score with slope approximately 0.375. The scores therefore induce identical rankings and, by implication, identical ROC/AUROC geometry; corresponding thresholds satisfy theta_H = 0.375 theta_F. This is a structural result, not an empirical matched-FPR equality. The derived clean-only reanalysis contains 2,382 usable clean records with both score supports exactly {0}; every positive threshold has observed FPR zero, so the clean set cannot identify a unique operating threshold. Selecting a threshold by harmful TPR would violate the clean-only contract. Historical fixed-threshold sensitivity evidence is retained in Appendix A.4, but the old [0,0] interval is not a clean-calibrated confirmatory result. When more than one leaf varies with the input, neither affine nor ranking equivalence is guaranteed.

The 118 injections close at the checkpoint level as 96 visible plus 22 silently absorbed; by family (injections / visible / absorbed): alias variant 47/43/4, date variant 17/15/2, mixed language 20/20/0, OCR-like 13/0/13, prefix noise 16/13/3, unit suffix 5/5/0 (frozen artifact t2_visibility_sensitivity.json; path in the evidence ledger). The protocol-level counts in Table 1 are measured on different signals and are therefore not a partition of the 96.

We label the affine-equivalence observation a degenerate-case result: it fixes the interpretation of the raw gap under the current single-varying-leaf instantiation and does not establish affine equivalence of the protocols in general.

### 5.3 Sensitivity and reproducibility

The identity of the family unobserved on the frozen scored surface is stable across the threshold grid. Absolute between-family range contracts at high thresholds, as expected when one changed header contributes at most 1/n for a table with n canonical headers. The literal preregistered range criterion fails at 0.7 and 0.9 and is reported as failed.

Across three injection seeds, flat table-detection rates are 75/95 = 0.7895, 76/97 = 0.7835, and 68/90 = 0.7556. Their spread is 0.0339; the denominator-weighted pooled rate is 219/282 = 0.7766 with a percentile bootstrap 95% interval of [0.7270, 0.8227] over the pooled 282 table units (seed 20260830; endpoints on the k/282 grid). The seed-42 run reproduces the frozen artifact byte-for-byte.

Judge calibration covers 120 leaf-state cells; this calibration window is distinct from the 28-case semantic boundary analysis reported in Section 6. In the control-state comparison, rejudged summaries of historical 0–5 judgments differ from the frozen dimension means by at most 0.5, meeting the preregistered consistency expectation. This checks reproduction of aggregate dimension scores, not agreement between judges re-evaluating the same original answers. On the derived 0–10 root scale, control roots differ by at most 0.22, while individual leaves can move by as much as 7.0. Agreement is therefore an aggregate observation, not evidence of cell-level interchangeability.

### 5.4 Weight search produces an informative null

PSO and greedy coordinate ascent reach the same mean separation of 1.432574. PSO repeats the result on all five seeds but requires 7,650 evaluations, compared with 67 for greedy search. A minimax variant improves worst-case separation to 0.35714 while reducing mean separation to 1.25605. We therefore do not claim PSO superiority. The result instead shows that objective choice matters more than optimizer sophistication in the present search space.

### 5.5 Stage-aligned instrumentation produces separable signatures - and its boundary

![Figure 3. Multi-leaf localization and ablation. Perfect full-vector and direct-codebook bars are construct-sensitive on the explicitly instrumented controlled M/R/N observation surface. After directly targeted checkpoints are removed, non-direct top-1 equals chance (0.3333); non-direct macro-F1 equals the uniform-class macro-F1 baseline (0.3333) but remains above the plotted majority macro-F1 baseline (0.1667). The result reflects stage-aligned instrumentation, not emergent localization from the remaining hierarchy.](../docs/research/figures_saner/fig3_localization_ablation.png)

The preregistered stage-aligned study separated the three controlled stages perfectly on the explicitly instrumented surface: leave-one-cluster-out macro-F1 and top-1 accuracy are 1.000 with cluster-bootstrap 95% intervals [1.0, 1.0] and permutation p = 1/10001 = 1e-4, with zero ties and zero errors, against metric-specific baselines (chance top-1 1/3; majority macro-F1 1/6). The per-stage response profiles are disjoint within the construction: M moves the field-hit and table-regression leaves, R moves the source-required leaf, and N moves the reconciliation leaf.

That positive result carries its boundary in the same rows. Re-scoring the identical 216 injections with the fixed three-direct-leaf codebook also yields macro-F1 and top-1 of 1.000; the non-direct leaves alone fall to 0.3333 with a tie rate of 0.6667 - the three-class chance level and the uniform-class macro-F1 baseline - and a single any-response scalar collapses to 0.0 with ties everywhere. Eight of the twelve leaf columns are identically zero over all injections. Perfect separability therefore reflects explicit stage-aligned instrumentation in a contract-derived construction, not emergent localisation from the remaining hierarchy, and the positive result is reported together with this ablation. Per-stage estimates are descriptive at this sample size; the population is the frozen controlled injection set, not a natural-failure distribution.

### 5.6 A second dataflow: a failed transfer consistent with a measurement-object mismatch

The FinQA second flow produced V = 89/89, D = 0/89 and O = 0/89: every injected change was observable on the mutated source fields, the frozen detection predicate never moved, and no downstream outcome field changed. This triple is what the construction predicts when the detection objects and the perturbation objects are not causally aligned: the detection rule consumes result fields that the perturbation does not recompute, so the zero detection count follows from the construction rather than from an inability to detect. The formal result class is a mixed second-flow outcome; the accepted interpretation is a measurement-object mismatch, recorded in a separate autopsy. We therefore treat causal alignment of measurement objects as a design requirement for future transfers, not as a validated law. Scorer non-portability, threshold non-transfer and corpus shift are not excluded by this evidence, and no transfer, blindness or semantic-correctness claim is made from this flow.

### 5.7 Boundary case outside the main contribution

This boundary case is not part of the evaluation-track contribution; it only marks where Stage E evidence stops and the broader Stage R question begins.

In a compact feedback example, a gain–collateral gate rejects all 7 adversarial high-confidence mappings and all 5 expanded-collision candidates. Across 15 collision tables, the gated-minus-ungated mean paired difference is 0.05 with a 95% interval of [0, 0.1056], while the exploratory pooled comparison is 7/40 versus 4/40 with exact McNemar p=0.375. This is not an efficacy claim.


## 6. Discussion and Limitations

### 6.1 Scientific limitations

The main finding is methodological. Aggregate evaluation can hide both system defects and defects unobserved on the scored surface. A checkpoint forest makes evidence decomposable, while a visibility profile shows which defect families are observable. Yet structure alone does not guarantee sensitivity: in the current single-responsive-leaf construction, flat and hierarchical scores are affine/rank-equivalent, while a clean-only empirical matched-FPR operating point is not identifiable.

Four limitations bound the claim. First, the evidence comes from one public tabular corpus with synthetic perturbations; no cross-domain generalization is claimed. Second, the OCR-like family is unobserved on the frozen scored surface, but whether each perturbation is harmful depends on the equivalence definition. Third, the semantic boundary analysis uses one judge on 28 cases; mixed-language and unit-suffix families receive no calls in that window (a separate window from the 120-cell judge calibration of Section 5.3). Fourth, under shared-header overlays the oracle correctness ceiling changes from 20/21 = 0.952381 to 40/67 = 0.597015 (the two figures use different denominators; this is not a ratio comparison), while global assignment changes no decision, locating the problem in score construction rather than allocation.

### 6.2 Deferred independent evidence

A preregistered second-dataflow extension did not satisfy its structural prerequisites and is therefore not used as evidence. A preregistered independent-scorer route triggered its pre-registered stop condition and is therefore not reported as a capability result. The criterion-relativity claim remains limited to the current evaluator and corpus; the detailed governance record is retained in Appendix A.




### 6.3 Integrating the observation surfaces

Three results share one structure. First, the frozen evaluation surface has a family-level boundary: the OCR-like family is unobserved across all tested thresholds and clusters while the remaining families are observed at rates from 0.81 to 1.00. Second, adding observations along the failure path changes what is diagnosable: with stage-aligned instrumentation the controlled stages separate perfectly, and when the directly targeted leaves are removed the remaining hierarchy carries no stage information - what a surface can diagnose is set by its instrumentation, not by its organisation. Third, when another dataflow is measured with a predicate that does not share its perturbation's object, the comparison is not estimable: the FinQA flow reports a construction-induced zero on detection, and the correct conclusion is a boundary rather than a performance number. Read together, the results support a measurement-validity discipline: audit an observation surface and its measurement objects per dataflow before trusting aggregate scores. The evidence remains bounded by one frozen public corpus with synthetic perturbations, one controlled instrumentation study, no natural-failure distribution, harmfulness defined relative to an equivalence contract, and a second dataflow that failed for measurement-object reasons. These limits define the paper's claims.

## 7. Conclusion

Final correctness cannot tell whether a defect was observed at an intermediate checkpoint, silently absorbed, or invisible to the evaluator itself. We introduced a three-way audit of visibility, detection, and harmfulness, implemented with hierarchical checkpoint evidence and per-family visibility profiles. On 118 controlled injections, observability and detection depend strongly on defect family and decision protocol. The central result is structural rather than a detector ranking: flat and hierarchical scores are affine/rank-equivalent in the single-responsive-leaf setting, while clean-only matched-FPR equality is not identifiable. Long-horizon evaluations should therefore report the protocol's own observation boundary, validity limits, and reproducible evidence chain alongside aggregate system performance.

## References

- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics. arXiv:2210.15615, 2022.
- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets at WMT 2023. arXiv:2311.01153, 2023.
- Chung, J., Byun, J., Vineet, V., and Kim, S. J. Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking. arXiv:2606.15673, 2026.
- Cho, S., Ruberto, S., and Terragni, V. Metamorphic Testing of Large Language Models for Natural Language Processing. arXiv:2511.02108, 2025.
- Deviyani, A., and Diaz, F. Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy. arXiv:2503.19828, 2025.
- Du, S., Liang, P., Shen, Y., et al. On the Stability of Prompt Ranking in Large Language Model Evaluation. arXiv:2606.24381, 2026.
- Fan, S., Ye, X., Huo, Y., et al. AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents. arXiv:2603.14465, 2026.
- Kendiukhov, I. Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking. arXiv:2603.03493, 2026.
- Li, Q., Dou, S., Shao, K., Chen, C., and Hu, H. Evaluating Scoring Bias in LLM-as-a-Judge. arXiv:2506.22316, 2025.
- Li, S., Xu, C., Wang, J., et al. LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge. arXiv:2506.09443, 2025.
- Moghe, N., Fazla, A., Amrhein, C., et al. Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets. arXiv:2401.16313, 2024.
- National Institute of Standards and Technology. Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1, January 2023. https://doi.org/10.6028/NIST.AI.100-1.
- Ross, C., Hall, M., Romero Soriano, A., and Williams, A. What Makes a Good Metric? Evaluating Automatic Metrics for Text-to-Image Consistency. arXiv:2412.13989, 2024.
- Tan, G., Sun, Z., Shi, J., et al. AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection. arXiv:2608.06790, 2026.
- Wang, J., et al. GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows. arXiv:2604.15715, 2026.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv:2306.05685, 2023.

## Appendix A. Deferred independent-evidence record

This appendix preserves the internal evidence and preregistration record for deferred extensions. These materials are boundary records, not Stage E results.

### A.1 Reinstatement criteria

Reinstatement criteria, not a timeline: the deferred arms return only when (i) a second dataflow with a table layer passes SOURCE_GO and SPLIT_GO with UID-disjoint layers, and (ii) a second scorer independent of the :8004 judge reproduces the leaf-state cells; until both hold, the arms remain preregistered-but-unreported.

### A.2 Second-dataflow record

Progress against criterion (i) is now measurable, clause by clause. Three corpora answer different clauses and are named separately: the acquisition corpus (FinQA, taken under the approved minimal scope), the action corpus (a schema-matching benchmark of ten table pairs), and the transfer corpus whose missing table layer triggered the original deferral. SOURCE_GO passed on 2026-09-25 for the acquisition corpus, with per-file digests recorded. Its table layer is present and uniform: all 7134 examples carry a non-empty rectangular table whose first row is entirely string-valued, with two to eleven columns, so the clause that deferred the transfer corpus, the absence of a table layer, does not apply to the acquisition corpus. A deterministic, label-blind split instrument now assigns layers whose independence clusters are report-level rather than dataset-level, and on the acquisition corpus the four role layers are geometrically fillable, with 2409 lineage UIDs over 768 report clusters at full population. SPLIT_GO is nonetheless not passed: the acquisition corpus has its own gate and sealed partitions withheld because its registered role list does not include them, while the action corpus, which is the one that carries an action vocabulary, contains ten table-pair clusters and under the frozen hash-threshold bucketing rule leaves the development layer empty, yielding ten independent units. The remaining gap is structural rather than incremental, and it belongs to the label gate rather than to criterion (i): the acquisition corpus publishes no official canonical vocabulary for table columns, so action labels could only be constructed by inventing a schema. Here, a table layer makes samples definable; it does not supply the gold those samples need.

### A.3 Independent-scorer record

Criterion (ii) has not been tested, and one candidate route toward it was stopped by its own pre-registration. A model-free detector, independent of the :8004 judge, was built over a corpus of 1970 frozen step-level records whose contents and fault families were fixed before any detector existed, and whose percent-convention stop threshold was pre-registered before the second detector run produced any output. Its pre-registration fixed a fidelity threshold in advance, and that threshold was not reached: fidelity of the reconstructed step semantics on percent-form results was 0.0298 under one percent convention and 0.2233 under the other (44 and 330 matches out of 1478 percent-form steps, respectively), both below the pre-set 0.5, so the route was stopped rather than re-parameterized. Because that detector measures reasoning-step checkpoints while criterion (ii) concerns reproduction of the frozen header-injection leaf-state cells, the two are different measurement objects; the leaf-state reproduction clause therefore remains untested rather than failed, and what the fired stop condition establishes is the boundary of the step-level route itself. The portion of that corpus with faithful reconstruction covers 322 records of 1970 under the convention yielding 0.0298, and 467 under the one yielding 0.2233, i.e. 16.3% to 23.7%, and is reported to bound the route, not as a capability.

### A.4 Historical matched-FPR sensitivity

The older D3 analysis reported 90/111 for both flat and hierarchical protocols and a zero-difference bootstrap interval under a historical fixed-threshold sensitivity setup. Those numbers remain archived evidence for that setup only. The newer clean-only cross-fitted audit found zero-valued clean score supports and therefore could not identify a unique FPR-constrained threshold. Accordingly, the historical equality is not promoted to a clean-calibrated confirmatory claim and is not used to rank the protocols.
