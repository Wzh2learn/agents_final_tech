# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：Step1完成：旧37探针恢复1/12、27B7/12，均保持8/8；96组新TRAIN形成30个原生通过修复。Step2首候选完成501更新，DEV64为33/64，64题全KEEP，无恢复或错改。TRAIN原生及HF直解同样偏KEEP；强制中性前缀能产生正确单位补丁，也能错改正确程序。[结果与归因](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#structural-patch-candidate-v1)。
- **实际运行 / 预算**：已结算本地FinQA5,237POST/22,166,718已知＋11未知360,448；含首候选、诊断、接口失败、弱提案32题和已停27B工具循环。在途27B提案/路由另据LIVE结算。校内5,393POST/52,678,540已知＋11未知2,883,584，合55,562,124/10亿；TAT不变。训练及HF/CPU编码单列。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：弱8B提案TRAIN32恢复0/错改5，停止加训和扩采。已切强备选：同TRAIN现场27B单次JSON补丁，首11题恢复1/错改0；有恢复则完成96源，CPU轻量模块预测恢复概率减错改概率，TRAIN分组交叉拟合阈值后冻结DEV路由，选中题才实际OpenCode接管。新64/DEV监督不入训练，净增至少3题再补确认。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：27B采集见correction_value_27b_v1/LIVE.json（PID2602854/ticks19298323）；correction_router_v1/CHAIN_LIVE.json（PID2607241/ticks19320168）等待其结束后接续CPU训练及DEV执行。弱提案correction_value_v1已结束；32GiB保护，27B为唯一GPU服务。raw留GB10，Paper E/开题/LoopB WIP不混入。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
