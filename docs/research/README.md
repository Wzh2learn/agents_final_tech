# 科研主线与论文验收入口

> 状态: 活跃 | 更新: 2026-09-23 | 取代/被取代: 不取代受保护路线文档；作为当前执行与验收入口

本文只回答三个问题：小论文在证明什么、大论文如何承接、下一项工作怎样验收。历史实验过程仍保留在 `docs/experiments/`，不在这里重复。

## 1. 权威层级与最短阅读路径

“单一权威”按职责划分，不等于只留一份文件。用户 2026-09-22 的明确校准优先；下表各层不得越权替代其他层。

| 层 | 权威文件 | 管什么、不管什么 |
|---|---|---|
| 导航入口 | 本文件；全仓目录见 `docs/INDEX.md` | 指定阅读顺序与冲突裁定，不另存实验数字真值 |
| 战略/导师政策依据 | `docs/33_导师指导吸收_科研三线升级.md`、`docs/34_专利_小论文_大论文协同研究路线.md` | 两件受保护、只读；导师要求与专利公开边界继续有效，旧小论文范围/排期不覆盖本次校准 |
| 当前论文叙事 | `paper/research_story_v2.md` | 唯一现役故事、RQ 与主张边界；目标贡献不等于结果 |
| 证据与资产账本 | `paper/research_asset_map_v2.md`；评估子稿细账为 `paper/claim_manifest_v1.json` | 区分已成立、机制级、needs-evidence 与历史素材；数字真值仍来自原始工件 |
| 当前执行计划 | `docs/handoff/2026-09-22-paper-research-next-phase.md` | 唯一下一阶段任务顺序、四层数据边界、阶段门与拆稿条件；不得再建平行计划 |
| 成熟评估保底稿 | `paper/teacher_review_draft_v1.md`、`paper/teacher_review_draft_v1.docx` | 仅 Stage E；其主张仍受 `docs/experiments/2026-08-30_phase_a_autopsy_and_claim_set_v2.md` 约束，不定义完整三阶段方向 |
| 数字真值 | `logs/graph/eval/` 下原始 JSON + 对应生成代码/冻结协议 | 原始数字优于文字摘要；历史实验只能支持原协议内的结论，不能反推新实验已经完成 |
| 历史/已取代过程稿 | `docs/30_科研线规划.md`、`docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md`、评估蓝图、旧大论文骨架、多轮审稿与旧任务卡 | 保留追溯/证据价值，不再控制当前方向或排期 |

冲突裁定：论文范围由用户校准及当前叙事覆盖 docs/33、docs/34 中的旧范围；公开限制不被覆盖。执行细节由当前计划覆盖旧任务卡；`docs/experiments/2026-09-22_distillation_mvp_preregistration.md` 是从属于该计划的实验口径合同，当前仍为 `DRAFT_NOT_FROZEN`，不是已授权实验。已执行实验的预注册与原始工件不可被新计划回改；数字不符先审计，不选择更有利的文字版本。审稿记录是问题来源，不自动成为新结论。

**最短必读路径**：`AGENTS.md` → `memory/CORE.md` / `memory/STATE.md` / `memory/THREADS.md` 当前科研线 → 本入口 → `paper/research_story_v2.md` → `paper/research_asset_map_v2.md` → 当前执行计划 §10 第一张任务卡。首次接手再只读 docs/33、docs/34 的政策；只在复核某条结论时打开对应实验工件或评估稿，不必重读全部旧稿。

历史材料不删除，也不能继续参与当前结论竞争；大规模移动、删除、改名须用户另行确认。Word/图是派生展示件，不覆盖 Markdown 权威源；`paper/research_story_v2.docx` 已按当前正文和三阶段表离线重生成，结构/口径检查通过，不等于 Office 视觉验收或可对外发布。

### 1.1 与代码资产和研发协作怎样接上

- 代码在哪里、输入输出和副作用：`docs/architecture/codebase_map.md`；科研证据成熟度仍由资产账本维护，二者不互相替代。
- 研发分工：`docs/17_Graph_Engineering_多层Loop设计.md`；工程路线/历史 backlog：`docs/29_graph_engineering_roadmap.md`。当前未决只在 `memory/THREADS.md`，科研顺序只在现有执行计划。
- 任务卡用 `templates/task_card_template.md`：D 授权 → A 执行 → B 独立验证 → C 独立审计 → D 验收。业务内 `src/agents/` 不承担这套治理角色，脚本在库不等于自动化已安装。
- 本地/GB10 分工以 `docs/governance/2026-09-07_execution_plane_boundary.md` 为准：零端点不等于可在本机创造正式实验事实，Loop B 默认检查也不是零调用。
- 用户说明原始语料、模型和执行环境在另一台服务器，本轮不连接或补齐；本地缺件是未核验依赖，不判作研究失败。下一阶段需该依赖时再按原计划取证。

## 2. 统一科研主线

### 2.1 会议小论文：评估—蒸馏—规则进化

当前目标故事见 `paper/research_story_v2.md`：大模型流程评估 → checkpoint 引导的小模型规则动作蒸馏 → 验证门控的规则自学习与版本化回滚。`research/vgmc_exp1.py` 主要记录动作事件，不是完整推理轨迹，近期只能称“动作策略蒸馏/规则候选蒸馏”。小模型负责候选提出和验证预筛，不替代最终确定性验证门。

| 阶段 | 论文责任 | 当前资产 | 成熟度 |
|---|---|---|---|
| E 大模型流程评估 | 提供经审计的 checkpoint 信号 | 95 表、118 注入、检查点树、可见性与协议审计 | 评估子稿已闭环；不代表动作标签天然正确 |
| D 小模型蒸馏 | 8B 主学生学习规则动作；4B 仅训练链 smoke | 零样本矩阵、文献、60 对单向 DPO 偏好 | 本地 P1 已审、未放行训练；服务器测试与后续实验分别接手/待批 |
| R 自学习规则进化 | 把稳定经验固化为可审计规则 | gain–collateral 门、碰撞/对抗实验、bandit/DPO 工件 | 机制级；独立验证、强基线与功效待补 |

`paper/teacher_review_draft_v1.md` / `paper/teacher_review_draft_v1.docx` 只覆盖 E 阶段，现定位为成熟证据子稿或分拆投稿备选，不再代表完整小论文。

### 2.2 评估子稿：已完成的证据底座

暂定题目：*Discriminability-Aware Evaluation of Long-Horizon Document AI Pipelines via Hierarchical Checkpoints and Defect Visibility Analysis*。

唯一主问题：最终答案正确时，长流程系统的中间缺陷是否仍可能被静默吸收，以及评测协议本身能否发现这种缺陷？

| 研究问题 | 稿件责任 | 当前证据 | 当前结论边界 |
|---|---|---|---|
| SP-RQ1：缺陷在哪一层可见、在哪一层被吸收？ | 主贡献 | 95 表、118 注入、阈值网格和可见性谱 | 只主张受测文档管线；字符扰动危害性依赖等价类定义 |
| SP-RQ2：分层检查点带来什么？ | 主贡献 | 端到端、扁平、层级协议与 matched-FPR 对照 | 当前只证实证据分解；不主张检出率更高，额外定位收益仍待多 leaf 变化场景验证 |
| SP-RQ3：结论是否依赖协议、匹配器和评分口径？ | 严谨性贡献 | 跨匹配器、匹配竞争、judge 校准、种子与敏感性分析 | 第二数据流和第二 scorer 尚未闭合，不外推为普遍定律 |
| SP-RQ4：评测发现能否反馈系统改进？ | 半页机制案例 | VGRM 门拒、规则固化与回归记录 | 不主张 VGRM 显著净收益；PSO 仅报告 null/负面结果 |

**评估子稿**明确不承担：VGRM 显著效果、PSO 优越性、严格“盲锥”理论、RL/DPO/bandit 扩展、任意长流程系统的普遍外推。完整三阶段方向中的 DPO 仍是条件臂，不能由这一历史子稿范围推导为永久取消，也不能预写增益。

### 2.3 研究生大论文：展开三阶段并验证长期闭环

| 创新点 | 核心问题 | 与小论文关系 | 独立验收条件 | 成熟度 |
|---|---|---|---|---|
| TH-I1 判别力感知的分层评测 | 如何以可控成本获得可诊断证据？ | 小论文 SP-RQ2/RQ3 是主体证据 | 强基线、多种子、不确定性、成本口径、第二类长流程 | 中高 |
| TH-I2 缺陷可见性与静默吸收 | 哪些缺陷为何不可见？ | 小论文 SP-RQ1 是主体证据 | 等价类、强度梯度、匹配器边界和跨数据流复现 | 中高 |
| TH-I3 评估引导的小模型动作策略蒸馏 | 如何将可靠规则动作迁移到低成本学生？ | 小论文 D 阶段 | 4B 仅 smoke、8B 主学生、SFT/条件 DPO、四层隔离、未见家族、质量—成本 Pareto | 低，先数据与可学性审计 |
| TH-I4 验证门控的规则自学习 | 如何安全固化并回滚？ | 小论文 R 阶段 | no-gate/gain-only/collateral-only/confidence-only/fixed-dual/gate-validation/rollback 强基线，功效分析 | 中 |

大论文不是把小论文拉长。TH-I1/TH-I2 复用评估底座，TH-I3 扩展多学生/多教师和泛化，TH-I4 扩展长期安全性与学习门。视觉补盲仅作 TH-I2 的条件性实验。

## 3. 论文导向验收体系

任何新测试、脚本或实验必须先绑定当前叙事 `RQ1–RQ4`、评估子稿 `SP-RQ*` 或大论文 `TH-I*`，并写清命名空间；三阶段蒸馏是 RQ2/TH-I3，不能混同评估子稿 SP-RQ2。不能回答论文问题的“全链路通过”只算工程健康检查，不算科研验收。

| 门 | 必须回答 | 通过证据 | 失败时处理 |
|---|---|---|---|
| G0 主张门 | 要支持或证伪哪条主张？ | 冻结 claim、成功/失败判据、禁止修改项 | 无 claim ID 不执行 |
| G1 构念门 | 注入真代表缺陷吗？指标真测到目标吗？ | 等价类审计、正负控、匹配器/评分口径说明 | 降级为边界或无效 mutant，不换标签救结果 |
| G2 数据门 | split、样本、分母和污染边界可靠吗？ | 公开数据卡、固定 hash、无甲方数据、表级聚类口径 | 批次无效，不进入论文 |
| G3 对照与统计门 | 结果能排除简单解释吗？ | 强基线、消融、多种子、CI/效应量、成本 | 收窄主张或保留 null |
| G4 复现门 | 独立环境能重建数字吗？ | 固定命令、环境、种子、输出 hash、数字到工件映射 | 不得写入正文结论 |
| G5 稿件一致性门 | 文字、表图和工件是否同口径？ | claim-evidence 表、术语/分母/数值扫描、独立审稿 0 blocking | 只修稿，不用新实验掩盖矛盾 |
| G6 外部效度门 | 结论能推广到哪里？ | 第二数据流、第二 scorer 或明确限制 | 使用预注册降级表述 |
| G7 公开门 | 可以投稿或公开吗？ | 专利申请状态及权利要求覆盖由用户确认 | 未确认前不外发、不上传 arXiv、不公开核心代码 |

### 验收结果只有四种

- `PASS`：预注册判据满足，可以支持指定 claim。
- `PARTIAL`：只支持收窄后的 claim，必须同时写限制。
- `NULL`：没有预期增益，但实验有效；保留为科研结果。
- `INVALID`：构念、数据、执行或证据链失败；不能进入论文。

“服务启动成功”“pytest 全绿”不能单独得到以上任何科研结论。

## 4. 当前就绪度

### 小论文

- T1/T2/T6 实验与 T7 回填已完成；Algorithm 1 已入稿并有实现对位表。
- 2026-09-21 双模型独立审稿均判定 `REVISE`；随后已完成口径、hinge、算法编号、门控披露等 P0 文本修订。
- 评估子稿已完成干净稿、Related Work、claim—number—artifact 机械验收。
- 完整三阶段小论文的最高价值缺口是蒸馏 MVP；第二数据流/第二 scorer 次于该缺口。
- 完整三阶段稿尚未达到投稿就绪；即使科研验收通过，专利公开状态仍是独立外发硬门。

### 大论文

- TH-I1/TH-I2 已有较完整的小论文证据底座。
- TH-I3 只有训练前矩阵、文献和偏好对，尚无蒸馏结果。
- TH-I4 有机制与探索性证据，强门控基线和功效分析尚未闭合。

## 5. 论文验收基线 v1

目标不是新跑模型，而是把现有科研资产变成可审计、可投稿、可继续扩展的基线。

当前已建立第一版仓内资产：

1. `paper/teacher_review_draft_v1.md`：独立的干净老师审阅稿；原内部稿继续作为证据底稿。
2. `paper/claim_manifest_v1.json`：每条 claim 对应稿件数字、证据、适用范围和降级边界。
3. `research/validate_paper_claims.py`：静态检查章节、证据路径、关键数字和内部注记泄漏。
4. `paper/teacher_review_draft_v1.docx`：老师可直接打开的 Word 审阅版，由 Markdown 离线生成。
5. `paper/teacher_review_readiness_v2.md`：方向校准后的内部送审判定、阻塞项与导师审阅问题。
6. `paper/thesis_manuscript_scaffold_v1.md`：大论文章节、创新点、小论文继承与新增证据边界。
7. `paper/research_story_v2.md`：三阶段统一故事、证据成熟度和最小蒸馏/规则实验闭环。
8. `paper/figures/fig_evaluate_distill_evolve_v1.svg`：三阶段总架构图。
9. `paper/research_story_v2.docx`：当前故事的离线派生件，含同步后的原生三阶段表；结构/口径测试通过，Office 视觉未验。
10. `paper/research_asset_map_v2.md`：评估、蒸馏、规则进化的代码、实验、稿件和缺口索引。
11. `docs/experiments/2026-09-22_distillation_mvp_preregistration.md`：从属于唯一执行计划的 `DRAFT_NOT_FROZEN` 实验口径合同；统一 RQ2–RQ4、数据/模型门、A0–A3、七臂 replay、双公平口径、统计和停止规则。数值参数在用户/导师确认前保持 `UNSET`。
12. `docs/handoff/2026-09-22-paper-research-next-phase.md`：后续 Agent 可直接执行的优先级、数据门、任务卡、合稿/拆稿门与三周排期。
13. `research/phase1a_data_contract.py`：Phase 1a 私有数据补充包的离线、fail-closed 机械预检；通过只表示 `READY_FOR_INDEPENDENT_ACCEPTANCE`，不表示 `DATA_GO`、训练许可或论文结果。合同与 GB10 命令见 `docs/experiments/2026-09-23_phase1a_data_no_go.md`。
14. `research/phase1a_learnability_baselines.py`：独立接收后才可运行的 proposal train/dev 五基线探针；仓内仅有合成合同测试，正式 GB10 开发数字尚未产生。输入回执、预注册配置与运行命令仍只维护在同一 Phase 1a data-gate 报告中。
15. `research/phase2_rule_gate_replay.py` / `research/paper_result_views.py`：共享候选、状态独立的七臂 replay 软件合同及 Table 2 / Figure 4 聚合接口；当前仅有合成测试，正式 Phase 2 未启动，GB10 命令和停止条件只维护在 handoff 的 Phase 2 节。
16. `paper/method_theory_materials_v1.md`：三阶段统一符号、SFT/选择性预测/三门更新公式、两个有限命题与已核验理论文献；是写作素材，不是已成立实验结论。
17. `paper/dataset_protocol_v1.md`：标签质量 × 实验角色二维分层、公开数据选择、模型对照配置与 GB10 数据门；不授权下载、构建、训练或解冻 TAT-DQA。
18. `paper/method_data_references_v1.bib` / `paper/figures/fig_rule_gate_replay_v1.svg`：经官方入口核验的理论与数据 BibTeX，以及共享流、独立状态、三门与回滚的论文方法图；正式稿引用前仍二次核版。

运行：

```bash
python3 research/validate_paper_claims.py
PYTHONPATH=. python3 -m pytest tests/test_paper_claim_acceptance.py -q
.venv/bin/python research/build_teacher_review_docx.py
```

评估子稿原有 G5 静态门已补充语义反向负控；OCR 可见性方向和表格检测信号已修正，两份导师 DOCX 已重生成。P1 本地审计已交付：动作 SFT/风险预筛 DATA_NO_GO，DPO 仅为审计素材的 PILOT_ONLY，均不导出训练数据；依据见资产账本 §3.1。本轮新增仓内补充包合同、五基线探针、七臂 replay 状态机及论文数据接口的合成测试，未生成正式实验数字；GB10 私有包验收和 Office 视觉核对仍未执行，Phase 1a/2 及后续实验等待各自明确批准。近期使用评估保底稿与方向说明，不等训练、不代发；详细停止条件只维护在 `docs/handoff/2026-09-22-paper-research-next-phase.md`。

本批不包含：生产探测、模型调用、TAT-DQA 解冻、D4 执行、专利公开状态判断或对外发送。

## 6. 当前状态边界

### 6.1 2026-09-23 strict closeout status

The 2026-09-22 acceptance stop has now been closed at the evidence boundary. GB10 production is aligned with `origin/main` at `d351d7e`, and a subsequent natural Loop B cycle recorded `git_alignment=PASS`. A-3 is closed at `PASS: 97` (A=76, C=21, missing=0, orphan=0). A-2 remains `SCOPED_PASS`: its four named tests passed with zero forbidden connects in the traced scope, but synthetic fixtures and a missing `injection_map.json` mean no claim about full pytest, production, or future experiment paths is allowed.

Phase 1a is a formal `DATA_NO_GO`, with no baseline result table; Phase 2 formal replay is unstarted even though its repository-only state-machine contract now exists. The data gate, historical-only boundary, missing evidence, and minimum supplement contract are recorded in `docs/experiments/2026-09-23_phase1a_data_no_go.md`. This status is a research decision boundary, not a failed experiment to be erased by reruns. The next permitted entries are data supplementation, repository-only software validation, a newly scoped A-2 expansion, or the Loop C Lead control-plane/governance work; none opens Phase 2 data execution, training, production endpoints, frozen rules, or publication.

A-2's four tested nodes were `test_adv_map_deterministic_nested_wrong_target`, `test_overlay_merge_adds_columns_and_entries`, `test_overlay_none_is_identity`, and `test_real_overlay_artifact_loads`; the traced scope was `4 passed`, rc=0, with zero `connect` syscalls. This is a scoped network statement, not a whole-project guarantee.

### 6.2 Local and remote status boundary (2026-09-23)

Section 6.1 is the earlier `d351d7e` closeout snapshot. At this delivery's clean baseline, local `main`, `origin/main`, and the working branch `test/compaction-guard-abort` were aligned at `061d881`; pre-delivery `origin/test/compaction-guard-abort` was `0aee20d`, and the repository-only contract is published on that test branch. GB10 was last observed at `e5ab809`, but its current production/worktree state, Loop B cycle, processes, and Loop C Lead queue are **unverified** because the last bounded SSH attempt timed out. The closeout audit remains `INCONCLUSIVE`; Phase 1a remains `DATA_NO_GO`, and Phase 2 has not started.

The repository-only Phase 1a supplement precheck, simple-baseline runner, Phase 2 seven-arm replay state machine, and paper-view adapter are now implemented with synthetic contract tests. They create no experimental result: GB10 must later run the fixed offline acceptance procedure against a read-only private package, obtain independent manual review, and receive separate authorization for each development/replay step before any metric exists. See the dated state in `memory/STATE.md`, §13 and Phase 2 of the handoff, and the data-gate report.

## 7. 常用入口

- 当前内部稿：`paper/draft_v0_s1_s2_s6.md`
- 老师审阅稿：`paper/teacher_review_draft_v1.md`
- 老师审阅 Word：`paper/teacher_review_draft_v1.docx`
- 方向校准说明：`paper/teacher_review_note_v2.md`
- 内部送审验收：`paper/teacher_review_readiness_v2.md`
- 三阶段总叙事：`paper/research_story_v2.md`
- 三阶段方向 Word：`paper/research_story_v2.docx`
- 三阶段架构图：`paper/figures/fig_evaluate_distill_evolve_v1.svg`
- 三阶段资产地图：`paper/research_asset_map_v2.md`
- 大论文稿件骨架：`paper/thesis_manuscript_scaffold_v1.md`
- Claim manifest：`paper/claim_manifest_v1.json`
- 小论文蓝图：`docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md`
- 冻结 Claim Set v2：`docs/experiments/2026-08-30_phase_a_autopsy_and_claim_set_v2.md`
- 最新双模型审稿：`docs/experiments/2026-09-21_loopc_review_diff_table.md`
- Algorithm 1 对位：`docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md`
- 大论文旧骨架（仅作素材）：`docs/experiments/2026-08-26_thesis_narrative_skeleton.md`
- 专利与论文协同路线：`docs/34_专利_小论文_大论文协同研究路线.md`
