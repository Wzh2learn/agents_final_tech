# Learning Methods

Use one method at a time. Preserve the boundary between intuitive explanation and mechanism-level explanation.

## 1. Dual Explanation

Run this method when a concept is not understood.

1. State the target concept and the user's current background.
2. Produce a beginner layer:
   - use ordinary language;
   - use one concrete example;
   - explain what problem the concept solves;
   - avoid pretending the analogy is the mechanism.
3. Produce an expert layer:
   - use accurate terminology;
   - explain the core mechanism;
   - state applicable boundaries;
   - identify common misconceptions.
4. Produce the requested synthesis:
   - map beginner phrases to professional terms;
   - list the most likely misunderstandings;
   - provide three questions that test actual understanding.

Output template:

```markdown
# Dual Explanation: <concept>

## Beginner Layer
<ordinary-language explanation and concrete example>

## Expert Layer
<mechanism, terminology, boundaries, and common misconceptions>

## Term Mapping
| Beginner phrase | Professional term | Why the mapping matters |

## Likely Misunderstandings
1. ...

## Understanding Checks
1. ...
2. ...
3. ...
```

## 2. Reverse Decomposition

Run this method for a strong product, page, workflow, dashboard, document, or process.

1. State the problem the artifact solves in one sentence.
2. Identify the audience and their success condition.
3. Reconstruct the structure or process from the artifact.
4. Identify choices that create the quality difference.
5. Define the artifact's completion standard.
6. Separate transferable principles from case-specific details.
7. Produce three to five reusable principles, an execution checklist, and one small practice.

Output template:

```markdown
# Reverse Decomposition: <artifact>

## Problem and Audience
## Structure or Process
## High-Leverage Choices
## Completion Standard
## Transferable Principles
## Execution Checklist
## First Small Practice
```

Do not infer hidden implementation details that the artifact does not reveal.

## 3. Horizontal and Vertical Domain Research

Run this method for a product, company, technology, industry, person, or event.

1. Establish the research cutoff date and object boundary.
2. Perform the vertical analysis:
   - origin context and demand;
   - key contributors;
   - major transitions, successes, and failures;
   - early choices that became capability, path dependence, or burden.
3. Perform the horizontal analysis:
   - select comparison objects and explain the selection;
   - compare strength, weakness, and uniqueness on shared dimensions;
   - explain adoption and abandonment from the user or market perspective.
4. Combine both axes:
   - explain how history constrains the future;
   - state the three most plausible future paths;
   - list prerequisites and warning signals for each path.
5. Apply the evidence rules:
   - prefer primary sources;
   - place source and date near important facts;
   - separate fact, inference, and opinion;
   - present conflicting evidence side by side;
   - mark missing evidence `UNVERIFIED`.

Output order:

```markdown
# Domain Research: <object>
## Core Conclusions
## Key Timeline
## Horizontal Comparison
## Detailed Analysis
## Future Paths
## Open Questions
```

Use report depth proportional to the request. Do not pad with unrelated source summaries.

## 4. Fact Check

Run this method for a factual claim, number, conclusion, proposal, or quoted statement.

1. Decompose the input into:
   - externally verifiable facts;
   - conclusions derived from facts;
   - value judgments.
2. Verify facts against source, sample, date, and full context.
3. Label each fact:
   - `CONFIRMED`;
   - `NEEDS_NARROWING`;
   - `CONTESTED`;
   - `INSUFFICIENT_EVIDENCE`;
   - `WRONG`.
4. Assuming supported facts are true, check:
   - whether they imply the conclusion;
   - hidden assumptions;
   - correlation-causation confusion;
   - missing explanations or evidence;
   - conditions under which the conclusion holds or fails.
5. Produce:
   - trusted and corrected facts;
   - the key reasoning gaps;
   - the strongest revised conclusion;
   - the confidence level that the evidence supports.

Do not turn a value judgment into a fact-check failure. Report it as a value judgment and evaluate its stated priorities separately.
