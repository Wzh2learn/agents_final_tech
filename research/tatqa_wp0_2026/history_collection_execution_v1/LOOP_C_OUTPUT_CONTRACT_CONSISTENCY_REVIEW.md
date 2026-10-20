# Loop C Output-Contract Consistency Review

- Task id: `output-contract-review-20261018-r1`
- **Verdict: `ACCEPTED`**
- **Blocker count: 0**
- Zero model, endpoint, judge, training, collection, or service calls.

## Verified

1. `OUTPUT_SCHEMAS.json` is the authority for plan/consume keys, constants, enums and lengths.
2. Each model-visible message contains its complete schema JSON and generated rules, including `calc`, `ANSWER`, `UNKNOWN`, `REFUSE`, and non-answer null requirements.
3. `validate_plan_response` rejects `calculator`, aliases and non-strings before tool execution and never rewrites the tool name.
4. `validate_consume_response` rejects `OK`, enforces exact keys/types/lengths and requires nulls for `UNKNOWN/REFUSE`.
5. Valid `calc/ANSWER`, `UNKNOWN`, and `REFUSE` objects pass; raw response preservation is unchanged.
6. `chat_template_kwargs.enable_thinking=false` remains a top-level JSON boolean and the manifest remains `5be130d7...`.

Non-blocking hardening notes:

- Generate an explicit positive `ANSWER` field rule in addition to the non-answer null rule.
- Bind validator constants to `OUTPUT_SCHEMAS.json` or add a consistency assertion.
- The independent reviewer read pure code paths and test assertions but could not run Python under its permission gate; local and GB10 receipts independently ran 17/17.

This review authorizes nothing.
