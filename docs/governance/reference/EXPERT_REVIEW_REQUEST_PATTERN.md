# Expert Review Request Pattern

> Status: active governance reference | Adapted for JinRongAgents from `skills-loop-engineering`.
> This pattern defines review artifacts; it does not grant review, experiment, model, or release authority.

## Purpose

An external review is useful only when its findings are checkable and its recommendations are
sequenced. The request and the resulting report must expose their evidence boundary before any
finding is read.

## Required Header

| Field | Required content |
|---|---|
| Nature | Independent advisory review. Diagnosis and recommendations only; no adjudication or asset modification unless separately authorized. |
| Baseline | Exact commit SHA and reviewed paths. `current main` is not a baseline. |
| Evidence | Files read in full, mechanical checks rerun, and checks deliberately not run. |
| Citation | State whether `path:line` refers to the baseline or to fresh read-only verification. |
| Independence | Reviewer identity/session, conflicts, and whether the reviewer saw another reviewer's output. |
| Boundary | Explicitly list data, model, service, publication, and frozen-criterion exclusions. |

Freshly recomputed numbers must be labelled `this re-verification`. They must not be presented as
existing project conclusions unless a project artifact supports the same value and scope.

## Required Structure

1. **Conclusion first:** one paragraph that answers the requested question.
2. **One sequenced recommendation:** name the first action and why later actions depend on it.
3. **Pause list:** work that should stop while the recommendation is evaluated.
4. **Findings:** each with baseline `path:line`, evidence, impact, and a proposed disposition.
5. **Open decisions:** items the human must adjudicate; do not silently choose research direction.

A review that recommends five parallel workstreams has enumerated options, not prioritized work.

## Request Contract

Give the reviewer:

- the pinned baseline and exact question;
- authoritative artifacts and their hashes where available;
- allowed read-only commands and explicit prohibitions;
- permission to reject the framing;
- no preferred answer or leading expected conclusion.

## Anti-Anchoring

Do not show another reviewer's output before independent production is complete. If prior output
was seen, disclose it and downgrade the result to `INFORMED_REVIEW`, not `INDEPENDENT_REVIEW`.

## Completion Semantics

Use [`FOUR_CONCEPT_SEPARATION_PATTERN.md`](FOUR_CONCEPT_SEPARATION_PATTERN.md): review completion,
review judgment, human decision, and project absorption are separate facts. A review is not a
research result, approval, or completion state.

## Related

- [`ACTION_FORMAT_SPEC.md`](ACTION_FORMAT_SPEC.md) - structured research-to-writing actions
- [`TRIPLE_AUDIT_PATTERN.md`](TRIPLE_AUDIT_PATTERN.md) - independent production for critical decisions
- [`PROVENANCE_MAP_PATTERN.md`](PROVENANCE_MAP_PATTERN.md) - claim-to-source traceability
- [`../../../skills/audit-cycle/`](../../../skills/audit-cycle/) - first-hand verification discipline
