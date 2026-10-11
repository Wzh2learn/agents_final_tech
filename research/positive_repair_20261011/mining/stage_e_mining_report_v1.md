# Stage E Observation Surfaces + Multi-Leaf — Evidence-Mining Report

> Miner: `/root/miner_stage_e` (read-only) | Repo root: `D:\AIRcommend\JinRongAgents\agents_final_tech` | 2026-10-11
> Recorded by Loop D into Track P staging (`_repair_portfolio_20261011`). Verbatim deliverable.

**Source handles used below** (all repo-relative):
- `SE118` = docs/research/stage_e_118_quantification_v1.md
- `OBM` = docs/research/stage_e_observability_metrics_v1.md
- `ZERO` = docs/research/stage_e_zero_event_uncertainty_note_v1.md
- `MFPR` = docs/research/stage_e_matched_fpr_reanalysis_v1.md
- `PRE` = docs/research/stage_e_multileaf_preregistration_v1.md
- `PACKET` = docs/research/stage_e_multileaf_result_packet_v1.md
- `ABL` = docs/research/stage_e_multileaf_signature_ablation_v1.md
- `V2DELTA` = docs/research/stage_e_multileaf_v2_robustness_preregistration_delta_v1.md
- `FEAS` = research/stage_e_multileaf_20261010/loop_d_inputs/stage_e_independent_scorer_feasibility_v1.md
- `DESIGN` = docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md
- `CDT` = logs/graph/eval/checkpoint_discrimination_tables_v2.json; `T2` = logs/graph/eval/t2_visibility_sensitivity.json
- `TREES` = config/eval_checkpoint_trees.json; `AGG` = scripts/eval_checkpoint_aggregate.py
- `RUNNER` = research/stage_e_multileaf_20261010/run_multileaf_formal.py; `RECEIPT` = docs/research/multileaf_preresult_freeze_receipt_v1.md
- `SL` = paper/saner_rene_manuscript_scope_lock_v1.md; `VB` = .../loop_d_inputs/stage_e_version_b_revision_proposal_v1.md

## 1. FACT INVENTORY

### 1.1 Setup (corpus / surfaces / families)
- `FACT` Corpus: 95 frozen tables / 118 header-drift injections (K3 drift v0 lineage, TAT-QA public base, fully synthetic); matcher = `scripts/m1_statement_parser.py::map_headers` (pure rule, zero endpoints); drop rule `(H_orig - H_inj) * 10`, main threshold 2.0 (CDT.meta; SE118 §1; DESIGN §2 L103).
- `FACT` Checkpoint surfaces: two trees (`parse`, `qa`) in TREES, 12 leaves total: `parse.doc.ok`, `parse.doc.throughput`, `parse.field.hit_rate`, `parse.reconcile.equations`, `parse.table.regression`, `qa.citation.judge`, `qa.faithfulness.judge`, `qa.numeric.exact`, `qa.numeric.number_grounding`, `qa.refusal.deterministic`, `qa.refusal.judge`, `qa.retrieval.source_required` (ABL §2; TREES). Weights 1-3, sibling-normalized; leaf scale 0-10.
- `FACT` Six defect families (name; injections; visibility): alias variant 47/43 (91.49%); date variant 17/15 (88.24%); mixed language 20/20 (100%); OCR-like 13/0 (0%); prefix noise 16/13 (81.25%); unit suffix 5/5 (100%) (SE118 §3; CDT.by_type).
- `FACT` Headline numbers: 96/118 visible (81.36%), 22 blind; macro family visibility 76.83%; table-cluster bootstrap [72.88%, 88.50%]. Distinct denominators: visibility/detection 118, table-level 95, matched-FPR harmful 111 — never combined (SE118 §2; OBM §2-3).

### 1.2 OCR-like `0/13`
- `FACT` 0/13 visible across 11 table clusters, blind under the frozen absorption rule and all five gamma in {0.2,...,0.9}; predefined negative-observability control (SE118 §3; T2.prereg_predicates.E2_1).
- `FACT` Uncertainty: `[0,24.71%]` exact binomial only as independence reference; `[0,28.49%]` table-cluster event sensitivity; cluster bootstrap degenerate `[0,0]` (must not be shown as population bound) (ZERO §2-3; SE118 §3).
- `FACT` Strength gradient: among 13 OCR cases, first-difference-adjacent duplication (S') with edit distance 2 => 8/8 visible; distance 1 => 5/5 absorbed; "absorption region perfectly predicted" (T2.prereg_predicates.E2_3). Prediction ">=10/13 visible" missed (constructive bias, no mechanism counterexample).

### 1.3 Detection protocols and matched-FPR
- `FACT` Injection-level detection (118): end-to-end `112/118` (VD 90 / VU 6 / BD 22 / BU 0; P(D|V)=93.75%, P(D|B)=100%); flat `85/118` (85/11/0/22; 88.54%/0%); hierarchical `13/118` (13/83/0/22; 13.54%/0%) (SE118 §4).
- `FACT` End-to-end detects all 22 checkpoint-blind cases via final mapping-text change — construct divergence, not repair of checkpoint blindness (SE118 §4).
- `FACT` Matched-FPR at alpha=0.05: theta_flat=1.428571, theta_layered=0.535714; detections 90 vs 90 on H∪HI=111; 2,000 paired table-cluster bootstraps (seed 20260830, 88 clusters) => difference `[0,0]` (SE118 §5).
- `FACT` Clean-only identifiability blocker: 2,382 usable clean rows have contrastive support exactly {0}; positive clean counts 0 in every fold; matched-FPR TPR is `NOT_IDENTIFIABLE` (MFPR §2). Structural affine equivalence: slopes 0.3749999125-0.3750000375, max dev 8.75e-08, Spearman 1.0 (MFPR §3).
- `FACT` Harmfulness cells H 85/0/85, HI 11/15/26, E 0/7/7 (visible/blind/total) are descriptive; semantic harmfulness-conditional blindness UNVERIFIED (28 judged cases, no mixed-language/unit-suffix calls) (SE118 §6).

### 1.4 Hinge behavior / stable rule / missing evidence
- `FACT` Hinge nodes `parse_ok / exact_numeric / number_grounding` are hard gates: score 0 on failure (TREES meta note L21). Aggregate stable rule: >=90% leaves >=7 **and** no hinge leaf <7 (at that surface 18/20) (AGG L17, L251-259). DESIGN defines hinge leaf = load-bearing leaf that must reach >=7; ordinary leaves can be averaged away; hierarchy stable rule "90% + hinge-7" (DESIGN §2 L56/L67/L103).
- `FACT` Missing-evidence policy: encoded `0`, counted separately, never silently treated as a successful response (PRE §6, L100); "missing evidence" != "evidence proven zero" (DESIGN term table L68).

### 1.5 Multi-leaf facts
- `FACT` M/R/N = mapping/schema, retrieval/grounding, numeric/reconciliation; gold = "expected first affected stage", fixed pre-scoring; unit = stage-namespaced cluster, 3 deterministic injections/cluster; **24 clusters/stage x 3 = 72 clusters / 216 injections**, outcome-blind SHA-256 selection (seed 20261010) (PRE §1).
- `FACT` Stage contracts: M replaces one first-row header token with `__MUTANT_<hash8>__` -> direct leaf `parse.field.hit_rate` (downstream `parse.table.regression` also moves); R removes all required source blocks -> `qa.retrieval.source_required`; N breaks a row/col numeric identity (mutation >= max(1%, 0.02), tolerance 0.01) -> `parse.reconcile.equations` (PRE §2-4).
- `FACT` Result: LOCO macro-F1 `1.0`, top-1 `1.0`, ties/errors 0/0; permutation p = 1/10001 ~ 1e-4; cluster bootstrap [1,1]; baselines chance 1/3, majority macro-F1 1/6; status POSITIVE, construct-sensitive (PACKET §1, §3).
- `FACT` Operationally "direct instrument" = leaf predicate written from the stage's injection contract (the preregistered direct target; M also moves table.regression through the production matcher); 4 of 12 leaves ever respond, forming 3 disjoint signatures; "non-direct" = all remaining leaves — they show zero response except M's propagation, and non-direct-only decoding collapses to M-detection + ties (PACKET §3-4).
- `FACT` Ablation (post-hoc exploratory): full vector 1.0; direct_target_codebook **1.0**; each single-direct-leaf removal still 1.0; non_direct_leaves_only macro-F1/top-1 **0.3333** (tie 0.6667); any_response_scalar 0.0 (tie 1.0) (ABL §1). The perfect result is codebook-driven; "hierarchy alone does not imply localization" (PACKET §4.1; ABL §3).
- `FACT` Secondary: flat vs hierarchy Pearson 0.931305, Spearman 0.866025, R^2 0.867329, max residual 0.265152; both AUROC 1.0; clean-only matched point NOT_IDENTIFIABLE; single-leaf affine degeneracy broken (PACKET §6).
- `FACT` Integrity: freeze-before-materialize receipt with git/manifest/runner/env hashes; runner refuses to start on any mismatch; stop conditions specified (RECEIPT; RUNNER docstring). Independent checks: metric recompute 22/22, contract audit 216/216, Decimal reimplementation (PACKET §4). Zero model/GPU/API in the deterministic fixture; snapshot->completion window ~53 s suggests sub-minute reruns (INFERENCE — no explicit runtime field).

## 2. MECHANISMS

- How visibility is measured: absorption-rule crossing of leaf criterion (drop >= 2.0 on the 0-10 scale) + threshold-conditioned visibility over gamma grid; response vector = per-leaf binary "paired response in preregistered direction"; missing -> 0 with separate count (CDT.meta; SE118 §3; PRE §6; T2.e2_1).
- Where observations sit: two-root checkpoint tree, 12 leaves; hinges are hard gates; protocol endpoints (end-to-end/flat/hierarchical) sample **different surfaces** — hence 112/85/13 vs 96 visibility don't subtract (SE118 §4; OBM §1; TREES).
- Placement/instrumentation evidence: (i) controlled separability exists only where explicit stage-aligned instrumentation writes the response (PACKET §4.1); (ii) without direct leaves, remaining hierarchy yields chance (ABL); (iii) QA-layer silent normalization is recorded in the 12-row qa_arm note (model re-writes mutant header back to canonical name -> blind spot; endpoint :8004) (CDT.qa_arm); (iv) judge leaves on the QA tree are unexercised by the multileaf population and the 28-case judge set lacks mixed-language/unit-suffix calls (SE118 §6).

## 3. CANDIDATE REPAIR SEEDS (11)

**S1 [blind-family coverage] — Strength-ladder repair for the OCR family.** `FACT` base: distance-2 S' all visible, distance-1 all absorbed. Intervention: preregister a 3-bin OCR-adjacent strength ladder (lev-1, lev-2, double-substitution) and predict per-bin visibility. Held-out: fresh table clusters; test that visibility is monotone in pre-registered strength. Tautology: LOW (strength defined from construction, frozen before visibility read). Cost: LOW (reuse drift generator + quantify script; zero model). NULL informative: YES (lev-2 absorbed out-of-sample kills the criterion). Label: INFERENCE->testable.

**S2 [blind-family coverage] — Second zero-visibility negative control.** Add one new family (e.g., internal-whitespace OOV) expected blind at all gamma alongside OCR. Held-out: new clusters x all gamma; check the "0 across five thresholds" pattern replicates. Tautology: LOW. Cost: LOW. NULL: YES (visibility >0 would show OCR's blindness is not a family-level design effect).

**S3 [silent absorption] — Absorption ledger + normalization-path audit.** `FACT` base: alias 4/47, date 2/17, prefix 3/16 absorbed. Intervention: for each absorbed injection, log where the drift dies (matcher normalization vs QA-layer normalization), preregister a bypass variant that skips the erasing normalizer. Held-out: predict which new injections get absorbed from the registered path features. Tautology: MEDIUM (path features must not be defined by outcome). Cost: LOW-MEDIUM (deterministic paths; qa-layer leg may need judge/model budget). NULL: YES.

**S4 [observation placement/alignment] — LLM read-through checkpoint probe.** From the qa_arm note (12 rows): drift survives iff model reads the mutant token through. Intervention: add a deterministic "read-through" leaf (does output text contain/paraphrase the mutated token?) next to the existing QA leaves, preregistered on the 12-row scenario first. Held-out: new QA-arm cases; predict absorption from read-through status. Tautology: LOW. Cost: MEDIUM (new leaf code; possible bounded model calls — resource plan required). NULL: YES.

**S5 [propagation distance] — Execute the frozen exploratory endpoints.** `FACT`: propagation depth, first-visible distance, silent-absorption stage are unexecuted (PACKET §7). Intervention: pure reanalysis of stored 216 response vectors + freeze records: earliest visible leaf along pipeline order, count of downstream responses. Held-out: none needed for descriptors; add a pre-registered prediction set for the next injection batch (e.g., N-injections propagate downstream to numeric leaves; M stays upstream). Tautology: LOW. Cost: LOW (no new data). NULL: informative (documents that response geometry is degenerate).

**S6 [threshold/support identifiability] — Clean-support null-mutation panel.** `FACT` the MFPR doc names the remedy: revised score with nonzero clean support or a preregistered pseudo-injection/null-mutation panel. Intervention: build neutral-edit panel (edits canonicalizer maps to identity) -> positive clean support -> retest matched-FPR identifiability. Held-out: calibrate on fresh null panel; evaluate on frozen harmful pairs. Tautology: LOW (panel semantics frozen). Cost: MEDIUM (new generator + calibration). NULL: YES (zero support again => score definition structurally defective, publishable boundary).

**S7 [threshold/support identifiability] — Family visibility floor over gamma.** Intervention: report per-family min-over-gamma visibility ("absorption floor") with preregistered floors (OCR=0; others >0). Held-out: recompute on new injections. Tautology: LOW. Cost: LOW (reuse T2 grid). NULL: informative. Note: literal E2_1 range>=0.5 predicate already fails at gamma=0.7/0.9 (T2) — the floor formulation is the repair.

**S8 [redundant-checkpoint pruning / cost-reduction] — Minimal-leaf panel.** Intervention: from v1 signals freeze per-family minimal leaf subsets ({field.hit_rate, table.regression, source_required, reconcile}) and test family-visibility recovery on held-out clusters; also test a 2-bit "response count+position" summary (any_response_scalar already dead: 0.0). Held-out: new clusters. Tautology: HIGH on reused data — must hold out clusters. Cost: LOW. NULL: YES.

**S9 [missing-evidence instrumentation] — Three-valued evidence cells.** Policy exists (encode 0 + count separately) but is not exercised by fixtures. Intervention: extend outcome tables to {response, no-response, no-evidence} with separate denominators + contract tests incl. no-evidence fixtures (V2DELTA §2.6 already requires such tests). Held-out: contract tests. Tautology: N/A. Cost: LOW. NULL: informative (exposes silent zero-conflation).

**S10 [observation placement/alignment / evidence routing] — Construct ledger + denominator lint.** `FACT` repeated reviewer risk: numbers from 4 surfaces (96/112/85/13) invite subtraction. Intervention: machine-readable ledger mapping every reported number -> construct, surface, denominator; CI lint fails on cross-surface arithmetic in paper sources. Held-out: run lint on next manuscript revision. Cost: LOW. NULL: N/A (governance artifact).

**S11 [cost-reduction / evidence routing] — Label-blind rerun on held-out clusters (v1.5 bridge).** V2DELTA requires a new namespace; cheapest bridge: reuse the deterministic multileaf harness (sub-minute, zero-model) with label-blind feature extraction + >=1 overlapping leaf, on held-out clusters of the same corpus, as a *non-confirmatory* sensitivity run. Held-out: disjoint clusters. Tautology: MEDIUM (same corpus); explicitly non-confirmatory. Cost: LOW-MEDIUM (extractor change only; harness refuses changed config without new freeze — requires new freeze receipt/namespace). NULL: YES and the delta says report NULL if full vector <= direct codebook.

## 4. OPEN QUESTIONS / MISSING EVIDENCE

1. No natural-failure distribution and no natural cross-stage ambiguity measured (PACKET §7; SL limitations).
2. No frozen independent semantic scorer for Stage E; prototype (5-feature observation scorer) passes tests but `SCORER_GO` not frozen (FEAS §4-6).
3. Clean panel with nonzero contrastive support missing (MFPR §5).
4. Propagation depth / first-visible distance / silent-absorption stage unexecuted (PACKET §7).
5. Judge-coverage gaps: 28-case semantic analysis; no mixed-language or unit-suffix calls (SE118 §6).
6. Second dataflow gates open: FinQA v2 namespace license/split/raw-adapter prerequisites unresolved (V2DELTA §3-5; FEAS).
7. Inter-rater reliability, second implementation, external-corpus calibration absent (OBM §5).
8. `UNVERIFIED`: hinge-leaf flags' mapping onto the 12-leaf multileaf tree is documented only via TREES meta note + AGG route names; a one-page crosswalk hinge<->multileaf leaves has not been audited.
9. `UNVERIFIED`: qa_arm note (LLM-layer silent normalization, n=12, endpoint :8004) is recorded but not systematically tested; endpoint-dependence unknown.
10. High-gamma family-separation criterion: literal "range >=0.5 at all gamma" fails (0.7/0.9); the ranked non-degeneracy criterion survives — which should be canonical for paper claims (T2).

Compliance: read-only respected — no file writes, no mutating git, no ssh/network/model calls. Two attempted inter-agent messages failed to resolve and were no-ops.
