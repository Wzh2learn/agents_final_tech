# Valentine full benchmark structure audit（2026-10-05）

> Status: `READ_ONLY_STRUCTURE_AUDIT_PASS / ROUTE_STOP_CONSERVATIVE_CLUSTERS_LT_40`
> Source: Zenodo DOI `10.5281/zenodo.5084605`, `Valentine-datasets.zip`, CC-BY-4.0
> Boundary: no full archive download, no extraction, no adapter run, no A0-A3/Phase 2/B5/training

## 1. Source and transport receipt

Zenodo metadata reports one file:

| Field | Value |
|---|---|
| Archive | `Valentine-datasets.zip` |
| Size | `602150347` bytes |
| Checksum | `md5:98da6d6701806538e5c685f4426b95f6` |
| Licence | `cc-by-4.0` |
| DOI | `10.5281/zenodo.5084605` |

The archive body was not downloaded. Two bounded HTTP Range audits read the ZIP central directory and representative entry schemas:

| Audit | Range bytes | Requests | Retries | Full download |
|---|---:|---:|---:|---|
| Central directory | `1,578,443` | 7 | 0 | false |
| Representative schemas | `6,034,891` | 24 | 0 | false |

Transport receipts and manifests:

- `docs/datasets/2026-10-05_valentine_full_remote_structure_receipt_v1.json`
- `docs/datasets/2026-10-05_valentine_full_entry_manifest_v1.json`
- `docs/datasets/2026-10-05_valentine_full_schema_audit_v1.json`
- `docs/datasets/2026-10-05_valentine_full_structure_summary_v1.json`

## 2. Archive inventory

The ZIP contains 7,746 entries. After excluding 3,873 `__MACOSX` AppleDouble entries, the real `Valentine-datasets` tree contains 3,873 entries: 3,303 files and 570 directories.

The real files comprise:

- 2,755 core pair files: 551 pairs × 5 required files;
- 540 generated `config_<pair>.ini` files;
- 7 `.DS_Store` metadata files, excluded from the data contract;
- 1 nested auxiliary `prospect_horizontal_50_ec_av.zip`, excluded from the pair contract.

No real pair directory lacks one of the five required files.

## 3. Pair counts, sources, scenarios, and dataset families

There are **551 pair directories**:

| Dataset family / source | Pair count | Base origin visible in pair names |
|---|---:|---|
| Magellan | 7 | seven legacy entity-matching pair names |
| OpenData | 180 | `miller2` |
| Wikidata | 4 | `Musicians` |
| TPC-DI | 180 | `prospect` |
| ChEMBL | 180 | `assays` |

Normalized scenario counts from directory paths:

| Scenario | Count |
|---|---:|
| Joinable | 145 |
| Semantically-Joinable | 145 |
| View-Unionable / View -Unionable | 145 |
| Unionable | 109 |
| Magellan legacy pairs without a scenario directory | 7 |

The third-party description of 551 pairs and four relatedness scenarios is therefore supported at the **pair-directory** level. It is not evidence of 551 independent origins.

## 4. Shared origins and conservative independence clusters

A generated pair name encodes a base dataset followed by perturbation parameters. All pairs with the same base prefix are conservatively treated as one origin component. Magellan pair names are grouped when they share a named underlying source entity.

| Conservative origin component | Pairs | Reason |
|---|---:|---|
| `OpenData/miller2` | 180 | all names derive from `miller2` |
| `TPC-DI/prospect` | 180 | all names derive from `prospect` |
| `ChEMBL/assays` | 180 | all names derive from `assays` |
| `Wikidata/Musicians` | 4 | four scenarios share `Musicians` |
| `Magellan/amazon_shared` | 3 | `amazon_google_exp`, `walmart_amazon`, `itunes_amazon` share Amazon |
| `Magellan/dblp_shared` | 2 | `dblp_acm`, `dblp_scholar` share DBLP |
| `Magellan/beeradvo_ratebeer` | 1 | no shared named source in the seven-pair set |
| `Magellan/fodors_zagats` | 1 | no shared named source in the seven-pair set |

This yields **8 conservative shared-origin components**. A stricter dataset-family grouping would yield only 5. Both counts are below 40.

Decision:
`conservative_independence_clusters=8 < required_40`. The hard stop condition is triggered. The gap is 32 components under the conservative grouping, or 35 under the stricter family-level grouping.

## 5. Actual source / target / ground-truth file structure

The eight representative schema inspections cover all five families and all four generated scenarios.

Every pair uses the same five-file contract:

```text
<pair>_source.csv
<pair>_source.json
<pair>_target.csv
<pair>_target.json
<pair>_mapping.json
```

Generated pairs additionally contain:

```text
config_<pair>.ini
```

Observed structures:

- `source.csv` / `target.csv`: one CSV header plus data rows; row and column counts vary by family and perturbation.
- `source.json` / `target.json`: column-keyed JSON objects; each column value contains a `type` field. These are schema metadata, not process traces.
- `mapping.json`: an object containing a `matches` array. Each match structurally contains string fields `source_table`, `source_column`, `target_table`, and `target_column`. Mapping values were not disclosed or used to generate action/target labels.
- `config_<pair>.ini`: sections `Approximation`, `Columns`, `Files`, `Paths`, and `Properties`; values were not disclosed.

The schema audit explicitly records:
`ground_truth_use=STRUCTURE_ONLY_NO_VALUES_DISCLOSED_NO_ACTION_TARGET_GENERATION`.

## 6. Checkpoint evidence feasibility

The archive contains source/target data, schema metadata, ground-truth mappings, and generated configuration files. It contains **no native matcher trajectory, checkpoint stream, event log, accept/reject trace, revision/rewrite trace, or finalization receipt**.

Therefore:

1. source and target files can drive a matcher;
2. checkpoint evidence cannot be read directly from the archive;
3. checkpoint evidence would require instrumenting a real matcher run and recording only events the matcher actually emits;
4. any absent stage must remain `unmeasurable` / `not_present`; it must not be fabricated;
5. ground truth cannot generate action/target labels or gold pipeline output;
6. action/target must still come from an independent Q3 process, and correctness may be joined from ground truth only after R1/R2/ADJ and the final ledger are sealed.

This is a feasibility statement only. No matcher or process adapter was run.

## 7. Hard-stop decision

Because the conservative independent cluster count is 8, below the required 40, the frozen stop rule applies before any download annex or adapter implementation:

- **Stop the Valentine full benchmark + frozen process adapter route.**
- Do not submit a selected-pair download annex.
- Do not download the 602 MB archive.
- Do not implement or run the process adapter.
- Do not start A0-A3, Phase 2, B5, or training.
- Accept `DATA_NO_GO / RQ2 NOT_IDENTIFIED` as the formal negative-result boundary.
- Keep the small paper on the mature Stage E fallback.
- Move the full Evaluate-Distill-Evolve validation to future work.

This decision does not say that no future dataset can support RQ2. It says that the currently selected Valentine full benchmark cannot meet the preregistered independence-cluster requirement under conservative shared-origin grouping.

## 8. Artifact hashes

- `docs/datasets/2026-10-05_valentine_full_remote_structure_receipt_v1.json`: `732b89bab957a55d0199d8db579e202acbe408ecfa4533aff1e2ba77f6674418`
- `docs/datasets/2026-10-05_valentine_full_entry_manifest_v1.json`: `9049994f2047e96afd825a93f895c787f9595fb05748c6d901cb0a3ebad31ee0`
- `docs/datasets/2026-10-05_valentine_full_schema_audit_v1.json`: `14b4368c723c25c8a9e17595b64d425c168c6d4cc443a8970c827fa1cbe64f12`
- `docs/datasets/2026-10-05_valentine_full_structure_summary_v1.json`: `fa3274bc884b7947b0daec5782f07d046b4de9023f829f9cb25c4f6af2cb51cf`

The first three hashes were independently re-read on GB10 after their range audits. The summary hash is bound at the point of this report; its values are mechanically derived from the entry manifest and schema audit.