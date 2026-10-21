# LC-RESEARCH-001-OFFLINE - offline evidence map: 7 missing Phase 1a roles + package root

- Card: `LC-RESEARCH-001-OFFLINE` (Mode: RESEARCH; zero endpoint, zero model, zero network, calls=0)
- Date: 2026-09-24 (CST)
- Author / executor: Loop D main thread (relay). Why Loop D and not a Loop C model session: see section 7.
- Inputs read at commit `1627a54` (main), read-only.
- Execution worktree: `/home/testuser/wzh/projects/agents_final_tech_lc_research`, branch `gb10/lc-research-20260924`.
- Deviation (recorded, not silent): the card names worktree `.../agents_final_tech_loop_c`. That branch head (`dc20ab1`) is **57 commits behind main** and does **not** contain this card's own inputs (the 2026-09-24 correction addendum of the DATA_NO_GO report; preregistration section 7.1). Merging main into it conflicts in `docs/INDEX.md` (3 main commits touched that path), which would put unrelated conflict resolution inside a research card. A fresh worktree at main was therefore used; the named branch was left untouched (no merge, no reset, no destructive git command).
- GB10-side calls=0 evidence: `strace -f -e trace=connect` over the verification run, section 8.

## 1 Scope and method

This card maps, against **all nine** machine-required roles, which evidence is missing, and proposes a
**bounded** supplement for the 7 roles that must be produced plus the package root. It produces no
baselines, no numbers, no gate changes, and no data. Method: static reading of the machine contract
`research/phase1a_data_contract.py` (line numbers cited below are from commit `1627a54`) plus the four
in-repo evidence documents listed in section 2. Every acceptance criterion quoted here is a **fail code
that already exists in the validator**, not a new invention.

Inputs (all in-repo, all read-only):

1. `docs/experiments/2026-09-23_phase1a_data_no_go.md` including its 2026-09-24 correction addendum A-E.
2. `docs/experiments/2026-09-24_phase1a_data_gate_reverification.md` (exhaustive search; section 10 schema candidate).
3. `docs/experiments/2026-09-24_phase1a_supplement_contract_role_gap.md` (8-vs-9 role gap, measured fail-closed).
4. `docs/handoff/2026-09-22-paper-research-next-phase.md` and `docs/experiments/2026-09-22_distillation_mvp_preregistration.md` section 7.1 (rulings D7/D8/D9/D10/D12).

## 2 Role inventory: 9 required, 2 present, 7 missing, plus 1 package root

`REQUIRED_ROLES` (`research/phase1a_data_contract.py:29-39`) has **9** members. The seven machine gates
are `artifact_integrity`, `layer_isolation`, `independent_correctness`, `licence_permission`,
`confidence_provenance`, `analysis_plan`, `parser_contract` (`:201-213`).

| # | Role | State | Evidence |
|---|---|---|---|
| 1 | `source_tables` | **PRESENT in production, do not re-deliver** | `data/research/drift_v0/input/tatqa_tables.json`, 1 442 890 B, sha256 `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` |
| 2 | `injection_map` | **PRESENT in production, do not re-deliver** | `data/research/drift_v0/output/injection_map.json`, 36 004 B, sha256 `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`; meta `{deterministic: true, ratio: 0.3, seed: 42, version: v0}`; 118 entries / 95 distinct uids |
| 3 | `schema` | MISSING | 0 hits machine-wide; the only candidate is **rejected** (section 5) |
| 4 | `label_ledger` | MISSING | 0 hits; injection map carries none of `LABEL_FIELDS` (`:72-81`) - it is perturbation ground truth, not independent correctness labels |
| 5 | `licence_record` | MISSING | 0 hits |
| 6 | `confidence_manifest` | MISSING | 0 hits |
| 7 | `analysis_plan` | MISSING | 0 hits (the string appears in the learnability runner only as a gate name) |
| 8 | `parser_contract_receipt` | MISSING | 0 hits |
| 9 | `learnability_feature_ledger` | MISSING | 0 hits; **no generator exists in the repo** - `phase1a_learnability_baselines.py::_load_feature_ledger()` only reads and hash-verifies a supplied file |
| +1 | package root `phase1a_manifest.json` | MISSING | does not exist anywhere on GB10 |

⇒ external ask = **7 roles + 1 package root**, with no remaining availability judgments.
`DATA_NO_GO` stands and is **not** lifted by this card.

## 3 Per-role supplement items (owner / source / acceptance / dependency)

Acceptance columns quote existing validator fail codes. "Gate" is the machine gate that consumes the role.

### 3.1 `schema` - gate `artifact_integrity` (+3 cross-role hash bindings)

- Owner: Loop C ONLINE research proposes; Loop D accepts; user confirms the source dataset.
- Source: the **official** schema/metadata of the selected public source (P1 FinQA process/checkpoint, P2 Valentine NYC schema-action). The `m1_table_schema.json` candidate is rejected and must not be reused (section 5).
- Acceptance: bound in the manifest with real `bytes` + `sha256`; the same hash must appear in `learnability_feature_ledger.schema_sha256` (`:690-699`, else `feature_ledger_source_hash_mismatch`), in `licence_record.covered_artifact_sha256` (`:856-874`, else `licence_artifact_hash_mismatch`) and in `parser_contract_receipt.input_sha256` (`:997-1012`, else `parser_input_hash_mismatch`). The validator imposes **no content shape** on `schema`, so domain adequacy is a scientific judgment and must be evidenced the same way the rejected candidate was: identifier-cardinality / script-class / overlap test against the corpus, recorded in the report.
- Dependency: source selection (`SOURCE_GO`). Blocks 3.5, 3.7, 3.9.

### 3.2 `label_ledger` - gate `independent_correctness`

- Owner: **two independent reviewer identities plus an adjudicator who is not one of them**; the generator of a draft label may not review its own draft. Disagreements are adjudicated by Loop D / user.
- Source: public gold labels, or a rule-derived draft whose derivation is traceable; either way each row needs two independent reviews.
- Acceptance (per row, `:780-833`): `LABEL_FIELDS` exactly `{sample_id, uid, col, gold_action, gold_target, quality_grade, reviewers, adjudication}`; `quality_grade == "Q3"` (`label_not_q3`); gold action/target valid (`invalid_gold_action`); `>= 2` distinct non-empty `reviewer_id` (`insufficient_independent_reviewers`); every reviewer label valid (`invalid_reviewer_label`); if reviewers agree, gold must equal that choice (`gold_review_mismatch`); if they disagree, an `adjudication` object must exist (`missing_adjudication`) with `adjudicator_id` non-empty, **not** in `reviewer_ids`, valid choice (`invalid_adjudication`) and equal to gold (`gold_adjudication_mismatch`); every `proposal_train` sample must have a label (`missing_label`).
- Dependency: `schema` + `source_tables` + fixed layer assignment. Blocks 3.5 and everything downstream of `LABEL_GO`.

### 3.3 `licence_record` - gate `licence_permission`

- Owner: Loop D / user (the acceptance signature is a human act; it may not be fabricated).
- Source: the dataset's official licence text, **quoted verbatim** rather than paraphrased, with owner and retrieval time.
- Acceptance (`:845-874`): `status == "accepted"` (`licence_not_accepted`); `accepted_by` non-empty (`missing_acceptance_owner`); `accepted_at` ISO-8601 (`invalid_acceptance_time`); `permitted_uses` a superset of `{training, tuning, evaluation, rule_acceptance}` (`missing_permitted_use`); `covered_artifact_sha256` matching the **actual** hashes of every artifact whose role is in `{source_tables, schema, injection_map, label_ledger, learnability_feature_ledger}` (`licence_artifact_hash_mismatch`).
- Dependency: **must be produced after** those five artifacts exist, because it hash-binds them. This is the one role whose position in the order is forced by the validator, not by convenience.

### 3.4 `confidence_manifest` - gate `confidence_provenance`

- Owner: data source if a real confidence field exists; otherwise Loop D records it as unmeasurable.
- Source: a **real source field only**. `gain` / `collateral` substitution is forbidden by the validator itself.
- Acceptance (`:884-899`): `field` non-empty (`missing_confidence_field`); `source` non-empty (`missing_confidence_source`); `missing_policy == "unmeasurable"` (`invalid_missing_policy`); `gain_collateral_substitution is False` (`gain_collateral_substitution_forbidden`); `allowed_values` set-equal to `{low, medium, high}` (`invalid_confidence_vocabulary`).
- Dependency: `schema` (the field must exist in the chosen source). Blocks 3.5.

### 3.5 `learnability_feature_ledger` - gate `artifact_integrity` (nine constraints)

- Owner: a **new deterministic derivation step** (no generator exists today); Loop A implements, Loop B/C verify.
- Source: derived from the accepted package - `source_tables` + `schema` + `confidence_manifest` + accepted `label_ledger`, restricted to the `proposal_train` layer.
- Acceptance (nine constraints, addendum A of the DATA_NO_GO report, code refs `:24`, `:665-673`, `:690-699`, `:700-703`, `:709-711`, `:714`, `:725-736`, `:739-742`): exact top-level key set `{contract_version, source_tables_sha256, schema_sha256, confidence_manifest_sha256, rows}`; `contract_version == "phase1a-feature-ledger-v1"`; the three sha256 fields equal the same package's actual hashes; `rows` non-empty list; each row's key set exactly `FEATURE_FIELDS` (`:82-90`); `canonical_fields` non-empty/unique with `candidate_target` a member when non-null; `confidence` null or in `{low, medium, high}`; each `sample_id` in `proposal_train` with matching registered `uid` (`feature_ledger_identity_mismatch`); row set covers `proposal_train` **exactly** (`feature_ledger_proposal_coverage_mismatch`).
- Dependency: 3.1, 3.2, 3.4 and a fixed `proposal_train` layer. Delivering the other eight roles without this one was **measured** to fail `artifact_integrity` with `missing_required_role`.

### 3.6 `analysis_plan` - gate `analysis_plan` (18 keys)

- Owner: user (ruling D8 supplies `approved_by` / `approved_at` / `significance_level` / `risk_limit` / `delta_*` / `minimum_cost_reduction` / `seed_list` / `target_power`); Loop D transcribes; an **independent** Loop C or independent agent performs the D10 machine audit (implementer does not self-verify).
- Source: the in-package machine contract (distinct artifact from the section 7 human freeze receipt, per ruling D7).
- Acceptance (`:909-977` plus addendum B): 18 required keys; `status == "approved"`; **no** legacy `alpha` / `power` / singular `noninferiority_margin` (`ambiguous_legacy_statistical_field`); `cluster_unit == "lineage_uid"`; `threshold_selection == "proposal_dev_only"` (scope token only - the full rule `proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative` is recorded separately as a rule field and machine-audited per D10, **not** encoded in the token and **not** implemented as an algorithm in this batch); `seed_uid_aggregation == "fixed_seed_pair_then_uid_cluster_bootstrap"`; `holm_adjustment == "step_down_adjusted_p_and_simultaneous_one_sided_ci"`; `holm_families` exactly `REQUIRED_HOLM_FAMILIES` (`:99-108`) with the D9 name `H3a_uid_any_harm`; `one_sided_p_value_methods` exactly 5 verbatim keys (`:946-953`); `noninferiority_margins` nested with key set exactly `{delta_quality, delta_harm, delta_retention}`, each in `[0,1)`; `primary_metrics` includes `{action_macro_f1, harmful_map_rate}`; `minimum_uid_by_action` key set exactly `{map_to, skip, hold}` with int `>= 2`; `minimum_uid_by_role_family` non-empty with int `>= 2`; `mde_by_confirmatory_contrast` key set exactly `REQUIRED_MDE_CONTRASTS` with values in `(0,1)`; `layer_manifest_sha256 == digest(manifest.layers)` (`:976`).
- Cross-artifact constraint (ruling D11, now enforced): `minimum_uid_by_action` / `minimum_uid_by_role_family` must equal the learnability config's `min_dev_uids_by_action` / `min_dev_uids_by_family` under convention (i) - config uses bare family names, `analysis_plan` uses `proposal_train.dev/<family>`; disagreement raises before any probe decision (`research/phase1a_learnability_baselines.py::_check_uid_floor_consistency`).
- Dependency: layers fixed in the package root (for `layer_manifest_sha256`) **and** a real development-side variance estimate for `mde_by_confirmatory_contrast` - until real dev-side sigma exists those D-class parameters cannot converge to a unique value, so this role is **last-but-one** in the order and cannot be filled with placeholders.

### 3.7 `parser_contract_receipt` - gate `parser_contract`

- Owner: a **deterministic GB10 run**, never hand-authored.
- Source: actual execution of the parser contract over the real `source_tables` / `schema` / `injection_map`.
- Acceptance (`:988-1012`): `status == "PASS"` (`parser_contract_not_passed`); `checker` non-empty (`missing_parser_checker`); `commit` full-matching 40 hex (`invalid_parser_commit`); `executed_at` ISO-8601 (`invalid_parser_execution_time`); `input_sha256` covering all three input roles and equal to their actual hashes (`parser_input_hash_mismatch`).
- Dependency: `schema` (3.1). Must be re-executed if any of the three inputs changes, since it hash-binds them.

### 3.8 package root `phase1a_manifest.json`

- Owner: Loop A assembles; an independent reviewer (Loop C or a separate agent) re-runs the precheck.
- Source: assembly of the nine roles - `artifacts` (role / path / bytes / sha256), `bindings` for all six `REQUIRED_BINDINGS` (`:40-47`), and `layers`.
- Acceptance: partitions must include the four `REQUIRED_PARTITIONS` (`proposal_train.train`, `proposal_train.dev`, `gate_validation`, `sealed_test`, `:48-53`); every layer row carries exactly `MANIFEST_ROW_FIELDS` (`:62-71`); `future_replay` may be empty but then needs the hash-bound acquisition protocol, else the report carries `LONGITUDINAL_EVIDENCE_UNAVAILABLE` (`:27`, `:392-450`); the precheck must be run **twice, byte-identical**, with **zero connect** and only aggregate output (no sample text ever written).
- Dependency: all nine roles. Its `layers` digest is an input to 3.6, so 3.6 and 3.8 are mutually dependent and must be closed in one assembly pass.

## 4 Bounded supplement order (dependency-driven, not preference-driven)

1. Source selection + `schema` (3.1) - `SOURCE_GO`.
2. Layer assignment by namespaced lineage UID (3.8 partial) - `SPLIT_GO`.
3. `label_ledger` with two independent reviewers + adjudication (3.2) - `LABEL_GO`.
4. `confidence_manifest` (3.4).
5. `learnability_feature_ledger` derivation (3.5).
6. `parser_contract_receipt` GB10 run (3.7).
7. `phase1a_manifest.json` assembly (3.8) - produces the `layers` digest.
8. `analysis_plan` (3.6) - consumes the `layers` digest; needs D8 values and real dev-side sigma.
9. `licence_record` (3.3) - hash-binds five artifacts, so it is signed last.
10. Double deterministic precheck, zero connect, byte-identical, then **independent** review. Only that can move `DATA_NO_GO`.

Power note carried forward (not re-derived here): `H3a_uid_any_harm` is pinned to `exact_mcnemar`, so at
alpha 0.05 it needs `>= 5` discordant pairs to be able to reach significance, while the contract only
requires `>= 2` UIDs per action as a sanity floor. The supplement target is 250-500 valid UIDs; if that
cannot be met the hypothesis is downgraded to exploratory **without** changing the test.

## 5 Rejected candidates and explicit non-actions

- `~/wzh/m1_samples/m1_table_schema.json` (14 253 B, sha `79bc3a17f6285e2b6071b5e8a3df5ae3927ce049f1d31c016c16e0a628ce9a3b`) is **REJECTED** as `schema`: 4 of its 5 table identifiers are CJK while the corpus's 2479 identifiers contain zero CJK, and identifier overlap is 0 against all three corpus artifacts. Different domain.
- `source_tables` and `injection_map` must **not** be re-delivered; both already exist in production with recorded sha256 and are hash-bindable as-is.
- TAT-DQA stays frozen. The old TAT-QA pool stays `HISTORICAL_ONLY` until its exposure audit is complete.
- No resplit of old data, no synthetic placeholder rows, no invented reviewers, no fabricated licence acceptance, no baseline numbers, no gate/threshold/oracle change.
- P1 FinQA process/checkpoint and P2 Valentine NYC schema-action are **separate streams**: separate provenance, separate role drafts, separate split namespaces. They must not be spliced into one same-distribution main experiment (user ruling 2026-09-24).

## 6 Structural findings for the control plane (governance feedback, no code changed)

1. **This card is inadmissible to a model-based Loop C session by construction.** It requires `calls=0` and forbids any model, yet the Loop C harness on GB10 is an LLM session. That is the same self-contradiction class that ruling D6 split out of the former `LC-RESEARCH-001`. Recommendation: add an explicit `executor: deterministic | model` field to the queue schema so `calls=0` cards are routed to a non-model executor instead of being silently undispatchable.
2. **Only one task can be ACTIVE, and `select_ready()` takes the first READY task in array order.** Dispatching the two user-authorized research cards therefore required reordering `QUEUE.yaml` (research cards moved ahead of `LC-GOV-002`, which stays READY and loses nothing but position). Backup: `/home/testuser/wzh/loopc_backup_20260924b/` (`QUEUE.yaml.pre`, `cards.pre/`). Validated with the lead's own loader: `check` rc=0 (7 tasks, `active={}`, `stop_exists=false`), `status` rc=0 (READY 3 / BLOCKED 4). No status, owner, budget or dependency field was altered.
3. **The ONLINE card's MCP premise is not currently satisfiable on GB10.** Claude Code 2.1.220 reports `mcpServers = []` both globally and for the project entry in `~/.claude.json` (names only were read; no credential value was printed). Most of that card's stated work - official URL, licence scope, commit/release, byte hash - is deterministic and needs **zero** model calls (`git ls-remote`, licence fetch, `sha256sum`). Recommendation: re-scope ONLINE into (i) a zero-model deterministic provenance collector and (ii) a small bounded model step for drafting and literature cross-check, so the `<200` cap is spent on judgment rather than on retrieval.

## 7 Acceptance status and why this is SCOPED_PASS, not PASS

Mechanically satisfied by this card: bounded supplement for all 7 roles + package root; every item carries
owner / source / acceptance / dependency; no old-data resplit; no synthetic placeholder; no gate, threshold
or oracle change; `DATA_NO_GO` unchanged; no baseline produced; owned-path discipline respected (this report
is the only file written).

**Not** satisfied, and therefore blocking a PASS: the control plane's GOAL requires *an independent C Audit
report* for every accepted card, and the author here is Loop D - the implementer must not self-verify. The
independent Loop C audit is **PENDING**. This card is accordingly completed as `SCOPED_PASS` with the audit
explicitly open, and no downstream card may treat it as audited.

## 8 Verification method and one honest disclosure

The GB10-side verification of this card is a deterministic structural checker (kept out of the repo at
`/tmp/lc_offline_check.py`) run under `strace -f -e trace=connect`. It reads only the report file and
prints aggregate counts plus a verdict; it contains no network, model or endpoint code path.

Disclosure (recorded rather than smoothed over): this report's **text was authored off-box by Loop D and
transferred with `scp` over the pre-existing SSH channel**. SSH transport is itself a TCP connection, so a
literal reading of the card's "NO network" cannot be satisfied by *any* card executed remotely on GB10 -
the operator's own shell is already a network session. What is asserted, and what section 10 measures, is
the meaningful invariant: **zero connect() to any service or model endpoint** (`:5050`, `:8004`, `:8006`,
`:8007`, `:8008`, `:4096`, `:15432`, DNS, or any external host) and **zero model calls** during GB10-side
execution of this card. Recommendation: re-word that acceptance line to "no connect to any service or
model endpoint; SSH transport excluded", otherwise every future remote card either fails its own
acceptance or quietly waives it.

## 9 Red lines observed by this card

- No gate, threshold, oracle, family, tolerance or frozen hash was changed; no code file was touched.
- `DATA_NO_GO` is unchanged and is not lifted by this card; no baseline, metric or paper number was produced.
- No old data was resplit; no synthetic placeholder row, invented reviewer or fabricated licence acceptance was proposed.
- TAT-DQA remains frozen; the old TAT-QA pool remains `HISTORICAL_ONLY` pending its exposure audit.
- `docs/33*` and `docs/34*` untouched; production worktree untouched; no service restart; no crontab change.
- Only file written by this card: `reports/LC-RESEARCH-001-OFFLINE.md` (this file).
- No credential, token or endpoint value is reproduced here; `~/.claude.json` was read for key names only.

## 10 Measured verification run (appended after measurement)

```
cd /home/testuser/wzh/projects/agents_final_tech_lc_research
strace -f -e trace=connect -o /tmp/lc_offline_strace2.txt python3 /tmp/lc_offline_check.py
```

| Measured item | Value |
|---|---|
| checker exit code | `0` |
| `connect()` lines in strace | **0** |
| model calls on GB10 for this card | **0** |
| checked file bytes / lines | `20843` / `178` |
| checked file sha256 | `f6eef52f95e54d186bee93c381417164024c687e11f40e35e95214cbdd19689a` |
| structural verdict | **PASS** |
| roles named | 9 / 9, none missing |
| role subsections `3.1`-`3.8` | 8, each carrying all four labels owner / source / acceptance / dependency |
| package-root block complete | yes |
| machine gates named | 7 / 7 |
| `DATA_NO_GO` stated / `DATA_GO` claimed | yes / no |
| placeholder markers (five marker kinds checked) | 0 |
| CRLF / bare CR / BOM / U+FFFD | 0 / 0 / none / 0 |
| ends with newline | yes |
| validator line references (`:NNN`) | 34 |

Honest note on the first run: it returned `STRUCTURAL_VERDICT = FAIL` with exit code 1 on exactly one
assertion, `ends_with_newline = false` (the transferred text had no final newline). The fix was to append
a newline to the report; **no assertion was weakened, removed or re-scoped**, and the first run's strace
already showed `connect()` = 0. This section is appended after the measured run, so the committed file's
sha256 necessarily differs from `f6eef52f...`; the committed value is recorded in the commit and in the
Loop D ledger entry.

Post-append correction (same card, before commit): the row above originally enumerated the five
placeholder marker strings verbatim, which made the report trip the very assertion it reports -
the same self-triggering class as a manuscript quoting its own forbidden-marker list. The wording
was changed to name the count instead of the strings. The checker's assertions were not touched.
