# RESEARCH_DECISION

> Decision: `STOP_CURRENT_PANEL / CEILING_ON_THIS_PANEL`

## Question

Does the restricted table-calculation task leave useful headroom for real-experience reuse over no experience, generic rules, or general domain/tool context?

## Frozen diagnostic

- 16 future tasks across 8 source clusters.
- B0 runs first with no extra context.
- R/C/H contents, H selection, task order and branch gates were frozen before B0.
- Model, thinking switch, `max_tokens=256`, output contract and tool protocol remained unchanged.
- New diagnostic bundle: `b0a846659d1e05e8680833e72674e0058f89765ad1b3724f5c9cab95a18625d0`.

## B0 result

- Task success: **16/16**.
- Source clusters with success: **8/8**.
- Reference match: **16/16**.
- Tool execution success: **16/16**.
- Answer/tool consistency: **16/16**.
- Non-success tasks: **0**.
- Requests: **32**; tokens: **13,144**.

Every source cluster contributed two successful tasks. The pre-frozen gate therefore returns `CEILING_ON_THIS_PANEL`.

## What does real history add?

**Unobserved.** R/C/H were not run because the B0 ceiling gate prohibited spending the other 96 requests. The absence of stage-three results must not be interpreted as H having zero effect.

What the evidence does show is that this panel offers no measurable improvement headroom under the current model and task contract. Any history effect would be bounded by a 16/16 baseline.

## Decision

Stop further investment in the current panel.

- Do not run R/C/H on these same 16 tasks.
- Do not claim experience reuse is ineffective in general.
- Do not change tasks, prompts, model or selection after observing B0.
- Preserve the 96-request stage-three budget as unused; it is not permission for another experiment.

The evidence supports a bounded conclusion:

> **The current restricted panel is at ceiling for the fixed model/runtime, so it cannot identify whether real experience improves performance. A future reuse study requires a different, independently justified task panel with genuine headroom.**
