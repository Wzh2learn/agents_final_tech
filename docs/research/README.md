# 科研主线与论文验收入口

> 状态: 活跃 | 更新: 2026-10-12 | 取代/被取代: 研究边界以治理基线v1为准，架构v3/蓝图v1按职责维护；受保护政策、历史证据与运行权限不变

本文只回答三个问题：小论文在证明什么、大论文如何承接、下一项工作怎样验收。历史实验过程仍保留在 `docs/experiments/`，不在这里重复。

**执行侧最新状态：** [EXECUTION_HANDOFF_STATUS_v1](EXECUTION_HANDOFF_STATUS_v1.md)。战略治理结束；后续仅 Paper E 的 WP-E 投稿修订流程和大论文 WP-0 只读资格核验。本轮仅交接并停止，未执行改稿/实现/实验；各 gate 与科学范围不变。

**2026-10-12 最终研究交接：** Paper E 先读 [投稿门禁](PAPER_E_SUBMISSION_READINESS_GATE_v1.md)，当前科学纠偏未执行、不可按现稿投稿；硕士工作先读 [执行入口](MASTER_RESEARCH_EXECUTION_ENTRY_v1.md)，下一步仍是 WP-0 只读材料核验；repo/harness 边界见 [治理收尾](REPO_GOVERNANCE_FINAL_v1.md)。这三份文件只收敛入口，不授权改稿、实现或实验。

**科学基线不变：** [治理基线v1](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md) → [架构v3](THESIS_RESEARCH_ARCHITECTURE_v3.md) → [蓝图v1](THESIS_EXECUTION_BLUEPRINT_v1.md)。RQ2 为待验证假设，G-RQ/G-M 均 PENDING、方法创新未识别；Paper E 只提供测量约束。[历史快照](history/2026-10-12_pre_governance/README.md) 保留原始字节。本文 §4–§6 及末尾旧日期记录不控制当前路线、投稿资格或运行许可。

**WP-0 设计入口：** [最小科学验证任务卡](thesis_experience_v1_task_card.md) 已记录最小问题、四臂识别边界、停止条件和 WP-0/WP-1 责任。`DESIGN_COMPLETE / QUALIFICATION_PENDING / EXPERIMENT_NOT_RUN`；确切来源、许可与经验仍未核验，G-RQ/G-M 不升级。下一步仍是同卡只读材料资格核验，不是 WP-1 实现或 WP-2 运行。

## 1. 权威层级与最短阅读路径

“单一权威”按职责划分，不等于只留一份文件。用户最新明确指令优先；2026-10-12 更新仅改变未来规划，下表各层不得越权替代其他层。

| 层 | 权威文件 | 管什么、不管什么 |
|---|---|---|
| 导航入口 | 本文件；全仓目录见 `docs/INDEX.md` | 指定阅读顺序与冲突裁定，不另存实验数字真值 |
| 战略/导师政策依据 | `docs/33_导师指导吸收_科研三线升级.md`、`docs/34_专利_小论文_大论文协同研究路线.md` | 两件受保护、只读；导师要求与专利公开边界继续有效，旧小论文范围/排期不覆盖本次校准 |
| Stage E 当前小论文 | `paper/saner_rene_manuscript_v1.md`、`paper/saner_rene_claim_matrix_v1.json`；`SANER_SCIENTIFIC_ADJUDICATION_v1.md` | canonical SANER 稿与作者级纠偏边界；纠偏未执行，不含Agent学习结果。旧teacher draft不覆盖当前SANER稿 |
| 证据与资产账本 | `paper/research_asset_map_v2.md`；原始工件；当前SANER矩阵与科学裁决 | 区分已成立、机制级与历史素材；旧解释与裁决冲突时不继承旧推断，数字真值仍来自原始工件 |
| 当前研究边界与推进裁决 | `THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md` | RQ2假设与创新边界、已有工作风险、G-RQ/G-M允许范围、禁止事项；不授权实验或认证方法 |
| Paper E 当前投稿资格 | `PAPER_E_SUBMISSION_READINESS_GATE_v1.md` | 科学纠偏待执行，当前不可按现稿外发；旧编译/机械PASS不覆盖作者级裁决 |
| 硕士当前执行路由 | `MASTER_RESEARCH_EXECUTION_ENTRY_v1.md` | Paper E继承边界、已验证/待验证/探索对象与Loop A/D入口；不增加路线 |
| 本轮repo/harness交接边界 | `REPO_GOVERNANCE_FINAL_v1.md` | 资产保留、路线冻结和局部文档收尾；不认证全库/远端/清场完成 |
| 当前未来执行规划 | `THESIS_EXECUTION_BLUEPRINT_v1.md` | 未授权的12个月工作包、首验参数和探索性资源门；服从治理基线，不重定义科学推进门；旧09-22计划不控制新序列 |
| WP-0 当前设计任务卡 | `thesis_experience_v1_task_card.md` | 细化最小验证与WP-0/WP-1；只完成设计，材料资格待核验，不覆盖基线/蓝图或签发许可 |
| 长期研究叙事 | `THESIS_RESEARCH_ARCHITECTURE_v3.md` | 三个TH3-RQ与Evaluation→Evidence→Learning→Adaptation；旧research_story_v2/EDR保留历史，不强制完成 |
| 数字真值 | `logs/graph/eval/` 下原始 JSON + 对应生成代码/冻结协议 | 原始数字优于文字摘要；历史实验只能支持原协议内的结论，不能反推新实验已经完成 |
| 历史/已取代过程稿 | `docs/30_科研线规划.md`、`docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md`、评估蓝图、旧大论文骨架、多轮审稿与旧任务卡 | 保留追溯/证据价值，不再控制当前方向或排期 |

冲突裁定：新规划取代旧未来路线和排期，不改变 docs/33、docs/34 的受保护原文或公开限制。旧预注册、DATA_NO_GO/RQ2 NOT_IDENTIFIED及闭线继续在旧命名空间有效；TH3-RQ不继承旧许可，也不回改原始工件。审稿记录是问题来源，不自动成为新结论。当前模型、训练、服务与数据运行仍需具体任务授权。

**最短必读路径**：`AGENTS.md` → `memory/CORE.md` / `memory/STATE.md` / `memory/THREADS.md` 相关当前条目 → 本入口 → 治理基线 → 架构v3相关RQ → 蓝图当前工作包。Paper E任务另读科学裁决与canonical稿；其余原始材料按问题加载，不重读全部旧稿。首次接手按需只读 docs/33、docs/34 的政策。

历史材料不删除，也不能继续参与当前结论竞争；大规模移动、删除、改名须用户另行确认。Word/图是派生展示件，不覆盖 Markdown 权威源；`paper/research_story_v2.docx` 已按当前正文和三阶段表离线重生成，结构/口径检查通过，不等于 Office 视觉验收或可对外发布。

### 1.1 与代码资产和研发协作怎样接上

- 代码在哪里、输入输出和副作用：`docs/architecture/codebase_map.md`；科研证据成熟度仍由资产账本维护，二者不互相替代。
- 研发分工：`docs/17_Graph_Engineering_多层Loop设计.md`；工程路线/历史 backlog：`docs/29_graph_engineering_roadmap.md`。当前未决只在 `memory/THREADS.md`，新科研顺序只在执行蓝图。
- 任务卡用 `templates/task_card_template.md`：D 授权 → A 执行 → B 独立验证 → C 独立审计 → D 验收。业务内 `src/agents/` 不承担这套治理角色，脚本在库不等于自动化已安装。
- 本地/GB10 分工以 `docs/governance/2026-09-07_execution_plane_boundary.md` 为准：零端点不等于可在本机创造正式实验事实，Loop B 默认检查也不是零调用。
- 原始语料、模型和执行环境在另一台服务器，本轮不连接或补齐；本地缺件是未核验依赖，不判作研究失败。后续按当前工作包和具体许可取证。

## 2. 统一科研主线

### 2.1 大论文当前规划：三个问题，一项核心学习研究

推荐工作题目《面向智能体的证据引导经验学习与持续适应研究》。保留Evaluation→Evidence→Learning→Adaptation作为科学依赖，不要求四模块、三阶段EDR或多篇对称论文。

| 新命名空间 | 职责 | 当前状态 |
|---|---|---|
| TH3-RQ1 | 候选反馈的事实支持、测量对象与使用条件；不证明未来效用 | E只提供测量约束、纠偏待执行；新任务QUALIFICATION_PENDING |
| TH3-RQ2 | 检验反馈能否改善未来行为与结果；Memory/SFT是研究对象 | 待验证假设，METHOD_NOVELTY=NOT_IDENTIFIED，NOT_RUN |
| TH3-RQ3 | 存活机制的有限适应收益、错误传播、遗忘与成本 | 条件性边界检验，不预设创新，NOT_RUN |

下一项只读工作是 WP-0 的 G-RQ/G-M 与任务资格核验；首个拟议模型实验仍是经验复用pilot。两门对相应范围的裁决、最小验证必要性及具体许可成立后才可实施。旧D/R协议、4B/8B顺序与DATA_NO_GO保持历史身份，不绑定新实现。

### 2.2 Stage E 小论文：当前正式内部投稿路线

canonical稿与矩阵见上表；最终题目与claim尚待落实科学裁决并由作者签署，本入口不另定稿。Paper E保留受限measurement-validity audit，不支持通用Agent/long-horizon或学习收益。

收尾重点：C2结构等价与部署规则拆开、non-direct部分信息、OCR非响应与harm分开、异质5/8、FinQA结果字段未重算及availability。具体修改原则只在科学裁决维护；本轮不改稿、不改冻结数字。

### 2.3 大论文与论文出口

Paper E作为受限测量基础经验章；核心学习论文是争取的出口，方法贡献取决于必要性、具体差异与独立效果证据，有限适应按存活机制开展。第二篇扩展不是硕士毕业前置。博士沿经验进入记忆/参数及失效纠正深化，不补救尚未成立的硕士方法。平台是复现支持，不另计科学贡献。

## 3. 论文导向验收体系

下表保留通用检查目录，不另立 TH3 推进门。当前研究问题与方法必要性裁决以治理基线 G-RQ/G-M 为准，具体分析以当前任务卡为准；不能从下表机械增加新数据流、训练、全量测试或运行预算。公开政策继续遵守受保护原文与具体许可。

任何新测试、脚本或实验必须绑定当前SANER claim、`TH3-RQ1/2/3`或明确的历史命名空间；旧TH-I/SP-RQ/Phase状态不自动迁移。新工作包是否获准、是否只到软件/资格/探索或确认级分别验收。不能回答论文问题的“全链路通过”只算工程健康检查，不算科研验收。

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

### 科研结论与执行状态分开

- `PASS`：预注册判据满足，可以支持指定 claim。
- `PARTIAL`：只支持收窄后的 claim，必须同时写限制。
- `NULL`：没有预期增益，但实验有效；保留为科研结果。
- `INVALID`：构念、数据、执行或证据链失败；不能进入论文。

新蓝图另报 `NOT_RUN / NOT_AUTHORIZED / NOT_EVALUABLE / UNDETERMINED` 等执行或未定状态，不能强塞进上述已完成结果分类。探索性继续门不是确认性PASS；宽区间未见增量不证明零效应。

“服务启动成功”“pytest 全绿”不能单独得到以上任何科研结论。

## 4. 历史就绪度快照（不控制新路线）

### 小论文

- 当前正式路线是 Stage E 内部投稿版 `paper/teacher_review_draft_v1.md` / `.docx`，身份为 evaluation-protocol measurement-validity / meta-evaluation。
- Stage E 已完成干净稿、Related Work、limitations、reproducibility 和 claim-evidence 机械验收；当前状态是 `ready for advisor review`。
- Office/PDF visual check PASS；claims `74/74`、submission `10/10`。这些是内部投稿范围验收，不是正式投稿完成。
- 外部投稿仍受专利、venue、作者/单位、匿名模板和 camera-ready 门控制；不上传 arXiv、不公开代码、不外发。
### 大论文

- TH-I1/TH-I2 已有较完整的小论文证据底座。
- TH-I3 只有训练前矩阵、文献和偏好对，尚无蒸馏结果。2026-09-25 实测进一步定位了其数据路径：在已批准来源范围内**没有单一命名空间可承载 Phase 1a 动作包**，且 250-500 有效 UID 的补充目标对 schema-matching 表对类来源不可达（K = 表对数，实测 K=10）。详见 §6.3。
- TH-I4 有机制与探索性证据，强门控基线和功效分析尚未闭合。

## 5. 历史论文验收基线 v1

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
16. `paper/method_theory_materials_v1.md`：三阶段统一符号、SFT/选择性预测/三门更新公式、有限样本风险上界、两个有限命题及最近邻差异；是写作素材，不是已成立实验结论。
17. `paper/dataset_protocol_v1.md`：标签质量 × 实验角色二维分层、过程/动作双来源选择、模型对照配置与 GB10 数据门；不授权下载、构建、训练或解冻 TAT-DQA。
18. `docs/datasets/paper-public-source-registry-v1.json`：10 个公开来源的 metadata-only 可机读快照，记录核验 commit、许可缺口、independence-cluster namespace、角色适配和准入状态；namespace 不是可直接写入样本 manifest 的粗粒度簇，全部 `download_approved=false`。
19. `paper/method_data_references_v1.bib` / `paper/figures/fig_rule_gate_replay_v1.svg`：经官方入口核验的理论与数据 BibTeX，以及共享流、独立状态、三门与回滚的论文方法图；正式稿引用前仍二次核版。
20. `docs/datasets/phase1a_licence_record_v1.json`：D-B 正式 licence_record；`accepted_by=Wzh`、`permitted_uses` 仅四项、covered hashes 仅限 D-B annex 三件。它是许可接受记录，不是 package-wide 授权，也不解除 `DATA_NO_GO`。

运行：

```bash
python3 research/validate_paper_claims.py
PYTHONPATH=. python3 -m pytest tests/test_paper_claim_acceptance.py -q
.venv/bin/python research/build_teacher_review_docx.py
```

Stage E 旧评估稿的 G5 静态门已补充语义反向负控；OCR 可见性方向和表格检测信号已修正，两份导师 DOCX 已重生成。P1 本地审计已交付：动作 SFT/风险预筛 DATA_NO_GO，DPO 仅为审计素材的 PILOT_ONLY，均不导出训练数据；依据见资产账本 §3.1。本轮新增仓内补充包合同、五基线探针、七臂 replay 状态机及论文数据接口的合成测试，未生成正式实验数字；Office 视觉核对已完成并 PASS；GB10 私有包验收仍未执行，Phase 1a/2 及后续实验等待各自明确批准。当前使用 Stage E 内部投稿版和长期方向说明，不等训练、不代发；详细停止条件只维护在 `docs/handoff/2026-09-22-paper-research-next-phase.md`。

本批不包含：生产探测、模型调用、TAT-DQA 解冻、D4 执行、专利公开状态判断或对外发送。

## 6. 历史状态边界（按日期读取）

### 6.1 2026-09-23 strict closeout status

The 2026-09-22 acceptance stop has now been closed at the evidence boundary. GB10 production is aligned with `origin/main` at `d351d7e`, and a subsequent natural Loop B cycle recorded `git_alignment=PASS`. A-3 is closed at `PASS: 97` (A=76, C=21, missing=0, orphan=0). A-2 remains `SCOPED_PASS`: its four named tests passed with zero forbidden connects in the traced scope, but synthetic fixtures and a missing `injection_map.json` mean no claim about full pytest, production, or future experiment paths is allowed.

Phase 1a is a formal `DATA_NO_GO`, with no baseline result table; Phase 2 formal replay is unstarted even though its repository-only state-machine contract now exists. The data gate, historical-only boundary, missing evidence, and minimum supplement contract are recorded in `docs/experiments/2026-09-23_phase1a_data_no_go.md`. This status is a research decision boundary, not a failed experiment to be erased by reruns. The next permitted entries are data supplementation, repository-only software validation, a newly scoped A-2 expansion, or the Loop C Lead control-plane/governance work; none opens Phase 2 data execution, training, production endpoints, frozen rules, or publication.

A-2's four tested nodes were `test_adv_map_deterministic_nested_wrong_target`, `test_overlay_merge_adds_columns_and_entries`, `test_overlay_none_is_identity`, and `test_real_overlay_artifact_loads`; the traced scope was `4 passed`, rc=0, with zero `connect` syscalls. This is a scoped network statement, not a whole-project guarantee.

### 6.2 Local and remote status boundary (2026-09-23)

Section 6.1 is the earlier `d351d7e` closeout snapshot. At this delivery's clean baseline, local `main`, `origin/main`, and the working branch `test/compaction-guard-abort` were aligned at `061d881`; pre-delivery `origin/test/compaction-guard-abort` was `0aee20d`, and the repository-only contract is published on that test branch. GB10 was last observed at `e5ab809`, but its current production/worktree state, Loop B cycle, processes, and Loop C Lead queue are **unverified** because the last bounded SSH attempt timed out. The closeout audit remains `INCONCLUSIVE`; Phase 1a remains `DATA_NO_GO`, and Phase 2 has not started.

The repository-only Phase 1a supplement precheck, simple-baseline runner, Phase 2 seven-arm replay state machine, and paper-view adapter are now implemented with synthetic contract tests. They create no experimental result: GB10 must later run the fixed offline acceptance procedure against a read-only private package, obtain independent manual review, and receive separate authorization for each development/replay step before any metric exists. See the dated state in `memory/STATE.md`, §13 and Phase 2 of the handoff, and the data-gate report.

### 6.3 Data-path boundary measured after the approved public-source download (2026-09-25)

SOURCE_GO is now evidenced for the D-C approved minimal scope (FinQA `train.json` / `dev.json`; Valentine 10 NYC pairs + LICENSE + bench.py), staged outside the repository on GB10 with per-file sha256 recorded in `docs/experiments/2026-09-25_source_go_p1p2_staging.md`. No data body entered Git.

The D-B licence acceptance is now formalized at `docs/datasets/phase1a_licence_record_v1.json` (accepted_by=`Wzh`, accepted_at generated on GB10, permitted_uses limited to `training`, `tuning`, `evaluation`, `rule_acceptance`). Its covered hashes are limited to the D-B annex artifacts (FinQA LICENSE, FinQA README, Valentine LICENSE); this is not a package-wide licence binding and does not lift `DATA_NO_GO`. No new download is authorized.

A deterministic, label-blind split instrument (`research/phase1a_split_assign.py`, 15 contract tests green on GB10) was then run read-only over that staging. It measured a boundary that changes how the RQ2/RQ3 data path must be described: within the approved scope **no single namespace can carry the Phase 1a action package**. Valentine supplies genuine action-label material (146 source columns over 10 pairs; source-side `matches` 77, `ambiguous_scenarios` 10, `false_positive_scenarios` 0, so `skip` has no mechanical seed) but only 10 origin clusters and 10 lineage UIDs: threshold bucketing leaves `proposal_train.dev` at zero clusters while the contract requires four non-empty partitions, and K=10 sits 25-50x below the 250-500 UID supplement target. That shortfall is bounded by the number of table pairs, not by annotation effort, because one pair is one lineage root and therefore one UID. The source registry and `paper/dataset_protocol_v1.md` §4.1 additionally confine this source to `PILOT_ONLY` proposal/dev. FinQA fills four layers comfortably (M=8 gives 856 samples / 286 UIDs / 88 clusters, inside the target band) but its audited schema role is entry-level and the registry records `action_label_fit = PROGRAMS_ARE_NOT_MAP_HOLD_SKIP_LABELS`; forcing its nine entry-level fields to serve as `canonical_fields` makes every real header unmappable, so `gold_action` collapses to all-`skip` and an always-skip rule scores `action_macro_f1 = 1.0` with `harmful_map_rate = 0`.

Consequently the same-sample bridge required by §4.1 (checkpoint evidence + Q3 action/target + Q3 outcome on one sample) does not exist in the approved scope, RQ2 stays `NOT_IDENTIFIED`, and `DATA_NO_GO` is not lifted by this work. Full measurements, the four walls W1-W4, and the resolved rulings G-A..G-E are in `docs/datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md` §12. G-A/G-B/G-C are not approved, G-E preserves `DATA_NO_GO` / `NOT_IDENTIFIED`, and V2-3 closes the FinQA step-level route. The exploratory Q3 review of the 146 Valentine source columns has now been reported as completed by three independent experts (R1/R2/ADJ): 146/146 adjudicated labels, 119/146 action exact agreement, and 41/41 target exact agreement on shared `map_to` decisions. Raw expert outputs and hashes are still pending seal, so this remains a user-confirmed exploratory summary rather than a complete artifact audit. It cannot support Stage D closure, RQ2 confirmation, `DATA_GO`, or training evidence.
The licence_record status above is an accepted D-B metadata record only. It does not supply missing label_ledger, schema, confidence_manifest, analysis_plan, parser_contract_receipt, or learnability_feature_ledger roles, and it does not authorize any additional data source or use.

### 6.4 Step-level checkpoint line executed, then stopped by its own pre-registration (2026-09-25)

The FinQA branch named in §6.3 was carried through rather than left as a plan: a step-level fault-injection corpus was frozen before any detector existed (1 970 records, sha `03cf47c3…`, double-run byte-identical), a deterministic re-execution scorer was written against a committed pre-registration, and both were run. Under the v1 percent convention `interpretation_fidelity` was 0.16345. v2 pre-registered a second reading and reported both, giving 0.16345 (`mantissa_direct`) and 0.23706 (`mantissa_scaled`); percent-form step fidelity was **0.0298** and **0.2233**. The stop condition frozen in advance — both readings below 0.5 means stop, and no v3 convention hunting — is therefore **triggered**. V2-3 subsequently closed this route: no official-operator application, no v3 convention, and no alternate reading may reopen it. The result remains a pre-registered negative boundary.

What survives is the methodology plus a clean negative result: a corpus frozen before the detector, a scorer that refuses to publish metrics without a committed spec and that embeds the spec's own sha256, a runtime guard proving v2 reproduces every v1 number under the original reading, and a stop condition that actually fired instead of being relaxed. Num-form step fidelity is 0.8304 under both readings, so the residual 518/3 096 mismatch is unexplained and deliberately left unattributed — explaining it would require the official operator semantics this line is no longer permitted to chase. Detection and localization figures (detection 0.99068 / 0.99358, root-cause localization 1.0) are conditional on the clean-faithful subset, i.e. 16-24% coverage, and must never be quoted as "step-level checkpoint detection works on FinQA". Details and hashes: `docs/experiments/2026-09-25_step_checkpoint_score_v2_results.md`.

## 7. 常用入口

- 当前研究边界：[治理基线v1](THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md)；研究范围：[架构v3](THESIS_RESEARCH_ARCHITECTURE_v3.md)；后续工作：[执行蓝图v1](THESIS_EXECUTION_BLUEPRINT_v1.md)。
- 当前SANER稿：`paper/saner_rene_manuscript_v1.md`；claim：`paper/saner_rene_claim_matrix_v1.json`；科学纠偏：[裁决v1](SANER_SCIENTIFIC_ADJUDICATION_v1.md)。

### 7.1 历史状态注记与材料入口（不控制当前路线）
2026-10-03 historical snapshot: at that time GB10 was verified, while `DATA_NO_GO`, RQ2 `NOT_IDENTIFIED`, V2-3 closure, the assembled-but-unreviewed Q3 package, and unrotated/unready token status were current. The 2026-10-04 addendum below supersedes only the Q3 review status.

2026-10-04 Q3 addendum：三位独立专家的 raw package 已封存，corrected ledger 为 `map_to=51 / skip=58 / hold=37`；旧 `52/58/36` 仅是 pre-correction 分布。R1/R2 exact agreement 119/146（81.51%），action κ≈0.727，共同 `map_to` 的 target 41/41，唯一 correction 为 line 61 `map_to|pap_curb_sec -> hold|null`。Q3 仍是 exploratory learnability evidence，不解除 `DATA_NO_GO / NOT_IDENTIFIED`。B5 保持 dormant / `NOT_RUN`。

2026-10-05 model sync addendum：官方 `huggingface.co:443` 路径仍被网络阻塞。Qwen3-4B revision `1cfa9a72...` 已通过批准的 `hf-mirror.com` fallback 同步到 `/home/testuser/wzh/models/hf/Qwen3-4B`，使用 `token=false` 与 `HF_HUB_DISABLE_XET=1`；13 个顶层文件、3 个权重分片、398 个 index 条目、Apache-2.0 licence、镜像 `X-Repo-Commit` 和 manifest 已验证。状态 `READY_FOR_ARTIFACT_VALIDATION`；Qwen3-8B 仍未下载。此状态不授权模型加载、S0、A0-A3、Phase 2 或训练。

2026-10-05 GB10 artifact validation addendum：Qwen3-4B 已在 GB10 完成真实 artifact validation，状态 `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`。13/13 immutable identity、3 个 safetensors header、398 个 tensor、tokenizer/licence、model-root-relative clean/full manifests 均通过；receipt 为 `docs/datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json`。本机 synthetic 测试只记 `DEV_ONLY / NON_AUTHORITATIVE`。readiness 为 `PASS_DRY_RUN_ONLY`，`smoke_model_revision_ready=true`，但 Qwen3-8B 未下载，`model_revision_ready=false`。S0/A0-A2 仅在两模型与全部科学/安全门通过后按条件式授权自动执行；当前仍不运行。

2026-10-05 Qwen3-8B sync/validation addendum：Qwen3-8B revision `b968826d...` 已通过 `hf-mirror.com` fallback 完成精确 15 文件同步与 GB10 真实 artifact validation。15/15 immutable identity、5 shard headers、399 tensors、tokenizer/licence、relative manifests 全过；见 `docs/experiments/2026-10-05_qwen3_8b_model_sync_and_validation.md`。readiness 现为 `model_revision_ready=true`，但科学门、stable Stage D residual 与训练窗口未全部满足，S0/A0-A2 仍不运行。

- 历史内部稿：`paper/draft_v0_s1_s2_s6.md`
- 老师审阅稿：`paper/teacher_review_draft_v1.md`
- 老师审阅 Word：`paper/teacher_review_draft_v1.docx`
- 方向校准说明：`paper/teacher_review_note_v2.md`
- 内部送审验收：`paper/teacher_review_readiness_v2.md`
- 旧三阶段总叙事：`paper/research_story_v2.md`
- 三阶段方向 Word：`paper/research_story_v2.docx`
- 三阶段架构图：`paper/figures/fig_evaluate_distill_evolve_v1.svg`
- 三阶段资产地图：`paper/research_asset_map_v2.md`
- 大论文稿件骨架：`paper/thesis_manuscript_scaffold_v1.md`
- Claim manifest：`paper/claim_manifest_v1.json`
- 小论文蓝图：`docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md`
- 冻结 Claim Set v2：`docs/experiments/2026-08-30_phase_a_autopsy_and_claim_set_v2.md`
- 历史双模型审稿：`docs/experiments/2026-09-21_loopc_review_diff_table.md`
- Algorithm 1 对位：`docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md`
- 大论文旧骨架（仅作素材）：`docs/experiments/2026-08-26_thesis_narrative_skeleton.md`
- 专利与论文协同路线：`docs/34_专利_小论文_大论文协同研究路线.md`

## 2026-10-04 boundary clarification

The Q3 result is a user-confirmed exploratory summary, not raw artifact closure. Raw R1/R2/ADJ outputs, final ledger, expert visibility receipt, and output manifest/hash are MISSING. The three invalid DSNY action references are audited but undecided. B0-B4 has a draft group-aware exploratory split protocol only; the frozen runner is not run because proposal_train.dev=0. B5 is an unverified offline candidate and is not installed or run. Goal remains ACTIVE; RQ2 NOT_IDENTIFIED / DATA_NO_GO and all Stage R/RQ4/training/release boundaries remain.

## 2026-10-04 ruling update

Raw originals now have a GB10 delivery target. Invalid references use quarantine as primary and whole-pair INVALID as mandatory sensitivity. B0-B4 uses LOO primary and salted split sensitivity with exploratory bootstrap only. B5 remains dormant. All execution gates remain closed.

## 2026-10-04 B0-B4 exploratory v2

The sealed corrected Q3 ledger and gold-free process views now support a frozen exploratory B0-B4 probe. B4 is the strongest primary action baseline and the baseline future student work must beat, but the result does not establish that a dedicated student is necessary. Pair-invalid sensitivity is similar; salted split sensitivity is wide and based on only 2 test pairs. All Stage D, training, Phase 2, B5, DATA_GO and RQ2 boundaries remain closed.
## 2026-10-05 Stage D necessity gate

B0-B4 exploratory v2 has been interpreted under the approved risk limit 0.10. B4 passes the primary and whole-pair risk slices but fails the 2-pair salted sensitivity slice; the gate is `PILOT_ONLY`, dedicated student necessity is `NOT_ESTABLISHED`, and the internal paper remains on the Stage E fallback route. No Stage D/A0-A2/Phase 2/training conclusion is produced.
## 2026-10-05 Stage D formal boundary

`DATA_NO_GO / RQ2 NOT_IDENTIFIED` is now recorded as a formal boundary with exact recovery requirements in `docs/experiments/2026-10-05_stage_d_data_no_go_boundary_and_requirements.md`. The exploratory same-sample linkage exists for the 10-pair subset, but confirmatory identification still lacks independent clusters, non-empty split layers, strict visibility receipts, and a signed power receipt.

2026-10-05 Route V full benchmark decision：用户选择第二路线（Valentine full benchmark + frozen process adapter）。Zenodo Valentine full benchmark 经只读 ZIP Range 结构审计，551 个完整 pair directories 仅形成 8 个保守 shared-origin components，低于 40 个独立 clusters；预注册硬止损因此自动转入第三路线。不下载 archive、不提交 selected-pair annex、不运行 full-benchmark matcher/process adapter。`DATA_NO_GO / RQ2 NOT_IDENTIFIED` 作为正式负结果边界，小论文保持 Stage E 保底路线，完整 Evaluate-Distill-Evolve 验证转 future work。
