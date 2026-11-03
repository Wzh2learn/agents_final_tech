#!/usr/bin/env python3
"""Derive an ICDAR working draft without changing the ICINT manuscript."""

import collections
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]
SOURCE = ROOT / "paper_e_icint_draft.md"
OUTPUT = ROOT / "paper_e_icdar_working.md"
RESULTS = REPOSITORY / "logs/graph/eval/checkpoint_discrimination_tables_v2.json"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("expected exactly one manuscript anchor: " + old[:80])
    return text.replace(old, new, 1)


def main():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    rows = [row for table in data["tables"] for row in table["injections"]]
    counts = collections.defaultdict(lambda: [0, 0])
    for row in rows:
        counts[row["type"]][0] += int(row["visible"])
        counts[row["type"]][1] += 1
    expected = {"alias_variant": [43, 47], "date_variant": [15, 17],
                "mixed_lang": [20, 20], "ocr_similar": [0, 13],
                "unit_suffix": [5, 5], "prefix_noise": [13, 16]}
    if dict(counts) != expected:
        raise ValueError("frozen visibility family counts differ")

    text = SOURCE.read_text(encoding="utf-8")
    text = replace_once(text,
        'title: "From Scores to Supported Claims: Measurement Audits of Document and Retrieval Evaluation"',
        'title: "From Detection Scores to Supported Claims: Measurement Audits for Document Analysis and Retrieval"')
    intro = ("Document-specific work also evaluates semantic alignment and stage-level extraction: "
             "SCORE [7] addresses valid alternative representations in generative parsing, while "
             "Soric et al. [8] benchmark table extraction across heterogeneous PDFs and analyze evaluation metrics. "
             "Our case studies ask a complementary question about the interpretation of an existing evaluation's "
             "thresholds and retrieval comparisons; we do not benchmark document extraction models or claim a superior parsing metric.")
    expanded_intro = ("Document analysis evaluation already addresses several related problems. SCORE [7] evaluates "
        "semantically equivalent but structurally different generative parsing outputs; Soric et al. [8] examine "
        "end-to-end and subtask table-extraction evaluation across heterogeneous PDFs. Those studies assess document "
        "parsing or extraction under their own evaluation designs. We instead audit the interpretation of measurements "
        "produced by a particular frozen evaluator, including what its selected mapping surface can observe and what "
        "follows from its scoring scale. Our table inputs are derived from financial QA data, not page-image OCR outputs. "
        "We do not benchmark document extraction models or claim a superior parsing metric.\n\n"
        "The document case is the primary construction: a controlled change to a table header travels through a "
        "mapping rule into a checkpoint score and then a thresholded decision. Its observation and decision contracts "
        "can be inspected separately. The two external ranking cases complement this document-centered analysis by "
        "examining whether scores and comparison claims remain stable under other declared conventions; they do not "
        "turn the controlled header study into an external validation of a document-image analysis method.")
    text = replace_once(text, intro, expanded_intro)

    visibility = ("Of 118 injections, 96 were visible. None of the 13 OCR-like changes was visible on this surface. "
                  "This observation does not establish 13 harmful misses: one existing semantic judge classified "
                  "the cases as referentially equivalent, without an independent human reference.")
    expanded_visibility = visibility + (
        " The family-level visible/injected counts were 43/47 alias variants, 15/17 date variants, "
        "20/20 mixed-language variants, 0/13 OCR-like variants, 13/16 prefix-noise variants and 5/5 unit-suffix "
        "variants. These are injection counts in the seed-42 panel; the 118 changes are clustered within 95 tables. "
        "They characterize the particular matcher-relative surface, not generic document defects or actual OCR error rates.")
    text = replace_once(text, visibility, expanded_visibility)

    stage = ("The three directly targeted leaves gave the same result; removing them reduced top-1 to 0.333 "
             "under the frozen tie-as-incorrect rule, with a 0.667 tie rate.")
    expanded_stage = ("The three directly targeted parsing, retrieval and reconciliation leaves gave the same result; "
        "removing them reduced top-1 to 0.333 under the frozen tie-as-incorrect rule, with a 0.667 tie rate. "
        "The classifier was evaluated by leaving one source cluster out at a time, so the three injected stages "
        "from the held-out cluster were not included when fitting its centroids. This ablation tests the source of "
        "the observed signal in the controlled instrument, not error localization on an independent deployed system.")
    text = replace_once(text, stage, expanded_stage)

    scaling = ("Matching the threshold to its score scale thus recovers the same decisions in this single-leaf "
        "setting and makes the original detection-rate gap interpretable. A deployment threshold still requires calibration.")
    concise_scaling = ("In this single-leaf setting, a positive rescaling preserves score order; retaining the same "
        "decision rule also requires rescaling its threshold. The matched-grid example uses saved outputs and does "
        "not calibrate a deployment threshold or establish equivalence with multiple responsive leaves.")
    text = replace_once(text, scaling, concise_scaling)

    dense_detail = ("The single BGE comparison originally used a paired bootstrap: the mean differences were 0.0505 "
        "[0.0137, 0.0891] on SciFact and 0.0376 [0.0154, 0.0608] on NFCorpus, uncorrected for a comparison family. "
        "It used normalized embeddings, the model's retrieval query prefix and a 512-token cap. A separate trec_eval "
        "execution agreed on 1,246 dense and BM25 per-query scores to the reference program's four-decimal print "
        "precision. The later 15-pair test answers a different question about multiplicity and must not be represented "
        "as a prospective verification of the selected BGE comparison.")
    concise_dense = ("The earlier single-pair BGE analysis used normalized embeddings, the model's query prefix and a "
        "512-token cap. Its uncorrected paired-bootstrap differences were 0.0505 [0.0137, 0.0891] on SciFact and "
        "0.0376 [0.0154, 0.0608] on NFCorpus. A separate trec_eval run agreed on 1,246 dense and BM25 per-query "
        "scores to four-decimal print precision. The later 15-pair test addresses multiplicity, not prospective confirmation.")
    text = replace_once(text, dense_detail, concise_dense)

    limitation = ("These findings have limited scope: the first case uses controlled table perturbations, "
                  "FinRank uses lexical baselines and has an unresolved reproduction gap, and the BEIR analyses "
                  "are retrospective runs over two datasets with a post-hoc dense extension.")
    expanded_limitation = ("These findings have limited scope: the first case uses controlled perturbations to "
        "structured tables, without a page-image recognition experiment or an independent human reference for the "
        "OCR-like variants. FinRank uses lexical baselines and has an unresolved reproduction gap, and the BEIR "
        "analyses are retrospective runs over two datasets with a post-hoc dense extension.")
    text = replace_once(text, limitation, expanded_limitation)
    text = replace_once(text, "manuscript text in Sections I–VI.",
                        "manuscript text in Sections 1–6.")
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        output.write(text)
    print("Wrote", OUTPUT, "with independently recounted seed-42 family counts")


if __name__ == "__main__":
    main()
