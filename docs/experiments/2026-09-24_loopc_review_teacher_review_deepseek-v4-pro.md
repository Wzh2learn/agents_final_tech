# Loop C independent review of the evaluation-track manuscript (model deepseek-v4-pro)

> Dispatched by Loop D on 2026-09-24 under the goal completion criterion (independent Loop C / dual-model review).
> Mode: evidence packet inline (manuscript + claim manifest + readiness record), no tools, 1 turn(s), cost $0.2682.
> Body below is the session final message verbatim; assembled by Loop D without edits.

# Independent Reviewer Report

**Manuscript:** *Discriminability-Aware Evaluation of Long-Horizon Document AI Pipelines via Hierarchical Checkpoints and Defect Visibility Analysis*
**Review type:** Evaluation-track evidence audit against claim manifest v1 and readiness record v2
**Date:** 2026-09-24

---

## 1. Overall Verdict

**REVISE**

The manuscript presents a coherent, well-scoped evaluation study that correctly treats the evaluation protocol itself as an object of empirical investigation. The core findings — the OCR-blind 0-of-13 visibility result and the matched-FPR affine equivalence between flat and hierarchical protocols — are retained honestly and interpreted within their proper limits. The claim-evidence mapping in the manifest is faithful to the manuscript text. The readiness record’s own assessment («静态通过») is substantiated by the material. However, two non-negotiable administrative gates remain open, and a single missing-data artifact in Section 6 is disclosed but not remediated. The paper cannot proceed to submission in its current form regardless of scientific merit. Revision should address the blocking items below and strengthen the major items before re-review.

---

## 2. Blocking Issues

### B1. Patent-status gate not closed — release prohibition active (Title block / Readiness §对外公开)

**Location:** Title block: «Do not distribute, submit, upload to arXiv, or publish code before the patent-status gate is cleared.» Readiness record: «专利状态尚未由用户确认».

**Evidence:** The manifest’s `release_gate` is `"patent_status_confirmation_required"`. The readiness record explicitly marks external publication as «阻塞».

**Severity:** BLOCKING. The authors’ own gate prohibits any onward movement. A reviewer cannot ethically recommend acceptance of a manuscript that carries an active legal-IP prohibition against submission. This is not a scientific objection; it is a pre-condition that must resolve to `"confirmed_clear"` (or equivalent) before the paper enters any review pipeline.

**Suggested fix:** Obtain formal clearance from the relevant IP officer or patent counsel. Record the clearance date, scope, and any carve-outs in a revised manifest. Remove the prohibition notice from the title block only after clearance.

### B2. Author metadata, affiliation, and target venue absent (Title block / Readiness §对外公开)

**Location:** Title block: «Author and affiliation are to be filled in.»

**Evidence:** The manuscript is anonymous by omission, not by double-blind policy. The readiness record confirms «作者、单位和目标会议模板未填写».

**Severity:** BLOCKING. The paper cannot be submitted to any venue without author list and affiliations. While this is trivially resolvable, a reviewer cannot assess conflicts of interest, author contribution, or venue fit without this information.

**Suggested fix:** Populate author block and identify at least one candidate target venue with its formatting requirements. If the venue requires double-blind submission, replace the filler text with an anonymization protocol rather than leaving it blank.

---

## 3. Major Issues

### M1. Preregistered transfer/second-dataflow arm deferred without timeline or criteria for reinstatement (Section 6, paragraph 6)

**Location:** «A second dataflow and a second scorer were preregistered but are not reported. The transfer corpus lacks the table layer required to define per-family constructible sample counts, so the transfer arm was deferred rather than silently replaced.»

**Evidence:** The readiness record notes that the three-stage direction is «未闭环» (not closed). The manifest’s SP-C3 scope limit states «No second-dataflow result and no second-scorer result are claimed.» The claim is therefore honest, but the absence is structural: the paper’s core argument — that visibility profiles and checkpoint trees generalise as an evaluation methodology — remains untested on a second corpus.

**Severity:** MAJOR. The deferral is disclosed, which is commendable. But an evaluation-track paper that introduces a framework for protocol-level auditing and then reports results on a single corpus has an external-validity gap that disclosure alone does not close. The reader needs to know (a) whether the missing table layer is a permanent property of the transfer corpus or a resolvable annotation gap, and (b) under what conditions the transfer arm would be executed.

**Suggested fix:** Add a concrete statement in Section 6 specifying whether the transfer corpus will be annotated, replaced, or abandoned. If abandoned, explain why the single-corpus evidence is nevertheless sufficient for the evaluation-track claim (which is about the protocol’s self-characterisation, not about cross-domain performance).

### M2. Single input-varying leaf limits the matched-FPR affine-equivalence finding to a degenerate case (Section 5.2, paragraph 3)

**Location:** «Under this construction, hierarchy supplies decomposable evidence but cannot demonstrate additional localization value until more than one leaf varies.»

**Evidence:** The manifest’s SP-C2 scope limit reads: «Localization value cannot be established while only one input-varying leaf is present.» This is an honest self-limitation, but it also means the paper’s headline finding — that hierarchical structure provides no discriminability gain — may be an artifact of a pipeline whose checkpoint tree has only one scored leaf that actually moves under perturbation. A tree with, say, three varying leaves distributed across branches might produce a different matched-FPR result.

**Severity:** MAJOR. The finding is reported as a «negative but useful» result in the Abstract and Conclusion, yet the locomotive of that finding (the single-varying-leaf property) is only mentioned once in Section 5.2 and not interrogated. A reader may reasonably ask: is this a domain property (tabular QA with header drift rarely disturbs multiple leaves), or a design property (the checkpoint tree over-partitions the scoring surface)?

**Suggested fix:** Add a brief diagnostic in Section 5.2 or 6 that characterises *why* only one leaf varies: is it the tree topology, the perturbation surface, or the scoring contracts? If this cannot be determined from the current evidence, state it explicitly as a limitation and note what additional instrumentation would resolve it.

### M3. Section 5.5 mechanism case is structurally disconnected from the evaluation-track contribution (Section 5.5)

**Location:** Entirety of Section 5.5 («Evaluation-driven rule consolidation is a mechanism case»), and SP-C4 in the manifest.

**Evidence:** SP-C4 is marked `"mechanism_case_only"` with the scope limit «The downstream efficacy effect is not significant and is not presented as a contribution.» The p=0.375 result is reported without spin. However, the section occupies approximately 10% of the Results and introduces a deterministic consolidation loop that is not described in the Method section. A reader following the Method → Results chain will encounter Section 5.5 as an unmotivated detour: the paper’s core concern is *whether the evaluator can see defects*, not *what to do after it sees them*.

**Severity:** MAJOR. The section is not dishonest, but it dilutes the paper’s focus. If the evaluation track does not require a downstream-use demonstration, the section should be removed or sharply condensed into a one-sentence forward-looking remark in the Discussion. If the venue expects a use-case, the Method section must introduce the consolidation loop so the Results are legible.

**Suggested fix:** Either (a) remove Section 5.5 and relocate its content to a single sentence in Section 7 («Future work could route evaluation findings into a gated deterministic consolidation loop; preliminary evidence shows no significant downstream benefit»), or (b) add a subsection in Section 3 that describes the consolidation mechanism, its gain–collateral gate, and the regression-verification protocol.

---

## 4. Minor Issues

### m1. Preregistered range criterion failure left unexplained (Section 5.3, sentence 2)

**Location:** «The literal preregistered range criterion fails at 0.7 and 0.9 and is reported as failed.»

**Evidence:** The statement reports a failure without defining the criterion or interpreting the failure. A preregistered criterion that fails is an important honesty signal, but the reader cannot assess whether the failure is expected (e.g., a criterion designed to tighten at high thresholds where one changed header contributes ≤ 1/n) or indicates a problem.

**Severity:** MINOR — does not threaten the core claims, but leaves an unreconstructed gap.

**Suggested fix:** Add a one-sentence definition of the range criterion and explain why its failure at high thresholds is consistent with (or informative beyond) the 1/n header-contribution explanation given in the preceding sentence.

### m2. “Class flip” operational definition absent (Section 5.1, paragraph 3)

**Location:** «changing the score normalization causes five class flips, all within the date-variation family»

**Evidence:** “Class flip” is used without definition. It presumably means that a perturbation-family pair changes its relative visibility rank, but the exact operation (rank inversion? crossing a threshold boundary? moving between visibility tiers?) is unclear.

**Severity:** MINOR — the claim about ranking instability is intelligible, but the metric is underspecified.

**Suggested fix:** Define “class flip” on first use (e.g., «a class flip occurs when two perturbation families exchange their ordinal position in the visibility ranking»), or replace the term with a more descriptive phrase.

### m3. Judge calibration description conflates two distinct agreement concepts (Section 5.3, paragraph 3)

**Location:** «rejudged summaries of historical 0–5 judgments differ from the frozen dimension means by at most 0.5» … «Agreement is therefore an aggregate observation, not evidence of cell-level interchangeability.»

**Evidence:** The text correctly warns against over-interpretation, but the description of what was measured («rejudged summaries of historical 0–5 judgments») is ambiguous. The readiness record clarifies: this is a «历史维均分的 control 汇总差异» (aggregate difference on historical dimension means in the control condition), not a re-evaluation of the same original answers by a different judge. The manuscript text could make this distinction sharper.

**Severity:** MINOR — the warning is present, but a hurried reader may miss the distinction between aggregate-mean agreement and cell-level agreement.

**Suggested fix:** Revise the sentence to: «In the control-state comparison, a judge re-summarising the same evidence artifacts produced aggregate dimension scores within 0.5 of the frozen dimension means. This checks reproducibility of aggregate score summaries, not inter-judge agreement on the same original answers.»

### m4. Figure paths are relative and may not survive PDF generation (Figures 1, 2)

**Location:** `../docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg` and `../docs/experiments/figures_paper/fig_visibility_spectrum.png`

**Evidence:** The paths use relative `../` notation that assumes the Markdown file is at `paper/teacher_review_draft_v1.md`. A build system that copies the file to a different directory (common in LaTeX or PDF pipelines) will break these references.

**Severity:** MINOR — no impact on review content, but a production hazard.

**Suggested fix:** Either use absolute paths within the repository root or, better, flatten the figure references to match the target venue’s figure-inclusion conventions.

### m5. Reference formatting inconsistency (References)

**Location:** Reference list entries use varying arXiv ID formats (some with `arXiv:` prefix, others without) and inconsistent handling of multi-author lists (some use «et al.», others list more names).

**Evidence:** Compare «arXiv:2210.15615, 2022» with «arXiv:2401.16313, 2024» and «arXiv:2606.24381, 2026» — all consistent. But the author-list truncation varies: some entries list three authors, others list one plus «et al.» without a clear rule.

**Severity:** MINOR — will be caught by venue formatting.

**Suggested fix:** Apply the target venue’s reference style uniformly before submission.

---

## 5. Claim–Evidence Consistency Assessment

### SP-C1: *«Defect visibility is type-dependent and OCR-like perturbations are fully blind in the tested evaluator.»*

**Verdict: CONSISTENT**

The manuscript reports 96/118 visible injections with OCR-like family at 0/13 across five thresholds (Section 5.1). The `manuscript_tokens` in the manifest (`96/118`, `are visible in 0/13 cases`, `five thresholds`) all appear in the manuscript text. The scope limit (`harmfulness remains equivalence-definition dependent`) is explicitly discussed in Section 5.1 («The harmfulness label is also criterion-dependent»). No over-claiming detected. The claim status `supported_with_scope_limit` is appropriate.

### SP-C2: *«Hierarchical checkpoints provide decomposition but do not improve matched-FPR discrimination on the current corpus.»*

**Verdict: CONSISTENT**

Table 1 reports the three raw detection counts (112, 85, 13), and Section 5.2 reports the matched-FPR bootstrap interval [0,0]. The manuscript explicitly states «hierarchical structure provides evidence decomposition, not better detection sensitivity» (Abstract) and «hierarchy supplies decomposable evidence but cannot demonstrate additional localization value» (Section 5.2). The scope limit (`Localization value cannot be established while only one input-varying leaf is present`) is present in the manifest and acknowledged in the manuscript. However, see Major Issue M2: the single-leaf condition is not interrogated, which weakens the interpretive depth of this otherwise honest finding.

### SP-C3: *«The blind-family structure is stable across tested matchers and seeds, while visible-family ranking depends on scoring caliber.»*

**Verdict: CONSISTENT**

Section 5.1 reports stabilty of the blind family («The blind family remains the same under four edit-distance matcher configurations»), and Section 5.3 reports seed sensitivity (0.7895, 0.7835, 0.7556). The «five class flips» token appears in Section 5.1. The scope limit (`No second-dataflow result and no second-scorer result are claimed`) is respected throughout: neither a second dataflow nor a second scorer is claimed in the manuscript. The deferred transfer arm is disclosed in Section 6. See Major Issue M1 for the structural concern.

### SP-C4: *«Evaluation findings can be routed through a gated deterministic consolidation loop.»*

**Verdict: CONSISTENT (within stated scope)**

The `mechanism_case_only` status is appropriate. Section 5.5 reports «all 7» adversarial rejections, «all 5» expanded-collision rejections, and `p=0.375`. No significance claim is made; the confidence interval [0, 0.1056] is reported. The scope limit is respected: «The downstream efficacy effect is not significant and is not presented as a contribution.» However, see Major Issue M3: the section’s placement in Results without a Method counterpart is structurally problematic regardless of claim honesty.

---

## 6. Honesty Checks

### 6.1 Forbidden manuscript markers

**Result: CLEAN.** None of the ten forbidden markers (`TODO`, `append-only`, `main thread`, `Loop D`, `Ruling `, `ruling `, `[logs/graph/eval/`, `[docs/experiments/`, `主线程`, `决策 `) appear in the manuscript text. The two figure paths use `docs/experiments/` but without bracket notation (`../docs/experiments/figures_paper/`); this is a path reference, not a forbidden log-path marker, and is acceptable.

### 6.2 Prohibited claims

- **Hierarchical superiority:** Not claimed. The manuscript explicitly states «We do not claim universal coverage, superior hierarchical detection, a formal geometric "blind cone," or significant downstream gains» (Section 1, final paragraph). Multiple locations reinforce that hierarchy provides decomposition, not better detection.
- **Trained-student results:** Not claimed anywhere in the manuscript. The readiness record confirms no training has occurred.
- **Significant downstream benefit from gated consolidation:** Not claimed. p=0.375 reported without spin.

### 6.3 Retained adverse findings

- Matched-FPR affine equivalence ([0,0] interval): Retained (Section 5.2).
- PSO null result (same mean as greedy, 7,650 vs. 67 evaluations): Retained (Section 5.4).
- Gate no-significant-benefit (p=0.375): Retained (Section 5.5).
- Preregistered range criterion failure: Retained (Section 5.3).
- Deferred transfer arm: Retained (Section 6).

**Verdict: PASS.** All adverse findings required by the manifest and readiness record are present in the manuscript without relabeling.

### 6.4 Internal-review / patent-gate notices

- Patent-gate notice: PRESENT in title block.
- Internal-review-only designation: PRESENT in title block («Do not distribute, submit, upload to arXiv, or publish code»).
- Author/affiliation absence: ACKNOWLEDGED in title block («Author and affiliation are to be filled in»).

---

## 7. Reviewer-Facing Risks

### R1. Venue-fit ambiguity

The manuscript is labelled «evaluation track» but does not name a target venue. Evaluation-track papers at major NLP/ML venues (e.g., ACL, EMNLP, NeurIPS Datasets & Benchmarks) have specific expectations about baselines, metric standardisation, and community resources. The paper’s methodological focus on the evaluation protocol (rather than a new dataset or benchmark leaderboard) may not align with all evaluation-track calls. This is an editorial concern rather than a scientific one, but reviewers should note it when assessing contribution scope.

### R2. Evidence not independently replicable within the review package

The manifest cites `logs/graph/eval/*.json` files and `docs/experiments/*.md` files as evidence. These are not included inline and were not available to this reviewer. The consistency assessment in Section 5 above therefore rests on the manifest’s claim–evidence mapping and the manuscript’s internal coherence, not on independent verification of the raw data. A full audit would require access to those files and, ideally, a run of the reproduction script (seed-42 byte-for-byte check reported in Section 5.3).

### R3. Readiness record’s own caveat about Office visual verification

The readiness record states «Office 视觉核对未完成» — the DOCX visual layout (pagination, missing characters, table overflow) has not been verified. This reviewer assessed the Markdown source, not the DOCX, and cannot confirm that the submission file matches the reviewed text in all typographic details.

### R4. Single-corpus scope limits the evaluation-track contribution taxonomy

The paper’s contribution is structured as a *framework + case study*, not a *benchmark*. Reviewers expecting a new dataset, a leaderboard, or a standardised evaluation protocol for community adoption may find the contribution too narrow. The paper partially mitigates this by explicitly disclaiming cross-domain generalisation (Section 6), but the resulting contribution classification (framework evaluation? meta-evaluation case study?) may provoke debate.

### R5. The SP-C4 mechanism case may attract misplaced criticism

If a reviewer treats SP-C4 as a fourth contribution rather than a mechanism case, they will legitimately object that an evaluation-track paper should not include a non-significant downstream-use demonstration. The manuscript would benefit from clearer signalling that SP-C4 is an appendix-level illustration, not a numbered contribution.

---

## Summary Table

| Category | Count | Items |
|---|---|---|
| Blocking | 2 | B1 (patent gate), B2 (missing metadata) |
| Major | 3 | M1 (deferred transfer arm), M2 (single-leaf degeneracy), M3 (Section 5.5 structural disconnect) |
| Minor | 5 | m1 (unexplained criterion failure), m2 (undefined “class flip”), m3 (ambiguous judge calibration), m4 (relative figure paths), m5 (reference formatting) |
| SP-C1 | CONSISTENT | — |
| SP-C2 | CONSISTENT | Degeneracy concern noted (M2) |
| SP-C3 | CONSISTENT | Transfer-arm gap noted (M1) |
| SP-C4 | CONSISTENT | Structural concern noted (M3) |
| Honesty | PASS | All adverse findings retained; no forbidden markers; no prohibited claims |
| Section 2 blocking | NONE | Related Work is adequate for an evaluation-track internal draft |
