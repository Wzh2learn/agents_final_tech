# PR-EXP-07 Implementation Contract — frozen before feature-value observation

> experiment_id: `PR-EXP-07` | role: `ROBUSTNESS_ANTI_TAUTOLOGY` supporting evidence only; never a repair-count positive
> frozen_at_utc: `2026-10-11T08:24:52Z`
> prereg: `research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md`
> prereg_sha256: `4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f`
> qualification_gate: Loop C pre-result re-audit `PASS`; source `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log`, sha256 `a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d`
> freeze timing: extractor, evaluator, feature sets, pairing rule, seeds, classifier, metrics, taxonomy, and source hashes are fixed below before any experiment feature value was computed or observed. Key names and source-code structure were inspected; no response value, feature vector, shuffled-control value, or blind-vs-original metric was observed before this freeze.
> post-freeze rule: these files are read-only for this run. Any edit invalidates this contract and requires a new preregistration; no rescue tuning is allowed.

## 1. Goal, done conditions, exclusions, and stop conditions

- Goal: re-extract the frozen 216-row multi-leaf population from unordered raw observation-state pairs without exposing label or construction fields to the extractor, then evaluate the frozen three feature sets under nearest-centroid LOCO.
- Done conditions: exact row preservation; all-row swap proof; pairing/leakage proof; full/direct/non-direct metrics; shuffled-label control; identical-row blind-vs-original delta with CI; attrition table; exactly one canonical outcome label; receipt with input/output hashes, zero endpoint cost, unverified items, and deviations.
- Exclusions: no model/judge calls, training, services, databases, network, commit/push, prereg edits, shared-surface edits, hunting, label misuse, production probes, or repair-count accounting.
- Stop conditions: `INPUT_MISSING`; `PREREG_MISMATCH` or `HASH_MISMATCH`; forbidden action; qualification failure -> `NOT_EVALUABLE`; leakage, pairing, or swap proof failure -> `INVALID`. Negative/NULL/`NOT_EVALUABLE` results are valid and must not be rescued.
- Partial-delivery note: acknowledged as non-blocking bookkeeping only. Missing verdict-relevant inputs or proofs remain fail-closed (`INPUT_MISSING` or `NOT_EVALUABLE`) and are never silently converted to NULL.

## 2. Shared-surface hash verification completed before execution

All entries of `research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json` were verified in manifest insertion order before this contract was created:

| Surface | Identity rule | Pinned identity | Verified identity |
|---|---|---|---|
| `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | raw_sha256 | `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4` | same |
| `research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl` | raw_sha256 | `39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f` | same |
| `research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl` | raw_sha256 | `37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06` | same |
| `research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json` | raw_sha256 | `15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163` | same |
| `scripts/m1_statement_parser.py` | git_blob | `def5161dd17fc14345d340879174ed01e0277626` | `git rev-parse HEAD:scripts/m1_statement_parser.py` = `def5161dd17fc14345d340879174ed01e0277626`; `git hash-object scripts/m1_statement_parser.py` = `def5161dd17fc14345d340879174ed01e0277626` |
| `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md` | raw_sha256 | `4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290` | same |

Canonicalizer informational raw SHA-256 on this host: `747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b` (matches the pinned GB10 informational value). Raw SHA-256 is not the canonical identity under the 2026-10-11T08:30Z rule; the two git-blob identities above are binding.

## 3. Enumerated verdict-relevant inventory with fail-closed semantics

Any missing path, hash mismatch, schema mismatch, or unpinned item below is `INPUT_MISSING` and stops before scientific evaluation.

### Contract and qualification sources

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 1 | Preregistration v2 | `research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md` | `4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f` |
| 2 | Shared freeze | `research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json` | `d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4` |
| 3 | SOURCE_LOCAL_RESPONSE term sheet | `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md` | `4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290` |
| 4 | Binding residual addendum | `research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md` | `a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569` |
| 5 | Loop A assignment card | `research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-07.md` | `448fe0868fdfc427d88aef72f4094fc54610b3380cbb084ca93ddfef13563d3a` |
| 6 | Loop C pre-result PASS re-audit | `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log` | `a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d` |
| 7 | Recheck packet header | `research/positive_repair_20261011/recheck_packet_header.md` | `1f89dc8215b171ae0189757c0dcdd90caccfd245a3e75d72228dbe19392b7768` |

### Population, pairing, grouping, and label provenance

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 8 | Freeze receipt / cluster and fold rule | `docs/research/multileaf_preresult_freeze_receipt_v1.md` | `a167f770f5b2e42cca69579ec60efafd233c7e8ed742c7178f244dbc6c78eaf1` |
| 9 | Freeze manifest | `research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json` | `15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163` |
| 10 | Sample manifest / design-label source | `research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json` | `8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693` |
| 11 | Formal runner / pairing source | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4` |
| 12 | Frozen leaf order source | `config/eval_checkpoint_trees.json` | `0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25` |

- Population: exactly 216 frozen carrier rows, 72 frozen clusters, three classes, three injections per cluster. Expected rows/clusters are part of the qualification gate.
- LOCO groups: `cluster_id` exactly as frozen in the paired carrier and freeze receipt; all rows for one cluster stay together. The cluster/LOCO rule is the receipt text above, referenced by hash.
- Label decoding map: `M -> M`, `R -> R`, `N -> N`, decoded only from the injection-design `stage` field after feature extraction. The evaluator asserts equality with `expected_first_affected_stage`; labels are never response-derived.
- Forbidden extractor knowledge: mutation family, stage, expected first stage, target checkpoint, gold outcome, sample namespace, sample ID, generation code, response vector, or contract checks.
- GB10-only drift/injection-map inputs: not applicable to PR-EXP-07; this run consumes the frozen multi-leaf carriers only.

### Frozen extractor, feature sets, and proof artifacts

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 13 | Label-blind extractor | `research/positive_repair_20261011/runs/PR-EXP-07/extractor.py` | `8b136537189343f479506b9191908ce7d607805a29330b0890cf999c417e2d9c` |
| 14 | Pair loader / seed rule | `research/positive_repair_20261011/runs/PR-EXP-07/extract_features.py` | `3419dba7f52497ba1c1fa721022a1b0a39d9e645c0b6afb0078dc2b105f0e2be` |
| 15 | Frozen evaluator | `research/positive_repair_20261011/runs/PR-EXP-07/evaluate_pr_exp_07.py` | `5f8310d0e86860915b55406b1a5eb82a94879f1ea2d73f6184780e84b0ce0dd1` |
| 16 | Feature-set definition | `research/positive_repair_20261011/runs/PR-EXP-07/feature_sets.json` | `931f2a2a4c1cf37a39a0b3cd26b6387a9a322387cec3f0702c5fa9ff9aac7a45` |
| 17 | Pairing-rule source and proof | `research/positive_repair_20261011/runs/PR-EXP-07/pairing_rule.json` | `873f7ca3b26d2f88c52c20cb6063cca5b333e67da6187cb2f278bc0565d05b40` |

Pairing-rule certification:

- Pair membership: within one already-frozen carrier record, pair `baseline_scores` with `injected_scores`. The formal materialization fixed those two states together for the same frozen sample/cluster before scoring; no cross-record matching or value-based search occurs.
- Pair order: frozen file order, one bit per record from `random.Random(2026101107)`; reverse exactly when the bit is 1. Seed `2026101107` is frozen.
- Code-inspection proof: `extractor.extract` accepts only a two-member sequence of observation-state mappings. `extract_features.py` accesses only `baseline_scores` and `injected_scores` before that call. The extractor does not import the formal runner and contains no forbidden label/contract fields. Pairing is therefore independent of response values.
- Swap proof: for every one of the 216 rows, `feature(P) == feature(swap(P))` exactly. Failure on any row is `INVALID`; no partial success substitutes for the all-row gate.

Feature vector: 12 frozen leaves in frozen tree order x 7 symmetric components = 84 dimensions:

`presence_min`, `presence_max`, `presence_xor`, `score_min`, `score_max`, `score_abs_diff`, `score_sum`.

Scores are divided by the frozen scale `10.0`; missing leaves are represented only through zero presence/score components. Each per-leaf component is computed with symmetric min/max/XOR/sum operations, so pair reversal cannot change it.

Frozen feature sets:

- Full: all 12 leaves, 84 dimensions, sha256 of definition `931f2a2a4c1cf37a39a0b3cd26b6387a9a322387cec3f0702c5fa9ff9aac7a45`.
- Direct-codebook subset: `parse.field.hit_rate`, `qa.retrieval.source_required`, `parse.reconcile.equations`; 21 dimensions; definition is fixed by the freeze manifest before feature observation, not by response values.
- Non-direct subset: the complementary nine leaves; 63 dimensions; same definition hash.

### Carrier and original-result inputs

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 18 | Paired raw-state carriers | `research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl` | `39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f` |
| 19 | Original prediction rows / identical-row anchor | `research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl` | `37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06` |
| 20 | Original frozen formal result | `research/stage_e_multileaf_20261010/results/multileaf_formal_results.json` | `ae9cf1cf37e2742e3895ec2bd0e4cf0c150a18c927eb9a618f612782b3d9cbb0` |
| 21 | Original bootstrap intervals | `research/stage_e_multileaf_20261010/results/multileaf_bootstrap_intervals.json` | `0dbfebc34aebafbafcebdcb7c944668ea8c235a87fd692454536a4444a91887a` |
| 22 | Original direct/non-direct ablation evidence | `research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json` | `0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d` |
| 23 | Original run receipt | `research/stage_e_multileaf_20261010/results/multileaf_run_receipt.json` | `66ab58fa4847e6ee25567443310781628ee92bd952cfc3a469d323efd9c11956` |

## 4. Frozen evaluation

- Classifier: deterministic Euclidean nearest-centroid, class serialization order `M,R,N`, leave exactly one frozen `cluster_id` out, all repeated injections for that cluster in the held-out fold.
- Tie rule: `np.isclose(..., rtol=0.0, atol=1e-12)`; any distance tie becomes `__TIE__` and scores incorrect.
- Primary point metrics: macro-F1 and top-1 accuracy. Raw outputs include per-class TP/FP/FN and F1 numerator/denominator, plus top-1 correct/total and confusion matrices.
- Chance: `1/3` for both reported chance references. Direct-codebook baseline is the frozen direct subset evaluated by the same LOCO classifier.
- Shuffled-label negative control: permute the 72 cluster labels as a multiset with `random.Random(2026101108)`, assign permuted labels back by frozen cluster, fit/score the full set against those permuted design labels. Seed `2026101108` is frozen.
- Bootstrap: 10,000 cluster resamples, seed `20261012`, percentile 2.5/97.5 CI. The blind-vs-original delta uses paired resamples of the same clusters and identical 216 rows for label-blind and original predictions.
- Original comparison: `delta = full_labelblind_macroF1 - original_frozen_macroF1`, with paired cluster-bootstrap CI. It is explicitly `NON_COMPARABLE_CLAIM_WISE`: the numeric delta is reported only because rows are identical; measurement objects differ.

## 5. SOURCE_LOCAL_RESPONSE operational binding

For PR-EXP-07, the binding operational test from `SOURCE_LOCAL_RESPONSE_v1.md` is applied rather than the over-inclusive prose definition: `full <= direct` is NULL, and ROBUST additionally requires the non-direct subset to clear `1/3 + 0.05`. A direct/source-local-concentrated gain cannot be narrated as robust or counted as a repair positive.

## 6. Frozen numeric criteria and total/disjoint taxonomy

Primary comparison point is macro-F1. `m = 0.05`, chance margin boundary `1/3 + 0.05 = 0.3833333333333333`.

Ordering is fixed as follows:

1. `NOT_EVALUABLE` first for undefined/missing feature rows, missing proof artifacts, qualification failure, or a residual region not covered by the prereg's four terminal cases; row-level attrition is mandatory.
2. `INVALID` second if any extractor leakage token is accessible, pairing proof fails, or any-row swap invariance fails.
3. `ROBUST` iff `full - direct >= 0.05` and `non_direct >= 1/3 + 0.05`.
4. `NULL` iff `full <= direct`.
5. `NULL_AT_CHANCE` iff `full > direct` and `abs(full - 1/3) <= 0.05`.
6. `NULL_DIRECT_CONCENTRATED` iff `full > direct`, full is outside the chance band, and `non_direct <= 1/3 + 0.05`.

This ordered rule is evaluated until one and only one label is assigned; each outcome record must land in exactly one bucket. Exactly one canonical outcome string is emitted. `NOT_EVALUABLE` is never merged into NULL.

Interpretation:

- `ROBUST` is supporting evidence only and never increases the repair count.
- Any degradation or NULL-family result retains a negative/NULL claim and emits an explicit claim-lowering note; it is never silent.

## 7. Attrition and outputs

Row-level attrition table must report expected/observed/retained/excluded rows plus counts for: missing pair member, non-finite feature, feature row missing, label missing, cluster missing, row alignment failure, and proof missing. Zero-count reasons remain explicit.

Required outputs under `research/positive_repair_20261011/runs/PR-EXP-07/`:

- `feature_values.jsonl`
- `extraction_proof.json`
- `swap_invariance_proof.json`
- `attrition.json`
- `result.json`
- `receipt.json`

`receipt.json` must contain: experiment ID; exactly one `outcome_label`; `prereg_sha256`; `implementation_contract_sha256`; start/end UTC; input and output SHA-256 maps; raw numerators/denominators and CIs; `model_calls=0` and all other endpoint counts zero; `unverified_items`; and `deviations`.

## 8. Deviations and unverified posture

- Planned deviations: none.
- Planned unverified items: none.
- If an actual deviation or unverified item arises, it must be recorded truthfully in `receipt.json`; it may not be hidden or used to rescue the result.
