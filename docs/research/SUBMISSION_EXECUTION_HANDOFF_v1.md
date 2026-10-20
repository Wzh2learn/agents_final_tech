# Submission Execution Handoff v1 (Paper E)

> date: 2026-10-13 | status: `PREPARED - OWNER-GATED` | owner decisions paused: venue, author order/corresponding author, abstract registration, formal submission, artifact release.
> This document executes nothing. It is the step list for the owner once authorisations land. Frozen science: do not edit any number, claim, or evidence hash while using this handoff.
> companions: `SUBMISSION_READY_CHECKLIST_v1.md`, `../positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md`, `SANER_RENE_2027_REQUIREMENTS.md` (venue requirements), `../research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md` (audit record).

## 1. Current state (frozen)

- Title (T1): Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation
- Package: `paper/overleaf_bundle/` - manuscript .tex, .bib, 3 figure assets, compiled PDF (9 pages, 0 overfull; body/appendix <= 10 pp; references ~1 p <= 2 pp; double-anonymous).
- Machine audit: `PRE_SUBMISSION_AUDIT = PASS` (LOCAL; GB10 authority = byte-exact `WIDE_EVIDENCE_CHECK = PASS`); independent Loop C audit delivered (v2 -> v3; see audit record).
- Registration package: abstract text below equals the manuscript abstract byte-for-byte (checked by the v3 audit).

## 2. Step 0 - owner inputs required before anything is clicked

1. Venue confirmed (SANER RENE default; alternatives per `../research/positive_repair_20261011/VENUE_PORTABILITY_NOTE_v1.md`).
2. Author list + order + corresponding author FINAL (SANER 2027: after acceptance the author list cannot change and must equal the submitted list).
3. Authorisation to register the abstract and to submit.
4. Artifact status: keep "not public, prepare-only" (current default) unless the owner changes it.

## 3. Step 1 - abstract registration (SANER RENE deadline: 2026-10-19 AoE)

Portal: EasyChair `saner27tracks` (per `SANER_RENE_2027_REQUIREMENTS.md`), RENE Track, submission type `RENE: NegativeResult`.

Copy-paste block:

Title:
Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation

Abstract (plain text, single paragraph):
Staged document-intelligence pipelines are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. Long-horizon and tool-using systems motivate the same questions, but the evidence here comes from one staged document-intelligence evaluator that we audit with controlled perturbations. On a frozen public tabular corpus (95 tables, 118 controlled header perturbations in six families), 96 injections are checkpoint-visible, while the OCR-like family is unobserved on the frozen scored surface (0/13 injections across 11 clusters at every tested threshold); the existing single judge classified all 13 as referentially equivalent under its table-context contract, so benign absorption remains an alternative interpretation rather than independent ground truth. In the single-responsive-leaf construction, the unrounded flat and layered contrastive scores are a positive affine/rank transform of one another and retain identical ranks, so corresponding decisions are structurally equivalent; the zero-by-construction clean panel leaves the registered deployment operating point unresolved, which does not negate that equivalence. A preregistered stage-aligned instrumentation study (mapping, retrieval and numeric perturbations; 72 clusters, 216 injections) yields perfectly separable stage signatures (leave-one-cluster-out macro-F1 and top-1 accuracy 1.0; permutation p = 1e-4). The same direct three-leaf codebook also reaches 1.0, while the non-direct leaves reach the three-class chance level (0.3333) and, under the frozen tie-as-incorrect rule, still separate mapping from the retrieval and numeric stages without separating retrieval from numeric: the signatures reflect explicit stage-aligned instrumentation in a contract-derived construction, not emergent localization from hierarchy. A second dataflow (FinQA program perturbations; 89 rows, 30 clusters) could not be transferred: the detection predicate is defined and the counts are reproducible, but the result fields it reads are not recomputed from the perturbed program, so V=89/89, D=0/89, O=0/89 describes this carrier construction rather than a detection ability, a measurement-object mismatch rather than protocol blindness. The contribution is a measurement-validity audit: visibility, detection and harmfulness are distinct constructs; the observation surface itself requires auditing per dataflow; and hierarchical organization alone does not guarantee diagnosability. The product of the audit is a boundary map and the removal of three tempting over-readings: that a visible score gap implies a performance gap, that an unobserved family is a harmful blind spot, and that separability follows from hierarchical organization, rather than a detector ranking.

Keywords:
observation-surface validity; evaluation blind spots; measurement validity; construct validity; fault injection; hierarchical evaluation; negative results; reproducibility.

Notes: the RENE CFP states no abstract word limit (UNKNOWN in the requirements record); register the text above verbatim; author identifiers are entered per the portal form and stay visible only to the chairs under double-anonymous review.

## 4. Step 2 - full paper submission (deadline: 2026-10-23 AoE)

1. Upload the compiled PDF from the frozen bundle (`paper/overleaf_bundle/saner_rene_manuscript_v1.pdf`) as the submission file; keep the full bundle for the artifact package.
2. Confirm double-anonymous compliance in the form (no author block, third-person self-citations, no identifying links).
3. Page limits: 10 pp including figures/appendices + up to 2 pp references-only (verified). Format: IEEEtran 10pt conference, no compsoc option.
4. Data Availability statement is already in the paper (recommended by RENE; kept factual: "prepared for release", no live URL).
5. Do NOT rename the title; SANER states titles cannot change after acceptance without program-chair approval.

## 5. Step 3 - after submission

- Notifications: 2026-12-08; Camera-ready + author registration: 2027-01-08.
- Camera-ready only: replace "Anonymous Submission" with the frozen author block; wire the artifact URL if the owner releases it; keep the number/claim freeze unless a new author-level adjudication happens.
- If the venue switches before Step 1: stop; run the portability note's estimate and re-confirm framing decisions with the owner first (no manuscript edit without that decision).

## 6. Materials index

| Item | Path |
|---|---|
| Manuscript (science source of truth) | `paper/saner_rene_manuscript_v1.md` |
| Submission bundle (compile + upload) | `paper/overleaf_bundle/` |
| Readiness checklist (10 items PASS) | `docs/research/SUBMISSION_READY_CHECKLIST_v1.md` |
| Abstract registration package | `research/positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md` |
| Venue requirements (primary-source record) | `paper/SANER_RENE_2027_REQUIREMENTS.md` |
| Venue portability note | `research/positive_repair_20261011/VENUE_PORTABILITY_NOTE_v1.md` |
| Independent audit record | `docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md` |
| Freeze guardrails | `docs/archive/2026-10-20_entry_consolidation/PROJECT_FINAL_STATE_BEFORE_SUBMISSION.md` |

**Nothing in this handoff has been executed; registration and submission remain owner actions.**
