# 三阶段科研资产地图 v2

> 状态：当前索引 | 更新：2026-10-05 | 范围：论文相关仓内资产与已知仓外证据

## 1. 账本职责与阅读顺序

先完成 `AGENTS.md` 的规则/记忆必读，再按 `docs/research/README.md` → `paper/research_story_v2.md` → 本账本 → `docs/handoff/2026-09-22-paper-research-next-phase.md` 阅读。入口 §1 管权威冲突，叙事管故事，本账本管证据与缺口，执行计划管下一张任务卡；数字以原始工件为准，不按文档新旧投票。

`paper/teacher_review_note_v2.md` 是当前导师说明；`paper/research_story_v2.docx` 已由当前 Markdown 和同步后的三阶段表离线重生成，结构/口径测试通过，Office 视觉验收已于 2026-10-03 PASS；它不覆盖 Markdown。方向包使用成熟评估稿 + 当前故事，不等待统一论文实验完成。

投稿准备入口为 `paper/submission_readiness_arr_www_v1.md`：只整理 ARR 10/12 主窗口与 WWW 10/18/10/25 后备窗口的材料清单和硬阻塞，不构成投稿、不解除专利门。

### 1.1 “有资产”与“可在本机执行”分开登记

> 2026-10-03 状态记录：两份 DOCX 的视觉验收证据见 `docs/experiments/2026-10-03_office_visual_acceptance.md`。

本账本中的“可用”仅指所列代码/报告/工件可作为相应证据或复用素材，不表示本机输入齐备、服务存活或获得执行许可。全仓依赖图见 `docs/architecture/codebase_map.md`；`scripts/catalog.toml` 不覆盖根 `research/`，不能据它漏掉科研代码。

| 输入/资产 | 仓内可核验 | 依赖及本轮边界 |
|---|---|---|
| `logs/graph/eval/` 已有 JSON | 既有统计、分母、hash 与 provenance 引用 | 复算不等于重做实验或完成 Phase 1 标签审计 |
| `research/vgmc_exp1.py` 的 fewshot/记忆纯逻辑 | 合成 fix/meas fixture 与 mock 请求合同 | `load_corpus()` 需要 `data/research/drift_v0/output/`；完整新 replay 不在本地跑 |
| `research/dpo_pairs_v0.py` | 从已有 checkpoint 构造偏好的代码与现有结果 | 60 对偏好单向；不可据脚本存在宣称训练数据过门 |
| 源表、逐题输出、模型权重与训练环境 | 仅仓内引用、代码所需路径与既有报告 | 用户说明在另一台服务器，本轮未核验；不下载、搬运或重建，不据本地缺件判失败 |
| 文稿与派生器 | Markdown、SVG、临时 DOCX 的离线结构检查 | 不能代替 Office 视觉验收、导师认可或公开许可 |

本地只分析既有事实和验证代码合同；生成新论文数字的可学性实验、规则 replay、训练与终评均按 `docs/governance/2026-09-07_execution_plane_boundary.md` 在 GB10 获批执行。未来若输入仍不可核验，明确暂停对应步骤，不伪造结果；这不是本轮环境治理任务。

## 2. Stage E — 大模型流程评估

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 路线 | `docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md` | 评估论文结构与实验问题 | 历史过程稿；只作评估素材，不再控制三阶段方向 |
| 方法 | `config/eval_checkpoint_trees.json` | 两棵检查点树定义 | 可用 |
| 方法 | `scripts/eval_checkpoint_aggregate.py` | 递归聚合实现 | 可用 |
| 方法核对 | `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md` | 算法行与实现对位 | 可用 |
| 主实验 | `logs/graph/eval/checkpoint_discrimination_tables_v2.json` | 95 表、118 注入、可见性 | 可用 |
| 对照 | `logs/graph/eval/t1_eval_baseline_comparison.json` | 端到端/扁平/层级协议 | 可用 |
| 稳健性 | `logs/graph/eval/t2_visibility_sensitivity.json` | 阈值敏感性 | 可用 |
| 匹配器 | `logs/graph/eval/d2_cross_matcher_det.json` | 跨匹配器结果 | 可用 |
| 统计 | `logs/graph/eval/d3_matched_fpr_stage_a.json` | matched-FPR bootstrap | 可用 |
| 稿件 | `paper/teacher_review_draft_v1.md` / `paper/teacher_review_draft_v1.docx` | Stage E 成熟英文子稿 | Markdown 主张核验及 DOCX 内容/结构比对已通过；Office 8/8 + 4/4 页视觉验收已于 2026-10-03 PASS，仍不代表完整三阶段论文 |

## 3. Stage D — 小模型蒸馏

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 模型矩阵设计 | `docs/experiments/2026-08-18_small_model_matrix_design.md` | 4B/8B/14B/27B 与质量—成本协议 | 可用 |
| 模型矩阵结果 | `docs/experiments/2026-08-19_small_model_matrix_c1c2.md` | 14B、8B 训练前基线 | 报告可用；逐题 JSON 在 GB10 gitignored 路径 |
| 模型矩阵结果 | `docs/experiments/2026-08-21_small_model_matrix_c3.md` | 4B 训练前基线 | 报告可用；逐题 JSON 在 GB10 gitignored 路径 |
| 文献 | `docs/experiments/2026-09-20_kd_literature_candidates.md` | KD、agent distillation、多教师路线 | 18 条候选已核；venue 仍按文档边界 |
| 方法与理论素材 | `paper/method_theory_materials_v1.md` | 统一记号、defer 路由、风险—覆盖、三门更新、有限样本风险上界、累计局部回归界、回滚不变量和最近邻差异 | 可用于 Method/Related Work；固定池伸缩界是条件推论，不等于实验保证 |
| 数据分层与选型 | `paper/dataset_protocol_v1.md` | Q0–Q3 标签质量 × 四层角色、FinQA 过程源 + Valentine 动作源的双 P0 选择、模型矩阵 | D-C 最小范围已下载到 GB10 仓外暂存并取证；不新增下载。动作包仍 `DATA_NO_GO`，Q3 仅 exploratory |
| Q3 复核包生成器 | `research/valentine_q3_review_package.py` | 从批准的 Valentine pair 输入生成 R1/R2/ADJ 输入包、样本清单和可见性 manifest | 零模型；只读 source/target 表头与文件 hash，`ground_truth.json` 仅允许存在性校验、禁止读取。三位独立专家 raw package 已封存，corrected ledger 51/58/37，visibility 例外保留 |
| Q3 exploratory result | `docs/experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md` | 三专家 R1/R2/ADJ 结果摘要、证据边界与 B5 typed-decision candidate | 用户确认摘要：146/146 adjudicated、119/146 exact agreement、41/41 target exact、pre-correction 52/58/36；authoritative corrected 51/58/37；raw sealed with visibility exceptions，仍只作 exploratory |
| B5 candidate | `docs/experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md` | Jev-like typed-decision baseline 的输入、两阶段输出、指标和 go/no-go 问题 | `PROPOSED_EXPLORATORY / NOT_RUN`；不替换 B0-B4，`open-alternative-jev` / `jevos-v2` 未核验，不安装、不运行 |
| Q3 输入边界 | `docs/experiments/2026-10-03_ruling_gd_q3_package_and_goal_refresh.md` | 10 pair / 146 source columns / 160 target headers、双跑包 hash 与零 gold 可见性证据 | 输入包与可见性已闭合；现役结果见 `SUMMARY_q3_label_and_baselines.md`，只作 exploratory，不得升级为 Stage D/RQ2/DATA_GO |
| Q3 allowlist 重建边界 | `research/valentine_q3_review_package.py` + `/tmp` 输入视图 | 当前原始 staging 含 `_full/_result/_trajectory` 扩展件，按新 allowlist 会被 `input_manifest_scope_mismatch` 拒绝；旧包是 hardening 前的不可变历史产物 | 重建必须使用仅含 10 pair × {source_table.csv, target_table.csv, ground_truth.json} 的过滤输入根和 30 行 manifest；ground_truth 只做存在性校验，禁止读取 |
| 公开来源注册表 | `docs/datasets/paper-public-source-registry-v1.json` | 10 个来源的核验 commit、许可缺口、independence-cluster namespace、角色适配与准入状态 | metadata only；namespace 需与具体 origin id 组合成样本簇，全部 `download_approved=false` |
| D-B licence_record | `docs/datasets/phase1a_licence_record_v1.json` | 正式接受记录：accepted_by=Wzh、现场 accepted_at、四项 permitted_uses；covered hashes 仅限 FinQA LICENSE / FinQA README / Valentine LICENSE | 已落地但仅限 D-B scope；不是 package-wide 授权，不解除 `DATA_NO_GO` |
| RQ2–RQ4 执行矩阵 | `paper/thesis_rq2_rq4_execution_matrix_v1.md` | 第 5–6 章的臂、指标、门序、确认性族与禁止写法 | 规划件；所有实验槽位仍为空，不产生结果 |
| 方法引用与细化图 | `paper/method_data_references_v1.bib`、`paper/figures/fig_rule_gate_replay_v1.svg` | 42 条已核候选 BibTeX；共享流七臂/三门/回滚/数据防火墙 | 可直接复用；图明确标注无正式结果 |
| 实验预注册 | `docs/experiments/2026-09-22_distillation_mvp_preregistration.md` | RQ2–RQ4、数据/模型门、A0–A3、七臂、双口径、统计与停止规则 | `DRAFT_NOT_FROZEN`；数值容差/资源/来源待人工批准 |
| 训练数据设计 | `docs/experiments/2026-08-28_dpo_pairs_v0_design.md` | 门控事件转偏好对 | 可用 |
| 候选事件 | `logs/graph/eval/vgmc*_checkpoint.json`（16 件） | 494 条有 gain/collateral 的 gated 事件，48 uid / 94 uid-col / 139 uid-col-target | 本地 P1 已审：292/202；16 组冲突隔离、41 列多 target；不等于训练数据放行 |
| 训练数据 | `logs/graph/eval/dpo_pairs_v0.json` | 60 对、36 uid、60 uid-col；全部 skip 优于 map_to | 无 Type-B、gate_fooled=9；偏好单向，不是 DATA_GO |
| 生成器与审计 | `research/dpo_pairs_v0.py` | 旧偏好生成入口 + 独立 `--audit` 路径 | 审计已交付，17项用例保留给服务器复核；不调用旧生成入口或建议器 |
| 学生训练 | 尚无 | 8B 动作策略/规则候选 SFT，DPO 条件实验；4B 仅 smoke | **needs-evidence**；不得称完整过程推理蒸馏 |
| 训练后评估 | 尚无 | 四层隔离、未见缺陷家族、质量—成本与回归 | **needs-evidence**；先离线强基线再申请训练 |

结论：小模型矩阵回答“现成模型能做到什么”，蒸馏实验回答“评估筛选的教师知识能否被迁移”。两者不能混用。

### 3.1 P1 本地审计交付（2026-09-22）

`research/dpo_pairs_v0.py --audit` 已完成本地可核范围，不调用旧生成入口、不加载原始语料/模型。37 件输入包括 16 checkpoint、16 results、3 overlay、DPO 和表级评估参考；23 条 arm 的接受事件从空规则库重建后均与 checkpoint/result 终态一致。这里只重建既有账本，不重算 gain/collateral 或产生新实验效果。

| 核验项 | 实测与解释 |
|---|---|
| 事件分母 | 全臂 1584；gated 原始 625 = 带分数 494 + no_map 126 + 非标准目标 5 |
| 原始动作 | map_to 499、skip 121、parse_fail 5、hold 0；旧格式42条 map_to 由分数合同推断且明确标记 |
| 去重与冲突 | 48 uid / 94 uid-col / 139 uid-col-target；包含事件前规则状态的完全重复观测17条，不靠重复扩独立样本；16组相反标签全部保留并隔离，41列多目标 |
| 冲突上下文 | 16组中15组规则前态不同、15组overlay版本不同；这解释“不能直接合并”的上下文差异，不是因果归因或反事实验证 |
| 参考字段核对 | 494条均可回链到已有注入/overlay的 header+canonical：368目标一致、126不一致；292条接受中17条与参考字段不一致。**这是对工件记录字段的精确比对，不是原文语义/下游危害独立真值** |
| DPO | 60对/36 uid；全部 skip>map_to，A=50、C=51重叠，Type-B=0；记录 gate_fooled=9；6对 rejected 的映射与对应参考字段一致，不能把拒绝标签直接当错误标签 |
| 来源隔离 | 16份历史划分一致、fix60/meas35、源表无交集；但67条去重的借用表头变体关系中28条跨历史fix/meas，扩展语料另有刻意共享变体；历史评估不能冒充新的未见终评 |
| 未见数据 | 95表全部只标 HISTORICAL_ONLY；不重新随机切分。新的 gate-validation / sealed test / future replay 均 MISSING；训练内部dev也未擅自分配 |

家族覆盖（gated，uid 数跨家族不可相加）：

| 家族 | 原始事件 | 带分数事件 | 独立 uid |
|---|---:|---:|---:|
| alias_variant | 220 | 171 | 17 |
| collision | 128 | 87 | 26 |
| date_variant | 99 | 92 | 10 |
| mixed_lang | 72 | 61 | 8 |
| prefix_noise | 66 | 47 | 9 |
| unit_suffix | 40 | 36 | 5 |
| ocr_similar | 0 | 0 | 0 |

**分视图判门**：动作 SFT、风险预筛为 `DATA_NO_GO`（当前输入不具备完整源表/候选schema、独立标签/许可核验及新隔离数据）；DPO 为 `PILOT_ONLY`（仅保留历史审计/设计素材，不批准训练）。三视图均有可追溯审计索引，`training_export=[]`。这是本地现有材料的放行判断，不是另一服务器资产丢失、实验失败或永久否决路线。

**功效仅作敏感性**：以独立 uid 为单位、双侧α=.05、80% power 的配对均值正态近似，假设差值SD为0.25/0.5/1；48 uid 的示意MDE为0.1010/0.2021/0.4041，36 uid 为0.1167/0.2333/0.4667。未测得真实差值方差，也未估计 macro-F1 专属功效，不能用此数字批准非劣δ或DATA_GO；指标/容差待确认。

复算命令（输出文件必须尚不存在）：

```bash
python3 research/dpo_pairs_v0.py --audit --output data/research/p1_audit/p1-data-audit.json
python3 research/dpo_pairs_v0.py --audit --output data/research/p1_audit/p1-data-audit-repeat.json
PYTHONPATH=src .venv/bin/python -m pytest tests/test_distillation_data_audit.py -q
```

两次 JSON 字节一致，SHA-256=`d5df834668878f70e09a0cbbb21f46ee0c5e08b86aafd41f66ea01c7013c2471`；输入清单内容hash=`5591e3a61071d476a53dc57942dc501e7ca65a7e75feed72ec6c524d411cfcb5`；历史/缺层 manifest hash=`b17c4741bf93b619c3ff39a95b2bb3bedbd6041bb5bde1b3daff272b91582504`。原checkpoint/DPO hash仍与执行计划§1.2一致；完整事件、冲突、来源索引和manifest仅在 gitignored `data/`，不提交。17项审计测试通过，endpoint/socket尝试均0。

**后续不自动运行**：保留评估稿作近期交付；完整源表/许可、正确动作和双向偏好、OCR/hold覆盖及独立新数据的补充，连同 Phase 1a/2 和训练都等待用户批准。其他服务器本轮不连接或获取。

**补充包预检器**：`research/phase1a_data_contract.py` 将上述缺口固化为七道机械门（工件完整性、层隔离、独立正确性、许可、confidence、分析计划、parser contract），合成回归位于 `tests/test_phase1a_data_contract.py`。它只可能输出 `DATA_NO_GO` 或 `READY_FOR_INDEPENDENT_ACCEPTANCE`；后者仍须 GB10 对私有原件做零连接、双跑确定性及人工独立验收，不是 `DATA_GO`、训练许可或新的论文证据。完整合同和命令见 `docs/experiments/2026-09-23_phase1a_data_no_go.md`。

**可学性五基线前置**：`research/phase1a_learnability_baselines.py` 与 `tests/test_phase1a_learnability_baselines.py` 已把 always-skip、确定性精确匹配、lexical/fuzzy、confidence-only 和简单 CPU 分类器固化为 proposal train/dev 专用 runner。接收回执必须绑定数据预检、私有 view 与预注册配置 hash；输出仅含聚合指标、UID-cluster 区间和 `SIMPLE_SUFFICIENT` / `LEARNABILITY_SIGNAL` / `NO_CLEAR_SIGNAL` / `PILOT_ONLY`。当前已有 GB10 exploratory v2 结果，但 Stage D necessity gate 为 PILOT_ONLY、RQ2/TH-I3 仍为 needs-evidence。

## 4. Stage R — 自学习规则进化

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 原始规划 | `docs/30_科研线规划.md` | VGMC/VGRM 早期单线设计 | 历史素材，受现行口径约束 |
| 方法稿 | `docs/experiments/2026-08-29_vgrm_method_chapter_draft_v0.md` | 门控算法、命题、碰撞机制 | 可用，需按最新证据收窄 |
| 核心实现 | `research/vgmc_exp1.py` | gated/ungated 规则固化 | 可用 |
| 对抗与碰撞 | `research/vgmc_adv_judge.py`、`research/vgmc_collision_corpus.py`、`research/vgmc_collision_expand.py` | 有害建议和碰撞暴露 | 可用 |
| 主工件 | `logs/graph/eval/vgmc_exp1_results.json` | 固化率、学习曲线、holdout | 可用；主效应不强 |
| 强机制证据 | `logs/graph/eval/vgmc_adv_curve.json` | 对抗候选拒绝 | 7/7 拒绝，机制证据 |
| 碰撞证据 | `logs/graph/eval/vgmc_collision_curve.json` | 门控与无门控差异 | 有方向性差异，不能替代功效分析 |
| 基线 | `logs/graph/eval/vgmc_baseline_curve.json` | few-shot/Mem0/AWM 式对照 | 与 no-gate 不可分，保留 null |
| 学习门 | `logs/graph/eval/bandit_gate_v0_eval.json`、`logs/graph/eval/bandit_prospective_eval.json` | 阈值 bandit | 奖励无分辨力，需重设计 |
| 七臂 replay 软件合同 | `research/phase2_rule_gate_replay.py`、`tests/test_phase2_rule_gate_replay.py` | 共享候选流、独立状态、逐臂重算与 rollback | 合成软件证据可用；正式 Phase 2 未执行 |
| 论文数据接口 | `research/paper_result_views.py` | Phase 2 报告 → Table 2 / Figure 4 聚合视图 | 仅未验收预览，固定 `paper_result=false`；不能作为论文数字 |

## 5. 总体路线与图

| 资产 | 角色 | 注意事项 |
|---|---|---|
| `docs/33_导师指导吸收_科研三线升级.md` | “评估 + 改进 + 自学习”原始总纲 | 受保护，只读 |
| `docs/34_专利_小论文_大论文协同研究路线.md` | 2026-08-29 的评估单线收敛与专利边界 | 论文范围已被 2026-09-22 用户校准；公开边界继续有效；受保护，只读 |
| `paper/figures/fig_evaluate_distill_evolve_v1.svg` | 三阶段 Figure 1 | 实线/虚线同时编码成熟度，不只靠颜色 |
| `paper/thesis_manuscript_scaffold_v1.md` | 大论文章节与创新点 | 已恢复蒸馏独立章节 |

## 6. 主张—证据—缺口账本

| 当前叙事 RQ | 已成立与限制 | 下一证据门 / 责任角色 |
|---|---|---|
| RQ1 / Stage E | 95 表、118 注入与可见性/协议审计；不主张层级检出率更高或跨系统普适 | 成熟评估保底稿；第二数据流/scorer 为后续条件工作 / 论文 Agent |
| RQ2 / Stage D | 本地 P1 已审，§3.1 记录冲突与标签边界；两头 SFT、risk–coverage 与条件 DPO 公式素材已整理；无训练结果，三视图均未放行训练 | 按 `dataset_protocol_v1.md` 补独立正确性/源表/新隔离数据，再经批准做 Phase 1a 与后续实验；DPO 独立判门 / 数据与实验 Agent |
| RQ3 / Stage R | 现有拒绝与碰撞是机制证据；累计局部回归界和 rollback 不变量已写明，固定池伸缩界及净收益/长期回滚仍 needs-evidence | Phase 2 七类共享流且状态独立的门基线、Phase 5 冻结快照评测 / 规则实验 Agent |
| RQ4 / 闭环 | needs-evidence，不把 E 与 R 分别存在写成闭环有效 | Phase 5 sealed test/future replay + Phase 6 合稿门 / 实验与论文 Agent |

执行计划的历史 §10 审计已交付，当前边界见 §13；补充包合同、五基线 runner、Phase 2 七臂状态机与论文数据接口当前只接受合成测试，不产生正式实验事实。GB10 私有包验收与导师包 Office 视觉核对仍待执行；Phase 1a 正式开发探针、Phase 2 数据 replay 及训练均待相应门通过和授权。保留评估稿作近期交付，不能从 PILOT_ONLY、`READY_FOR_INDEPENDENT_ACCEPTANCE`、`LEARNABILITY_SIGNAL` 或软件合同 PASS 推导训练许可/论文结论，详细停止条件仍只维护在执行计划。

## 7. 清理裁定

- 保留评估子稿，不复制其正文到三阶段总叙事；内部稿、评估蓝图、旧骨架和审稿记录只作历史/素材，不再竞争当前方向。
- 不把模型矩阵、DPO 偏好对或训练钩子表述为已完成蒸馏；14B 既有异常尚未归因。
- 不把 bandit 奖励无分辨力包装成学习门有效。
- 不修改 `docs/33*`、`docs/34*`；入口仅覆盖旧论文范围/排期，不覆盖专利公开限制或已执行实验真值。
- 不再新增临时路线稿/claim 矩阵；叙事更新 `research_story_v2.md`，资产更新本账本，执行更新现有 handoff。
- 历史文件不删；大规模移动、删除、改名须用户另行确认。

## 2026-10-04 boundary/blocker addendum

- Q3 raw closure: COMPLETE_WITH_VISIBILITY_EXCEPTIONS. R1/R2/ADJ outputs, corrected label ledger, receipts and hashes are sealed; authoritative distribution is `map_to=51 / skip=58 / hold=37`. R1 saw lineage grouping and R2/ADJ lack independent signed visibility receipts, so evidence remains exploratory only.
- Invalid action reference audit: Option A quarantines turn 12/13/31 with `invalid_action_reference_count=3`; Option B whole-pair INVALID is the mandatory 9-cluster / 130-column sensitivity.
- B0-B4 exploratory protocol: [docs/datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md](../docs/datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md), v2 executed on GB10 as exploratory evidence; first run remains invalidated by the salted B4 alignment bug.
- B5: no locally verifiable source/licence/version/dependency/output capability for either candidate; PROPOSED_EXPLORATORY / NOT_RUN.

## 2026-10-04 ruling update

Raw delivery target and no-reconstruction rule are recorded in docs/datasets/phase1a_q3_seal_receipt_v1.json. Invalid references are Option A primary / Option B sensitivity. B0-B4 is LOO primary / salted sensitivity, bootstrap exploratory only. B5 remains dormant.

## 2026-10-04 raw seal update

Q3 raw package is sealed with visibility exceptions. Corrected ledger SHA256 cf339cef8b7065dad05f574a1400415a7bff64b78b66e1db38f74143cc49ccb6; authoritative counts 51/58/37. R1 is not strict three-field-only and R2/ADJ lack signed visibility receipts.

## 2026-10-04 B0-B4 exploratory evidence

- Freeze v2: `docs/datasets/2026-10-04_b0_b4_exploratory_freeze_v2.json`.
- Machine results: `docs/datasets/2026-10-04_b0_b4_exploratory_results_v2.json`.
- Narrative results: `docs/experiments/2026-10-04_b0_b4_exploratory_probe_results_v2.md`.
- Primary B4 action macro-F1 0.717 / harmful-map 0.062 / coverage 0.260; B3 0.572 / 0.178 / 0.329. Pair-invalid B4 is similar. Salted sensitivity is only 2 test pairs and remains uncertain.
- Scientific boundary: B4 is the baseline to beat; dedicated student necessity is not established; all results are exploratory and `paper_result=false`.
## 2026-10-05 Stage D necessity gate

Machine gate: `docs/datasets/2026-10-05_stage_d_necessity_gate_v1.json`; report: `docs/experiments/2026-10-05_stage_d_necessity_gate.md`. B4 is risk-admissible in primary and pair-invalid slices but not in the 2-pair salted slice. Verdict `PILOT_ONLY`; dedicated student necessity `NOT_ESTABLISHED`; internal paper route remains Stage E fallback.
## 2026-10-05 Stage D boundary requirements

Formal boundary: `docs/experiments/2026-10-05_stage_d_data_no_go_boundary_and_requirements.md`. It distinguishes the exploratory 10-pair same-sample linkage from confirmatory RQ2 and enumerates the exact SOURCE/LABEL/SPLIT/POWER/BASELINE/MODEL/SAFETY conditions required to change `DATA_NO_GO / NOT_IDENTIFIED`.
## 2026-10-05 training readiness and protocol assets

- `docs/datasets/2026-10-05_stage_d_training_readiness_config_v1.json`: A0-A3/4B-smoke dry-run config, QLoRA/A3 conditional fields, resource gates and planning estimates.
- `docs/datasets/2026-10-05_stage_d_training_readiness_validation_v1.json`: GB10 dry-run validator report, `PASS_DRY_RUN_ONLY`; `peft/trl` and `accelerate` are installed, `deepspeed` is intentionally not installed, and no training execution has started.
- `docs/experiments/2026-10-05_model_sync_mirror_success.md`: Qwen3-4B exact-revision artifact acquired through the approved `hf-mirror.com` fallback with `token=false`, Xet disabled, verified hashes/license, and third-party provenance wording.
- `docs/datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json`: GB10 real artifact validation receipt. It verifies 13/13 immutable identities, 3 shard headers, 398 tensors, tokenizer/licence, and canonical model-root-relative manifests. It is model artifact evidence only, not Stage D, MODEL_GO, or training evidence.
- `docs/experiments/2026-10-05_qwen3_8b_model_sync_and_validation.md` and its two receipts: GB10 evidence that Qwen3-8B revision `b968826d...` is downloaded and artifact-validated with 15/15 identities, 5 shard headers, 399 tensors, tokenizer/licence, and canonical manifests. This is model artifact evidence only; it does not close Stage D, RQ2, Stage R, RQ4, or training.
- `docs/experiments/2026-10-05_stage_d_necessity_residual_memo.md`: A2 residual criteria and current `PILOT_ONLY` decision.
- `docs/experiments/2026-10-05_stage_r_rq4_static_protocol.md`: seven-arm order/state/rollback and C0-C3 static contract.
- `docs/datasets/2026-10-05_rq2_source_label_split_power_application_v1.md`: exact SOURCE/LABEL/SPLIT/POWER request, pending user approval and no download.

## 2026-10-05 Valentine full benchmark structural audit

- `docs/experiments/2026-10-05_valentine_full_benchmark_structure_audit.md`: read-only Zenodo ZIP Range audit of the 602,150,347-byte CC-BY-4.0 archive. It records 551 complete pairs, five families, four scenario classes, actual source/target/mapping/config structure, shared-origin components, and the `8 < 40` hard stop.
- `docs/datasets/2026-10-05_valentine_full_remote_structure_receipt_v1.json`: transport receipt, 1,578,443 range bytes, 7 requests, 0 retries, no full download.
- `docs/datasets/2026-10-05_valentine_full_entry_manifest_v1.json`: 7,746 ZIP entries with names, sizes, CRCs, compression modes, and offsets; includes `__MACOSX` metadata that is excluded from data counts.
- `docs/datasets/2026-10-05_valentine_full_schema_audit_v1.json`: eight representative pairs across all five families/four generated scenarios; CSV headers/row counts, column-keyed JSON type maps, mapping structure, and INI section/key names only. No ground-truth values or action/target labels were generated.
- `docs/datasets/2026-10-05_valentine_full_structure_summary_v1.json`: machine summary of inventory, scenario counts, shared-origin components, and the hard-stop decision.

These assets support a formal negative-result boundary only. They do not authorize archive download, adapter execution, A0-A3, Phase 2, B5, training, or external release.
## 2026-10-05 Route V DOCX refresh

`paper/research_story_v2.md` and its derived `paper/research_story_v2.docx` were synchronized after the Route V negative-boundary decision. DOCX hash is `5a506de6723a3364a06315c35581554406a4dce34e1efc90ec8a8ed498e8ef30`; GB10 Office text/ZIP/PDF/page-4 visual checks passed. The mature Stage E teacher-review DOCX was not changed.
## 2026-10-05 Track B pilot and formal negative path B closure

- Track B pilot receipt: `docs/experiments/2026-10-05_track_b_adapter_pilot_receipt.md`. Durable GB10 package: `/home/testuser/wzh/track_b_adapter_20261005_seal/`; manifest hash `dc388959150c98ffa7639108e1e80e306c346317b1cdced632ab66593960a04b`. Primary is 10 pairs / 146 columns / 657 events; pair-invalid sensitivity is 9 pairs / 130 columns / 573 events. `ground_truth_read=false`, `correctness_status=NOT_RUN`, `paper_result=false`.
- Formal negative completion audit: `docs/experiments/2026-10-05_formal_negative_path_b_completion_audit.md`. The current goal's path B is complete: `DATA_NO_GO / RQ2 NOT_IDENTIFIED`, 551-to-8 origin explanation, no native trajectory/checkpoint bridge, Stage E internal submission, and thesis proposal/chapters 1-2/framework plus pilot, negative-boundary and future-data evidence are all present.
- Evidence classification remains strict: Stage E is the formal small-paper route at internal submission scope; Q3, B0-B4 and Track B are exploratory/within-origin pilot and are not RQ2, Stage D, Stage R or RQ4; Stage D/R/RQ4 remain plans or empty slots; model artifacts are readiness only.
- External submission, patent, venue, authorship, camera-ready, Stage D/R/RQ4, training, Phase 2 and external release remain incomplete.
- Git source relationship: `f0764e714d21408a1a848ee0f327a22294eda73a` is the scientific/test content source or equivalent GB10 baseline; `652c9c6cadc2b62b731ee13ed34663562f88dc65` is metadata-only; `1d5a7ff8218fa9ec073cebcd81a0a39523d7c14b` is documentation archive/link/workspace neat. The latter two do not change scientific results or running code.

## 2026-10-07 Stage E narrative and independent-evidence boundary

- The Stage E manuscript now uses `Visibility Is Not Detection` as its primary narrative: the evaluator's observability, protocol detection, and equivalence-dependent harmfulness are separated before any system-level interpretation.
- The current result remains narrow: hierarchical checkpoints improve evidence decomposition but not matched-FPR discriminability in the single-varying-leaf instantiation. No localization or cross-domain claim is promoted.
- Future independent evidence is tracked in `paper/teacher_review_readiness_v2.md`: second dataflow, independent second scorer, multi-leaf responsiveness, and external document scenarios such as financial audit, compliance review, and enterprise table processing.
- These future items require new artifacts and independent review before they can replace current limitations or become paper results.

## 2026-10-08 Stage E advisor-review readiness

- Stage E package head: `62274ef1fa624912390d4f0a05828c038a938ccb`; current repository head: resolve with `git rev-parse HEAD` on local/origin/GB10; pre-closeout synchronized head: `8c0b248ddfe19c937e815003ac31db48a54bc091`. Post-package commits are governance-only and do not change paper evidence.
- Canonical package hashes: source `abab44657e17936badf371a606198886ccd333a4c1489600c8922f78a6c57e80`; DOCX `6cfa6d9d329c172028cca18312921842fc2747bda3c6b331655cc7cacf7e4e85`; anonymous preview `fcce418a840373ccde8eece23f28fe0b2258de355a346184b82ffc2a70858d35`; submission audit `8cb1bce3c11344b3083004e6850206e4023964d82a7b21b318a2e31d161421ed`.
- Current status is `Stage E ready for advisor review`; Office/PDF visual check is PASS. Pending advisor decisions remain multi-leaf versus second dataflow and harmfulness definition selection.

> SUPERSEDED STATUS NOTE 2026-10-11: multi-leaf is complete and construct-sensitive; Route B is `NO / STOP_BRANCH`; FinQA formal-v3 is `SECOND_FLOW_MIXED` with accepted `MEASUREMENT_OBJECT_MISMATCH` interpretation. Historical future-work language below is retained as a dated record.
