# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：旧37同TRAIN96已61成功；完整DeepSeek原生63，简单单位保护后74。相对BGE路由DEV35、选择探针TRAIN10/16均停止；新8B共享教师状态效用模型已开训，96来源252视图＋121回放，计划434更新。旧37/64保留，新候选尚无DEV分数。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#shared-teacher-value-v1)。
- **实际运行 / 预算**：本地FinQA5,686POST/23,910,452＋12未知393,216；校内5,692POST/54,073,554＋11未知2,883,584，合56,957,138/10亿。本批新增本地126POST/505,126、校内182POST/858,816，未知0；CPU值头另1,000更新，新GPU训练在途另记，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：跟进acquisition_value_v1现有训练，不重启。训练后自动做64个公共状态的真实HF效用前向、冻结最多18个接管任务；随后运行evaluate，已授权校内Key仅经隐藏输入进入进程，执行仍用完整OpenCode。不得把共享教师视图当独立任务，DEV监督与新64隔离。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：当前父4100174/21736071、训练子4100300/21736480已核存活。只加载8B训练权重，32GiB保护保留；预测子进程结束后父流程恢复27B。新公开模块只含代码，raw/数据/Key不入Git；其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
