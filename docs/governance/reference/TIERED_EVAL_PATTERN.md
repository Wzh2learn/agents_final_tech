# Tiered Eval Pattern

> Status: active governance reference | Adapted for JinRongAgents from `skills-loop-engineering`.
> This pattern dispatches existing checks; it does not create a new evaluation engine.

## Purpose

Verification depth must match the change. Every report must disclose the tier actually run so a
structural check cannot be mistaken for full behavioral replay.

## Tiers

| Tier | Name | Checks | Appropriate change |
|---|---|---|---|
| 0 | Structural | files, syntax, schema, links, hashes | documentation or index-only |
| 1 | Component | focused tests for touched components | bounded code or test change |
| 2 | Logic | state, gate, protocol, and output invariants | control-flow or contract change |
| 3 | Full replay | golden replay plus state-machine replay | release or cross-cutting change |

Tiers are cumulative. Tier 2 includes Tier 0 and Tier 1. Passing a cheaper tier is never reported
as Tier 3.

## Changed-Path Selector

Classify each changed path and run the highest required tier:

- docs/index only -> Tier 0;
- one component's code/tests -> Tier 1;
- state machine, gate, split, threshold, or protocol -> Tier 2;
- release, frozen expectation, or cross-cutting behavior -> Tier 3.

An unclassified path is a loud failure. Do not silently assign Tier 0 to the least familiar change.

## Golden Replay Boundary

Tier 3 inputs must be recorded real runs or frozen project artifacts, not newly invented examples.
If rules legitimately changed, update the expected result in the same controlled change and record
why. Do not modify frozen criteria merely to make replay green.

## Reporting Contract

Every verification claim includes:

- tier and scope;
- commands and exit codes;
- covered and excluded paths;
- whether the run was authoritative or `DEV_ONLY / NON_AUTHORITATIVE`;
- failures and nulls retained without reinterpretation.

Example: `Tier 1 component checks PASS; Tier 3 replay NOT RUN` is complete and honest.

## Related

## PASS Vocabulary

Gate labels must include the exact level:

- `UNIT_PASS` — isolated tests only.
- `COMPONENT_PASS` — one module/adapter and its focused boundary tests.
- `CONTRACT_PASS` — schema, semantic, provenance and hash-domain invariants.
- `INTEGRATION_PASS` — the composed runner -> adapter -> scorer-input seam.
- `END_TO_END_PREFLIGHT_PASS` — complete execution chain simulated, stopping before scientific output.
- `FORMAL_RUN_PASS` — formal results plus independent recomputation.

A lower level never implies a higher level. Reports must state covered and excluded paths.

- [`../../../skills/eval-harness/`](../../../skills/eval-harness/) - evaluation and replay mechanics
- [`FOUR_CONCEPT_SEPARATION_PATTERN.md`](FOUR_CONCEPT_SEPARATION_PATTERN.md) - execution, evidence, judgment, and approval
- [`PROVENANCE_MAP_PATTERN.md`](PROVENANCE_MAP_PATTERN.md) - result-to-artifact traceability
- [`NEGATIVE_CLAIM_BURDEN_PATTERN.md`](NEGATIVE_CLAIM_BURDEN_PATTERN.md) - required evidence for negative claims
