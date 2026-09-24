# Independent Loop C audit of protocol sections 7-9 and the analysis_plan template (model qwen3.8-max)

> Dispatched 2026-09-24 against commit 60bf9d2; evidence packet inline; no tools; 1 turn(s), cost $0.1815.
> Verdict: PASS_WITH_NOTES - 18 required keys plus one sanctioned extra; token values verbatim; four PENDING placeholders honest and must-fail as designed; runner specs carry the contract-enforced fields, double-run identity, zero-connect guard and tamper must-fire examples.
> Low note: REQUIRED_HOLM_FAMILIES was cross-verified rather than quoted inline in the packet; the constant was verified at write time against contract lines 99-109 and future packets will inline it.
> Body verbatim.

**VERDICT: PASS_WITH_NOTES**

Independent Loop C audit of commit 60bf9d2 — protocol §7–9 + `phase1a_analysis_plan_template_v1.json`. All determinations made solely against the inline evidence (template, §7–9 text, contract excerpt).

---

**Finding 1 — Key inventory exact (PASS, severity: none).**
Template contains 19 keys: the 18 required contract keys (`status`, `approved_by`, `approved_at`, `cluster_unit`, `significance_level`, `target_power`, `risk_limit`, `noninferiority_margins`, `primary_metrics`, `threshold_selection`, `seed_uid_aggregation`, `holm_families`, `one_sided_p_value_methods`, `holm_adjustment`, `minimum_uid_by_action`, `minimum_uid_by_role_family`, `mde_by_confirmatory_contrast`, `layer_manifest_sha256`) plus exactly one sanctioned extra, `threshold_selection_rule_note`, matching the D10 ruling as described in §9. No unsanctioned extras. Informational: the excerpt shows no exact-key-set gate for analysis_plan, so the note key is structurally safe against the current checker.

**Finding 2 — Token values verbatim (PASS, severity: none).**
- `threshold_selection = "proposal_dev_only"` — character-identical to the contract comparison. ✓
- `seed_uid_aggregation = "fixed_seed_pair_then_uid_cluster_bootstrap"` ✓
- `holm_adjustment = "step_down_adjusted_p_and_simultaneous_one_sided_ci"` ✓
- `one_sided_p_value_methods`: all five key–value pairs match the contract dict verbatim (H2a/H2b/H2c → `paired_uid_sign_flip_on_seed_mean_difference`; `H3a_uid_any_harm` → `exact_mcnemar`; `H3a_valid_rule_retention` → `paired_cluster_sign_flip_noninferiority`). ✓
- `holm_families`: `REQUIRED_HOLM_FAMILIES` is referenced but not inlined in the excerpt, so verbatim equality cannot be checked against the constant itself. Cross-verification performed instead: (a) §9 asserts H3a_uid_any_harm inclusion — template rq3 contains it; (b) the family union {H2a, H2b, H2c, H3a_uid_any_harm, H3a_valid_rule_retention} is exactly the five keys of `one_sided_p_value_methods`, internally consistent. (NOTE, severity: low — a future audit batch should quote the constant inline.)

**Finding 3 — PENDING honesty and must-fail verification (PASS, severity: none; one low note).**
No invented (0,1) MDE values — `mde_by_confirmatory_contrast` is the string `PENDING_DEV_SIGMA`, exactly per the §9 rule that any pre-σ value would be fabrication. Fail codes that fire on the template as-is, traced line-by-line through the excerpt:
1. `analysis_plan_not_approved` — `"PENDING_USER_APPROVAL" != "approved"`.
2. `invalid_analysis_approval_time` — `"PENDING_ISO8601"` is not ISO8601.
3. `invalid_minimum_uid_by_role_family` — string, fails `isinstance(..., dict)`.
4. `invalid_mde_by_confirmatory_contrast` — string, fails `isinstance(..., dict)`.
5. `layer_manifest_hash_mismatch` — `"PENDING_SPLIT_GO"` ≠ `_digest_object(manifest.layers)`.
The template therefore MUST be rejected pre-completion, as §9 requires. Note (low): `missing_analysis_owner` does **not** fire — `"PENDING_USER"` is a non-empty string and satisfies the contract's weak check. Approval integrity is nonetheless enforced via codes 1–2, so this is a contract-check looseness, not a template defect; flagged for the record.

**Finding 4 — `minimum_uid_by_action` provenance (NOTE, severity: low; not REJECT-triggering).**
`{"map_to": 2, "skip": 2, "hold": 2}` passes the contract's structural checks (int, ≥2, assuming `VALID_ACTIONS` = {map_to, skip, hold} — constant not inlined). However, §9's enumeration of D8-approved starting values (0.05 / 0.80 / 0.10 / delta_* 0.02 / metrics / cluster_unit / the verbatim tokens) does not explicitly list these minimums. The value 2 is the contract-enforced floor, i.e., the minimal conservative choice required for the key to exist at all — not an invented statistic of the MDE kind — so this does not force REJECT, but the approval record should cite provenance for these three integers.

**Finding 5 — Numeric values otherwise attributed (PASS, severity: none).**
0.05, 0.8, 0.1, and all three deltas 0.02 fall in the contract's required open/closed intervals and are explicitly attributed in §9 to the D8 approval — provenance exists, so they are not invented. `primary_metrics` contains the two metrics §9 names (`REQUIRED_PRIMARY_METRICS` constant not inlined; consistent by §9 assertion — covered by the Finding 2 low note on constants).

**Finding 6 — No legacy keys (PASS, severity: none).**
`alpha`, `power`, `noninferiority_margin` are absent. The near-miss keys `target_power` and `noninferiority_margins` (plural) do not trigger `ambiguous_legacy_statistical_field` because Python dict membership is exact-key. Confirmed no substring-collision risk in the gate as written.

**Finding 7 — §7 runner spec complete (PASS, severity: none).**
All contract-enforced receipt fields specified: `status=PASS`, non-empty `checker`, 40-hex `commit` pinned to repo HEAD at run time, ISO8601 `executed_at`, `input_sha256` covering all three inputs (source_tables / schema / injection_map) and equal to actual in-package hashes. Double-run byte-identity required. Zero-connect guard present (socket guard, local-file IO only, observed port set recorded as `[]`, mirroring the w2 endpoint-guard pattern). Positive/negative examples mandated, with the tampered-hash case explicitly required to fire `parser_input_hash_mismatch`. Prerequisite (schema binding; current corpus BLOCKED per §6) is consistent and honestly stated.

**Finding 8 — §8 mirrors nine constraints; self-audit bar held (PASS, severity: none).**
Counted exactly nine mirrored constraints: (1) top-level key set; (2) `contract_version=phase1a-feature-ledger-v1`; (3) three cross-role sha256 = actual in-package hashes; (4) rows non-empty; (5) row key set = FEATURE_FIELDS; (6) canonical_fields non-empty, unique, candidate_target ∈ canonical_fields; (7) confidence ∈ {null, low, medium, high}; (8) sample_id/uid consistent with proposal_train registration; (9) row set exactly covers proposal_train. Plus double-run byte-identity, independent Loop C audit, and generator-cannot-self-audit (derivation-script author barred from signing acceptance). Confidence-fixed-null rule is consistent with the unmeasurable confidence_manifest policy.

**Finding 9 — §9 D11 cross-consistency statement (PASS, severity: none).**
§9 states D11 requires `minimum_uid_by_role_family` to equal config `min_dev_uids_by_family` after stripping the `proposal_train.dev/` prefix, with full key-value equality — matching the convention under audit. The pending reason (family taxonomy awaiting learnability design) is coherent with the placeholder token `PENDING_FAMILY_TAXONOMY`.

---

**Summary:** The template carries exactly 18 required keys + the D10-sanctioned note key; all machine-audited tokens are verbatim; all four PENDING placeholders are honest and provably fire five contract fail codes (with the documented nuance that `PENDING_USER` alone would not trip `missing_analysis_owner`); no legacy keys; no invented (0,1) values; §7–9 specs are complete and self-consistent. Outstanding low-severity items: inline quotation of the four contract constants (REQUIRED_HOLM_FAMILIES, REQUIRED_PRIMARY_METRICS, VALID_ACTIONS, REQUIRED_MDE_CONTRASTS) in future audit evidence, and provenance citation for the `minimum_uid_by_action` floor values. **PASS_WITH_NOTES.**
