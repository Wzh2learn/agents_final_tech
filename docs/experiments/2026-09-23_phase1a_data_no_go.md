# Phase 1a data-gate report — DATA_NO_GO

**Date:** 2026-09-23  
**Execution plane:** GB10 isolated worktree at `d351d7e`; no model, service, or business endpoint calls.  
**Status:** `DATA_NO_GO`. This is a valid research-gate result. It is not a failed experiment to be made green by rerunning. **Phase 2 was not started.**

## Expected inputs

The approved plan expects a provenance-complete, internally split development view and separately manifested validation layers:

- `logs/graph/eval/vgmc*_checkpoint.json` and the associated source tables/schema;
- `logs/graph/eval/dpo_pairs_v0.json` and checkpoint discrimination tables;
- proposal/train views grouped by `uid`, with a frozen internal `uid-dev` split;
- separate `gate-validation`, `sealed test`, and `future replay` manifests;
- correctness labels for `map_to`/`hold`, confidence provenance, licence/permission records, and an auditable injection map.

## Assets actually found

The read-only audit found 37 audit artifacts, 494 events with complete gain/collateral fields, 48 `uid`s, and 16 conflict groups. It also found 17 accepted targets that disagree with stored canonical references, 6 DPO pairs that reject reference-matching mappings, DPO `60/60` preference for `skip`, action-SFT/risk `DATA_NO_GO`, DPO `PILOT_ONLY`, and an empty training export. These are historical audit facts and provenance signals; they are not a training-ready label table.

The available internal split is hash-based (`uid % 5 == 0` for dev), with 10 dev and 38 train `uid`s and zero overlap. The split itself does not supply independent correctness. In the isolated VGMC path, `injected_tables.json` is present with the previously recorded SHA256, but `injection_map.json` is absent. The Phase 1a audit therefore recorded `independent_correctness_all_null=true` and did not emit baseline result numbers.

## Missing gates and permitted use

| Gate | Finding | Consequence |
|---|---|---|
| Source/schema completeness | Source tables and an auditable injection map are incomplete in the isolated input path | No corpus correctness or parser-to-label identity claim |
| Independent correctness | Correct `map_to`/`hold` labels are all null in the audited view | Action macro-F1, map/hold recall, harmful-action rate, useful coverage, and worst-family metrics are `UNMEASURABLE` |
| Licence/provenance | No accepted training licence and layer manifest were supplied with the audited labels | No training, tuning, or rule acceptance |
| Independent layers | No accepted disjoint gate-validation, sealed-test, and future-replay manifests | No generalization or gate calibration claim |
| Confidence | Confidence provenance and a missing-confidence policy are not established | `confidence-only` cannot be evaluated; gain/collateral cannot substitute for confidence |
| Statistical plan | Power, non-inferiority margin, and acceptance parameters are not approved for this gate | No inferential or non-inferiority conclusion |

Historical checkpoints, old accepted labels, DPO pairs, and rolling audit artifacts may be used for provenance and failure analysis only. They must not be re-split into training data, used to tune a rule, or used as a replacement for a sealed/test layer. Synthetic placeholders, duplicated historical events, and an existing test set reused as training are prohibited.

## Minimum supplement to leave DATA_NO_GO

| Item | Source/owner | Acceptance method | Dependency |
|---|---|---|---|
| Complete source tables, schema, and `injection_map` | Data owner | Immutable manifest, SHA256, parser-contract check | Needed before corpus identity can be checked |
| Independent correctness labels for `map_to`/`hold` | Research/labeling owner | Double review or equivalent provenance with adjudication record | Needed before action metrics are measurable |
| Licence and permission record | Data owner | Auditable layer manifest tied to hashes | Required for any train/tune use |
| Frozen proposal/train, gate-validation, sealed-test, future manifests | Loop D + research owner | Disjoint `uid`/hash check and recorded split rule | Required before any replay or generalization claim |
| Confidence provenance and missingness policy | Research owner | Field-level manifest plus explicit `UNMEASURABLE` rule | Required for confidence-only arm |
| Pre-approved power, non-inferiority, and safety parameters | Loop D/user decision | Decision record before rerun | Required for inferential gates |

Only after these items pass independent acceptance may Phase 1a be reconsidered as `PILOT_ONLY` or `GO`. Phase 2 remains `REPLAY_BLOCKED`; no empty baseline, placeholder result, or speculative paper number is valid.

## Evidence and boundaries

The non-formal Phase 1a audit trace is retained on GB10 at `/tmp/phase1a.stderr`; the A-2 and A-3 reports and raw traces remain under `/tmp` as execution evidence, not Git source. No model calls, endpoint calls, canaries, training, old receipt recomputation, or service restarts were used for this gate. The next permitted entries are data supplementation, a separately scoped A-2 expansion, or Loop C Lead governance/control-plane work.
