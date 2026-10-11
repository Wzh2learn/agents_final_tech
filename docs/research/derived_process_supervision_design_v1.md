# Derived Process-Supervision Design v1

Status: `DESIGN_ONLY_NOT_AUTHORIZED`

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

## 1. Source and boundary record

The pre-conclusion source register is [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json). Reused evidence comes from the external schema, taxonomy, and stop reports cited in [`process_supervision_adaptation_review_v1.md`](process_supervision_adaptation_review_v1.md).

`FACT`: this design does not edit a frozen schema, create training data, inspect a released body, or authorize C0/C1/C2/C4.

`UNVERIFIED`: no admitted source currently proves exact revision + dataset licence + stable trajectory/checkpoint/action/outcome join + origin-group split.

## 2. Design goal

`VALUE`: determine whether process evidence adds held-out value beyond terminal outcome while preserving the provenance and independence of each supervision signal.

The design must keep five evidence classes separate:

1. **native** — created by the original generation/evaluation process;
2. **deterministic-derived** — reproducibly computed from preserved inputs and fixed rules;
3. **verifier/judge-derived** — generated or transformed by a verifier or judge;
4. **human-validated** — independently reviewed under a frozen contract;
5. **proxy** — correlated with process quality but not process correctness.

`INFERENCE`: none of these classes substitutes for another merely because its numeric values look similar.

## 2.1 Label-quality ladder

| Level | Evidence meaning | Permitted interpretation |
|---:|---|---|
| L0 | Terminal outcome only | Outcome filtering or C2 comparator |
| L1 | Proxy process signal | Sensitivity analysis only; never native process correctness |
| L2 | Deterministic-derived process signal | Reproducible derived arm with input/code/output hashes |
| L3 | Model/verifier-derived process label | Verifier-derived supervision with identity, version and contract provenance |
| L4 | Human-validated process label | Human review under a frozen, independently recorded contract |
| L5 | Independent multi-source validated process evidence | Strongest evidence class; requires independent implementation/reviewer/source convergence on the same sample |

`FACT`: `native`, `human-annotated`, `deterministic-derived`, `verifier-derived`, `judge-derived`, and `proxy` remain provenance labels. They are not interchangeable with L0-L5 quality levels. Native source provenance does not assign a level by itself; the level follows the independent evidence required by the ladder.

## 3. Proposed event contract

Every proposed event carries the following fields:

| Group | Fields |
|---|---|
| Identity | `dataset_id`, `dataset_revision`, `origin_group`, `task_id`, `trajectory_id`, `step_id` |
| Process | `state_before`, `reasoning_if_public`, `action`, `action_type`, `action_arguments`, `observation`, `state_after` |
| Outcome | `terminal_outcome`, `terminal_reward` |
| Supervision | `step_correctness`, `step_reward`, `checkpoint_evidence`, `checkpoint_name`, `checkpoint_score`, `checkpoint_pass` |
| Provenance | `evaluator_type`, `evidence_origin`, `evidence_level`, `native_source_provenance`, artifact/input/code hashes |
| Isolation | `split_role`, calibration/evaluation status, capability and error-family tags when available |
| Risk | external `harm_or_risk` annotation kept separate from frozen Stage E harmfulness |

`FACT`: null means unavailable. The design never fabricates a label or turns an absent checkpoint into a zero.

## 4. Provenance rules

### Native

Native source evidence admission requires:

- exact source revision;
- stable task/trajectory/sample identity;
- artifact reference and SHA-256;
- checkpoint/evaluator identity;
- evidence created by the original generation/evaluation process;
- a stable sample-level join.

`FACT`: code capability without paired released samples is not native sample evidence.

### Deterministic-derived

Level 2 requires:

- exact input hash;
- rule/code version and code hash;
- deterministic output hash;
- replay test;
- explicit `evidence_origin=deterministic_derived`.

Example permitted derivations:

- state transition normalization;
- action/parameter parse checks;
- mechanically derived stage-failure categories;
- Stage E visibility **only as its own construct**, not as correctness.

### Verifier/judge-derived

Requires judge/verifier identity, version/date, prompt or contract hash where applicable, and `judge_derived`.

`UNVERIFIED`: a second field or prompt does not prove independence; shared code/labels may explain agreement.

### Human-validated

Level 4 requires Level 3 evidence plus a genuinely independent reviewer/contract/implementation joined to the same sample under frozen predicates.

`FACT`: human validation is not assumed where reviewer contract, blinding, identity, or sample join is absent.

### Proxy

Includes student-teacher divergence, heuristic error strings used as stand-ins, and other correlated signals.

`VALUE`: proxies may support sensitivity analyses but cannot populate native C4.

## 5. Source admission gates

| Gate | Required evidence | Failure status |
|---|---|---|
| G0 Identity | Exact revision, task/trajectory/step IDs | `UNAVAILABLE` |
| G1 Licence | Dataset-specific licence and permitted research/training/modification scope | `BLOCKED_METADATA_ONLY` |
| G2 Join | Trajectory + checkpoint/evaluator + action + outcome stable join | `NO_SAME_SAMPLE_BRIDGE` |
| G3 Provenance | Native/derived/judge/human/proxy origin plus evaluator identity | `NOT_ELIGIBLE` |
| G4 Split | Origin group assigned before outcome inspection; zero cross-role leakage | `NO_CONFIRMATORY_SPLIT` |
| G5 Coverage | Explicit denominators, skipped/missing steps, error-family composition | `COVERAGE_UNVERIFIED` |
| G6 Replay | Deterministic adapters reproduce hashes and schema | `NOT_REPRODUCIBLE` |
| G7 Power | Group-level variance, effect size, ≥80% power, α=.05, ≥24 groups and ≥8 per major family where available | `UNDERPOWERED_STOP` |

`FACT`: every gate is conjunctive for future confirmatory selection; passing schema validation alone does not approve a source.

## 6. Selection design

### Mother pool

Build one pool before outcome-based selection with source/revision, origin group, trajectory/step IDs, terminal outcome, native checkpoint evidence when available, evidence level/origin, post-template token count, capability/error annotations, and licence/provenance status.

### Roles

| Role | Permitted use |
|---|---|
| `proposal` | Adapter/schema/protocol development only |
| `train` | Future fitting after separate authorization |
| `gate_validation` | Threshold, ablation, stopping decisions |
| `sealed_test` | One final confirmatory pass after code/rule freeze |
| `future_replay` | Reserved independent replay |

`VALUE`: a starting allocation of 10% proposal, 60% train, 15% gate-validation, and 15% sealed test is a design proposal, not a fitted optimum; every non-proposal role requires at least eight independent origin groups.

### Arms

| Arm | Selection | Role |
|---|---|---|
| C0 | Unfiltered mother pool | Sanity baseline |
| C1 | Random selection matched on trajectories, tokens, and origin groups | Chance control |
| C2 | Terminal-outcome/reward only | Outcome comparator |
| C4 | Native checkpoint/process evidence only | Primary process arm |

`VALUE`: the primary comparison is C4 minus C2; C0 and C1 diagnose selection effects but cannot rescue it.

Optional C3/C5/C6/C7 arms may test heuristics, weighting, divergence, or joint signals only if preregistered. They cannot be relabelled as the primary native-process test.

## 7. Stage E relation

Stage E can inform:

- observable versus blind families;
- threshold stability;
- protocol detection cells;
- negative-observability controls;
- the requirement that visibility, detection, and harmfulness remain separate.

Stage E cannot currently provide:

- action correctness;
- terminal student benefit;
- native process labels;
- a harmful-map for Stage D;
- an independent second dataflow;
- proof that checkpoint filtering improves distillation.

`FACT`: the frozen `H/HI/E` operational classes are not imported as a Stage D harmful-map, and the `harmful-map risk upper <= 0.10` future gate remains separate.

## 8. Stop conditions

Stop before fitting if any source lacks revision/licence/provenance; C4 uses proxy or terminal-only evidence; any join/split overlap exists; model/token/optimizer/seed hashes differ; token mismatch exceeds 0.5%; power fails; sealed evidence influenced a rule; or any model, training, GPU, service, database, credential, Phase 2, Stage R, or E-D-R action lacks separate authorization.

`FACT`: current status stops at design. No arm is trained, no source body is admitted, and no execution window exists.
