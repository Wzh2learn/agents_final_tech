#!/usr/bin/env python3
"""Build a reader-oriented Paper E draft from the frozen v4, without experiments."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parent
source = root / "paper_e_review_revision_v4.md"
destination = root / "paper_e_review_revision_v5.md"
text = source.read_text(encoding="utf-8")


def replace_once(before, after):
    global text
    if text.count(before) != 1:
        raise ValueError(f"Expected one occurrence, found {text.count(before)}: {before[:100]}")
    text = text.replace(before, after, 1)


def replace_between(start, end, replacement):
    global text
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Non-unique section boundary: {start} / {end}")
    prefix, rest = text.split(start, 1)
    _, suffix = rest.split(end, 1)
    text = prefix + replacement + end + suffix


replace_once(
    'title: "Visibility Is Not Detection: Measurement Audits for Document and Evidence-Ranking Evaluation"',
    'title: "From Scores to Supported Claims: Measurement Audits of Document and Retrieval Evaluation"',
)

replace_between(
    "**Abstract—**", "**Index Terms—**",
    """**Abstract—** Evaluation scores are often used to compare systems, yet their interpretation depends on what an evaluator observes, how it scores the observation, and which comparison the evidence supports. We examine these dependencies through three measurement audits: a controlled staged document evaluator, the released FinRank evidence-ranking benchmark, and researcher-generated retrieval runs on two BEIR datasets. In the staged evaluator, 96 of 118 header changes were visible at the selected evidence surface; under a single-responsive-leaf restriction, flat and hierarchical scores retained the same ordering up to an approximate 0.375 rescaling despite different fixed-threshold detection rates. In FinRank, alternative tie policies changed absolute pairwise accuracy while preserving the direction of the hard-versus-random comparison. In the BEIR runs, a paired sign-flip analysis with Holm correction supported two of ten lexical-system comparisons on SciFact and one on NFCorpus. An exact-tie-aware point-estimate baseline already passed our duplicate and degradation controls. Together, these cases show how an audit can qualify or preserve a comparison by making its measurement contract explicit. The findings apply to the examined constructions, not to a universally validated audit method.

""",
)

replace_between(
    "# I. Introduction", "# II. Audit Questions and Procedure",
    """# I. Introduction

A score is useful when readers know what it supports. A lower detection rate might indicate weaker ranking, or it might result from applying the same threshold to differently scaled scores. A changed benchmark score might alter a model-selection conclusion, or it might leave the comparison of interest intact. Likewise, the highest mean on a retrieval leaderboard identifies a point-estimate leader but does not by itself establish that every apparent ordering is supported by the data.

These examples share a practical problem: a numerical result and the conclusion drawn from it need not describe the same measurement. We ask **which interpretations of an evaluation result remain supported when its observation surface, scoring rules and comparison procedure are made explicit?** We answer this question through three complementary audits, rather than proposing another general theory of validity.

Our first case uses a frozen staged document evaluator and controlled financial-table perturbations to separate observable changes from predicate detection. The second inspects FinRank [4] to distinguish tie-policy sensitivity in absolute scores from stability of a specific hard-versus-random comparison. The third audits our own retrieval runs on two BEIR datasets [5], asking how metric definitions, tie ordering and paired comparisons affect the interpretation of their scores. These are researcher-generated BEIR runs, not the published BEIR leaderboard; a later dense run is exploratory.

The contribution is an artifact-grounded account of how a reported result becomes a supported claim. In the examined constructions, we (1) explain a large detection-rate gap through a score rescaling under an explicit single-leaf restriction; (2) show that a benchmark comparison can retain its direction despite a material change in absolute scores; and (3) contrast point-estimate rankings with the support obtained from a specified family of paired statistical comparisons. The evidence also includes controls that limit each interpretation. Table 1 provides the resulting audit-to-interpretation map.

This work builds on prior studies of metric and construct validity [1]–[3]. AgentSuite's component-oriented benchmark audit [11] and Chen's study of oracle failures [12] address related validity and evaluation-system questions at broader Agent-evaluation scale. Our focus is narrower: the arithmetic, observation and comparison contracts governing particular document and retrieval results. A small development-only Agent inspection is retained in Appendix A as an illustration of the same observation/reference distinction, not as a fourth validated case.

""",
)

replace_once(
    "The staged evaluator has parsing and question-answering checkpoint trees containing twelve scored leaves. The primary panel contains 95 public TAT-QA-derived source tables [7] with 118 controlled header changes across six families.",
    "The staged evaluator has parsing and question-answering checkpoint trees containing twelve scored leaves. Its seed-42 primary panel contains 95 public TAT-QA-derived source tables [7] with 118 controlled header changes across six families.",
)

replace_once(
    "Across 72 source clusters and 216 injections, the full response vector distinguished the three stages with macro-F1 and top-1 accuracy 1.000. The same result followed from directly reading three targeted leaves; after removing those leaves, top-1 accuracy fell to 0.333. The positive separation therefore reflects explicit stage-aligned instrumentation, not evidence that hierarchy alone localizes natural failures.",
    "The three stages are mapping, retrieval and numeric processing. Each of 72 source clusters contributes one controlled injection per stage. For the binary leaf-response vector, a leave-one-cluster-out nearest-centroid classifier attained macro-F1 and top-1 accuracy of 1.000 over 216 injections. The same separation followed from the three direct stage-targeted leaves: parsing, retrieval and reconciliation. Removing these leaves reduced top-1 accuracy to 0.333 with a 0.667 tie rate under the frozen tie-as-incorrect rule; the remaining leaves retained partial information but did not separate retrieval from numeric changes. Thus the perfect controlled separation is attributable to the explicit instrumentation, rather than to hierarchy alone.",
)

replace_between(
    "Under tie-as-positive versus strict-win pairwise scoring,",
    "The corrected, source-informed identity analysis",
    """Under tie-as-positive scoring, an exact score tie counts for the gold passage; under strict-win scoring it does not. Table 3 shows that this change moves random-negative accuracy by 1.084 percentage points for TF-IDF and 1.029 for BM25, above the fixed 1.0-point materiality threshold. Yet the random-minus-hard gap remains positive for both systems: the evaluated qualitative conclusion survives even though the absolute scores are sensitive to the tie contract.

**Table 3. FinRank pairwise accuracy and random-minus-hard gap under two tie policies. Values are percentages; gaps and movements are percentage points.**

| Model | Tie policy | Hard accuracy | Random accuracy | Random minus hard |
| --- | --- | ---: | ---: | ---: |
| TF-IDF | Tie-as-positive | 77.756 | 91.935 | 14.179 |
| TF-IDF | Strict win | 77.030 | 90.850 | 13.821 |
| BM25 | Tie-as-positive | 74.780 | 87.789 | 13.009 |
| BM25 | Strict win | 74.094 | 86.760 | 12.666 |

Movements and gaps are calculated before display rounding; subtracting the rounded cells need not reproduce the reported values exactly. This result concerns the stated comparison, rather than every possible use of the scores.

""",
)

replace_once(
    "The corrected, source-informed identity analysis reproduces two known properties: 442 hard-negative occurrences across 305 records share canonical text identity with another record’s gold passage, and the inspected metadata filter loses gold evidence in 33 records.",
    "The corrected, source-informed identity analysis reproduces two known properties: 442 hard-negative occurrences across 305 records share canonical text identity with another record’s gold passage, and the inspected metadata filter loses gold evidence in 33 records. In the pooled corpus, text is deduplicated by first occurrence, whose metadata is retained; filtering on that metadata can consequently exclude a passage that is gold for a later record.",
)

replace_once(
    "We independently constructed five lexical retrieval configurations—four BM25 parameterizations and one TF-IDF system—on BEIR SciFact and NFCorpus [5].",
    "We independently constructed five lexical retrieval configurations on BEIR SciFact and NFCorpus [5]: TF-IDF and BM25 with (k1, b) values (0.9, 0.4), (1.2, 0.75), (0.5, 0.3) and (1.5, 0.6).",
)
replace_once(
    "We compared the five systems using 2,000 paired bootstrap resamples and a paired sign-flip test with Holm correction across ten pairs.",
    "We compared the five systems using 2,000 paired bootstrap resamples and a two-sided paired sign-flip test with 2,000 Monte Carlo draws per pair and Holm correction across ten pairs.",
)
replace_once("**Table 3. Evidence about retrieval comparisons.**", "**Table 4. Evidence about retrieval comparisons.**")
replace_once("**Table 4. Exploratory BGE versus", "**Table 5. Exploratory BGE versus")
replace_once(
    "The paired bootstrap differences were 0.0505 [0.0137, 0.0891] and 0.0376 [0.0154, 0.0608], respectively.",
    "The paired bootstrap differences were 0.0505 [0.0137, 0.0891] and 0.0376 [0.0154, 0.0608], respectively; Table 5 displays the same mean differences to five decimal places.",
)

agent_start = "**Post-hoc Agent inspection (development only).**"
discussion_start = "# VI. Discussion and Limitations"
if text.count(agent_start) != 1 or text.count(discussion_start) != 1:
    raise ValueError("Agent section boundaries not unique")
prefix, rest = text.split(agent_start, 1)
agent_body, suffix = rest.split(discussion_start, 1)
agent_body = agent_body.replace(
    "| Inspection object | Final answer | Additional observation or reference | Interpretation boundary |",
    "**Table A1. Development-only Agent inspections.**\n\n| Inspection object | Final answer | Additional observation or reference | Interpretation boundary |",
)
text = prefix + discussion_start + suffix
appendix = """# Appendix A. Development-only Agent inspection

The following source-exposed checks are included as a supplementary illustration, not a fourth independent audit case. BASE and PROSE denote two previously generated migration candidates, not two independent repositories. For each selected SciFact query, A and B are the two presented candidate passages.

**Post-hoc Agent inspection (development only).**""" + agent_body
replace_once("# Acknowledgment", appendix + "# Acknowledgment")

replace_once(
    "The supplementary Agent inspection uses four source-exposed development tasks and does not establish agent generalization;",
    "The supplementary Agent inspection comprises four source-exposed runs in two settings and does not establish agent generalization;",
)
with destination.open("w", encoding="utf-8", newline="\n") as output:
    output.write(text)
print("source_sha256", hashlib.sha256(source.read_bytes()).hexdigest())
print("output_sha256", hashlib.sha256(destination.read_bytes()).hexdigest())
