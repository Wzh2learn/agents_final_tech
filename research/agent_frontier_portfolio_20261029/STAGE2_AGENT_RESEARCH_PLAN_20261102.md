# 第二阶段研究议题与证据入口

> 2026-11-23｜[v5 阶段档案](IJCNN_MANUSCRIPT.md) · [双栏 PDF](ijcnn_ieee/main.pdf) · [实验总表](results/IJCNN_EXPERIMENT_TABLES.md) · [v4 审阅快照](https://github.com/Wzh2learn/agents_final_tech/blob/7900037223d357bb56e08bbc550bda46dd3d1ee6/research/agent_frontier_portfolio_20261029/ijcnn_ieee/main.pdf)

<a id="competitive-research-agenda"></a>
## 强对标后的研究议题｜外部专家讨论

400 题零训练探针已完成，选择[路线 A](../finance_frontier_pilot/README.md#路线裁决)。[FinQA 1,147 题与 TAT-QA 718 题的全量对标](../finance_frontier_pilot/README.md#两套官方全量结果2026-11-24)已齐，含 CAR、BudgetVerify、Cascade Routing 与固定级联适配。两库的短程序首答及未执行回退补足了低成本区，FinQA 的同值歧义选题在独立 TRAIN 开发集未产生净增。当前优先验证 TAT-QA 首答的尺度监督和保留能力。独立的端到端计时仍待恢复校内网关凭证，运行目录与回执见[现役实验记录](../finance_frontier_pilot/README.md)。

争取在**可执行的金融表文推理、紧凑模型、有限推理预算**这一场景做到领先。绝对准确率和准确率—成本前沿都值得竞争。优先回答两件事：能否提高强首答的正确候选覆盖率，以及执行反馈能否让强首答继续获益。允许重做首答生成、训练数据、教师机制和推理策略，也允许把现有三段重新组织成一个新方法。实验取舍由证据决定。

- **强首答。** 首选官方开放的 ODA-Fin-RL-8B，配合本地 Qwen3-8B/27B 和原生 OpenCode 执行。先获取权重与同条件分数，再选择可运行的同量级专门模型。DCRC 和 MATATA 是较高成绩参照。可结合可执行的来源绑定、训练集执行筛选和更有区分力的反事实。
- **强修订。** 固定首答和证据时，比较 CAR 式定向修订、CCT 式保持/纠正和本项目同一真实恢复前后反例分配。科学价值取决于强基座上能否多救错题且少破坏对题。
- **强预算策略。** 固定预算时，与 BudgetVerify 式局部复查和独立重解、同模型风险、多候选选择、全量教师对照。报告总推理 token、教师用量和墙时。若多个动作有独立互补性，可重设控制策略及训练过程。

新方法比较基于同划分、公开输入、程序输出条件与官方计分。开发使用未参与选型的来源，已封存确认组保留。公开测试和有限预算面板分别记成绩与边界。[全文复核、候选模型与原文库](IJCNN_RELATED_WORK_REFRESH_20261030.md#全文复核与强基线)

<a id="v5-factorial-goal"></a>
## 冻结证据与优先补强

- **本地纠正。** FinQA DEV64 的无反例、恢复前、恢复后、成对是 33/29/34/37。内部封存确认普通→成对 34→39/64（R6/H1）。前向 57 两种纠正各 32。新单步 64 本地为普通 7、成对 4，同为 8 次教师接管时普通＋效用 14，成对＋效用 11。[实验总表](results/IJCNN_EXPERIMENT_TABLES.md#fresh64-factorial-result)
- **候选上限。** 前向 57 的低预算完整策略为 35/57。已有首答、两纠正臂与全量共享教师的正确候选并集只有 39/57，18 题无正确候选。新单步 64 的 53 个可执行错答中，18 个按已知尺度倍数可对齐参考值，优先追查数据口径与生成能力。
- **教师与代价。** 96 条教师轨迹形成 252 个状态视图。旧确认 64 的 K8 为 41/64，用全量无保护教师的 16.0% tokens。同一保护器用全量是 44/64。前向 57 的 K7 完整策略以 63,222 教师 tokens 得 35，普通＋风险以 98,995 得 33。新 64 的方向不一致。[方法与预算](results/FINQA_CORRECTION_METHOD.md#shared-teacher-value)
- **跨契约与课堂资产。** TAT-QA 固定教师算式的最新新表 32 题，普通和成对尺度适配均 18→21/32（K6）。旧证据卡原生教师同为 9/16，保护后为 10/16 对 9/16。已有 ALFWorld、代码与客服资产供更广的候选验证，按[机制知识](results/CONTINUATION_PROGRAM.md#mechanism-knowledge)按需加载。

<a id="c3-scale-study"></a>
<a id="post-v4-intervention"></a>
<a id="teacher-scale-budget-confirmation"></a>
## 历史批次与复用

[尺度适配](results/IJCNN_EXPERIMENT_TABLES.md#c3-scale-adaptation)、[证据干预](results/IJCNN_EXPERIMENT_TABLES.md#post-v4-intervention-results)、[教师尺度复验](results/IJCNN_EXPERIMENT_TABLES.md#teacher-scale-budget-new32)均已完成。[此前完整短计划快照](https://github.com/Wzh2learn/agents_final_tech/blob/7c7b30450ee8a694dc582032a4c66270a51634c2/research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)保留具体协议、检验和私有回执位置。

<a id="边界预算与恢复位置"></a>
## 边界与恢复

立项前三问：实测瓶颈是什么，这次能改变哪条科学主张，同样资源是否有信息量更高的用法。新模型、训练和跑分的完成状态以实际回执为准。旧的资格检查和首分叉局部调参不作为研究进度代理。以最能改变科研判断的实验排序，保留原生结果、失败与成本。Paper E、开题及投稿由独立对话维护。[执行入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md) · [GB10 原文与模型入口](IJCNN_RELATED_WORK_REFRESH_20261030.md#全文复核与强基线)

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="恢复研究requests-自然任务对2026-11-05"></a>
<a id="与-paper-e-并行"></a>

旧跨场景研究入口见[主题归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。
