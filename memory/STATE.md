# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：paused；用户独立授权的零训练探针已结束，不构成恢复Goal或开训授权。轻量探索：候选单臂对缓存普通SFT，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：12错＋8对探针：普通SFT恢复0/12、保持8/8；DeepSeek盲测恢复5/12、保持8/8。学生20次均未输出诊断ACTION，不能据此判8B容量不足。旧开发37与确认均30保留。[实测](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#zero-training-alignment-probe)。
- **实际运行 / 预算**：FinQA本地4,832POST/20,417,440已知＋9未知预留294,912；TAT另228POST/824,488＋2未知65,536。校内5,302POST/52,236,672已知＋10未知2,621,440，合54,858,112/10亿。本轮含提交修正后的学生重跑，无新训练。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：三臂loss小试取消，未开训。恢复Goal后再选诊断自纠或接管效用学习；保留121组回放，从TRAIN形成修复/KEEP对，DEV教师输出不进训练。新64留出不碰；当前不继续模型调用。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：探针进程已结束，27B恢复ready，守卫2355498、32GiB保护，约76GiB可用。探针raw在GB10，代码和短结果本机保留，按用户轻量模式未打包。旧材料及Paper E/开题/LoopB WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
