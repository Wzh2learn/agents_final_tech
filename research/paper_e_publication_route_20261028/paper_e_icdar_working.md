---
title: "From Detection Scores to Supported Claims: Measurement Audits for Document Analysis and Retrieval"
lang: en-US
---

**Abstract—** Evaluation scores are used to compare systems, but their interpretation depends on what an evaluator observes, how observations are scored and what comparison is supported. We examine these dependencies in three audits: a staged document evaluator, the released FinRank evidence-ranking benchmark and researcher-generated runs on two BEIR datasets. In the staged evaluator, 96 of 118 controlled header changes were visible; under a single-responsive-leaf restriction, flat and hierarchical scores had the same ordering up to an approximately 0.375 scale factor, despite different fixed-threshold detection rates. In FinRank, changing the tie policy shifted absolute pairwise accuracy while preserving the direction of the examined hard-versus-random comparison. For the BEIR runs, a paired sign-flip analysis with Holm correction supported two of ten lexical-system comparisons on SciFact and one on NFCorpus. An exact-tie-aware point-estimate baseline also passed our duplicate and degradation controls. These findings show how explicit measurement contracts qualify or preserve particular comparisons; they do not establish a universally validated audit method.

**Index Terms—** measurement validity, document evaluation, information retrieval, reproducibility, benchmark auditing.

# I. Introduction

A lower detection rate can indicate a weaker evaluator, but it can also arise when the same numerical threshold is applied to scores on different scales. Likewise, a change in benchmark score need not change the comparison for which the score was reported; and the highest mean in a leaderboard does not by itself establish that every apparent ordering is supported by the data. Such distinctions matter when researchers use evaluation results to select systems or interpret a benchmark.

We ask: **which interpretations remain supported when the observation surface, scoring rule and comparison procedure are made explicit?** We investigate three evaluation constructions. First, controlled changes to public financial tables probe a staged document evaluator. Second, we inspect tie handling and source identity in FinRank [1]. Third, we assess researcher-generated lexical retrieval runs on SciFact and NFCorpus from BEIR [2], with a later dense-model exploration. The BEIR runs are our own constructions, not the published benchmark leaderboard.

Our contributions are empirical and bounded. We explain a detection-rate difference by a positive score rescaling under a single-responsive-leaf restriction; show that a particular FinRank comparison retains its direction despite changes in absolute scores; and distinguish point-estimate rankings from comparisons supported under a specified paired statistical procedure. Each finding is tied to an explicit measurement object and relevant limitations.

Prior work has examined metric and construct validity [3], [4], [5]. AgentSuite [6] audits interacting components in agent benchmarks at broader scale. Our study instead examines arithmetic, observation and comparison contracts in specific document and retrieval evaluations. It does not propose a new general theory of validity or claim an observed change in a user's decision.

Document analysis evaluation already addresses several related problems. SCORE [7] evaluates semantically equivalent but structurally different generative parsing outputs; Soric et al. [8] examine end-to-end and subtask table-extraction evaluation across heterogeneous PDFs. Those studies assess document parsing or extraction under their own evaluation designs. We instead audit the interpretation of measurements produced by a particular frozen evaluator, including what its selected mapping surface can observe and what follows from its scoring scale. Our table inputs are derived from financial QA data, not page-image OCR outputs. We do not benchmark document extraction models or claim a superior parsing metric.

The document case is the primary construction: a controlled change to a table header travels through a mapping rule into a checkpoint score and then a thresholded decision. Its observation and decision contracts can be inspected separately. The two external ranking cases complement this document-centered analysis by examining whether scores and comparison claims remain stable under other declared conventions; they do not turn the controlled header study into an external validation of a document-image analysis method.

# II. Audit Design

We distinguish three questions: whether a change is **visible** at a selected evidence surface; whether a specified predicate **detects** it; and whether it changes an outcome under a stated equivalence contract. Visibility, detection and outcome change are separate observations. We then examine score sensitivity, the stability of a named comparison and numerical reproducibility.

The designs differ. Case 1 uses controlled perturbations. Case 2 inspects a released benchmark, including source-informed post-hoc identity analysis. Case 3 uses researcher-generated systems and test queries from a public benchmark; its original audit choices were not independently timestamped before the first run. We preserve fixed outputs and identify later explorations rather than treating them as prospective confirmation.

The cases target three interpretations. First, a detection-rate difference does not necessarily imply a ranking difference when the score scales differ. Second, a shift in absolute accuracy need not reverse a stated comparison. Third, a higher retrieval mean is a point estimate; it does not automatically establish every pairwise system ordering. The following table summarizes what the audit changes in each interpretation; the cases below specify what is held fixed and what is varied.

| Case | Tempting interpretation | Supported interpretation after audit |
| --- | --- | --- |
| Document | Lower detection means weaker ranking | The reported rates differ, but rankings coincide in the single-leaf setting. |
| FinRank | Absolute score changes imply a changed comparison | The random-minus-hard gap stays positive under both inspected tie policies. |
| Retrieval | A higher mean establishes every system ordering | The paired test supports only some differences; unsupported pairs are not proven equal. |

For each construction we identify the input and outcome carrier, the evaluator or scoring implementation, the original reporting convention, the comparison of interest, and any alternative rule applied to fixed outputs. We use the term *decision* for a stated analytical interpretation such as the direction of a comparison; no intervention with a human decision-maker was conducted. The analysis can preserve an initial interpretation as well as qualify it. An audit of a score is useful even when the direction remains stable, because it identifies which aspects of the scoring contract matter to that conclusion.

The cases are complementary rather than replications of one universal intervention. The document case compares response visibility and threshold behavior in an instrumented construction. The FinRank case varies tie credit for a released financial retrieval benchmark. The BEIR case investigates metric definitions, query-level variation and uncertainty for newly constructed runs. Consequently, their sample counts, populations and effect sizes are not combined into one overall audit-success rate.

# III. Controlled Document Evaluation

The frozen staged evaluator has parsing and question-answering checkpoint trees with twelve scored leaves. Its seed-42 panel contains 95 TAT-QA-derived source tables [9] and 118 controlled header changes across six families. Mapping and regression artifacts form the observed surface. For each injected header, the visibility analysis identifies its original canonical field: the change is counted as absorbed when that field still maps to the injected header, and visible otherwise. This matcher-relative criterion is not simply a character-level difference. Protocol detection and downstream harm are separate quantities. The audit holds the evaluated inputs and scores fixed while comparing declared aggregation and threshold conventions. It does not observe every internal state or possible downstream use.

Of 118 injections, 96 were visible. None of the 13 OCR-like changes was visible on this surface. This observation does not establish 13 harmful misses: one existing semantic judge classified the cases as referentially equivalent, without an independent human reference. The family-level visible/injected counts were 43/47 alias variants, 15/17 date variants, 20/20 mixed-language variants, 0/13 OCR-like variants, 13/16 prefix-noise variants and 5/5 unit-suffix variants. These are injection counts in the seed-42 panel; the 118 changes are clustered within 95 tables. They characterize the particular matcher-relative surface, not generic document defects or actual OCR error rates.

In this construction the QA tree was frozen and only the field-hit-rate leaf responded. The unrounded hierarchical contrastive score was a positive rescaling of the flat score, with fitted slope approximately 0.375 and identical observed rankings. The original flat field-hit-rate drop and hierarchical parsing-root drop each used a numerical operating threshold of **at least 2.0**, on their respective scales. Under the observed scaling, a flat threshold of 2.0 corresponds to about 0.75 on the hierarchical scale, rather than 2.0. At these original operating points the flat and hierarchical protocols detected 75/95 versus 20/95 tables, or 85/118 versus 13/118 injections. Tables and injections are distinct units. The difference in rates therefore does not by itself establish a difference in ranking ability.

| Original operating point | Flat | Hierarchical |
| --- | ---: | ---: |
| Source tables | 75/95 | 20/95 |
| Header injections | 85/118 | 13/118 |

The separate matched-threshold reanalysis used strict greater-than comparisons: a flat threshold of 1.0 corresponds to a hierarchical threshold of 0.375; the recorded fold detects 21 cases under either. It is not the original 2.0 operating-point analysis. This distinction also matters for boundary values: 12 of the 95 tables have a flat drop exactly equal to 2.0.

In this single-leaf setting, a positive rescaling preserves score order; retaining the same decision rule also requires rescaling its threshold. The matched-grid example uses saved outputs and does not calibrate a deployment threshold or establish equivalence with multiple responsive leaves.

The clean-only contrastive construction compares repeated deterministic computations on an unchanged record. All 2,382 usable clean records have zero scores, so every positive threshold has observed clean false-positive rate zero; this panel does not identify a unique deployment threshold. Across three seeds, the flat descriptive table-run ratio was 219/282 using 119 unique source-table identifiers. A post-hoc UID-cluster bootstrap gives a 95% interval of [0.7117, 0.8364]; the repeated table runs are not 282 independent source tables.

The per-seed contributions to the 219/282 ratio are 75/95, 76/97 and 68/90. The denominators refer to table appearances within each run; the same source table may contribute to more than one run. The bootstrap samples source identifiers with replacement, includes all run appearances for each sampled identifier, and recalculates the pooled ratio. This uncertainty interval is post-hoc and conditional on the available source tables and three seeds; it should not be interpreted as a guarantee for future datasets or seeds. Equal weighting of source identifiers gives 0.7535 with interval [0.6835, 0.8207].

In a separate stage-aligned control, 72 source clusters contributed one injection each for mapping, retrieval and numeric processing. A leave-one-cluster-out nearest-centroid classifier on the full response vector attained macro-F1 and top-1 1.000. The three directly targeted parsing, retrieval and reconciliation leaves gave the same result; removing them reduced top-1 to 0.333 under the frozen tie-as-incorrect rule, with a 0.667 tie rate. The classifier was evaluated by leaving one source cluster out at a time, so the three injected stages from the held-out cluster were not included when fitting its centroids. This ablation tests the source of the observed signal in the controlled instrument, not error localization on an independent deployed system. The observed stage separation is attributable to explicit instrumentation, not to hierarchy alone. A nested FinQA probe [10] covered 89 rows from 30 report clusters; it changed program fields but did not recompute downstream result fields. Its zero detected and zero changed outcomes cannot estimate a failure rate for changed answers.

# IV. FinRank: Score Sensitivity and Decision Stability

FinRank ranks evidence from financial filings [1]. Under tie-as-positive scoring, a score tie counts for the gold passage; under strict-win scoring, it does not. The tie comparisons and materiality threshold were fixed before pair-level outcomes. The following table shows that random-negative accuracy moves by 1.084 percentage points for TF-IDF and 1.029 for BM25, exceeding the fixed 1.0-point threshold, while the random-minus-hard gap remains positive in both systems.

| System | Tie policy | Hard (%) | Random (%) | Gap (pp) |
| --- | --- | ---: | ---: | ---: |
| TF-IDF | Positive | 77.756 | 91.935 | 14.179 |
| TF-IDF | Strict win | 77.030 | 90.850 | 13.821 |
| BM25 | Positive | 74.780 | 87.789 | 13.009 |
| BM25 | Strict win | 74.094 | 86.760 | 12.666 |

Gaps are random accuracy minus hard accuracy, computed before display rounding. The comparison's qualitative direction is stable under these two policies; this does not establish stability for all decisions. A later source-informed identity analysis reproduces 442 hard-negative occurrences across 305 records sharing canonical text with another record's gold passage, and gold-passage loss in 33 records under the inspected metadata filter. These are post-hoc reproductions of known properties, not newly discovered benchmark defects. In-record and pairwise metrics reproduce exactly in the audited environment; global and metadata-filtered metrics differ from the released results by up to 0.19 and 0.16 percentage points, respectively, with the cause unresolved.

The identity analysis also explains why text identity and record identity are different contracts. A pooled passage can occur in several records with different metadata. When the inspected implementation deduplicates text by first occurrence and retains that occurrence's metadata, a later record's gold text can be excluded by metadata filtering even though its text appeared in the pooled corpus. The reproduced counts describe that implementation and its released data, not the prevalence of this behavior in other retrieval systems. Exact in-record reproduction and the remaining global mismatch are reported separately because one does not resolve the other.

# V. Retrieval Comparisons

We built five lexical configurations on BEIR SciFact and NFCorpus [2]: TF-IDF and BM25 parameter pairs (k1, b) of (0.9, 0.4), (1.2, 0.75), (0.5, 0.3) and (1.5, 0.6). We concatenate each document's title and text, lowercase and tokenize on ASCII alphanumeric runs, use log-scaled term frequency and smoothed inverse document frequency for TF-IDF cosine, and resolve equal scores by ascending document ID unless testing the alternative order. They use the released corpora, qrels and 300/323 judged queries, respectively. The systems are our own runs, and the two datasets belong to one benchmark family. We compare system scores on the same queries so that statistical analysis is paired; each dataset has its own comparison family.

Our initial scoring implementation binarized graded relevance and used a different MAP denominator. Aligning it with the trec_eval contract corrected both definitions. Under graded nDCG@10, TF-IDF moved from second to third in one NFCorpus ranking; the separate denominator correction changed TF-IDF's MAP@10 from approximately 0.2200 to 0.1162. This is a correction of our implementation, not evidence that the official leaderboard was wrong. For fixed rankings, trec_eval 10.0-rc3 agreed with 18,690 per-query nDCG, MAP and recall values within 1e-4; it does not validate tie-breaking policy.

The cross-check writes a strictly decreasing score for each fixed rank, so the reference evaluator receives the order selected by our run. It can test the metric values for that order, but cannot decide which document should win an equal-score tie. The maximum observed discrepancy was approximately 0.00005, consistent with four-decimal output precision. The executable used was trec_eval itself; the check was not a separate execution of the pytrec_eval Python binding. These distinctions make the reproducibility statement narrower and more useful than a general assertion that an entire retrieval pipeline has been independently reproduced.

For the five systems, 2,000 paired bootstrap resamples produced intervals excluding zero for 3/10 pairs on SciFact and 4/10 on NFCorpus. A separate two-sided paired sign-flip procedure with 2,000 Monte Carlo draws per pair and Holm correction supported 2/10 and 1/10, respectively. These are different inference procedures, so the count difference is not attributable to Holm correction alone. The inference depends on the relevant exchangeability or symmetry and query-independence assumptions; non-significance does not establish equality.

The supported SciFact pairs were BM25(1.5, 0.6) versus TF-IDF (mean nDCG@10 difference +0.03334; Holm-adjusted p = 0.0100) and BM25(1.2, 0.75) versus TF-IDF (+0.02930; p = 0.0450). On NFCorpus, BM25(1.5, 0.6) versus BM25(0.5, 0.3) had a difference of +0.00817 (p = 0.0300). A later 200,000-draw sensitivity check on regenerated lexical query scores retains the same three supported pairs when Holm is recalculated within the five-system family. It reduces Monte Carlo variability but does not independently validate the data or inferential assumptions.

Separately from varying cutoff k, reversing document-ID tie order for one NFCorpus BM25 configuration at k=10 changed the ordered top ten for 36.5% of queries and top-ten membership for 25.7%. Mean nDCG@10 changed from 0.30453945 to 0.30449093, approximately 0.00005. Query-level changes can therefore be hidden by the aggregate in this setting; this is not an estimated benchmark-wide failure rate.

For an intentionally duplicated system and an intentionally degraded control, an exact-tie-aware point-estimate rule and the paired audit both passed both controls. The controls do not demonstrate that the audit outperforms the simpler rule. A subsequent BGE-small-en-v1.5 [11] exploration gave mean nDCG@10 of 0.7127 versus 0.6622 for BM25 on SciFact, and 0.3438 versus 0.3062 on NFCorpus. This is an exploratory retrieval result selected after the original analysis, not evidence that the audit improved a user decision or that lexical tie findings transfer to dense models.

The BGE comparison was later included with the five lexical runs in a separate six-system family of 15 pairs per dataset. With 200,000 Monte Carlo sign flips per pair and Holm correction within each dataset, the BGE-minus-BM25 nDCG@10 difference was +0.05049 on SciFact (adjusted p = 0.066000) and +0.03759 on NFCorpus (adjusted p = 0.015540). These post-hoc tests are not the original ten-pair family or independent confirmation. The saved dense outputs contain ranked document IDs rather than original dense scores, so they cannot establish dense-score tie frequencies. Numerical reproducibility of the tests does not establish their inferential assumptions.

The earlier single-pair BGE analysis used normalized embeddings, the model's query prefix and a 512-token cap. Its uncorrected paired-bootstrap differences were 0.0505 [0.0137, 0.0891] on SciFact and 0.0376 [0.0154, 0.0608] on NFCorpus. A separate trec_eval run agreed on 1,246 dense and BM25 per-query scores to four-decimal print precision. The later 15-pair test addresses multiplicity, not prospective confirmation.

# VI. Discussion and Conclusion

The three cases show distinct ways in which an evaluation contract constrains a claim. In the staged evaluator, a rate difference coexists with identical ranks under a restricted score rescaling. In FinRank, a tested comparison retains direction as absolute scores change. In our BEIR runs, metric definitions, ties and statistical comparison procedures affect the interpretation of rankings.

These findings have limited scope: the first case uses controlled perturbations to structured tables, without a page-image recognition experiment or an independent human reference for the OCR-like variants. FinRank uses lexical baselines and has an unresolved reproduction gap, and the BEIR analyses are retrospective runs over two datasets with a post-hoc dense extension. Existing validity frameworks already cover broader audit principles [3], [4], [5]. Our contribution is a reproducible set of case-specific observations and the distinction between numerical movement and supported interpretation. We recommend reporting the measurement object, scoring convention, comparison and uncertainty together; we do not claim a general audit guarantee or observed deployment benefit.

# Data and Materials

The TAT-QA, FinRank and BEIR data used in this study are described in [9], [1] and [2], respectively; the BEIR runs use released relevance judgments. Study-specific audit scripts, configuration records and aggregate results are retained as research artifacts. Access to and redistribution of underlying data remain subject to the respective source terms.

# Acknowledgment

Generative AI tools, including DeepSeek [12] and OpenAI Codex [13], assisted with analysis-code development and drafting and revision of manuscript text in Sections 1–6. Google Gemini [14] provided review suggestions on earlier drafts. The authors are responsible for the final manuscript and its conclusions.

# References

[1] S. Mansouri et al., “FinRank: An Evidence-Grounded Benchmark for Financial Question Answering and Retrieval over SEC Filings,” arXiv:2608.07400, 2026.

[2] N. Thakur et al., “BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models,” NeurIPS Datasets and Benchmarks, 2021.

[3] C. Ross et al., “What makes a good metric? Evaluating automatic metrics for text-to-image consistency,” arXiv:2412.13989, 2024.

[4] W. Caban, “Measurement Without Validity: The Compounding Reliability Problem in Agentic AI Evaluation,” arXiv:2608.00794, 2026.

[5] A. M. Bean et al., “Measuring what Matters: Construct Validity in Large Language Model Benchmarks,” arXiv:2511.04703, 2025.

[6] H. Suh et al., “AgentSuite: Toward More Reliable Agent Evaluation with a Component-Based Benchmark Auditing Pipeline,” ICML, PMLR 306:116300–116319, 2026.

[7] R. Li et al., “SCORE: A Semantic Evaluation Framework for Generative Document Parsing,” arXiv:2509.19345, 2025.

[8] M. Soric, C. Gracianne, I. Manolescu, and P. Senellart, “Benchmarking Table Extraction from Heterogeneous Scientific PDF Documents,” arXiv:2511.16134v2, 2026.

[9] F. Zhu et al., “TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance,” ACL-IJCNLP, 2021, doi: 10.18653/v1/2021.acl-long.254.

[10] Z. Chen et al., “FinQA: A Dataset of Numerical Reasoning over Financial Data,” EMNLP, 2021, doi: 10.18653/v1/2021.emnlp-main.300.

[11] Beijing Academy of Artificial Intelligence, “bge-small-en-v1.5,” model card, revision 5c38ec7c, https://huggingface.co/BAAI/bge-small-en-v1.5.

[12] DeepSeek, “DeepSeek V4.1,” https://www.deepseek.com/, accessed November 2, 2026.

[13] OpenAI, “Codex,” https://openai.com/codex/, accessed November 2, 2026.

[14] Google, “Gemini,” https://gemini.google.com/, accessed November 2, 2026.
