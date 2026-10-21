# SANER RENE Manuscript Scope Lock v1

> Status: `FROZEN_SCOPE_NOT_PAPER_BODY`
> Primary route: `A`
> Optional route: `B — STOPPED (STOP_BRANCH 2026-10-11; retained as history only)`
> Manuscript hard freeze: `2026-10-20 18:00 Asia/Shanghai`

## Dated Amendment — 2026-10-21 Canonical Integration

> Current disposition: `NARROW_AND_CONTINUE`.
> This amendment supersedes active title, case accounting and submission wording only. The freeze record below is preserved unchanged as history.

- Canonical title: **Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and Evidence-Ranking Evaluation**.
- Exactly two counted cases: (1) the staged document evaluator, with FinQA as a nested boundary probe inside Case 1; (2) the FinRank evidence-ranking audit.
- MA-CERD and adaptive revalidation are not Paper E cases.
- FinRank v1 tie metrics and materiality thresholds are preregistered and unchanged. The canonical trimmed/`text_sha1` branch and the `442/305` and `33/2` counts are post-hoc v2 corrections after the wrong-identity v1 application; v1's raw-exact `293/220` result remains preserved.
- Visibility, detection, harmfulness, score sensitivity, decision stability and reproduction gap are separate constructs.
- Residual global and metadata metric drift is exposed; its cause is unresolved.
- The six-step review sequence is a proposed checklist, not a validated universal method.
- The AI-assisted 24-task review and deferred model-free/scoring routes are historical/internal-only and excluded from the submission body.
- The compact feedback/gain-collateral result is removed from the submission body.

## Tentative Title

**Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation**

## One-Sentence Thesis

Evaluation validity depends on auditing the observation surface itself: in a staged document-intelligence evaluator, controlled perturbations expose family-specific observation boundaries, hierarchy alone does not guarantee diagnosability, and a second dataflow's transfer requires causally aligned measurement objects (a design requirement, not a validated law).

## Historical, Non-Operative

The retained material below records the earlier single-case freeze. It does
not override the 2026-10-21 two-case/provenance amendment above and must not be
used as the current contribution statement.

## Frozen Contributions

1. **Construct separation and observation boundaries.** Separate visibility, detection and harmfulness, quantify family-level visibility and report the OCR-like `0/13` boundary.
2. **Structural identifiability and instrumentation.** Show that in the single-responsive-leaf construction the two protocols' decisions are structurally equivalent (positive affine/rank transform, identical ranks), while the registered deployment operating point remains unresolved under a degenerate clean panel; show that, in a contract-derived construction, explicit stage-aligned instrumentation carries the separable controlled signature, that the direct codebook matches the full vector, and that non-direct leaves carry partial stage information rather than none.
3. **Measurement-object alignment and failed transfer.** Treat FinQA v2 as a failed-transfer autopsy consistent with a measurement-object mismatch, and use NIST/TEVV construct-validity language to motivate auditing observation surfaces.

## Allowed Claims

- Controlled evaluator surfaces can hide some defect families while exposing others.
- Visibility, detection and harmfulness are different constructs.
- OCR-like injections were invisible in the frozen Stage E surface: `0/13` across `11` table clusters; the existing single judge classified all 13 as referentially equivalent, so non-response alone does not establish harmful false negatives.
- Single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent in the current construction.
- The registered deployment operating point remains unresolved under the zero-support clean panel; the structural equivalence of the two protocols' decisions is a separate finding and holds.
- Explicit stage-aligned instrumentation can produce separable controlled signatures in the contract-derived construction; non-direct leaves separate mapping from retrieval/numeric but not retrieval from numeric, and do not establish emergent localization.
- FinQA v2 is consistent with a failed transfer / measurement-object mismatch: the detection predicate is defined and the counts are reproducible, but the downstream result fields are not regenerated from the perturbed program; it is not evidence of protocol blindness (both terms defined in `paper/saner_rene_claim_matrix_v1.json`).
- NIST motivates evaluation of metric and TEVV effectiveness; it does not certify this project's metrics.

## Forbidden Claims

- Universal blind spots across AI systems.
- Hierarchy localizes natural failures.
- Hierarchy alone produces emergent localisation.
- Visibility-detection separation universally transfers across dataflows.
- FinQA confirms protocol blindness.
- A causal-aware checkpoint-selection method has been validated.
- Automatic checkpoint/oracle generation or complete causal discovery.
- Semantic process correctness or harmfulness beyond the stated equivalence contract.
- Stage D/C4 training or PRM performance claims.

## Core Evidence Table

| Claim | Evidence | Status |
|---|---|---|
| 95 tables / 118 injections; 96 visible | `docs/research/stage_e_118_quantification_v1.md` | frozen |
| OCR-like `0/13` across 11 clusters | `docs/research/stage_e_zero_event_uncertainty_note_v1.md` | frozen |
| Family visibility profile | `logs/graph/eval/checkpoint_discrimination_tables_v2.json`, `t2_visibility_sensitivity.json` | frozen |
| Affine/rank equivalence and unresolved matched-FPR operating point | `docs/research/stage_e_matched_fpr_reanalysis_v1.md` | frozen |
| Multi-leaf controlled signatures | `docs/research/stage_e_multileaf_result_packet_v1.md` | construct-sensitive |
| Direct-codebook ablation | `docs/research/stage_e_multileaf_signature_ablation_v1.md` | negative/boundary |
| FinQA failed transfer | `docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md`, `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md` | autopsy/design boundary |
| NIST/TEVV framing | `docs/research/nist_measurement_validity_ledger_v2.md` | motivation only |

## Figure Definitions

### Figure 1 — Measurement chain

`NIST / long-horizon motivation -> controlled failure -> checkpoint visibility -> protocol detection -> outcome/harm`

Purpose: explain why final correctness cannot establish observation validity.

### Figure 2 — Defect family × visibility

Rows: six Stage E families. Columns: threshold/visibility surface. Include `0/13` OCR-like boundary and family rates.

### Figure 3 — Multi-leaf localization and ablation

Panel A (macro-F1): full/direct/non-direct bars (`1.0 / 1.0 / 0.3333`) with the majority-class reference (`0.1667`).  
Panel B (top-1): full/direct/non-direct bars (`1.0 / 1.0 / 0.3333`) with the chance reference (`0.3333`).  
The FinQA failed-transfer boundary (`V=89/89`, `D=0/89`, `O=0/89`, labelled `MEASUREMENT_OBJECT_MISMATCH`) is carried in the manuscript text, not plotted in this figure.

## Role Boundaries

- **FinQA:** failed-transfer autopsy and causal-alignment requirement.
- **Multi-leaf:** controlled evidence for stage-aligned instrumentation and the hierarchy-alone limitation.
- **NIST:** measurement-validity motivation and TEVV effectiveness framing.
- **ITIL:** at most one motivation paragraph on lifecycle governance and continual improvement.

## Limitations

- One frozen public tabular corpus and synthetic controlled perturbations.
- Limited mutation mechanisms; no natural-failure distribution.
- Harmfulness is equivalence-dependent.
- FinQA transfer is consistent with unaligned measurement objects; alternative explanations (scorer non-portability, threshold non-transfer, corpus shift) are not excluded.
- No positive causal-aware checkpoint-selection method is claimed.
- Per-stage multi-leaf inference is descriptive at the current sample size.

## Out of Scope

- Stage D training / PRM performance.
- Causal-aware checkpoint selection as a validated contribution.
- Automatic checkpoint or oracle generation.
- Complete causal discovery.
- Natural-failure localization.
- Universal cross-system generalization.

Classification note: the formal result class is `SECOND_FLOW_MIXED`; the scientific interpretation is `MEASUREMENT_OBJECT_MISMATCH`, recorded in `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`.
- **FinQA classification:** formal result `SECOND_FLOW_MIXED`; accepted methodological boundary `MEASUREMENT_OBJECT_MISMATCH` is recorded in `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`.
