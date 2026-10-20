# MA-CERD Gold Public v1

MA-CERD is an anonymized, synthetic and simulator-backed benchmark for evaluating how requirement, authority, evidence, state, and expression interventions affect multi-agent joint plans.

## Contents

- `data/ma_cerd_gold_public_v1.jsonl`: one Gold record per line
- `data/ma_cerd_gold_public_v1.json`: collection wrapper
- `metadata/dataset_summary.json`: aggregate counts and claim boundary
- `metadata/family_split_manifest.csv`: leakage-resistant family/base split mapping
- `metadata/privacy_release_audit.json`: anonymization audit
- `schema/ma_cerd_contract_v1.schema.json`: record schema
- `scripts/validate_release.py`: integrity and privacy validation
- `scripts/evaluate_predictions.py`: reference evaluator
- `docs/DATA_DICTIONARY.md`: field definitions
- `docs/DATASET_CARD.md`: provenance, limitations, and release boundary
- `docs/INTENDED_USE.md`: intended and prohibited uses
- `SHA256SUMS.json`: content manifest
- `LICENSE.md`: dataset/documentation license and citation notice
- `LICENSE_CODE_APACHE-2.0.txt`: software license for scripts

## Quick validation

```bash
python scripts/validate_release.py
```

## Prediction format

Provide JSON Lines with `contract_id`, `relation`, `acceptable_decisions`, `impact_node_ids`, and `preserved_node_ids`, then run:

```bash
python scripts/evaluate_predictions.py predictions.jsonl
```

## Evidence status

All 1,000 records have completed O1, anonymized blind O2 adjudication, deterministic simulator-only shadow-mode O3, and resolved alignment. Reviewer identities, signatures, email, correspondence, raw free text, and private response-collection bindings are excluded.

Gold means benchmark evidence, not operational authorization, certified simulator fidelity, physical-flight validity, deployment readiness, weapon-control authority, or real-world safety.

## License

The MA-CERD dataset, metadata, schema, and documentation are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. The Python scripts under `scripts/` are licensed under **Apache License 2.0**. See `LICENSE.md` and `LICENSE_CODE_APACHE-2.0.txt`.

Zenodo concept DOI for the dataset series: **10.5281/zenodo.21946187**.
