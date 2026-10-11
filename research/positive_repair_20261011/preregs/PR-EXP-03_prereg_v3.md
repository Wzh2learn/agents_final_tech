# PR-EXP-03 Preregistration v3 (Track P recovery #1)

> MODE: minimal-experiment | experiment_role: INTERVENTION_REPAIR | date: 2026-10-11
> authority: research/positive_repair_20261011/PR-03_v3_design_decision_v1.md (frozen design, verbatim)
> prerequisite: EXECUTION_PREFLIGHT_PASS (research/positive_repair_20261011/execution_preflight/EXECUTION_PREFLIGHT_SPEC_v1.md)
> round-1 record unchanged: registered INVALID (gate provenance) / scientific NOT_EVALUABLE.

## 0. Core question (UNCHANGED)
Does a preregistered table-structure oracle recover held-out structural failures that the existing field-hit-derived oracle misses, while preserving comparable measurement cost?

## 1. Hypothesis
H1: a table-structure oracle defined from table/schema/execution semantics (never from mutation or stage labels) yields incremental held-out failure coverage and/or improved stage/family diagnosability over the field-hit-derived oracle, at comparable observation cost, without unacceptable regression on M1 held-out cases.

## 2. Measurement objects
- BEFORE: field-hit-derived oracle O_FH = the production greedy header matcher (scripts/m1_statement_parser.py, map_headers) hit-rate; response = 1 if injected hit-rate < baseline hit-rate else 0. Undefined where the header is entirely empty (baseline undefined).
- AFTER: table-structure oracle O_TS = total structural signature (column_count, ordered positional header-token sequence under the pinned canonicalizer with the empty string allowed as a token, row_count); response = 1 if the injected structure differs from the baseline structure else 0. Defined on every P1 case (PATH A).

## 3. Intervention (single design factor)
Replace the field-hit-derived oracle with the preregistered table-structure oracle on the SAME population, SAME held-out split, SAME metric definitions, SAME or bounded cost. The one changed factor is the oracle's measurement object.

## 4. Population
- P1 population: the frozen held-out structural (topology) failure carriers recorded in research/positive_repair_20261011/runs_local_mirror/PR-EXP-03/p1_generation_manifest.json.
- Controls: A0 identity arm (expected 0), A1 value-only arm (expected 0), and a structural control set carrying a genuine structural change (expected 1).
- PATH A: the two all-empty-header tables are RETAINED under the total signature (transpose of two empty headers -> identical signature -> response 0). No post-hoc exclusion.

## 5. Held-out rule
- Split assigned by the frozen rule (sorted carrier UID index modulo k) before any outcome is read; group-disjoint.
- No held-out outcome is read during prereg, implementation, or preflight.

## 6. Gate (replaces the round-1 sanity gate)
Non-degeneracy gate, evaluated on fixtures/controls BEFORE any P1 outcome:
(a) O_TS is not constant on the structural control set (fires, =1);
(b) O_TS returns 0 on A0 (identity) and A1 (value-only);
(c) O_TS is not identical to O_FH on P1 (at least one disagreement).
A constant-1 detector fails (b).

## 7. Metrics (UNCHANGED from round 1)
Primary: (1) held-out incremental coverage delta (held-out failures O_TS catches that O_FH misses); (2) stage/family diagnosability delta.
Secondary: unique catches; M1 regression (does O_TS regress on M1 held-out cases); observation/check cost.

## 8. Success / null / negative / invalid rules
- POSITIVE: gate passes AND (incremental coverage > 0 OR diagnosability improves) AND the improvement is not SOURCE_LOCAL_RESPONSE AND no unacceptable M1 regression AND cost comparable.
- NULL: gate passes but no held-out diagnostic gain (O_TS is merely different); or a source-local-only gain.
- NEGATIVE: gate passes and O_TS performs worse than O_FH on the primary metrics.
- INVALID: measurement or provenance integrity failure (schema/hash/gate), recorded with provenance.
- NOT_EVALUABLE: population or oracle undefined (should not occur under PATH A). NOT_EVALUABLE is never merged into NULL.

## 9. Tautology and leakage controls
- The oracle is frozen before any P1/M2 result is read; it never reads the mutation label, the stage label, or any held-out outcome.
- The (c) disagreement clause measures the design-intended difference between the two oracles, not a structural-null tautology.

## 10. Cost
Observation cost = number of leaves/checks consumed per case; must be comparable to O_FH (bounded). Report both.

## 11. Stop condition (owner-set)
If v3 stops at schema / gate / provenance / undefined-domain WITHOUT entering effect measurement, then PR-03 = NOT_EVALUABLE_FINAL and the branch STOPS; there is no fourth engineering repair.

## 12. Sequence
This prereg -> Loop A implementation + EXECUTION_PREFLIGHT_PASS -> Loop C fresh-context pre-result audit -> formal run -> Loop C post-result recompute.

## 13. Prereg hash
The prereg hash is recorded as `PREREG_SHA256` in the v3 implementation contract (research/positive_repair_20261011/runs/PR-EXP-03-v3/implementation_contract.md); its value is the sha256 of this frozen file.