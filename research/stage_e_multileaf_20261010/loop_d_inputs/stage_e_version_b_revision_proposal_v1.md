# Paper E Version-B Revision Proposal v1

> Status: `PROPOSAL_ONLY_PAPER_BODY_UNCHANGED` | Evidence: Stage E quantification + multi-leaf v1 + Loop C audit + signature ablation

## 1. Proposed title

**Visibility Is Not Detection: Quantifying Observation Boundaries in Long-Horizon AI Evaluation**

## 2. Three contributions

1. **Construct separation and observation boundaries.** Separate visibility, detection, and harmfulness as distinct evaluation constructs, and quantify family-level observation boundaries.
2. **Protocol identifiability.** Show that single-responsive-leaf hierarchy scores collapse to an affine/rank-equivalent measurement, while clean-only matched operating points are not identifiable under zero-support clean scores.
3. **Instrumentation-aligned controlled localization.** Using preregistered mapping/retrieval/numeric perturbations, show that explicit stage-aligned checkpoints produce separable visibility signatures; ablation demonstrates that localization disappears without directly instrumented stage signals.

Scientific implication: **Structured evaluation can support diagnosis only when its observation surface is aligned with the failure stages; hierarchical organization alone is insufficient.**

The third contribution must not be shortened to “hierarchy localizes failures.”

## 3. Abstract candidate

Long-horizon AI systems are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. We introduce an evaluation-protocol audit that separates these constructs and reports observation boundaries rather than only aggregate accuracy. On a frozen public tabular corpus of 95 tables and 118 controlled injections, 96 injections are checkpoint-visible, while 0/13 OCR-like injections are visible across 11 table clusters. Protocol counts use different detection signals and therefore do not form a single partition of visibility. In the current single-responsive-leaf construction, flat and hierarchical scores are positive affine transformations with identical rankings and ROC geometry; a clean-only matched-FPR operating point is not empirically identifiable because all clean scores are zero. Preregistered mapping, retrieval, and numeric perturbations induce perfectly separable stage-aligned signatures on an explicitly instrumented observation surface. When directly targeted checkpoints are removed, localization collapses to approximately chance, showing that the result reflects stage-aligned instrumentation rather than emergent localization from the remaining hierarchy. Structured evaluation can support diagnosis only when its observation surface is aligned with failure stages; hierarchical organization alone is insufficient.

## 4. Introduction logic

1. Long-horizon AI services move evaluation from a single prediction to a sequence of stages and checkpoints.
2. NIST AI RMF measurement guidance asks whether metrics/TEVV are appropriate and effective; a prerequisite is that the evaluator can observe the target failure mode.
3. Final correctness cannot distinguish robustness from evaluator blindness or silent absorption.
4. Define `V`, `D`, and `H` separately and make their denominators explicit.
5. Quantify family-level and worst-case observation boundaries.
6. Audit whether protocol comparisons are empirically identified once score/threshold structure is considered.
7. Stress the instrument across multiple controlled stages, but disclose when features are a contract-derived codebook.
8. Conclude with a measurement agenda: `Quantify -> Stress-test -> Transfer -> Distill`.

## 5. Evidence table

| Evidence | Status | Paper role |
|---|---|---|
| 96/118 visible, OCR 0/13 over 11 clusters | frozen | headline quantification |
| per-family/micro/worst-family VR | frozen | observation profile |
| visibility x detection cells | frozen, signal mismatch disclosed | diagnostic |
| flat/hierarchy affine/rank equivalence | structural | identifiability audit |
| clean-only matched-FPR equality | `NOT IDENTIFIABLE` | negative boundary |
| M/R/N 24 clusters/stage, 216 injections | controlled | multi-stage stress test |
| LOCO macro-F1/top-1 = 1.0 | controlled | positive but construct-sensitive |
| direct-codebook ablation = 1.0 | exploratory | limitation/negative evidence |
| second dataflow / natural signatures | future | external validity |

## 6. Required limitations

- one frozen public corpus for the quantification result;
- synthetic controlled perturbations;
- harmfulness remains equivalence-dependent;
- OCR uncertainty uses two distinct estimands;
- clean matched-FPR equality is unidentified, not zero-difference confirmed;
- multi-leaf features are contract-derived and perfectly separable by construction;
- no natural-failure localization or hierarchy-localization claim;
- TARGET design supports pooled/macro inference, not separate powered claims for every stage;
- second dataflow, independent semantic scorer and Stage D are separate future work.

## 7. Reviewer-attack responses

| Attack | Response |
|---|---|
| The metrics are invented | report them as a compact decomposition tied to mutation/detection/localization precedents and state which names are project-specific |
| OCR `0/13` is overinterpreted | report raw count, cluster count and two different exact intervals |
| Matched-FPR `[0,0]` proves equality | remove that claim; report structural equivalence and clean-support non-identifiability |
| Multi-leaf localization is tautological | include direct-codebook ablation and restrict the claim |
| Hierarchy is the contribution | keep hierarchy as an evidence instrument, not a detector/localizer |
| Stage D should validate the paper | keep Paper E and Paper D separate until C4-C2 evidence exists |

## 8. ITIL placement

Use one short motivation paragraph only:

- AI-enabled services require lifecycle governance, continual monitoring, oversight and improvement.
- Do not attribute the three advisor slogans to ITIL unless direct official text is found.
- ITIL does not enter the method or novelty claim.

## 9. Decision

Paper E Version B is the clearest near-term route, but only with the construct-sensitive multi-leaf wording. The paper can proceed as `QUANTIFICATION_READY` plus a controlled stress-test section; natural localization and Stage D remain future work.

`DECIDE NEXT LOOP: CONTINUE` to evidence-table/figure production only if no paper-body edit is made without user review.
