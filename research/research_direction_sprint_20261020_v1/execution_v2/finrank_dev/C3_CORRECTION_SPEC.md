# C3 Correction Specification

Status: `FROZEN_BEFORE_RED_GREEN_FIXTURE`

## Blocker 1: Literal Percent Unit Alias

Observed deterministic defect:

```text
_unit_matches("%", "percent") == False
normalized_tokens("%") == set()
```

ESD_004 B0 V3 facts contain `8.7%` and `20.8%` with correct labels, periods,
evidence, and tool consistency. The scorer nevertheless reports missing `roe`
and `roic_adjusted`.

Required correction:

- Treat literal `%` as a valid actual unit for expected `percent`.
- Preserve B0 V3's frozen `4/7`.
- Produce a separate post-hoc V3 rescore using the corrected deterministic
  scorer.
- The rescore may change ESD_004 only if its stored facts match the reference.
- ESD_006 `UNKNOWN` must remain non-success.
- ESD_012 truncated JSON must remain a model output-format failure.

Red-green discipline:

- Run the unit fixture before the scorer change and save the failing receipt.
- Change only unit normalization.
- Run the same fixture after the change and save the passing receipt.
- Add the same assertion to the complete C3 fixture suite.

## Blocker 2: Minified Output At Fixed Token Budget

Observed B0 V3 ESD_012 behavior:

- `finish_reason=length`
- `completion_tokens=256`
- consume content is a plausible JSON prefix but has no closing braces.

No raw repair, schema change, model change, parameter change, or
`max_tokens` increase is allowed.

Required correction:

- Add an explicit model-visible instruction to return minified JSON.
- Permit whitespace only inside JSON string values.
- Forbid Markdown fences, commentary, indentation, and pretty-printing.
- Add an offline fixture proving both plan and consume messages contain the
  constraint.
- Run one complete B0 V4 over the same seven tasks in the same order.

## ESD_006 Boundary

ESD_006 B0 V3 saw sufficient evidence but returned `UNKNOWN`. This is a real
actor non-success. No reference or scorer change may convert it to success.

## Blocker 3: Explicit Derived-Value Support

The current `answer_tool_consistency` implementation searches arbitrary pairs
of numeric values in returned evidence for `+`, `-`, `*`, or `/`. This can
create false support: `10127 / 846 ~= 11.9704` appears close to the ESD_006
gross-margin answer `11.97`, even though neither ESD_006 operand is present.

Required correction:

- Ordinary facts must be supported by literal returned evidence.
- A derived fact is supported only when reference V3 names its target atom,
  operand atoms, operator and formula.
- Every named operand's reference value must occur in the actual returned
  evidence.
- The target must match the explicitly named formula.
- Arbitrary two-number arithmetic is prohibited.
- Preserve existing consistency results and produce a new post-hoc rescore.
- Add red/green fixtures for false pair-derived support and true explicit
  derivation support.

## FULL_VISIBLE Estimand Limit

`FULL_VISIBLE_CANDIDATES_AT_PLAN` measures selection and consumption from a
complete visible candidate set. It is not active evidence acquisition, because
the actor does not choose what candidate text to fetch before seeing it. It is
also not a reproduction of any prior V2 experiment. C3 labels this estimand
`COMPLETE_CANDIDATE_SELECTION_AND_CONSUMPTION`.

## C3 Accounting

- Expected prior requests: `42/192`.
- B0 V4: `14` requests, zero retries, same seven-task order.
- Expected total after B0 V4: `56/192`.
- Judge, training, production Memory, history collection, and pilot: zero.
