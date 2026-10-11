# Abstract Registration Package v1

> target: ABSTRACT_REGISTRATION_READY by 2026-10-18 | mandatory abstract submission 2026-10-19 AoE | venue authority: paper/SANER_RENE_2027_REQUIREMENTS.md
> source: paper/saner_rene_manuscript_v1.md (Abstract) + paper/saner_rene_claim_matrix_v1.json (C1-C3)

## 1. Frozen title
Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation
(single active title; earlier working variants retired per the claim matrix title_note)

## 2. Abstract (ready; copy of the manuscript abstract)
Long-horizon AI systems are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. We audit the observation surface of a staged document-intelligence evaluation using controlled perturbations. On a frozen public tabular corpus (95 tables, 118 controlled header perturbations in six families), 96 injections are checkpoint-visible, while the OCR-like family is unobserved on the frozen scored surface (0/13 injections across 11 clusters at every tested threshold). In the single-responsive-leaf construction, flat and layered contrastive scores are a positive affine/rank transform of one another, and a clean-only matched-FPR operating point is not identifiable, so the frozen evidence cannot rank the two protocols at matched FPR. A preregistered stage-aligned instrumentation study (mapping, retrieval and numeric perturbations; 72 clusters, 216 injections) yields perfectly separable stage signatures (leave-one-cluster-out macro-F1 and top-1 accuracy 1.0; permutation p = 1e-4). The same direct three-leaf codebook also reaches 1.0 while non-direct leaves fall to the three-class chance level (0.3333): the signatures reflect explicit stage-aligned instrumentation in a contract-derived construction, not emergent localisation from hierarchy. A second dataflow (FinQA program perturbations; 89 rows, 30 clusters) could not be transferred: everything was observable by construction and nothing was detected downstream (V=89/89, D=0/89, O=0/89), consistent with a measurement-object mismatch rather than protocol blindness. The contribution is a measurement-validity audit: visibility, detection and harmfulness are distinct constructs; the observation surface itself requires auditing per dataflow; and hierarchical organisation alone does not guarantee diagnosability.

## 3. Author list / order
OWNER INPUT REQUIRED. Internally finalize order and confirm the patent-status gate before the 2026-10-19 abstract. Placeholder only; do not submit without owner confirmation.

## 4. Keywords
observation-surface validity; evaluation blind spots; measurement validity; construct validity; fault injection; hierarchical evaluation; negative results; reproducibility.

## 5. Track / submission type
Track = RENE (Reproducibility Studies and Negative Results). Submission type = RENE: NegativeResult.

## 6. Anonymization / COI plan
- Double-anonymous per SANER: omit author names and affiliations; third-person self-citations; no identifying acknowledgments; anonymize project/repo names and any identifiable links; artifacts via the EasyChair additional-material field or an anonymized repository.
- Data Availability statement after Conclusions with an anonymized repository link (recommended).
- COI: declare any conflicts at submission; none known internally.
- BLOCKING: the evaluation-track draft front matter says not to distribute/submit/upload/publish code before the patent-status gate is cleared. Confirm this gate with the owner before the 2026-10-19 abstract submission.

## 7. Registration checklist (target 2026-10-18)
- [x] frozen title
- [x] abstract text
- [ ] author list/order internally finalized (owner)
- [x] keywords
- [x] track + submission type
- [ ] anonymization/COI plan confirmed + patent gate cleared (owner)