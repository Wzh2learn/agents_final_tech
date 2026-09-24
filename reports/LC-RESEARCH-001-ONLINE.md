# LC-RESEARCH-001-ONLINE report (model qwen3.8-max, packet mode)

> Card LC-RESEARCH-001-ONLINE, dispatched 2026-09-24 after the user routing ruling (MIMO paused, Loop C on qwen3.8-max).
> Mode: evidence packet inline (zero-model provenance facts, licence excerpts, OFFLINE report role sections, contract constants, verified cite-key pool), no tools, 1 turn(s), cost $0.3117.
> Two earlier tool-enabled attempts (30-turn cap) were aborted without output; their streams are preserved at /tmp/lc_online_result.json and /tmp/lc_online.stream equivalents.
> Body below is the session final message verbatim; landed by Loop D without edits.

# LC-RESEARCH-001-ONLINE — Loop C Online Research Card Report

Card: LC-RESEARCH-001-ONLINE · Mode: zero-model online probe evidence only (GB10) · Provenance snapshot time: 2026-09-24T08:05Z · Report date: 2026-09-24 · Status carried forward: **DATA_NO_GO (unchanged)**

Splicing rule observed throughout: P1 (FinQA/ConvFinQA process-checkpoint) and P2 (Valentine NYC schema-action) are reported in strictly separate lanes; no P1 evidence is applied to P2 or vice versa.

---

## 1 Per-source provenance table

| Source ID | Official URL | Licence scope (QUOTED verbatim from inline licence excerpts) | Default-branch head | Retrieval time (UTC) | Bytes | sha256 |
|---|---|---|---|---|---|---|
| `finqa` | https://github.com/czyssrs/FinQA | "MIT License — Copyright (c) 2021 Zhiyu Chen — Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software." (license_http=200) | `0f16e2867befa6840783e58be38c9efb9229d742` | 2026-09-24T08:05Z | 1067 | `92c0e67bd762c15c07ba60de09558338315a8ebf99aac4f51f487179809ac087` |
| `convfinqa` | https://github.com/czyssrs/ConvFinQA | "MIT License — Copyright (c) 2022 Zhiyu Chen" (excerpt scope as provided inline; license_http=200) | `cf3eed2d5984960bf06bb8145bcea5e80b0222a6` | 2026-09-24T08:05Z | 1067 | `5c7b6fe25d37f4b6cc7e0e76267bce7146765b7661d4bb0e9ecc4eb0ed34fb4c` |
| `valentine_nyc` | https://github.com/delftdata/valentine | "Apache License — Version 2.0, January 2004 — http://www.apache.org/licenses/ — TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" (excerpt scope as provided inline; **license_http=307 — see caveat**) | *(empty — unresolved)* | 2026-09-24T08:05Z | 64 | `92a6e3d1139ec8191a01fad126cde7502edd2f13d3b40f0616a414ac77c741b3` |

Provenance notes (facts only, no inference beyond the probe outputs):

- **P1 lane — complete.** Both `finqa` and `convfinqa` returned license_http=200 with full 1067-byte MIT bodies, distinct sha256 values (consistent with distinct copyright years, 2021 vs 2022), and resolved 40-hex default-branch heads matching `COMMIT_RE` shape. P1 provenance is hash-bindable today.
- **P2 lane — incomplete, flagged.** `valentine_nyc` returned license_http=**307** (redirect, not a terminal 200) with a **64-byte** body and an **empty default-branch head**. The 64-byte sha256 above is the hash of the redirect response, *not* of a confirmed full Apache-2.0 licence text at a canonical URL, and no commit head is pinnable. Consequence: P2 cannot pass `SOURCE_GO`, and the `licence_record` role (§3.3) cannot hash-bind a P2 source until a re-retrieval yields license_http=200, a full licence body, and a resolved head. The inline Apache excerpt is recorded as *indicative scope only*, never as accepted licence evidence.
- No dataset bodies were downloaded for either lane; only licence/metadata probes (1067 B, 1067 B, 64 B).

---

## 2 Schema candidate sources

### 2.1 P1 — FinQA / ConvFinQA process-checkpoint (reported first, per priority)

Candidate schema source: the **official repository documentation and data-format metadata** of `czyssrs/FinQA` at head `0f16e2867befa6840783e58be38c9efb9229d742` and `czyssrs/ConvFinQA` at head `cf3eed2d5984960bf06bb8145bcea5e80b0222a6`, exactly as described inline: the official schema/metadata of the selected public source for the P1 process/checkpoint role (derivation-program / reasoning-step structure accompanying the tables). Rationale, P1-local only:

- Both heads are pinned and reproducible; the schema artifact can later be bound with real `bytes` + `sha256` per the offline report §3.1 acceptance.
- MIT scope quoted verbatim in §1 permits use, copy, and modification, which covers the downstream derivation steps (parser contract execution, feature-ledger derivation) that consume the schema.
- The FinQA/ConvFinQA process-checkpoint structure is the natural P1 fit for step-level process evidence in the pool (§4, keys `fan2026agentprocessbench`, `chung2026webstep`).

Status: **candidate proposed by Loop C ONLINE; Loop D accepts; user confirms the source dataset** (owner chain per offline §3.1). Domain adequacy must still be evidenced by identifier-cardinality / script-class / overlap tests against the corpus and recorded in the report, because the validator imposes no content shape on `schema`.

### 2.2 P2 — Valentine NYC schema-action (reported second; no P1 material reused)

Candidate schema source: the **official repository documentation** of `delftdata/valentine` describing the NYC-schema / schema-action benchmark material, as described inline. However, this candidate is **provisional and blocked**: the head is unresolved and the licence retrieval terminated in a 307 (§1). Until a re-probe pins a 40-hex head and a 200-status full Apache-2.0 text, P2 has no admissible provenance and must not be advanced to `SOURCE_GO`. No P1 hash, head, or licence statement is transferred into this lane.

### 2.3 Why `m1_table_schema.json` stays rejected

The `m1_table_schema.json` candidate **remains rejected and must not be reused** (offline report §3.1 → §5). Grounds restated from the inline record: it failed the scientific domain-adequacy evidence path — identifier-cardinality / script-class / overlap testing against the corpus — and the validator imposes no content shape on `schema`, so that judgment is not machine-recoverable; a rejected candidate cannot be laundered back in by any later assembly. The `schema` role must instead be bound to official source metadata (P1: §2.1; P2: §2.2 once unblocked) with real `bytes` + `sha256`, and that same hash must appear in `learnability_feature_ledger.schema_sha256`, `licence_record.covered_artifact_sha256`, and `parser_contract_receipt.input_sha256`.

---

## 3 Data-role requirement drafts (seven missing roles)

All fail codes cited below appear verbatim in the inline contract/offline-record evidence; no new codes are invented. Role set cross-check against `REQUIRED_ROLES`: the nine required roles minus these seven leaves `source_tables` and `injection_map`, which are outside this card's drafting scope.

### 3.1 `schema` — gate `artifact_integrity` (+3 cross-role hash bindings)
- **Owner:** Loop C ONLINE proposes (this card, §2); Loop D accepts; user confirms the source dataset.
- **Source:** P1 first — official FinQA/ConvFinQA schema/metadata at the pinned heads (§2.1). P2 second — Valentine official repository documentation, blocked pending re-retrieval (§2.2). `m1_table_schema.json` permanently excluded (§2.3).
- **Machine acceptance:** bound in the manifest with real `bytes` + `sha256` (`SHA256_RE` shape); absence of the role fails as `missing_required_role`; hash agreement enforced downstream via `feature_ledger_source_hash_mismatch`, `licence_artifact_hash_mismatch`, `parser_input_hash_mismatch`. No content-shape check exists — domain adequacy is evidenced by the identifier-cardinality / script-class / overlap tests recorded in the report.
- **Dependency:** source selection (`SOURCE_GO`). Blocks `learnability_feature_ledger`, `parser_contract_receipt`, and the licence hash-binding.

### 3.2 `label_ledger` — gate `independent_correctness` (binding `("independent_correctness", "label_ledger")`)
- **Owner:** two independent reviewer identities plus an adjudicator who is not one of them; a draft's generator may not review its own draft; disagreements adjudicated by Loop D / user.
- **Source:** public gold labels, or a rule-derived draft with traceable derivation; every row receives two independent reviews.
- **Machine acceptance (per row):** fields exactly `LABEL_FIELDS` = `{sample_id, uid, col, gold_action, gold_target, quality_grade, reviewers, adjudication}`; `quality_grade == "Q3"` else `label_not_q3`; gold action ∈ `VALID_ACTIONS` = `{map_to, skip, hold}` else `invalid_gold_action`; ≥2 distinct non-empty reviewer ids else `insufficient_independent_reviewers`; every reviewer label valid else `invalid_reviewer_label`; on agreement, gold must equal the agreed choice else `gold_review_mismatch`; on disagreement, an `adjudication` object must exist else `missing_adjudication`, with non-empty `adjudicator_id` not among reviewers and a valid choice else `invalid_adjudication`, equal to gold else `gold_adjudication_mismatch`; every `proposal_train` sample labelled else `missing_label`.
- **Dependency:** `schema` + `source_tables` + fixed layer assignment. Blocks `learnability_feature_ledger` and everything downstream of `LABEL_GO`.

### 3.3 `licence_record` — gate `licence_permission` (binding `("licence_permission", "licence_record")`)
- **Owner:** Loop D / user — the acceptance signature is a human act and may not be fabricated.
- **Source:** the dataset's official licence text **quoted verbatim** (as §1 does), with owner and retrieval time. P1: MIT texts at 200 status are quotable now. P2: **not quotable as accepted evidence** until the 307/64-byte retrieval is redone to a 200 with full body and resolved head (§1 caveat).
- **Machine acceptance:** `status == "accepted"` else `licence_not_accepted`; non-empty `accepted_by` else `missing_acceptance_owner`; ISO-8601 `accepted_at` else `invalid_acceptance_time`; `permitted_uses ⊇ REQUIRED_USES` = `{training, tuning, evaluation, rule_acceptance}` else `missing_permitted_use`; `covered_artifact_sha256` matching the actual hashes of every artifact in roles `{source_tables, schema, injection_map, label_ledger, learnability_feature_ledger}` else `licence_artifact_hash_mismatch`.
- **Dependency:** forced by the validator to be produced **after** those five artifacts exist (it hash-binds them). P2 additionally depends on licence re-retrieval.

### 3.4 `confidence_manifest` — gate `confidence_provenance` (binding `("confidence_provenance", "confidence_manifest")`)
- **Owner:** the data source if a real confidence field exists; otherwise Loop D records it as unmeasurable.
- **Source:** a **real source field only** — for P1 this must be located in the official FinQA/ConvFinQA metadata at the pinned heads; `gain`/`collateral` substitution is forbidden by the validator itself.
- **Machine acceptance:** non-empty `field` else `missing_confidence_field`; non-empty `source` else `missing_confidence_source`; `missing_policy == "unmeasurable"` else `invalid_missing_policy`; `gain_collateral_substitution is False` else `gain_collateral_substitution_forbidden`; `allowed_values` set-equal `{low, medium, high}` else `invalid_confidence_vocabulary`.
- **Dependency:** `schema` (the field must exist in the chosen source). Blocks `learnability_feature_ledger`.

### 3.5 `analysis_plan` — gate `analysis_plan` (binding `("analysis_plan", "analysis_plan")`; 18 keys)
- **Owner:** user (ruling D8 supplies `approved_by` / `approved_at` / `significance_level` / `risk_limit` / `delta_*` / `minimum_cost_reduction` / `seed_list` / `target_power`); Loop D transcribes; an **independent** Loop C or independent agent performs the D10 machine audit — the implementer does not self-verify.
- **Source:** the in-package machine contract (distinct artifact from the §7 human freeze receipt, per ruling D7).
- **Machine acceptance:** 18 required keys; `status == "approved"`; **no** legacy `alpha` / `power` / singular `noninferiority_margin` else `ambiguous_legacy_statistical_field`; `cluster_unit == "lineage_uid"`; `threshold_selection == "proposal_dev_only"` (scope token only; the full rule `proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative` is recorded separately as a rule field and machine-audited per D10, not encoded in the token, not implemented as an algorithm in this batch); `seed_uid_aggregation == "fixed_seed_pair_then_uid_cluster_bootstrap"`; `holm_adjustment == "step_down_adjusted_p_and_simultaneous_one_sided_ci"`; `holm_families` exactly `REQUIRED_HOLM_FAMILIES` including `H3a_uid_any_harm` (rq2: `H2a_quality_noninferiority`, `H2b_safety_noninferiority`, `H2c_risk_constrained_coverage`; rq3: `H3a_uid_any_harm`, `H3a_valid_rule_retention`); `one_sided_p_value_methods` exactly the 5 verbatim keys; `noninferiority_margins` key set exactly `REQUIRED_NONINFERIORITY_MARGINS` = `{delta_quality, delta_harm, delta_retention}`, each in [0,1); `primary_metrics ⊇ REQUIRED_PRIMARY_METRICS` = `{action_macro_f1, harmful_map_rate}`; `minimum_uid_by_action` key set exactly `{map_to, skip, hold}` with int ≥2; `minimum_uid_by_role_family` non-empty with int ≥2; `mde_by_confirmatory_contrast` key set exactly `REQUIRED_MDE_CONTRASTS` (the five hypotheses above) with values in (0,1); `layer_manifest_sha256 == digest(manifest.layers)`. Cross-artifact (ruling D11, enforced): the two `minimum_uid_*` maps must equal the learnability config's `min_dev_uids_by_action` / `min_dev_uids_by_family` under convention (i) — config bare family names vs `proposal_train.dev/<family>` — disagreement raises before any probe decision via `research/phase1a_learnability_baselines.py::_check_uid_floor_consistency`.
- **Dependency:** layers fixed in the package root (for `layer_manifest_sha256`) **and** a real development-side variance estimate for `mde_by_confirmatory_contrast`; until real dev-side sigma exists the D-class parameters cannot converge, so this role is **last-but-one** and cannot be filled with placeholders.

### 3.6 `parser_contract_receipt` — gate `parser_contract` (binding `("parser_contract", "parser_contract_receipt")`)
- **Owner:** a **deterministic GB10 run** — never hand-authored.
- **Source:** actual execution of the parser contract over the real `source_tables` / `schema` / `injection_map` (P1 inputs first once §2.1 is accepted).
- **Machine acceptance:** `status == "PASS"` else `parser_contract_not_passed`; non-empty `checker` else `missing_parser_checker`; `commit` full-matching `COMMIT_RE` (40 hex) else `invalid_parser_commit`; ISO-8601 `executed_at` else `invalid_parser_execution_time`; `input_sha256` covering all three input roles and equal to their actual hashes else `parser_input_hash_mismatch`.
- **Dependency:** `schema` (§3.1). Must be re-executed if any of the three inputs changes, since it hash-binds them.

### 3.7 `learnability_feature_ledger` — gate `artifact_integrity` (binding `("artifact_integrity", "learnability_feature_ledger")`; nine constraints)
- **Owner:** a **new deterministic derivation step** (no generator exists today); Loop A implements, Loop B/C verify.
- **Source:** derived from the accepted package — `source_tables` + `schema` + `confidence_manifest` + accepted `label_ledger`, restricted to the `proposal_train` layer.
- **Machine acceptance (nine constraints):** exact top-level key set `{contract_version, source_tables_sha256, schema_sha256, confidence_manifest_sha256, rows}`; `contract_version == "phase1a-feature-ledger-v1"`; the three sha256 fields equal the same package's actual hashes else `feature_ledger_source_hash_mismatch`; `rows` non-empty list; each row's key set exactly `FEATURE_FIELDS` = `{sample_id, uid, observed_header, canonical_fields, candidate_target, confidence, family}`; `canonical_fields` non-empty/unique with `candidate_target` a member when non-null; `confidence` null or in `{low, medium, high}`; each `sample_id` in `proposal_train` with matching registered `uid` else `feature_ledger_identity_mismatch`; row set covers `proposal_train` **exactly** else `feature_ledger_proposal_coverage_mismatch`. Role absence itself fails as `missing_required_role` — **measured**: delivering the other eight roles without this one failed `artifact_integrity`.
- **Dependency:** §3.1, §3.2, §3.4 and a fixed `proposal_train` layer.

Ordering consequence (dependency-driven, not preference-driven): schema → {confidence_manifest, label_ledger} → learnability_feature_ledger → licence_record (hash-binds five artifacts, position forced by validator) ; parser_contract_receipt after schema; analysis_plan last-but-one (mutually dependent with the package root `phase1a_manifest.json` via the `layers` digest — closed in one assembly pass); P2 entries enter the same order only after their provenance gap (§1) closes, and never ahead of P1.

---

## 4 Literature cross-check (verified cite-key pool only; no new venues)

Cross-check of this card's decisions against the inline verified pool; keys are used only as supporting context, and no venue or claim outside the pool is introduced.

- **P1 process-checkpoint suitability** (FinQA/ConvFinQA derivation-step structure as process evidence): `fan2026agentprocessbench`, `chung2026webstep`, `wang2026gta2` — the pool contains process/step-level benchmark lines consistent with treating program-derivation structure as checkpoint-grade evidence.
- **Label review design** (two independent human reviewers + non-reviewer adjudicator; no self-review; Q3 grading): `zheng2023judge`, `li2025robustjudge`, `li2025scoringbias` — judge/scoring-bias lines support keeping automated judging out of the gold-label path; `li2024pedants` — fine-grained verification line supports row-level review discipline.
- **Confidence honesty** (real-field-only rule; `unmeasurable` policy; no `gain`/`collateral` substitution): `messing2026measurementerror`, `ross2024goodmetric` — measurement-error and metric-validity lines support recording unmeasurable confidence rather than proxying it.
- **Analysis-plan statistics** (one-sided p methods, Holm step-down families, non-inferiority margins, no legacy ambiguous fields): `amrhein2022aces`, `amrhein2023aceswmt`, `moghe2024acesjournal` — statistical-interpretation lines consistent with the D7/D8/D9/D11 rulings.
- **Parser-contract receipt as deterministic re-execution** (and re-run on any input change): `cho2025metamorphic`, `tan2026agentchaos` — metamorphic/robustness lines support machine re-execution over hand-authored attestations.
- **Learnability feature ledger** (sample-level learnability features derived deterministically): `hinton2015distilling`, `gou2021kdsurvey`, `xu2024kdsurveyllm`, `qiu2025agentdistill`, `liu2025structuredagent` — distillation/structured-agent lines form the concept lineage for per-sample learnability features.
- **Candidate/threshold ordering context** (dev-only threshold-selection token; coverage-then-F1 ordering recorded separately): `kendiukhov2026ranking`, `du2026promptranking` — ranking lines are consistent with keeping ranking rules explicit, recorded, and machine-audited rather than encoded in a scope token.
- **P2 contextual schema-action framing:** `deviyani2025contextual` — contextual-data line relevant to schema-action grounding; noted but **not load-bearing**, since P2 is blocked on provenance (§1) regardless of literature support.
- **Unmapped keys:** `chen2026counteraction`, `ma2026mopd` — retained in the pool; no role decision on this card cites them as evidence, and none will until a mapped use exists.

Cross-check verdict: no card decision contradicts the pool; no key outside the pool is referenced; P1 and P2 literature support is reported separately and never spliced.

---

## 5 Closing section

**Call accounting (cap 200):**

| Item | Count |
|---|---|
| Canaries (failed or passed) | 3 |
| Prior aborted session turns | 31 |
| This session turns (single final-message turn) | 1 |
| **Total consumed** | **35** |
| **Cap** | **200** |
| **Remaining headroom** | **165** |

**Compliance statements:**

1. **DATA_NO_GO is unchanged.** This card proposes candidates and drafts role requirements only; no gate (`SOURCE_GO`, `LABEL_GO`, or any manifest precheck) is claimed passed by this report. The P2 lane is additionally flagged blocked on its 307/empty-head provenance gap.
2. **No dataset bodies were downloaded.** Only licence/metadata probes were retrieved: 1067 B (finqa licence), 1067 B (convfinqa licence), 64 B (valentine redirect body). No table, split, sample text, or corpus payload was fetched, and no sample text is written anywhere in this report.
3. **No tokens printed.** No API keys, credentials, session tokens, or bearer material appear in this report or in the provenance table; hashes and HTTP status codes only.
4. **Priority order respected:** P1 (FinQA/ConvFinQA) reported first, P2 (Valentine NYC) second, with no cross-lane reuse of heads, hashes, or licence statements.
5. `m1_table_schema.json` remains rejected and was not reused (§2.3).

End of report — LC-RESEARCH-001-ONLINE, final message, self-contained.
