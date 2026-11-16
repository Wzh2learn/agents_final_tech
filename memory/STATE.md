# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：纠正价值路由DEV **36/64：保持33、恢复3、错改0、18次接管**。完整27B参照37/64；同18次调用的错误风险/固定随机也36，仅问题35。保留路由为预算部件，单独的机制优势尚未拉开。三个恢复均为取数/年份语义绑定。[结果](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#correction-value-router-v1)。
- **实际运行 / 预算**：本批已闭合，本地FinQA5,397POST/22,791,219已知＋11未知360,448；补参照新增46POST/178,702，复用18次不重计。校内5,393POST/52,678,540＋11未知2,883,584，合55,562,124/10亿；TAT不变。训练和CPU另账。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：从30个TRAIN成功补丁的296个子集反馈学习联合修复；19个可执行错例至少需两个联合改动，15个无前置步骤。下一候选先抽象操作数角色/证据绑定模板，检查TRAIN候选覆盖，再训练小选择器真实出分；继续四算子，不建重型编译器。路由/旧37保留作缓存参照，新64/DEV监督不入训练。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：TRAIN、主路由、完整参照和控制链全部RETURNED，correction_router_v1下各RESULT可定位；不要重启这些批次。27B服务保留、32GiB保护；路由权重和5份短回执已存本机私有资产目录。原始证据留GB10，本批不混Paper E/开题/旧Goal WIP。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
