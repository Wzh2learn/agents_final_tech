# Triple Audit Pattern

> Status: active governance reference | Adapted for JinRongAgents from `skills-loop-engineering`.
> This pattern reduces anchoring for critical decisions; it does not certify factual correctness.

## Purpose

A reviewer who reads a draft first tends to improve that draft's framing instead of challenging
it. For decisions that are expensive to reverse, produce independent alternatives before any
comparison.

## Method

1. Reviewer A produces Draft A without reading other drafts.
2. Reviewer B produces Draft B without reading Draft A.
3. A comparison author who did not produce either draft builds a divergence table.
4. The human resolves each divergence or leaves it explicitly open.
5. The final artifact credits both sources and links the preserved drafts and resolution record.

Required artifacts:

- `Draft A` with baseline, scope, and evidence receipt;
- `Draft B` with baseline, scope, and evidence receipt;
- `Comparison and resolution` with the human decision per divergence.

## Divergence Table

| Node | Draft A | Draft B | Type | Resolution |
|---|---|---|---|---|
| Topic | Position and evidence | Position and evidence | structural / detail / framing / open | Decision, owner, trigger |

`Structural` divergences are the highest-value signal. Do not force convergence; an unresolved
point remains `OPEN` with a revisit trigger.

## Isolation Requirements

- Different sessions or agent identities.
- No shared generation context or reviewer output.
- Same baseline, question, and deadline where feasible.
- Input visibility recorded before output is accepted.
- Ground-truth material remains isolated as described in
  [`GROUND_TRUTH_ISOLATION_PATTERN.md`](GROUND_TRUTH_ISOLATION_PATTERN.md).

## Cross-Model Verification

Cross-context and cross-model independence remove different risks. Cross-model review can reduce
shared factual blind spots but does not remove framing lock-in or agreement bias. A verifier with
no retrieval or source access can report `NOT_CHECKED`, not `VERIFIED`.

Before sending unpublished material to another provider, record provider, model, and content class,
then obtain explicit consent. A configured credential is not consent.

## When Not To Use

Routine edits, implementation within an approved design, and cheap-to-reverse changes do not need
triple production. Use ordinary review plus mechanical tests instead.

## Related

- [`EXPERT_REVIEW_REQUEST_PATTERN.md`](EXPERT_REVIEW_REQUEST_PATTERN.md) - review request and report contract
- [`FOUR_CONCEPT_SEPARATION_PATTERN.md`](FOUR_CONCEPT_SEPARATION_PATTERN.md) - independent production is not adjudication
- [`../../../skills/self-eval-bias/`](../../../skills/self-eval-bias/) - self-review bias control
