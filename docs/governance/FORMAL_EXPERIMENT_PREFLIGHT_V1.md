# Formal Experiment Preflight v1

> Status: active governance checklist | Updated: 2026-10-10 | Scope: formal research runs
> Purpose: simulate the execution chain and stop before scientific output. Formal runs must not discover interface defects.

## PASS Levels

A gate must name its level. A lower level never implies a higher one.

| Level | Meaning | Required evidence |
|---|---|---|
| `UNIT_PASS` | isolated function/test | focused tests with fail cases |
| `COMPONENT_PASS` | one module or adapter | component tests plus boundary inputs |
| `CONTRACT_PASS` | schema/semantic invariants | exact fields, hashes, provenance and fail-closed checks |
| `INTEGRATION_PASS` | runner -> adapter -> scorer-input seam | real call shape, required metadata and trace validation |
| `END_TO_END_PREFLIGHT_PASS` | complete execution chain simulated | all prior levels, exact population, zero scientific outputs |
| `FORMAL_RUN_PASS` | formal scientific execution | scorer/estimands/bootstrap plus independent recomputation |

`SCORER_GO`, `SPLIT_GO`, `PREREG_GO` and similar names must include the level and scope in their evidence record. `PASS` alone is ambiguous and is not a valid final label.

## Preflight Checklist

Run this before any formal scorer call:

1. **Authority version** — each authority path from `GRAPH_LOOP_AUTHORITY_MAP_V1.md` exists and matches its recorded SHA-256.
2. **Hash domain** — raw provenance and normalized runtime hashes are distinct, named and bound to the same source artifact.
3. **Runtime interface** — required metadata fields are explicit; missing/null/empty values raise; no silent defaults.
4. **Sample/group identity** — exact IDs, sample count, cluster count and connected components match the frozen manifest.
5. **Split determinism** — role assignment replays from the frozen seed/rule; no cross-role group or duplicate source identity.
6. **Scorer binding** — scorer source, measurement object and paired artifacts are hash-bound; no shared fault adapter or Stage E aggregation.
7. **Analysis plan** — estimands, V/D/O definitions, exclusions, seed, replicate count and CI method are frozen before output.
8. **Seeds and uncertainty** — bootstrap/permutation settings are explicit; `NOT_USED` is stated where applicable.
9. **Integration dry-run** — runner -> binding adapter -> scorer input construction -> hash/trace validation passes on the complete target population and stops before `score_pair`.
10. **Zero-output qualification** — no V/D/O, estimand, bootstrap or formal result file exists before the preflight receipt.
11. **Previous-run immutability** — all prior invalid-run hashes still match; no old result is overwritten or hidden.
12. **Handoff closure** — D -> A -> C contracts contain authority paths, hashes, allowed/forbidden actions, outputs and stop conditions.

## Required Receipt

A preflight receipt records:

- `verification_level = END_TO_END_PREFLIGHT_PASS` only when all checks pass;
- exact counts and hash mismatches;
- required metadata values;
- integration trace counts;
- zero-output scan;
- prior-run hash status;
- commands, environment and test output hashes.

Any failed check stops the run before scientific output. Do not repair the contract in the same formal namespace.

## Hook Timing

| Existing capability | Earliest useful stage | Required move |
|---|---|---|
| `summary-recompute-guard` | FREEZE / REPORT | verify before result summary is accepted |
| `index-guard` | DOCUMENT CREATE / DISPATCH | reject unregistered live authority |
| `skill_router.py` | DISPATCH | route before execution, not after |
| `dispatch_precheck.sh` | DISPATCH | keep as watcher subcheck; not a scientific preflight |
| `verify-before-done` | POST-RUN and COMPLETION | adversarial review plus fresh command output |
| `audit-cycle` | POST-RUN / GOVERNANCE CLOSEOUT | baseline, first-hand evidence and anomaly filing |
| `self-eval-bias` | REVIEW | force fresh-context reviewer for A/C claims |

## Boundary

This checklist validates readiness and execution-chain integrity. It does not authorize a scientific result, alter frozen design, or replace independent Loop C recomputation.
