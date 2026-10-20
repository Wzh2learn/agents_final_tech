# Loop C Output-Contract Consistency Review

Task id: `output-contract-review-20261018-r1`
Mode: read-only targeted review of one output-contract increment. Do not issue model requests or authorize execution.

Verify the full path:

1. `OUTPUT_SCHEMAS.json` is the authority for plan/consume keys, constants and enums.
2. Every model-visible plan/consume message contains the complete schema JSON plus generated rules, including `calc`, `ANSWER`, `UNKNOWN`, `REFUSE`, and non-answer null requirements.
3. `validate_plan_response` rejects `calculator`, aliases, and non-strings before tool execution; it never rewrites the tool name.
4. `validate_consume_response` rejects `OK`, enforces exact keys/types/lengths, and requires nulls for `UNKNOWN/REFUSE`.
5. Valid `calc/ANSWER`, `UNKNOWN`, and `REFUSE` objects pass; raw response preservation remains unchanged.
6. The real request payload still contains boolean `chat_template_kwargs.enable_thinking=false`, and task/reference manifest remains `5be130d7...`.

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED` with blocker count. Recommend a report filename that does not overwrite prior independent reviews.
