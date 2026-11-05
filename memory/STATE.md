# Current State

> 2026-11-05 | 当前短状态；证据与导航见 [科研入口](../docs/research/README.md)，未决事项见 [THREADS](THREADS.md)。2026-10-29 治理前的完整原文见 [历史快照](archive/STATE_2026-10-29_pre_neat.md)，其中相对链接沿用原文件位于 memory/ 时的基址。

## 科研与论文

- **当前节奏**：用户已将 Paper E 审阅稿和导师沟通稿发送给老师，等待导师和作者团队反馈。第二阶段科研 Goal 已暂停，待用户确认恢复；架构与 skill 基建升级已完成本批离线验证。研究现场见[第二阶段计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。Paper E 尚未投稿，不把内部准备等同于录用或发表。
- **导师阶段确认**：用户于 2026 年 11 月 5 日前已发送[导师沟通稿](../research/advisor_direction_review_20261102/ADVISOR_BRIEF_20261102.md)及 Paper E 审阅 PDF；等待对学位方向、研究点、投稿路线与学校成果认定的反馈。该稿中的三个研究点为拟议结构，尚未取得导师确认。
- **Paper E**：现役 [ICINT 短稿](../research/paper_e_publication_route_20261028/paper_e_icint_draft.md)、[4 页审阅 PDF](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)及[文档分析定位的 ICDAR 备投工作稿](../research/paper_e_publication_route_20261028/ICDAR_ADAPTATION_RETURN_20261101.md)，路线及限制见[投稿计划](../research/paper_e_publication_route_20261028/PUBLICATION_PLAN_ZH.md)。Gemini 建议经[既有数据与代码核对](../research/paper_e_publication_route_20261028/ICINT_CLAIM_EVIDENCE_REVIEW.md)后整合，匹配阈值下逐表和逐注入结果一致；另用 SciPy 与 statsmodels 对已存逐查询数据独立实现复算，30 组显著性判断一致。后者不是新样本或人工统计评审。ICDAR 工作稿仍含致谢，尚非合规双盲稿。先准备 ICINT，拒稿或正式撤稿后再考虑 ICDAR。作者已提供署名与通讯作者信息，私有记录已准备；作者团队终核、AI 声明、许可和独立审阅仍未完成。[v6](../research/paper_e_agent_evidence_20261029/paper_e_review_revision_v6.md)是历史详细稿。
- **第二篇和学位**：以 IJCNN 2027 为探索目标，重点是 Agent 从反馈/经验学习和变化环境下的技能适配；训练、蒸馏、记忆、规划协作及可靠执行仍可按证据调整，[长期研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)。[来源见证与人工修订试验](../research/agent_frontier_portfolio_20261029/SKILL_VERIFICATION_RETURN_20261101.md)显示单条风险建议可被局部修订，另一条旧范围条件仍可能被沿用；普通历史与确定性工具基线也能完成当前筛选，经验方法增量尚未确立。硕士目标 2027 年 10 月送审，具体日期未知。
- **Agent 基建升级**：[现役架构说明](../docs/17_Graph_Engineering_多层Loop设计.md#基建升级事实记忆与协作2026-11-05)记录三项上游源码版本和记忆分层。现有 `neat-freak`、`spec-first` 按项目规则升级；新增可选的来源溯源上下文包，A/C 派发器防止相同任务角色覆盖旧回执，情景记忆保护会话元数据，并以单进程消息 ID 游标修复滑动窗口内重复/停更。它们均不等于跨进程永久记忆、持续自动调度或完整八层记忆；实际分发与验证以本次回执和命令为准。
- **Agent 开发证据**：[地震板块对照](../research/agent_frontier_portfolio_20261029/EARTHQUAKE_AGENT_DEVELOPMENT_20261103.md)有一次生成 skill 的正向距离线索，也有不稳定运行；[连续办公任务](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)中直接执行、历史和 skill 均完成目标，原评分还漏检一类错误 slug。[DBSCAN](../research/agent_frontier_portfolio_20261029/DBSCAN_AGENT_PILOT_RETURN_20261102.md)与[认证任务](../research/agent_frontier_portfolio_20261029/AUTH_TRANSFER_AUTOPSY_20261102.md)目前也没有识别出可靠方法增量。下一步寻找能区分强基线的自然变化任务，建立多来源和重复对照。
- **股票可视化格式变化**：[现役计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)记录 CSV 源、JSON/TSV 目标的无历史、历史、生成 skill 和事后反馈对照；各格仅一次，同属一个已曝光工作流族。skill 未稳定超过无历史或研究者的透明适配；一条目标未完成文件交付。历史读取的实际截断与上游 tooltip 测试的实现敏感性已分别用逐行对照和可执行反例核实。Agent 本身没有浏览器，成本与边界均在计划中单列；尚无跨来源方法收益。
- **SkillFlow 对账任务**：[现役计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)记录两个同族合成 PDF/Excel 任务及一个单元格变化的过时示例变体。无历史、真实源历史、生成 skill 在目标原题及变体的单次输出均与当前输入独立复算一致；变体不能用旧测试答案评分。目标条件各仅一次，无法判断稳定效率差或方法增益。
- **EvoClaw 配置迁移**：[现役计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)记录公开合成任务的评分反例及真实 Agent 开发对照：95 个类型标签全错的构造产物仍通过 `30/30` 原检查；无历史和源历史各一次均正确完成四个目标文件。不是已观察到的 Agent 受错误反馈影响，也没有方法增量。后续优先资格验证真实项目任务。
- **真实项目 Agent 开发**：[aiohttp 对照](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)的目标条件计划公开测试 `13/14`，但补充检查发现正常退出与异常传播缺陷。SymPy 单次 skill 的正向线索在修复依赖后的同题重复中未稳定：无历史、中性计划与条件计划各两次 `15/15`、`4/4`，完整 skill 为 `1/15`、`10/15`，补充检查一次导入失败、一次 `2/4`；正常退出和自写测试通过均不能替代独立检查。两项目需求由 benchmark 构造；上述为开发观察，未确立方法优势，继续拓展真实问题与来源。
- **自然问题与历史来源**：[SWE-ContextBench 筛查](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)固定 300 个源任务、99 个目标任务和 102 条关联；6/102 对题面规范化后相同，一条公开源轨迹含目标修复后的 Git 提交摘要。SymPy 自然问题的无历史、源历史和生成 skill 目标各一次均未通过目标问题测试、事后 `84/84` 回归通过；历史达到请求上限，skill 达墙时上限，不能推断稳定方法效果。源经验压缩未清楚保留最终失败状态，是值得进一步验证的具体线索。
- **第二自然项目**：Django 源和目标无历史 Agent 均达到请求上限、未通过问题测试；目标回归 `15/17`。历史和生成 skill 目标臂未修复目标且未改源码；原序历史只读到 `73/82` 行，遗漏第 79 行的源反馈。同内容反馈前置后，目标臂读到源反馈但达到请求上限、未改源码、问题测试仍报错，回归 `17/17`。暂停前启动的同候选中性续修臂已结束，目标仍报错、回归仍有 2 项报错；反馈臂未运行，不能比较反馈效果。1 条源回归记录是说明文字、未映射。[详情](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **最新资产复核**：[离线复算与尸检](../research/asset_revalidation_20261029_v1/REVALIDATION_AND_AUTOPSY.md)核对 Paper E 冻结结果、迁移验证合同、Agent 单任务的 2,000 行产物及 MA-CERD 动作集合；均为事后复核，不是独立来源确认。
- **解释边界**：BEIR 为研究者自建运行而非官方榜；FinRank 的部分身份结果为源码知情事后复现；未标注不等于不相关，统计不显著不等于相等。旧 R/E、exact-cache、FinRank H/K 等具体面板停止不等于相关一般方向无效。以日期更正和原证据为准。

## Git 与工作区

- 主线、集成分支和 GB10 以当前 Git 与远端实测为准；因 GitHub SSH 公钥认证失败，暂由校验过的 Git bundle 对齐本机与 GB10，GitHub 待认证恢复后补推。2026-10-29 的治理起点及历史结果见 [治理与资产地图](../docs/governance/2026-10-29_research_neat_closeout.md)。
- 2026-11-05 本机重复集成 worktree 与 GB10 同 HEAD 的 `paper_e_research_20261028` 已核实无独有内容后移除；集成分支引用保留。GB10 另有 7 个历史 worktree，含被忽略的结果、日志或模型文件，暂时保留。GB10 主树 Loop B 测试日志可能持续更新，不回滚或提交。
- 历史账本各自独立；旧 340-token 差额与已记录的未知模型请求用量未解决，不能自行抹平或将账本简单相加。

## 运行及权限

科研 Agent 实验使用隔离环境与既有本地研究模型服务，不可由 Git 同步推断生产已部署。投稿、付款、签字、公开资料或外部联系须按用户和实际要求处理。运行模型或训练以具体目标、资源账本与项目权限为准，不从历史 prompt 推断现役预算。
