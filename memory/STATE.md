# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：DEV效用/风险41、单状态40。冻结新57来源：首轮31、普通/旧37均32；16接管效用35、风险/单状态33、随机35；7接管35/33/35/33。直接教师32、保护后37。局部收益迁移，固定混合40停止。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#forward-sources57-v1)。
- **实际运行 / 预算**：已结算本地FinQA5,913POST/24,796,155＋12未知393,216；校内5,854POST/54,810,875＋11未知2,883,584，合57,694,459/10亿。57批新227本地/885,703tokens、107校内/487,662，未知0；HF累计363前向/544,523输入tokens。GPU已完成4,569更新/8,094前向；扩样训练在途另记，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：acquisition_value_expanded_v1父127302/23418412，153 TRAIN来源/323视图、121回放原样，计划548更新/1,036前向。57前向批已先闭合，才纳入训练；预留64隔离。完成后自动HF预测/恢复27B，再evaluate --variant expanded及matched --variant expanded，不把已训练57再当验证。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：57批短回执已同步本机，原始wire留GB10；预测汇总NameError已仅补汇总，0重跑、原失败保留。当前扩样单8B训练，32GiB保护，训练/预测退出后恢复27B。代码/短状态本批同步，数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
