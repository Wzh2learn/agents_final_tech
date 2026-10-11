# Current Status Reconciliation Proposal

> 状态: `PROPOSAL_ONLY / NOT_APPLIED / READ_ONLY_RECONCILIATION`
> 日期: 2026-10-09
> 禁止: 不删除历史记录，不修改冻结实验件，不触碰 GB10 脏文件。README/STATE 的修改仅在本文件给出 patch proposal，尚未应用。

## 1. 当前权威文件

进入项目或准备导师材料时，建议按以下顺序读取：

1. `AGENTS.md`：权限、执行面和冻结红线。
2. `memory/CORE.md`：长期架构、运行拓扑和历史基线。
3. `memory/STATE.md`：当前现役状态。
4. `memory/THREADS.md`：未决决策、阻塞和外部输入。
5. `side_handoff.md`：本轮/下一轮交接入口。

科研讨论需要打开证据时，再读：

- `docs/research/README.md`：科研路线入口；
- `docs/experiments/2026-10-05_formal_negative_path_b_completion_audit.md`：当前 Path B 完成口径；
- `paper/teacher_review_readiness_v2.md` 与 `paper/claim_manifest_v1.json`：Stage E claim boundary。

## 2. 含 stale statement 的旧文件

| 文件/段落 | stale statement | 建议标记 | 处理意见 |
|---|---|---|---|
| `docs/experiments/2026-10-05_goal_requirement_completion_audit_current.md` | `NOT_COMPLETE_FOR_FULL_GOAL`、`SCIENTIFIC_CLOSURE_PENDING_EXTERNAL_DATA_INPUT` | `historical snapshot / superseded for current Path B` | 保留原文；在头部注明它对应 stricter confirmatory-only 解释，当前结论以 formal negative path B audit 为准 |
| `docs/experiments/2026-10-05_internal_deliverable_completion_audit.md` | `GOAL_REMAINS_ACTIVE` | `historical snapshot / superseded for current Path B` | 保留原文；不删除历史判断，只加当前 override 指针 |
| `docs/research/README.md` §6.1-6.2 | `INCONCLUSIVE`、旧 GB10 head、Phase 1a 旧状态 | `historical snapshot` | 明确这些是 2026-09-23 快照，不参与当前状态竞争 |
| `docs/research/README.md` §6.3 | `SOURCE_GO is now evidenced`；licence `permitted_uses` 包含 `training` | `still valid as historical D-B metadata; not current authorization` | 必须补一句：不等于 `DATA_GO / MODEL_GO / TRAINING_GO`，不解除 `DATA_NO_GO` |
| `docs/research/README.md` Q3 旧句 | “raw expert outputs and hashes are still pending seal” | `superseded` | 当前是 raw package sealed with visibility exceptions；R2/ADJ signed visibility receipt 仍不完整，Q3 仍为 exploratory |
| `docs/research/README.md` §7.1 | `Goal remains ACTIVE` | `superseded` | 当前为 `COMPLETE_FOR_FORMAL_NEGATIVE_PATH_B`，不是 E-D-R 全闭环完成 |
| `docs/research/README.md` model sync 旧附记 | Qwen3-8B 未下载 | `superseded by later addendum` | 保留时间线，当前只承认 artifact readiness，不承认 MODEL_GO/TRAINING_GO |
| `memory/THREADS.md` 早期条目 | `Goal ACTIVE`、Q3 raw missing、`peft/trl/deepspeed absent` | `historical snapshot / superseded where later evidence exists` | 不删除历史条目；阅读时只取顶部/后续条目作为当前状态 |
| `memory/STATE.md` Git/GB10 dirty-list 段 | 旧的 fixed-five 清单和现场 dirty 集合不一致 | `superseded for runtime snapshot` | 仅提出 patch proposal，当前不改 STATE |
| `docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md` | 旧 T1-T8、PSO/第二数据流执行顺序 | `historical snapshot` | 保留作历史计划，不作为当前执行顺序 |

## 3. 建议 patch proposal（未应用）

### `docs/research/README.md`

在文件顶部增加一个 current override block：

```text
Current override (2026-10-09): the current scientific status is
COMPLETE_FOR_FORMAL_NEGATIVE_PATH_B with FORMAL_NEGATIVE_BOUNDARY /
DATA_NO_GO / RQ2 NOT_IDENTIFIED. Historical sections below retain their
original dates and are not current authorization. Q3, B0-B4, and Track B
remain exploratory evidence.
```

### `memory/STATE.md`

只替换 GB10 dirty-file snapshot 段为现场清单：

```text
GB10 current dirty files (2026-10-08 23:20:55 +0800 read-only status):
config/schema_suggestions.json
logs/graph/dispatch_log.md
logs/graph/docs_lint_report.json
logs/graph/governance_drift_latest.md
logs/graph/loop_b_last_status
logs/graph/verify-report.json
```

现场冲突说明：用户给定保护集为 5 个文件且明确要求不修改；只读复查又观察到 `logs/graph/loop_b_last_status` 从 `FAIL` 变为 `PASS`，因此当前共有 6 个 dirty 文件。本轮未触碰任何一项；后续应把 6 个文件全部视为只读保护，直至用户裁定。

## 4. 建议的 3-5 个入口文件

日常进入项目固定读：

1. `AGENTS.md`
2. `memory/STATE.md`
3. `memory/THREADS.md`
4. `side_handoff.md`
5. `docs/experiments/2026-10-05_formal_negative_path_b_completion_audit.md`

`memory/CORE.md` 和 `docs/research/README.md` 作为需要架构或科研路线时的第二层入口。

## 5. 不应做的事

- 不把历史 audit 的 `ACTIVE` 或 `NOT_COMPLETE_FOR_FULL_GOAL` 当作当前结论。
- 不把 `SOURCE_GO`、licence permitted uses、Q3 exploratory 或 Track B payload PASS 升格为 DATA_GO / MODEL_GO / TRAINING_GO。
- 不删除旧文档，不重写冻结实验件，不修改 GB10 当前脏文件。
- 不把本 proposal 当成 README/STATE 已经更新的证明。
