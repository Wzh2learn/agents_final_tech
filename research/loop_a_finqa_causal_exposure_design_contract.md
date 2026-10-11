# Task Contract: FinQA Causal-Exposure Experiment Design - Loop A

- Task ID: `finqa-causal-exposure-design-a-20261010`
- Role: Loop A / GB10 feasibility and design
- Scope: design + frozen proposal only
- Window: zero-endpoint, no formal execution
- Mode: `inquiry-methods` first-principles/minimal-experiment design

## Frozen Scientific Question

When a controlled FinQA perturbation is allowed to causally propagate through program execution into the fields consumed by the frozen detection rule, what is the relationship between checkpoint visibility and protocol detection?

Do not assume D should be 1 and do not optimize for a non-degenerate VxD distribution.

## Fixed Design Boundaries

- Preserve the old FinQA v2 result as `FAILED TRANSFER DUE TO MEASUREMENT-OBJECT MISMATCH`.
- Do not change the old scorer semantics, metrics, thresholds, split, sample IDs or results.
- This is a new experiment proposal, not an execution.
- Do not manually edit `res` or `answer` in substantive cases.
- Do not select cases based on observed V/D outcomes.

## Initial Causal-Exposure Hypotheses

Classify and justify each family before outcome access:

1. `E` evidence mutation:
   - `NOT_CAUSALLY_EXPOSED_TO_D` under a fixed gold-program/argument execution path.
   - Keep as visibility-only/instrumentation control unless a separately specified deterministic evidence-to-argument extraction stage is part of the pipeline.
2. `P` operator mutation:
   - candidate `CAUSALLY_EXPOSED_TO_D` only if a deterministic executor recomputes downstream `res` and terminal answer.
3. `N` argument mutation:
   - candidate `CAUSALLY_EXPOSED_TO_D` only if a deterministic executor recomputes downstream `res` and terminal answer.

The proposal must include an explicit graph:

`injection target -> downstream computation -> res -> answer -> D input`.

## Program Re-execution Feasibility

Audit existing FinQA artifacts and semantics to determine:

- supported operator families and exact arithmetic rules;
- numeric literals, percent/string handling and `#k` references;
- downstream step dependency resolution;
- clean replay criterion: every gold `res` and terminal answer must be reproduced exactly before mutation is admitted;
- unsupported/ambiguous operations and exclusion policy;
- whether P/N mutations can be propagated without hand-writing results.

If full execution semantics are not established from existing evidence, report `EXECUTOR_FEASIBILITY_CONDITIONAL` and list the missing contract. Do not invent semantics.

## Eligibility Contract

Primary detection population must be frozen before V/D outcomes:

- multi-step FinQA records;
- deterministic clean replay passes;
- mutation is a legal P or N operation;
- mutation target and downstream execution path are known;
- report-cluster group is unique and split-safe;
- no eligibility criterion may use V, D, O, correctness, or expected effect.

Report `causal-exposure eligible rate` over the declared mother-pool denominator.

## Required Controls

Separate controls from substantive cases:

A. unchanged/sham pair: measurement sanity only, expected V=0/D=0;
B. V-positive instrumentation control: expected visible upstream change without substantive D claim;
C. D-positive instrumentation control: direct result/answer perturbation only to prove the detector can fire;
D. causal propagated P/N perturbations: the only primary scientific cases.

Controls must be labelled `CONTROL`, never pooled into primary estimands.

## Proposed Estimands

Pre-register only:

- V count/rate;
- D count/rate;
- VxD table;
- `P(D=1 | V=1)`;
- `P(D=1 | V=0)` if identifiable;
- per causal-family profile for P and N;
- causal-exposure eligible rate;
- clean-replay validity and exclusion counts.

No outcome-driven metric or target cell distribution.

## Required Proposal Outputs

1. `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`
2. `research/finqa_causal_exposure_20261010/finqa_causal_exposure_design.json`
3. `research/finqa_causal_exposure_20261010/finqa_causal_exposure_feasibility.json`
4. exact source/assumption/uncertainty ledger;
5. proposed frozen task card for a later execution, explicitly marked `NOT_EXECUTED`;
6. a machine-readable proposal receipt with hashes.

## Required Proposal Tests

No formal execution. The proposal must state how future implementation will test:

- clean replay exactness;
- deterministic P/N propagation;
- no manual `res`/`answer` editing in substantive cases;
- unchanged/sham and D-positive controls remain separate;
- eligibility is outcome-blind;
- unsupported operations fail closed.

## Forbidden Actions

- Execute the causal-exposure experiment.
- Run model/API/database/training calls.
- Modify frozen FinQA v2 artifacts or Paper E.
- Add new scientific hypotheses or metrics.
- Force E into D primary analysis.
- Select or drop cases based on V/D/O results.

## Stop Conditions

- no deterministic execution semantics for P/N;
- clean replay cannot reproduce gold outputs;
- causal path cannot be defined without manual result editing;
- eligibility cannot be made outcome-blind;
- controls cannot be separated from substantive cases.

## Success Exit

A frozen, reviewable proposal exists with explicit E/P/N causal graph, executor feasibility status, outcome-blind eligibility, controls, estimands and a `NOT_EXECUTED` task card, ready for Loop C challenge.
