# Graph Loop Meta-Retrospective: FinQA Runtime Failures

> Status: governance audit | Date: 2026-10-10 | Scope: analysis-plan freeze, raw/normalized binding and runner->adapter metadata failures
> Baseline: `docs/governance/audit/harness_audit_20260905/AUDIT_REPORT.md` plus the two preserved FinQA invalid runs
> Nature: root-cause and governance audit; no scientific result is created here.

## Executive Judgment

The failures were not caused by the FinQA scientific design, population, split, join or scorer semantics. They were allowed by a governance and verification architecture that accepted local PASS labels without proving the end-to-end execution seam. The system repeatedly crossed the boundary between `COMPONENT_PASS` and `FORMAL_RUN_PASS` without an `END_TO_END_PREFLIGHT_PASS`.

## Root-Cause Tree

| Branch | Finding | Failure family | Evidence | Why the gate missed it |
|---|---|---|---|---|
| `SCIENTIFIC_DESIGN` | RQ, V/D/O and analysis estimands were valid and frozen before the first valid analysis attempt | not a cause | `FINQA_V2_ANALYSIS_PLAN.md`, C freeze audit | No scientific gate was wrong; execution never reached measurement |
| `DATA` | 89/30 population, IDs, source hashes and split membership stayed stable | not a cause | both invalid-run receipts, C recomputation | Data checks were scoped to manifests, not runtime call shape |
| `CONTRACT` | raw payload hash and normalized scorer hash shared one field name and different serialization domains | primary | `RAW_NORMALIZED_HASH_DOMAIN_MISMATCH` | Contract tests checked values in isolation, not the authoritative hash domain at the seam |
| `CONTRACT` | trace schema mixed immutable identity with runtime metadata | primary | `RUNTIME_METADATA_NOT_FORWARDED_TO_BINDING_SEAM` | No schema-level rule said which fields belong to identity versus join metadata |
| `INTERFACE` | runner omitted `split_role`, `stage`, `cluster_id`, `report_cluster`; adapter silently defaulted them to empty | primary | C independent 420/420 counterfactual | No runner->adapter integration test used the real call shape |
| `TEST_COVERAGE` | 19 unit/freeze tests passed while the real seam failed | primary | 19 passed vs 89/89 pre-scorer failures | Tests covered scorer/adapter components, not the composed chain |
| `DOCUMENTATION` | task card referenced a frozen analysis plan before the plan was materialized | contributing | old preflight and analysis-freeze timeline | Task-card checklist did not bind the plan path/hash as a mandatory input |
| `DOCUMENTATION` | C audit reports lived in `loop_runs/c.log` and were not repo-authoritative | contributing | A preflight `BLOCKED_LOOP_C_AUDIT_REPORT_MISSING` | Handoff rules allowed a live conclusion outside the indexed evidence surface |
| `STATE_MEMORY` | D knew the C verdict from the running-session log while A searched repository state | contributing | A stop receipt versus C log | `STATE`/`THREADS` did not carry the exact authority path and hash for the C report |
| `ROLE_HANDOFF` | contracts included actions and outputs but not a complete authority/hash chain | primary | repeated A/C/D dispatches | Handoff templates had no mandatory authority map or pass-level field |
| `GOVERNANCE` | `PASS` was used for unit, component, binding and formal-run scopes | primary | old gate labels and task cards | `TIERED_EVAL_PATTERN` existed but was not enforced as the vocabulary for every gate |

### A. Discoverable before formal run

All four failures were discoverable with a dry-run of the complete runner->adapter->scorer-input chain. The analysis-plan omission was discoverable at preflight; hash-domain and metadata defects were discoverable with 89-pair binding qualification and missing-field controls.

### B. Why existing gates missed them

The gate system verified existence, isolated hashes and focused tests. It did not require a single `END_TO_END_PREFLIGHT_PASS` receipt, did not distinguish `CONTRACT_PASS` from `INTEGRATION_PASS`, and did not force task cards to bind every authority path/hash before dispatch.

### C. Documents that should have recorded the missing facts

`FINQA_V2_ANALYSIS_PLAN.md` should have been an explicit task-card input before the first run. The C audit report should have been materialized in `docs/experiments/` before any downstream dispatch. The binding contract should have named the raw/normalized authority domain. The handoff template should have required authority paths, hashes and pass level.

### D. State that existed but did not enter D's decision context

C's independent PASS existed in `loop_runs/c.log`; A correctly required a repo-visible report. The analysis plan existed only after the initial pre-result gap. The old harness audit already warned about multi-source state and local PASS overreach, but its recommendations were not integrated into the FinQA dispatch path.

### E. Multiple sources of truth

Chat summaries, `loop_runs/*.log`, task cards, receipts, `memory/STATE.md`, `memory/THREADS.md`, `docs/INDEX.md` and experiment reports each carried pieces of status. Several were valid evidence but none was consistently marked as the authority for the next decision.

### F. A/C/D contract understanding

A treated the task card's binding guard as sufficient until the real runner shape was tested. C independently found the metadata seam. D accepted the high-level `SCORER_BINDING_GO=PASS` without requiring the repo-visible report path in the next handoff. The roles agreed on intent but not on the authoritative evidence carrier.

### G. Component versus end-to-end tests

The 19 passed tests proved normalization, scorer behavior and freeze invariants in isolation. They did not prove runner metadata forwarding, full trace comparison under the real payload shape, or zero-output qualification over 89 pairs.

### H. Gates that were only local PASS

`SCORER_GO` proved source independence and frozen binding fields, not runtime execution. `SPLIT_GO` proved manifest split, not runner call shape. `PREREG_GO` proved plan freeze timing, not that the plan was bound to the task card before dispatch. These must be relabeled by level.

## Authority and Memory Audit

- `memory/STATE.md` is the intended current-state authority, but it mixed historical scientific state with current execution status.
- `memory/THREADS.md` is the intended blocker authority, but detailed blockers were also copied into prompts, logs and task cards.
- `logs/graph/dispatch_log.md` is a useful execution ledger but not a source of scientific truth.
- `docs/INDEX.md` is the navigation authority but was not updated for the FinQA binding-v3 qualification or the C audit report.
- `loop_runs/*.log` is an execution artifact, not a project authority unless copied into `docs/experiments/` and indexed.
- `docs/governance/audit/harness_audit_20260905/AUDIT_REPORT.md` is a valid historical governance baseline and already identifies the same failure families.

## Handoff Audit

The existing `SESSION_HANDOFF_TEMPLATE.md` required done/in-progress/issues but not authority paths, hashes, frozen/mutable fields, pass level, preflight command or stop state. The Graph Loop task contracts were stronger than the generic template but were created per task, so omissions could recur. The fix is a reusable handoff contract and a preflight receipt, not another task-specific prose checklist.

## Pass-Level Definition

| Level | Allowed claim |
|---|---|
| `UNIT_PASS` | a function/test passed |
| `COMPONENT_PASS` | one component passed focused checks |
| `CONTRACT_PASS` | schema/semantic/hash contract passed |
| `INTEGRATION_PASS` | the composed runtime seam passed |
| `END_TO_END_PREFLIGHT_PASS` | full chain simulated before scientific output |
| `FORMAL_RUN_PASS` | formal results plus independent recomputation passed |

No lower level may be summarized as a higher level. Gate reports must state scope and excluded paths.

## Hooks and Skills: Timing Review

| Capability | Current timing | Move earlier to | Rationale |
|---|---|---|---|
| `summary-recompute-guard` | pre-commit | FREEZE / REPORT | summary claims must not be accepted before evidence binding |
| `index-guard` | pre-commit | DOCUMENT CREATE / DISPATCH | authority files must be registered before downstream handoff |
| `skill_router.py` | routing aid | DISPATCH | route before execution and record selected skills |
| `dispatch_precheck.sh` | watcher-specific | DISPATCH subcheck | useful but insufficient for scientific preflight |
| `verify-before-done` | completion | POST-RUN and COMPLETION | catch local PASS overreach before result claims |
| `audit-cycle` | ad hoc | POST-RUN / GOVERNANCE CLOSEOUT | preserve baseline and first-hand evidence |
| `self-eval-bias` | review warning | every A/C verdict | fresh-context evidence is required for acceptance |
| `offline-eval-playbook` | interpretation | PREFLIGHT and CLAIM | check denominator/space/coverage before reading metrics |

## State Cleanup

- `ACTIVE`: FinQA runtime binding v3 engineering qualification.
- `READY`: none for a third formal scientific run.
- `BLOCKED`: `RUNTIME_BINDING_INTEGRATION_GO` and the repo-visible C qualification report for the in-flight v3 task.
- `STOPPED`: formal FinQA scientific reruns, PRM training, new scientific hypotheses.
- `SUPERSEDED`: binding-v2 as the runtime authority once binding-v3 is independently accepted; raw provenance remains retained.
- `INVALID_BUT_PRESERVED`: both prior formal FinQA runs and their receipts.
- `DONE`: analysis-plan freeze, raw/normalized diagnosis, source/ID/JOIN/SPLIT/scorer semantics qualification.

The current true blocker is end-to-end runtime binding integration coverage, not scientific design.

## Loop D Self-Audit

I dispatched formal work before requiring a repo-visible analysis-plan and end-to-end preflight receipt. I accepted local component PASS as evidence for a composed system. I relied on session/log summaries instead of forcing authority paths and hashes into every handoff. I optimized for progress over integration qualification. I did not ensure that A/C outputs flowed back into `STATE`, `THREADS` and `INDEX` before the next dispatch. These are orchestration defects and are addressed by the authority map, pass levels and formal preflight contract.

## Governance Readiness

`GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = NO`

The system is ready to continue governance and engineering qualification, but not a third formal scientific run. The next formal run requires a repo-visible `END_TO_END_PREFLIGHT_PASS`, binding-v3 `RUNTIME_BINDING_INTEGRATION_GO=PASS`, independent C PASS and the updated handoff/preflight receipts.
