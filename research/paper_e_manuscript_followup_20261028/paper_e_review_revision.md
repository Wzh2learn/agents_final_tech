---
title: "Visibility Is Not Detection: Measurement Audits for Document and Evidence-Ranking Evaluation"
author: Anonymous Authors
lang: en-US
---

**Abstract—** Evaluation scores can conceal the difference between an unobserved defect, a visible difference and an error that changes a decision. We audit three evaluation constructions: a staged document evaluator using controlled changes to public financial tables; FinRank, an external financial evidence-ranking benchmark; and a researcher-generated leaderboard over two BEIR retrieval datasets. In the staged evaluator, 96 of 118 controlled header changes were visible at the selected evidence surface, whereas 13 OCR-like changes were not visible; this observation does not establish harmfulness. In FinRank, tie policy changed absolute pairwise scores while the direction of the hard-versus-random comparison remained stable. For BEIR, correcting our initial treatment of graded relevance changed the NFCorpus example ranking, and a paired test with multiplicity correction supported two of ten comparisons on SciFact and one on NFCorpus. A simple rule respecting exact ties already passed our duplicate and degradation controls. The results demonstrate bounded, reproducible checks on evaluation interpretation, not a validated universal audit or a claim about agent performance.

**Index Terms—** measurement validity, retrieval evaluation, reproducibility, document processing, benchmark auditing.

# I. Introduction

An evaluation score is an operational measurement, not the evaluated system itself. A document question-answering pipeline may parse tables, retrieve evidence and compute an answer; a final score alone may not reveal which changes were visible to its evaluation or which scoring conventions affected its interpretation. Similarly, retrieval rankings depend on evaluation contracts. A score change need not change the practical comparison, and a small gap between systems need not support a strict ordering.

Prior work studies metric validity and construct validity [1]–[3], while FinRank provides a financial evidence-ranking task [4]. We contribute an artifact-grounded application across three constructions: a staged document evaluator, the released FinRank evaluation, and two subsets of the BEIR retrieval benchmark [5]. Our audit separates visibility, detection and outcome harm; distinguishes absolute-score sensitivity from decision stability; and records reproducibility boundaries. The third case concerns researcher-generated lexical runs and one post-hoc dense comparison, not the published BEIR leaderboard. None of the cases directly evaluates an agent.

The audit's value is conditional: it can clarify which interpretations are supported and which require further evidence, without claiming that the checks themselves constitute a universal method. We retain negative and stable outcomes alongside the effects identified.

The motivation is practical: readers may use evaluation summaries to choose a model or interpret a benchmark, but these choices are justified only for the measurement actually performed. We therefore pair each observation with its carrier and a decision-relevant question. This does not establish that a user changed a real decision, nor that any specific system is safe or unreliable. Our work applies existing validity ideas to three concrete evaluation objects rather than introducing a new general theory of validity.

# II. Audit Questions and Procedure

For an evaluation object we ask: (i) whether a controlled change is visible at a specified evidence surface; (ii) whether the evaluation's predicate detects it; and (iii) whether it changes the downstream outcome under an explicit equivalence contract. These are different observations. A lack of visible change is not, by itself, evidence of harmful blindness.

**Table 1. From an initial interpretation to the observation supported by each audit.**

| Evaluation case | A possible initial interpretation | Audit observation | Supported interpretation |
| --- | --- | --- | --- |
| Staged document evaluator | A lower detection rate necessarily indicates poorer ranking. | Only one leaf responds; scores are positively rescaled. | Compare matched thresholds and report the measurement surface. |
| FinRank | A tie-policy score shift means the hardness conclusion changes. | Scores change while the tested random-versus-hard gap retains its direction. | Separate score sensitivity from decision stability. |
| BEIR-based runs | Every higher mean score supports a strict ordering. | Some comparisons lack support under a paired, multiplicity-adjusted test. | Report the supported comparisons and uncertainty; non-significance is not equality. |

These are interpretations of constructed or released evaluation objects, not observed changes in a real user's decision.

For scoring we separately vary declared conventions and inspect whether the reported absolute scores and the decision under examination change. Where systems are compared on shared queries, we use paired query-level resampling and report multiple-comparison sensitivity. We retain the original outputs and distinguish prospectively fixed choices from source-informed or post-hoc analyses.

The three applications differ in design and evidence. Case 1 uses synthetic perturbations on public tables. Case 2 inspects a released benchmark and its implementation. Case 3 uses independently generated retrieval runs over BEIR's released data and relevance judgments; its original audit choices were not independently timestamped before the first run. All three support only the observations stated for their respective constructions.

The intervention, evidence surface, predicate and downstream outcome need to refer to compatible objects. For example, changing a stored program without recomputing the field that the predicate reads can produce a reproducible zero response without testing the predicate's behavior on the changed program's true result. We report such execution boundaries explicitly. For pairwise ranking, the comparison and scoring conventions are part of the measurement contract, and conclusions about the direction of a comparison are separate from conclusions about its numerical magnitude.

# III. Staged Document Evaluator

The staged evaluator has parsing and question-answering checkpoint trees containing twelve scored leaves. The primary panel contains 95 public TAT-QA-derived source tables [7] with 118 controlled header changes across six families. The observed surface consists of mapping and regression artifacts; the primary drop rule compares the original and injected parsing-root scores. A change is visible when that surface records a difference, while protocol detection and downstream harm remain separate judgments. The surface includes only the selected artifacts, not every internal model state or every possible user outcome.

Of the 118 injected changes, 96 were visible. None of 13 OCR-like changes appeared on the selected surface. This is an observation boundary, not proof of 13 harmful misses: one existing semantic judge classified the cases as referentially equivalent. The QA tree was frozen and the field-hit-rate leaf was the only responsive leaf in this header-change construction. Under this restriction, the unrounded hierarchical contrastive score was a positive rescaling of the flat score, with fitted slope approximately 0.375 and identical observed ranks. Thus corresponding thresholds satisfy θ_H = 0.375 θ_F; different fixed operating thresholds can yield different detection rates despite the same ordering. This is an observed structural equivalence in the present construction, not a general result for multiple responsive leaves.

**Table 2. Seed-42 detection and stage-instrumentation controls.**

| Evaluation and unit | Flat / full response | Hierarchical / direct or reduced response | Interpretation |
| --- | --- | --- | --- |
| Header detection, 95 tables at the reported operating points | Flat 75/95 | Hierarchical expert 20/95 | Raw rates depend on threshold and score scale; ranks match in this single-leaf construction. |
| Header detection, 118 injections at the reported operating points | Flat 85/118 | Hierarchical expert 13/118 | Injection and table denominators are different units. |
| Stage localization, 216 controlled injections | Full vector macro-F1 and top-1 1.000 | Three direct leaves: 1.000; removing them: top-1 0.333 | Stage alignment is provided by explicit instrumentation. |

The table describes the reported operating points; the clean-only panel did not identify a unique deployment threshold.

Across three seeds the descriptive detection table-run ratio was 219/282, using 119 unique source-table identifiers. A post-hoc UID-cluster bootstrap, which retains repeated table appearances within each source, gives a 95% interval of [0.7117, 0.8364]. Equal weighting of source UIDs gives 0.7535 [0.6835, 0.8207]. The per-seed denominators (95, 97 and 90) are not the count of one shared panel, and three seeds are insufficient to characterize a population of future seeds. The semantic assessment above relies on one judge rather than an independent human reference.

A separate stage-aligned instrument introduced controlled mapping, retrieval and numeric changes. Across 72 source clusters and 216 injections, the full response vector distinguished the three stages with macro-F1 and top-1 accuracy 1.000. The same result followed from directly reading three targeted leaves; after removing those leaves, top-1 accuracy fell to 0.333. The positive separation therefore reflects explicit stage-aligned instrumentation, not evidence that hierarchy alone localizes natural failures. A nested FinQA probe [8] changes program fields without recomputing downstream result fields and is interpreted only as a measurement-object boundary.

The stage study uses leave-one-cluster-out evaluation, with one injection from each of the three contracts per cluster; its positive result is for the frozen controlled set. The FinQA boundary study contains 89 rows in 30 report clusters. It records 89 visible changes, no detected change and no changed outcome field; because the downstream results were not regenerated, those zeros do not estimate the detector's true failure rate on changed answers.

# IV. FinRank: Score Sensitivity and Decision Stability

FinRank is a public evidence-ranking benchmark over financial filings [4]. We inspect its released implementation and outputs, including exact ties and source identity. The tie comparisons and thresholds were fixed before pair-level outcomes. A later canonical-text identity correction is explicitly post-hoc; the source code made the inspected identity behavior visible before this analysis.

Under tie-as-positive versus strict-win pairwise scoring, TF-IDF random-negative accuracy moved by 1.084 percentage points, exceeding the fixed 1.0-point materiality threshold. Its random-minus-hard gap nevertheless retained direction, moving from 14.179 to 13.821 points; BM25 showed the same qualitative stability. Thus the absolute score is convention-sensitive while this particular hardness comparison survives the tested policies.

For TF-IDF, the reported hard and random accuracies were 77.756% and 91.935% under tie-positive scoring, versus 77.030% and 90.850% under strict wins. Differences use full precision before rounding, so subtracting the rounded cells need not reproduce the displayed movement exactly. This checks a specific directional claim, not the effect of all plausible score contracts on every application decision.

The corrected source-informed identity analysis reproduces 442 hard-negative occurrences in 305 records sharing canonical text identity with a gold passage elsewhere and gold loss in 33 records under the inspected metadata filter. These counts are post-hoc reproductions, not newly discovered or independently preregistered benchmark defects.

In-record and pairwise metrics reproduce exactly in the audited environment. Some global and metadata-filtered metrics still differ from released results; without the original score matrices or complete environment, the cause remains unresolved. Numerical reproduction and ranking interpretation are distinct claims.

# V. Public Retrieval Evaluation

We independently constructed five lexical retrieval configurations—four BM25 parameterizations and one TF-IDF system—on BEIR SciFact and NFCorpus [5]. The evaluation uses the released test queries, corpora and relevance judgments: 300 judged queries on SciFact and 323 on NFCorpus. These are two subsets of one benchmark family, not two independently established benchmarks. The original five-system analysis is retrospective and covers no dense or generative retriever.

During development our own first implementation binarized graded relevance and used a different MAP denominator. Comparing it with the trec_eval contract corrected both definitions. Under graded nDCG@10, TF-IDF moved from second to third in the NFCorpus example ranking; its position change is specific to the constructed systems and judgments, not a correction to an official leaderboard. The reference implementation trec_eval 10.0-rc3 was subsequently run on the fixed rankings. Across 18,690 per-query nDCG, MAP and recall values, discrepancies were within 1e-4, with maximum approximately 5e-5 due to printed precision. The comparison verifies scores for given rankings, not the policy that breaks ties.

These are two separate corrections: graded relevance changed nDCG, while dividing average precision at the cutoff by the full number of relevant documents changed MAP@10 on NFCorpus from approximately 0.2225 to 0.1193 for the example. The latter does not explain the nDCG ranking change. The cross-check used trec_eval itself, not the pytrec_eval Python binding; it does not demonstrate agreement with a separately executed pytrec_eval installation.

We compared the five systems using 2,000 paired bootstrap resamples and a paired sign-flip test with Holm correction across ten pairs. The uncorrected bootstrap intervals excluded zero for three pairs on SciFact and four on NFCorpus; the corrected sign-flip analysis supported two and one, respectively. These are separate inferential procedures, so the change in counts cannot be ascribed solely to Holm correction. A failure to exclude zero is not proof that two systems are equal.

Cutoff choice also affected ordering. For one BM25 configuration on NFCorpus, reversing document-ID tie order changed the ordered top ten for 36.5% of queries and changed the top-ten document set for 25.7%. Mean nDCG@10 changed from 0.30453945 to 0.30449093, about 0.00005; the aggregate rounds to the same four-decimal display. On SciFact those tie-change rates were zero. The finding illustrates a per-query effect hidden by aggregation within these conditions, not a general failure rate.

We also compared naive sorting, a point-estimate rule that treats exactly equal scores as ties, and the paired audit. The naive view incorrectly asserts an order for an intentionally duplicated system; the simple equality rule and audit both avoid that assertion and both identify an intentionally degraded control. Thus this control does not show the audit beats the simple rule. The audit reports which comparisons are supported under its statistical contract, at the cost of additional metric sweeps and resampling; it is not a demonstrated real-user decision improvement.

**Table 3. Evidence about retrieval comparisons.**

| Object | Observation | Limit of the interpretation |
| --- | --- | --- |
| Five lexical systems, SciFact / NFCorpus | Holm-adjusted paired sign-flip tests support 2/10 and 1/10 pairs. | The ten pairs are within each dataset; no conclusion of equality follows from a non-significant comparison. |
| NFCorpus tie-order perturbation, one BM25 system | 36.5% of queries change ordered top-10; 25.7% change its membership; mean nDCG@10 changes by about 0.00005. | These are query-list, query-set and aggregate-score quantities, respectively; this is not an official benchmark-wide failure rate. |
| Exact duplicate and degraded controls | Exact-tie point estimates and the paired audit both pass both controls. | These controls do not establish an advantage over the simpler baseline. |

**Post-hoc dense exploration.** To widen model coverage, we subsequently ran the public BGE-small-en-v1.5 encoder [9], using the same data, qrels and nDCG@10 contract. We normalized embeddings, used the model's retrieval query prefix, capped inputs at 512 tokens and compared with the fixed BM25(1.2, 0.75) run. Dense versus BM25 mean scores were 0.7127 versus 0.6622 on SciFact and 0.3438 versus 0.3062 on NFCorpus. The paired bootstrap differences were 0.0505 [0.0137, 0.0891] and 0.0376 [0.0154, 0.0608], respectively. Each interval is uncorrected and the exploration was chosen after the original analyses; neither belongs to the original ten-pair Holm family or establishes a general model ranking. Independent execution of trec_eval agreed for all 1,246 dense and BM25 per-query scores to its four-decimal print precision. The encoder improvement is a retrieval result, not evidence that the audit improved a user decision or that the lexical tie conclusions transfer to dense models.

# VI. Discussion and Limitations

The cases connect evaluation objects to supported claims. A visible mutation is not automatically detected; a non-response is not automatically harmful; metric sensitivity is not automatically a decision reversal. Explicit stage instrumentation produces a controlled positive result, while its direct-leaf control limits what may be attributed to hierarchy. FinRank's decision remained stable under the examined tie policies, even as absolute scores moved. The BEIR development correction shows how an evaluation contract can change an example ranking, while careful point-estimate handling already solves the duplicated control.

Scope is restricted. Header changes are synthetic on one source corpus. FinRank covers lexical baselines and has a residual reproduction gap. BEIR covers two subsets of one benchmark and constructed lexical systems, plus one post-hoc dense encoder; its design is retrospective. We did not test agent execution, human decisions, generative retrieval or deployment benefit. Confidence intervals and multiplicity correction do not establish equivalence when a comparison is inconclusive. Existing construct-validity frameworks already cover broad audit principles [2], [3]; our contribution is the bounded application and the observed distinctions, not a general theory.

# VII. Conclusion

Three measurement audits illustrate how evidence surfaces, score conventions and reproducibility delimit evaluation claims. In the tested constructions, explicit checkpoints aided controlled stage separation; a FinRank comparison retained direction across tie policies; and a BEIR-based example showed that graded relevance and uncertainty can alter interpretation. These findings motivate reporting the measurement object, scoring contract, uncertainty and reproduction scope together. General effectiveness and deployment value remain open.

# Acknowledgment

AI-assisted tools were used for manuscript organisation, English editing, consistency checks and drafting code for analysis; the authors remain responsible for verification and conclusions [6]. The complete tool list, precise disclosure and author details require author confirmation.

# References

[1] C. Ross, M. Hall, A. R. Soriano and A. Williams, “What makes a good metric? Evaluating automatic metrics for text-to-image consistency,” arXiv:2412.13989, 2024.

[2] W. Caban, “Measurement Without Validity: The Compounding Reliability Problem in Agentic AI Evaluation,” arXiv:2608.00794, 2026.

[3] A. M. Bean, R. O. Kearns, A. Romanou et al., “Measuring what Matters: Construct Validity in Large Language Model Benchmarks,” arXiv:2511.04703, 2025.

[4] S. Mansouri, D. Saad, M. Wahrenburg, M. Weissel and F. Woebbeking, “FinRank: An Evidence-Grounded Benchmark for Financial Question Answering and Retrieval over SEC Filings,” arXiv:2608.07400, 2026.

[5] N. Thakur, N. Reimers, A. Rücklé, A. Srivastava and I. Gurevych, “BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models,” NeurIPS Datasets and Benchmarks, 2021.

[6] OpenAI, “Codex,” 2026. Available: https://openai.com/codex/.

[7] F. Zhu et al., “TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance,” Proc. ACL-IJCNLP, 2021, doi: 10.18653/v1/2021.acl-long.254.

[8] Z. Chen et al., “FinQA: A Dataset of Numerical Reasoning over Financial Data,” Proc. EMNLP, 2021, doi: 10.18653/v1/2021.emnlp-main.300.

[9] Beijing Academy of Artificial Intelligence, “bge-small-en-v1.5,” model card, revision 5c38ec7c, https://huggingface.co/BAAI/bge-small-en-v1.5.
