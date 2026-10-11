# Process-Supervision Adaptation Review v1

Status: metadata and schema review only; no released dataset body was opened for this deliverable.

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

## 1. Source record before conclusions

The new PRM800K and Math-Shepherd records are in [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json). The previously completed Agent Distillation, ToolAlpaca, TheAgentCompany, AgentTuning, Agent-FLAN, and SOD audits are reused rather than repeated:

- [`external_related_work_matrix_v1.md`](../../../../external_stage_d_repro/reports/external_related_work_matrix_v1.md)
- [`checkpoint_evidence_quality_taxonomy_v1.md`](../../../../external_stage_d_repro/reports/checkpoint_evidence_quality_taxonomy_v1.md)
- [`external_real_schema_audit_v1.md`](../../../../external_stage_d_repro/reports/external_real_schema_audit_v1.md)
- [`stage_e_external_candidate_matrix_v1.md`](../../../../external_stage_d_repro/reports/stage_e_external_candidate_matrix_v1.md)
- [`phase_g_stop_report_v1.md`](../../../../external_stage_d_repro/reports/phase_g_stop_report_v1.md)

`FACT`: the reused reports record fixed repository commits, licence status, inspected code/schema evidence, and exact missing layers. They do not authorize dataset use or training.

## 2. PRM800K official audit

| Field | Record |
|---|---|
| Identity | OpenAI PRM800K, *Let's Verify Step by Step* |
| Paper | [arXiv:2305.20050](https://arxiv.org/abs/2305.20050) |
| Repository | [openai/prm800k](https://github.com/openai/prm800k) |
| Revision | commit `7ecc794703b2877f63226f2477a49b34f9b25163`, latest repository commit dated 2023-06-01T17:40:59Z |
| Repository licence | root [MIT licence](https://github.com/openai/prm800k/blob/main/LICENSE) |
| Dataset revision | `UNVERIFIED` |
| Dataset-specific licence | `UNVERIFIED`; no separate data notice was found |
| Bodies / LFS revisions | Not downloaded / not enumerated |

`FACT`: the README documents newline-delimited JSON records with one full solution per line. Documented fields include `question`, `pre_generated_steps`, `pre_generated_answer`, `pre_generated_verifier_score`, `labeler`, quality-control/screening flags, and `label.steps` entries containing text, `rating`, `flagged`, `human_completion`, and `chosen_completion`; `label` also documents `total_time` and `finish_reason`.

`INFERENCE`: the documented step labels are candidates for source-native process supervision if the released records prove a stable sample-level join and the dataset use terms are separately cleared.

`UNVERIFIED`: released body schema, exact dataset revision, dataset-specific licence, train/held-out group mapping, and the actual completeness of every documented field union.

`VALUE`: PRM800K is a high-priority future process-label source, but it is metadata-only until those blockers close.

## 3. Math-Shepherd official audit

| Field | Record |
|---|---|
| Identity | *Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations* |
| ACL | [2024.acl-long.510](https://aclanthology.org/2024.acl-long.510/) |
| DOI | [10.18653/v1/2024.acl-long.510](https://doi.org/10.18653/v1/2024.acl-long.510) |
| arXiv | [2312.08935](https://arxiv.org/abs/2312.08935), v3 updated 2024-02-19T14:07:53Z |
| Official repository | `NOT_ESTABLISHED` |
| Paper/data licence | `UNVERIFIED` |
| Dataset revision and schema | `UNVERIFIED` |

`FACT`: the paper describes automatic construction from a problem, intermediate solution steps, and a golden answer. A completer generates multiple continuations from each prefix; hard estimation labels a step by whether any decoded continuation reaches the golden answer, while soft estimation uses the proportion of successful continuations.

`FACT`: the inspected official paper reports GSM8K and MATH construction/evaluation but provides no released-record JSON schema in the inspected material.

`INFERENCE`: if an exact, licence-cleared implementation and record are later proved, Math-Shepherd labels would be verifier-derived process supervision rather than native human checkpoints.

`UNVERIFIED`: official repository identity, released data, schema, revision, licence, continuation-generation parameters, and stable joins.

`FACT`: the paper's cited `deepseek-ai/DeepSeek-LLM` repository is not treated as a Math-Shepherd project repository.

## 4. Reused source classifications

| Source | Supported evidence boundary | Highest presently supported level | Missing layer |
|---|---|---:|---|
| Agent Distillation | Message/step structure, terminal score, deterministic error handling; `step_reward` provenance unknown | 2 at most | Released payload and `step_reward` provenance |
| ToolAlpaca | Nested action/argument/thought/observation and final output; no machine-readable step-correctness field | 0 for native checkpoint; Level 1 only as proxy | Native step correctness and stable group split |
| TheAgentCompany | Native `Checkpoint(total,result)`, `Result.final_score`, checkpoint rubrics, and task evaluators | 3 in capability; 0 in released sample evidence | Zero bundled `traj_*.json`/`eval_*.json` pairs |
| AgentTuning | README-level terminal/reward filtering claim | 0 from inspected payload | Schema, native step evidence, licence, groups |
| Agent-FLAN | Corpus decomposition and negatives described at README level | 0 for process checkpoint | Trajectory/checkpoint payload and schema |
| SOD | README describes step-level teacher-student divergence and adaptive weighting | 1 proxy | Native correctness, payload, licence, groups |
| PRM800K | Documented stepwise rating/flagged/human/chosen fields | Level 3 candidate, not admitted | Dataset revision/licence and released join |
| Math-Shepherd | Paper-level hard/soft automatic continuation labels | Level 2 candidate, not admitted | Repository, data, schema, revision, licence |

`FACT`: no source currently supplies an admitted, licence-cleared, same-sample bridge containing trajectory, native checkpoint/evaluator, action steps, terminal outcome, origin group, and split role.

## 5. Evidence-level rules

| Level | Meaning | Stage D use |
|---:|---|---|
| 0 | Terminal-only or no intermediate evidence | C2 comparator only |
| 1 | Proxy process signal such as divergence | Optional sensitivity; never native C4 evidence |
| 2 | Deterministically derived process evidence | Eligible only as a separate derived arm after code/hash/replay validation |
| 3 | Native checkpoint/process evidence joined to the same sample | Required class for C4 |
| 4 | Level 3 plus genuinely independent validation | Stronger confirmation; not automatic from a second field/prompt |

`INFERENCE`: terminal reward, a field named `step_reward`, a checkpoint-shaped object, or a second judge does not by itself prove native or independent evidence.

`VALUE`: retain `native`, `deterministic_derived`, `judge_derived`, `proxy`, and `unavailable` as orthogonal origin labels; do not collapse provenance into a single usefulness score.

## 6. Adaptation to Stage E-derived supervision

`INFERENCE`: Stage E may identify whether an intermediate representation observes an injection, but visibility must not be relabelled as process correctness.

`VALUE`: any future Stage E-to-Stage D adapter should emit separate fields:

```text
checkpoint_visibility
protocol_detection
operational_harmfulness
evidence_origin
evidence_level
source_revision
artifact_sha256
origin_group
split_role
```

`FACT`: these fields are a proposed contract, not a modification to frozen Stage E JSON or schemas.

`UNVERIFIED`: any claim that visibility predicts correct actions, terminal success, or beneficial distillation.

## 7. Blockers and stop

Stop adaptation if:

- dataset revision, licence, or permitted-use scope is missing;
- native process evidence lacks a stable same-sample join;
- deterministic-derived fields lack input/code/output hashes;
- proxy labels are promoted to native checkpoints;
- judge-derived fields omit judge identity/date outside the record;
- origin groups or split roles are unavailable;
- Stage E visibility is substituted for detection or harmfulness;
- any model, judge, training, GPU, service, database, Phase 2, Stage R, or E-D-R action would be required.

`FACT`: this review executed no dataset-body download, package installation, model/judge call, training, GPU work, service, database, credential, Phase 2, Stage R, or E-D-R action.
