# Runtime Requalification Change Record

Preserved failed rounds:

- `failed_run_5a389f0e/`: original strict-wrapper failure.
- `failed_run_21e83312/`: metadata-wrapper plus `/no_think` retry, still empty content.

## Authorized runtime fix

1. Send top-level JSON boolean `chat_template_kwargs.enable_thinking=false` on every `/v1/chat/completions` request.
2. Restore prompts to their pre-`/no_think` text; task wording is unchanged.
3. Keep `timings` and optional `reasoning_content` as metadata, while empty content remains a qualification failure.
4. Stop fixture qualification at the first failed fixture instead of mechanically consuming all six fixture requests.

Unchanged: task/reference manifest, model, tokenizer, chat template, source split, JSON protocol, tool/scoring semantics, generation parameters, `max_tokens=256`, and sample counts.

Status is `RUNTIME_REQUALIFICATION_REQUIRED`, not an experience-learning result.

## Output-contract consistency fix

Preserved third-run bundle and raw evidence under `failed_run_8819c732/` and the fixed run root.

1. Render the authoritative `OUTPUT_SCHEMAS.json` object and generated field rules into every model-visible plan/consume message.
2. Validate `tool == "calc"` before calculator execution; reject aliases and non-strings without rewriting.
3. Keep consume enum strict: `ANSWER`, `UNKNOWN`, `REFUSE`; never convert `OK`.
4. Preserve raw model output unchanged and enforce existing required keys, types, constants, enums and lengths.

Task/reference, model, thinking switch, `max_tokens=256`, tool/scoring semantics and source split remain unchanged.
