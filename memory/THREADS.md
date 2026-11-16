# Open Decisions And Blockers

> 2026-11-16 | 只留未决与下一动作；当前实验数值见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，不在这里重抄实验日志。

| 事项 | 下一动作 / 边界 |
| --- | --- |
| 导师 / 开题 | 11-11反馈：Paper E老师先审后提交；当前优先开题报告与答辩。独立对话负责，研究点按问题、机制、形式化和验证组织，后两点是否合并待导师指导。 |
| Paper E 投稿办理 | 独立对话跟进，当前办理状态未复核。既有待项为账号、作者终核、邮箱/声明和提交授权；暂定王/阮/侯/俎、俎通讯、北邮电子工程学院。拒稿/撤稿后启用ICDAR；邮箱不入Git。 |
| 第二篇唯一下一步 | 成对37对普通33、半权重32。DeepSeek同64为38，6误改均输出尺度；补每状态等权SFT，确认前统一比例输出说明，然后冻结53及TAT增强。不追加系数矩阵。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。 |
| GB10教学沉淀 | 开题答辩后，复用既有GB10/OpenCode、微调/蒸馏/优化和评估资料，为学弟学妹整理可复用教程及经典文献。当前仅登记，不建设新框架。 |
| 必要接入修复 | SQL源任务长行读取截断、正常终答未提交已定位；未来同类适配须统一完整输入/原生终答接口并先离线验证，保留本轮原始失败，不据此声称学习无效或补计成功。 |
| 公开方法参照 | 已有普通纠正、成功上下文和步骤偏好的核心适配对照；新增来源后继续同条件比较，不扩整张文献矩阵，不称完整原法复现。差异与消融按[近邻表](../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)核对。 |
| 来源与参考资格 | 历史代码与客服按[知识索引](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)保留。新增Astropy14182仅CPU控制完成，Matplotlib25079收集警告未解，无Agent/训练；不作金融主线前置。 |
| 成本及运行器 | 本地4,208POST/17,942,361已知，未知9；校内新增111POST/493,462，累计5,133POST/51,435,878已知，未知10预留2,621,440。全部批次已退出，27B恢复ready；旧未知/失败/缓存账保留。 |
| 记忆和自动调度 | 反思游标只验单进程；统一八层记忆、恢复队列和自动唤醒未实现。个人会话接入与生产调用另按授权；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。 |
| 工作区与分享 | 旧包保留；主f5a60b1b、减权1f87ea50、TRAIN教师642792ef、同64教师d509b63b双份逐文件核SHA。37/64及各对照仍为开发，待强基线/确认。Paper E/开题及LoopB的WIP保留。 |
| 文档与 skill 存量 | 机制知识和现役入口已收敛；本次仅只读doctor/map，不安装/分发新skill。既有WIP缺陷与历史warning单列；不让存量全库治理阻塞后续机制研究。 |
| 历史生产事项 | PostgreSQL/Loop B/kiosk 并发、M1 OCR 等未复验项见[更早台账](archive/THREADS_2026-10-21_pre_workspace_governance.md)，此次文档整理不关闭它们。 |

科研运行状态以宿主Goal控制面及用户最新明确指令为准；[STATE](STATE.md)是状态快照。较长旧台账见[治理前快照](archive/THREADS_2026-11-06_pre_context_neat.md)；停止具体候选不等于关闭新来源研究。2027 年 10 月具体送审日仍待学校确定。
