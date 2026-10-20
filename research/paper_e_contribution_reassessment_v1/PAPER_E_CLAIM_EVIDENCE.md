# Paper E: Claim-Evidence-Use Matrix

Status: `EXPLORATORY_REASSESSMENT`; frozen manuscript and results are unchanged.

## 1. Three evidence lines

| evidence line | question | what the current evidence establishes | what it does not establish |
|---|---|---|---|
| Paper E manuscript | Can a staged document-evaluation case support a useful measurement-audit contribution? | The saved case separates observation, decision predicates, score structure and dataflow binding; it removes several invalid readings of the same aggregates. | A universal audit method, a detector ranking, or general document-intelligence performance. |
| TQ-4/TQ-5 | Do five upgrade cases add semantic-gold evidence for a stronger verification claim? | Local artifact facts and bounded case observations; frozen scores remain valid for their frozen contracts. | C-vs-B superiority, common blind spots, population error rates, or broad document-QA claims. |
| Experience reuse | Does real history improve the restricted calculation panel? | A complete 12-task execution chain exists, and B0 is 16/16 on the fixed 16-task panel. | Experience efficacy or inefficacy: U/E were identical and R/C/H were never run. |

The three lines are independent. TQ `NO_PROMOTION` applies to TQ promotion claims. `CEILING_ON_THIS_PANEL` applies to accuracy-headroom identification on the frozen reuse panel. Neither ruling retroactively invalidates the manuscript's measurement audit.

## 2. Claim matrix

Evidence type abbreviations:

- `D`: deterministic recomputation or direct artifact fact.
- `O`: descriptive observation on a frozen sample.
- `S`: bounded semantic interpretation requiring a stated contract.
- `P`: proposed procedure or interpretation, not yet independently validated.

| ID | proposed claim | source and evidence type | strongest defensible wording | wording not supported | external research use | disposition |
|---|---|---|---|---|---|---|
| C1 | Visibility, protocol detection and harmfulness are different measurement objects. | Manuscript §§1, 5.1, 6.3; frozen injection records; `D/S`. | In this staged evaluator, an injected change can be observed at a checkpoint, consumed or ignored by a decision predicate, and be benign or harmful only relative to a stated equivalence contract. | These are three universal latent variables, or their separation alone predicts downstream correctness. | Stop interpreting one aggregate as all three; report the observation surface and equivalence contract before comparing systems. | Keep as the conceptual spine, but describe it as a measurement decomposition for this case, not a new validity theory. |
| C2 | Aggregate checkpoint visibility hides family-level boundaries. | Manuscript §5.1: 96/118 visible overall; OCR-like 0/13 across 11 clusters at every tested threshold; `D/O`. | On the frozen scored surface, visibility is family-dependent, and the OCR-like family was not observed under the five tested thresholds. | The evaluator has a universal OCR blind spot; the family is harmful; the rates estimate natural document defects. | Require per-family observation profiles and thresholds before treating non-detection as failure or success. | Keep with the harmfulness and synthetic-injection caveats adjacent to the claim. |
| C3 | OCR-like non-response is not proven harmfulness. | Manuscript §5.1; one existing judge called all 13 referentially equivalent; `S`. | Benign absorption remains an alternative interpretation because harmfulness depends on the table-context equivalence contract and is not independently established. | The judge is human gold, the substitutions are harmless, or 0/13 is a false-negative rate. | Require an explicit equivalence contract and independent harmfulness evidence before calling a family a blind spot. | Keep as a boundary result; move judge details to methods/appendix. |
| C4 | Flat and layered scores are structurally equivalent in the single-responsive-leaf construction. | Manuscript §5.2 and algebraic score path; unrounded scores are a positive affine/rank transform; `D`. | In this construction, the unrounded flat and layered contrastive scores induce the same rank and corresponding threshold decisions. | Hierarchical and flat evaluation are generally equivalent; the historical detection counts were equal; a deployment operating point was calibrated. | Check score algebra and decision predicates before reading a raw protocol gap as ranking quality. | Keep; this is a strong, narrow technical fact and a useful identifiability warning. |
| C5 | The clean calibration panel cannot identify a unique operating point. | Manuscript §5.2 and clean-only reanalysis: 2,382 usable clean records have score support exactly `{0}`; `D`. | The frozen clean-only procedure leaves the registered operating point unresolved because every positive threshold has observed FPR zero on this panel. | Matched-FPR evaluation is impossible generally; hierarchical scoring is better or worse; the old fixed-threshold analysis is confirmed. | Design clean calibration panels with non-degenerate support, or state the operating point as unresolved. | Keep as a negative calibration finding; do not merge it with C4. |
| C6 | Stage-aligned instrumentation yields perfect localization in the controlled construction. | Manuscript §5.5: 216 injections, 72 clusters, macro-F1/top-1 1.0; `D/O`. | Explicit stage-aligned leaves perfectly separate three constructed stages on this frozen injection surface. | Hierarchy discovers stages, natural failures localize perfectly, or the score generalizes to other pipelines. | Validate whether diagnostic gains come from instrumentation or merely from labels aligned to the manipulated stage. | Keep, always paired with the ablation. |
| C7 | Perfect localization is not evidence that hierarchy itself adds diagnosability. | Same rows, direct three-leaf codebook also 1.0; non-direct leaves 0.3333 top-1 with 0.6667 ties; `D/O`. | The direct codebook contains the separability; non-direct leaves provide partial mapping-versus-other information but do not separate retrieval from numeric under the frozen rule. | Non-direct leaves are useless, or hierarchy never helps in other constructions. | Compare against a direct instrumentation baseline before crediting organizational structure. | Keep as the principal incremental-information control. |
| C8 | FinQA transfer is a measurement-object mismatch. | Manuscript §5.6: mutated program fields visible 89/89, detection 0/89, outcome 0/89 because downstream results are not recomputed; `D/S`. | This execution does not estimate detection ability because the perturbation and predicate do not share a causally updated measurement object. | The detector is blind, FinQA is unsuitable, or transfer generally fails. | Before transferring perturbations, bind mutation, observation and outcome fields through the same recomputed state. | Keep as an autopsy and design requirement, not as evidence of a general law. |
| C9 | TQ frozen labels conflate several measurement layers. | `CONTRIBUTION_RULING_v2.md` and `CASE_EVIDENCE_MATRIX.md`; `D/S`. | The five TQ cases show that a frozen `NO_MATCH` can coexist with legal evidence, valid arithmetic before rounding, scope mismatch, parser normalization and invalid verifier output. | Five actor errors, five reference errors, or a verifier failure rate. | Preserve frozen scoring while separately reporting notation, scope, precision, provenance and output validity. | Move to a short boundary section or appendix; it supports the audit vocabulary but not a method-superiority claim. |
| C10 | A staged-evaluation audit checklist helps reviewers. | Synthesis of C1-C9; `P`. | We propose a review sequence: identify observation surface, bind perturbation to recomputed state, inspect score algebra and threshold support, then state the equivalence contract and decision use. | The checklist is validated, general, causal, or superior to existing validity practice. | Gives an evaluator author/reviewer a concrete pre-comparison checklist whose consequences can later be tested. | Keep only as `PROPOSED_DESIGN`; a second independently applied dataflow is the minimal validation gap. |

## 3. TQ cases: contribution boundary

TQ contributes diagnostic distinctions, not a new scoring method:

1. T01 shows that source notation and signed normalization are separate from semantic correctness.
2. T07 shows that a stored derivation can coexist with an unestablished denominator and an inconsistent actor answer.
3. T08 shows that evidence provenance is not task-scope satisfaction: a dated paragraph can locate a value without answering an all-years question.
4. T10/T12 show that evidence-location legality is not support, and that an unstated precision policy can dominate the frozen score.
5. Invalid verifier JSON remains invalid even when prose contains a plausible decision.

These facts are useful for Paper E because they make the measurement-object distinction concrete. They cannot be used to rank B/C, estimate an error rate, or claim independent semantic gold. The earlier TQ disposition of thesis/methods material is retained unless a narrower use is explicitly chosen.

## 4. Manuscript allocation

### Main text

- Measurement decomposition and evaluation-identifiability question.
- Frozen construction and observation surfaces.
- Family visibility, including OCR-like 0/13 with harmfulness caveat.
- Flat/layered affine/rank equivalence and unresolved operating point.
- Stage instrumentation result plus direct-codebook/non-direct ablation.
- FinQA measurement-object boundary.
- The proposed review sequence, clearly labelled as a design proposal.

### Appendix

- Full threshold and matcher sensitivity tables.
- Historical fixed-threshold evidence with its superseded scope.
- TQ T01/T07/T08/T10/T12 as bounded measurement-layer cases.
- Exact prompts, JSON contracts, manifests and reproduction details.
- Details of the failed independent-scorer route and the non-passing source gates.

### Delete or narrow

- Any phrase implying a general detector ranking.
- Any claim that hierarchy is superior or generally equivalent.
- Any "blind spot" language without the observation-surface and harmfulness qualifiers.
- Any implication that the FinQA zero counts measure detection capability.
- Any presentation of the proposed checklist as validated methodology.
- Any suggestion that the TQ cases establish model error rates or semantic gold.

## 5. Alternative explanations still open

1. The OCR-like family may be benignly absorbed under the judge's referent contract rather than harmfully missed.
2. The stage-localization result may be entirely explained by contract-aligned direct instrumentation; the ablation supports this explanation over emergent hierarchy.
3. The FinQA transfer may additionally involve scorer portability, threshold transfer or corpus shift; the present evidence selects measurement-object mismatch as a sufficient boundary diagnosis, not an exclusive cause.
4. TQ differences may reflect prompt exposure, parser policy or semantic ambiguity rather than verifier quality.
5. The proposed audit steps may be common practice under different terminology; nearest-work comparison is required before novelty language.

## 6. Evidence strength summary

The manuscript has one strong narrow algebraic result (C4), two construction-bounded empirical audits (C2/C6-C7), two explicit boundary diagnoses (C3/C8), and one useful synthesis (C1). That is enough to support a measurement-audit case paper if novelty is located in the staged observation surface and identifiability diagnosis. It is not enough for a universal method claim without an independent application that changes another evaluation's interpretation or decision.
