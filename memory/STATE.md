# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；深化执行错误分叉与状态绑定的纠正/保持。旧有效片段继续复用；收尾重写的4/32版本已停止，当前规则保留，扩大真实训练来源。
- **研究阶段**：保留v2的15/32对14及13/13保持信号；扩样已编译88组（两条冲突监督暂挂），普通/候选147目标逐token相同，成功蒸馏176目标。[方案](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#expanded-state-v1)。
- **实际运行 / 预算**：FinQA已闭合2,961POST/12,701,094已知＋7未知（229,376预留）；本轮教师100POST/496,680、未知0。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)。HF训练与旧中断另账；新42评估尚0调用。
- **下一交付**：三臂训练后由评估监督1206819/tick9247761接续，当前WAIT_TRAINING；42组协议65721486、准备ee064be8双份，尚无评估调用。依次直接27B、共同首轮、两臂同现场复查、成功蒸馏；不重复启动。TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：训练代码cbbc4027三端一致；监督1191213/tick9098840、主训练1191331/tick9099248，boot b4166d98。普通臂264更新/441前向完成，权重9090de2e双份；候选臂运行，可用约90GiB。32GiB保护、单权重，27B结束后恢复；其他对话/LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
