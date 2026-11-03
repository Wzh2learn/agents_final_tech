# Open Decisions And Blockers

> 2026-11-03 | 只列当前未决。历史原文见 [治理前快照](archive/THREADS_2026-10-29_pre_neat.md)，相对链接沿用原文件位于 memory/ 时的基址；科研当前状态见 [STATE](STATE.md)。

| 事项 | 当前状态与下一步 |
| --- | --- |
| Gemini 审稿反馈 | 已收到完整修改稿和核查表，并经现有数据、代码和 GB10 离线重建选择性整合到 [Paper E 现役稿](../research/paper_e_publication_route_20261028/ICINT_CLAIM_EVIDENCE_REVIEW.md)。对指定折 21/24 相同注入已逐条证实；未解复现差异不预设原因。原始 AI 输出作为历史输入保留，不是同行评审。用户已恢复长期科研 Goal，后续按现役计划推进。 |
| 2026-11-05 前导师确认 | 将[方向与小论文进展讨论稿](../research/advisor_direction_review_20261102/ADVISOR_BRIEF_20261102.md)及当前 Paper E 审阅稿提供给导师；听取对研究主线、后两点划分、投稿路线与学校成果认定的意见。导师反馈尚未取得。 |
| Paper E 正文 | [ICINT 审阅稿](../research/paper_e_publication_route_20261028/paper_e_icint_draft.md)已结合 Gemini 建议更新并编译为 4 页；[当前证据核对](../research/paper_e_publication_route_20261028/ICINT_CLAIM_EVIDENCE_REVIEW.md)不替代独立统计、引文、匿名和许可复核。匹配原操作点的 `>=2` / `>=0.75` 与另一严格 `>` 网格必须区分。[ICDAR 工作稿](../research/paper_e_publication_route_20261028/ICDAR_ADAPTATION_RETURN_20261101.md)已同步正文，但仍含 Acknowledgment，尚不符合其双盲审稿稿禁止致谢的要求。 |
| 投稿与学位认定 | 用户选择 ICINT 首投、ICDAR 顺序备投，可到场参会；学校要求本人第一作者、北邮第一单位、方向相关，会议还需召开并宣读/张贴。用户已给出第一、第二作者及两位老师的英文姓名，确认两名学生的北邮电子工程学院署名，并指定暂定通讯作者；私有投稿准备文件保存在仓库外。最终作者顺序与作者团队对成稿的确认仍待办理。AI 披露、专利、artifact 许可、2027 论文集出版信息、费用及正式提交仍待实际办理；不同时一稿多投。2027 年 10 月具体送审日未知。 |
| 第二篇 Agent 方法 | [长期研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)以 IJCNN 为目标，围绕经验反馈学习与变化任务技能适配。[来源见证与人工局部修订](../research/agent_frontier_portfolio_20261029/SKILL_VERIFICATION_RETURN_20261101.md)在两个已暴露项目保持快照相对输出，未发现留存时间篡改，但另一处旧过滤仍被沿用。[DBSCAN 真实 Agent 试验](../research/agent_frontier_portfolio_20261029/DBSCAN_AGENT_PILOT_RETURN_20261102.md)中无历史、源历史及透明规则均完成目标；原测试存在白盒构造盲点，许可和上游固定环境仍待核实。尚未确立方法贡献；后续按[第二阶段计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)探索多族与真实反馈。 |
| 资源账本 | 历史 340-token 差额、部分未完成 POST 用量、模型权重标识等仍未核实；继续分别记账，不能视作零。 |
| Git 与现场 | 本机集成工作树 30 项和 GB10 C 审阅工作树 3 项未跟踪文件均已校验归档；历史 worktree 的忽略文件与 GB10 活动 Loop B 日志保留。[最新归档及实验复核](../research/asset_revalidation_20261029_v1/REVALIDATION_AND_AUTOPSY.md)。 |
| skill 分发 | 2026-11-01 本机和 GB10 的 `sync_skills --check` 均为 100 项一致。仓库 skill-doctor 为 0 errors、140 warnings（67 项字段顺序、73 项缺少显式完成证据），退出码 1；skill-map 报 1 组 `pdf` 同名和 27 条待判的类似引用，不能把候选全部当成真实断链。未自动修改 skills。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 边界及其他未复验事项保持未知；见[更早快照](archive/THREADS_2026-10-21_pre_workspace_governance.md)，不能因归档宣称解决。 |

不得因记录停止某一候选就将新来源研究或用户已授权的科研一概关闭；也不得因新授权改写旧实验、参考或冻结账本。
