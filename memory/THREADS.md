# Open Decisions And Blockers

> 2026-11-11 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师及作者反馈 | Paper E与方向沟通稿已发送，等待反馈。第二篇Goal已由用户恢复，按短计划推进。 |
| Paper E 投稿办理 | ICINT首投、拒稿或撤稿后ICDAR；暂定 Zhonghua Wang、Jiali Ruan、Bin Hou、Yunxiao Zu（通讯），北邮电子工程学院，待团队终核。声明、学校凭证与费用待确认；ICDAR稿启用前处理双盲。作者邮箱不入Git。 |
| 第二篇当前推进 | 三策略批次冻结，20项离线检查通过，下一运行首臂核送达再续跑。跨项目信号后扩确认/训练，见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。 |
| 公开方法参照 | RethinkSkill仅协议接通；真实反馈、隔离和接受门仍待验证。[相关工作](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。 |
| 来源与参考资格 | Matplotlib/SymPy有真实成功来源，迁移未完成；[Astropy隔离批次](../research/agent_frontier_portfolio_20261029/results/ASTROPY_ISOLATED_CONTROLS_20261106.md)四臂完成、普通历史有目标成本信号。均已曝光开发题，形成成本另算。Sphinx来源仍失败，Requests参考冲突/EdgeBench跨架构未决。 |
| 成本及运行器 | 保留历史340-token差额、未知请求和权重标识。旧ContextBench标识绑定task/condition/seed，改造须迁移输出；跨机预算锁未实现。 |
| 记忆和自动调度 | 反思游标只验单进程；统一八层记忆、恢复队列和自动唤醒未实现。个人会话接入与生产调用另按授权；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | main代码/文档三端同步；恢复原型已入Git。GB10另有`logs/graph/pytest_loopb.txt`，7历史worktree保留；完整raw不在GitHub。 |
| 文档与 skill 存量 | doctor 0 errors/134既有warnings；3项docs时效警告及map旧提示保留。Windows CLAUDE加载未验。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态以宿主Goal控制面及用户最新明确指令为准；[STATE](STATE.md)是状态快照。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
