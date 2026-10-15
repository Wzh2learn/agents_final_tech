# Paper E Layer-1 v4 Closeout

> Status: `HELDOUT_RESULT_DELIVERED` | Date: 2026-10-15
> Contract: `LAYER1_V4_COMPACT_CONTRACT_v3.json` (`322c3b38...`)
> Result: `V4_RESULTS_v1.json` (`b412c3cb...`)

## Result (held-out 59)

- `GOLD_ESTABLISHED_ON_HELDOUT`
- Label counts: E=29, H=18, U=12
- `u_rate_heldout = 0.2033898305084746` (gate <= 0.30)
- Visible contingency: E=19, H=17, U=12
- Blind contingency: E=10, H=1, U=0
- `co_miss_rate = 0.09090909090909091` (1/11 blind harmful)
- `co_alarm_rate = 0.3958333333333333` (19/48 visible legal variation)
- Zero model / judge / network / training calls

Boundary: descriptive held-out feasibility result only. Not a population rate, OCR result, or
harmful-blind-spot claim.

## Audits

- Pre-result narrow audit: CONDITIONAL, non-blocking residuals R1-R6; explicit statement that
  the held-out run is safe to execute.
- Post-result audit: 59/59 labels, reasons, bindings and nearest distances independently
  re-derived; all counts and rates reproved; checker read strictly after labels freeze.
  Verdict CONDITIONAL only on documentation item N1, closed by `V4_CONTRACT_ERRATA_v1.md`.
- Frozen label file sha256: `c17e31af7b808161cc36102672317ed65de4d8424b31b0852ae5a7fe079d86cf`.

## Interpretation

The independent gold is constructible on this held-out split under the frozen column-local
contract. The result also shows two different error surfaces: most checker-invisible cases are
legal variations (10/11), while visible cases include a large share of legal variations
(19/48 co-alarm). This is feasibility evidence for the upgraded Paper E direction; it does not
by itself replace the frozen manuscript claims or authorize Layer 2.
