# GB10 Loop A Condition-Change Fix Task

Task ID: `gb10-condition-change-feedback-20261020-fix-a`

Read `condition_change_feedback_v1/SPRINT_CONTRACT.md` and the GB10 Loop C
review findings embedded below. Make one bounded revision in the same package.
Do not send model requests or edit FinRank/Paper E artifacts.

## Required Fixes

1. Extend actor input with the applicable policy text or explicit policy delta
   for `policy_version_id`. Keep derived decisions, minimal sufficient sets,
   reference facts, and adjudication fields out of actor input. The actor must
   be able to observe the condition change without seeing gold.
2. Recut the out-of-scope feedback fixture as a single-factor test: submit the
   correct derived outcome and a selection that satisfies a minimal set but
   includes exactly one out-of-scope fact. Add the counterfactual without that
   fact as a frozen fixture. Composite must retain the clean selection and
   revise only the extra-fact selection because of scope precision.
3. Append one paired case, preserving all existing cases, where the decision is
   invariant across the policy delta but the minimal sufficient set changes.
   Derive both references from the same policy engine.
4. Separate reason codes so answer mismatch, insufficient plan, scope
   impurity, and in-scope over-selection are reported independently.
5. Make `plan_precision_mean` reproducible across Python 3.11 and 3.12 using
   deterministic rational or fixed-decimal aggregation.
6. Use stable package provenance:
   `task_id=condition_change_feedback_v1`; record launcher IDs only in run
   manifests.

## Output Rules

- Preserve all V1 frozen inputs/results.
- Write revised actor/reference/probe artifacts as V2 files and update the
  machine receipt to hash both versions.
- Run the full five-command sequence and focused tests.
- Update `RETURN.md`, `CONDITION_CHANGE_LOOP_A_RETURN.md`, and
  `CONDITION_CHANGE_LOOP_A_VERIFICATION.json` without overwriting
  `GB10_LOOP_A_*`.
- Report exact changes, hashes, tests, zero-request accounting, and remaining
  blockers.
