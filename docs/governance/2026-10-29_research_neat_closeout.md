# 科研资产治理与挖宝

日期：2026-10-29，Asia/Shanghai。方法：inquiry-methods 的 portfolio-triage，范围是项目现有证据、科研入口和工作区；本轮未运行科研实验、模型、训练、生产探针或外部联系。以下“机会”是研究负责人推断，不是已验证贡献。

## 一、整理了什么

- 用 git mv 原文归档旧 [科研入口](../archive/2026-10-29_research_neat/RESEARCH_ENTRY_pre_neat.md)、[Loop D 指令](../archive/2026-10-29_research_neat/LOOP_D_PROMPT_pre_neat.md)、[STATE](../../memory/archive/STATE_2026-10-29_pre_neat.md) 和 [THREADS](../../memory/archive/THREADS_2026-10-29_pre_neat.md)，再在原路径建立精简现役版本。旧快照内相对链接按原文件原目录解释，历史结果与授权不自动迁移为当前事实。
- 当前科研入口为 [docs/research/README.md](../research/README.md)；唯一可维护指令仍为 [LOOP_D_RESEARCH_PROMPT.md](../research/LOOP_D_RESEARCH_PROMPT.md)。Paper E 当前 v5 是内部审阅稿；历史 v2/v3/v4 保留不覆盖。
- 主工作树 7 个未跟踪结果文件与 GB10 原文件逐项 SHA-256 一致，已备份到本机 D:/Documents/Loop_D_assets/neat_20261029，含逐文件 manifest，再移除工作树重复副本。GB10 原始证据未动；备份目录不是 Git 真值或公开 artifact。
- 本机集成 worktree 有 30 个未跟踪文件，均没有 HEAD 同路径文件；含旧投稿构建脚本、PDF/DOCX、页面图与两个结果文件。不同路径可能另有重复，但未全部证明，保留原位；不能视为全部可删除。
- GB10 审阅 worktree 的 C_TASK.md、budget_measure.py 不在 main 同路径，暂保留；C_PAPER_E_V2_REVIEW.md 与 main 对应 blob 相同。其余历史 worktree 未跟踪文件数为零，但各含 3 至 420 个 Git 忽略文件，未逐个确认价值，保留。
- GB10 主树的 pytest_loopb.txt 仅观察到一行测试耗时变化，可能由活跃 Loop B 更新，未回滚、提交或拷贝覆盖。

## 二、Git、规则及验证范围

治理前本机 main、GitHub main、GB10 main 和当前论文 worktree 为 19df9ffe；本机集成分支同头。可见远端分支均为 main 的祖先，未发现必须再合并的提交。GB10 本地旧 integration 分支当时指向 1d9669a5，属落后且未检出的分支，可快进；历史 worktree 的分支与忽略文件不是多余提交的证明。

近几次 commit 是连续增量，历史已推送共享，不做 rebase、squash 或强推。最终 commit 以实际 Git 与本轮回复核验为准。未验证生产部署或运行服务，不以 Git 一致宣称运行一致。

repo skill-doctor 只读检查为 0 errors / 140 warnings；skill-map 只读按仓库范围检查 agent-prompt-contracts，发现 m2-rag-playbook 的引用。既有 docs_lint 有 agent-prompt-contracts 安装内容漂移及 SKILL_ROUTING 时效提示；本轮不覆盖共享安装，也不降低门槛。

## 三、资产机会：按 Paper E、第二篇和学位价值排序

| 排序 | 证据及事实 | 可挖掘的价值与下一动作 | 关键边界 |
| --- | --- | --- | --- |
| 1 | [Paper E 负结果复核](../../research/negative_result_robustness_20261013/NEGATIVE_RESULT_ROBUSTNESS_AUDIT_v1.md)记录单响应叶约 0.375 由权重导出、干净差值支撑集为 0，以及受控阶段消融。 | Paper E 可更清楚地解释“为什么阈值会制造检出率差”和“为什么干净集不能选唯一阈值”，把公式、分母和对照绑在同一个读者例子里；先核映射再改稿。 | 是单叶和冻结构造的解释，不是普遍理论；不要把单 judge 判定当人类 gold。 |
| 2 | [真实迁移复核](../../research/publication_thesis_goals_v1/revision_v2/G2_V2_REPORT.md)及 [NtripBrowser 资格](../../research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/QUALIFICATION_RETURN.md)保留行为测试、静态检查与依赖消费的反例。 | 可为学位论文提供直观说明：同一输出通过测试，仍可能不满足更具体的目标合同；适合做审计原理教学和未来真实任务资格素材。 | 简单 alias-aware 检查加行为测试已追平现有候选，不是新的通用 verifier 方法。 |
| 3 | [Agent 候选方向](../../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)覆盖 skill 适用性、工具恢复、预算决策，已有公开论文和基线边界。 | 优先研究可见条件变化时如何选择或修正 skill；先跨多公开任务检验最强固定文档/规则/重试并计总成本，再决定是否引入学习。 | 一项公开任务、不同实际调用成本与接口故障不能证明方法；近邻 Skill-V/SkillsBench 等需按版本再对标。 |
| 4 | [SkillsBench 开发性可选文档运行](../../research/agent_skill_method_20261029/DOCS_LIMIT12_EXPLORATION.md)中，任务产物的 10 项断言通过，但 Agent 进程退出 1，拒绝原因未定。 | 分别测量“产物是否正确”和“执行过程是否干净结束”，作为 Agent 评测合同的实用设计，后续跨任务验证。 | 一次运行和一个任务不支持概率或普遍规律；10 项断言不是 10 个独立任务。 |
| 5 | [MA-CERD 日期更正](../../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)澄清资源 membership 非图传播，0.012 是完整集合精确匹配，241/250 为合法 defer。 | 可复用“合法动作、完成任务、风险、覆盖率、成本分开”的评价设计，特别适合研究 Agent 弃答和工具恢复。 | 旧 [尸检](../../research/ma_cerd_independent_v1/EXPERIMENT_AUTOPSY.md)的图传播和依赖解释被更正；不复活旧宣称，未独立重建 simulator trace。 |
| 6 | [Phase B 前提更正](../../research/decision_residual_pivot_20261026_v1/D_PREMISE_CORRECTION.md)发现父 adapter 没有按预期激活、集合准确率不等于答案正确率。 | 保留为训练实验可复用的控制清单：明确实际激活参数、同起点、可见信息、输出合同和评测指标，再考虑 LoRA/SFT。 | 当前 R/E 实现停止，不能推成所有反馈学习或局部编辑无效。 |
| 7 | [G3 离线检索与纠偏](../../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)将 coverage/成本潜力与真实任务收益拆开，弱信号与随机相容。 | 未来 Agent 的主动证据获取可复用 runner、覆盖/总成本指标与强随机/固定策略作为检查。 | oracle 的潜力不是部署收益；旧面板不重新包装为方法成果。 |

## 四、下一步与退出条件

1. **优先 Paper E**：基于 v5 核实阈值/评分公式，补一处清晰的数值解释，再按选定正式 venue 编排与精简；若目标范围或页数不匹配，换渠道或重构，不靠缩字号。需要统计/首次读者审查及作者对外事项。
2. **第二篇开发**：整理多个公开 Agent 任务的许可、环境、独立 verifier、暴露边界与真实成本，比较信息匹配的强基线；若简单对照解释收益，调整问题或保留负结果。
3. **学位资产**：逐项区分已成立的 Paper E 证据、待确认的 Agent 方法与可复用失败教训；不把同一机制拆成两个创新点。

不因清理而删除原始输出、证据、历史账本或工作树；不因机会清单自动开启实验、外部公开或投稿。本报告是盘点和建议，不是新的科研结论。
