# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：效用/风险原生DEV均41，单状态对照40；共同教师池复现41/41/40。多状态多恢复1题，12接管效用40/风险39的局部信号保留；固定双头混合40，停止组合搜索。转剩余57个未使用TRAIN来源的冻结模型前向开发验证，预留64隔离。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#shared-teacher-value-v1)。
- **实际运行 / 预算**：已结算本地FinQA5,686POST/23,910,452＋12未知393,216；校内5,747POST/54,323,213＋11未知2,883,584，合57,206,797/10亿。单状态新增7校内POST/29,288，未知0；GPU累计4,569更新/8,094前向，三HF头192前向/284,855tokens。新57本地采集在途另记，复用响应不重复充账，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：forward_sources57_v1父59528/23057236；顺序首轮、普通SFT、旧37原生执行。等待预测64609、教师等待67217：本地完成后冻结三选择器和固定随机的16接管决策，再生成同57原始现场的公共教师池并比较7/10/16预算。57结果闭合前不训练；不是最终确认，新64不启用。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：三组权重/短回执已同步本机。当前57来源单8B顺序采集、32GiB保护；本地采集及HF预测各结束后恢复27B，教师为校内API。代码/短状态本批同步，raw/数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
