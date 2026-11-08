# Open Decisions And Blockers

> 2026-11-08 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师及作者反馈 | Paper E 与方向沟通稿已发送；等待研究点划分、首投路线和成稿反馈。内部研究可继续，无需等待此项。 |
| Paper E 投稿办理 | ICINT 首投、拒稿或正式撤稿后 ICDAR；作者暂定 Zhonghua Wang、Jiali Ruan、Bin Hou、Yunxiao Zu（通讯），北邮电子工程学院。团队终核、声明、许可、学校凭证与费用须在正式办理时确认。ICDAR 工作稿仍有致谢，启用前处理双盲。作者邮箱等私有字段不入 Git。 |
| 第二篇当前比较 | 同BF16 F/O/R新12题/36槽运行中，先查STATE及私有进程票据/逐槽回执，禁止重启。结束核36槽原生结果、实际采样/费用及服务恢复，再作裁决；优越性前补同面板普通历史。见[资产入口](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)。 |
| 公开方法参照 | RethinkSkill 仅完成协议级接入；需合格真实反馈、训练/验证/目标隔离及接受门，才能形成方法比较。[相关工作](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。 |
| 来源与参考资格 | Requests 此对题面/版本/gold 行为冲突，不继续该对模型比较；Sphinx/Django/SymPy 等旧现场按[历史证据目录](../docs/archive/2026-11-06_agent_research_context/README.md)查阅。新来源先核验实际原题、base/gold、回归与时间边界。EdgeBench x86→ARM 尚未确认。 |
| 成本及运行器 | 历史340-token差额、历史未知请求和部分权重标识保留。Requests/Astropy已有显式attempt；旧ContextBench标识仍绑定task/condition/seed，改造须迁移输出目录。跨机器预算锁未实现；当前是否在途查STATE，不能从本行推断。 |
| 记忆和自动调度 | 反思游标只验证单进程；尚无统一八层记忆、恢复队列或持续自动唤醒。个人会话接入、身份/归属和生产反思调用均不能由已有摘要功能推定已授权或实现。见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | SSH恢复，三端main已重对齐，GB10 Loop B日志保留；18个`archive/20261108/*`与7棵含独有忽略产物的旧树保留。本机CLAUDE为Windows链接占位、加载未验。分享前核许可及私有面。 |
| 文档与 skill 存量 | 本轮doctor 0 errors/134既有warnings，本机101安装项无漂移；GB10沿用前轮记录，待重连复验。map的1个同名组/27条疑似引用不自动清理。保留3项docs时效警告；Windows CLAUDE链接与更早规则扫描边界见历史记录。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态只查[STATE](STATE.md)及用户最新明确指令。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
