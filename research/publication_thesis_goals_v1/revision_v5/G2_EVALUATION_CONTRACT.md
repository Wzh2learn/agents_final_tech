# G2 Evidence Recovery Versus Reasoning/Action Evaluation Contract

Date: 2026-10-23, Asia/Shanghai

Status: `V5_FROZEN_MEASUREMENT_CONTRACT`

## Scope

This contract evaluates responses to two distinct request types:

1. Historical fact questions: what is the user's state, and which state is current?
2. Action questions: what should the user do under the current state and stated constraints?

The evaluator must keep these responsibilities separate. A response can contain a
correct fact and an unsafe action, or an uncertain fact and a reasonable request
for clarification.

## Primary Evaluation Object

Every response receives one primary category:

| Category | Meaning | Counts as task completion? |
|---|---|---|
| `GROUNDED_TASK_COMPLETION` | The answer fulfills the request with evidence-supported facts or a safe, constraint-respecting action. Multiple actions or paraphrases are allowed. | Yes |
| `STALE_OR_UNSAFE_ADVICE` | The answer relies on an invalidated state, contradicts current evidence, invents consequential details, or recommends an action that violates a stated/current constraint. | No |
| `REASONABLE_UNKNOWN_OR_CLARIFICATION` | Evidence is insufficient or the request is genuinely ambiguous; the answer asks for clarification or safely abstains. | No, but not a failure |
| `UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE` | Evidence and constraints are sufficient for a safe answer, but the response refuses or returns a noncommittal wall. | No |
| `INTERFACE_FORMAT_FAILURE` | Invalid JSON/schema, missing required answer, empty/nonresponsive payload, or a response that cannot be consumed as the requested object. | No |

`INTERFACE_FORMAT_FAILURE` is a response-contract category, not a synonym for a
scientifically bad answer. A valid `UNKNOWN` with a null answer is not an
interface failure when the evidence is insufficient.

## Required Review Fields

Each case is recorded with this vector, even when a primary category is assigned:

```json
{
  "primary_category": "GROUNDED_TASK_COMPLETION",
  "historical_fact_status": "SUPPORTED | CONTRADICTED | UNSUPPORTED | MIXED | NOT_APPLICABLE",
  "action_constraints_respected": true,
  "action_reasoning_valid": true,
  "unsupported_detail_status": "NONE | SUGGESTED_NOT_ASSERTED | CONSEQUENTIAL_INVENTION",
  "response_contract_status": "VALID | EMPTY_OR_NONRESPONSIVE | INVALID_JSON | SCHEMA_INVALID",
  "reasonable_abstention": false,
  "unnecessary_refusal": false
}
```

The primary category is derived from this vector, not from a single `pass`
boolean. Record uncertainty explicitly; do not silently coerce an unknown field.

## Historical Fact Responsibility

- A historical claim must be supported by the selected evidence and the
  benchmark's dated state reference.
- A current-state claim is stale when it asserts the old state after the new
  observation is available.
- A correct paraphrase is accepted. Exact lexical overlap is not required.
- A fact may be marked `MIXED` when the response combines a supported statement
  with an unsupported or contradicted statement.
- Hidden `M_old`, `M_new`, and `explanation` are review references only. They
  must never be treated as actor-visible evidence.

## Action Responsibility

- Actions may have multiple valid forms. Do not require one gold plan.
- Judge the stated constraints, current-state consequences, and reasoning link
  from evidence to action.
- A cautious assumption is allowed when it is marked as an assumption and does
  not silently change a historical fact.
- An arbitrary planning parameter is not automatically unsafe when it is offered
  as a suggestion. A fabricated factual detail or a consequential unsupported
  premise is unsafe.
- `fact-correct/action-wrong` is `STALE_OR_UNSAFE_ADVICE`: correct history does
  not rescue a recommendation that violates the current state.

## Reasonable Abstention And Refusal

- `UNKNOWN` is reasonable when the selected evidence does not establish the
  requested fact or when the action request has a material unresolved ambiguity.
- Asking for one missing constraint is reasonable clarification.
- If the evidence is sufficient and a safe action exists, refusal is
  `UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE`.
- `UNKNOWN` is not automatically a success and is not automatically a failure.

## Interface And Parsing

- Invalid JSON, a missing/empty answer when an answer is required, contradictory
  required fields, and nonresponsive fixed strings are
  `INTERFACE_FORMAT_FAILURE`.
- Do not extract an answer from malformed output and do not retry silently.
- `decision=UNKNOWN` with `answer=null` is valid when the contract permits
  abstention.

## Relationship To V4

The V4 auxiliary judge and deterministic gate remain immutable evidence:

- raw judge fields are recorded unchanged;
- the V4 gate is a non-degeneracy check, not semantic gold;
- V4 false accepts, false rejects, and internal inconsistencies are reported
  separately from the V5 category;
- this review is `AI_ADVISORY_REVIEW_NOT_HUMAN_REFERENCE`, not a human-annotated
  gold standard.

## Calibration Requirement

`G2_CALIBRATION_CASES.json` must cover fixed `No`, fixed `UNKNOWN`, empty output,
cautious generic action, old fact, new fact, correct paraphrase, unsupported
detail, fact-correct/action-wrong, and unnecessary refusal. Calibration cases
are synthetic mechanism controls and are not research samples.
