# 相关工作 v4（论文身份重冻结后四簇重排）

> 状态: 骨架稿（2026-08-31, Phase B 首件, Loop D 主线程零端点）| 取代关系: 结构取代 v3（v3 簇一保留并入新簇三; 簇二/三降为 S6 短段素材）; v1/v2/v3 保留备查
> 依据: Paper Claim Set v2（2026-08-30_phase_a_autopsy_and_claim_set_v2.md）+ 用户 08-31 裁定（文献重构不从零开始; 六线索侧线已核验, 本文按 citation-management 流程实查落 BibTeX, 存在性以实查为准）
> 禁则: BiomniBench arXiv 全库 0 命中, 未证实前禁用, 不得入稿（侧线 08-30 核验 + 本文复核接受该结论）

## 0 修订记录

- v3 → v4: 论文身份 = 长流程评测协议的判别力与缺陷可见性（非记忆/自进化）。簇一（变异测试）与新身份同构, 保留并入簇三; 簇二（记忆）/簇三（自进化）降为 S6 短段（VGRM 案例语境）。
- 新四簇: meta-evaluation / 过程级评测 / 突变与故障注入 / 裁判可靠性。
- 六条专家线索实查结果（本文 2026-08-31 经 arXiv API 逐条拉取元数据, 与侧线 08-30 核验清单一致）:
  1. AgentChaos = arXiv 2608.06790（2026-08-07）✓
  2. Metamorphic Testing of LLMs = arXiv 2511.02108（2025-11-03）✓（venue 标签 ICSME 来源侧线转述, arXiv 元数据无 venue → 待证实, 见 §7 队列）
  3. AgentProcessBench = arXiv 2603.14465v2 ✓
  4. WebStep "Where Did It Go Wrong?" = arXiv 2606.15673v2 ✓（venue 标签 COLM 来源侧线转述, arXiv 元数据无 venue → 待证实, 见 §7 队列）
  5. ACES 期刊版 = arXiv 2401.16313（同族 2210.15615 / 2311.01153 均实查在案）✓
  6. Contextual Metric Meta-Evaluation = arXiv 2503.19828（侧线核验 ACL 2025 Findings (NAACL) 276; 本文以 arXiv 版入 BibTeX, 刊版信息作注记）✓
  - BiomniBench: 禁用（见头部禁则）。
- 09-01 文献补线（专家第 2 轮 §8, 指标对表示层鲁棒性 = R3 理论坐标, 非边缘）: 检索词组 ①② 实查（沉淀件截断, ③④ 待补发; 锚点 2503.19828 / 2401.16313 同族已在案）, arXiv API 逐条核验元数据, 新增 7 件: 排序不稳定框架（2603.03493, GRN 域方法同构）/ LLM 评测 prompt 排序稳定性（2606.24381）/ 指标质量元评测（2412.13989, T2I 域）/ LLM 管线隐藏测量误差（2604.11581）/ judge 鲁棒性系统评估（2506.09443）/ judge 打分偏差（2506.22316）/ 答案等价判定（2402.11161, 与 DR-4 Step1 oracle 同族）。全部存在性已证, 零猜测。

## 1 簇一 · Meta-evaluation（评测协议/指标的元评测）

对位问题: 指标与评测协议本身需要被评测——本文把被测对象从"单一指标分数"换成"长流程管线评测协议的判别力与可见性"。

1. **ACES 系**（amrhein2022aces → amrhein2023aceswmt → moghe2024acesjournal）: 以人工判定的翻译准确性挑战集（challenge sets）元评测 MT 指标——指标应区分"真错误/可接受变体/无误"。**与本文对位**: 同构主张 = 评测器必须能区分"真缺陷/等价变体/无缺陷"; 本文的等价变异校正（T2, 7 等价注入）与有效突变体审计（D1 三分类）即该区分在长流程管线上的操作化。差异: ACES 面向标量指标可靠性, 本文面向多层协议的按类型可见性谱。
2. **Contextual Metric Meta-Evaluation**（deviyani2025contextual）: 以局部指标精度（局部上下文内度量准确性）元评测指标。**与本文对位**: "评测器对自身盲区的感知"是局部精度问题的协议级版本; 本文的 matched-specificity（D3）与聚类统计预案（Phase C）回应其"按上下文分层评估"的方法论要求。

3. **【09-01 增簇】指标排序不稳定与表示层敏感性（R3 理论坐标, 专家第 2 轮 §8）**:
   - **Quantifying Ranking Instability Across Evaluation Protocol Axes**（kendiukhov2026ranking, 2603.03493）: 系统诊断框架, 量化评估协议轴（预处理/参数/指标选择）变化下的基准排序不稳定度。**与本文对位**: 方法同构——该件量化"协议轴变动 → 排序漂移", 本文量化"打分表示/匹配器变动 → 可见性谱漂移"（D2 τ_min=0.7333 与嵌入臂谱塌降即其实例）; 差异: 该件域为基因调控网络基准, 本文域为长流程文档管线, 且本文同时给出机制归因（打分轴单轴驱动）。
   - **On the Stability of Prompt Ranking in LLM Evaluation**（du2026promptranking, 2606.24381）: LLM 评测中 prompt 排序对随机种子/评测子集选择的稳定性。**与本文对位**: 同为"评测结论对评测配置的敏感性", 其敏感性源 = 抽样与随机性, 本文敏感性源 = 匹配/打分表示层; 两件并置支撑 R3 的"可见性是 evaluator-context dependent"叙事。
   - **What makes a good metric?**（ross2024goodmetric, 2412.13989, T2I 域）: 元评测视角审"好指标"应具备的性质（对语言/视觉性质的灵敏度）。**与本文对位**: 本文"评测协议必须能看见注入缺陷"即其灵敏度要求在长流程协议级评测的实例化; 域差异显式标注（图像生成一致性 → 文档管线判别力）。
   - **Hidden Measurement Error in LLM Pipelines**（messing2026measurementerror, 2604.11581）: LLM 管线中隐藏测量误差扭曲标注/评测/基准。**与本文对位**: 同为"管线中间层使真实信号不可见"; 该件面向测量误差的统计分解, 本文面向缺陷可见性的类型级谱与静默吸收机制——互补证据: 可见性盲区是管线评测的一阶问题而非边角。

## 2 簇二 · 过程级评测（step/process-level evaluation）

对位问题: 最终答案正确 ≠ 过程可靠; 中间步骤质量需要独立度量。

1. **AgentProcessBench**（fan2026agentprocessbench）: 工具使用智能体步级过程质量诊断基准。**与本文对位**: 同为"不看最终答案看过程"; 本文以检查点树 + 确定性契约实现步级度量, 并额外回答"该过程度量自身能否看见注入缺陷"（元层）——AgentProcessBench 度量系统, 本文同时度量度量。
2. **WebStep**（chung2026webstep）: Web 智能体过程级评测 + 语义状态跟踪, 定位"哪一步出错"。**与本文对位**: 定位诊断轴（R2 b 轴）同源; 本文的静默吸收分析（缺陷被中间层吸收而不显形）是其未覆盖的失败模式类——过程正确而缺陷不可见。

## 3 簇三 · 突变与故障注入（保留 v3 簇一 + 新两件）

对位问题: 受控扰动是测量评测判别力的标准手段; 扰动本身的有效性（保真度/可观测性）必须先被审计。

1. **变异测试谱系**（v3 簇一, v2 §4 mutation score 方法论已完备, 保留）: 突变体未杀死测试 ≠ 系统正确, 可能是突变体无效——本文 M7 保真度发现（F_W2_1）与 D1 三分类（有害/等价/不可观测）即该风险在评测协议测量场景的实例化与操作化。
2. **AgentChaos**（tan2026agentchaos）: 智能体系统的混沌工程——程序化故障注入暴露系统弱点。**与本文对位**: 同为程序化注入, 目标互补: AgentChaos 测系统鲁棒性（系统能否扛住故障）, 本文测评测可见性（评测能否看见故障）; 本文的注入谱（6 类表头漂移 + 9 检查点突变体）是其故障目录在文档管线评测维度的扩展。
3. **Metamorphic Testing of LLMs**（cho2025metamorphic）: LLM 的蜕变关系测试（输入变换下输出应满足的关系）。**与本文对位**: 等价变体（吸收后标准字段集不变 = 蜕变关系成立 → 鲁棒）与有害变体（蜕变关系被破坏而评测未察觉 = 盲区）的形式边界, 与本文等价类定义同族; 本文按设计口径冻结等价类范围（仅 alias/mixed_lang/prefix_noise, OCR 形近不在内, 论证骨架见 D1 设计稿）。

4. **【09-01 增簇】PEDANTS: 答案等价判定**（li2024pedants, 2402.11161）: 廉价、可解释的答案对等价类判定（QA 场景）。**与本文对位**: 与 DR-4 重写后的 Step 1 独立 oracle 同族——等价判定先于且独立于系统输出（等价是语义性质, 不是检测结果）; 差异: PEDANTS 判定答案串等价, 本文判定表头变换的规范真值映射与下游语义不变性（实例级冻结, 不按类型一刀切）。

## 4 簇四 · 裁判可靠性（judge reliability）

对位问题: 以 LLM 为裁判时, 裁判自身的偏差与灵敏度是评测有效性的一阶威胁。

1. **Judging LLM-as-a-Judge**（zheng2023judge）: MT-Bench/Chatbot Arena 确立 LLM 裁判与人类偏好一致性范式, 同时暴露位置偏差等裁判偏差。**与本文对位**: 本文裁判使用约束（不见注入真值 = 防泄漏; 确定性契约优先, judge 只评开放语义维）是其偏差控制清单的工程化实例。
2. 本文内部证据（非文献, 供引用时标注口径）: 四维 judge 基线 4.94-5.0（08-08, :8006 xhigh 口径）; 端点一致性只能验证到离散评分分辨率（|Δ| 容差 = 0-10 整数叶分分辨率, F_W2_4）; 同口径内判分-映射排序一致性 Spearman 0.9744 / 方向一致 0.9907（限 :8004 口径内, 不得表述为跨端点证据, J6 裁定）。
3. **【09-01 增簇】RobustJudge: judge 鲁棒性系统评估**（li2025robustjudge, 2506.09443）: 对 LLM-as-a-Judge 在扰动下的鲁棒性做综合评估（含跨配置判分一致性）。**与本文对位**: 本文裁判口径注记（端点一致性只能验证到离散评分分辨率, F_W2_4）是其问题域的协议侧实例; 该件提供鲁棒性度量方法参照。
4. **【09-01 增簇】Evaluating Scoring Bias in LLM-as-a-Judge**（li2025scoringbias, 2506.22316）: 裁判打分偏差的度量（含自偏好/位置类偏差）。**与本文对位**: 支撑本文"judge 不见注入真值 + 确定性契约优先"的偏差控制设计; 引用时与 zheng2023judge 并列。
5. **TODO（Phase B 续, 部分清零 09-01）**: ~~judge 鲁棒性专项~~（已由 2506.09443 / 2506.22316 部分覆盖）; 剩余待实查 = judge 端点敏感性的既有度量 + 评分者间一致性在评测协议场景的量化方法——入稿前必须实查落 BibTeX。

## 5 S6 短段素材（原簇二/三降级留存）

- 记忆评测三件（MemoryAgentBench / Evo-Memory / RecMem）: 仅在 S6 VGRM 案例段作"巩固的准入判据"语境引用（增益-附带双门 ↔ 选择性遗忘的回归约束）。
- 自进化两件（Q-Evolve / SE-Coding 综述）: 仅在 S6 作"规则侧免训练对偶"一句定位。
- BibTeX 保留（v3 §3 原样）, 引用位置限 S6 短段。

## 6 BibTeX（本次实查落库; 作者列表 = arXiv 条目原文）

```bibtex
@article{tan2026agentchaos,
  title   = {AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection},
  author  = {Tan, Gou and Sun, Zhensu and Shi, Jieke and Zhang, Ting and He, Zilong and Wu, Qingfu and Liang, Shuai and Sun, Weifeng and He, Junda and Chen, Pengfei and Zhang, Chuanfu and Shar, Lwin Khin and Lo, David},
  journal = {arXiv preprint arXiv:2608.06790}, year = {2026}}

@article{cho2025metamorphic,
  title   = {Metamorphic Testing of Large Language Models for Natural Language Processing},
  author  = {Cho, Steven and Ruberto, Stefano and Terragni, Valerio},
  journal = {arXiv preprint arXiv:2511.02108}, year = {2025},
  note    = {venue 待证实（侧线转述 ICSME 2025 pp.174-186, arXiv 元数据无 venue; 入正文前 DBLP 核验, 未证实则去标签）}}

@article{fan2026agentprocessbench,
  title   = {AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents},
  author  = {Fan, Shengda and Ye, Xuyan and Huo, Yupeng and Chen, Zhi-Yuan and Guo, Yiju and Yang, Shenzhi and Yang, Wenkai and Ye, Shuqi and Chen, Jingwen and Chen, Haotian and Cong, Xin and Lin, Yankai},
  journal = {arXiv preprint arXiv:2603.14465}, year = {2026}}

@article{chung2026webstep,
  title   = {Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking},
  author  = {Chung, Jiwan and Byun, JiHyuk and Vineet, Vibhav and Kim, Seon Joo},
  journal = {arXiv preprint arXiv:2606.15673}, year = {2026},
  note    = {venue 待证实（侧线转述 COLM 2026, arXiv 元数据无 venue; 入正文前 DBLP 核验, 未证实则去标签）}}

@article{moghe2024acesjournal,
  title   = {Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets},
  author  = {Moghe, Nikita and Fazla, Arnisa and Amrhein, Chantal and Kocmi, Tom and Steedman, Mark and Birch, Alexandra and Sennrich, Rico and Guillou, Liane},
  journal = {arXiv preprint arXiv:2401.16313}, year = {2024},
  note    = {MIT CL 期刊版; 同族 amrhein2022aces / amrhein2023aceswmt}}

@article{amrhein2022aces,
  title   = {ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics},
  author  = {Amrhein, Chantal and Moghe, Nikita and Guillou, Liane},
  journal = {arXiv preprint arXiv:2210.15615}, year = {2022}}

@article{amrhein2023aceswmt,
  title   = {ACES: Translation Accuracy Challenge Sets at WMT 2023},
  author  = {Amrhein, Chantal and Moghe, Nikita and Guillou, Liane},
  journal = {arXiv preprint arXiv:2311.01153}, year = {2023}}

@article{deviyani2025contextual,
  title   = {Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy},
  author  = {Deviyani, Athiya and Diaz, Fernando},
  journal = {arXiv preprint arXiv:2503.19828}, year = {2025},
  note    = {侧线核验: ACL 2025 Findings (NAACL) 276}}

@article{zheng2023judge,
  title   = {Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena},
  author  = {Zheng, Lianmin and Chiang, Wei-Lin and Sheng, Ying and Zhuang, Siyuan and Wu, Zhanghao and Zhuang, Yonghao and Lin, Zi and Li, Zhuohan and Li, Dacheng and Xing, Eric P. and Zhang, Hao and Gonzalez, Joseph E. and Stoica, Ion},
  journal = {arXiv preprint arXiv:2306.05685}, year = {2023}}
@article{kendiukhov2026ranking,
  title   = {Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking},
  author  = {Kendiukhov, Ihor},
  journal = {arXiv preprint arXiv:2603.03493}, year = {2026}}

@article{du2026promptranking,
  title   = {On the Stability of Prompt Ranking in Large Language Model Evaluation},
  author  = {Du, Shaoshuai and Liang, Penghao and Shen, Yixian and Shi, Chuanqi and Zhang, Hang and Wang, Lun},
  journal = {arXiv preprint arXiv:2606.24381}, year = {2026}}

@article{ross2024goodmetric,
  title   = {What makes a good metric? Evaluating automatic metrics for text-to-image consistency},
  author  = {Ross, Candace and Hall, Melissa and Romero Soriano, Adriana and Williams, Adina},
  journal = {arXiv preprint arXiv:2412.13989}, year = {2024}}

@article{messing2026measurementerror,
  title   = {Hidden Measurement Error in LLM Pipelines Distorts Annotation, Evaluation, and Benchmarking},
  author  = {Messing, Solomon},
  journal = {arXiv preprint arXiv:2604.11581}, year = {2026}}

@article{li2025robustjudge,
  title   = {LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge},
  author  = {Li, Songze and Xu, Chuokun and Wang, Jiaying and Gong, Xueluan and Chen, Chen and Zhang, Jirai and Wang, Jun and Lam, Kwok-Yan and Ji, Shouling},
  journal = {arXiv preprint arXiv:2506.09443}, year = {2025}}

@article{li2025scoringbias,
  title   = {Evaluating Scoring Bias in LLM-as-a-Judge},
  author  = {Li, Qingquan and Dou, Shaoyu and Shao, Kailai and Chen, Chao and Hu, Haixiang},
  journal = {arXiv preprint arXiv:2506.22316}, year = {2025}}

@article{li2024pedants,
  title   = {PEDANTS: Cheap but Effective and Interpretable Answer Equivalence},
  author  = {Li, Zongxia and Mondal, Ishani and Liang, Yijun and Nghiem, Huy and Boyd-Graber, Jordan Lee},
  journal = {arXiv preprint arXiv:2402.11161}, year = {2024}}

```

（v3 五篇 + Voyager/MemGPT 两篇 BibTeX 原样保留于 2026-08-29_related_work_v3.md §3/§4, S6 短段引用时直接取用, 不重录。）

## 7 覆盖度自查（Claim Set v2 ↔ 簇）

| 主张/组件 | 覆盖簇 | 缺口与处置 |
|---|---|---|
| R1 可见性谱 | 簇一（元评测范式）+ 簇二（过程级对位） | 无文献缺口; 写作差异点 = 按类型谱 + 静默吸收 |
| R2 检出-吸收-传播 + 定位-诊断 | 簇二（WebStep 定位轴）+ 簇三（注入手段） | 无缺口 |
| R3 可见性边界机制（匹配/打分层 + 量化 + 保真度） | 簇三（蜕变关系/故障注入）+ 簇四（裁判分辨率）+ 簇一增簇（排序不稳定/表示层敏感性 4 件, 09-01） | 有效突变体定义的形式化引用待 D1 后补（Phase C）; R3 理论坐标已有实查文献支撑（沉淀件 §8 ③④ 待补发后再扩） |
| R4 跨数据流（研究问题） | 簇二（基准多样性语境） | D4 结果出来前不引具体基准 |
| matched-FPR（D3）/ 聚类统计（Phase C） | 方法学, 非文献簇 | Phase C 预注册时再查统计方法文献 |
| 簇四裁判可靠性 | zheng2023judge 为锚 + RobustJudge/scoring bias（09-01 增） | TODO 部分清零: 余 = judge 端点敏感性度量 + 评分者间一致性量化, 入稿前清零 |
| BiomniBench | — | 禁用（0 命中未证实） |
| venue 待证实 ×2（ICSME 2511.02108 / COLM 2606.15673） | 簇三/簇二 | Phase B 实查队列: DBLP 核验, 未证实去标签（用户 08-31 更正注记） |