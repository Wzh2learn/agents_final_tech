# Open Decisions And Blockers

> 2026-11-14 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师 / 开题 | 11-11反馈：Paper E老师先审后提交；当前优先开题报告与答辩。独立对话负责，研究点按问题、机制、形式化和验证组织，后两点是否合并待导师指导。 |
| Paper E 投稿办理 | 独立对话跟进，当前办理状态未复核。既有待项为账号、作者终核、邮箱/声明和提交授权；暂定王/阮/侯/俎、俎通讯、北邮电子工程学院。拒稿/撤稿后启用ICDAR；邮箱不入Git。 |
| 第二篇唯一下一步 | Goal active；FinQA 8题采集与7失败教师接续已闭合，6条成功纠正可导出。先剥离参考标签、定义字段token位置，再做同数据普通/加权LoRA和新报告验证，见[计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。 |
| GB10教学沉淀 | 开题答辩后，复用既有GB10/OpenCode、微调/蒸馏/优化和评估资料，为学弟学妹整理可复用教程及经典文献。当前仅登记，不建设新框架。 |
| 必要接入修复 | SQL源任务长行读取截断、正常终答未提交已定位；未来同类适配须统一完整输入/原生终答接口并先离线验证，保留本轮原始失败，不据此声称学习无效或补计成功。 |
| 公开方法参照 | [近邻表](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)用于借鉴与比较；恢复SFT、片段监督、能力保留可组合。需确定一条具体差异与消融，匹配近邻实验尚未完成。 |
| 来源与参考资格 | 历史代码与客服按[知识索引](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)保留。新增Astropy14182仅CPU控制完成，Matplotlib25079收集警告未解，无Agent/训练；不作金融主线前置。 |
| 成本及运行器 | 校内50,815,217已知＋2,621,440未知预留不变；新FinQA本地93POST/428,110tokens，未知0；27B启动失败0POST及240次自有health GET另列。既有本地216/1,496,913及96更新不混计。 |
| 记忆和自动调度 | 反思游标只验单进程；统一八层记忆、恢复队列和自动唤醒未实现。个人会话接入与生产调用另按授权；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | FinQA采集闭合，自有模型均停止，原始证据保留。提交本轮研究代码/状态；其他对话Paper E/开题WIP、LoopB/历史worktree保持原位。 |
| 文档与 skill 存量 | 机制知识和现役入口已收敛；本次仅只读doctor/map，不安装/分发新skill。既有WIP缺陷与历史warning单列；不让存量全库治理阻塞后续机制研究。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态以宿主Goal控制面及用户最新明确指令为准；[STATE](STATE.md)是状态快照。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
