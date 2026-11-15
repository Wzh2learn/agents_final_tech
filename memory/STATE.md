# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；保留执行错误分叉与状态绑定的纠正/保持部件，先统一纠正模块的程序提议/提交接口，再验证学习增量。
- **研究阶段**：88组三臂训练、42报告的252执行已闭合，普通/候选原生同13/42；文字方案回放14对13。共用提交接口两轮8次检查已闭合，第二轮4次均实际提交/有效；候选优势未成立，已冻结新64报告作同条件验证。[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#terminal-interface-v1)。
- **实际运行 / 预算**：已结算FinQA累计3,499POST/15,168,929已知＋7未知（229,376预留）；新64在途费用按wire保存，未计入此累计。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[成本](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。训练/CPU回放另账。
- **下一交付**：新64协议58db3ef3已启动：成功蒸馏首轮，普通/候选及原成功模型同现场复查，合256执行、上限3,072POST。完成后用`TEST_EXECUTION_ANALYSIS.py`全量重评分/对账；不新增训练/扫系数，TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：接口/格式01319f38三端对齐；ec1ea34d/fdb29f13双份。新批监督1405155/tick10697428、boot b4166d98运行中，当前8B，27B批后恢复；进度以私有`test_execution_v1/EVALUATION_LIVE.json`为准。32GiB保护/单权重，其他对话及LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
