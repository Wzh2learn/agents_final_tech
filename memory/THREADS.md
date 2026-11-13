# Open Decisions And Blockers

> 2026-11-13 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师 / 开题 | 11-11反馈：Paper E老师先审后提交；当前优先开题报告与答辩。独立对话负责，研究点按问题、机制、形式化和验证组织，后两点是否合并待导师指导。 |
| Paper E 投稿办理 | 独立对话跟进，当前办理状态未复核。既有待项为账号、作者终核、邮箱/声明和提交授权；暂定王/阮/侯/俎、俎通讯、北邮电子工程学院。拒稿/撤稿后启用ICDAR；邮箱不入Git。 |
| 第二篇唯一下一步 | [20组已闭合](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#expansion-v1)，当前整体控制器停扩；[尸检](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#cross-batch-autopsy)回收条件动作及Actor续行。下一实现见证约束修订，同信息普通更新/简单规则对照，先新DEV再决定扩样，不先训练。 |
| GB10教学沉淀 | 开题答辩后，复用既有GB10/OpenCode、微调/蒸馏/优化和评估资料，为学弟学妹整理可复用教程及经典文献。当前仅登记，不建设新框架。 |
| 必要接入修复 | SQL源任务长行读取截断、正常终答未提交已定位；未来同类适配须统一完整输入/原生终答接口并先离线验证，保留本轮原始失败，不据此声称学习无效或补计成功。 |
| 公开方法参照 | [近邻表](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)已含HASP/SkillCAT/SCOPE：可执行干预、成败分歧和局部技能组链已有。匹配近邻比较未完成；一步选项不另算新方法。 |
| 来源与参考资格 | Matplotlib公开崩溃已解除，辅助函数较强验收未过；SymPy迁移未完成。[Astropy](../research/agent_frontier_portfolio_20261029/results/ASTROPY_ISOLATED_CONTROLS_20261106.md)普通历史有目标成本信号。均为曝光开发题，形成成本另算；Sphinx失败源及Requests/EdgeBench旧未决保留。 |
| 成本及运行器 | 最新845请求无新未知，累计中的8旧未知预留2,097,152。预算停原生轨迹保存已修，旧缺失不回填；本批20/20原生重放/公开缓存匹配。缓存异常不推算非缓存费；历史340-token差额及跨机预算锁未闭合。 |
| 记忆和自动调度 | 反思游标只验单进程；统一八层记忆、恢复队列和自动唤醒未实现。个人会话接入与生产调用另按授权；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | 本轮本机HTTPS推送成功，GB10经验证bundle对齐；SSH22/443为网络超时，先用HTTPS，GB10网络失败时用bundle，不重配密钥。保留LoopB日志/7历史worktree，完整raw不在GitHub。 |
| 文档与 skill 存量 | 11-13复核doctor仍1 error/135 warnings：error在开题对话未提交skill，不代改；map仍1组pdf重复/27提示，docs仍4项时效提醒。退出契约已在7836c893分发，本批未改skill。Windows CLAUDE加载未验。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态以宿主Goal控制面及用户最新明确指令为准；[STATE](STATE.md)是状态快照。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
