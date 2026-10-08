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
