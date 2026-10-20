# C2 Root-Cause Comparison

Status: `FROZEN_BEFORE_B0_V3`

## 1. Plan-Time Visibility Confound

B0 V2 request evidence:

- The plan request contains a `candidate_catalog`.
- Catalog fields are only `candidate_id`, `page_number`, and
  `visible_source_scope`.
- Candidate text length in the plan request is zero.
- The prompt explicitly says candidate text is hidden until `evidence_lookup`.

Strong-rule input evidence:

- `strong_rule_plan` reads all six ESD_001 candidate text fields.
- Across the first task the deterministic rule can inspect 32,856 candidate
  text characters before choosing IDs.
- It therefore uses body periods, table headers, metric rows, and lexical
  overlap that B0 cannot see at plan time.

The observed B0 V2 plan sufficient-set rate `3/7` and strong-rule rate `7/7`
are therefore not a same-information comparison.

## 2. Frozen C2 Visibility Decision

Selected policy: `FULL_VISIBLE_CANDIDATES_AT_PLAN`.

Both B0 and the deterministic strong rule will see the same complete candidate
records before planning:

- `candidate_id`
- `text`
- `page_number`
- `visible_source_scope`

`evidence_lookup` remains in the execution chain and returns the requested
candidate records in request order. Consume may cite only IDs actually
returned by that call.

This policy is frozen before B0 V3 and will not be adjusted after observing B0
V3 outputs.

Rejected alternatives:

- `METADATA_ONLY_FOR_BOTH`: would remove the body-period, header, and metric
  signals that the owner explicitly requires from the strong rule.
- `DERIVED_PREVIEW_SUMMARY`: would introduce a new generated/derived feature
  and make the comparison depend on summary quality.
- `HIDE_TEXT_FROM_STRONG_RULE`: would weaken the named strong-rule baseline
  instead of fixing unequal access.

## 3. ESD_006 Reference Scope

Question asked:

- Gross profit for the stated Automotive reporting-line calculation.
- Corresponding gross margin percentage.

Reference V1 requires four answer atoms:

- Automotive revenue
- Automotive and other cost of sales
- Derived gross profit
- Derived gross margin percentage

This over-constrains the requested answer. B0 V2 returned both requested
derived values but was marked missing the two calculation operands.

Frozen C2 reference V2 rule:

- Required answer atoms: `derived_gross_profit` and
  `derived_gross_margin`.
- Verification operand facts: `automotive_revenue` and
  `automotive_and_other_cost_of_sales`.
- Operand facts remain auditable evidence for the disclosed-line derivation
  and interpretation limit; they are not additional required answer fields.
- No other task reference changes.

This rule is based on the task wording and
`ADJUDICATION_AND_NEXT_GOAL.md` ESD_006 ruling, and is frozen before B0 V3.
