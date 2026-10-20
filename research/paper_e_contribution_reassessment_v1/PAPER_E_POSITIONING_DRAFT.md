# Paper E Positioning Draft

Ruling: `NARROW_AND_CONTINUE_RECOMMENDATION`.

This is a positioning draft, not a rewrite of the frozen manuscript. All numerical results and frozen statements remain unchanged.

## 1. Preferred position

**Position P1, selected:** A reproducible measurement audit of a staged document-intelligence evaluation, showing how observation surfaces, decision predicates, score algebra and dataflow binding determine which comparisons are identifiable, and giving an application-ready review sequence.

**One-sentence contribution:** In a controlled staged document-evaluation case, we separate checkpoint visibility, protocol detection and contract-relative harmfulness; show why a raw flat/hierarchical gap can be structurally uninformative and why stage-localization can be instrumentation-induced; and derive a review sequence for checking observation and measurement-object binding before comparing systems.

**Why P1 is the only defensible main-paper position:** It is grounded in a complete frozen case and does not require the TQ upgrade to establish method superiority. Its external value is concrete: an evaluator author can change what is reported and how a comparison is interpreted before spending more experiments.

## 2. Rejected alternatives

### P2: A new detector or verifier benchmark

Rejected. TQ remains `NO_PROMOTION`; the five cases do not establish C-vs-B superiority, error rates or semantic gold. The manuscript's strongest result is structural/measurement-bound, not detector ranking. Making P2 the main claim would exceed the evidence.

### P3: A general theory of hierarchical evaluation

Rejected. The affine/rank result is explicitly limited to the single-responsive-leaf construction, and the stage result is explicitly stage-aligned. The evidence does not establish general hierarchy equivalence or superiority.

### P4: A generic "stages matter" agent-evaluation paper

Rejected. AgentBench and τ-bench already make process/tool interaction central. Paper E must retain the document-evaluator observation-boundary and dataflow-binding case to be distinct.

## 3. Title candidates

Preferred: **Auditing the Observation Surface in Staged Document Evaluation**

Alternative: **What Can This Evaluation Observe? A Measurement Audit of Staged Document Intelligence**

Avoid titles promising "detecting blind spots," "hierarchical superiority," or "a universal metric."

## 4. Contributions (maximum three)

1. **Measurement-object separation:** visibility, decision detection and contract-relative harmfulness are reported separately, so a visible change is not silently promoted to a harmful error.
2. **Identifiability audit:** a deterministic score-equivalence analysis and a direct-codebook/non-direct-leaf ablation show when raw protocol gaps and perfect localization do not identify ranking quality or hierarchy benefit.
3. **Boundary-aware transfer autopsy and review sequence:** the FinQA carrier demonstrates that mutation, observation and outcome must share a causally updated measurement object; the proposed review sequence turns that boundary into actionable checks for evaluator authors.

The third contribution is explicitly a design proposal unless an independent application demonstrates that it changes an evaluation decision.

### Craft implications from the 2026 comparison set

- *Measurement Without Validity* and *Measuring What Matters* already provide general compounding-validity models, construct-validity audits, prescriptions and checklists. Paper E must not present “audit the measurement chain” or “use a checklist” as the novel contribution.
- *Same-Number Citation Swaps* is the closest concrete writing model: it separates numerical correctness, cited-role support and acceptance, declares prospective versus exploratory analyses, and reports costs and failure conditions. Paper E should match that reporting discipline.
- The final Introduction should use the six-move sequence: concrete evaluator/operator stakes, structural identification gap, named observation-boundary abstraction, one-paragraph audit intuition, evidence-backed contributions and bounded numerical preview.
- The Evaluation should use claim-first subsections with explicit takeaways: observation surface, score identifiability, instrumentation attribution and dataflow binding. The direct-codebook/non-direct ablation is the central control, not an optional appendix.

## 5. One-page argument

**Problem.** Staged document pipelines are usually ranked by final answers or aggregate scores. That score does not say whether an intermediate instrument observed a defect, whether the decision rule consumed the observation, or whether the defect changed the outcome under the stated equivalence contract.

**Case.** In one frozen public-tabular evaluator, controlled header perturbations and stage-aligned injections expose the chain. The OCR-like family is 0/13 on the frozen scored surface, but the single judge treats those cases as referentially equivalent under its table-context contract. Thus non-observation is not automatically harmfulness.

**Identification result.** In the single-responsive-leaf construction, flat and layered contrastive scores are positive affine/rank transforms, so the raw detection gap cannot identify ranking quality. The clean calibration panel is degenerate and leaves the deployment operating point unresolved. Separately, the stage study reaches 1.0 macro-F1/top-1 on the direct instrumented surface, but the direct three-leaf codebook also reaches 1.0 while non-direct leaves fall to 0.3333 with ties. The gain is attributable to explicit instrumentation, not emergent hierarchy.

**Transfer boundary.** FinQA program perturbations are visible but the downstream result fields are not recomputed from the mutated program. The 89/89 visibility and 0/89 detection counts therefore describe a measurement-object mismatch, not a detector failure rate.

**Use.** The case supports a checklist for evaluator authors and reviewers: state the observation surface, bind mutation to recomputed state, inspect score algebra and threshold support, and state the equivalence contract before comparing systems. The checklist is a design proposal; its value is that each step prevents a specific over-reading that this case demonstrates.

**Boundary.** The evidence is one public corpus, synthetic perturbations, one local judge and a non-portable second carrier. It does not support universal blind spots, detector superiority, natural-failure rates or general document-intelligence claims.

## 6. Proposed paper structure

1. Introduction: final-score identifiability problem and three measurement objects.
2. Related work: construct validity, behavioral/mutation testing, tool-agent process evaluation; explicitly locate Ross et al., CheckList, metamorphic testing, τ-bench and AgentBench.
3. Audit case and contracts: frozen corpus, perturbation map, observation surfaces, equivalence contract and decision predicates.
4. Results A: family visibility and OCR-like harmfulness boundary.
5. Results B: affine/rank score equivalence and unresolved calibration point.
6. Results C: stage localization and direct-codebook ablation.
7. Results D: FinQA measurement-object mismatch.
8. Proposed review sequence and implications for evaluator design.
9. Limitations and bounded conclusion.

Appendices carry detailed thresholds, manifests, TQ cases, prompt surfaces and reproduction records.

## 7. Abstract draft

Final-answer scores can hide failures in staged document-intelligence pipelines: a defect may be invisible to the observation surface, ignored by a decision predicate, or harmless under the evaluation's equivalence contract. We audit one frozen evaluator with controlled header and stage perturbations. In this construction, visibility is family-dependent (96/118 checkpoint-visible; OCR-like 0/13 on the frozen scored surface), while harmfulness remains contract-relative. The unrounded flat and layered scores are positive affine/rank transforms, so their raw detection gap does not identify ranking quality; the clean-only panel also leaves the operating point unresolved. Stage-aligned instrumentation separates three constructed stages perfectly, but the direct three-leaf codebook does the same, while non-direct leaves fall to chance-level top-1 with ties. A second FinQA carrier shows a measurement-object mismatch: the mutated program is visible, but downstream result fields are not recomputed for the detector. We contribute a boundary map and a proposed review sequence for checking observation surfaces, score algebra and dataflow binding before interpreting evaluation comparisons. The result is a measurement audit, not a detector ranking or universal blind-spot claim.

## 8. Introduction problem and contribution paragraphs (draft)

**Problem paragraph.** Evaluation of staged document systems often reports a final score as if it were a direct measure of system quality. Yet the score can conflate different events: an intermediate instrument may or may not observe a perturbation; a decision predicate may or may not consume that observation; and an outcome may or may not change under the evaluation's equivalence contract. When these objects are conflated, a score gap can be read as protocol sensitivity, a non-response can be called a harmful blind spot, and a hierarchy can be credited with localization that is actually supplied by direct instrumentation.

**Contribution paragraph.** We present a reproducible measurement audit of one staged document-intelligence evaluator. The audit separates visibility, detection and contract-relative harmfulness; shows that flat and layered contrastive scores are affine/rank-equivalent in the single-responsive-leaf construction; and uses a direct-codebook ablation to show that perfect stage localization is instrumentation-induced rather than emergent from hierarchy. A second dataflow is retained as a boundary case because its perturbation and detector do not share a causally updated measurement object. These results support an application-ready review sequence for evaluation designers, while explicitly leaving universal generalization and detector ranking outside the claim.

## 9. Minimal gap before stronger submission claims

**Gap to close:** independently apply the proposed review sequence to one second, causally aligned staged evaluation or dataflow, with the review and decision rule fixed before reading its results.

**Alternative explanation to exclude:** the current case merely labels local implementation bugs and the proposed steps do not change how a competent evaluator author interprets or reports a comparison.

**Minimum evidence:** a documented second case where the review separates at least two plausible interpretations (for example, score non-identifiability versus true sensitivity, or observation failure versus harmfulness), and an independent reviewer records whether the interpretation/decision changes.

**Craft constraint:** the second case must report separate endpoints for observation, decision and outcome, identify prospective versus post-hoc analyses, and state costs and failure conditions. Merely applying a generic construct-validity checklist does not satisfy this gap.

**Stop result:** if the second case shows no interpretation or decision change, retain Paper E as a bounded case/methods-adjacent paper and remove "validated method" language; do not add more cases merely to inflate evidence.

## 10. Current disposition

Continue with narrowing. The manuscript is worth revising as a measurement-audit case paper; it is not ready for a universal-method or detector-performance claim. The next revision should make the proposed checklist visibly distinct from Ross et al. and metamorphic-testing work and reserve any "validated" wording until the minimal independent application is complete.
