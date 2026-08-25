# Goal Card Template — Research Direction Planning

> A goal card defines a research direction from hypothesis to execution plan.
> It's the bridge between "we should try X" and "here's exactly what to run."

## When to use
- Starting a new research direction (not a single experiment, but a direction)
- Translating a paper insight into an implementation plan
- Committing to a multi-experiment exploration arc

## Template

```markdown
# Goal Card: [Direction Name] (date established)

> **Status**: 📋 Planning / 🔄 Active / ✅ Concluded / 📦 Archived
> **Priority**: P0 (blocking) / P1 (next up) / P2 (backlog)
> **Estimated scope**: [N experiments, ~X GPU-hours]

## 一、Why Now (Motivation — 3 evidence convergence)

1. [Evidence 1]: What observation/data/paper points to this direction?
2. [Evidence 2]: What gap in current system does this address?
3. [Evidence 3]: What makes this tractable with current infrastructure?

## 二、Constraints (Design boundaries — nail down first)

| Constraint | Implication |
|-----------|------------|
| [Hard constraint 1] | [What this means for the design] |
| [Hard constraint 2] | [What this rules out] |
| [Infrastructure limit] | [Maximum scope possible] |

## 三、Mechanism Mapping (What to try → How it maps to the system)

| Module/Change | Source (paper/insight) | Implementation sketch | Which gap it solves |
|--------------|----------------------|---------------------|-------------------|
| [Change 1] | [Paper X, Section Y] | [~N lines, where in code] | [Gap description] |
| [Change 2] | ... | ... | ... |

**Migration principle**: One module at a time (single variable discipline).

## 四、Pre-registered Judgment (BEFORE any experiment runs)

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Success | [metric > X] | [How measured, which eval] |
| Quality floor | [metric > Y] | [Minimum acceptable] |
| Direction killed | [metric < Z OR condition] | [When to stop] |

## 五、Experiment Queue (Ordered by dependency)

| Phase | Experiment | Depends on | Pre-registered prediction |
|-------|-----------|-----------|--------------------------|
| M1 | [First experiment] | — | [Expected outcome if hypothesis correct] |
| M2 | [Second experiment] | M1 succeeds | [Expected if M1 worked] |
| M3 | [Third experiment] | M2 | ... |

## 六、Reading Linkage (Papers that inform this direction)

| Paper | Relevant mechanism | Priority |
|-------|-------------------|----------|
| [Paper 1] | [What to borrow] | Must-read |
| [Paper 2] | [Counter-evidence] | Check |

## 七、Exit Conditions

- **Success exit**: [What "done" looks like — metric + deployed + paper-ready]
- **Failure exit**: [After N experiments all below floor → direction closed]
- **Pivot conditions**: [If X happens, redirect to Y instead]

## 八、Review & Conclusion (filled after direction concludes)

- **Outcome**: [Succeeded / Failed / Partially succeeded]
- **Key insight**: [What we learned that wasn't in the hypothesis]
- **Supersedes**: [What old beliefs this overturns]
- **Feeds into**: [What new direction this enables]
```

## Rules for Goal Cards

1. **Constraints first** — nail these before any mechanism design
2. **Pre-register before running** — judgment criteria defined, written to disk, THEN experiments start
3. **One variable per experiment** — don't test M1+M2 together
4. **Prediction required** — "if hypothesis is correct, we expect X" BEFORE seeing results
5. **Exit conditions explicit** — prevent zombie directions that never get killed
6. **Review mandatory** — even failed directions get a conclusion section
