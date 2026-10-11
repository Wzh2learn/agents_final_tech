# Positive Repair Candidate Pool v1

> Status: `CANDIDATE_MINING_COMPLETE_PENDING_LOOP_C_CHALLENGE` | Round: Track P phase-1 (mining + selection) | 2026-10-11
> Mode (inquiry-methods): primary = `minimal-experiment` (choosing among minimal repair experiments); secondary = `first-principles` (reserved for the future synthesis gate, not used to force a method).
> Boundary: read-only mining over `eae2688` canonical artifacts + frozen result carriers. No experiment executed. No frozen value changed. All numbers below are FACT-labeled only when traceable to a cited artifact; otherwise labeled INFERENCE / UNVERIFIED.
> Routing: candidate selection follows the user's transparent multi-dim ordering (A validity / B isolation / C held-out evaluability / D low tautology / E low cost / F SANER relevance / G shared-principle potential). No pseudo-precise single score.

## 0. Pool summary

| ID | Category | One-line repair | Tier | Draft set |
|---|---|---|---|---|
| PR-01 | threshold/support identifiability | clean-support null-mutation panel; re-test matched-FPR identifiability with nonzero clean support | T1 | FOR-CHALLENGE |
| PR-02 | observation placement/alignment | placement-distance re-observation over frozen 216x12 carriers; quantify decay of diagnosability with source->observation distance | T1 | FOR-CHALLENGE |
| PR-03 | oracle alignment / de-alias | replace the aliased M-stage "downstream" leaf with a genuine structural oracle; close the MVP HIGH blocker | T1 | FOR-CHALLENGE |
| PR-04 | replicated repair / mechanism transfer | implement ONE additional deterministic mechanism for one stage; test cross-mechanism A->B/B->A transfer | T1 | FOR-CHALLENGE |
| PR-05 | blind-family coverage | preregistered OCR-adjacent strength ladder + second expected-blind control family on held-out clusters | T1 | FOR-CHALLENGE |
| PR-06 | redundant-checkpoint pruning / cost | minimal sufficient leaf subset at equal held-out diagnosability + cost ledger | T1/T2 | FOR-CHALLENGE |
| PR-07 | measurement-object separation | label-blind re-extraction bridge (v2-delta requirements) as non-confirmatory sensitivity run | T1/T2 | FOR-CHALLENGE |
| PR-08 | missing-evidence instrumentation | tri-state {response / no-response / no-evidence} cells + contract fixtures; decision-flip accounting | T2 | FOR-CHALLENGE |
| PR-09 | silent absorption (QA layer) | deterministic read-through leaf probe for QA-layer normalization blind spot | T2 | RESERVE |
| PR-10 | silent absorption (diagnostics) | absorption ledger + normalization-path audit (where the drift dies) | T2 | RESERVE |
| PR-11 | propagation instrumentation | runner emits per-stage state hashes + first-visible leaf index (new namespace) | T2 | RESERVE |
| PR-12 | deterministic contract / judge->rule | replace one judge leaf with deterministic rule (needs a population where judges fire) | T3 | RESERVE |
| PR-13 | threshold criterion repair | family visibility floor (min-over-gamma) criterion, out-of-sample only | T3 | MARGINAL |
| PR-14 | deterministic contract (micro) | stable-k overwrite quirk in aggregate report path (verify intent, then fix) | T3 | HYGIENE |
| PR-15 | governance artifact | construct ledger + denominator lint for cross-surface numbers | T3 | NOT-AN-EXPERIMENT |
| E1 | FinQA scoring repair | any change to FinQA step-scoring semantics | - | ELIMINATED (policy) |
| E2 | direct comparator probe | family-targeted direct comparator for OCR visibility | - | ELIMINATED (direct-codebook) |
| E3 | trace completeness | Stage E traces already complete; FinQA trace side closed | - | ELIMINATED (no repair target) |
| E4 | stage-local evidence routing standalone | subsumed by PR-02 / PR-06 | - | MERGED |
| E5 | add direct checkpoints for more families | direct-codebook class, penalized by design rules | - | ELIMINATED (tautology) |

## 1. Full candidate entries (19 required fields each)

Field order: 1 problem_id / 2 observed problem / 3 supporting evidence / 4 root-cause hypothesis / 5 minimal intervention / 6 causal mechanism / 7 measurement object before / 8 measurement object after / 9 held-out population / 10 primary metric / 11 secondary metric / 12 observation+compute cost / 13 implementation effort / 14 tautology risk / 15 leakage risk / 16 task-definition change / 17 NULL value / 18 SANER relevance / 19 possible shared principle.

### PR-01 Clean-support null-mutation panel

1. `PR-01 / SUPPORT-REPAIR`
2. `FACT`: clean-only matched-FPR operating point is `NOT_IDENTIFIABLE`; 2,382 usable clean rows carry contrastive support exactly `{0}`; positive clean counts `0/0` in every fold (MFPR §2).
3. `FACT`: MFPR §2 names the remedy verbatim - "a revised score definition with nonzero clean support or a separately preregistered pseudo-injection/null-mutation panel"; frozen matched-FPR detections 90 vs 90, CI `[0,0]`, 88 clusters, seed 20260830 (SE118 §5).
4. `INFERENCE`: the score's two sub-observations are identical for unmodified rows (`h_repeat ≡ h`), so clean support degenerates; with zero support any positive threshold shows observed FPR 0 and equality is untestable.
5. Minimal intervention: build a preregistered null-mutation panel (semantics-preserving edits that the canonicalizer maps to identity) on the frozen corpus machinery; re-run the SAME identifiability analysis (same score definition, folds, threshold rule) with support > 0.
6. `INFERENCE`: null edits create nonzero-but-clean score variation -> clean FPR becomes observable across thresholds -> the matched operating point becomes decidable (identifiable interval), or provably still not.
7. Before: clean FPR support `{0}`; empirical equality `NOT_IDENTIFIABLE`.
8. After: identical measurement contract; clean support > 0; identifiability status decidable; equality claim re-adjudicated.
9. Held-out: panel calibration on one table-cluster half; identifiability re-test on held-out clusters; families kept separate.
10. Primary: clean-side positive support count (>0) and identifiability decision; paired TPR difference at matched FPR with CI (where identifiable).
11. Secondary: null-panel false-positive rate; score variance; per-fold stability; denominator accounting.
12. Cost: LOW - deterministic, zero model/endpoint; new generator + calibration ~1 day; sub-minute GB10 runs.
13. Effort: LOW-MED - new deterministic mutation generator + freeze receipt + analysis rerun; no executor rewrite.
14. Tautology risk: LOW-MED - panel semantics must be frozen before harmful-side inspection; risk is "engineered support"; NULL remains possible (support may stay 0).
15. Leakage risk: LOW - null panel never touches harmful rows; folds fixed.
16. Task-definition change: NO - same scores, same evaluation task; adds a control panel (disclosed as design augmentation).
17. NULL value: HIGH - zero support even after null edits proves the score definition structurally defective (actionable, publishable boundary).
18. SANER relevance: HIGH - repairs/re-frames the headline negative `[0,0]`; answers "can the identifiability blocker be repaired?".
19. Shared principle: threshold identifiability requires clean-side support that must be CONSTRUCTED, not assumed.

### PR-02 Observation placement / alignment re-observation

1. `PR-02 / PLACEMENT-DISTANCE`
2. `FACT`: localization exists only at directly instrumented leaves; non-direct collapse to `0.3333` (tie 0.6667); "propagation depth, first-visible distance and silent absorption remain unexecuted" (ABL §1; PACKET §7).
3. `FACT`: 4 of 12 leaves respond; 8/12 columns identically zero; leaf order/weights frozen in `config/eval_checkpoint_trees.json`; `scripts/eval_checkpoint_aggregate.py` derives any tree-node score from leaf scores by sibling-normalized weighted mean. `FACT` (code-miner Q6-b1): re-placement over existing 12-leaf responses is "hours, no runner change".
4. `INFERENCE`: diagnosability is a function of distance from fault source to observation node; aggregation dilutes the responsive leaf's contribution; a recoverable band beyond distance 0 may or may not exist.
5. Minimal intervention: freeze a placement rule set (parent / grandparent / sibling sets / non-direct subset of each responsive leaf); compute node scores via the frozen aggregation from the frozen 216x12 carriers; re-run the frozen nearest-centroid discrimination per placement under LOCO. New namespace; no new injections.
6. `INFERENCE`: signal persists while the responsive leaf's weighted fraction of the observed aggregate keeps the class separation above noise; the curve quantifies decay.
7. Before: accuracy from full/direct surface only.
8. After: accuracy as function of placement distance; same metric, same classes, same measurement contract.
9. Held-out: LOCO clusters (72); placement rules frozen before results.
10. Primary: macro-F1 / top-1 vs placement class; decay curve; ties.
11. Secondary: cost proxy per placement (leaf-check counts); ablation controls (full/direct/non-direct replication).
12. Cost: LOW - hours of analysis; seconds of compute; zero endpoints.
13. Effort: LOW - analysis script + freeze; reuse aggregate code.
14. Tautology risk: MED - decay is expected; require pre-declared shape predictions and falsification thresholds; probe "definitional dilution".
15. Leakage risk: LOW - frozen rules; LOCO.
16. Task-definition change: NO.
17. NULL value: HIGH - "no signal beyond direct" sharpens the necessity claim; a curve creates the first quantitative placement basis.
18. SANER relevance: HIGH - "aligned observation" is the paper's core implication.
19. Shared principle: diagnosability decays with source->observation distance; alignment = placing observation within the recoverable band. (Strongest shared-principle seed in the pool.)

### PR-03 M-stage oracle de-alias

1. `PR-03 / DEALIAS-M`
2. `FACT`: `parse.table.regression` and `parse.field.hit_rate` are the same predicate and identical columns across all 216 rows (`run_multileaf_formal.py:257-258`); MVP Loop C filed this as a HIGH incident and the single blocker (MVP-Audit F5/F7, "Single blocker", "Repair condition").
3. `FACT`: the frozen anti-tautology contract depends on the SOURCE_LOCAL vs DOWNSTREAM_CAUSAL partition, which is undefined while the two leaves alias (MVP-Audit I1-I3).
4. `INFERENCE`: one predicate was written to two leaf slots; the "table regression" label has no genuine table-shape oracle behind it.
5. Minimal intervention: implement a genuine structural oracle (column-order/shape signature comparison) for `parse.table.regression`; freeze it before any association test; re-run the frozen evaluation + ablation with the corrected column; report which conclusions change (expect M1 downstream stays non-estimable - correct by construction - and the alias is gone).
6. `INFERENCE`: authentic structural measurement removes the contamination; the source/downstream partition becomes well-defined for future mechanisms.
7. Before: two aliased leaves; undefined partition.
8. After: two independent measurements; explicit non-estimability accounting preserved.
9. Held-out: LOCO + existing ablation codebook control.
10. Primary: leaf independence (identical-column check -> 0), stage signature re-derivation, ablation status; explicit "still not estimable" reporting.
11. Secondary: M1 response unchanged on `parse.field.hit_rate`; tie counts.
12. Cost: LOW-MED - one deterministic oracle + analysis rerun; no new injections; ~1 day.
13. Effort: LOW-MED - new oracle script + analysis; no change to the frozen namespace.
14. Tautology risk: LOW - oracle structural, frozen before association.
15. Leakage risk: LOW.
16. Task-definition change: NO - defect repair.
17. NULL value: HIGH - even if M downstream remains non-estimable, a HIGH defect is closed and machinery becomes well-defined.
18. SANER relevance: MED-HIGH - concrete instance of "measurement objects must be causally aligned; aliased oracles are invalid observations".
19. Shared principle: one predicate is not two measurements; observation identity requires structural independence.

### PR-04 Cross-mechanism transfer (one new mechanism)

1. `PR-04 / MECH-TRANSFER`
2. `FACT`: every stage has exactly one frozen mechanism; `train_on_one_mechanism_test_on_another = NOT_IDENTIFIED`; status `MECHANISM_GENERALIZATION_NOT_IDENTIFIED` (mechanism audit JSON).
3. `FACT`: MVP design lists M2/R2/N2 operators as unimplemented; minimum required mechanisms per stage = 2, observed = 1 (mechanism audit; MVP-Audit F9).
4. `INFERENCE`: with one mechanism per stage, "stage-aligned observation generalizes" cannot be separated from "single mechanism is fingerprinted by its direct leaf".
5. Minimal intervention: implement ONE additional deterministic mechanism for ONE stage (first choice N2: operator/coefficient perturbation - deterministic arithmetic, zero model); freeze under the same discipline; evaluate A->B and B->A transfer on held-out clusters with frozen nearest-centroid + direct-codebook controls. If attempted on M, PR-03 de-alias is a prerequisite.
6. `INFERENCE`: if the stage signature fit on mechanism-A rows still predicts mechanism-B rows without directly targeting B, alignment is mechanism-general; otherwise it is fingerprint-bound.
7. Before: single-mechanism stage decoding.
8. After: cross-mechanism decoding (A->B / B->A) on the same measurement vectors.
9. Held-out: mechanism-level split + cluster-level LOCO (both frozen).
10. Primary: cross-mechanism macro-F1 / top-1 each direction vs chance/majority/direct baseline; direction consistency.
11. Secondary: within-mechanism reference; tie rates; cluster bootstrap CI.
12. Cost: MED - operator + freeze + run; sub-minute compute; ~1-2 days including audit.
13. Effort: MED - new mechanism operator + new-namespace freeze + runner variant.
14. Tautology risk: MED - extraction frozen before B rows observed; direct-codebook control mandatory; probe "trivially shared leaf".
15. Leakage risk: KEY RISK - mechanism<->cluster disjointness audited.
16. Task-definition change: NO - extends mechanism family of the same task.
17. NULL value: HIGH - a null directly bounds the flagship controlled result.
18. SANER relevance: HIGH - the replication step (Level 2 path) for the strongest existing positive.
19. Shared principle: separation of stage alignment from mechanism fingerprint.

### PR-05 Blind-family boundary replication

1. `PR-05 / BLIND-BOUNDARY`
2. `FACT`: OCR-like `0/13` blind across 11 clusters at all gamma; strength gradient post-hoc: edit-distance-2 duplication visible `8/8`, distance-1 absorbed `5/5`; "absorption region perfectly predicted" (T2 `prereg_predicates.E2_3`; SE118 §3).
3. `FACT`: only one blind family exists; the literal range predicate failed at gamma 0.7/0.9 (preserved, not silently repaired) (T2; protocol v2 §7).
4. `INFERENCE`: absorption boundary may be a deterministic function of pre-registered edit strength (mapping-loss boundary), generic rather than family-specific; current evidence is post-hoc and n=13.
5. Minimal intervention: freeze a 3-bin OCR-adjacent strength ladder (lev-1 / lev-2 / double-substitution) + one additional expected-blind control family (e.g., internal-whitespace OOV); generate on fresh held-out table clusters; preregister per-bin visibility predictions; run the frozen quantify pipeline (zero model).
6. `INFERENCE`: edits that preserve the canonicalization mapping are absorbed; edits that break matcher mapping become visible; boundary sits at mapping loss.
7. Before: `0/13` descriptive + post-hoc gradient.
8. After: preregistered out-of-sample visibility per bin + second control family, same frozen visibility rule.
9. Held-out: new clusters; predictions frozen before outcomes read.
10. Primary: monotonicity of visibility across strength bins; control-family rate.
11. Secondary: gamma-grid blindness replication; edit-distance predictor accuracy.
12. Cost: LOW-MED - generator reuse + new injections; zero model; ~1 day.
13. Effort: LOW-MED.
14. Tautology risk: MED - "monotone by construction" must be falsifiable: preregister bins and failure conditions.
15. Leakage risk: LOW - predictions frozen before results; disjoint clusters.
16. Task-definition change: NO.
17. NULL value: HIGH - an out-of-sample absorbed lev-2 kills the boundary rule.
18. SANER relevance: HIGH - converts the headline blind family from description to boundary law.
19. Shared principle: silent absorption boundary = mapping-loss boundary (generic, not family-specific).

### PR-06 Minimal-leaf pruning at equal diagnosability (cost axis)

1. `PR-06 / PRUNE-COST`
2. `FACT`: 8/12 leaves never respond on this construction; direct 3-leaf codebook already achieves 1.0; full-vs-direct `full_equals_direct_codebook: true` (ABL).
3. `FACT`: per-leaf MI table exists; cost proxies available (leaf check counts; judge call counts in config).
4. `INFERENCE`: zero-variance leaves carry no decision power in this construction; a pruned subset can preserve stage diagnosability at lower observation cost.
5. Minimal intervention: freeze a label-blind pruning rule (train-split response variance > 0 AND MI > epsilon; stage-aligned manual baseline as control); evaluate preserved diagnosability on LOCO held-out; report cost ledger (leaf checks, model/judge calls saved).
6. `INFERENCE`: information-theoretic - removing zero-information observations cannot reduce held-out decision power if rule is honest; the claim is COST-side.
7. Before: 12-leaf vector, cost C12.
8. After: k-leaf vector, cost C_k, same metric and splits.
9. Held-out: LOCO; prune rule frozen on train folds only.
10. Primary: non-inferiority of macro-F1/top-1; cost delta.
11. Secondary: tie rates; MI table; per-leaf deletion curve.
12. Cost: LOW - hours; seconds compute.
13. Effort: LOW - reuse `analyze_multileaf_signature_ablation.py` patterns.
14. Tautology risk: MED-HIGH caution - close to the existing ablation; must be framed strictly as cost-side; train-only pruning.
15. Leakage risk: prune on train, evaluate held-out.
16. Task-definition change: NO.
17. NULL value: MED - breakage of diagnosability under pruning is itself a fragility boundary.
18. SANER relevance: MED - extends to the observation-cost axis the user explicitly wants.
19. Shared principle: minimal-sufficient observation set.

### PR-07 Label-blind re-extraction bridge

1. `PR-07 / LABEL-BLIND`
2. `FACT`: v1 features are contract-derived; the surviving reviewer attack is exactly this; v2 delta lists label-blind extraction + non-degenerate signatures as required design corrections (V2DELTA §2.1-2.2; PACKET §4.1).
3. `FACT`: paired artifacts (216 rows) carry baseline/injected scores + contract checks; harness reruns in ~53 s; any config change requires a new prereg namespace (code-miner Q4).
4. `INFERENCE`: label-blind features re-extracted from paired raw artifacts either support stage decoding or they do not; the delta's rule makes the outcome reportable either way (NULL if full vector <= direct codebook).
5. Minimal intervention: new namespace; extractor reads only paired raw outputs (no stage/mutation labels); rerun discrimination + ablation on the 216 carriers; success rule per delta §4; explicitly non-confirmatory sensitivity run.
6. `INFERENCE`: removing label leakage from feature construction measures actual observation dynamics rather than injection labels.
7. Before: contract-derived features.
8. After: label-blind features on the same task.
9. Held-out: LOCO; delta requirement.
10. Primary: label-blind macro-F1 vs strongest codebook baseline; NULL rule per delta.
11. Secondary: ablation set (full/direct/non-direct); tie rates.
12. Cost: MED-LOW - extractor change + new freeze; sub-minute compute.
13. Effort: MED - new namespace + freeze + audit.
14. Tautology risk: MED - same corpus; non-confirmatory by construction; delta already defines NULL.
15. Leakage risk: DESIGN TARGET - extractor must be provably label-blind.
16. Task-definition change: NO (new namespace).
17. NULL value: HIGH - delta: report NULL if no incremental info.
18. SANER relevance: HIGH - directly answers the strongest surviving attack on the flagship result.
19. Shared principle: observation over labeling.

### PR-08 Tri-state missing-evidence cells

1. `PR-08 / TRI-STATE`
2. `FACT`: missing evidence is encoded `0` and counted separately, but fixtures do not exercise it; `missing_score` asymmetry is parse=0 / qa=5; Loop C filed MED incidents (`ripr-flags-emit-boolean-zero`, `missing-score-asymmetry`) (PRE §6; TREES; MVP-Audit I5, F10).
3. `FACT`: aggregate code has explicit degraded paths (F-J1) and records `_note`/`_n` per leaf (AGG lines ~179-187).
4. `INFERENCE`: explicit {response / no-response / no-evidence} semantics will change at least one decision class versus encode-0; direction and magnitude unknown.
5. Minimal intervention: recompute a bounded outcome table in tri-state from frozen inputs (where dropped/na leaves are recorded) + construct no-evidence fixtures; contract tests; report decision flips versus current policy.
6. `INFERENCE`: zero-conflation versus unknown is a policy choice with measurable consequences; the repair makes the choice explicit.
7. Before: 2-state encode-0.
8. After: 3-state with separate denominators and identification status.
9. Held-out: contract fixtures + cluster-split sensitivity.
10. Primary: flip rate of visibility/detection cells under policy; identification status of affected cases.
11. Secondary: bounds under policy space; test coverage counts.
12. Cost: LOW-MED.
13. Effort: LOW-MED - aggregate report layer + fixtures; days.
14. Tautology risk: LOW.
15. Leakage risk: none new.
16. Task-definition change: reporting object changes (disclosed; new namespace).
17. NULL value: HIGH - robustness is still a publishable property.
18. SANER relevance: MED - measurement hygiene supporting observation-surface validity.
19. Shared principle: non-identifiability must be represented, never zeroed.

## 2. Reserve / marginal entries (abbreviated)

- `PR-09` QA-layer read-through probe (silent-normalization repair): qa_arm note (12 rows) records model re-writing mutant tokens back to canonical names at the QA layer; a deterministic read-through leaf could re-cover that blind spot. Cost MED (new leaf + possible bounded model calls; resource plan required). Reserve because model-leg cost and small n.
- `PR-10` Absorption ledger + normalization-path audit: log where each absorbed injection dies (matcher normalization vs QA-layer normalization); preregister path features. MED cost; diagnostic that feeds PR-09. Reserve.
- `PR-11` Propagation instrumentation run: runner emits per-stage input/output hashes + first-visible leaf index in a new namespace; enables true propagation-depth quantification (currently NOT computable from frozen carriers - no intermediate states). Days of work; reserve behind PR-02.
- `PR-12` Judge->deterministic leaf replacement: judges have zero nonzero responses on the frozen corpora; needs a population where judge leaves fire (new data / production eval records, policy care). Reserve.
- `PR-13` Family visibility floor criterion: replace the failed range predicate with min-over-gamma floors. Marginal: metric-change-after-failure smell; acceptable only as an out-of-sample criteria test.
- `PR-14` Stable-k overwrite quirk (`stable` persists last threshold k=8 in the aggregate report while text says >=7): micro deterministic-contract item; verify intended semantics before touching anything. Hygiene, not a scientific repair.
- `PR-15` Construct ledger + denominator lint: machine-readable number->construct->denominator map + lint against cross-surface arithmetic. Governance artifact; complements Track A, not a repair experiment.

## 3. Eliminated with reasons

- `E1 FinQA scoring repairs` (any change to step-scoring semantics, deterministic-verifier replacement included): `BLOCKED-BY-POLICY` - V2-3 stop condition fired and "no new FinQA experiment is authorized"; official-operator application / v3 convention hunting explicitly closed (scorer feasibility §4-5).
- `E2 direct comparator probe` for OCR visibility (a comparator against the injected target): direct-codebook tautology; penalized class per user rules.
- `E3 trace completeness`: Stage E multileaf traces complete (216/216 retained); FinQA trace side closed. No repair target.
- `E4 stage-local evidence routing standalone`: subsumed by PR-02 (placement) and PR-06 (pruning).
- `E5 "add direct checkpoints" family expansions`: direct-codebook class; penalized.

## 4. Transparent multi-dim ranking (draft; final after Loop C)

Ordering dims: A scientific validity / B intervention isolation / C held-out evaluability / D low tautology / E low engineering cost / F SANER relevance / G shared-principle potential.

| ID | A | B | C | D | E | F | G | draft rank |
|---|---|---|---|---|---|---|---|---|
| PR-01 | High | High | High | Low-Med | Med | High | High | 1 |
| PR-02 | Med-High | High | High | Med | Low | High | High | 2 |
| PR-03 | High | High | High | Low | Low-Med | Med-High | Med-High | 3 |
| PR-04 | High | Med | High | Med | Med | High | High | 4 |
| PR-05 | High | Med-High | High | Med | Low-Med | High | Med-High | 5 |
| PR-07 | Med-High | Med | Med-High | Med | Med | High | High | 6 |
| PR-06 | Med | High | High | Med-High | Low | Med | Med | 7 |
| PR-08 | Med | High | Med | Low | Low-Med | Med | Med | 8 |

Penalty screen (user rules): no candidate requires direct-codebook repair, outcome-selected samples, oracle-target edits for gain, large executor rewrite, full dataset rebuild, or model training. PR-04/PR-05 carry the mechanism/construction coupling caveats noted above; PR-13 is explicitly marginal.

## 5. Status

- This round: mining complete; draft challenge set = PR-01..PR-08; Loop C fresh-context challenge = NEXT ACTION; final Top 3-5 to be selected after challenge verdicts (FAIL candidates removed).
- No experiment executed; no frozen artifact modified; commit/push NOT performed.
