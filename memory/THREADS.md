# Open Decisions And Blockers

> 2026-11-08 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师及作者反馈 | Paper E 与方向沟通稿已发送；等待研究点划分、首投路线和成稿反馈。内部研究可继续，无需等待此项。 |
| Paper E 投稿办理 | ICINT 首投、拒稿或正式撤稿后 ICDAR；作者暂定 Zhonghua Wang、Jiali Ruan、Bin Hou、Yunxiao Zu（通讯），北邮电子工程学院。团队终核、声明、许可、学校凭证与费用须在正式办理时确认。ICDAR 工作稿仍有致谢，启用前处理双盲。作者邮箱等私有字段不入 Git。 |
| 第二篇当前比较 | 新3任务/8槽已闭合且C复核；无成功交叉，不训练选择器。下一步一次直接动作接口诊断，再据结果扩独立任务。见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。 |
| 公开方法参照 | RethinkSkill 仅完成协议级接入；需合格真实反馈、训练/验证/目标隔离及接受门，才能形成方法比较。[相关工作](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。 |
| 来源与参考资格 | Requests 此对题面/版本/gold 行为冲突，不继续该对模型比较；Sphinx/Django/SymPy 等旧现场按[历史证据目录](../docs/archive/2026-11-06_agent_research_context/README.md)查阅。新来源先核验实际原题、base/gold、回归与时间边界。EdgeBench x86→ARM 尚未确认。 |
| 成本及运行器 | 历史 340-token 差额、在途请求及部分模型权重标识保持未知。Requests/Astropy 已有显式 attempt；三个旧 ContextBench runner 的标识仍绑定 task/condition/seed，改造须同时迁移实际输出目录。跨机器预算锁未实现。 |
| 记忆和自动调度 | 反思游标只验证单进程；尚无统一八层记忆、恢复队列或持续自动唤醒。个人会话接入、身份/归属和生产反思调用均不能由已有摘要功能推定已授权或实现。见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | GB10 7 个历史 worktree 内有独有日志/模型等忽略产物，继续保留；Loop B 日志不回滚。对外分享前须核查 Paper E 私有复现包、FinRank 非商用数据及代码许可；远端可见性未核实。 |
| 文档与 skill 存量 | C9已定向同步并核对本机、GB10各两安装副本；不是全库重验。既有skill-doctor0 errors/134 warnings与map记录保留。文档与实际安装按发布终态核，见[历史复核](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_TEXT_AGENT_20261106.md#expert-review)。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态只查[STATE](STATE.md)及用户最新明确指令。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
