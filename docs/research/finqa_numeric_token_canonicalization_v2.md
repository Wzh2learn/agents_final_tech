# FinQA Numeric-Token Canonicalization v2

> Status: `ENGINEERING_RECONCILIATION_NOT_EXPERIMENTAL` | Evidence class: `ENGINEERING` | No formal FinQA experiment or frozen-artifact rewrite

## Reconciliation

Namespace: `FINQA_NUMERIC_TOKEN_CANONICALIZATION_V2`.

- Candidate selection reaches token identity through `resolve_numeric_argument()`.
- The causal-join audit now imports the same `numeric_tokens()` and `try_canonical_numeric_token()` adapter.
- Numeric literals are canonicalized as exact fixed-point `Decimal` strings; `float(...):.10f` is no longer part of token identity.
- Ambiguous evidence still fails closed with `unresolved_ambiguous_evidence`; no-match evidence still fails closed with `unresolved_no_evidence`.

The old audit and candidate-manifest JSON remain frozen and unmodified. This namespace changes only future shared logic and focused verification; it does not reinterpret their recorded counts or authorize execution.
