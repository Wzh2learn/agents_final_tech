# Paper E Layer-1 v4 Contract Errata v1

> Applies to: `LAYER1_V4_COMPACT_CONTRACT_v3.json`
> Contract sha256: `322c3b380d9f36d2603e89eef49f296d86c012497b442ec9c77b36c0adbdc8aa`
> Issued after the held-out run and post-result audit. No result changes.

## N1 operative reading

`injection_id_definition` is read as using:

`json.dumps(..., ensure_ascii=False, separators=(",", ":"))`

for each of the seven fields `uid, col, original, injected, type, variant, seed_component`,
joined with `U+001F`.

The `ensure_ascii=False` setting is load-bearing: the default (`True`) would produce a
60/58 held-out/dev split instead of the frozen 59/59. The frozen runner and all results use
`ensure_ascii=False`. This errata records that operative reading; no re-run is required.
