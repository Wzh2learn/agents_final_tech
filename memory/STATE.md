# Current State

> 2026-11-15 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；开发32题首分叉负方向/成功上下文均14、普通11、步骤偏好10。四方案已冻结，正验证64个新报告，训练不重跑。
- **研究阶段**：6种训练方案的开发对照已齐；主候选保留语义纠正信号，与成功上下文同分但成功题不同，不再围绕32题加门控。[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#expanded-boundary-v1)。
- **实际运行 / 预算**：FinQA闭合1,818POST/7,966,636已知＋2未知（65,536预留）；新对照134POST/572,707tokens。校内总账仍5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)；运维55,809另账。
- **下一交付**：64报告首轮已完成，四方案各64次复查进行中；总320次执行，非320独立报告。协议90b86595不变。TAT-QA32原始算术题已完成CPU准备，尚无Agent/训练。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：监督748348；阶段、子进程和进度只读`confirmation_v1/PIPELINE_LIVE.json`。27B暂卸，32GiB/单权重保护、批后恢复。FinQA/TAT-QA准备包6e72d21c/97f8521c均双份，非完成结果。其他对话/LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
