# Current State

> 2026-11-19 | 当前状态见本页。接续按[研究导航](../docs/research/README.md)选入口，未决见[THREADS](THREADS.md)。

- **v5 论文工作稿**：已重写摘要、引言与近邻归因，前向57四臂入稿。完整方案对普通＋风险 K7 35对33（教师 tokens 少36.1%），K16 35对34。另行锁定的 FinQA 新64以 K8 为主、K18 为次，运行状态查私有 `forward64_factorial_fresh_v1`。[v5 PDF](../research/agent_frontier_portfolio_20261029/ijcnn_ieee/main.pdf) · [四臂结果](../research/agent_frontier_portfolio_20261029/results/IJCNN_EXPERIMENT_TABLES.md#factorial-combination)。
- **第二篇导师审阅 v4**：Git 冻结 `79000372`。FinQA 封存确认 34→39→42。TAT-QA 同面板扩容128表成对29对普通22，选128后K18价值35、风险37，均无错改。[v4 PDF](https://github.com/Wzh2learn/agents_final_tech/blob/7900037223d357bb56e08bbc550bda46dd3d1ee6/research/agent_frontier_portfolio_20261029/ijcnn_ieee/main.pdf)。
- **本地纠正**：FinQA DEV64普通／恢复前单侧／恢复后单侧／成对为33／29／34／37。成对与恢复后单侧均保住原33题。封存确认64仍为普通34、成对39。接管预算结果见[总表](../research/agent_frontier_portfolio_20261029/results/IJCNN_EXPERIMENT_TABLES.md)。
- **v4 后续干预**：新TAT32尺度门槛12→13，Pair128同为13且R5/H0；证据卡配对10→9，校内291,116 tokens；固定Pair128+Risk保留为路由参照。[结果](../research/agent_frontier_portfolio_20261029/results/IJCNN_EXPERIMENT_TABLES.md#post-v4-intervention-results)。
- **教师尺度复验**：旧两组固定 K9 回放40→45/64（R5/H0）。新 TAT-QA 32 表，K6 教师尺度检查21/32 对 K9 原输出18/32（R3/H0，教师 tokens 少36.9%），K9 同预算复验22/32。校内新增77,045，累计含未知预留60,106,846／10亿。[新表结果](../research/agent_frontier_portfolio_20261029/results/IJCNN_EXPERIMENT_TABLES.md#teacher-scale-budget-new32)。
- **同条件补验**：同一四状态模型内，前向57 K16 效用比风险多恢复1–2题，DEV主预算逐题相同。固定教师算式，普通／成对尺度适配在新32表同为 K6 21、K9 22。新增校内0。[补充消融](../research/agent_frontier_portfolio_20261029/results/IJCNN_EXPERIMENT_TABLES.md#matched-teacher-scale-adapters)。
- **预算**：C3累计912次本地请求、3,390,227已知tokens、1次未知。新增接管56次校内POST、241,529 tokens、0未知。校内累计含未知预留59,738,685／10亿。
- **后续机制存档**：MultiHiertt 同值引用与 tau2／ALFWorld 进度配对保留为后续研究材料。[实验索引](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **复算位置**：公开摘要随Git同步。原始模型回执按实验记录定位，留在GB10私有目录。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
