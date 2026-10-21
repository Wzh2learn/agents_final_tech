# VersiCode Observability Pre-Model Report

- Evidence identity: `DEV_ONLY_EXTERNAL_VERSION_CHANGE_OBSERVABILITY_ABLATION`
- Tasks: `8` unique dependency/name-change families
- Arms: `base, prose_mapping, structured_mapping, probe_evidence`
- Planned model attempts: `32`
- Retries: `0`; concurrency: `1`
- Gold code is present only in `VERSICODE_TASKS.json.oracle` and never in prompts.
- BASE prompts exclude the hidden target symbol; PROSE and STRUCTURED contain the same mapping facts.
- PROBE evidence is generated only from the exact target package artifact and the old symbol name.

This is a DEV_ONLY observability ablation. VersiCode reference code is not a behavioral oracle.
