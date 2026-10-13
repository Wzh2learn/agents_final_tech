# Decision Methods

Use these methods after options exist but before a choice is recorded or executed.

## 1. Two-Way Steelman Decision

Run this method when two options both have credible support.

1. Restate the actual decision with the goal, options, and constraints.
2. Build the strongest case for each option:
   - strongest reasons;
   - applicability conditions;
   - largest benefit;
   - largest risk;
   - hardest objection.
3. Compare the cases:
   - identify real disagreements;
   - identify the variables most likely to change the result;
   - list missing information.
4. Ask one question whose answer is most likely to change the decision.
5. After the answer, provide:
   - a clear recommendation;
   - reasons;
   - applicability conditions;
   - next action.

Do not recommend both options as equally good unless the evidence truly supports that conclusion.

Output template:

```markdown
# Steelman Decision: <decision>
## Accurate Restatement
## Strongest Case A
## Strongest Case B
## Real Disagreements
## Decision Variables
## One Question
---
## Recommendation After Answer
## Conditions
## Next Action
```

## 2. Minimal Experiment

Run this method when further discussion is unlikely to resolve an assumption.

1. List the three assumptions most likely to change the decision.
2. Select the one with the highest decision impact.
3. Design one low-cost, reversible experiment that can finish within the approved cycle.
4. Specify:
   - concrete action;
   - time and resource budget;
   - observed metrics;
   - continue condition;
   - stop condition;
   - information gained after completion;
   - first action for the next day.
5. Check the execution boundary:
   - protect frozen criteria and data splits;
   - avoid production writes and external release;
   - use one heavy task where applicable;
   - preserve logs, hashes, commands, and exit codes.
6. Hand execution to `sprint-contract`, `eval-harness`, and `verify-before-done` after authorization.

Output template:

```markdown
# Minimal Experiment: <decision>
## Candidate Assumptions
## Selected Assumption
## Experiment
| Action | Budget | Metric | Continue | Stop |
## Expected Information
## Execution Boundary
## First Action Tomorrow
```

Do not call a mock, dry run, or synthetic fixture a scientific result. Label it `DEV_ONLY` or `NOT_AUTHORITATIVE` when applicable.

## 3. Portfolio Triage (Exhaustive -> Bottom-Up -> Compounding Gate)

Use when many candidate directions, experiments, or subtasks compete for one scarce budget, and the goal is to pick the path whose many small results can compound into a qualitative step (quantity into quality) - not to pick a single big bet.

1. **Exhaustive menu (scope-bounded).** List all candidates from already-recorded scope; do not open a new search frontier. Tag each with its current status (active / conditional / frozen) and its owner.
2. **Bottom-up screen (four questions per candidate).** (a) independent target and licence? (b) what is the next cheap action? (c) how much does the nearest neighbour already cover? (d) can it stop cleanly on failure?
3. **Compounding ranking.** Prefer candidates that (a) decompose into multiple independent small experiments, (b) whose small results can share one mechanism or effect, (c) with pre-declared stop rules. Deprioritize single-shot big bets and anything requiring irreversible commitment before evidence.
4. **Single decision gate per stage.** One owner decision unlocks the next stage; record why, alternatives, and risk. Never batch-approve further stages; re-run the screen only when a stage produces new evidence.

Output template:

```markdown
# Portfolio Triage: <decision>
## Menu (status, owner)
## Bottom-Up Screen (four questions per candidate)
## Compounding Ranking
## Stage Plan (one decision gate per stage)
## Stop Rules
```

Boundary: this method selects work order; it does not authorize execution, change claims, or reopen frozen branches. Pair it with `decision-record` after each gate.
