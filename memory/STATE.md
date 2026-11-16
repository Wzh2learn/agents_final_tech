# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；成对反例v1确认闭合，继续从实际恢复与死因改进训练规则；动作对齐为共同控制。
- **研究阶段**：121组扩样闭合：普通33/64、成对34/64，旧成对37保留。普通新版9选对数量、39学对关系，但分别缺单位换算/合法DSL；总分持平不等于没有学习。固定输出展平两者均34，不改原生分数。53确认均30保留。[局部深化](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_METHOD.md#goal-conditioned-correction-v1)。
- **实际运行 / 预算**：FinQA本地4,792POST/20,241,900已知＋9未知预留294,912；TAT另228POST/824,488＋2未知65,536。校内5,261POST/52,037,133已知＋10未知2,621,440，合54,658,573/10亿。现役同设八臂完成2,310更新/3,816前向/373,254监督tokens。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：优先目标条件化纠正：4个TRAIN自然问题对已CPU准备，固定证据/公共ID/程序/反馈，仅变问题；先用真实教师接续形成保持/纠正材料，再同数据比较普通SFT与具体改进。探索以可复现局部改善推进；前缀双对照后置、未训练。新64留出不训练，原53不回流。[机制](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_METHOD.md#goal-conditioned-correction-v1)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：本批监督/训练/原生/CPU均退出，27B恢复ready，守卫2214564/tick16645591、boot b4166d98、32GiB保护。结果43cca26e双份2366文件、尸检2a4f854b双份3文件。目标对PLAN d026b3b7/准备47afca4d双份45文件，仅4次CPU种子执行、0模型调用；前缀与新64仍未执行，其他WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
