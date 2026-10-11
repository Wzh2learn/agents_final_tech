# Loop C Independent Re-Audit — SANER Route A Claim/Manuscript Boundary (TRACK_A_CLAIM_AUDIT)

You are the independent Loop C auditor. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. This is the RE-AUDIT after the Track A critical fixes to the reviewer-attack audit findings F1-F11 (task track-a-reviewer-attack-audit-c-20261011, 2026-10-11).

## Round context
- The prior audit returned CHALLENGE_CLAIM_SET with F1/F2 CRITICAL and F3-F11 HIGH/MEDIUM/LOW findings. Loop D applied wording/governance-only repairs (NO new experiments; NO scientific claims added or removed; frozen measured quantities unchanged).
- Residuals declared by Loop D (verify and judge their blocking status): F7 partial (readiness RR-12/RR-17 refresh and the 5-internal-claims-vs-3-matrix mapping not yet enumerated); F8 partial (compound claim clauses separated in text; C1-C3 IDs kept for reference stability); F9 (draft section 5.5 Stage-R boundary paragraph retained, self-declared outside the contribution); F10 (official NIST citation decision deferred to the owner; Figure-3 cell status labels not yet rendered); DOCX derivatives not yet regenerated.
- Target: `TRACK_A_CLAIM_AUDIT = PASS`. PASS requires F1-F6 fully closed and no CRITICAL/HIGH item left open; enumerate any low/governance residuals separately (they do not block PASS if non-overreaching).

## Loop D closure map (claimed; verify against the embedded revised texts)
- F1 claim matrix: repaired in place as valid JSON (schema_version 2, local parse verified): 14 hash bindings covering EVERY cited evidence path (incl. finqa_v2_measurement_object_mismatch_autopsy_v1.md and finqa_v2_formal_v3_activation_record_v1.md), keys are full paths, harmfulness clause restored to forbidden_claims (10 items), definitions block added. Original malformed file preserved at paper/archive/saner_rene_claim_matrix_v1_original_malformed_20261011.json (git mv).
- F2 contribution 3: rewritten (scope lock contributions + V-B proposal): "stage-aligned instrumentation carries the separable signature in a contract-derived construction"; ablation = exploratory boundary with the 3-class chance level (0.3333) stated; no "controlled localization", no transfer success.
- F3 FinQA causal + undefined vocabulary: "because" -> "consistent with" everywhere; alternatives named; protocol blindness / MEASUREMENT_OBJECT_MISMATCH / SECOND_FLOW_MIXED / M aliasing / R/N downstream non-estimability defined in the matrix definitions block; thesis and V-B implication softened to design-requirement wording.
- F4 harmfulness forbidden-claim: restored to the machine-readable list.
- F5 blindness deficit framing: title unified; draft/preview Section 5.1/5.3/6.1 now say "unobserved on the frozen scored surface"/"observation boundary"; the "blind cone" phrase remains only as an explicitly denied claim.
- F6 numbers: pooled rate stated as denominator-weighted 219/282 with per-seed denominators (75/95, 76/97, 68/90); CI estimator + seed + grid stated for [0.7270,0.8227] and for [0.6947,0.8737]/[0.1263,0.2947] (table-level percentile bootstrap, seed 20260830, k/95 grid); oracle ceiling now 20/21 vs 40/67 with "different denominators, not a ratio comparison"; 95-table corpus rule stated in the matrix (drift-v0 deterministic injection-carrier subset, seed 42/ratio 0.3); 2,382 clean-row construction stated (usable (table_uid, column) rows of non-injected frozen D3 inputs; fold = sorted(table UID) mod 5).
- F7 fixed parts: single active title across scope lock/matrix/draft/preview/V-B; scope-lock optional route marked STOPPED.
- F8-F11: see residuals above; F11 (internal-consistency positives) intentionally preserved.

## Required output (machine-parseable)
## INDEPENDENCE DECLARATION
## F-ITEM CLOSURE VERIFICATION
- F1..F11: CLOSED | PARTIAL | NOT_CLOSED + one-line evidence (cite embedded text)
## PER-CLAIM ADMISSIBILITY (C1, C2, C3): admissible / narrowed-required / not-admissible + one line each
## FORBIDDEN-LANGUAGE RESCAN (list any remaining hits with location; if none, say NONE)
## RESIDUAL RISKS
## VERDICT: PASS | CONDITIONAL | FAIL
(If CONDITIONAL/FAIL: exact blocking items. If PASS: optional non-blocking notes.)
End with the literal line: CLAIM_REAUDIT_COMPLETE

--- BEGIN paper/saner_rene_claim_matrix_v1.json ---{
  "schema_version": 2,
  "status": "FROZEN_SCOPE_NOT_PAPER_BODY",
  "primary_route": "A",
  "optional_route": "B - STOPPED (STOP_BRANCH as of 2026-10-11; retained as history only, not an active option)",
  "hard_freeze": "2026-10-20T18:00:00+08:00",
  "title": "Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation",
  "title_note": "Single active title (2026-10-11 fix). Earlier working variants used 'Blind Spots'/'Quantifying Observation Boundaries'; both are retired.",
  "thesis": "Long-horizon evaluation validity depends on auditing the observation surface itself: controlled perturbations expose family-specific observation boundaries, hierarchy alone does not guarantee diagnosability, and cross-dataflow transfer requires causally aligned measurement objects (stated as a design requirement, not a validated law).",
  "claims": [
    {
      "id": "C1",
      "claim": "Visibility, detection and harmfulness are distinct constructs and the frozen evaluator has family-specific observation boundaries.",
      "evidence": [
        "docs/research/stage_e_118_quantification_v1.md",
        "docs/research/stage_e_observability_metrics_v1.md",
        "logs/graph/eval/checkpoint_discrimination_tables_v2.json",
        "logs/graph/eval/t2_visibility_sensitivity.json"
      ],
      "allowed": true
    },
    {
      "id": "C2",
      "claim": "Single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent (structural diagnosis) and clean-only matched-FPR equality is not identifiable (a statement about the frozen evidence, not a ranking of the protocols); in the controlled multi-leaf construction, stage-aligned instrumentation carries the separable signature, and hierarchical organisation alone does not produce emergent localisation.",
      "evidence": [
        "docs/research/stage_e_matched_fpr_reanalysis_v1.md",
        "docs/research/stage_e_multileaf_result_packet_v1.md",
        "docs/research/stage_e_multileaf_signature_ablation_v1.md"
      ],
      "allowed": true
    },
    {
      "id": "C3",
      "claim": "Cross-dataflow transfer requires causal alignment of measurement objects. The frozen FinQA v2 second-dataflow result (formal class SECOND_FLOW_MIXED) is consistent with a failed-transfer / measurement-object mismatch; it is not evidence of protocol blindness (both terms are defined in `definitions`), because the detection predicate was undefined by construction for the perturbed object.",
      "evidence": [
        "docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md",
        "docs/research/finqa_causal_exposure_preregistration_proposal_v1.md",
        "docs/experiments/2026-10-11_loop_c_causal_checkpoint_mvp_design_audit.md",
        "docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md",
        "docs/research/finqa_v2_formal_v3_activation_record_v1.md"
      ],
      "allowed": true
    }
  ],
  "definitions": {
    "protocol blindness": "An evaluation protocol that cannot observe a defect under any tested observation surface or threshold within its frozen configuration. Used only as a defined alternative; the paper does not claim or exclude it without this definition.",
    "MEASUREMENT_OBJECT_MISMATCH": "The perturbation and the detection rule operate on different measurement objects, so the detection predicate cannot respond to the perturbation by construction; this is a statement about object alignment, not about detector quality.",
    "SECOND_FLOW_MIXED": "The frozen formal result class of the FinQA v2 second-dataflow run: a mixed observation/detection pattern produced under a construction that was not causally aligned. A classification only; it is not a performance or transfer claim.",
    "M aliasing (Route B)": "Two M-stage leaf slots written from the same predicate, so the source-local / downstream partition is not separable (MVP design audit, filed HIGH).",
    "R/N downstream non-estimability (Route B)": "For stages R and N no downstream checkpoint responded on the frozen carriers, so the downstream causal term could not be estimated.",
    "harmfulness equivalence-dependence": "Harmfulness is defined relative to a stated equivalence contract; changing the contract can change the label (hence the boundary framing)."
  },
  "forbidden_claims": [
    "universal blind spots across AI systems",
    "hierarchy localizes natural failures",
    "hierarchy alone produces emergent localisation",
    "visibility-detection separation universally transfers",
    "FinQA confirms protocol blindness",
    "causal-aware checkpoint selection is validated",
    "automatic checkpoint or oracle generation",
    "complete causal discovery",
    "semantic process correctness or harmfulness beyond the stated equivalence contract",
    "Stage D/C4 or PRM performance"
  ],
  "figures": {
    "figure_1": "NIST/long-horizon motivation -> failure -> checkpoint visibility -> protocol detection -> outcome/harm",
    "figure_2": "six defect families x visibility surface; OCR-like 0/13 across 11 clusters",
    "figure_3": "multi-leaf full/direct/non-direct ablation plus FinQA failed-transfer measurement-object boundary"
  },
  "evidence_hashes": {
    "docs/research/stage_e_118_quantification_v1.md": "39134a1359cd153175f793e0b1d5ff8ebaed5ee8df8e415a79fcfb42a9ff9084",
    "docs/research/stage_e_observability_metrics_v1.md": "204f178f35ce28398f9b770453a4edf1904ee933e37cbbc378fbde3bb11e38c1",
    "logs/graph/eval/checkpoint_discrimination_tables_v2.json": "7c634b8a180b87b9d565699426704f266bc79427bd64223caaa2d50e56cffb72",
    "logs/graph/eval/t2_visibility_sensitivity.json": "eff82b0b7abbb8edcb8aef24a921806a760624fc84b57b3c2e54331394f99ea5",
    "docs/research/stage_e_zero_event_uncertainty_note_v1.md": "97ccc92ccd7d31b9c3e37b1d8250d439f21d0e79c251f298254355097a57a5b7",
    "docs/research/stage_e_matched_fpr_reanalysis_v1.md": "611b2c2f2e2cabf62a007e281fcd999f913df2f4e220474f7d1a31a1ce4bc1e9",
    "docs/research/stage_e_multileaf_result_packet_v1.md": "99ccc81b92db2d5350aafdefb44ce73ec055ab8e33008e54aed5456ec3d9cbb8",
    "docs/research/stage_e_multileaf_signature_ablation_v1.md": "4d4961d4eb274ce8adaa786920bbb33c41c5b3be473bcc941380f5fafd089c3d",
    "docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md": "2435b838537c8bdbf5d687fb3b6c71e6db35fc0c06a094915f549c801bdfd3a6",
    "docs/research/finqa_causal_exposure_preregistration_proposal_v1.md": "6a9d6965988f80dcd3be3702577540eeba16138a2c7754ba34930d1ce0cb6216",
    "docs/experiments/2026-10-11_loop_c_causal_checkpoint_mvp_design_audit.md": "7ccc685d466f91299e42b77612f216c74cfda1eeeb60e73c2645a176b1005182",
    "docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md": "340794d244aa29f1846c02f04237cb6d757d6f0e73dcfc229f7f2431fafedf67",
    "docs/research/finqa_v2_formal_v3_activation_record_v1.md": "a74aed656f63f560b274c9a465e47766d8931c7ee60d33a6e009f8311bfa105f",
    "docs/research/nist_measurement_validity_ledger_v2.md": "84cb4621b1bde099a9a4c76b04c033eb91cd2af1fe25bbf1b63e3a404a145cec"
  },
  "hash_binding_note": "sha256 values are bound to GB10 raw bytes (the authoritative host) and were all recomputed/verified on 2026-10-11. Every cited evidence path has an entry; no cited path is unbound.",
  "corpus_note": "Frozen evaluation corpus: normalized public TAT-QA table base (no client data); the drift-v0 injector (seed 42, ratio 0.3, deterministic) marks the injection-carrier tables; the frozen surface uses the 95 such tables and their 118 injections (docs/experiments/2026-08-18_drift_injection_v0.md).",
  "internal_manifest_note": "paper/claim_manifest_v1.json is the finer-grained Stage-E internal claim ledger; this matrix is the SANER Route A authority. Residual: a clause-level mapping between the two is not yet enumerated; cite this matrix.",
  "route_b_qualification": {
    "status": "NO",
    "decision": "STOP_BRANCH",
    "reason": "No two execution-confirmed downstream stages with source-local/downstream separation and two genuine mechanisms per stage; the C audit found M aliasing and R/N downstream non-estimability (both defined in `definitions`)."
  }
}
--- BEGIN paper/saner_rene_manuscript_scope_lock_v1.md ---
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

--- BEGIN paper/teacher_review_draft_v1.md ---
# Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation

> Evaluation-track evidence draft for internal teacher review, 2026-09-22. This document covers the evaluation stage only; the current three-stage paper direction is documented separately. Author and affiliation are to be filled in. Do not distribute, submit, upload to arXiv, or publish code before the patent-status gate is cleared.

## Abstract

Long-horizon document intelligence systems are usually scored on final-answer correctness, which cannot distinguish a defect observed by an intermediate checkpoint from one that was silently absorbed, nor reveal that the evaluator itself was blind to the defect. We study evaluation-protocol validity rather than proposing a stronger detector. Our meta-evaluation separates checkpoint-level visibility, protocol-level detection, and equivalence-dependent harmfulness, using hierarchical checkpoint evidence as an instrument and per-family visibility profiles as the reporting surface. On a frozen public tabular corpus containing 95 tables and 118 synthetic header-drift injections, checkpoint-level analysis yields 96/118 visible injections; 0/13 OCR-like injections were visible across 11 table clusters. End-to-end, flat, and hierarchical protocols detect 112/118, 85/118, and 13/118 injections under different decision signals. In the current single-responsive-leaf instantiation, the flat and hierarchical contrastive scores are positive affine transformations and therefore induce identical rankings and ROC geometry. A clean-only matched-FPR operating point is not empirically identifiable because all 2,382 clean scores are zero; historical fixed-threshold equality is retained only as sensitivity evidence. This diagnosis shows that protocol comparisons without identifiable operating points can create misleading superiority stories: hierarchy decomposes evidence, while detection sensitivity and localization remain separate questions. Our results motivate evaluation reports that publish per-family visibility profiles, explicit construct definitions, validity boundaries, and reproducible evidence chains alongside aggregate scores.

## 1. Introduction

Document intelligence systems are increasingly implemented as pipelines rather than single predictors. A financial document may be decoded, segmented into tables, mapped to a canonical schema, checked for arithmetic consistency, indexed for retrieval, and finally queried by a language model. Each stage can fail independently, while later stages may compensate for or conceal an earlier error. Final-answer accuracy therefore cannot reveal whether the system followed a reliable path.

This creates a second problem that is easier to overlook: the evaluation protocol may itself be unable to observe particular defects. If a perturbed header is normalized back to the original field before the first measured checkpoint, every downstream score can remain unchanged. A correct final answer then has at least two explanations—the pipeline was robust to the perturbation, or the evaluation was blind to it. A single end-to-end score cannot separate these cases.

We study this problem through controlled fault injection. A frozen public tabular corpus contains 95 tables and 118 synthetic header perturbations across six families: alias variation, mixed language, unit suffix, date variation, OCR-like character substitution, and prefix noise. We separate three questions that aggregate scores usually collapse: whether a checkpoint observes a change, whether a protocol turns that observation into a detection decision, and whether the perturbation is harmful under a stated equivalence criterion. This separation exposes a strong family effect: 0/13 OCR-like injections were visible across 11 table clusters. The raw flat--hierarchical gap is instead traced to score and threshold structure; a clean-only matched-FPR operating point is not identifiable on the frozen clean scores.

We study evaluation-protocol validity rather than proposing a stronger detector. We ask the prior question: can the evaluation protocol observe the defect at all, and can it disclose the blind regions that make a result ambiguous? This reframes hierarchy as an evidence instrument rather than an automatic sensitivity gain, and leads to three contributions:

1. **Construct separation.** We distinguish checkpoint-level visibility, protocol-level detection, and equivalence-dependent harmfulness, which aggregate scores usually collapse into one outcome.
2. **Quantified observation boundaries.** We report per-family visibility rate, micro visibility, worst-family visibility, and visibility-conditioned protocol use, so aggregate accuracy cannot hide a family that the evaluator cannot observe.
3. **Structural protocol identifiability audit.** We show that the apparent hierarchical detection advantage in the current single-responsive-leaf setting is explained by score and threshold structure: flat and hierarchical scores are affine/rank-equivalent, while clean-only matched-FPR equality is not empirically identifiable.

This positioning keeps the empirical claim commensurate with the evidence. We do not claim universal coverage, superior hierarchical detection, a formal geometric “blind cone,” or significant downstream gains from the gated self-improvement case.

## 2. Related Work

### 2.1 Meta-evaluation

Machine-translation challenge sets such as ACES evaluate whether a metric can distinguish genuine errors from acceptable variants [Amrhein et al., 2022; Amrhein et al., 2023; Moghe et al., 2024]. Contextual metric meta-evaluation extends this view to local, context-dependent correctness [Deviyani and Diaz, 2025]. More recent studies show that rankings can change with protocol axes, prompt subsets, seeds, or the property a metric is intended to measure [Kendiukhov, 2026; Du et al., 2026; Ross et al., 2024]. We adopt the same meta-evaluation principle but focus on a prior question: whether a long-horizon protocol can observe an injected defect at all.

### 2.2 Process-level and hierarchical evaluation

Process-oriented benchmarks diagnose intermediate behavior in tool-using and web agents rather than scoring only final success [Fan et al., 2026; Chung et al., 2026]. GTA-2 represents a task as recursively aggregated checkpoints [Wang et al., 2026]. Our aggregation follows this structure, while adding deterministic contracts, explicit missing-evidence behavior, and controlled injections that expose the evaluator's sensitivity by defect family.

### 2.3 Mutation testing and fault injection

Mutation testing and metamorphic testing introduce controlled changes to measure whether a test or metric notices them [Cho et al., 2025]. AgentChaos applies programmatic fault injection to agent systems [Tan et al., 2026]. These traditions usually summarize each mutant as killed or surviving. We refine surviving or non-detected mutants by distinguishing silent absorption, unobservability at the scored layer, and equivalence-dependent interpretation, then report those mechanisms by defect family. We distinguish evaluator blindness from mutants whose intended effect is not represented on the scored observation surface. We reserve the term invalid mutant for cases that fail a separate validity audit.

### 2.4 Reliability of semantic judges

LLM judges are useful for open-semantic qualities but exhibit position, verbosity, self-preference, and perturbation sensitivity [Zheng et al., 2023; Li et al., 2025a; Li et al., 2025b]. We therefore reserve deterministic checks for contractible properties, use a judge only for semantic dimensions, hide injected ground truth from the judge prompt, and report the judge's resolution and sample limits explicitly. The distinction from prior process-level work is deliberate: those methods diagnose system behavior, whereas this paper first audits whether the evaluator can observe a controlled defect before interpreting that behavior.

## 3. Method

The conceptual core is a three-way audit of visibility, detection, and harmfulness; the hierarchical checkpoint forest is the evidence instrument that makes the audit reproducible.

### 3.1 Evidence instrument: checkpoint forest

We model the pipeline as two checkpoint trees. The parsing tree covers document ingestion, table structure, field mapping, and arithmetic reconciliation. The QA tree covers retrieval grounding, faithfulness, numeric correctness, citation quality, and appropriate refusal. Together the trees contain 12 scored leaves.

The twelve scored nodes are five in the parsing tree (document status, document throughput, table regression, field hit-rate, reconciliation equations) and seven in the QA tree (retrieval contract, faithfulness judge, numeric contract, number grounding, citation judge, refusal judge, refusal contract), per config/eval_checkpoint_trees.json v0.1.0. The visibility audit exercises the parsing-tree leaves whose evidence is the mapping and regression artifacts; under the frozen drop rule (drop = (H_orig - H_inj) x 10, threshold 2.0) only the field hit-rate leaf responds to header drift, while QA-tree leaves keep their frozen evidence and the QA arm is reported separately (12 calls at the same endpoint). This is precisely why additional localization value remains unestablished in the current instantiation. In Table 1, the label 'Pruned parsing-root drop' denotes exactly this operation: the parsing root is collapsed to its single input-responsive leaf (the field hit-rate leaf) and the drop rule above is applied there.

![Figure 1. Two checkpoint trees used by the evaluation protocol.](../docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg)

Each leaf receives a score in [0,10]. Contractible properties use deterministic checks; semantic properties use a 0–5 judge score mapped to [0,10]. Sibling weights are normalized locally before bottom-up aggregation. Missing evidence is explicit: the parsing tree assigns 0, whereas the QA tree assigns a neutral 5. Hinge leaves affect the stability verdict, not the missing-evidence score. Every leaf stores its evidence and degradation reason.

For node n with children C(n), the recursive score is

\[
S(n)=\sum_{c\in C(n)} \frac{w(c)}{\sum_{j\in C(n)}w(j)}S(c).
\]

For a leaf, S(n) is the mapped contract or judge score. A tree is stable only when at least 90% of its leaves exceed the selected threshold and every hinge leaf scores at least 7. The implementation is deterministic once the evidence artifacts are fixed.

### 3.2 Separating visibility, detection, and harmfulness

Visibility is defined relative to the selected checkpoint evidence surface, whereas protocol detection may use a different downstream signal.

The primary conceptual structure is the following visibility-by-detection matrix:

| Checkpoint evidence | Protocol detects | Protocol does not detect |
|---|---|---|
| Visible | Detected visible defect | Visible but undetected |
| Not visible | Detection through a different signal or predicate | Silently absorbed or unobservable |

Harmfulness is orthogonal to this matrix and is annotated separately as harmful, equivalent, or unresolved under the selected equivalence criterion.

For an injected defect d, visibility and protocol detection are separate observations:

- **Detected:** the selected protocol satisfies its detection predicate, which may test a mapping change or a score threshold.
- **Visible but not detected:** the checkpoint exposes a difference, but the selected protocol does not satisfy its detection predicate.
- **Silently absorbed:** normalization or matching preserves the canonical correspondence, so that checkpoint does not expose the perturbation.

Harmfulness is a separate, **equivalence-dependent** judgment, not a mutually exclusive visibility outcome: canonical-form preservation and reader-referent recoverability need not agree.

The defect visibility profile reports visibility separately for each family. This preserves information lost by a single mutation score and distinguishes a missing checkpoint from a genuinely robust stage.

### 3.3 Evaluating the evaluator

We compare four protocols on frozen evidence: end-to-end roots, a flat leaf average, hierarchical expert weights, and hierarchical searched weights. We measure table-level detection, injection-level detection, mean separation between clean and perturbed states, worst-family behavior, localization, and evaluation cost. Because raw thresholds can manufacture differences, we separately audit (i) structural score/ranking equivalence and (ii) whether a matched-FPR operating point is identifiable from clean scores alone.

The audit further varies the injection seed, visibility threshold, matching algorithm, and scoring normalization. A semantic-judge arm is evaluated separately and never substituted for deterministic evidence when a contract exists.

## 4. Experimental Setup

### 4.1 Corpus and perturbations

The study uses a frozen public tabular base and contains no client data. It includes 95 tables and 118 synthetic injections across six header-drift families. Schema and header matching are the perturbation carrier in this instantiation; the object of study is the evaluation protocol's observation boundary. Each injected record preserves its source table, family, seed, changed field, and expected observation surface.

Concretely, the base is the frozen drift-v0 table set derived from public TAT-QA tables (data/research/drift_v0/input/tatqa_tables.json, sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302); the corpus was frozen before this study's data gates and no new TAT-QA use is introduced. The perturbations are the fully synthetic injection map (data/research/drift_v0/output/injection_map.json, sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e; deterministic, seed 42, ratio 0.3). The primary matcher is the production greedy header matcher (scripts/m1_statement_parser.py, map_headers); the cross-matcher audit adds greedy-normalized, hungarian-production, and hungarian-normalized configurations. Semantic leaves are scored by the M2 judge pipeline (source tag m2_judge in config/eval_checkpoint_trees.json), i.e. Qwen3.6-35B-A3B (Q4_K_M GGUF) served at 127.0.0.1:8004, with 0-5 dimension scores mapped to [0,10]. The primary threshold grid is

\[
\Gamma=\{0.2,0.3,0.5,0.7,0.9\}.
\]

The OCR-like family contains 13 single-token, lowercase Levenshtein-distance-one substitutions with unchanged column values. These properties are mechanically recomputed before interpretation.

### 4.2 Baselines and controls

The protocol baselines are end-to-end scoring, flat leaf scoring, and hierarchical scoring with expert weights. Weight-search controls include equal weights, expert weights, 30 random trials, greedy coordinate ascent, particle-swarm optimization (PSO), and a minimax objective. Assignment controls compare greedy matching with Hungarian global assignment and include a positive solver test.

### 4.3 Statistical discipline

We freeze inputs and decision criteria before reading each result. Confidence intervals are reported on table-level clustered units where available (percentile bootstrap over the 95 table units, seed 20260830; endpoints on the k/95 grid for the 95-table arm). Seed sensitivity uses three injection seeds. For the clean-only matched-FPR audit, threshold selection may use clean scores only; injected and harmful outcomes are prohibited from calibration. Because the frozen clean supports are degenerate, non-identifiability is reported rather than forced into an empirical equality. The 2,382 clean records are the usable (table_uid, column) rows of the non-injected source tables in the frozen D3 inputs, with fold assignment = sorted(table UID) index modulo 5. Null and adverse findings are retained rather than relabeled as improvements.

## 5. Results

### 5.1 Visibility is strongly defect-type dependent

Checkpoint-level analysis makes 96/118 injections visible, but the aggregate hides a large family effect. 0/13 OCR-like injections were visible across 11 table clusters under all five thresholds; all 13 were invisible under this observation criterion. Other families range from 0.81 to 1.00 visibility at the primary setting. For uncertainty, the injection-level reference estimand is 0/13 with an exact binomial 95% interval of [0, 24.71%] under an independent-injection assumption; the distinct table-level event estimand is 0/11 with an exact binomial interval of [0, 28.49%]. The latter is not a clustered confidence interval for injection-level visibility.

![Figure 2. Defect visibility varies strongly across perturbation families.](../docs/experiments/figures_paper/fig_visibility_spectrum.png)

The family unobserved on the frozen scored surface remains the same under four edit-distance matcher configurations. However, the ordering of visible families is not invariant: changing the score normalization causes five class flips, all within the date-variation family, whereas switching from greedy to global assignment causes no flips. Thus, the existence of a family unobserved on the frozen scored surface is stable within the tested matcher family, but the full ranking is protocol-dependent.

The harmfulness label is also criterion-dependent. An instance-level oracle rejects all seven members previously placed in a type-level equivalence class. Across eight paired comparisons, five disagree, and the disagreements align with criterion kind—canonical-form preservation versus reader-referent recoverability—rather than appearing as random case-level noise. We therefore report that this family is unobserved on the frozen scored surface, while treating whether that absence is harmful as a boundary question.

### 5.2 The raw hierarchy gap is a threshold-placement artifact

The raw detection counts are not evidence of protocol discriminability. Table 1 compares three transferable protocols under different decision predicates: end-to-end detection tests whether the final mapping text changes, whereas flat and hierarchical scoring use frozen score-drop thresholds. A changed source-header string can therefore count as end-to-end detection even when the canonical match is preserved, explaining why 112/118 exceeds the 96/118 visibility count. Table-level counts apply all assigned injections together, whereas injection-level counts apply one perturbation at a time; the 20 detected tables and 13 individually detected injections are not nested counts. At the frozen threshold, hierarchical scoring is not a more sensitive detector.

| Protocol | Detection signal | Tables detected | Injections detected |
|---|---|---:|---:|
| End-to-end | Final mapping change | 95/95 (1.0000) | 112/118 (0.9492) |
| Flat | Field-hit-rate drop | 75/95 (0.7895; 95% CI [0.6947, 0.8737]) | 85/118 (0.7203) |
| Hierarchical, expert weights | Pruned parsing-root drop | 20/95 (0.2105; 95% CI [0.1263, 0.2947]) | 13/118 (0.1102) |

The raw flat--hierarchical gap does not establish inferior ranking quality. In the current single-responsive-leaf construction, the hierarchical contrastive score is a positive affine transform of the flat contrastive score with slope approximately 0.375. The scores therefore induce identical rankings and, by implication, identical ROC/AUROC geometry; corresponding thresholds satisfy theta_H = 0.375 theta_F. This is a structural result, not an empirical matched-FPR equality. The derived clean-only reanalysis contains 2,382 usable clean records with both score supports exactly {0}; every positive threshold has observed FPR zero, so the clean set cannot identify a unique operating threshold. Selecting a threshold by harmful TPR would violate the clean-only contract. Historical fixed-threshold sensitivity evidence is retained in Appendix A.4, but the old [0,0] interval is not a clean-calibrated confirmatory result. When more than one leaf varies with the input, neither affine nor ranking equivalence is guaranteed.

The 118 injections close at the checkpoint level as 96 visible plus 22 silently absorbed; by family (injections / visible / absorbed): alias variant 47/43/4, date variant 17/15/2, mixed language 20/20/0, OCR-like 13/0/13, prefix noise 16/13/3, unit suffix 5/5/0 (frozen artifact t2_visibility_sensitivity.json; path in the evidence ledger). The protocol-level counts in Table 1 are measured on different signals and are therefore not a partition of the 96.

We label the affine-equivalence observation a degenerate-case result: it fixes the interpretation of the raw gap under the current single-varying-leaf instantiation and does not establish affine equivalence of the protocols in general.

### 5.3 Sensitivity and reproducibility

The identity of the family unobserved on the frozen scored surface is stable across the threshold grid. Absolute between-family range contracts at high thresholds, as expected when one changed header contributes at most 1/n for a table with n canonical headers. The literal preregistered range criterion fails at 0.7 and 0.9 and is reported as failed.

Across three injection seeds, flat table-detection rates are 75/95 = 0.7895, 76/97 = 0.7835, and 68/90 = 0.7556. Their spread is 0.0339; the denominator-weighted pooled rate is 219/282 = 0.7766 with a percentile bootstrap 95% interval of [0.7270, 0.8227] over the pooled 282 table units (seed 20260830; endpoints on the k/282 grid). The seed-42 run reproduces the frozen artifact byte-for-byte.

Judge calibration covers 120 leaf-state cells; this calibration window is distinct from the 28-case semantic boundary analysis reported in Section 6. In the control-state comparison, rejudged summaries of historical 0–5 judgments differ from the frozen dimension means by at most 0.5, meeting the preregistered consistency expectation. This checks reproduction of aggregate dimension scores, not agreement between judges re-evaluating the same original answers. On the derived 0–10 root scale, control roots differ by at most 0.22, while individual leaves can move by as much as 7.0. Agreement is therefore an aggregate observation, not evidence of cell-level interchangeability.

### 5.4 Weight search produces an informative null

PSO and greedy coordinate ascent reach the same mean separation of 1.432574. PSO repeats the result on all five seeds but requires 7,650 evaluations, compared with 67 for greedy search. A minimax variant improves worst-case separation to 0.35714 while reducing mean separation to 1.25605. We therefore do not claim PSO superiority. The result instead shows that objective choice matters more than optimizer sophistication in the present search space.

### 5.5 Boundary case outside the main contribution

This boundary case is not part of the evaluation-track contribution; it only marks where Stage E evidence stops and the broader Stage R question begins.

In a compact feedback example, a gain–collateral gate rejects all 7 adversarial high-confidence mappings and all 5 expanded-collision candidates. Across 15 collision tables, the gated-minus-ungated mean paired difference is 0.05 with a 95% interval of [0, 0.1056], while the exploratory pooled comparison is 7/40 versus 4/40 with exact McNemar p=0.375. This is not an efficacy claim.


## 6. Discussion and Limitations

### 6.1 Scientific limitations

The main finding is methodological. Aggregate evaluation can hide both system defects and defects unobserved on the scored surface. A checkpoint forest makes evidence decomposable, while a visibility profile shows which defect families are observable. Yet structure alone does not guarantee sensitivity: in the current single-responsive-leaf construction, flat and hierarchical scores are affine/rank-equivalent, while a clean-only empirical matched-FPR operating point is not identifiable.

Four limitations bound the claim. First, the evidence comes from one public tabular corpus with synthetic perturbations; no cross-domain generalization is claimed. Second, the OCR-like family is unobserved on the frozen scored surface, but whether each perturbation is harmful depends on the equivalence definition. Third, the semantic boundary analysis uses one judge on 28 cases; mixed-language and unit-suffix families receive no calls in that window (a separate window from the 120-cell judge calibration of Section 5.3). Fourth, under shared-header overlays the oracle correctness ceiling changes from 20/21 = 0.952381 to 40/67 = 0.597015 (the two figures use different denominators; this is not a ratio comparison), while global assignment changes no decision, locating the problem in score construction rather than allocation.

### 6.2 Deferred independent evidence

A preregistered second-dataflow extension did not satisfy its structural prerequisites and is therefore not used as evidence. A preregistered independent-scorer route triggered its pre-registered stop condition and is therefore not reported as a capability result. The criterion-relativity claim remains limited to the current evaluator and corpus; the detailed governance record is retained in Appendix A.




## 7. Conclusion

Final correctness cannot tell whether a defect was observed at an intermediate checkpoint, silently absorbed, or invisible to the evaluator itself. We introduced a three-way audit of visibility, detection, and harmfulness, implemented with hierarchical checkpoint evidence and per-family visibility profiles. On 118 controlled injections, observability and detection depend strongly on defect family and decision protocol. The central result is structural rather than a detector ranking: flat and hierarchical scores are affine/rank-equivalent in the single-responsive-leaf setting, while clean-only matched-FPR equality is not identifiable. Long-horizon evaluations should therefore report the protocol's own observation boundary, validity limits, and reproducible evidence chain alongside aggregate system performance.

## References

- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics. arXiv:2210.15615, 2022.
- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets at WMT 2023. arXiv:2311.01153, 2023.
- Chung, J., Byun, J., Vineet, V., and Kim, S. J. Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking. arXiv:2606.15673, 2026.
- Cho, S., Ruberto, S., and Terragni, V. Metamorphic Testing of Large Language Models for Natural Language Processing. arXiv:2511.02108, 2025.
- Deviyani, A., and Diaz, F. Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy. arXiv:2503.19828, 2025.
- Du, S., Liang, P., Shen, Y., et al. On the Stability of Prompt Ranking in Large Language Model Evaluation. arXiv:2606.24381, 2026.
- Fan, S., Ye, X., Huo, Y., et al. AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents. arXiv:2603.14465, 2026.
- Kendiukhov, I. Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking. arXiv:2603.03493, 2026.
- Li, Q., Dou, S., Shao, K., Chen, C., and Hu, H. Evaluating Scoring Bias in LLM-as-a-Judge. arXiv:2506.22316, 2025.
- Li, S., Xu, C., Wang, J., et al. LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge. arXiv:2506.09443, 2025.
- Moghe, N., Fazla, A., Amrhein, C., et al. Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets. arXiv:2401.16313, 2024.
- Ross, C., Hall, M., Romero Soriano, A., and Williams, A. What Makes a Good Metric? Evaluating Automatic Metrics for Text-to-Image Consistency. arXiv:2412.13989, 2024.
- Tan, G., Sun, Z., Shi, J., et al. AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection. arXiv:2608.06790, 2026.
- Wang, J., et al. GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows. arXiv:2604.15715, 2026.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv:2306.05685, 2023.

## Appendix A. Deferred independent-evidence record

This appendix preserves the internal evidence and preregistration record for deferred extensions. These materials are boundary records, not Stage E results.

### A.1 Reinstatement criteria

Reinstatement criteria, not a timeline: the deferred arms return only when (i) a second dataflow with a table layer passes SOURCE_GO and SPLIT_GO with UID-disjoint layers, and (ii) a second scorer independent of the :8004 judge reproduces the leaf-state cells; until both hold, the arms remain preregistered-but-unreported.

### A.2 Second-dataflow record

Progress against criterion (i) is now measurable, clause by clause. Three corpora answer different clauses and are named separately: the acquisition corpus (FinQA, taken under the approved minimal scope), the action corpus (a schema-matching benchmark of ten table pairs), and the transfer corpus whose missing table layer triggered the original deferral. SOURCE_GO passed on 2026-09-25 for the acquisition corpus, with per-file digests recorded. Its table layer is present and uniform: all 7134 examples carry a non-empty rectangular table whose first row is entirely string-valued, with two to eleven columns, so the clause that deferred the transfer corpus, the absence of a table layer, does not apply to the acquisition corpus. A deterministic, label-blind split instrument now assigns layers whose independence clusters are report-level rather than dataset-level, and on the acquisition corpus the four role layers are geometrically fillable, with 2409 lineage UIDs over 768 report clusters at full population. SPLIT_GO is nonetheless not passed: the acquisition corpus has its own gate and sealed partitions withheld because its registered role list does not include them, while the action corpus, which is the one that carries an action vocabulary, contains ten table-pair clusters and under the frozen hash-threshold bucketing rule leaves the development layer empty, yielding ten independent units. The remaining gap is structural rather than incremental, and it belongs to the label gate rather than to criterion (i): the acquisition corpus publishes no official canonical vocabulary for table columns, so action labels could only be constructed by inventing a schema. Here, a table layer makes samples definable; it does not supply the gold those samples need.

### A.3 Independent-scorer record

Criterion (ii) has not been tested, and one candidate route toward it was stopped by its own pre-registration. A model-free detector, independent of the :8004 judge, was built over a corpus of 1970 frozen step-level records whose contents and fault families were fixed before any detector existed, and whose percent-convention stop threshold was pre-registered before the second detector run produced any output. Its pre-registration fixed a fidelity threshold in advance, and that threshold was not reached: fidelity of the reconstructed step semantics on percent-form results was 0.0298 under one percent convention and 0.2233 under the other (44 and 330 matches out of 1478 percent-form steps, respectively), both below the pre-set 0.5, so the route was stopped rather than re-parameterized. Because that detector measures reasoning-step checkpoints while criterion (ii) concerns reproduction of the frozen header-injection leaf-state cells, the two are different measurement objects; the leaf-state reproduction clause therefore remains untested rather than failed, and what the fired stop condition establishes is the boundary of the step-level route itself. The portion of that corpus with faithful reconstruction covers 322 records of 1970 under the convention yielding 0.0298, and 467 under the one yielding 0.2233, i.e. 16.3% to 23.7%, and is reported to bound the route, not as a capability.

### A.4 Historical matched-FPR sensitivity

The older D3 analysis reported 90/111 for both flat and hierarchical protocols and a zero-difference bootstrap interval under a historical fixed-threshold sensitivity setup. Those numbers remain archived evidence for that setup only. The newer clean-only cross-fitted audit found zero-valued clean score supports and therefore could not identify a unique FPR-constrained threshold. Accordingly, the historical equality is not promoted to a clean-calibrated confirmatory claim and is not used to rank the protocols.

--- BEGIN Version-B revision proposal ---
# Paper E Version-B Revision Proposal v1

> Status: `PROPOSAL_ONLY_PAPER_BODY_UNCHANGED` | Evidence: Stage E quantification + multi-leaf v1 + Loop C audit + signature ablation

## 1. Proposed title

**Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation**

## 2. Three contributions

1. **Construct separation and observation boundaries.** Separate visibility, detection, and harmfulness as distinct evaluation constructs, and quantify family-level observation boundaries.
2. **Protocol identifiability.** Show that single-responsive-leaf hierarchy scores collapse to an affine/rank-equivalent measurement, while clean-only matched operating points are not identifiable under zero-support clean scores.
3. **Stage-aligned instrumentation (contract-derived signature).** Using preregistered mapping/retrieval/numeric perturbations, show that explicit stage-aligned checkpoints carry the separable stage signature in a contract-derived construction; the exploratory ablation shows the boundary - when directly targeted checkpoints are removed, LOCO macro-F1 falls to the three-class chance level (0.3333). This is not a claim of controlled localization or of hierarchy-based localisation.

Scientific implication: **In our construction, structured evaluation supports diagnosis only when its observation surface is aligned with the failure stages; hierarchical organisation alone does not guarantee diagnosability.**Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation**

The third contribution must not be shortened to “hierarchy localizes failures.”

## 3. Abstract candidate

Long-horizon AI systems are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. We introduce an evaluation-protocol audit that separates these constructs and reports observation boundaries rather than only aggregate accuracy. On a frozen public tabular corpus of 95 tables and 118 controlled injections, 96 injections are checkpoint-visible, while 0/13 OCR-like injections are visible across 11 table clusters. Protocol counts use different detection signals and therefore do not form a single partition of visibility. In the current single-responsive-leaf construction, flat and hierarchical scores are positive affine transformations with identical rankings and ROC geometry; a clean-only matched-FPR operating point is not empirically identifiable because all clean scores are zero. Preregistered mapping, retrieval, and numeric perturbations induce perfectly separable stage-aligned signatures on an explicitly instrumented observation surface (the features are contract-derived and separable by construction; the full vector equals the direct three-leaf codebook at macro-F1 1.0). When directly targeted checkpoints are removed, LOCO macro-F1 falls to the three-class chance level (0.3333), showing that the result reflects stage-aligned instrumentation rather than emergent localisation from the remaining hierarchy. In our construction, structured evaluation supports diagnosis only when its observation surface is aligned with failure stages; hierarchical organisation alone does not guarantee it.

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

--- BEGIN paper/submission_review_risk_register_v1.md ---
# 小论文投稿前 reviewer 风险登记 v1

> 状态：内部审稿风险登记，不是投稿许可 | 更新：2026-10-04
> 来源：双模型审稿原件、步级链路审计、投稿包审计、Office 视觉验收
> 判定口径：blocking = 阻止投稿；should-fix = 投稿前应处理；controlled = 已有正文边界；pending-external = 等用户/venue/专利外部确认

## 1 风险表

| id | 风险 | 严重度 | 当前证据 | 状态/处置 |
|---|---|---|---|---|
| RR-01 | matched-FPR `[0,0]` 区间看起来退化，审稿人可能质疑 | should-fix | §5.2 已补 single-varying-leaf 仿射分数推导，明确 `[0,0]` 是退化支持集而非一般等价定理 | **closed**；主稿已补推导，数字/结论不变 |
| RR-02 | 112 > 96 的首读悖论 | should-fix | Abstract 与 §5.2 已明确 checkpoint visibility 与 protocol detection 是不同信号，不是 96 的分区 | **closed**；保留显式解释 |
| RR-03 | 单一公开表格语料、单 varying leaf 的外部效度 | major limitation | §5.2/§6 明确不主张普适性；第二数据流仍 pending | **controlled/open**；必须保留在 Limitations |
| RR-04 | step-level scorer 的低保真度被误读为检测能力 | should-fix | SP-C5 = `attempted_stopped_by_preregistration`；0.0298/0.2233 停止条件触发；detection/localization 禁止作为能力结论 | **closed**；V2-3 已关闭，不开 v3 |
| RR-05 | 匿名预览中的 artifact 路径/模型身份脱敏后，复现细节不够 | should-fix | `submission_draft_arr_www_anonymous_v0.md` 禁词 0；`reproducibility_statement` 列出可公开候选与不外发边界 | **pending-external**；venue 版需补匿名补充材料编号 |
| RR-06 | venue 模板、作者/单位、匿名、专利门未完成 | blocking-submission | `submission_package_audit` 明确 `PENDING_EXTERNAL_ITEMS` | **open**；不得投稿/上传/公开 |
| RR-07 | Related Work 部分 venue 标签未全部核验 | should-fix | `references_v0` 坚持未核 venue 写 `arXiv preprint`；15 条主稿引用集合已机械闭合 | **controlled/open**；venue 官方核验后才能改 |
| RR-08 | 图表在打印尺寸下的可读性 | should-fix | 叙事修订版 DOCX 已重建，GB10 PDF 8 页，抽样 1/4/5/8 页 PASS；Figure 2 与 Table 1 完整 | **closed for internal review**；camera-ready 仍需 venue 版式复验 |
| RR-09 | round5 N-1/N-2 簿记/证据锚点 | minor | N-1 `audit_status=round5` 已更新；N-2 已补 FinQA process structure evidence，claims 74/74 | **closed** |
| RR-10 | Loop B `adv_cross_doc` 间歇 source retrieval 缺失 | operational | `5f82efb` 自然周期 `sources empty`，上一周期同题 PASS | **tracked**；不阻塞论文文本，不隐藏、不重置 |
| RR-11 | 标题/摘要未把反直觉结论放在首屏 | should-fix | 已改为 `Visibility Is Not Detection`，摘要、Introduction、结果标题与 Conclusion 同步 | **closed**；写作层修复，不改数字或 claim |
| RR-12 | 第二数据流、独立 scorer 与多 leaf localization 证据不足 | major limitation | 当前仍为 deferred/unestablished；计划见 `teacher_review_readiness_v2.md` | **open**；只允许 future work，不升级当前主张 |
| RR-13 | 社会价值场景过于单一 | should-fix | 当前只保留金融文档动机；通用场景列入 readiness backlog | **pending**；后续可在不改变技术结论的前提下扩展场景 |

## 2 首要投稿前动作

1. 取得 venue 官方模板/CFP，确定页数、匿名、References 和 supplementary policy。
2. 在不改变 claim/evidence 的前提下生成 venue 版 PDF，补齐作者/单位并复验图表打印尺寸。
3. 专利确认后再决定任何外发、arXiv 或代码公开。
4. 146 列 Q3 已完成 R1/R2/ADJ 并封存 raw/ledger/hash，但带 visibility exceptions；它只作为 exploratory learnability evidence，不进入 Stage E 保底稿结果，也不得升级为 Stage D/RQ2。

## 3 当前判定

没有发现新的 manuscript blocking issue；当前 blocking 全部是外部投稿条件，不能用内部 mechanical audit 绿灯替代。
| RR-14 | 仍被误读为 hierarchical evaluator 方法论文 | should-fix | 标题、Abstract、贡献和 Method 均明确 measurement validity；hierarchy 明示为 instrument | **closed**；身份已收敛 |
| RR-15 | 被误读为 schema-matching robustness 论文 | should-fix | §4.1 明示 schema/header matching 是 perturbation carrier，研究对象是 observation boundary | **closed for positioning**；跨 pipeline 泛化仍是 evidence ceiling |
| RR-16 | visibility / detection / harmfulness 概念混淆 | should-fix | §3.2 增加 visibility × detection 矩阵，harmfulness 明确为 orthogonal annotation | **closed** |
| RR-17 | single responsive leaf 被掩盖 | major limitation | Abstract、§3.1、§5.2、§6.1 和 Conclusion 均明示 localization 未建立 | **controlled/open**；等待导师决策后续证据优先级 |
| RR-18 | null result 被解释为方法失败 | should-fix | §5.2 明示 threshold confounding diagnostic；PSO 明示 informative null；Stage R 明示 boundary case | **closed** |

--- BEGIN paper/submission_language_audit_v1.md ---
# 小论文投稿前语言与术语审计 v1

> 状态：内部静态审计，不替代 venue 格式审查 | 更新：2026-10-04
> 对象：`paper/teacher_review_draft_v1.md` 与 `paper/submission_draft_arr_www_anonymous_v0.md`
> 依据：`paper-polish-and-audit` 检查单；零模型、零外部调用

## 1 术语一致性

| 术语 | 统一口径 | 结果 |
|---|---|---|
| checkpoint-level visibility | 协议是否在中间检查点观测到缺陷 | 一致 |
| protocol-level detection | 聚合分数/映射文本是否越过检测阈值 | 一致 |
| silent absorption | 检查点证据保持而缺陷未被观测到的第三类结果 | 一致 |
| matched-FPR / affinely equivalent | 匹配假阳率后的退化等价观察 | 一致 |
| single-varying-leaf | `[0,0]` 支持集的构造条件 | 一致 |

未发现同义词漂移；Related Work 四簇与主稿方法/结果术语一致。

## 2 强主张与 AI 风格扫描

- `state-of-the-art`、`delve into`、`it is important to note that`、`in conclusion` 命中 0。
- `superior`、`significant`、`robust` 等命中项均位于“not claim / does not establish / not a general”等否定、边界或测量语境，不构成无依据强主张。
- 主稿不使用训练完成、Stage D 闭合、DATA_GO 等结果性措辞；Q3 输入包与未完成项显式保留为边界。

## 3 版本同步

- 主稿、匿名预览、DOCX、claim manifest、acceptance report 由投稿包审计统一检查。
- 匿名预览保留全部 claim tokens；内部路径、hash、模型/端点身份按 redaction map 脱敏。
- 结论段与 Abstract 均强调“decomposition, not better detection sensitivity”，未出现主张漂移。

## 4 结果

未发现 blocking language issue；本次不改主稿。剩余工作属于 venue 官方格式、作者/匿名、专利和 camera-ready 外部项。

## 5. 2026-10-07 narrative revision audit

- Title and abstract now foreground `Visibility Is Not Detection`; the abstract uses the same claim tokens and measured values as the body.
- Introduction contributions now follow the order: three-way distinction, hierarchical evidence instrument, controlled protocol audit.
- Section 5.2 leads with the threshold-artifact interpretation; Section 6 separates scientific limitations from deferred independent evidence.
- No new strong-claim language was introduced. Future dataflow/scorer/localization work is explicitly deferred and does not change current claim status.

## 6. 2026-10-07 identity-convergence review

- The manuscript now states `We study evaluation-protocol validity rather than proposing a stronger detector` in both Abstract and Introduction.
- Contributions are ordered as construct separation, evidence instrument, and protocol audit; hierarchy is explicitly not an algorithmic novelty.
- The mutation-testing comparison now refines surviving/non-detected mutants instead of claiming a universally new third outcome.
- Section 5.5 is a boundary case, Section 6.2 is concise, and detailed deferred-evidence governance is preserved in Appendix A.
- No experiment number, claim token, preregistered stopping rule, or harmfulness definition was changed.

--- END PACKET ---
