# Multi-Leaf Pre-Result Freeze Receipt v1

FREEZE COMPLETE

Captured: `2026-10-10T01:01:51+08:00`

Temporal order enforced:

```text
FREEZE COMPLETE
-> materialize formal evaluator outputs
```

The formal result directory did not exist when this receipt was generated. No M/R/N formal evaluator output was read or created before this receipt.

## Immutable identities

- Git HEAD: `e97340387888290e69fbfff122ab163de971b37e`
- Git diff SHA-256: `be2c114561d3798e4227897612b51f8fc0de9e616dbc5863516d9cde248e2ad8`
- Git status SHA-256: `dc4403e0de6d3d4a4e7f8825b332fd0197df326964e1975ef531dcdbfb4b16dd`
- Manifest SHA-256: `15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163`
- Formal runner SHA-256: `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4`
- Sample manifest SHA-256: `8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693`
- Task-card section SHA-256: `023f5a58ce7fb56235f7a613bce4e537541794dedab52b845dfbccd2bdd1a42a`
- Environment snapshot SHA-256: `190474fdba454e8da735ec5b1ecbb7fa96b6a4e6a30ee9211a0418897a7d5293`

## Frozen scientific contract

- Primary RQ: Do checkpoint visibility signatures contain stage-localizing information?
- Gold: expected first affected stage `M/R/N`.
- Predictor: `deterministic nearest-centroid with Euclidean distance on leave-one-cluster-out training folds`.
- Response vector: `all leaves from config/eval_checkpoint_trees.json in frozen tree order; binary paired response vector`.
- Tie rule: `a distance tie is scored incorrect; M/R/N lexical order is used only to serialize a deterministic output`.
- LOCO rule: `leave one stage-namespaced table/document/origin cluster out; all three repeated injections stay in the held-out fold`.
- Primary metrics: `macro-F1, top-1 stage accuracy`.
- Chance top-1: `0.3333333333333333`.
- Majority baseline: `predict the first frozen class M; top-1=1/3 and macro-F1=1/6 on the balanced freeze`.
- Permutation: seed `20261011`, `10000` replicates.
- Bootstrap: seed `20261012`, `10000` replicates.
- Sample tier: `TARGET`, 24 clusters/stage x 3 injections = 72 clusters / 216 injections.
- Claim scope: `pooled/macro localization only`.

## Stop conditions

- Any M/R/N stage contract fails: STOP_THAT_STAGE and classify confirmatory result INVALID.
- Any UID/origin leakage or fold contamination: classify INVALID.
- Fewer than two population-responsive leaves: localization remains unestablished.
- Expected-stage or predictor definitions change after result access: classify INVALID.
- Any flat/hierarchy secondary result cannot overwrite the primary localization result.

## Frozen files

- `/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json`: `07395642f317754ed22bd8330525af7c1e15b7189efdf046cd0a257fc3178fcb` (1210555 bytes)
- `/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_test_gold.json`: `e6758315b839203a72e05f8849ce4d56fc8d6d7c34dc0240352769014807f5da` (1229595 bytes)
- `/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_train.json`: `3025b4ca9c3c87f5ecd2c504371e1ee92929ef1f31d8a3ac38bc3a5376582fab` (9722633 bytes)
- `config/eval_checkpoint_trees.json`: `0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25` (7215 bytes)
- `data/research/drift_v0/input/tatqa_tables.json`: `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` (1442890 bytes)
- `docs/research/stage_e_multileaf_power_plan_v1.md`: `3a5778bd8a4bac580be2d3bb0c969128a7d6ff8dde2aa522336e167401825a62` (3137 bytes)
- `docs/research/stage_e_multileaf_preregistration_v1.md`: `e489c32cc50bdadc34247e3102d896bd23ac185507ca225acc53906504766934` (10886 bytes)
- `research/stage_e_method_revision_20261009/multileaf_freeze.json`: `7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d` (558712 bytes)
- `research/stage_e_multileaf_20261010/build_multileaf_preresult_freeze.py`: `b60c3e5fa16b4e446743dccc360bc85880d147594c44a2b762de3b26c003664c` (13235 bytes)
- `research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json`: `8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693` (182830 bytes)
- `research/stage_e_multileaf_20261010/run_multileaf_formal.py`: `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4` (35423 bytes)
- `tests/test_multileaf_formal_contract.py`: `b315f926ea34d4c6eae83e7e5d4b8f93d7b6ee797134cbec3637e68b4e31a22a` (1996 bytes)

## Post-freeze rule

After `FREEZE COMPLETE`, the listed files, sample IDs, expected stages/checkpoints, predictor, response-vector rule, tie/LOCO rules, baselines, metrics, seeds, sample-size tier, stop conditions and secondary aggregation contract must not be modified after any formal result is read. Any required correction invalidates this confirmatory run and requires a new preregistration namespace.
