# FinQA Face — Evidence-Mining Report for Track P Candidate Mining

> Miner: `/root/miner_finqa` (read-only) | Repo: `D:\AIRcommend\JinRongAgents\agents_final_tech` (LOCAL @ `eae2688`; GB10 checkout read-verified) | 2026-10-11
> Process note: this thread was bootstrapped with the parent's context (compaction mix-up); identity re-verified (interrupt guard: "cannot interrupt itself" + own transcript). This is the FinQA-face mining deliverable for the Track P candidate pool; sibling reports (stage E, code) were delivered by their own threads.
> Compliance: zero endpoint/model/database/service/training calls; read-only file + log inspection (incl. GB10 ssh reads of run logs); single staging write = this file (plus `stage_e_mining_report_v1.md` saved earlier in the same folder).

**Source handles** (repo-relative unless noted): `AUTOPSY` = docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md · `LINEAGE` = docs/research/finqa_v2_asset_lineage_v1.md · `GATES2` = docs/research/finqa_v2_gate_reconciliation_v2.md · `RCOMP` = docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md · `PROPOSAL` = docs/research/finqa_causal_exposure_preregistration_proposal_v1.md · `CCHAL` = GB10 run log `/home/testuser/wzh/loop_runs/finqa-causal-exposure-challenge-c-20261010/c.log` (status done, rc 0, 2026-10-10T15:31:37Z) · `CARD` = research/finqa_causal_exposure_20261010/FINQA_CAUSAL_EXPOSURE_LATER_EXECUTION_TASK_CARD_NOT_EXECUTED.md · `MVP` = docs/experiments/2026-10-11_loop_c_causal_checkpoint_mvp_design_audit.md · `MC` = miner_code report (sibling) · `SL` = paper/saner_rene_manuscript_scope_lock_v1.md.

## 1. FACT INVENTORY

### 1.1 Execution lineage (11-node, hash-bound; `LINEAGE`)
- Invalid run #1: fail-closed `artifact_sha256_mismatch` 89/89; V/D/O null; 0/10,000 bootstraps — `INVALID_BUT_PRESERVED`, no scientific claim.
- binding_v2: repaired the raw/normalized binding seam (historical engineering contract only).
- Invalid run #2: `BINDING_TRACE_MISMATCH` 89/89 — `INVALID_BUT_PRESERVED`.
- binding_v3: 89/89 runtime bindings + 420/420 trace matches; zero scientific outputs before formal run.
- End-to-end preflight: 89/89 bindings, 420/420 trace rows, 30/30 groups, 14 hash bindings; authorized no result by itself.
- Formal v3 result: `SECOND_FLOW_MIXED`, V=89/89, D=0/89, O=0/89 — recompute PASS: 56/56 estimands, 10,000/10,000 bootstraps match; `P(D=1|V=0)` `NOT_IDENTIFIABLE` (valid=0 / failed=10000); `detection_rate_given_visibility_positive` [0,0] `DEGENERATE` (`RCOMP` §1, §8).
- Scientific autopsy: `MEASUREMENT_OBJECT_MISMATCH` accepted (`ACCEPTED_METHODOLOGICAL_BOUNDARY`); formal counts not rewritten.

### 1.2 Why the negative is a mismatch (mechanism, not blindness)
- V observes source/local field changes; D consumes downstream `res`/`answer` fields that were never recomputed: frozen P/N artifacts copy `steps`, then write only `op` or `arg`; `answer = str(steps[-1]["res"])`. Consequence: for P/N, `step_result_consistency = 0` and `answer_consistency = 0` **by construction** → D ≡ 0; V = 1 forced by every instantiated operation; D fields are a structural subset of the V field set → cell (V=0, D=1) structurally empty, and the V×D "relationship" has no estimable contrast (`CCHAL` F1–F3, I1).
- Old step-reexecution line is `STOPPED_BY_PRE_REGISTERED_V2_3`; percent fidelity 44/1478 = 0.0298 and 330/1478 = 0.2233 (threshold 0.5); numeric mismatch 518/3096 ≈ 0.1696 (`PROPOSAL` §feasibility; `CCHAL` F4). Step re-execution is not identifiable from public metadata alone.
- Re-execution silently redefines the referent of `res`/`answer` (dataset-serialized gold → executor-derived), while the object name stays fixed; the exact clean-replay gate is load-bearing and currently unsatisfied (`CCHAL` I3).
- Official FinQA execution code is not staged; the approved staging contains only `finqa/train.json` and `finqa/dev.json` (`CCHAL` F5).

### 1.3 Six gates, canonical reconciliation (`GATES2`; `FORMAL_FINFQA_V2_GO = NO`, overall `SECOND_FLOW_BLOCKED`)
| Gate | Status | Boundary |
|---|---|---|
| `SOURCE_GO` | `PASS_SOURCE_IDENTITY_AND_HASHES` | byte + SHA-256 bound; not execution authorization |
| `ID_GO` | `PASS_CANDIDATE_IDS_FROZEN_NOT_EXECUTION` | E/P/N IDs frozen outcome-blind; not execution |
| `JOIN_GO` | `PASS_RESOLVER_AND_CANDIDATES_NOT_FORMAL` | lexical unique-evidence join only; not native provenance or semantic evidence use |
| `SPLIT_GO` | `BLOCKED_SPLIT_ROLE_NOT_FROZEN` | train/dev/test/sealed/gate/eval roles unfrozen |
| `SCORER_GO` | `PROTOTYPE_PASS_NOT_FROZEN` | scorer v2 passes 5/5 tests; exact artifact linkage + pre-result freeze missing |
| `PREREG_GO` | `BLOCKED_PENDING_SPLIT_GO_AND_SCORER_FREEZE` | sequencing dependency |

Machine counts: 7,134 records (6,251 train / 883 dev); 10,960 steps; 2,894 multi-step; 3,818 `#k` refs (0 forward / 0 out-of-range); 65 raw op tokens. Result forms: numeric 6,841 / percent 3,980 / boolean 132 / other 7. Join feasibility: 6,794 rows with ≥1 unique join; 627 multi-step clusters with unique join; candidate manifest: E/P/N = 24 clusters × 72 injections each; eligible-after-stage-disjointness 594 / 526 / 553; the `627 vs 594` relation is `NOT_YET_RESOLVED`.

Frozen machinery: scorer v2 measures "paired clean/mutant checkpoint observation reproduction" over 5 fields (`evidence_required_hit`, `operator_consistency`, `argument_consistency`, `step_result_consistency`, `answer_consistency`); stdlib-only; `semantic_correctness_claim = false`. Resolver v2 = deterministic lexical uniqueness; fails closed; 3/3 tests; explicitly not provenance.

### 1.4 Causal-exposure proposal (frozen design) + Loop C challenge verdict (`PROPOSAL`, `CCHAL`, `CARD`)
- Proposal state: `PROPOSAL_FROZEN_NOT_EXECUTED`; `EXECUTOR_FEASIBILITY_CONDITIONAL`; `MOTHER_POOL = 7134`; clean-replay gate (5 conditions) + propagation gate (5 conditions); E = `NOT_CAUSALLY_EXPOSED_TO_D`; P/N = candidate causal exposures conditional on executor replay; controls A/B/C structurally segregated; stop conditions active.
- Loop C challenge verdict: **`BLOCKED`** — "**D is not a defined variable**": U-A (legal P/N mutation grammar), U-B (exact serialization/equality rule), U-C (terminal-answer derivation) are unfrozen; "an undefined outcome cannot be preregistered".
- Independent objections: (1) V side is tautological/structurally degenerate (forced V=1, no V×D contrast); (2) D conflates causal propagation with executor error/serialization choice unless exact clean replay holds (which available semantics fail at scale); (3) re-execution redefines the measurement object *silently* and the eligible population is gold-agreement-selected (historical faithful coverage ≈ 16.3%–23.7% in a comparable corpus; `CCHAL` I4).
- Safe final RQ given by challenge: a **mutation-propagation rate under a reconstructed executor**; V reportable only as manipulation check; never claim a visibility–detection relationship, protocol detection, or generalization; do not reopen v2-3; do not merge with the old `FAILED TRANSFER DUE TO MEASUREMENT-OBJECT MISMATCH` string.

### 1.5 Cross-face blockers from the causal-checkpoint MVP design audit that touch FinQA-derived repairs (`MVP`; corroborated by `MC`)
- Filed incidents (pattern-named): `aliased-checkpoint-pair-labelled-as-distinct-oracles` (HIGH) — `parse.table.regression` ≡ `parse.field.hit_rate`, byte-identical predicate; `downstream-response-asserted-by-map-not-dependency-path` (HIGH) — downstream class from a static dict, `NO_RAW_STATE_PROOF`; `execution-confirmed-edge-relation-label-not-matching-carrier` (HIGH); `missing-score-asymmetry-converts-nonidentifiable-to-full-marks` (MED; qa=5 vs parse=0); `ripr-flags-emit-boolean-zero-instead-of-not-identifiable` (MED); `decision-rule-specified-but-not-implemented` (MED; MINIMUM gate has no code); `execution-confirmed-edge-citation-is-definition-only` (MED).
- Operators M2/R2/N2 are unimplemented; 8/12 checkpoint columns are dead zeros; `METHOD_DATASET_READY = BLOCKED`; `SANER_MVP = CONDITIONAL`; single blocker = the SOURCE_LOCAL vs DOWNSTREAM partition is not well-defined for M.

## 2. MECHANISMS — failure taxonomy on this face (and where repair is admissible)
1. **Undefined referent** (D over un-recomputed fields; referent drift under re-execution). Repair admissible only with a frozen executor contract; not metric-side.
2. **Structural degeneracy** (D ⊆ V; V forced; empty cells; `NOT_IDENTIFIABLE` pre-closed). Repair = object separation + honest estimand list (challenge's safe RQ), not new contrasts.
3. **Gold-agreement selection** (eligibility conditioned on exact clean replay). Repair = strata visibility + denominator discipline, without relaxing the gate.
4. **Construction invariants presented as findings** (V1D0 corner). Repair = explicit construction-invariance accounting.
5. **Asserted vs recorded causality** (hardcoded stage→leaf map; byte-identical aliases; no dependency path). Repair = dependency-derived partition/instrumentation with a recorded path (this is where a small Track P experiment is actually possible).

Admissibility boundary: closed lines = FinQA v2-3, invalid runs, formal-v3 counts, frozen artifacts. Open-but-unauthorized = executor contract, split/scorer freezes, new pre-registration. Track-P-admissible without new scientific authority *if approved as a small experiment*: repair experiments that reuse frozen inputs under a new namespace and fail closed (F1, F5).

## 3. CANDIDATE REPAIR SEEDS (F-series; fields per Track P contract)

**F1 [observation placement / propagation-aware instrumentation / direct–non-direct restructuring] — Dependency-path-based partition repair (de-alias the M pair; make SOURCE_LOCAL vs DOWNSTREAM well-defined).** *NOMINATE FOR TOP POOL.*
- Base (FACT): MVP single blocker + incidents above; `MC` Q2 code reading: both M response bits = `int(mutated_hit < baseline_hit)` (byte-identical); 8/12 columns dead zero; multileaf runner is deterministic, sub-minute, zero-endpoint.
- Intervention (one design factor): replace the hardcoded stage→leaf alias map with a **recorded, frozen dependency path** derived from production code semantics (mutation target → pipeline states → leaf predicate), and replace the M-pair alias with a downstream object computed through the production path (not a copy); fail closed if no non-identity path exists for a stage.
- Held-out: derive/freeze the partition rule on half the stage-namespaced clusters; evaluate partition well-definedness + non-alias (downstream differs from source-local under ≥1 neutral variant) on the held-out half; then full-population rerun as replication. New prereg namespace + freeze receipt; frozen v1 artifacts untouched.
- Metrics: primary = fraction of stages with well-defined, non-aliased partition; secondary = dead-zero column count; downstream estimability flag.
- Tautology: LOW (path derived from code, frozen pre-outcome; no outcome-driven wiring). Cost: LOW–MEDIUM (config + analysis; ~1 min compute; real cost = freeze/audit ≈ 1–1.5 days; zero model calls).
- If NULL: informative — "no non-identity downstream object exists in the current pipeline" becomes explicit boundary evidence (strengthens SANER's story; converts the MVP blocker into a documented boundary rather than an ambiguous block).
- SANER relevance: HIGH. Cross-merge: extends stage-E S8 + code seed (f); directly defuses `aliased-checkpoint-pair…` and `downstream-response-asserted-by-map…`. NOT a relaunch of the MVP — single-defect repair, usable as boundary evidence if it fails.

**F2 [measurement-object separation / deterministic contract replacement] — "D-defined" executor contract for a bounded operator subset.** *POOL-CONDITIONAL; not first batch.*
- Base: `CCHAL` primary blocker; 10 missing contract items (`PROPOSAL` §missing contract); official executor not staged; fidelity fail (F4).
- Intervention: hash-bound contract for top-k operator families + exact serialization/equality + terminal-answer derivation; clean-replay run; declare admitted-subset denominator.
- Held-out: operator families excluded from contract construction must fail closed; evaluate only records whose ops ⊂ admitted set; report `eligible/7134`.
- Tautology LOW; cost MEDIUM–HIGH; NULL informative. **Explicitly reopens a stopped line → requires separate user re-authorization; do not auto-start.**

**F3 [causal alignment / evidence routing] — Deterministic evidence-to-argument extraction stage (E-arm causal exposure).** *DESIGN-ONLY.*
- Base: E is `NOT_CAUSALLY_EXPOSED_TO_D` under fixed gold path; frozen join is lexical-uniqueness only; proposal states a deterministic evidence→argument extractor "would be a different pipeline and would require a new reviewed contract".
- Intervention sketch: frozen extractor maps evidence content → program arguments, enabling recomputation to reach D; held-out on argument forms (`#k` refs vs literals vs percent). Tautology MEDIUM (risk of constructing the path to force exposure). Cost MEDIUM–HIGH. New reviewed contract required.

**F4 [threshold/support identifiability] — Fidelity-stratified support reporting for the future causal-exposure run.** *CAN BE FROZEN NOW, EXECUTES LATER.*
- Base: eligibility conditions on exact clean replay → selection on a gold-labeled quantity; historical faithful coverage 16.3%–23.7%; challenge objection 4.
- Intervention: freeze strata edges (exact / numeric-near / unresolved) computed from one clean-replay pass; primary estimand still exact-gate; strata reported separately so support is visible; no denominator shrinking.
- Held-out: freeze edges on a design split, report on dev split; recompute on next dataflow. Tautology LOW. Cost LOW (spec now; execution once executor exists). NULL: strata degenerate → object structurally defective (publishable boundary). Cross-merge: same family as stage-E S6.

**F5 [missing-evidence instrumentation] — Fail-closed form-coverage channel for terminal answers (percent / boolean / other=7).** *CHEAP CONTRACT REPAIR.*
- Base: result forms numeric 6,841 / percent 3,980 / boolean 132 / other 7; terminal-answer derivation for percent/boolean/other unspecified; fail-closed preference is project policy.
- Intervention: frozen form-coverage table + exclusion codes; tri-state evidence channel (present / absent / unresolved), never guessing; contract tests.
- Held-out: contract-test fixtures; next dataflow form set. Tautology N/A–LOW; cost LOW. Cross-merge: FinQA instance of stage-E S9.

**F6 [evidence routing / writing guard] — V×D containment lint.** *TOOLING, not an experiment.*
- Base: D ⊆ V structural; several surfaces still show relationship-style language as a risk.
- Intervention: machine lint that fails any draft claim of a visibility–detection "relationship/transfer" on FinQA-derived material; require propagation-rate language; V as manipulation check only. Cost LOW; no science. Cross-merge: stage-E S10.

## 4. OPEN QUESTIONS / LIMITS
1. `627 vs 594` eligibility-chain relation `NOT_YET_RESOLVED` (`GATES2` §4).
2. Split roles, scorer freeze, exact artifact linkage, new pre-registration: all still unfrozen; no execution authorized.
3. Executor contract has ≥10 missing items; clean replay never run at scale; terminal-answer forms (percent/boolean/other) undefined.
4. No second dataflow currently qualifies beyond design-only; cross-dataflow replication of any repair is not yet possible.
5. This mining did not mutate or re-run any FinQA artifact; no JSONL row-level audit was redone (relies on hash-bound receipts); GB10 reads were limited to run logs/status.

## 5. INTEGRATION HINTS FOR ROOT
- Only **F1** is a first-batch-viable FinQA-derived experiment under Track P rules (cheap, deterministic, held-out-able, informative NULL); it also directly targets the MVP's single blocker and the two HIGH incidents, so it doubles as boundary repair for SANER.
- F2/F3 need new authorization and are not first-batch; F4 should be frozen as spec now and bound to any future executor run; F5/F6 are cheap complements.
- Negative-form shared principle across faces (INFERENCE, for synthesis step only, not a claim): Stage E (direct-codebook ablation 1.0), MVP (hardcoded map + byte-identical alias), FinQA (D ⊆ V + un-recomputed referents) all fail the same way — **the observation/detection object was never made well-defined; results inherit the object defect.** A positive shared principle requires at least one successful repair (F1 is the cheapest test of it).
