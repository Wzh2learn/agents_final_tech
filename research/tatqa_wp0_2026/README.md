# TAT-QA WP-0 - tracked scripts and probes

> purpose: reproduce the WP-0 TAT-QA measurements (A1 licence, A2 raw fetch, A3/A4 origins + candidate items, A5 adapter/checker contract, A6 qualification appendix)
> runtime outputs are GB10-only and gitignored: raw archives under `data/research/tatqa_raw_2026/`, built objects under `data/research/tatqa_wp0_2026/`.

## Files
- `build_origins.py` - deterministic origin builder (stdlib only). Reads the raw archives, writes `origin_manifest.json`, `candidate_items_v1.json`, `GENERATION_RECEIPT.json`.
- `probes/p5_record_shape_and_signature_probe.py` - record schema + paragraph-set signature uniqueness (2467/2479 signatures; origin = one raw record is the valid grouping rule).
- `probes/p6_distribution_scan.py` - `req_comparison` / `answer_type` / `answer_from` / `scale` distributions.
- `probes/p7_comparison_pool_probe.py` - comparison+arithmetic+table+scale+multi-period eligibility scan (measured: `req_comparison=true` questions are `span`-type with empty scale; intersection with arithmetic+scale is 0).
- `probes/p8_funnel_scan.py` - the staged funnel counts (843 -> ... -> 0).
- `probes/p9_constructible_pool_probe.py` - constructible pool: 184 records satisfy multi-period + unit + >=1 numeric two-period row; 176 with >=2 usable rows.

## How to run (GB10, from the repo root)
1. `bash scripts/research/fetch_tatqa_raw.sh` - fetch + integrity-gate the raw archives (data: CC BY 4.0; repo: MIT; see `docs/datasets/tatqa_licence_record_v1.md`).
2. `python3 research/tatqa_wp0_2026/probes/p5_record_shape_and_signature_probe.py` (and p6-p9 as needed).
3. `python3 research/tatqa_wp0_2026/build_origins.py`

## Frozen measured facts (2026-10-13)
- raw archives: train 2201 + dev 278 = 2479 records; sha256 train `2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69`, dev `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`.
- build: origins 182; origins_with_ge2_usable_rows 176; candidate_items 60 (60 distinct origins).
- `origin_manifest.json` sha256 `3718e6fef4d52bec0c1c29b47ba9ab60e298754b9e8527835d09c9d223d70cea`; `candidate_items_v1.json` sha256 `bc55fe7a53381f32e5d84ff6c17ced18ec72fd322f98a9f80c4eccb714caac12` (see `GENERATION_RECEIPT.json` on GB10).

These numbers are the frozen WP-0 measurement facts; do not re-derive differently for the qualification appendix.
