# Authorized Change Record

Authorization: `AUTHORIZED_BOUNDED_SINGLE_COLLECTION`
Baseline bundle: `0d13f55609633dd3c9943cc95036c59187297d7542c8bdc01a1812c5e965e3b5`
Baseline preserved at: `baseline_0d13f556/`

## Allowed changes

1. `collection_runner.py`: check the active window before every request, require the full request timeout to fit before expiry, stop new requests at expiry, and persist partial `EXECUTION_RESULT.json`.
2. `collection_runner.py`: run three qualification fixtures first as six requests; fail closed with history request count 0 unless parse/schema/tool/reference qualification passes.
3. `build_task_manifest.py` / `EXECUTION_PLAN.json`: order the same 54 request slots fixture-first. Task/reference manifest remains byte-identical.
4. Tests and receipts: add window-expiry, fixture-failure-zero-history, fixture-first order, and total-cap regressions.
5. Bundle and change artifacts: new bundle, manifest comparison, targeted re-audit, and authorization binding.

## Explicitly unchanged

- `TASK_REFERENCE_MANIFEST.json` SHA-256 remains `5be130d7d6c3514862ad44149ec61b95ba68c8d83178e259aa7da90904633db6`.
- Model, tokenizer, chat template, prompt contents, generation parameters, `max_tokens=256`, source split, selected tasks, references, and sample counts are unchanged.
- No online request, service start/restart/switch, pilot, training, memory write-back, source change, retry, top-up, or public release occurred during this change set.
