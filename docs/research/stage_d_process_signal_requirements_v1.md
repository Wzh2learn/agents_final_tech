# Stage D Process Signal Requirements v1

> 状态: `QUALIFIED_FOR_NONCOMMERCIAL_ACADEMIC_DESIGN_AND_SMOKE` | 更新: 2026-10-10 | 取代/被取代: 纳入实际 Agent Distillation payload 与新 licence policy；不授权正式 C0/C1/C2/C4 training

## 1. Licence boundary

Record three ledgers separately:

```text
CODE LICENCE
DATA LICENCE
MODEL LICENCE
```

Apache-2.0 / MIT / BSD code may be cloned, modified, run, reproduced, adapted and used in non-commercial academic experiments. A missing dataset/model licence is `LICENCE_PENDING`, not a default research stop.

While `LICENCE_PENDING`:

- allowed: metadata/schema inspection, small-sample inspection, adapter development, preprocessing/smoke, local non-commercial academic method validation and experiment design;
- not allowed: public redistribution, released derived datasets, commercial use, or large-scale formal training used as the final paper main result.

Only explicit terms prohibiting the current academic use justify `LICENCE_BLOCKED`.

## 2. Mother-pool hard condition

Do not prioritize trajectory volume. A defensible C2/C4 pilot needs the same sample to contain:

```text
trajectory/action + terminal success/outcome + at least one verifiable process signal
```

It also needs exact revision, data/model licence status, stable task/trajectory IDs, origin grouping, split role, token count and process-signal provenance.

## 3. ToolAlpaca first signal

Name: **Tool Contract Validity**, not step/process correctness.

```text
TCV(step) = tool_exists AND action_type_valid AND argument_schema_valid
```

- Deterministic if tool registry and argument schemas are frozen.
- No replay is required for syntactic validity.
- Replay is required for observation consistency or state-transition validity.
- Evidence level: L2 deterministic-derived.
- It cannot judge semantic action correctness.

Minimum additional semantic signal for a real C4-derived arm: observation consistency, state-transition validity, execution success, goal-progress verifier or independent step verifier.

## 4. Agent Distillation actual payload qualification

Official baseline dataset revision: `cbd8971069aeb04ec3cc95282ef2397e8206a817`. Actual payload SHA-256: `ba36277510a35b51125c9b0a0a6847f18a6403488152f4afff4a51841da565df`, 47,349,288 bytes, 1,928 JSONL rows.

| Requirement | Actual status | Provenance |
|---|---|---|
| Mother pool | 1,928 released baseline trajectories | `DATA VERIFIED` |
| Action/observation | `tool-call` / `tool-response` messages and memory steps | `DATA VERIFIED` |
| Terminal score | raw values `True=784`, `1=597`, blank=`547` | `DATA VERIFIED`, normalization required |
| Terminal variation | 1,381 normalized positives, 0 normalized negatives, 547 missing/non-binary | `DATA VERIFIED` |
| Process signal | `step_reward` rows=`0` | no released native process label |
| Task/trajectory/origin IDs | explicit fields=`0` | derived IDs/groups required |
| Split | explicit row split=`0` | derived split required |
| Code licence | Apache-2.0 | `REPO VERIFIED` |
| Data licence | `LICENCE_PENDING` | dataset README has no explicit licence text |
| Model licence | not needed for payload inspection | separate if models are later used |

`FACT`: the released payload is more than code capability, but it is not yet a clean C2/C4 mother pool. The missing terminal negatives prevent a meaningful terminal-outcome filter contrast; missing process provenance prevents native C4.

`VALUE`: Agent Distillation remains the preferred **agent-distillation engineering carrier candidate** for adapter and preprocessing work. Its current gate is `DATA_CAPABLE_LICENCE_PENDING_NOT_PILOT_READY`, not `C2/C4 PILOT CANDIDATE`.

## 5. External source order

1. PRM800K: validate process-versus-outcome reference contract; `PRM_REFERENCE_READY`.
2. Math-Shepherd: validate automatic derived-process-supervision paradigm.
3. Agent Distillation: adapter/engineering carrier and future agent-domain mother-pool candidate.
4. ToolAlpaca: action adapter and Tool Contract Validity feasibility only.

ToolBench/AgentTuning remain secondary candidates until actual payload, outcome variation, process signal and grouping are verified.

## 6. Minimum missing items for Agent Distillation pilot

A small C2 versus C4 pilot still needs:

1. terminal outcome variation, including defensible negatives or a documented alternative outcome oracle;
2. at least one provenance-labeled process signal not derived from the terminal score;
3. stable task/trajectory/origin IDs and a frozen split.

Adapter/preprocessing smoke may proceed now. Formal pilot fitting remains `NEEDS_DECISION` after those three items are closed.

## 7. C2/C4 comparison boundary

- C2 selects on terminal outcome only.
- C4 selects on independently identified process/checkpoint evidence.
- Match mother pool, student model, optimizer, token budget, origin-group budget and evaluation set.
- C4 must be compared with C2, not only with zero-shot/unfiltered.
- Derived labels must retain `deterministic-derived`, `verifier-derived`, `judge-derived` or `proxy`; never relabel them as native.

`FACT`: no training is run in this qualification stage.
