# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；接管价值备选已完成固定64确认，保留实际纠正收益，继续提炼增量机制。首分叉微调线、无增量四算子生成器及153扩样配方停止；不打包或逐文件核SHA。
- **研究阶段**：确认64：首轮/普通34、旧成对39；主18接管效用42、风险43、单状态/随机41。效用相对普通8胜0负，相对风险1胜2负；多状态仍有局部收益，不能把风险43替换成主方法。DEV41与新57的35保留。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#confirmation64-v1)。
- **实际运行 / 预算**：已结算本地FinQA6,169POST/25,834,794＋12未知393,216；校内5,977POST/55,385,441＋11未知2,883,584，合58,269,025/10亿。GPU含inline首失败累计5,120更新/9,133前向，HF619前向/960,068输入tokens；新v2在途另记，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：inline_acquisition_v2父284507/24638858运行：原96教师/252状态＋121回放，434更新后自动跑原DEV64，程序后同响应输出接管价值，取消额外分类前向；缓存教师、8/12/18预算固定。v1失败3更新已计，64确认始终禁入训练/调参。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：确认短回执已同步本机，raw留GB10。确认HF与27B启动重叠的计时偏差保留，停止逻辑已修。inline父顺序占GPU、32GiB余量，运行中卸载27B、收尾自动恢复；无第二实验或模型并跑。数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
