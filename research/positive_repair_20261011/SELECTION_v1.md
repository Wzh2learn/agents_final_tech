# Track P Selection v1 — First-Round Experiment Set

> Status: `FINAL_SELECTION_FOR_USER_APPROVAL` | 2026-10-11 | Loop C challenge incorporated | NO experiment executed
> Loop C challenge: task `positive-repair-challenge-c-20261011` via `scripts/graph/loop_ac_launcher.sh`; rc=0; 2026-10-11T05:36:45Z → 05:42:24Z (~5m40s); packet sha256 `93151e01…`; output `loop_c_challenge_result_raw.log` (18,806 B, sha256 `3ea95284…`).

## 1. Challenge verdicts (Loop C, fresh context, packet-only, read-only)

| ID | Verdict | Key condition / reason |
|---|---|---|
| PR-01 | REVISE | Fix the score functional's evaluation point (pre/post-canonicalization) + frozen feasibility gate; keep original 2,382-row identifiability reported separately so E2's population is not silently replaced. |
| PR-02 | REVISE | Non-confirmatory label (decay hypothesis derived from E3 on the same carriers); numeric falsification thresholds before running; leaf-level vs node-level metric objects declared non-comparable. |
| PR-03 | REVISE | Predeclare pre/post non-comparability (conclusion-level deltas only, no F1 deltas); identical-column check demoted to sanity gate; E6 namespace+freeze+audit inside the cost estimate. |
| PR-04 | REVISE | Preregister N2 selection rationale (determinism/cost-based); minimum visibility floor for mechanism-B so transfer-NULL is not confounded; explicit responsive-leaf-set overlap report A vs B. |
| PR-05 | REVISE | Bins defined solely by generator parameters (never by observed score/distance-to-visible); absolute per-bin rate predictions with numeric failure thresholds; scope "generic effect" claim unless a second loss-type control family is added. |
| PR-06 | **FAIL** | At E3's 1.0 ceiling (direct 3-leaf codebook already 1.0) non-inferiority is definitionally near-guaranteed; expected NULL uninformative; cost benefit unquantified/plausibly immaterial. Removed from round 1; re-file as cost-ledger derivation from E3 or replace with a headroom design. |
| PR-07 | REVISE | Specify blind pair construction (extractor cannot infer which pair member is mutated); v1-vs-v2 F1 non-comparable; source-leaf feature attribution required. |
| PR-08 | KEEP | Best first-round backup (Loop C). |

Loop C ranking: **PR-03 > PR-05 > PR-07 > PR-04 > PR-01**; backup PR-08; PR-02 second-round; PR-06 out.

Strongest cross-cutting objection (accepted): **shared-evidence-base circularity** — six of eight candidates recycle the same frozen carriers; only PR-05 (fresh clusters) and PR-04 (new mechanism) escape it. The first-round claim set must therefore be framed as "repairs plus one out-of-sample replication".

## 2. Loop D final decision (first round = 5; for user approval)

Approval IDs (execution would require user approval; nothing is authorized yet):

1. `PR-EXP-03` ← PR-03 M-stage oracle de-alias (instrument repair of a filed HIGH defect).
2. `PR-EXP-05` ← PR-05 Blind-family boundary replication (fresh-cluster out-of-sample replication).
3. `PR-EXP-07` ← PR-07 Label-blind re-extraction bridge (adjudicates the surviving reviewer attack; non-confirmatory).
4. `PR-EXP-04` ← PR-04 Cross-mechanism transfer, N2 first (mechanism-level out-of-distribution test).
5. `PR-EXP-01` ← PR-01 Clean-support null-mutation panel (repairs the headline identifiability blocker; gated by Loop C's feasibility condition).

- Backup: `PR-EXP-08` (PR-08, KEEP) — activated if PR-01's feasibility gate fails.
- Second-round: PR-02 (placement/distance) — after first-round out-of-sample evidence exists.
- Removed: PR-06 (FAIL).
- Each REVISE condition must be folded into that experiment's own prereg BEFORE freezing; no shared vague prereg.

## 3. Diversity check (user requirement: not 5x the same repair)

- Stages: M (PR-03), N via N2 (PR-04), cross/construction (PR-07), family-level (PR-05), threshold/support (PR-01).
- Objects/failure families: aliased oracle; OCR blind family; label-leaky features; single-mechanism fingerprint; clean-support degeneracy.
- Mechanisms: instrument replacement; new-injection replication; extractor repair; new mechanism + transfer; control-panel construction.

## 4. Evidence-ladder status

- Current portfolio level: `LEVEL_0` (audit findings only). This round's goal was to open `LEVEL_1` candidates; the selected set includes two built-in out-of-sample faces (PR-04, PR-05).
- Synthesis gate (>=3 C-audited positives, >=2 stages/mechanisms): NOT met; no synthesis inquiry launched.
- Shared-principle seed (`INFERENCE` only, not a claim): "the object was never made well-defined; results inherit the object defect" — Stage E (direct-codebook 1.0), MVP (alias + hardcoded map), FinQA (D⊆V, un-recomputed referents) fail isomorphically. Verifying this principle requires >=1 successful repair first; the cheapest test is the de-alias repair (PR-03).

## 5. FinQA-face integration (miner_finqa report, 2026-10-11)

- `F1` Dependency-path-based partition repair == PR-03 scope (de-alias M pair + recorded dependency path); nominated and merged into PR-03.
- `F2`/`F3` (executor contract / deterministic evidence→argument extraction): POOL-CONDITIONAL, second wave, need separate re-authorization; NOT in round 1.
- `F4` fidelity-stratified support reporting (freeze spec now), `F5` fail-closed form-coverage channel, `F6` V×D containment lint: cheap complements; merge with PR-08 family / governance items.
- FinQA closures honored: no change to step-scoring semantics; no v2-3 reopening; safe RQ = mutation-propagation rate (proposal-level only).

## 6. Process incidents (recorded, no artifact lost)

- Subagent bootstrap identity mix-up: `miner_code` and `miner_finqa` were bootstrapped with parent context; `miner_code` self-recovered and delivered; `miner_finqa` was interrupted twice and re-anchored, delivered a full report at the end; `miner_stage_e` self-recovered.
- `apply_patch` tool channel malfunctioned this session (double-escaping; even minimal patches rejected) → round artifacts were written via controlled shell writes (UTF-8, no BOM); content integrity verified by size/hash checks.
- Loop C observed a session-hook magic-keyword false positive (`ai-slop-cleaner`) and correctly did not invoke it on this read-only task.