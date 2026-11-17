# Current State

> 2026-11-18 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：paused，用户要求本批后深度对齐，不开下一轮。两阶段纠正＋状态条件接管主线保留；TAT迁移与FinQA全K已闭合。4B从未开训且取消，四算子/首分叉微调/CPU小头/153扩样封存；不打包或逐文件核SHA。
- **研究阶段**：确认64：首轮/普通34、旧成对39；主18接管效用42、风险43、单状态/随机41。效用相对普通8胜0负，相对风险1胜2负；多状态仍有局部收益，不能把风险43替换成主方法。DEV41与新57的35保留。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#confirmation64-v1)。
- **实际运行 / 预算**：FinQA本地6,310POST/26,149,988＋76未知2,490,368不变；TAT本地累计372POST/1,359,784＋2未知65,536。校内总6,036POST/55,621,283＋11未知2,883,584，合58,504,867/10亿。GPU训练5,554更新/10,027前向不变，HF683前向/1,026,954输入；CPU旧计数缺口保留。[账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：FinQA全K/交叉病例及PNG/PDF完成。TAT32首轮1、普通5、成对7；成对相对普通修3误1，2为语义恢复。主K9价值/风险/随机11/13/13，次级K16为16/14/16，全教师19。教师59POST/235,842，0新增训练。当前只对齐讨论，确认64不重评新模型。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：TAT本地504677及教师509720均RETURNED且进程退出；27B守护525515/tick26027020及容器c7f249808f5c已核实运行，可用75.14GiB。短回执已存本机，raw留GB10；32GiB保护，计时偏差/未知用量保留，数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
