# Open Decisions And Blockers

> 2026-11-05 | 只列当前未决。历史原文见 [治理前快照](archive/THREADS_2026-10-29_pre_neat.md)，相对链接沿用原文件位于 memory/ 时的基址；科研当前状态见 [STATE](STATE.md)。

| 事项 | 当前状态与下一步 |
| --- | --- |
| 科研目标 | 第二阶段 Goal 已暂停，等待用户确认恢复；暂停期间不新启动模型实验或训练。恢复后按[第二阶段计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)核对导师反馈、现场和资源。 |
| 导师反馈 | 用户已向老师发送[方向与小论文进展讨论稿](../research/advisor_direction_review_20261102/ADVISOR_BRIEF_20261102.md)及 Paper E 审阅 PDF；等待对研究主线、后两点划分、投稿路线与学校成果认定的意见。 |
| Paper E 正文 | [ICINT 审阅稿](../research/paper_e_publication_route_20261028/paper_e_icint_draft.md)及 4 页 PDF 已按反馈更新摘要、排版和相关文献；[证据核对](../research/paper_e_publication_route_20261028/ICINT_CLAIM_EVIDENCE_REVIEW.md)保留数值与审阅边界。等待导师和作者团队意见，之后完成声明、匿名及许可终核。匹配原操作点的 `>=2` / `>=0.75` 与另一严格 `>` 网格必须区分。[ICDAR 工作稿](../research/paper_e_publication_route_20261028/ICDAR_ADAPTATION_RETURN_20261101.md)仍含 Acknowledgment，启用前须依双盲要求调整。 |
| 投稿与学位认定 | 用户选择 ICINT 首投、ICDAR 顺序备投，可到场参会；学校要求本人第一作者、北邮第一单位、方向相关，会议还需召开并宣读/张贴。2026-11-04 用户已确认暂定四位作者顺序及通讯作者，确认两名学生的北邮电子工程学院署名；私有投稿准备文件已更新并保存在仓库外。作者团队对最终顺序与成稿的确认仍待办理。AI 披露、专利、artifact 许可、2027 论文集出版信息、费用及正式提交仍待实际办理；不同时一稿多投。2027 年 10 月具体送审日未知。 |
| 第二篇 Agent 方法 | [长期研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)以 IJCNN 为目标，围绕经验反馈学习与变化任务技能适配。[来源见证与人工局部修订](../research/agent_frontier_portfolio_20261029/SKILL_VERIFICATION_RETURN_20261101.md)及 [DBSCAN 试验](../research/agent_frontier_portfolio_20261029/DBSCAN_AGENT_PILOT_RETURN_20261102.md)均未确立方法增量。[地震任务开发](../research/agent_frontier_portfolio_20261029/EARTHQUAKE_AGENT_DEVELOPMENT_20261103.md)出现一次 skill 辅助距离结果与独立界一致的积极线索，也出现同一 skill 的失败；股票格式变化的各臂及反馈对照同样没有稳定方法增量。[SkillFlow 对账族](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)目标原题与过时示例变体均被无历史、源历史和 skill 单次解对；未识别稳定方法优势，变体须按新输入评分。需在不同来源和重复运行上验证适用性、失败反馈及真实成本。EdgeBench 官方 51 项定义均声明 x86，GB10 为 ARM，跨架构可运行性尚未验证。 |
| Agent 来源扩展 | [EvoClaw 配置任务](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)中原评分漏检类型错误；无历史和源历史在目标四文件各一次均正确。[SWE-Skills-Bench](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)的 aiohttp 补充行为检查推翻了仅据 `13/14` 宣称条件计划更优；SymPy 在依赖修复后的同题重复中，无历史与两种计划均两次 `15/15`、`4/4`，原 skill 两次为 `1/15`、`10/15`，初次正向结果不稳定。相关任务是 benchmark 构造需求和本地 ARM 适配，下一步转向自然问题与不同来源，不据此宣称普遍 skill 退化。 |
| 自然任务及经验时序 | [SWE-ContextBench](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md) 的固定 Lite 来源提供真实问题对，一条公开源轨迹含目标后的修复提交摘要。SymPy 目标无历史、源历史及生成 skill 各一次均未通过目标问题测试、独立 Python 3.8 回归 `84/84`；历史达请求上限，skill 达墙时上限。skill 未清楚保留源任务最终失败状态；这是反馈保真度的开发线索，尚不是方法优势。 |
| Django 自然任务 | [固定源码与资格](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)已在 ARM 上完成源/目标问题正负控制与 `35/35`、`17/17` 可映射回归。目标无历史臂未修复且产生 2 项回归；历史/skill 臂未改源码、未修复。原序历史读取遗漏第 79 行反馈，同内容反馈前置后读到反馈但仍未修复且达到请求上限。同候选中性续修臂已运行，反馈臂未运行；恢复后核对现场和预算，再决定是否补做，不从未配对结果推断反馈效果。源另有 1 条非测试名未映射，公开旧轨迹不用于时间隔离经验。 |
| 资源账本 | 历史 340-token 差额、部分未完成 POST 用量、模型权重标识等仍未核实；继续分别记账，不能视作零。 |
| 长期记忆与自主调度 | [架构说明](../docs/17_Graph_Engineering_多层Loop设计.md#基建升级事实记忆与协作2026-11-05)区分项目状态、会话持久化、向量情景记忆与候选复习/反思；当前仍无已验证的统一八层记忆或恢复型自动队列。反思增量游标仅在单进程内生效，游标已滑出窗口或缺少稳定 ID 时跳过，存储响应丢失后的重试可能重复；现有反射代码配置外部模型接口，实际生产调用未核验，个人对话接入前需明确数据与授权范围。会话元数据约束不代替用户身份和资源归属认证。 |
| Git 与现场 | 本机旧集成 worktree 的 30 项及 GB10 C 审阅 worktree 的 3 项未跟踪文件此前已校验归档；2026-11-05 又移除了本机和 GB10 各一个已合并、只剩可重建缓存/报告的重复 worktree。GB10 另有 7 个历史 worktree，其 HEAD 均在 main 历史中，但忽略文件含 JSON、日志及模型权重，保留待逐项处理；Loop B 日志保持原状。[历史归档与实验复核](../research/asset_revalidation_20261029_v1/REVALIDATION_AND_AUTOPSY.md)。GitHub SSH 公钥认证仍未恢复；本机与 GB10 通过校验过的 Git bundle 对齐，待恢复后补推。 |
| 文档时效与 skill | 2026-11-05 文档 lint 为 0 fail、3 warn：两份 33/34 为项目明确冻结文档，另一份 `m1_coldstart_candidates.md` 仍待相关工作复验，不用仅改日期消警。本次已更新现有 `neat-freak` 与 `spec-first`；GB10 `sync_skills --check` 为 100 项一致，仓库 skill-doctor 为 0 errors、136 warnings，skill-map 报 1 组 `pdf` 同名和 27 条待判的类似引用，不能把候选全部当成真实断链。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 边界及其他未复验事项保持未知；见[更早快照](archive/THREADS_2026-10-21_pre_workspace_governance.md)，不能因归档宣称解决。 |

不得因记录停止某一候选就将新来源研究或用户已授权的科研一概关闭；也不得因新授权改写旧实验、参考或冻结账本。
