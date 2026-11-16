# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；保留执行反例纠正的语义收益，降低对正确程序的误改。保持投影未改善整体，下一步检验训练与部署动作的对齐。
- **研究阶段**：新64组追加128执行已全量闭合：普通34、原反例33、半权重33、投影32；投影修5/错改6。保留期间、分母及算式结构修复，停止扩投影版本，检查成功状态监督与实际提交动作。[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#retention-projection-v1)。
- **实际运行 / 预算**：FinQA累计3,952POST/16,943,529已知＋7未知预留229,376；本批另528更新/882显式前向/162额外梯度求值。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[成本](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。训练与HTTP分账。
- **下一交付**：同88组/147目标的动作对齐数据编译与普通/反例最小配对计划：训练公开提示及正确/错误状态目标对齐实际Final program提交，重新核对监督剂量；无新增教师或测试标签。余53未启用，TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：冻结代码4a5ee70e未变，训练66d6579d/结果1f9cd322双份逐文件核SHA。旧监督/训练/原生进程均退出；27B由1566839/tick11813490、boot b4166d98恢复，health GET200。当前无科研训练/评估在跑；单权重/32GiB保护，保留其他对话及LoopB。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
