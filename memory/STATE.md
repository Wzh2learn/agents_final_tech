# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；深化执行错误分叉与状态绑定的纠正/保持。旧有效片段继续复用；收尾重写的4/32版本已停止，当前规则保留，扩大真实训练来源。
- **研究阶段**：保留v2的15/32对14及13/13保持信号；扩样已编译88组（两条冲突监督暂挂），普通/候选147目标逐token相同，成功蒸馏176目标。[方案](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#expanded-state-v1)。
- **实际运行 / 预算**：FinQA已闭合2,961POST/12,701,094已知＋7未知（229,376预留）；本轮教师100POST/496,680、未知0。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)；新训练192更新/322前向另账。
- **下一交付**：扩样首试被32GiB保护中止；完整输入下减少无损失前缀词表投影，55项/39子测试通过。新目录/同数据三臂计划df0cc72a、d26c394c，准备包fb7594d1双份，尚未启动。完成后新报告留出评估，TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：已发布代码00931098；扩样旧训练进程已结束，31.9605GiB触发SIGTERM，完成计数28更新/45前向/4,086监督tokens，另有在途计算未知。27B守护1169995/tick8953808、boot b4166d98已恢复，GET模型200。原现场保留；其他对话/LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
