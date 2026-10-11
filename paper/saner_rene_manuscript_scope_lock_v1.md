# SANER RENE Manuscript Scope Lock v1

> Status: `FROZEN_SCOPE_NOT_PAPER_BODY`
> Primary route: `A`
> Optional route: `B — STOPPED (STOP_BRANCH 2026-10-11; retained as history only)`
> Manuscript hard freeze: `2026-10-20 18:00 Asia/Shanghai`

## Tentative Title

**Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation**

## One-Sentence Thesis

Long-horizon evaluation validity depends on auditing the observation surface itself: controlled perturbations expose family-specific observation boundaries, hierarchy alone does not guarantee diagnosability, and cross-dataflow transfer requires causally aligned measurement objects (stated as a design requirement, not a validated law).

## Frozen Contributions

1. **Construct separation and observation boundaries.** Separate visibility, detection and harmfulness, quantify family-level visibility and report the OCR-like `0/13` boundary.
2. **Structural identifiability and instrumentation.** Show that single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent and that clean-only matched-FPR equality is not identifiable; show that, in a contract-derived construction, explicit stage-aligned instrumentation carries the separable controlled signature, while hierarchy alone produces no emergent localisation.
3. **Measurement-object alignment and failed transfer.** Treat FinQA v2 as a failed-transfer autopsy consistent with a measurement-object mismatch, and use NIST/TEVV construct-validity language to motivate auditing observation surfaces.

## Allowed Claims

- Controlled evaluator surfaces can hide some defect families while exposing others.
- Visibility, detection and harmfulness are different constructs.
- OCR-like injections were invisible in the frozen Stage E surface: `0/13` across `11` table clusters.
- Single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent in the current construction.
- Clean-only matched-FPR equality is not empirically identifiable when clean score support is zero.
- Explicit stage-aligned instrumentation can produce separable controlled signatures in the contract-derived construction; non-direct leaves do not establish emergent localization.
- FinQA v2 is consistent with a failed transfer / measurement-object mismatch; it is not evidence of protocol blindness (both terms defined in `paper/saner_rene_claim_matrix_v1.json`).
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
| Affine/rank equivalence and matched-FPR non-identifiability | `docs/research/stage_e_matched_fpr_reanalysis_v1.md` | frozen |
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

### Figure 3 — Instrumentation and measurement-object boundary

Panel A: multi-leaf full/direct/non-direct ablation (`1.0 / 1.0 / 0.3333`).  
Panel B: FinQA failed-transfer boundary (`V=89/89`, `D=0/89`, `O=0/89`) labelled `MEASUREMENT_OBJECT_MISMATCH`, not protocol blindness.

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
