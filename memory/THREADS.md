# Open Decisions And Blockers

> 2026-11-09 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师及作者反馈 | Paper E 与方向沟通稿已发送；等待研究点划分、首投路线和成稿反馈。内部研究可继续，无需等待此项。 |
| Paper E 投稿办理 | ICINT 首投、拒稿或正式撤稿后 ICDAR；作者暂定 Zhonghua Wang、Jiali Ruan、Bin Hou、Yunxiao Zu（通讯），北邮电子工程学院。团队终核、声明、许可、学校凭证与费用须在正式办理时确认。ICDAR 工作稿仍有致谢，启用前处理双盲。作者邮箱等私有字段不入 Git。 |
| 第二篇当前比较 | 提示式及代码筛查已闭合，停止同例调参。主攻行动后果监督的局部经验重构，不把交互loss当创新；需同数据/动作/反馈联合策略对照。134 valid_unseen保留。[现场](../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#direct-method)。 |
| 公开方法参照 | RethinkSkill仅协议接通；真实反馈、隔离和接受门仍待验证。[相关工作](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。 |
| 来源与参考资格 | Requests 此对题面/版本/gold 行为冲突，不继续该对模型比较；Sphinx/Django/SymPy 等旧现场按[历史证据目录](../docs/archive/2026-11-06_agent_research_context/README.md)查阅。新来源先核验实际原题、base/gold、回归与时间边界。EdgeBench x86→ARM 尚未确认。 |
| 成本及运行器 | 历史340-token差额、历史未知请求和部分权重标识保留。Requests/Astropy已有显式attempt；旧ContextBench标识仍绑定task/condition/seed，改造须迁移输出目录。跨机器预算锁未实现；当前是否在途查STATE，不能从本行推断。 |
| 记忆和自动调度 | 反思游标只验单进程；统一八层记忆、恢复队列和自动唤醒未实现。个人会话接入与生产调用另按授权；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | 三端仅main，旧树独有产物及Loop B日志保留；分享前核许可和私有面。 |
| 文档与 skill 存量 | doctor 0 errors/134既有warnings；3项docs时效警告及map旧提示保留。Windows CLAUDE加载未验。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态只查[STATE](STATE.md)及用户最新明确指令。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
