# PR-EXP-03 implementation contract (frozen before P1)

experiment_id = PR-EXP-03
PREREG_SHA256 = f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250
shared_surface_freeze = research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
implementation_freeze_order = source hashes -> this contract hash -> P1 generation -> evaluation
pre_result_authorization = Loop C recheck result states "PR-EXP-03 ... PASS"; residual_notes_v1 is binding
stop_semantics = missing verdict-relevant input -> INPUT_MISSING; shared/prereg/source mismatch -> HASH_MISMATCH or PREREG_MISMATCH; forbidden action required -> STOP; undefined oracle cell -> NOT_EVALUABLE cell; sanity-gate failure -> INVALID

## Verbatim SOURCE_HASH inventory

SOURCE_HASH research/positive_repair_20261011/runs/PR-EXP-03/experiment.py = d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3
SOURCE_HASH scripts/m1_statement_parser.py = 747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b
SOURCE_HASH src/biz/m1_statement_parser.py = d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8
SOURCE_HASH research/stage_e_multileaf_20261010/run_multileaf_formal.py = d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4
SOURCE_HASH research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json = 8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693
SOURCE_HASH research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json = 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163
SOURCE_HASH research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl = 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f
SOURCE_HASH research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl = 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06
SOURCE_HASH research/stage_e_method_revision_20261009/multileaf_freeze.json = 7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d
SOURCE_HASH data/research/drift_v0/input/tatqa_tables.json = 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302
SOURCE_HASH data/research/drift_v0/output/injection_map.json = d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e
SOURCE_HASH research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md = 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290
SOURCE_HASH research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json = d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4
SOURCE_HASH research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md = f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250
SOURCE_HASH research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md = a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569
SOURCE_HASH config/eval_checkpoint_trees.json = 0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25

## Enumerated verdict-relevant inventory

| Parameter | Verbatim rule or pinned value | Status / missing semantics |
|---|---|---|
| prereg | research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md; sha256 f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250 | mismatch -> PREREG_MISMATCH |
| shared freeze | research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json; sha256 d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4 | mismatch -> HASH_MISMATCH |
| SOURCE_LOCAL_RESPONSE operational test | PR-EXP-03: unique new catches vs both baselines; A0/A1 clean; constant-1 documented to fail specificity | missing -> INPUT_MISSING; prose is not substituted for operational test |
| drift membership | all records in data/research/drift_v0/input/tatqa_tables.json, each `uid` exactly once; sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302 | missing/duplicate/malformed -> INPUT_MISSING |
| all drift UID list | sorted unique UIDs, UTF-8 one UID plus LF per line | list sha256 b030d9df505eb406c00767947e6eab101a61a8f969c8e20550e68f3802be024a; missing -> INPUT_MISSING |
| held-out UID list | drift UIDs minus M/N exclusion registry; structural eligibility requires a nonempty table and header row width >= 2 | 2431/2431 eligible; list sha256 7a83aa01063be5bc10f5645236bd086771a2a16f9f2fa09b47dad782dedf8675; missing -> INPUT_MISSING |
| P1 ordering and membership | every eligible held-out UID ordered ascending by hex SHA-256 of `20261011:namespace="pr03-topology":uid`; no result or label is read for selection | 2431 ordered UIDs; list sha256 7a83aa01063be5bc10f5645236bd086771a2a16f9f2fa09b47dad782dedf8675; no eligible UID -> NOT_EVALUABLE |
| exclusion registry | exact command and list below | missing/unextractable -> INPUT_MISSING; overlap with P1 -> INVALID |
| pair selection | exact rule below | undefined pair -> NOT_EVALUABLE |
| oracle v2 source | research/positive_repair_20261011/runs/PR-EXP-03/experiment.py; sha256 d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3 | mismatch -> HASH_MISMATCH |
| canonicalizer identity | exact git_blob and raw-sha256 results below | mismatch -> HASH_MISMATCH |
| baseline runner | research/stage_e_multileaf_20261010/run_multileaf_formal.py; sha256 d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 | mismatch -> HASH_MISMATCH |
| baseline extract | lines 256-258 inclusive; extract sha256 e4cdc5c2b59e97cb51cbb5d88dc8386c9a9e08da29d541d7dfcab62aa1a21298; 188 bytes | mismatch -> HASH_MISMATCH |
| carriers | multileaf_freeze sha256 7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d; sample manifest sha256 8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693; paired artifacts sha256 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f | mismatch/ID mismatch -> HASH_MISMATCH or INPUT_MISSING |
| carrier subsample | exact rule below | empty/missing class/group -> NOT_EVALUABLE |
| bootstrap | seed 20261012; 10000 replicates; exact derived-seed rules below | missing -> INPUT_MISSING |
| arms | exact definitions below | any undefined cell -> NOT_EVALUABLE cell |
| outcome taxonomy | exactly one of POSITIVE / DIAG_ONLY / NULL / NEGATIVE / INVALID / NOT_EVALUABLE per prereg section 7 | no rescue or relabeling |

The injection map is verified at full sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e but is not an input to P1 selection or evaluation. config/eval_checkpoint_trees.json is verified read-only and is not modified.

## Shared-surface hash check results (all pre-run PASS)

| Key | Identity rule | Expected | Actual | Result |
|---|---|---|---|---|
| multileaf_response_rule_and_runner | raw_sha256 | d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 | d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 | PASS |
| multileaf_paired_artifacts | raw_sha256 | 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f | 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f | PASS |
| multileaf_prediction_rows | raw_sha256 | 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06 | 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06 | PASS |
| multileaf_preresult_freeze_manifest | raw_sha256 | 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163 | 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163 | PASS |
| canonicalizer_file | git_blob | def5161dd17fc14345d340879174ed01e0277626 | rev-parse def5161dd17fc14345d340879174ed01e0277626; hash-object def5161dd17fc14345d340879174ed01e0277626 | PASS |
| source_local_term_sheet | raw_sha256 | 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290 | 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290 | PASS |
| gb10_only_inputs[1] drift tables | sha256 prefix | 3e7e0568 | 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302 | PASS |
| gb10_only_inputs[2] injection map | sha256 prefix | d7612405 | d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e | PASS |

Verified canonicalizer value required by residual_notes_v1: raw sha256 = 747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b (GB10 informational host value). The binding identity is git_blob = def5161dd17fc14345d340879174ed01e0277626, verified by both commands. The implementation source src/biz/m1_statement_parser.py is raw sha256 d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8 and git_blob 47e379bbe8e0a5c4d637123a2e4dda73b53f06f8 by both commands.

## Verbatim M/N UID exclusion extraction command

Command executed verbatim:

`python3 -c 'import json; x=json.load(open("research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json")); print("\n".join(sorted({r["source_uid"] for r in x["rows"] if r["stage"] in {"M","N"}})))'`

Extracted registry (48 UIDs; UTF-8 one UID plus LF list sha256 e511b6ed7ad40d0b336cdf49362af728b7301b6d696322bd3ede87b883ef99cd):

```text
1a153890-b70e-4746-947b-de2ff48027ce
1b6fe333-4e8b-468e-af0c-4de123fca154
2266f020-d5ef-4343-86d3-64f3fe883976
233252a6-3a26-489a-9e55-0b8fd9004c71
28f9a92f-7b79-4cd7-ae29-2b712e0856e5
2cb3ef36-9d41-4357-8b09-205ca457a263
403e498a-59a2-4d4f-b560-a7ca853d6dc2
43fac1ff-7968-4e7b-adcc-8a611b283ff2
481dd318-a69d-498e-aa28-869093371f0a
4c0023fe-f2df-49a5-babf-bc9bcf5367ba
4fa0f9f0-4665-4faa-89e8-7d0f208331d1
515a0a4c-fae0-4b03-96f1-2961eb823479
538ada9e-1c28-447d-9ff7-b12995c2432d
5728e846-a3da-4e10-b117-738cbbce305c
5db485cf-6c57-4869-8065-14e334b4b733
5e2b5b29-e0c9-4abb-935e-a3fc13d18285
5f46a008-12b7-4c0d-b9e5-4b8e31cb0ba8
6651cfa6-fe03-41a5-8713-32eb0e3b704a
68b8d514-802c-4ebc-a754-db4a3db7f9fd
6bf238a5-0a3e-492d-91f8-7f62d3b37fba
6e698627-eeee-46e3-b1b0-76dae40aa474
725f49da-9041-4f26-8b57-62427b0a3f92
736d8572-272b-4cab-8062-9012ec6e7fe9
736f65a8-7b6b-47bc-8c6a-3a2d641695bc
73a817fc-25df-494d-b0f2-79cfdab34076
7cea4c2f-f2a9-4a25-a459-6b193e821841
8692f92d-668a-452d-be7a-2b491ee27585
8da9eb14-c639-44f7-8730-2213d34f050d
8e4af07f-365e-4b40-b1b9-502b2fa50648
906decc3-1bc8-49a4-b0ff-a79d3ce5531f
98ac5f10-46c6-431d-b5a0-0463870a87af
9b1ab08e-2478-417c-9fcb-f654f88104ff
a0bd03e7-fbb5-447f-ad77-ecc116b1134a
a9bb6c15-8103-456a-b273-7b35b2eed202
aea2257f-c275-4c9f-a4fe-81b0b39693eb
b1164469-b658-4743-910a-9508c3b21b85
c0f66238-591a-4693-b2d2-fee0f6843420
d123906f-d70e-4313-9489-3e9f38347895
d66638f7-6e4a-464b-ad17-d2a51dad9b6d
de1c7388-c0ab-45d5-9c5a-259273d3f42c
e614befa-40ae-43c0-93b1-385899b6b181
e61fed25-0910-4ae5-ad68-8ba18dfcc8f9
ed31537b-9e9b-4645-ba47-3a2af77411f8
ef1bb586-08a6-4a28-b556-191841742424
f069afb6-f2a4-43fc-8908-9686b62cf714
f440390f-d988-4765-b573-273d5e351be2
f5511f3c-b02d-4142-aa16-0b87cd61690f
f77930d9-10f3-4ea3-8557-c6554fc9c823
```

## P1 generator and pair-selection rules

For each selected UID, `pair_index = int(SHA-256_hex("20261011:pr03-pair:" + uid), 16) mod (len(table[0]) - 1)`; pair = `[pair_index, pair_index + 1]`. Swap those adjacent positions in every row that contains both positions. The generator does not read stage/family/outcome labels to choose UIDs or pairs. It preserves every cell value, every row length, the row count, and the column count. Output serialization is UTF-8 JSON Lines with sorted keys and compact separators, one LF after each row. Generator run 1 and run 2 must be byte-identical; any mismatch is INVALID.

## Oracle v2 frozen semantics

`structural_signature(table) = (column_count, ordered positional header-token sequence, row_count)` where `column_count = max(len(row) for row in table)`, header token at position j is `normalize_header(table[0][j])` when j exists and `normalize_header(None) = ""` otherwise, and `row_count = len(table)`. Pinned canonicalizer semantics are the exact implementation at src/biz/m1_statement_parser.py lines 70-74: apply regex `[\\s\\u3000\\(\\)\\[\\]{}（）【】《》<>:：;；,，.。、/\\\\\\-—_~`'\"!！?？*]+`, remove matches, lowercase, with None -> empty string.

`response = int(structural_signature(baseline) != structural_signature(injected))`, emitted only at leaf `parse.table.regression`. The oracle receives table artifacts only; it never receives mutation labels, held-out outcomes, thresholds, or field-hit scores. For a carrier with no table (stage R), the defined unchanged execution artifact is `NO_TABLE = (0, (), 0)` for both baseline and injected, so response is 0. Any genuinely missing or malformed artifact is an undefined cell -> NOT_EVALUABLE cell, not 0.

## Frozen baseline extracts and implementations

Runner file hash: d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4.

Verbatim extract from run_multileaf_formal.py lines 256-258 inclusive (188 bytes; extract sha256 e4cdc5c2b59e97cb51cbb5d88dc8386c9a9e08da29d541d7dfcab62aa1a21298):

```python
    response = {leaf: 0 for leaf in leaves}
    response["parse.table.regression"] = int(mutated_hit < baseline_hit)
    response["parse.field.hit_rate"] = int(mutated_hit < baseline_hit)
```

The v1 aliased baseline selects `parse.table.regression` from that extract. The standalone field-hit baseline independently computes the unchanged formula from lines 248-254 and selects `parse.field.hit_rate`. Both use the same population and one leaf response per case. Both are compared to oracle v2 without alteration.

## Arms

- A0 no-op/identity: `structural_signature(table) != structural_signature(table)` on every P1 table; expected 0.
- A1 value-only specificity: select the non-header cell at flattened row-major index `int(SHA256("20261011:pr03-value-only:" + uid), 16) mod number_of_non_header_cells`; replace it with `__PR03_A1_VALUE__`, appending underscores only if needed to ensure a different string. Structure is preserved; expected 0.
- A2 P1: the frozen adjacent-column transposition; expected 1.
- A3 M1 regression: all 72 frozen M carrier rows; construct the injected table by changing only `source_object.cell` to `field_after`; expected 0.
- Constant-1 control: returns 1 on P1, A0, and A1; P1 coverage is 1 but A0/A1 false positives are both denominators, so specificity fails and it cannot support POSITIVE.

Carrier construction used for diagnostic evaluation: M changes only `source_object.cell` to `field_after`; N changes only `source_object.mutated_cell` to `value_after`; R has the defined unchanged NO_TABLE artifact. Source table JSON hashes are checked before construction.

## Mixed diagnosability population and classifier

Carrier subsample rule: group all 216 frozen carrier rows by `cluster_id`; within each group choose the row minimizing `(SHA-256_hex('20261011:namespace="pr03-carrier-subsample":' + cluster_id + ':' + sample_id), sample_id)`. This yields exactly one row per cluster and never changes carrier artifacts. Mixed population = all 2431 P1 rows plus this 72-row carrier subsample.

Ground truth is read only after freeze: P1 uses prereg-fixed `stage_label="M"` and `family_label="topology_transposition"`; carrier rows use the frozen manifest fields `stage` and `injection_operation`. LOCO group = `source_uid` for both P1 and carriers, so a shared source UID remains in one held-out group and there is no source overlap across folds.

Classifier is the frozen deterministic nearest-centroid rule: one scalar binary feature, Euclidean distance equivalent to absolute distance; leave one source_uid group out; train centroids on remaining groups; classes present in the full mixed population; tie -> `__TIE__` and scored incorrect. Macro-F1 uses the union of truth and prediction labels, including ties as prediction-only labels. Primary `Δdiag = min(Δstage_macro_F1, Δfamily_macro_F1)` against the v1 aliased baseline. Stage and family deltas are both reported at conclusion level only.

Coverage delta cluster bootstrap: resample P1 source_uid/table groups with replacement, 10000 replicates, seed 20261012, NumPy-free deterministic `random.Random`; percentile interval uses linear interpolation at 2.5% and 97.5%. Diagnosability cluster bootstrap: resample mixed source_uid groups with replacement, 10000 replicates; metric-specific seed is the integer represented by the first 16 hexadecimal digits of SHA-256 of `20261012:diag:stage_label` or `20261012:diag:family_label`; same percentile rule. Wilson 95% intervals are used for individual binary rates. Counts are raw exact numerators/denominators.

## Sanity, attribution, cost, and outcome gates

Sanity gate: on P1, oracle v2 must differ from standalone field-hit on at least one row; on all 216 frozen carriers, oracle v2 must not be a monotone binary function of standalone field-hit. A binary mapping is monotone when each field-hit value maps to at most one structural value and the two ordered outputs are nondecreasing or nonincreasing. Any failure -> INVALID.

Attribution pass = unique new catches against both baseline oracles AND A0/A1 structural false-positive counts are zero AND the constant-1 rule is documented to fail A0/A1 specificity. The SOURCE_LOCAL_RESPONSE prose does not override this per-experiment operational test.

Cost: exactly one leaf response per case for each oracle on P1, A0, A1, A3, and mixed diagnosability. Exact check-count equality is the only cost tolerance; no runtime performance claim. model_calls=0, judge_calls=0, training=0, network=0, database=0, production-service calls=0. Runtime is recorded only as cost ledger time.

Outcome priority after executable/defined gates: INVALID for sanity, UID overlap, double-run mismatch, cost inequivalence, label access before freeze, or post-freeze edit; NOT_EVALUABLE for missing/undefined P1 or oracle semantics; NEGATIVE if Δdiag < -0.02; POSITIVE only if coverage delta >0 with CI lower>0, Δdiag >= -0.02, A0/A1 pass, no A3 regression, and attribution pass; DIAG_ONLY only on the prereg's nonpositive/CI-inclusive coverage branch with Δdiag > +0.02; otherwise NULL. Exactly one canonical label is emitted.

## Binding residual addendum application

residual_notes_v1.md is read and incorporated before P1: canonicalizer verified sha256 recorded; SOURCE_LOCAL_RESPONSE pinned by sha256 and its PR-EXP-03 operational test is binding; full GB10 drift and injection-map hashes are recorded; the inventory above is exhaustive with INPUT_MISSING semantics; drift membership, UID list/exclusion registry, pair rule, oracle source, baseline extract hashes, arms, and bootstrap seed are enumerated. Frozen multileaf carriers, D3 inputs, drift outputs, config/eval_checkpoint_trees.json, tests, and frozen hashes remain read-only.
