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

## Executable supplement contract

The repository now contains `research/phase1a_data_contract.py`, which converts the six missing-gate categories above into a deterministic, fail-closed package precheck. It reads only the supplied package directory, blocks Python socket entry points, does not import model/service clients, and reports only aggregate counts, hashes, gate errors, and the manual-review checklist. It never writes sample text into the report.

The package root must contain `phase1a_manifest.json`. Every artifact entry requires a unique `id`, one `role`, a package-relative `path`, exact byte count, and lowercase SHA-256. The eight required roles are:

| Role | Minimum contract |
|---|---|
| `source_tables` / `schema` / `injection_map` | Immutable inputs; their exact hashes must be bound into the parser receipt and licence record |
| `label_ledger` | JSONL with `sample_id`, `uid`, non-negative integer `col`, gold `map_to/skip/hold`, and at least two distinct reviewer identities; disagreement requires an independent adjudicator |
| `licence_record` | Accepted owner/time, all four permitted uses (`training`, `tuning`, `evaluation`, `rule_acceptance`), and covered-input hashes |
| `confidence_manifest` | Pre-verification field/source, exact `low/medium/high` vocabulary, `missing_policy=unmeasurable`, and no gain/collateral substitution |
| `analysis_plan` | Approved owner/time, `cluster_unit=uid`, finite alpha/power/non-inferiority margin, required primary metrics, and the exact layer-manifest hash |
| `parser_contract_receipt` | PASS receipt with checker, 40-hex commit, timezone-bearing execution time, and source/schema/injection-map hashes |

The manifest must bind the five disjoint layers `proposal_train.train`, `proposal_train.dev`, `gate_validation`, `sealed_test`, and `future_replay`. Every layer is non-empty and contains only `sample_id`/`uid` references; both sample IDs and UIDs must remain disjoint across layers. Private artifact bodies and the complete manifest remain outside Git.

The command has only two scientific-boundary outcomes:

- `DATA_NO_GO` (exit 2): at least one mechanical gate failed.
- `READY_FOR_INDEPENDENT_ACCEPTANCE` (exit 0): all seven mechanical gates passed, but licence authority, reviewer independence, analysis-plan approval, and parser execution provenance still require independent human/Loop review. This is never `DATA_GO`, training permission, or a paper result.

## GB10 acceptance after connectivity is restored

Do not run this block merely because GB10 is reachable. First confirm a clean isolated worktree at the reviewed commit and mount the private package read-only. Then run the exact scope below; replace only the package path and do not place reports in Git:

```bash
python3 -m py_compile research/phase1a_data_contract.py
PYTHONPATH=src python3 -m pytest tests/test_phase1a_data_contract.py -q

strace -f -e trace=connect -o /tmp/phase1a-contract-1.strace \
  python3 research/phase1a_data_contract.py \
  --package-root <GB10-private-package-root> \
  --output /tmp/phase1a-precheck-1.json

strace -f -e trace=connect -o /tmp/phase1a-contract-2.strace \
  python3 research/phase1a_data_contract.py \
  --package-root <GB10-private-package-root> \
  --output /tmp/phase1a-precheck-2.json

sha256sum /tmp/phase1a-precheck-1.json /tmp/phase1a-precheck-2.json
cmp --silent /tmp/phase1a-precheck-1.json /tmp/phase1a-precheck-2.json
```

Acceptance requires: 19 focused tests pass; both trace files contain zero `connect(` syscalls; the two JSON files are byte-identical; `endpoint_calls=0`, `socket_attempts=0`; all seven gates are `PASS`; and status is exactly `READY_FOR_INDEPENDENT_ACCEPTANCE`. Loop B/C or the designated reviewers must then independently verify the three manual-review items against the private originals. Any failed gate, non-determinism, network attempt, provenance doubt, or private-data leakage keeps `DATA_NO_GO`. Passing does not start Phase 1a, Phase 2, or training; those remain separately authorized execution steps.

## Evidence and boundaries

The non-formal Phase 1a audit trace is retained on GB10 at `/tmp/phase1a.stderr`; the A-2 and A-3 reports and raw traces remain under `/tmp` as execution evidence, not Git source. No model calls, endpoint calls, canaries, training, old receipt recomputation, or service restarts were used for this gate. The next permitted entries are data supplementation, a separately scoped A-2 expansion, or Loop C Lead governance/control-plane work.
