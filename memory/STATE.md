# Current State

> 2026-11-04 | 当前短状态；证据与导航见 [科研入口](../docs/research/README.md)，未决事项见 [THREADS](THREADS.md)。2026-10-29 治理前的完整原文见 [历史快照](archive/STATE_2026-10-29_pre_neat.md)，其中相对链接沿用原文件位于 memory/ 时的基址。

## 科研与论文

- **当前节奏**：Paper E 审阅稿与 11 月 5 日前的导师讨论材料已备好，等待导师和作者团队反馈；科研执行重点转向 Agent 经验、反馈学习及变化适配，见[第二阶段计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。Paper E 尚未投稿，反馈到来后继续办理，不把内部准备等同于录用或发表。
- **导师阶段确认**：2026 年 11 月 5 日前拟就学位方向、Paper E 投稿计划和已有研究与导师沟通；[导师沟通稿](../research/advisor_direction_review_20261102/ADVISOR_BRIEF_20261102.md)是当前讨论入口，旧导师一页稿和旧学位骨架仅为历史。该稿中的三个研究点为拟议结构，尚未取得导师确认。
- **Paper E**：现役 [ICINT 短稿](../research/paper_e_publication_route_20261028/paper_e_icint_draft.md)、[4 页审阅 PDF](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)及[文档分析定位的 ICDAR 备投工作稿](../research/paper_e_publication_route_20261028/ICDAR_ADAPTATION_RETURN_20261101.md)，路线及限制见[投稿计划](../research/paper_e_publication_route_20261028/PUBLICATION_PLAN_ZH.md)。Gemini 建议经[既有数据与代码核对](../research/paper_e_publication_route_20261028/ICINT_CLAIM_EVIDENCE_REVIEW.md)后整合，匹配阈值下逐表和逐注入结果一致；另用 SciPy 与 statsmodels 对已存逐查询数据独立实现复算，30 组显著性判断一致。后者不是新样本或人工统计评审。ICDAR 工作稿仍含致谢，尚非合规双盲稿。先准备 ICINT，拒稿或正式撤稿后再考虑 ICDAR。作者已提供署名与通讯作者信息，私有记录已准备；作者团队终核、AI 声明、许可和独立审阅仍未完成。[v6](../research/paper_e_agent_evidence_20261029/paper_e_review_revision_v6.md)是历史详细稿。
- **第二篇和学位**：以 IJCNN 2027 为探索目标，重点是 Agent 从反馈/经验学习和变化环境下的技能适配；训练、蒸馏、记忆、规划协作及可靠执行仍可按证据调整，[长期研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)。[来源见证与人工修订试验](../research/agent_frontier_portfolio_20261029/SKILL_VERIFICATION_RETURN_20261101.md)显示单条风险建议可被局部修订，另一条旧范围条件仍可能被沿用；普通历史与确定性工具基线也能完成当前筛选，经验方法增量尚未确立。硕士目标 2027 年 10 月送审，具体日期未知。
- **Agent 开发证据**：[地震板块对照](../research/agent_frontier_portfolio_20261029/EARTHQUAKE_AGENT_DEVELOPMENT_20261103.md)有一次生成 skill 的正向距离线索，也有不稳定运行；[连续办公任务](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)中直接执行、历史和 skill 均完成目标，原评分还漏检一类错误 slug。[DBSCAN](../research/agent_frontier_portfolio_20261029/DBSCAN_AGENT_PILOT_RETURN_20261102.md)与[认证任务](../research/agent_frontier_portfolio_20261029/AUTH_TRANSFER_AUTOPSY_20261102.md)目前也没有识别出可靠方法增量。下一步寻找能区分强基线的自然变化任务，建立多来源和重复对照。
- **股票可视化格式变化**：[现役计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)记录 CSV 源、JSON/TSV 目标的无历史、历史、生成 skill 和事后反馈对照；各格仅一次，同属一个已曝光工作流族。skill 未稳定超过无历史或研究者的透明适配；一条目标未完成文件交付。历史读取的实际截断与上游 tooltip 测试的实现敏感性已分别用逐行对照和可执行反例核实。Agent 本身没有浏览器，成本与边界均在计划中单列；尚无跨来源方法收益。
- **SkillFlow 对账任务**：[现役计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)记录两个同族合成 PDF/Excel 任务及一个单元格变化的过时示例变体。三次无历史 Agent 均与独立输入复算一致；变体不能用旧测试答案评分。正计划以真实源轨迹和反馈形成历史、skill，再与无历史比较；当前没有方法收益结论。
- **最新资产复核**：[离线复算与尸检](../research/asset_revalidation_20261029_v1/REVALIDATION_AND_AUTOPSY.md)核对 Paper E 冻结结果、迁移验证合同、Agent 单任务的 2,000 行产物及 MA-CERD 动作集合；均为事后复核，不是独立来源确认。
- **解释边界**：BEIR 为研究者自建运行而非官方榜；FinRank 的部分身份结果为源码知情事后复现；未标注不等于不相关，统计不显著不等于相等。旧 R/E、exact-cache、FinRank H/K 等具体面板停止不等于相关一般方向无效。以日期更正和原证据为准。

## Git 与工作区

- 主线、集成分支和 GB10 以当前 Git 与远端实测为准；2026-10-29 的治理起点及历史结果见 [治理与资产地图](../docs/governance/2026-10-29_research_neat_closeout.md)。
- GB10 主树的 Loop B 测试日志可能持续更新；非本次研究改动，不回滚或提交。本机集成 worktree 及 GB10 C 审阅 worktree 的未跟踪文件已校验归档；历史 worktree 忽略文件仍保留。
- 历史账本各自独立；旧 340-token 差额与已记录的未知模型请求用量未解决，不能自行抹平或将账本简单相加。

## 运行及权限

科研 Agent 实验使用隔离环境与既有本地研究模型服务，不可由 Git 同步推断生产已部署。投稿、付款、签字、公开资料或外部联系须按用户和实际要求处理。运行模型或训练以具体目标、资源账本与项目权限为准，不从历史 prompt 推断现役预算。
