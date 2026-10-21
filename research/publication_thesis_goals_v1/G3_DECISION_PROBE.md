# G3 Evidence-Driven Revalidation Headroom Probe

Date: 2026-10-21, Asia/Shanghai

Status: `BOUNDED_HEADROOM_CONTINUE_TO_NEW_REAL_TASK_DESIGN`

Evidence identity: `DEV_ONLY_MIXED_NATURAL_STATE_AND_SYNTHETIC_CONTROL_PROBE`

## 1. G3 Research Question

G2 asks whether a candidate migration is complete. G3 asks a different
decision question:

> When a dependency, rule or execution environment changes, which evidence
> should be acquired next, when is enough known to accept or reject, and when
> should the system stop or defer?

The target is not to build a more complex planner. The target is to determine
whether real tasks contain complementary validation actions with different
costs and risks, such that selective revalidation can preserve full-evidence
decisions at lower cost.

## 2. Evidence And Cases

The probe uses three natural NtripBrowser candidate states, one natural
DateTimeRange environment failure and seven explicitly labelled synthetic
controls. The synthetic cases cover valid aliases/wrappers, fallback masking,
dead target calls, behavioral regression, clean valid work and unresolved
dynamic imports.

Natural cases:

- NtripBrowser BASE: behavior passes but target dependency consumption fails
  because an old call is swallowed and UTF-8 fallback preserves fixtures.
- NtripBrowser PROSE and STRUCTURED: behavior and target consumption agree.
- DateTimeRange: the environment fails before a valid candidate judgment.

Synthetic controls are mechanism coverage only. They do not estimate natural
error prevalence.

## 3. Actions And Fixed Cost Model

| Action | Cost unit | Evidence |
|---|---:|---|
| Preflight | 1 | Environment and dependency readiness |
| Simple contract | 1 | Import/call presence or absence |
| Behavior | 3 | Deterministic selected tests |
| Enhanced consumption | 4 | Alias/wrapper-aware runtime or data-consumption evidence |

These costs are transparent planning units, not measured seconds. The model
was fixed before evaluation and was not tuned to make a strategy win.

## 4. Compared Strategies

- `no_revalidation`: accept without evidence.
- `behavior_only`: run behavior tests and accept on pass.
- `contract_only`: run a simple structural contract and accept on pass.
- `hybrid_fixed`: require behavior and simple contract.
- `full_revalidation`: run every action on every case.
- `fixed_order`: preflight, behavior and simple contract in a fixed order,
  escalating only after disagreement.
- `risk_greedy`: use actor-visible fallback, contract-gap and dynamic-import
  risk to select the first action and stop when evidence is sufficient.

Only actor-visible features drive `risk_greedy`; hidden truth and action
outcomes are used for evaluation after the decision.

## 5. Results

| Strategy | Correct | False accept | False reject | Unresolved | Coverage | Cost |
|---|---:|---:|---:|---:|---:|---:|
| No revalidation | 5/11 | 4 | 0 | 0 | 1.000 | 0 |
| Behavior only | 6/11 | 3 | 0 | 0 | 1.000 | 33 |
| Contract only | 5/11 | 2 | 2 | 0 | 1.000 | 11 |
| Hybrid fixed | 6/11 | 1 | 2 | 0 | 1.000 | 44 |
| Full revalidation | 11/11 | 0 | 0 | 2 | 0.818 | 99 |
| Fixed order | 10/11 | 1 | 0 | 2 | 0.818 | 63 |
| Risk greedy | 11/11 | 0 | 0 | 2 | 0.818 | 62 |

The main observation is:

> On this controlled probe, risk-triggered selective revalidation reproduces
> the decisions of full revalidation while reducing cost from 99 to 62.

The result also identifies two failure modes of simpler methods. Behavior-only
accepts fallback-masked and dead-consumption cases. Contract-only rejects
reasonable alias/wrapper implementations and still accepts some dead-code
presence cases.

## 6. Ruling

`CONTINUE_TO_NEW_REAL_TASK_DESIGN`.

There is enough headroom to justify a small confirmation study of risk-triggered
selective revalidation. There is not enough evidence to claim a new adaptive
method. The current natural sample contains one task and one environment
failure; most mechanism coverage comes from synthetic controls.

The candidate G3 contribution should therefore be framed as:

> Selective revalidation under explicit fallback/consumption risk: choose
> behavioral, structural and consumption evidence to minimize validation cost
> while preserving full-evidence decisions and exposing unresolved cases.

This is distinct from G2. G2 evaluates migration validity; G3 evaluates the
order, stopping and deferral policy over those evidence sources.

## 7. Next Confirmation Gate

Freeze the risk features and action costs before collecting new tasks. Use at
least 8 previously unused real task families or source clusters, with no
synthetic case counted as an independent task. Compare full revalidation,
fixed order, risk greedy and simple behavior/contract baselines.

Primary metric: total validation cost at equal false-accept risk and no lower
coverage than full revalidation. Secondary metrics: false reject, unresolved,
actions per task, and the fraction of tasks where early stopping is safe.

Stop or simplify the G3 method if:

- risk greedy has any additional false accept;
- coverage falls below full revalidation;
- cost saving disappears after measured action costs replace planning units;
- a fixed rule or always-run-one-action baseline matches it;
- the risk features require hidden checker or gold information.

## 8. Memory And Training Decision

No Memory or LoRA/SFT experiment is started. The available evidence has no
repeated error-feedback-action trajectory and no learned condition that must be
represented in parameters. If later real tasks show repeated repairable errors
with observable preconditions, conditional experience can be tested against
strong rules and solved examples. Training remains a replaceable mechanism,
not a G3 contribution by default.

## 9. Resource Use

- Model calls: 0.
- Judge calls: 0.
- Training runs: 0.
- Network calls: 0.
- Computation: deterministic Python evaluation and five focused tests.
- Raw output: `G3_PROBE_RESULTS.json`.
