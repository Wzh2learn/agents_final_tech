# TQ-5 Source-Separation Developmental Panel - Spec v2 (frozen; supersedes v1 before any model output)

> Revision note: v1 (same day) defined `percentage_change` as "contains '/ and *100'". A pre-run corpus survey showed
> TAT-QA essentially never encodes percent-change as `*100` (1/3061 slash-derivations); v1 was INOPERABLE, not strict.
> v2 revises the classification to the corpus' actual encoding, WITHOUT lowering validity gates. No TQ-5 model output
> existed at either freeze. The v1 shortage event is preserved in the build history (`TQ5_NOT_RUN.md` from v1).

## Layers (frozen v2; derivation shape + answer encoding)

Normalize the derivation (strip $ ¥ £ € , % spaces) -> expr. Strip the explicit `*100` multiplier for shape tests (expr2).

- `percentage_change`: expr2 contains '/' and '-', no '+', no other '*'; AND (explicit `*100` present OR answer ≈ eval(expr) x 100 within tolerancE).
- `ratio`: expr2 contains '/', no '-', no '+', no '*'; AND answer ≈ eval(expr) (direct) OR ≈ eval(expr) x 100.
- `difference`: expr2 contains '-', no '/', no '+', no '*'; AND answer ≈ eval(expr) (direct).
- Anything else: excluded (see skip log). Averages/sums (any '+') are excluded everywhere.

Tolerance = 0.5 x 10^-d, d = decimal digits of the recorded answer (same rule as TQ-4).

## Scoring material (frozen v2)

- compare_mode = numeric. unit_kind: percentage_change -> `percent`; ratio -> `percent` if encoded x100 else `ratio`;
  difference -> `percent` if '%' in the raw derivation else `plain`.
- Other gates from v1 remain: answer_from in {table, table-text}; numeric answer; operand locatability
  (all operands except the *100 multiplier must appear in normalized table/paragraph text); one question per table;
  unique table uids; layer order difference -> ratio -> percentage_change; 4 per layer; seed 20261016; hash order;
  shortage -> NOT_RUN without substitution.
