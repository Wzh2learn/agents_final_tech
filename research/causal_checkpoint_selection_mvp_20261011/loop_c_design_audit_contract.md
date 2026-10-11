# Task Contract: Causality-Aware MVP Method Design Audit - Loop C

- Task ID: `causal-checkpoint-mvp-design-audit-c-20261011`
- Role: Loop C / GB10 independent scientific audit
- Window: zero-endpoint, zero new scientific dataset
- Inputs: design qualification, six-mechanism contract, A DEV_ONLY smoke code/results/tests
- Evidence class: design audit + engineering verification

## Required Checks

1. Verify the six mechanisms are genuinely distinct operators, not template/string/parameter variants.
2. Verify each mechanism has:
   - exact source state;
   - deterministic mutation operator;
   - expected causal path;
   - candidate downstream checkpoints;
   - automatic execution feasibility;
   - executor-owned downstream state.
3. Classify every dependency edge as `DESIGN_EDGE` or `EXECUTION_CONFIRMED_EDGE` using source evidence.
4. Attack direct-codebook tautology:
   - source-local responses cannot count as primary causal gain;
   - downstream causal response requires a recorded dependency path;
   - source-local-only advantage is method failure.
5. Verify RIPR fields and `NOT_IDENTIFIABLE` handling.
6. Verify corrected hard-budget greedy has no human cost weights and exact tie order.
7. Verify diagnosability uses a fixed nearest-centroid definition and tie=failure.
8. Verify MINIMUM A->B / B->A decision rule uses effect size, direction consistency and group uncertainty, not p-value alone.
9. Verify baseline inventory and terminal-only `NOT_AVAILABLE` decision.
10. Independently execute the DEV_ONLY smoke tests and inspect result schema.
11. Verify smoke uses only old 216x12 data and produces zero scientific claims/new dataset rows.
12. Decide:
   - `MECHANISM_DIVERSITY_PASS | FAIL`
   - `METHOD_DATASET_READY | BLOCKED`
   - `SANER_MVP = FEASIBLE | CONDITIONAL | NOT_FEASIBLE`.

## Output

Return a fresh report with:

- FACT / INFERENCE / UNVERIFIED sections;
- exact mechanism and edge verdicts;
- anti-tautology verdict;
- smoke test command/results;
- top three scientific objections;
- single blocker if `BLOCKED`;
- final readiness decision.

## Forbidden

- Materialize the 96-injection dataset.
- Modify design or smoke artifacts.
- Run a scientific experiment.
- Add mechanisms, metrics or baselines.
- Interpret DEV_ONLY smoke numbers as H1 evidence.

## Success Exit

The audit either certifies the design as safe to materialize or identifies one concrete blocker.
