# Open Decisions And Blockers

> 2026-11-10 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师及作者反馈 | Paper E 与方向沟通稿已发送；等待研究点划分、首投路线和成稿反馈。内部研究可继续，无需等待此项。 |
| Paper E 投稿办理 | ICINT首投、拒稿或撤稿后ICDAR；暂定 Zhonghua Wang、Jiali Ruan、Bin Hou、Yunxiao Zu（通讯），北邮电子工程学院，待团队终核。声明、学校凭证与费用待确认；ICDAR稿启用前处理双盲。作者邮箱不入Git。 |
| 第二篇当前方法边界 | Recuris已覆盖进度工作记忆、反馈定位、经验局部修补、验证门控和同题适配；其Terminal-Bench同预算下适配53/87、冻结记忆重试51/87（p=0.774）。VCE-Skill已覆盖公共技能版本变化经验。Matplotlib一次冻结回归仍未作因果识别，普通反馈复跑可修复。暂停“反馈驱动局部修订”候选的模型实验；真实软件/API版本变化中按行为依赖更新经验、同时保留不可回滚进度，现仅是待查场景差异。先证明不同于近邻及版本检查/全量回归的算法决策，并找到未曝光可评分样本；否则换题，不重跑曝光目标。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)和[相关工作](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。
| 公开方法参照 | RethinkSkill仅协议接通；真实反馈、隔离和接受门仍待验证。[相关工作](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。 |
| 来源与参考资格 | [Sphinx8282→8127](../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#sphinx-新来源公开问题与实际运行11-09)两题base/gold与回归已核；8282实际Agent和反馈提案未通过，8127未进行模型迁移实验。Requests旧对存在参考冲突；EdgeBench跨架构未确认。 |
| 成本及运行器 | 保留历史340-token差额、未知请求和权重标识。旧ContextBench标识绑定task/condition/seed，改造须迁移输出；跨机预算锁未实现。 |
| 记忆和自动调度 | 反思游标只验单进程；统一八层记忆、恢复队列和自动唤醒未实现。个人会话接入与生产调用另按授权；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | 三端仅main，旧树独有产物及Loop B日志保留；分享前核许可和私有面。 |
| 文档与 skill 存量 | doctor 0 errors/134既有warnings；3项docs时效警告及map旧提示保留。Windows CLAUDE加载未验。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态以宿主Goal控制面及用户最新明确指令为准；[STATE](STATE.md)是状态快照。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
