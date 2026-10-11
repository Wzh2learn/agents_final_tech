# Loop C Pre-Result Design RE-AUDIT — Track P First-Wave Preregs v2 (single budgeted re-audit)

You are the independent Loop C auditor. This is the ONE budgeted re-audit after revision 1 (user rule). Read-only, packet-only, report-only. No tools, no file reads, no network, no edits.

## Context and consequence
- Audit v1 (2026-10-11) returned CONDITIONAL for all four experiments: none FAIL, all SCOPE_CHANGE: NO. Loop D then applied ONE batched revision of prereg / implementation-contract text only (v2 files below) plus two shared contracts.
- This re-audit is final. PASS -> execution is authorized for that experiment (Loop D auto-dispatches; no further user approval). CONDITIONAL at this stage is treated as final non-PASS -> STOP_BRANCH (no further revision is authorized). FAIL -> STOP_BRANCH. Scientific scope must NOT change.
- If a residual issue does not undermine executability/interpretability, you may note it as non-blocking under PASS. If it does undermine, mark FAIL and state why.

## Audit-v1 condition closure map (claimed; verify against the v2 texts)

### PR-EXP-03
- (a) no-op + specificity arms + FP side -> v2 section 4 Arms A0/A1 (must return 0), section 5 secondary (A0/A1 false-positive counts), section 7 POSITIVE requires A0/A1 pass; constant-1 documented control.
- (b) attribution operationalization -> contracts/SOURCE_LOCAL_RESPONSE_v1.md per-experiment test; v2 section 5 attribution-pass definition (unique catches + A0/A1 clean + constant-1 documented failure).
- (c) complete outcome taxonomy + sanity-gate definition -> v2 section 7 (POSITIVE / DIAG_ONLY / NULL / NEGATIVE / INVALID / NOT_EVALUABLE; sanity gate defined; NOT_EVALUABLE never merged into NULL).
- (d) freeze verbatim rules/hashes -> v2 section 3 (selection rule verbatim + exclusion registry + extraction command), section 4 (baseline verbatim extract + hashes), section 8 implementation-contract requirement.
- (e) cost tolerance + P1 ground-truth labels -> v2 section 6 exact-equality check-count tolerance; section 3 ground truth (stage "M", family "topology_transposition"); section 5 mixed-population diagnosability definition + LOCO groups.

### PR-EXP-01
- (a) surfaces + non-identity-on-scored / hash-identity-on-truth + NOT_EVALUABLE fallback -> v2 section 2.
- (b) threshold rule incl. ties/strictness -> v2 section 4.
- (c) checker independence + panel completeness -> v2 section 2.
- (d) empirical clean-row bridge report -> v2 section 7.
- (e) single canonical outcome label -> v2 section 6.

### PR-EXP-04
- (a) cost section -> v2 section 6.
- (b) symmetric gate / attrition -> v2 section 3 (N1 descriptive attrition reported; N2 gate; declarations).
- (c) numeric directional taxonomy -> v2 section 7 (margin m=0.05; SUPPORTED / NULL fingerprint-bound / NEGATIVE / NOT_EVALUABLE with insufficient-groups clause).
- (d) harness confound control -> v2 section 4 harness-equivalence control (mandatory; failure = INVALID); conclusion bound to the shared generation harness; confound recorded.
- (e) numeric baselines + group definition + contamination declaration -> v2 section 5 (frozen numbers), section 3 (group definition; N1-development contamination declared).

### PR-EXP-07
- (a) NOT_EVALUABLE + attrition rule -> v2 section 3 taxonomy + section 5 attrition table.
- (b) label provenance + pairing-rule certification -> v2 section 1 (injection-design labels; pairing rule built from frozen structure; certification note).
- (c) population/fold pinned by hash + freeze timing -> v2 section 2 (population pinned; folds referenced by hash) + section 1 (freeze before feature-value observation).
- (d) numeric "clearly above" + taxonomy completeness -> v2 section 3 (0.05 margins; NULL_DIRECT_CONCENTRATED; NULL_AT_CHANCE).
- (e) quantified blind-vs-original delta + robust binding -> v2 section 5 (delta on identical rows) + section 3 (robust criteria).

### Global closures
- SOURCE_LOCAL_RESPONSE defined with per-experiment operational tests (see contract).
- Shared-surface ordering: contracts/shared_surface_freeze_v1.json pins runner / carriers / manifest / canonicalizer hashes; no edits after observation; GB10-only inputs noted for execution-time pinning.
- Anti-cherry-picking: failures retained; NOT_EVALUABLE never merged into NULL; PR-07 compliance fixed; PR-01 labels canonicalized.

## Audit questions (answer ALL 10 per experiment; one line each)
1. Is any improvement guaranteed by definition (or achievable only via definitional construction)?
2. Does the design change observability rather than labels / task truth?
3. Is the held-out set independent and correctly partitioned (leakage, UID overlap, freeze order)?
4. Are baselines fair and complete for this experiment type?
5. Is cost accounted fairly; is a same-budget comparison possible?
6. Can a source-local-only gain be ruled out (or is source-locality handled in the right direction)?
7. Are before/after measurement objects comparable, with non-comparabilities correctly declared?
8. Is NULL / NOT_EVALUABLE informative and correctly separated?
9. Does anything change the scientific scope relative to the human-approved prompt? (also set SCOPE_CHANGE)
10. Are any mandatory conditions still missing? (list precisely)

## Required output format (machine-parseable)
## PR-EXP-03
- Q1..Q10 lines
- VERDICT: PASS | CONDITIONAL | FAIL
- SCOPE_CHANGE: NO | YES (<desc>)
- RESIDUAL_NOTES: (optional; non-blocking)
- BLOCKING_REASON: (only if FAIL or if CONDITIONAL would stop the branch)
(repeat for PR-EXP-01, PR-EXP-04, PR-EXP-07)
## GLOBAL
- <notes>
End with the literal line: RE-AUDIT_COMPLETE

--- BEGIN PR-EXP-03 prereg v2 ---
# Prereg — PR-EXP-03: M-stage structural-oracle coverage repair (de-alias)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-03 | candidate: PR-03 | role: INTERVENTION_REPAIR
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> shared artifacts pinned in research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json

## 1. Hypothesis
A table-structure oracle defined from table/schema semantics and frozen before any topology-outcome observation recovers held-out structural failures that the existing field-hit-derived oracle misses, at comparable measurement cost, without constant-1-style or duplicate-catch artifacts.

## 2. Owner-fixed criteria (2026-10-11 human decision, section 3)
Primary question: held-out structural failures recovered where the existing oracle misses, comparable cost. Oracle from table/schema/execution semantics; no mutation labels; no held-out outcome; frozen before any M2-type result observation; held-out topology failures independent; old vs repaired oracle on the same population. Primary metrics: (1) held-out failure coverage delta; (2) stage/family diagnosability delta. Improvement only from SOURCE_LOCAL_RESPONSE -> not a repair positive. Merely-different oracle with no held-out diagnostic gain -> NULL.

## 3. Population
- P1 held-out topology failure set: deterministic adjacent-column transposition failures over held-out table UIDs. Selection rule (verbatim; pinned in the implementation contract): UIDs = ascending SHA-256(seed=20261011:namespace="pr03-topology":uid) over the frozen drift corpus table set (membership pinned by source-file hash + UID list hash); EXCLUSION REGISTRY = M-stage UIDs and N-stage UIDs extracted from research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json (extraction command recorded verbatim); exactly one adjacent column pair transposed per selected table, pair index by frozen per-table hash rule; values and row counts preserved; generator double-run byte-identical required.
- Ground truth for P1: stage_label="M", family_label="topology_transposition".
- P2 control: frozen 216-row carriers — untouched; only for the regression check; never for primary metrics.
- P3 M1 regression set: held-out M1-style cases (frozen selection rule).

## 4. Intervention and arms (frozen before P1 generation)
Structural oracle v2 at parse.table.regression: response = int(structural_signature(baseline) != structural_signature(injected)); structural_signature = (column_count, ordered positional header-token sequence under the pinned canonicalizer, row_count). No mutation labels; no held-out outcomes; fail-closed: undefined artifacts -> NOT_EVALUABLE cell.
Freeze order: (1) oracle implementation hash + verbatim rules; (2) P1 generation; (3) evaluation. No edits after P1 observation.
Arms (same frozen response rule): A0 no-op/identity (structural oracle must return 0 on every case); A1 value-only specificity (cell-value changes, structure preserved; must return 0); A2 P1 (expected 1); A3 frozen-carrier regression (M1 subset; expected 0).
Baseline oracles on the same population: (a) v1 aliased implementation (verbatim two-line extract from run_multileaf_formal.py:256-258 + file hash), (b) standalone field-hit oracle; unchanged.
Constant-1 control: documented that a constant-1 rule attains coverage=1 on P1 but fails A0/A1; POSITIVE therefore requires A0/A1 pass.

## 5. Metrics
Primary: (1) held-out failure coverage delta = coverage(new) − coverage(old) on P1 (raw numerators/denominators; cluster bootstrap CI over table UIDs, frozen seed); (2) stage/family diagnosability delta on the mixed held-out population = P1 ∪ frozen-rule subsample of carriers; macro-F1 via frozen nearest-centroid, LOCO over groups (table/document clusters, no source overlap); conclusion-level deltas only.
Secondary: disagreement rate; incremental unique catches; check-cost (§6); M1 regression; A0/A1 false-positive counts.
Attribution audit (operational; per contracts/SOURCE_LOCAL_RESPONSE_v1.md): pass = unique new catches AND A0/A1 clean AND constant-1 documented failure.

## 6. Cost and cost tolerance (defined)
Zero model/judge calls. Both oracles produce exactly 1 leaf response per case: check-count equality is the frozen cost tolerance (exact equality; no runtime-based claim). Freeze/audit overhead recorded in the cost ledger.

## 7. Outcome taxonomy (complete)
- POSITIVE: Δcov > 0 with CI lower > 0 AND Δdiag >= −0.02 (frozen materiality margin) AND A0/A1 pass AND no M1 regression AND attribution pass.
- DIAG_ONLY: Δcov <= 0 or CI includes 0, but Δdiag > +0.02 -> recorded as NULL with diag gain noted; NOT a repair positive.
- NULL: no material gain and no material loss (coverage nonpositive or CI includes 0; |Δdiag| <= 0.02).
- NEGATIVE: Δdiag < −0.02 (regardless of coverage).
- INVALID: sanity-gate failure, label access, post-freeze edits, UID overlap, cost inequivalence.
- NOT_EVALUABLE: P1 not executable/visible, or oracle semantics undefined on held-out artifacts. Never merged into NULL.
Sanity gate (defined): the structural column must differ from the field-hit column on >=1 held-out P1 case AND must not be a monotone function of field-hit on the frozen 216 rows; failure = INVALID (implementation defect), not a scientific outcome.

## 8. Implementation contract requirement
Before execution, Loop A materializes runs/PR-EXP-03/implementation_contract.md containing verbatim: drift-corpus membership rule (source path + sha256 + UID list hash), UID exclusion registry (extracted list + extraction command), pair-selection hash rule, oracle v2 source hash, baseline extract hashes, arm definitions, bootstrap seed, shared-surface hash check results. Missing items -> INPUT_MISSING stop.

## 9. Stop conditions
Any requirement violation; no threshold/oracle hunting; any scope change -> new prereg + re-audit. If any audit-v1 condition cannot be satisfied within this revision -> STOP_BRANCH.

--- BEGIN PR-EXP-01 prereg v2 ---
# Prereg — PR-EXP-01: SYNTHETIC_NULL_SUPPORT_REPAIR

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-01 | candidate: PR-01 | role: INTERVENTION_REPAIR
> claim object: SYNTHETIC_NULL_SUPPORT_REPAIR — never "empirical clean-only matched-FPR repair"
> frozen: 2026-10-11 | authority: Human decision 2026-10-11; execution requires Loop C pre-result PASS and the null-semantics qualification below

## 1. Background (facts)
Clean-only matched-FPR operating point NOT_IDENTIFIABLE; 2,382 clean rows carry contrastive support exactly {0}; the frozen reanalysis doc names the remedy: nonzero clean support via a preregistered null-mutation panel.

## 2. Null-semantics qualification (fail-closed; surfaces defined)
- Scored surface: the exact raw observation surface consumed by the frozen contrastive score computation — pinned verbatim in the implementation contract by reading the frozen scorer implementation (path + hash + exact input expression).
- Task-truth surface: downstream canonical artifacts (post-canonicalization pipeline outputs) — identity (hash equality) required.
- Admitted edits must be NON-identity on the scored surface AND hash-identical on the task-truth surface. If no edits satisfy both under the frozen edit DSL -> NOT_EVALUABLE (panel empty), never NULL.
- Generator/checker independence: checker must not import the generator module (AST import check); separate file-hash lineage recorded; checker re-runs canonicalization + downstream pipeline and requires downstream hash equality.
- Panel completeness: panel = the complete admitted set under the frozen rule; no sampling, no outcome-based selection.

## 3. Populations and split
- Calibration nulls: admitted edits on calibration folds (frozen 5-fold table-UID rule inherited from the matched-FPR reanalysis namespace; rule text pinned verbatim in the implementation contract).
- Held-out nulls: disjoint folds.
- Harmful pairs: frozen 111 harmful pairs; NEVER used for threshold selection; read only after the operating point is frozen.

## 4. Threshold rule (frozen, incl. ties)
Threshold = the smallest t such that fraction(calibration-null scores > t) <= alpha, alpha=0.05; strict greater-than comparison; ties handled by the frozen "smallest t" rule (all candidate t drawn from the calibration-null score support). Rule hash-frozen before any harmful-side read.

## 5. Primary qualification and positive rule
- calibration null support > single point;
- threshold solely from calibration nulls;
- held-out null FPR <= alpha;
- THEN held-out harmful TPR at the frozen operating point (+ paired cluster bootstrap CI).
- POSITIVE = operating point becomes identifiable AND held-out null FPR contract satisfied. Identifiability status recorded as a result ATTRIBUTE, not a label.

## 6. Outcome labels (canonical, single string per run)
- POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE (exactly one).
- NULL: substantive run failing support or FPR contract (informative: bounds the remedy). 
- NOT_EVALUABLE: empty admission set, unverifiable identity, or unpinnable scored surface; never merged into NULL.
- INVALID: harmful-side involvement in selection; any post-freeze edit; relabeling as empirical clean-only repair.

## 7. Reporting boundary and bridge report
- Report the original 2,382-row identifiability result separately; never silently replace E2's population. All conclusions phrased as SYNTHETIC_NULL_SUPPORT_REPAIR.
- Bridge report (required): empirical clean-row score distribution + their FPR at the frozen threshold, labeled explicitly as a non-comparable empirical-vs-synthetic read.

## 8. Cost
Zero model calls; deterministic; calibration + held-out runs in minutes; same-budget comparison = same procedure on both null partitions.

## 9. Stop conditions
Qualification failure or unverifiable identity -> STOP (NOT_EVALUABLE). If the scored surface cannot be pinned without changing the claim object -> STOP_BRANCH. No threshold hunting; any scope change -> new prereg + re-audit.

--- BEGIN PR-EXP-04 prereg v2 ---
# Prereg — PR-EXP-04: Cross-mechanism generalization (N1 vs N2)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-04 | candidate: PR-04 | role: GENERALIZATION_TEST (supporting evidence only; does NOT count toward the repair count)
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS

## 1. Hypothesis
The frozen stage-aligned signature for stage N generalizes across genuine mutation mechanisms: N1 operand-value perturbation vs N2 operator/coefficient perturbation. Tests whether instrumentation captures stage information beyond a single mutation fingerprint.

## 2. N2 requirements (all mandatory; else MECHANISM_NOT_EVALUABLE)
- genuine different mechanism (operator/coefficient/sign semantics change; not a string/parameter variant);
- deterministic;
- executor-owned downstream consequence (relation recomputed through the frozen reconciliation path);
- preregistered before any N2 result (this file);
- visibility/evaluability minimum gate: >= 2/3 of generated N2 injections produce >= 1 measurable response on the frozen 12-leaf surface under the frozen response rule AND >= 6 distinct held-out groups show response. Otherwise: MECHANISM_NOT_EVALUABLE (never a generalization failure);
- N2 selection rationale: determinism and executor ownership, NOT expected performance.

## 3. Population, groups, and split
- N1 rows: existing frozen N-stage carriers (unchanged; descriptive gate attrition reported).
- N2 rows: new deterministic N2 injections on held-out groups; generation rule frozen; UIDs disjoint from N1 groups; double-run byte-identical.
- "Group" (defined): stage-namespaced cluster as in the frozen freeze receipt (N:<uid>); for N2, groups = held-out table UIDs.
- mechanism-disjoint + group-disjoint; directions N1->N2 and N2->N1 (fit on one mechanism's groups; evaluate on the other's).
- Declarations: N1 and N2 are different populations by design; the visibility gate conditions N2 (N1 is frozen with its own observed 72/72 visibility; attrition reported for both); method-development history on N1 carriers is recorded as making the N2->N1 direction potentially optimistic.

## 4. Design and controls
Frozen nearest-centroid (tie=failure), LOCO on held-out groups; direct-codebook control mandatory; responsive-leaf-set overlap report mandatory; extraction frozen before N2 rows observed; no feature edits after observation.
- Feature surface ban: features may only use the frozen 12-leaf response surface + frozen contract-check outputs; provenance/mechanism-identifier features are forbidden (pinned in the implementation contract).
- Harness-equivalence control (mandatory): regenerate N1 rows through the N2 harness code path; require byte-identical response vectors vs frozen N1 rows; failure -> INVALID (harness confound not separable).

## 5. Primary metric and frozen baselines
macro-F1 / stage identification per direction; frozen baselines (numeric): chance top-1 = 1/3; uniform-class macro-F1 = 1/3; majority macro-F1 = 1/6; direct-codebook references from the frozen ablation (full 1.0 / direct 1.0 / non-direct 0.3333). Cluster bootstrap CIs.

## 6. Cost (added)
Zero model/judge calls; GB10 minutes; same-budget comparison = identical procedure both directions; freeze/audit overhead in the cost ledger.

## 7. Outcome taxonomy (complete, numeric)
Materiality margin m=0.05.
- SUPPORTED (supporting): both directions point >= 1/3 AND >= 1 direction CI-low > 1/3 AND direct-codebook control reported AND overlap report attached.
- NULL (fingerprint-bound): all directions |point − 1/3| <= m, or CI includes 1/3 without meeting SUPPORTED criteria. Documented; bounds the flagship claim.
- NEGATIVE: any direction point < 1/3 − m.
- NOT_EVALUABLE: N2 fails the visibility/evaluability gate (MECHANISM_NOT_EVALUABLE), or insufficient groups for a CI. Never merged into NULL.
- INVALID: leakage between mechanism sets; harness-equivalence failure; post-hoc tuning; prereg deviations.

## 8. Stop conditions
Any requirement violation; no tuning to recover transfer. This experiment never counts toward the repair count.

--- BEGIN PR-EXP-07 prereg v2 ---
# Prereg — PR-EXP-07: Label-blind re-extraction (anti-tautology robustness)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-07 | candidate: PR-07 | role: ROBUSTNESS_ANTI_TAUTOLOGY (supporting evidence only; NOT a repair count)
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> Objective: re-test the multi-leaf result after removing every possible label / contract-construction information channel. NOT a new positive method.

## 1. Extractor blindness contract (provably enforced)
Inputs ONLY: the unordered pair {A,B} of paired raw observation states. Blind pairing: the PAIRING RULE is built from the frozen cluster structure only (which samples belong together is fixed by construction, never by response values); pair ORDER randomized by frozen seed; features computed as order-invariant (symmetric) functions; swap-invariance test required across all rows (feature(P) == feature(swap(P))).
Forbidden knowledge (structurally impossible): mutation family label; stage label; expected first stage; target checkpoint identity; gold outcome; sample namespace; generation code.
Label provenance (declared): decoded labels are injection-design stage labels fixed in the frozen freeze record before scoring; labels are never response-derived.
Freeze timing: extractor + feature sets frozen BY HASH BEFORE any feature-value observation (freeze first, then compute features, then evaluate). No post-hoc tuning; any edit -> new prereg.
Pairing-rule certification: record the pairing rule source + proof it reads no response values (code inspection note + hash).

## 2. Frozen feature sets and population
- Population: the frozen 216-row multi-leaf carriers (paths + hashes pinned in the implementation contract); LOCO groups = frozen cluster ids (rule referenced by hash from the freeze receipt).
- Feature sets frozen by hash: full label-blind set; direct-codebook subset (label-blind definition frozen); non-direct subset.
- NULL rule (binding): full <= direct -> NULL.

## 3. Primary metric and numeric criteria
macro-F1 / top-1 under frozen nearest-centroid + LOCO vs direct-codebook baseline vs chance (1/3).
Shuffled-label negative control (frozen seed) included.
Numeric "clearly above" (frozen): ROBUST requires (full point − direct point >= 0.05) AND (non-direct point >= 1/3 + 0.05).
Case taxonomy (complete): ROBUST (both criteria); NULL_DIRECT_CONCENTRATED (full > direct but non-direct <= chance margin); NULL (full <= direct); NULL_AT_CHANCE (full > direct but full ≈ chance within 0.05); NOT_EVALUABLE (undefined features / missing proof artifacts; row-level attrition accounting mandatory; never merged into NULL); INVALID (any leakage channel usable; swap-invariance or pairing proof fails).

## 4. Interpretation (owner-fixed)
- ROBUST -> robust supporting evidence.
- Degradation -> retain NULL/negative AND explicitly lower the original multi-leaf claim (recorded, never silent).

## 5. Required reports
- Quantified blind-vs-original delta on identical rows: Δ = full_labelblind_macroF1 − original_frozen_macroF1, reported with CI; explicitly declared non-comparable claim-wise (different measurement objects) while the numeric delta is recorded.
- Attrition table (rows per exclusion reason).

## 6. Cost / Stop
Zero model calls; deterministic; minutes of GB10 compute.
STOP: swap-invariance or pairing proof failure -> INVALID; then stop. No rescue tuning of the extractor.

--- BEGIN contract: SOURCE_LOCAL_RESPONSE_v1.md ---
# Shared Term Sheet — SOURCE_LOCAL_RESPONSE v1

> frozen: 2026-10-11 | closes audit-v1 GLOBAL condition (undefined shared term) | applies to PR-EXP-03/01/04/07

## Definition
`SOURCE_LOCAL_RESPONSE`: a response that is a pure function of the mutation target's own local state (the exact tokens/cells/structure the mutation wrote), computable without observing any state beyond the mutation point.

## Attribution rule
A repair's gain is "source-local-only" (and therefore NOT counted as a repair positive) unless the experiment's frozen operational test passes. Global minimum requirements: (i) duplicate-catch analysis (new catches must not be duplicates of the baseline channel's catches); (ii) the experiment's specificity/no-op arms must not fire for the new channel; (iii) no constant-1-style trivial rule may attain the gain.

## Per-experiment operational tests (frozen)
- PR-EXP-03: pass = (i) all new structural catches unique vs both baseline oracles at frozen rules; (ii) no-op/identity and value-only arms return 0 for the structural oracle; (iii) constant-1 rule documented to fail specificity.
- PR-EXP-04: source-locality is the failure mode under test; fingerprint-bound NULL branch + direct-codebook control + responsive-leaf overlap report operationalize it.
- PR-EXP-07: `full <= direct` binding NULL rule; "robust" additionally requires the non-direct subset to clear chance (frozen margin), so a direct/source-local-concentrated gain cannot be narrated as robust.
- PR-EXP-01: claim object restricted to SYNTHETIC_NULL_SUPPORT_REPAIR; source-local language not used.

--- BEGIN contract: shared_surface_freeze_v1.json ---
{
  "file": "shared_surface_freeze_v1",
  "frozen": "2026-10-11",
  "rule": "Locked first per audit-v1 GLOBAL ordering constraint: these shared surfaces must be hash-verified before any run and must not be edited after any P1/N2/panel observation. If any is edited, all dependent experiment freezes are invalidated.",
  "pinned": {
    "multileaf_response_rule_and_runner": {"path": "research/stage_e_multileaf_20261010/run_multileaf_formal.py", "sha256": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4"},
    "multileaf_paired_artifacts": {"path": "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl", "sha256": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f"},
    "multileaf_prediction_rows": {"path": "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl", "sha256": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06"},
    "multileaf_preresult_freeze_manifest": {"path": "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json", "sha256": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163"},
    "canonicalizer_file": {"path": "scripts/m1_statement_parser.py", "sha256": "F9F1BC92C9D2963B3F346C0557F2B6A59D22201277B2023400F6953C59AC4AEE", "note": "hash computed at revision time (2026-10-11); re-verified by Loop A before runs"},
    "source_local_term_sheet": {"path": "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md"}
  },
  "gb10_only_inputs": [
    {"path": "data/research/drift_v0/input/tatqa_tables.json", "sha256_prefix_known": "3e7e0568", "note": "full hash pinned by Loop A in the implementation contract"},
    {"path": "data/research/drift_v0/output/injection_map.json", "sha256_prefix_known": "d7612405", "note": "full hash pinned by Loop A in the implementation contract"}
  ]
}

--- END PACKET ---
