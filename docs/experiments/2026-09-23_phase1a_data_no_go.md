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
| Independent layers | No accepted disjoint gate-validation/sealed-test manifest and no future-replay batch or acquisition protocol | No generalization or gate calibration claim; no longitudinal evidence |
| Confidence | Confidence provenance and a missing-confidence policy are not established | `confidence-only` cannot be evaluated; gain/collateral cannot substitute for confidence |
| Statistical plan | Power, non-inferiority margin, and acceptance parameters are not approved for this gate | No inferential or non-inferiority conclusion |

Historical checkpoints, old accepted labels, DPO pairs, and rolling audit artifacts may be used for provenance and failure analysis only. They must not be re-split into training data, used to tune a rule, or used as a replacement for a sealed/test layer. Synthetic placeholders, duplicated historical events, and an existing test set reused as training are prohibited.

## Minimum supplement to leave DATA_NO_GO

| Item | Source/owner | Acceptance method | Dependency |
|---|---|---|---|
| Complete source tables, schema, and `injection_map` | Data owner | Immutable manifest, SHA256, parser-contract check | Needed before corpus identity can be checked |
| Independent correctness labels for `map_to`/`hold` | Research/labeling owner | Double review or equivalent provenance with adjudication record | Needed before action metrics are measurable |
| Licence and permission record | Data owner | Auditable layer manifest tied to hashes | Required for any train/tune use |
| Frozen proposal train/dev, gate-validation, sealed-test, plus future batch or acquisition protocol | Loop D + research owner | Namespaced lineage UID、root 与 independence-cluster 零交叉；future 空时检查 hash-bound protocol | 当前四层用于实验接收；future 空只限制长期主张 |
| Confidence provenance and missingness policy | Research owner | Field-level manifest plus explicit `UNMEASURABLE` rule | Required for confidence-only arm |
| Pre-approved power, non-inferiority, and safety parameters | Loop D/user decision | Decision record before rerun | Required for inferential gates |

Only after these items pass independent acceptance may Phase 1a be reconsidered as `PILOT_ONLY` or `GO`. Phase 2 remains `REPLAY_BLOCKED`; no empty baseline, placeholder result, or speculative paper number is valid.

## Executable supplement contract

The repository now contains `research/phase1a_data_contract.py`, which converts the six missing-gate categories above into a deterministic, fail-closed package precheck. It reads only the supplied package directory, blocks Python socket entry points, does not import model/service clients, and reports only aggregate counts, hashes, gate errors, and the manual-review checklist. It never writes sample text into the report.

The package root must contain `phase1a_manifest.json`. Every artifact entry requires a unique `id`, one `role`, a package-relative `path`, exact byte count, and lowercase SHA-256. The eight required roles are:

| Role | Minimum contract |
|---|---|
| `source_tables` / `schema` / `injection_map` | Immutable inputs; their exact hashes must be bound into the parser receipt and licence record |
| `label_ledger` | Canonical Q3 JSONL with exact fields `sample_id/uid/col/gold_action/gold_target/quality_grade/reviewers/adjudication`; at least two distinct reviewer identities, disagreement requires an independent adjudicator |
| `licence_record` | Accepted owner/time, all four permitted uses (`training`, `tuning`, `evaluation`, `rule_acceptance`), and covered-input hashes |
| `confidence_manifest` | Pre-verification field/source, exact `low/medium/high` vocabulary, `missing_policy=unmeasurable`, and no gain/collateral substitution |
| `analysis_plan` | Approved owner/time, `cluster_unit=lineage_uid`, distinct `significance_level`/`risk_limit`, target power/non-inferiority margin, frozen Holm family、seed×UID aggregation、threshold-selection rule、每角色×家族最低 UID、每个确认性对比的 MDE，以及 exact layer-manifest hash |
| `parser_contract_receipt` | PASS receipt with checker, 40-hex commit, timezone-bearing execution time, and source/schema/injection-map hashes |

The v2 manifest must bind `proposal_train.train`, `proposal_train.dev`, `gate_validation`, `sealed_test`, and `future_replay`. The first four are non-empty. `future_replay` may be empty only with a hash-bound `future_replay_protocol` that freezes acquisition time, source constraints, partition rule, and no-return contamination policy; the report then records `LONGITUDINAL_EVIDENCE_UNAVAILABLE` without blocking mechanical precheck. Every row has the exact lineage fields documented in `paper/dataset_protocol_v1.md` §6. `uid` is computed from `dataset_id + dataset_revision + lineage_root_id`; UID, lineage root, and `independence_cluster` are all checked for cross-layer overlap. Private artifact bodies and the complete manifest remain outside Git.

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

Acceptance requires: the current focused suite passes; both trace files contain zero `connect(` syscalls; the two JSON files are byte-identical; `endpoint_calls=0`, `socket_attempts=0`; all seven gates are `PASS`; and status is exactly `READY_FOR_INDEPENDENT_ACCEPTANCE`. Loop B/C or the designated reviewers must then independently verify the three manual-review items against the private originals. Any failed gate, non-determinism, network attempt, provenance doubt, or private-data leakage keeps `DATA_NO_GO`. Passing does not start Phase 1a, Phase 2, or training; those remain separately authorized execution steps.

## Phase 1a learnability probe after independent acceptance

`research/phase1a_learnability_baselines.py` is the repository-only runner for the five Phase 1a development baselines. Its presence does not start the probe. It refuses to run until all of the following are supplied outside Git:

1. the byte-exact `READY_FOR_INDEPENDENT_ACCEPTANCE` precheck report;
2. an `ACCEPTED_FOR_PHASE1A_LEARNABILITY` receipt binding the package-manifest, precheck-report, learnability-view, and preregistered-config SHA-256 values;
3. three recorded, distinct manual-review PASS identities for licence authority, label independence, and analysis/parser provenance;
4. one hash-bound JSONL view whose rows exactly match `proposal_train.train` and `proposal_train.dev` sample/UID references; and
5. a preregistered config fixing the lexical threshold, confidence policy, classifier hyperparameters, bootstrap seed/count, and decision policy before execution.

The JSONL view accepts only `sample_id`, `uid`, `observed_header`, `canonical_fields`, `candidate_target`, `confidence`, `gold_action`, `gold_target`, `quality_grade=Q3`, and `family`. Unknown fields are rejected. In particular, `gain`, `collateral`, `accepted`, `split`, and `partition` cannot enter the feature path. The runner derives the split only from the accepted package manifest, rereads the hash-bound canonical label ledger, and rejects any identity/gold/quality mismatch plus missing, extra, gate-validation, sealed-test, or future-replay samples.

The five arms are `always_skip`, exact normalized `deterministic_matcher`, preregistered-threshold `lexical_fuzzy`, frozen-policy `confidence_only`, and a deterministic CPU softmax `simple_classifier`. The classifier uses only header/candidate lexical similarity, exact-match indicators, candidate availability, confidence indicators, and bounded shape features. It does not use family, gold target/action, split identity, post-verification scores, accepted state, or learned rule state as features.

Reports contain aggregate train/dev metrics, worst-family aggregates, deterministic UID-cluster intervals, input/config/implementation hashes, and no row-level predictions or sample text. `harmful_map_rate` means incorrect map-to/all measurable samples; `map_to_risk` means incorrect map-to/all map-to predictions; `correct_map_coverage` means correct map-to/all measurable samples. Missing confidence is excluded as `unmeasurable`, never filled with zero. The only decisions are `SIMPLE_SUFFICIENT`, `LEARNABILITY_SIGNAL`, `NO_CLEAR_SIGNAL`, and `PILOT_ONLY`; all carry `training_authorized=false` and `paper_result=false`.

After the data package and receipt have been independently accepted and the user separately authorizes the development probe, run from a clean reviewed GB10 worktree. Replace placeholders only; keep reports and traces outside Git and outside the private package:

```bash
python3 -m py_compile research/phase1a_learnability_baselines.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_phase1a_learnability_baselines.py -q

strace -f -e trace=connect -o /tmp/phase1a-probe-1.strace \
  env PYTHONPATH=. .venv/bin/python research/phase1a_learnability_baselines.py \
  --package-root <GB10-private-package-root> \
  --precheck-report <phase1a-precheck-report> \
  --acceptance-receipt <independent-acceptance-receipt> \
  --config <approved-preregistered-config> \
  --output /tmp/phase1a-probe-1.json

strace -f -e trace=connect -o /tmp/phase1a-probe-2.strace \
  env PYTHONPATH=. .venv/bin/python research/phase1a_learnability_baselines.py \
  --package-root <GB10-private-package-root> \
  --precheck-report <phase1a-precheck-report> \
  --acceptance-receipt <independent-acceptance-receipt> \
  --config <approved-preregistered-config> \
  --output /tmp/phase1a-probe-2.json

sha256sum /tmp/phase1a-probe-1.json /tmp/phase1a-probe-2.json
cmp --silent /tmp/phase1a-probe-1.json /tmp/phase1a-probe-2.json
```

Software acceptance requires the focused synthetic suite to pass, both traces to contain zero `connect(` calls, and both reports to be byte-identical with `endpoint_calls=0` and `socket_attempts=0`. Scientific interpretation still occurs only after checking the approved thresholds, measurable denominators, family/UID support, and confidence missingness. `LEARNABILITY_SIGNAL` can justify asking for a later training window; it is not evidence that an 8B student is better. `SIMPLE_SUFFICIENT` stops escalation under the current plan.

## Evidence and boundaries

The non-formal Phase 1a audit trace is retained on GB10 at `/tmp/phase1a.stderr`; the A-2 and A-3 reports and raw traces remain under `/tmp` as execution evidence, not Git source. No model calls, endpoint calls, canaries, training, old receipt recomputation, or service restarts were used for this gate. The next permitted entries are data supplementation, a separately scoped A-2 expansion, or Loop C Lead governance/control-plane work.

## Correction addendum (2026-09-24, user rulings D0/D1 — append-only)

This section is an append-only correction authorized by user ruling D1. **It does not modify any text above and does not change the `DATA_NO_GO` conclusion**, which was re-confirmed on 2026-09-24 by exhaustive search (see `2026-09-24_phase1a_data_gate_reverification.md` §4). Where this addendum conflicts with the text above, **this addendum governs**.

### A. The required role count is 9, not 8

The “Executable supplement contract” above states “**The eight required roles are**” and lists 8. The machine contract `research/phase1a_data_contract.py` requires **9** (`REQUIRED_ROLES`, `:29-38`); the omitted one is **`learnability_feature_ledger`**.

Measured consequence of delivering exactly the 8 documented roles (real validator, otherwise-valid package, all other hash bindings intact): baseline with 9 roles = `READY_FOR_INDEPENDENT_ACCEPTANCE`, 7 gates PASS; with the documented 8 = **`DATA_NO_GO`**, `artifact_integrity` FAIL with `{"code": "missing_required_role", "role": "learnability_feature_ledger"}` and `{"code": "missing_or_mismatched_binding"}`, other 6 gates PASS. Evidence: `2026-09-24_phase1a_supplement_contract_role_gap.md`.

This role is **not** generated downstream: `phase1a_learnability_baselines.py` only imports the constants and its `_load_feature_ledger()` reads and hash-verifies a supplied file; a repo-wide search finds no generator. It must be supplied.

**`learnability_feature_ledger` constraints (nine, previously undocumented):**

| Constraint | Code | Fail code |
|---|---|---|
| Top-level key set exactly `contract_version` / `source_tables_sha256` / `schema_sha256` / `confidence_manifest_sha256` / `rows` | `:665-673` | `invalid_feature_ledger_fields` |
| `contract_version` exactly `phase1a-feature-ledger-v1` | `:24`, `:674-675` | `invalid_feature_ledger_version` |
| The three sha256 fields must each equal the actual hash of the same package's `source_tables` / `schema` / `confidence_manifest` artifacts (cross-role binding) | `:690-699` | `feature_ledger_source_hash_mismatch` |
| `rows` must be a non-empty list | `:700-703` | `invalid_feature_ledger_rows` |
| Each row's key set exactly `FEATURE_FIELDS` = `sample_id` / `uid` / `observed_header` / `canonical_fields` / `candidate_target` / `confidence` / `family` | `:82-90`, `:709-711` | `invalid_feature_ledger_row` |
| `canonical_fields` non-empty, elements non-empty strings, no duplicates; `candidate_target` if non-null must be a member of `canonical_fields` | `:714`, `:725-729`, `:736` | `invalid_feature_ledger_row` |
| `confidence` must be `null` or one of `low` / `medium` / `high` | `:730-734`, `:736` | `invalid_feature_ledger_row` |
| Each row's `sample_id` must belong to the `proposal_train` layer and its `uid` must match that sample's registered uid | `:704-708`, `:739-740` | `feature_ledger_identity_mismatch` |
| The row set must cover the `proposal_train` layer **exactly** (no more, no less) | `:741-742` | `feature_ledger_proposal_coverage_mismatch` |

### B. `analysis_plan` requires 18 keys; the row above names only 3 verbatim

Mechanically derived from the validator: 15 literal `analysis.get("...")` reads plus 3 loop-bound keys (`significance_level` / `target_power` / `risk_limit`, `:920-921`), minus 3 legacy keys that fail if merely present (`alpha` / `power` / singular `noninferiority_margin`, `:910`) = **18 required keys**.

Of those 18, the `analysis_plan` row above names **3** verbatim (`cluster_unit`, `risk_limit`, `significance_level`), describes **10** only in prose, and omits **5** entirely (`primary_metrics`, `one_sided_p_value_methods`, `holm_adjustment`, `minimum_uid_by_action`, `status`).

**The 18 required keys** (per ruling D7, `analysis_plan.json` is a separate in-package artifact from the §7 human freeze receipt):

`status` · `approved_by` · `approved_at` · `cluster_unit` · `significance_level` · `target_power` · `risk_limit` · `noninferiority_margins` · `primary_metrics` · `threshold_selection` · `seed_uid_aggregation` · `holm_families` · `one_sided_p_value_methods` · `holm_adjustment` · `minimum_uid_by_role_family` · `minimum_uid_by_action` · `mde_by_confirmatory_contrast` · `layer_manifest_sha256`

**Exact tokens the prose cannot convey:**

- `status` must equal exactly `approved` (`:912`)
- `cluster_unit` must equal exactly `lineage_uid` (`:918`)
- `threshold_selection` must equal exactly `proposal_dev_only` (`:940`) — per ruling D10 this token records **scope only**; the full selection rule is recorded separately as a rule field/note and machine-audited, not encoded in this token
- `seed_uid_aggregation` must equal exactly `fixed_seed_pair_then_uid_cluster_bootstrap` (`:942`)
- `holm_adjustment` must equal exactly `step_down_adjusted_p_and_simultaneous_one_sided_ci` (`:954`)
- `holm_families` must be a nested dict exactly equal to `REQUIRED_HOLM_FAMILIES` (`:99-108`); per ruling **D9** the RQ3 hypothesis name is unified to **`H3a_uid_any_harm`**
- `one_sided_p_value_methods` must be an exactly-5-key dict with verbatim values (`:946-953`)
- `noninferiority_margins` must be a nested dict whose key set is exactly `{delta_quality, delta_harm, delta_retention}`, each in `[0,1)` (`:924-935`) — **not** the flat `delta_*` fields of the §7 receipt
- `primary_metrics` must include `{action_macro_f1, harmful_map_rate}` (`:936-939`)
- `minimum_uid_by_action` key set must be exactly `{map_to, skip, hold}`, values `int >= 2` (`:962-968`)
- `minimum_uid_by_role_family` non-empty dict, values `int >= 2` (`:956-961`)
- `mde_by_confirmatory_contrast` key set exactly `REQUIRED_MDE_CONTRASTS` (derived from the Holm families, `:110-114`), values in `(0,1)`
- `layer_manifest_sha256` must equal the digest of the manifest's `layers` object (`:976`)

Per ruling **D11**, `minimum_uid_by_action` / `minimum_uid_by_role_family` must also agree with the learnability config's `min_dev_uids_by_action` / `min_dev_uids_by_family` / `min_dev_uids`; a cross-artifact consistency check is being added, and disagreement must fail.

### C. Runbook command corrections (both command blocks above)

Measured on GB10: of the 10 documented command lines, **6 fail when run verbatim** — 5 with rc=127 because **`.venv/bin/python` does not exist** (the real path is `venv/bin/python`, no leading dot), and 1 with rc=1 because **bare `python3` has no pytest**. Evidence and per-line exit codes: `2026-09-24_phase1a_phase2_runbook_command_defects.md`.

Corrected forms (all verified by execution):

```bash
# In an isolated worktree the venv/ directory does NOT exist; use the absolute
# production interpreter path (safety-gates doc §6.2). In a production checkout,
# venv/bin/python also works.
PY=~/wzh/projects/agents_final_tech/venv/bin/python

python3 -m py_compile research/phase1a_data_contract.py                    # rc=0 (unchanged)
"$PY" -m pytest tests/test_phase1a_data_contract.py -q                     # rc=0, 31 passed
"$PY" -m pytest tests/test_phase1a_learnability_baselines.py -q            # rc=0, 29 passed
"$PY" research/phase1a_data_contract.py --package-root <pkg> --output <o>  # rc 0/2 is business semantics
```

Also: `PYTHONPATH=src` is **unnecessary** for every command above (nothing in `research/` or these tests imports `src`), and it puts production service modules on the import path during runs whose central claim is zero-endpoint — it is removed. `PYTHONPATH=.` is required **only** for `research/paper_result_views.py`. **All documented CLI flags were verified correct and must not be changed.** Note that `rc=2` from `phase1a_data_contract.py` is its documented `DATA_NO_GO` exit code, not a failure.

Before running any test in a fresh isolated worktree, copy production's whole `data/` tree and verify per-file sha256 (safety-gates §6.2). The worktree otherwise lacks 8 gitignored fixtures, which produces 4 spurious `FileNotFoundError` failures **and one silent skip** (`tests/test_drift_inject.py:151`) — so a baseline must pin `passed` **and** `skipped` counts, not merely "zero failures".

### D. Gate 1 re-verified: two roles already exist; the `schema` candidate is rejected

The gate-1 finding above is scoped “in the isolated input path”, and that scoping matters: the audit ran inside isolated worktree `agents_final_tech_accept_d351d7e` (trace path frequencies 36 vs 9 for production). Production **does** have both artifacts gate 1 names:

| Role | Production path | Bytes | sha256 |
|---|---|---|---|
| `source_tables` | `data/research/drift_v0/input/tatqa_tables.json` | 1 442 890 | `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` |
| `injection_map` | `data/research/drift_v0/output/injection_map.json` | 36 004 | `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e` |

The injection map is complete and auditable: `meta` = `{deterministic: true, input: tatqa_tables.json, ratio: 0.3, seed: 42, version: v0}`; `mapping` = **118** entries over **95** distinct uids with entry keys `col/injected/original/row/seed_component/source_key/type/uid/variant` — matching the documented Stage E “95 tables, 118 controlled injections”.

The only `schema` candidate found, `~/wzh/m1_samples/m1_table_schema.json` (14 253 B, sha `79bc3a17f6285e2b6071b5e8a3df5ae3927ce049f1d31c016c16e0a628ce9a3b`), is **rejected**: its 5 table identifiers are 4/5 CJK while the corpus's 2479 identifiers contain zero CJK, and identifier overlap is 0 against all three corpus artifacts. Different domain. Per ruling D1 it must not be reused.

**Therefore the external supplement ask is 7 roles + 1 package root**, with no remaining availability judgments:

- Already in production, hash-bindable, **not** to be re-delivered (2): `source_tables`, `injection_map`
- Must be produced (7): `schema`, `label_ledger`, `licence_record`, `confidence_manifest`, `analysis_plan`, `parser_contract_receipt`, `learnability_feature_ledger`
- Plus (1): the package root `phase1a_manifest.json`, which does not exist anywhere on GB10

### E. `DATA_NO_GO` unchanged, and now confirmed more strongly

Gates 2–6 were re-verified by exhaustive forward search rather than inherited: `gold_action`, `label_ledger`, `confidence_manifest`, `parser_contract_receipt`, `analysis_plan`, and `phase1a_manifest` all return **0 hits** across production `data/`, `logs/graph/eval/`, `~/wzh/datasets`, `~/wzh/m1_samples`, and `~` (maxdepth 6, excluding `venv/` and `skills/`). The injection map carries **none** of `LABEL_FIELDS` — it is perturbation ground truth, not independent correctness labels, which require ≥2 independent reviewer identities plus adjudication.

⇒ **`DATA_NO_GO` stands.** Gate 1's evidence basis was environment-scoped and is corrected above; the decisive gate (independent correctness) is confirmed absent machine-wide.
