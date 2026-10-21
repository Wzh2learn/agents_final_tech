# Adaptive Revalidation V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the V3 adaptive-revalidation artifact with an isolated policy RPC boundary, opaque actor identifiers, replay-bound receipts, and the required 0-9 budget comparison.

**Architecture:** Split actor-safe DTOs and policy code from evaluator-only graph/fixture/metric code. Execute policy batches in a spawned process whose only outward capability is a three-method RPC client. The evaluator serves tool calls, replays the fixed repairer, computes metrics/upper bounds, and verifies receipts by recomputing the complete result payload.

**Tech Stack:** Python 3.9 and 3.11, standard-library multiprocessing/JSON/hashlib, pytest.

## Global Constraints

- Preserve all files and results under `research/adaptive_revalidation_v2/`; do not edit that package.
- Keep nine scenario families and five policies: `no_check`, `random_check`, `unit_cost_greedy`, `two_step_lookahead`, `full_recompute`.
- Keep the fixed repairer and all V2 metrics; do not replace partial metrics with a single score.
- Policy code receives only serialized `ActorInput`, returned evidence, and exactly `inspect_dependency`, `inspect_change`, `run_target_test`.
- Actor-visible scenario, change, node, and output IDs are stable opaque IDs; semantic names and evaluator mappings stay outside policy inputs.
- Run query budgets 0 through 9, report the cost/action-loss frontier, and compare greedy versus two-step at matched query cost.
- All outputs remain `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`; model, network, judge, database, and training calls are zero.
- Do not commit the shared dirty worktree.

---

### Task 1: Actor-Safe DTO and Identifier Boundary

**Files:**
- Create: `research/adaptive_revalidation_v3/actor.py`
- Modify: `research/adaptive_revalidation_v3/model.py`
- Modify: `research/adaptive_revalidation_v3/fixtures.py`
- Test: `research/adaptive_revalidation_v3/tests/test_adaptive_revalidation.py`

**Interfaces:**
- Consumes: frozen `scenarios.json`, `ExecutionGraph`, `ScenarioFixture`.
- Produces: `ActorInput`, `ChangeSummary`, `DependencyEvidence`, `ChangeEvidence`, `TargetTestEvidence`, `EvidenceBundle`, `FinalAction`, `PolicyDecision`, `PolicySpec`, `PolicyKind`, and `ActorIdentityMap`.

- [ ] **Step 1:** Add actor-only DTOs, canonical JSON helpers, and strict actor-input validation in `actor.py`.
- [ ] **Step 2:** Add stable index-derived opaque IDs and evaluator-only semantic mappings in `fixtures.py`; derive changed sources in graph order.
- [ ] **Step 3:** Rewrite `model.py` to import actor DTOs and retain evaluator-only graph/trace/result classes.
- [ ] **Step 4:** Add opacity tests that mutate hidden family/description/scenario labels and Gold snapshots and assert identical serialized actor input.
- [ ] **Step 5:** Run the focused test module and fix only boundary/type failures.

### Task 2: Process/RPC Policy Capability Boundary

**Files:**
- Create: `research/adaptive_revalidation_v3/policy_rpc.py`
- Modify: `research/adaptive_revalidation_v3/policies.py`
- Modify: `research/adaptive_revalidation_v3/environment.py`
- Modify: `research/adaptive_revalidation_v3/repairer.py`
- Test: `research/adaptive_revalidation_v3/tests/test_adaptive_revalidation.py`

**Interfaces:**
- Consumes: actor DTOs and the evaluator's `ThinEnvironment` tool handler.
- Produces: `execute_policy_batch`, `run_introspection_probe`, and actor-only `PolicyDecision` values.

- [ ] **Step 1:** Remove evaluator imports from `policies.py` and `repairer.py`; use only `actor.py`.
- [ ] **Step 2:** Implement a spawn-based batch worker and RPC client with exactly three public call methods and serialized tool payloads.
- [ ] **Step 3:** Make `ThinEnvironment` accept only opaque actor IDs and map to semantic fixture/graph state internally.
- [ ] **Step 4:** Run policy batches through `execute_policy_batch`; fail closed on tool, type, budget, and protocol violations.
- [ ] **Step 5:** Add adversarial introspection tests for public methods, object slots/globals, forbidden evaluator modules, and policy-process PID separation.

### Task 3: Metrics, Budget Sweep, and Scientific Comparison

**Files:**
- Modify: `research/adaptive_revalidation_v3/metrics.py`
- Modify: `research/adaptive_revalidation_v3/runner.py`
- Test: `research/adaptive_revalidation_v3/tests/test_adaptive_revalidation.py`

**Interfaces:**
- Consumes: actor actions/evidence, evaluator-only `ScenarioFixture` and `ExecutionGraph`.
- Produces: `run_experiment(..., budgets=...)`, `run_budget_sweep`, `compute_cost_action_loss_frontier`, `compare_paired_policies`, and serialized comparison sections.

- [ ] **Step 1:** Map opaque output IDs back to semantic graph outputs before computing all existing metrics.
- [ ] **Step 2:** Add `query_budget` to episode records and execute budgets 0-9 without family-based sampling or scoring.
- [ ] **Step 3:** Compute nondominated aggregate cost/action-loss points and matched-budget greedy/two-step paired deltas.
- [ ] **Step 4:** Assert five policy kinds, nine families, deterministic replay, fixed-repairer boundary, and zero-call accounting in tests.

### Task 4: Replay-Bound Receipt Verification

**Files:**
- Modify: `research/adaptive_revalidation_v3/receipt.py`
- Modify: `research/adaptive_revalidation_v3/__main__.py`
- Test: `research/adaptive_revalidation_v3/tests/test_adaptive_revalidation.py`

**Interfaces:**
- Consumes: source hashes, frozen scenarios, budget-sweep replay, and test-summary arguments.
- Produces: `build_receipt`, `write_receipt`, `verify_receipt`, and CLI commands `run`, `receipt`, `verify-receipt`.

- [ ] **Step 1:** Make `build_receipt` include budget sweep, frontier, paired comparison, source hashes, zero-call accounting, evidence boundary, and replay hashes.
- [ ] **Step 2:** Make `verify_receipt` recompute the complete result payload and aggregates from source/frozen inputs.
- [ ] **Step 3:** Validate test summary shape/status/counts and all zero-call fields; reject missing, inconsistent, or non-zero values.
- [ ] **Step 4:** Add tamper tests for result rows, aggregates, replay hashes, source hashes, and test summary fields.
- [ ] **Step 5:** Regenerate `result_receipt.json` only after source and tests are stable; verify it with the CLI.

### Task 5: Documentation and Cross-Version Verification

**Files:**
- Modify: `research/adaptive_revalidation_v3/README.md`
- Modify: `research/adaptive_revalidation_v3/TASK_SPEC.md`
- Modify: `research/adaptive_revalidation_v3/RESULT_NOTE.md`
- Modify: `research/adaptive_revalidation_v3/IMPLEMENTATION_REPORT.md`
- Create: `research/research_portfolio_v2/ADAPTIVE_V3_IMPLEMENTATION_REPORT.md`

- [ ] **Step 1:** Replace stale V2 paths/counts with V3 RPC, opaque-ID, budget, frontier, and receipt semantics.
- [ ] **Step 2:** Run focused tests under Python 3.9 and Python 3.11.
- [ ] **Step 3:** Run deterministic replay, budget sweep, receipt creation, and receipt verification.
- [ ] **Step 4:** Record exact commands, outputs, file list, and remaining concerns in the required implementation report.
- [ ] **Step 5:** Confirm no model/network/judge/database/training calls and no commit.
