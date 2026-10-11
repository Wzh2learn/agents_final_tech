# GEMINI_REVIEW_TRIAGE_v1.md

> date: 2026-10-11 | status: READ-ONLY DECISION RECORD | Gemini A/B reviews = EXTERNAL_REVIEW_INPUT, NOT scientific authority
> Evidence base (disclosed): the two Gemini review texts are NOT present in the repository workspace (only the input packs `../gemini_notebook_export_20261011/PACK_A_BLIND_REVIEW`, `PACK_B_META_REVIEW` exist). This triage classifies the points as summarized by the owner (A-K) and the quoted Gemini-B claims, each checked against canonical repo artifacts. No new claim is adopted from the reviews; no experiment is started/stopped on their advice.
> Labels: SUPPORTED / USEFUL_HYPOTHESIS / OVERSTATED / CONTRADICTED_BY_CURRENT_EVIDENCE / OUT_OF_SCOPE_FOR_SANER

## Triage table (A-K)

| Point | Classification | Basis (canonical) |
|---|---|---|
| A. Paper E = SANER RENE Weak Accept / 6/10, route fit strong, rigor strong, repro strong | SUPPORTED (as external reviewer assessment; adopted as route-sufficiency input) | Consistent with our own readiness record (`paper/teacher_review_readiness_v2.md`) and the frozen claim set; it is a venue-fit value judgment, not a repo-verifiable fact |
| B. Strongest reject = bespoke-system autopsy / weak external validity | SUPPORTED | Matches the canonical #1 limitation: one frozen public corpus, synthetic perturbations, no natural-failure distribution (scope lock Limitations; reviewer-audit F6/F10 items) |
| C. No automatic selector required | SUPPORTED | Matches the standing decision: a positive causal-aware selector is not a Route A prerequisite; evidence ladder has no LEVEL_4/5 claim; selector = future work only |
| D. No new experiment required for submission | SUPPORTED | ROUTE_A_SCIENTIFIC_SUFFICIENCY = YES (owner-confirmed); Track P = upside option |
| E. Multi-leaf direct-instrumentation interpretation | SUPPORTED (construction-bounded) | Canonical boundary: "in the contract-derived construction, stage-aligned instrumentation carries the separable signature; non-direct leaves do not establish emergent localisation" (matrix C2, ablation 1.0/1.0/0.3333) |
| F. Observability Horizons abstraction | USEFUL_HYPOTHESIS (CANDIDATE_FRAMING) | Organizes existing FACTs (see OBSERVABILITY_HORIZON_NOTE_v1.md); no horizon metric/distance/law is validated anywhere in the repo |
| G. Silent Absorption | SUPPORTED (definitional core) / OVERSTATED (as "silent system failure") | Supported: normalization preserves the canonical mapping so the mutation is unobserved at the frozen surface (22/118 blind; OCR 0/13 across 11 clusters at all gamma). Not supported: any claim that downstream system behaviour is silently wrong — the frozen cells show end-to-end detected 22/22 blind cases |
| H. FinQA downstream re-execution ("just rerun the arithmetic interpreter") | OVERSTATED; disposition = NEW_MEASUREMENT_CONTRACT_REQUIRED (post-SANER) | See fact-check (3): the causal-exposure qualification found D undefined (grammar/serialization/terminal semantics), official executor not staged, and V2-3 closed; this is not an engineering-only fix |
| I. PR-02 placement-distance decay | USEFUL_HYPOTHESIS; verdict NOT_CURRENTLY_IDENTIFIED | See PR-02_feasibility_factcheck_v1.md: no authoritative checkpoint-to-stage distance, no propagation-edge records, no meaningful non-direct variation on current carriers |
| J. Governance autoimmunity | SUPPORTED (as process feedback) | Adopted: governance narrows to scientific-invalidity prevention / reproducibility / claim boundary; passed governance is not reopened; no blocking on format nits or repeated multi-layer audits |
| K. Should Track P stop? | SUPPORTED (re-scoped, not stopped) | Owner decision adopted: Track P = UPSIDE_OPTION with MAXIMUM_PARALLEL_SCIENTIFIC_RECOVERY = 1, priority PR-03 v3 > PR-01 v3 > PR-04-R > PR-07 v3 (PR-07 deferred until manuscript body = SUBMISSION_DRAFT_COMPLETE) |

## Fact-checks (owner-ordered)

### (1) "end-to-end evaluation fails to detect 20%+ faults" -> OVERSTATED
Frozen cells (`docs/research/stage_e_118_quantification_v1.md` §4): E2E detection 112/118; checkpoint-visible 96/118; checkpoint-blind 22/118; E2E cells VD 90 / VU 6 / BD 22 / BU 0 -> **E2E detects all 22 checkpoint-blind cases**; E2E's own miss is VU = 6/118 (~5.1%). The 22/118 (18.6%) figure is *checkpoint observation blindness*, not end-to-end detection failure. Writing "end-to-end fails to detect 20%+" would be CONTRADICTED by the frozen cells; mark OVERSTATED and use the checkpoint-blind phrasing only.

### (2) "hierarchy / non-direct observation is strictly non-diagnostic" -> OVERSTATED
Permitted boundary (frozen): in the current explicitly instrumented construction, non-direct leaves do not establish emergent localisation (non-direct-only LOCO macro-F1 0.3333 = three-class chance / uniform-class baseline; any-response scalar 0.0). No universal theorem; no statement about hierarchy in other systems.

### (3) FinQA "just rerun the arithmetic interpreter" -> NEW_MEASUREMENT_CONTRACT_REQUIRED (post-SANER)
Checked against the causal-exposure qualification (`docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`, MVP audit): (i) operator semantics: legal P/N grammar unfrozen (U-A); (ii) rounding/serialization: exact serialization/equality unfrozen (U-B); (iii) percentage semantics: two percent readings remain STOPPED_BY_PRE_REGISTERED_V2_3 (0.0298 / 0.2233 fidelity); (iv) terminal semantics: terminal-answer derivation unfrozen (U-C) and `res`/`answer` referents change under re-execution; (v) official executor availability: official FinQA execution code not staged (train/dev JSON only). Conclusion: an interpreter re-run is not an engineering fix; it requires a new measurement contract + executor provenance + an unfreeze decision. Keep as post-SANER future work; do NOT unfreeze.

### (4) PR-02 "distance decay" -> NOT_CURRENTLY_IDENTIFIED (see PR-02_feasibility_factcheck_v1.md)

## Adopted / rejected (summary)
Adopted: A-E (as assessment/boundary), J (governance downgrade), K (Track P re-scope); G's definitional core may appear in Discussion as `observation-surface absorption`; F as candidate framing only.
Rejected/overstated: Gemini-B's "20%+ E2E miss" (contradicted), "strictly non-diagnostic hierarchy" (overstated), "FinQA interpreter re-run" (new contract required), any introduction of distance-decay/strict-horizon/silent-absorption-law/dilution-law as facts.
Note: the reviews were not adopted as claim authority; every adopted item already exists in canonical artifacts.