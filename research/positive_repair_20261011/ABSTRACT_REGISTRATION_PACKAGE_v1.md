# Abstract Registration Package v1

> target: ABSTRACT_REGISTRATION_READY by 2026-10-18 | mandatory abstract submission 2026-10-19 AoE | venue authority: paper/SANER_RENE_2027_REQUIREMENTS.md
> source: paper/saner_rene_manuscript_v1.md (Abstract) + paper/saner_rene_claim_matrix_v1.json (C1-C3)

## 1. Frozen title
Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation
(single active title; earlier working variants retired per the claim matrix title_note)

## 2. Abstract (ready; copy of the manuscript abstract)
Staged document-intelligence pipelines are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. Long-horizon and tool-using systems motivate the same questions, but the evidence here comes from one staged document-intelligence evaluator that we audit with controlled perturbations. On a frozen public tabular corpus (95 tables, 118 controlled header perturbations in six families), 96 injections are checkpoint-visible, while the OCR-like family is unobserved on the frozen scored surface (0/13 injections across 11 clusters at every tested threshold); the existing single judge classified all 13 as referentially equivalent under its table-context contract, so benign absorption remains an alternative interpretation rather than independent ground truth. In the single-responsive-leaf construction, the unrounded flat and layered contrastive scores are a positive affine/rank transform of one another and retain identical ranks, so corresponding decisions are structurally equivalent; the zero-by-construction clean panel leaves the registered deployment operating point unresolved, which does not negate that equivalence. A preregistered stage-aligned instrumentation study (mapping, retrieval and numeric perturbations; 72 clusters, 216 injections) yields perfectly separable stage signatures (leave-one-cluster-out macro-F1 and top-1 accuracy 1.0; permutation p = 1e-4). The same direct three-leaf codebook also reaches 1.0, while the non-direct leaves reach the three-class chance level (0.3333) and, under the frozen tie-as-incorrect rule, still separate mapping from the retrieval and numeric stages without separating retrieval from numeric: the signatures reflect explicit stage-aligned instrumentation in a contract-derived construction, not emergent localization from hierarchy. A second dataflow (FinQA program perturbations; 89 rows, 30 clusters) could not be transferred: the detection predicate is defined and the counts are reproducible, but the result fields it reads are not recomputed from the perturbed program, so V=89/89, D=0/89, O=0/89 describes this carrier construction rather than a detection ability, a measurement-object mismatch rather than protocol blindness. The contribution is a measurement-validity audit: visibility, detection and harmfulness are distinct constructs; the observation surface itself requires auditing per dataflow; and hierarchical organization alone does not guarantee diagnosability. The product of the audit is a boundary map and the removal of three tempting over-readings - that a visible score gap implies a performance gap, that an unobserved family is a harmful blind spot, and that separability follows from hierarchical organization - rather than a detector ranking.

## 3. Author list / order
H1 PARTIALLY_RESOLVED (2026-10-13): first author = 王中华 (final); advising teachers with substantive contributions may be co-authors; final co-author order and corresponding author pending advisor confirmation. Do not submit without owner confirmation.

## 4. Keywords
observation-surface validity; evaluation blind spots; measurement validity; construct validity; fault injection; hierarchical evaluation; negative results; reproducibility.

## 5. Track / submission type
Track = RENE (Reproducibility Studies and Negative Results). Submission type = RENE: NegativeResult.

## 6. Anonymization / COI plan
- Double-anonymous per SANER: omit author names and affiliations; third-person self-citations; no identifying acknowledgments; anonymize project/repo names and any identifiable links; artifacts via the EasyChair additional-material field or an anonymized repository.
- Data Availability statement after Conclusions with an anonymized repository link (recommended).
- COI: declare any conflicts at submission; none known internally.
- H2 CLOSED (2026-10-13): no patent issue; the advisor approved external submission. Abstract registration and submission still require the owner go-ahead (co-author order + corresponding author pending).

## 7. Registration checklist (target 2026-10-18)
- [x] frozen title
- [x] abstract text
- [ ] author list/order internally finalized (owner)
- [x] keywords
- [x] track + submission type
- [ ] anonymization/COI plan confirmed + owner go-ahead for registration/submission (owner)