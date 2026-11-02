# Current State

> 2026-11-02 | 当前短状态；证据与导航见 [科研入口](../docs/research/README.md)，未决事项见 [THREADS](THREADS.md)。2026-10-29 治理前的完整原文见 [历史快照](archive/STATE_2026-10-29_pre_neat.md)，其中相对链接沿用原文件位于 memory/ 时的基址。

## 科研与论文

- **导师阶段确认**：2026 年 11 月 5 日前拟就学位方向、Paper E 投稿计划和已有研究与导师沟通；[导师沟通稿](../research/advisor_direction_review_20261102/ADVISOR_BRIEF_20261102.md)是当前讨论入口，旧导师一页稿和旧学位骨架仅为历史。该稿中的三个研究点为拟议结构，尚未取得导师确认。
- **Paper E**：现役 [ICINT 短稿](../research/paper_e_publication_route_20261028/paper_e_icint_draft.md)、[4 页审阅 PDF](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)及[文档分析定位的 ICDAR 备投工作稿](../research/paper_e_publication_route_20261028/ICDAR_ADAPTATION_RETURN_20261101.md)，路线及限制见[投稿计划](../research/paper_e_publication_route_20261028/PUBLICATION_PLAN_ZH.md)。三案例测量审计，先准备 ICINT，拒稿或正式撤稿后再考虑 ICDAR；[机器审读与数值更正](../research/paper_e_publication_route_20261028/ICINT_AI_REVIEW_RETURN_20261031.md)不是专家或同行评审。作者已提供署名与通讯作者信息，私有记录已准备；作者团队终核、AI 声明、许可和独立审阅仍未完成。[v6](../research/paper_e_agent_evidence_20261029/paper_e_review_revision_v6.md)是历史详细稿。
- **第二篇和学位**：以 IJCNN 2027 为探索目标，重点是 Agent 从反馈/经验学习和变化环境下的技能适配；训练、蒸馏、记忆、规划协作及可靠执行仍可按证据调整，[长期研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)。[来源见证与人工修订试验](../research/agent_frontier_portfolio_20261029/SKILL_VERIFICATION_RETURN_20261101.md)显示单条风险建议可被局部修订，另一条旧范围条件仍可能被沿用；普通历史与确定性工具基线也能完成当前筛选，经验方法增量尚未确立。硕士目标 2027 年 10 月送审，具体日期未知。
- **新工作流试验**：[DBSCAN 距离变化](../research/agent_frontier_portfolio_20261029/DBSCAN_AGENT_PILOT_RETURN_20261102.md)已执行三条真实 Agent 轨迹及透明规则：目标无历史、源历史和规则均交付同样结果；源历史组读取并修改旧程序，但单次调用和报告 token 更多。该结果仅属同源开发材料，不能证明一般方法收益；下一阶段见[研究计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **最新资产复核**：[离线复算与尸检](../research/asset_revalidation_20261029_v1/REVALIDATION_AND_AUTOPSY.md)核对 Paper E 冻结结果、迁移验证合同、Agent 单任务的 2,000 行产物及 MA-CERD 动作集合；均为事后复核，不是独立来源确认。
- **解释边界**：BEIR 为研究者自建运行而非官方榜；FinRank 的部分身份结果为源码知情事后复现；未标注不等于不相关，统计不显著不等于相等。旧 R/E、exact-cache、FinRank H/K 等具体面板停止不等于相关一般方向无效。以日期更正和原证据为准。

## Git 与工作区

- 主线、集成分支和 GB10 以当前 Git 与远端实测为准；2026-10-29 的治理起点及历史结果见 [治理与资产地图](../docs/governance/2026-10-29_research_neat_closeout.md)。
- GB10 主树的 Loop B 测试日志可能持续更新；非本次研究改动，不回滚或提交。本机集成 worktree 及 GB10 C 审阅 worktree 的未跟踪文件已校验归档；历史 worktree 忽略文件仍保留。
- 历史账本各自独立；旧 340-token 差额与已记录的未知模型请求用量未解决，不能自行抹平或将账本简单相加。

## 运行及权限

科研 Agent 实验使用隔离环境与既有本地研究模型服务，不可由 Git 同步推断生产已部署。投稿、付款、签字、公开资料或外部联系须按用户和实际要求处理。运行模型或训练以具体目标、资源账本与项目权限为准，不从历史 prompt 推断现役预算。
