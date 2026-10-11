# PR-EXP-03 v3 implementation contract (frozen before the v3 formal run)

experiment_id = PR-EXP-03
version = v3
PREREG_SHA256 = 4c632300a588e2b20d05a66ee0d5b104490313959c8c12a14c94bf316f658445
shared_surface_freeze = research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
implementation_freeze_order = source hashes -> this contract hash -> P1 generation -> evaluation
stop_semantics = missing input -> INPUT_MISSING; shared/prereg/source mismatch -> HASH_MISMATCH or PREREG_MISMATCH; undefined oracle cell -> NOT_EVALUABLE cell; sanity-gate failure -> INVALID
v3_change_1 = PATH A: field_hit is total (empty/header-less table -> 0 observable hits -> response 0); no population exclusion
v3_change_2 = sanity gate replaced: non-degeneracy = oracle fires on P1 (>=1) AND A0/A1 structural false positives == 0 AND oracle differs from field-hit on >=1 P1 row. The round-1 carrier-monotonicity clause is removed (unsatisfiable-by-construction on structurally-null carriers).
unchanged = oracle semantics, populations, split, bootstrap seed 20261012 / 10000 reps, arms A0/A1/A2/A3, metrics, outcome taxonomy, and all SOURCE_HASH inputs below

## SOURCE_HASH inventory (verified against GB10 raw bytes)
SOURCE_HASH data/research/drift_v0/input/tatqa_tables.json = 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302
SOURCE_HASH data/research/drift_v0/output/injection_map.json = d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e
SOURCE_HASH research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json = 8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693
SOURCE_HASH research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json = 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163
SOURCE_HASH research/stage_e_method_revision_20261009/multileaf_freeze.json = 7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d
SOURCE_HASH research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl = 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f
SOURCE_HASH research/stage_e_multileaf_20261010/run_multileaf_formal.py = d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4
SOURCE_HASH scripts/m1_statement_parser.py = 747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b
SOURCE_HASH src/biz/m1_statement_parser.py = d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8
SOURCE_HASH config/eval_checkpoint_trees.json = 0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25
SOURCE_HASH research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json = d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4
SOURCE_HASH research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md = 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290
SOURCE_HASH research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v3.md = 4c632300a588e2b20d05a66ee0d5b104490313959c8c12a14c94bf316f658445

## Notes
- The oracle, drift membership, UID list/exclusion registry, pair rule, arms, and bootstrap rules are unchanged from the v2 contract and remain in force; see research/positive_repair_20261011/runs/PR-EXP-03/implementation_contract.md for the verbatim v2 detail retained by reference.
- Frozen multileaf carriers, D3 inputs, drift outputs, config/eval_checkpoint_trees.json, tests, and frozen hashes remain read-only.