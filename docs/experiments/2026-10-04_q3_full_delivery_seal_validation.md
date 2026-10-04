# Q3 full delivery seal validation (2026-10-04)

> Status: `SEALED_WITH_VISIBILITY_EXCEPTIONS` | `seal_complete=true`
> Local evidence: `logs/graph/q3_raw_seal_20261004/`
> GB10 evidence: `/home/testuser/wzh/q3_raw_seal_20261004/inbox/q3_raw_seal_20261004/`

## 1. Package integrity

The delivery contains 10 files. All 9 entries in `sha256_manifest.txt` are present and hash-identical; `sha256_manifest.txt` is itself preserved with SHA256 `0b2c470404286d87782755a92c76f953a2b8599905404a012cfd190f0294aeab`. Secret-pattern scan returned zero hits.

| Role | File | Rows | SHA256 |
|---|---|---:|---|
| R1 | `r1_chat_raw_output.txt` | 146 | `f1de10f8c75016330ad6874707ff12118a399993f967e889d0c377fe395e0aa0` |
| R2 | `粘贴的 Markdown (1).md` | 146 | `2b6d792dac2ec394f238380d869586896ef2fefea39eb35d539ffbd602d00378` |
| ADJ | `adj_chat_raw_output.txt` | 27 | `a2bfef296dae28c62003d68802e84f4bcddf5f1dc12049fcc3105b21dd92212c` |
| Final pre-correction | `q3_gold_adjudicated_v1.txt` | 146 | `baa4ebf27d77c72825fba003b8316853a5d8370563b63f4e181a696c24f3fb8a` |
| Final corrected | `final_q3_label_ledger_corrected_v1.txt` | 146 | `cf339cef8b7065dad05f574a1400415a7bff64b78b66e1db38f74143cc49ccb6` |

## 2. Mechanical cross-check

- R1 action counts: `map_to=57 / skip=60 / hold=29`.
- R2 action counts: `map_to=41 / skip=49 / hold=56`.
- Exact R1/R2 agreement: `119/146 = 81.5068%`.
- Disagreements: `27`; ADJ contains exactly those 27 sample IDs with no missing or extra rows.
- Action-only Cohen's kappa: `0.7265348595`, consistent with the reported `≈0.727`.
- The pre-correction final ledger is exactly the 119 R1/R2 agreements plus the 27 ADJ decisions. Mechanical derivation errors: `0`.
- Corrected ledger differs from pre-correction in exactly one row, line 61:
  `map_to | pap_curb_sec` -> `hold | null`.
- Corrected action counts: `map_to=51 / skip=58 / hold=37`.
- Corrected target validation: `146/146` sample IDs aligned to the input package; zero invalid or non-null target errors.

## 3. Visibility exceptions

The raw artifact package is closed, but reviewer-visibility certification is not absolute:

- R1 is gold-isolated and reviewer-isolated from `ground_truth`, source-side gold, pipeline mapping, injection map, R2, and ADJ.
- R1 saw `lineage_root_id` / table grouping, so it must not be described as a strict three-field-only review.
- R2 and ADJ raw outputs are archived, but their sessions did not provide separately signed visibility receipts.

Therefore the correct evidence label is `ARTIFACT_CLOSED_WITH_VISIBILITY_EXCEPTIONS`, not an unqualified strict blind-review PASS.

## 4. Scientific boundary

This seals exploratory Q3 evidence only. It does not change `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, Stage D, Stage R, RQ4, training, or external-release status.
