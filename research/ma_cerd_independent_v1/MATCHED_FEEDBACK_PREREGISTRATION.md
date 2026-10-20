# Matched Feedback Experiment

Status: `FROZEN_BEFORE_REQUESTS`
Evidence identity: `INDEPENDENT_MACERD_DEVELOPMENT`

## Design

Select 15 MA-CERD test contracts from distinct families: 8 change and 7
invariant, balanced across intervention target kinds by deterministic
SHA-256 ordering. Each contract is evaluated under:

- prior: `correct` or `wrong`;
- feedback: `no_feedback`, `exact_match`, `sufficiency_only`, `composite`.

This produces 15 x 2 x 4 = 120 requests. Correct and wrong priors are fixed
before execution. Every arm receives the same revision state:

- correct prior -> `RETAIN`;
- wrong prior -> `REVISE`.

Feedback text uses a common template and comparable length. Only the rule
criterion differs. No gold answer is shown.

## Metrics

- Primary: wrong-prior repair rate, defined as exact relation + exact
  acceptable-decision set + impact F1 1.0 + preserved F1 1.0.
- Primary: correct-prior regression rate, defined as any loss of exact match.
- Secondary: relation accuracy, handling exact match, impact F1, preserved
  F1, parse validity, token cost.
- Aggregate by feedback arm and prior stratum; report family-level rows.

## Bounds

- Model: pinned `Qwen3.6-35B-A3B-Q4_K_M.gguf`.
- `temperature=0`, `max_tokens=256`, `enable_thinking=false`.
- Single concurrency, zero retries.
- 120 physical model requests.
- Hard accounting cap for this run: 220,000 tokens.
- Shared request cap increases from 228 to 348; total token cap remains
  2,000,000.

## Non-Claims

This is a development mechanism experiment. It does not establish training,
production-memory benefit, broad generalization, or human-gold validity.
