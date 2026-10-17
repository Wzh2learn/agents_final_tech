# TQ-5 recovery snapshot v1

This directory is the immutable execution snapshot for the single authorized TQ-5 run.

- `chain_config_tq5_frozen.json` is the actual run config. Relative to the source config it changes only `root` to the GB10 Linux absolute path, points `templates_md` at the copied frozen template, and adds `snapshot_manifest`.
- `chain_runner.py` and `tq4_scoring_entry_v21.py` are byte-for-byte copies of the TQ-4 execution files already point-checked for TQ-5.
- `prompt_templates_v2.md` is a byte-for-byte copy of the frozen template.
- `chain_analyze.py` is a new analysis version. It preserves raw decisions but renders parse failures as `invalid`, supports isolated output directories, and includes the execution snapshot hashes in the generated run/analysis manifest.
- `tq5_snapshot_entry.py` refuses formal run/analysis unless every snapshot file matches `SNAPSHOT_MANIFEST.json`, the exact frozen config is used, and `--root` is the Linux execution root.

No TQ-4 run output, frozen material, old config hash, or `RUN_META` value is modified. The missing TQ-4 run-time config snapshot remains an explicit provenance gap.
