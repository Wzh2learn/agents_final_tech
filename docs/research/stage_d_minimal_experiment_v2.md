# Stage D Minimal Experiment v2

Status: `DESIGN_ONLY_NOT_AUTHORIZED`; `execution_authorized=false`

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

## 1. Source and boundary record

This v2 adapts the already audited C0/C1/C2/C4 design in [`evaluation_guided_distillation_design_v1.md`](../../../../external_stage_d_repro/reports/evaluation_guided_distillation_design_v1.md). Source identity/licence/schema blockers are recorded in [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json) and the reused audits listed in [`process_supervision_adaptation_review_v1.md`](process_supervision_adaptation_review_v1.md).

`FACT`: no model, judge, dataset body, SFT, training, GPU, endpoint, service, database, package installation, Phase 2, Stage R, or E-D-R action has occurred.

## 2. Research assumption

> At a fixed student, optimizer, token budget, origin-group budget, evaluation set, and seed set, filtering with native process/checkpoint evidence (C4) improves held-out terminal performance over terminal-outcome filtering (C2).

`INFERENCE`: C4-C2 is the smallest decision-relevant comparison. It does not prove that all process evidence helps, that proxy divergence equals native checkpoints, or that Stage E localization transfers.

## 3. Mother pool and source gate

A future mother pool must contain:

- source project and exact revision;
- task/API/environment origin group;
- trajectory and step IDs;
- terminal outcome/reward;
- native checkpoint evidence where available;
- evidence-origin and quality level;
- token count after the frozen chat template;
- capability/error-family annotations where publicly available;
- licence/provenance/permitted-use status.

Only sources whose dataset revision, licence, provenance, and permitted research/training/modification scope are proved may enter a training pool. All other sources remain metadata-only.

`FACT`: currently no inspected source has closed every required source, join, split, licence, and process-evidence gate.

## 4. Origin groups and split

`origin_group` is the independent unit:

- ToolAlpaca: API `Name` or preregistered API family;
- TheAgentCompany: task family/environment lineage;
- Agent Distillation: source dataset/question family;
- other sources: source project plus task/environment family declared before outcome inspection.

All records from one origin group and every step of a trajectory stay in exactly one role.

| Role | Purpose |
|---|---|
| `proposal` | Adapter/schema/protocol development; no scientific threshold fitting against final outcomes |
| `train` | Future fitting only after authorization |
| `gate_validation` | Threshold, ablation, and stopping decisions |
| `sealed_test` | Final confirmatory evaluation after all rules and hashes freeze |
| `future_replay` | Reserved independent replay |

`VALUE`: a starting allocation of 10% proposal, 60% train, 15% gate-validation, and 15% sealed test is a design choice, not an optimized result. Every non-proposal role needs at least eight independent groups.

Evaluation membership, tokenizer/chat template, metric code, and hashes freeze before arm construction.

## 5. Arms

All arms use one mother pool and the same base model, optimizer, chat template, maximum sequence length, and token accounting.

| Arm | Rule | Minimum role |
|---|---|---|
| C0 | Unfiltered mother pool | Sanity baseline |
| C1 | Random selection matched on trajectories, tokens, and origin groups | Chance-selection control |
| C2 | Terminal outcome/reward selection only | Outcome-only comparator |
| C4 | Native checkpoint/process-evidence selection | Primary process arm |

`VALUE`: paper-primary comparison is **C4-C2**. C0/C1 diagnose selection effects; they are not substitutes for C2.

Optional reward/heuristic, weighting, divergence, or joint arms remain secondary and preregistered.

## 6. Regimes

Report both:

1. **Natural-data regime** — actual available scale;
2. **Matched size/token/group regime** — matched trajectory count, non-padding tokens, and origin-group distribution.

`FACT`: the confirmatory claim rests on the matched regime. A natural-size result cannot attribute gains to selection quality when token/group budgets differ.

`FACT`: token mismatch may not exceed 0.5%; model, optimizer, template, and seeds must match across arms.

## 7. Model and resource contract

| Item | Frozen design value |
|---|---|
| Main student | 8B |
| Training smoke only, if separately authorized | 4B; never main evidence |
| Token budget | 64M non-padding tokens per arm/seed |
| Arms | C0, C1, C2, C4 |
| Seeds | 5 |
| Epochs | 1 |
| Total main planned budget | `64M × 4 × 5` non-padding tokens |
| GPU/model calls in this task | 0 |

`FACT`: these are planning values from the reused design, not executed work or measured results.

## 8. Metrics

### Primary

- held-out terminal success for C4-C2 in the matched regime.

### Secondary

- terminal outcome/reward;
- native checkpoint score and pass fields where available;
- step/tool error rates by planning, tool selection/arguments, retrieval, observation interpretation, arithmetic/reasoning, and final answer;
- external harm/risk annotations, kept separate from frozen Stage E harmfulness;
- success per million non-padding tokens;
- capability-family and worst-group scores;
- calibration only if collected by the frozen evaluator;
- retention composition by group, trajectory, step, token, error family, and evidence level.

`FACT`: secondary metrics cannot rescue a failed primary comparison.

## 9. Statistics and power

- Experimental unit: `origin_group`.
- Pairing: C4 versus C2 within the same seed and evaluation group.
- Primary interval: group-clustered paired bootstrap with 10,000 resamples.
- Report point estimate, 95% interval, per-seed values, and per-group values.
- Mixed-effects sensitivity may include seed as a random intercept and capability family as a fixed effect.
- Five seeds are not 25 independent groups.

`UNVERIFIED`: no external variance estimate has been accessed. Before any future training:

1. estimate group-level variance only from proposal or gate-validation evidence;
2. set the smallest effect of interest before fitting;
3. require at least 80% power at two-sided α=.05;
4. require at least 24 independent evaluation groups;
5. require at least 8 groups per major capability family where available.

## 10. Decision rules

Request a future execution authorization only if source cards pass; C4 uses Level 3/4 native evidence; same-sample joins are proved; split overlap is zero; hashes match; token mismatch is ≤0.5%; and the power gate passes.

Support for the process-evidence hypothesis requires:

1. C4 exceeds C2 in the matched regime;
2. the 95% interval for `Delta_primary` excludes zero in the positive direction;
3. the direction repeats in at least four of five seeds;
4. external risk/harm metrics do not regress beyond a preregistered non-inferiority margin;
5. the sealed test runs once after code and rules freeze.

`VALUE`: a one-percentage-point harm/risk regression margin is only a starting proposal and must be fixed before gate-validation outcomes are inspected.

## 11. Stop conditions

Stop if source licence/provenance fails; C4 is proxy or terminal-only; split/group overlap is nonzero; token mismatch exceeds 0.5%; model/optimizer/template/seeds differ; power fails; sealed information influenced a rule; safety regression crosses the frozen margin; primary effect is non-positive; or any model/training/service action lacks explicit separate authorization.

## 12. Current experiment state

| Action | State |
|---|---|
| Source card closure | Blocked |
| Stable same-sample bridge | Missing |
| Static group/token matching audit | Not run in this task |
| C0/C1/C2/C4 fitting | Not authorized |
| Sealed evaluation | Not authorized |
| Phase 2 / Stage R / E-D-R | Not started |

`FACT`: this is a design document only. It does not advance Stage D or produce a confirmatory result.
