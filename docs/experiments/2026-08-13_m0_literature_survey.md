# M0 文献调研：VGMC 差异化判定（docs/30 科研线）

> 执行: Loop D 主线程, 2026-08-13 夜（约 1h, 任务卡见 docs/30 文末附录）
> 方法: arXiv API 全文（HTML）+ OpenAlex/Crossref 元数据检索; GB10 隔离执行, 未动生产代码。
> 硬约束遵守: literature-review 子技能中 parallel.ai 的 curl|bash 引用**未执行**; 检索全程走 arXiv/OpenAlex/Crossref REST API。
> 原始物料: ~/wzh/research/m0_lit/（batch1-4.json + 5 篇全文 txt, GB10 本地不入 git）

## 一、逐篇精读（4 篇主读 + 3 篇补扫, 按任务卡）

### 1. RecMem — Recurrence-based Memory Consolidation（最近邻 1）
- 出处: ACL 2026 Findings（DOI 10.18653/v1/2026.findings-acl.1619）; arXiv 2605.16045; Huawei Cloud + BUPT + Huawei Theory Lab + WHU
- 问题: 长时运行对话 agent 的记忆构建 token 成本过高（现有系统 Mem0/Zep/A-Mem 对每条交互都做 eager LLM 固化）
- 方法: 三层记忆（subconscious 原始缓冲+轻量 embedding / episodic 情节摘要 / semantic 细粒度事实）。**recurrence 触发固化**: 仅当新交互在潜意识层找到足量语义相似历史时才调 LLM 做 episodic 抽象 + semantic refinement（认知科学 multi-store/CLS 理论动机）
- 记忆形态: **自然语言**（情节摘要 + 原子事实）, 供检索 QA
- 验证机制: **无**。固化触发 = 相似度/重现已启发式; 质量把关靠 LLM 自身; 评测 = LoCoMo 对话记忆 QA（F1 + LLM judge）
- **vs VGMC**: RecMem 回答"何时固化省成本", 记忆仍是 NL 检索件; VGMC 回答"固化成什么 + 如何防漂移"——确定性可执行规则（schema/synonyms）+ 回归验证门 + LLM 介入随记忆库衰减。互补不重叠, **差异化成立**

### 2. CAIS 2026 episodic critique → semantic guidance（最近邻 2）——**未能验证存在**
- arXiv 站内检索（"episodic critique"+"semantic guidance" 多种组合）、OpenAlex、Crossref 均 0 命中; Semantic Scholar 持续 429（共享 IP 池限流）未能复核
- 判定: docs/30 中该锚点来自 08-13 凌晨首轮快速检索（经 web_search）, **无法在公开数据库复现**, 疑似检索幻觉或极新/未公开条目。若按原描述（episodic critique 蒸馏为 semantic guidance）存在, 其 semantic memory 仍是 NL 提示, 与 VGMC 的可执行规则+验证门仍有差异——但此判断**待作者人工核验**（OpenReview/CAIS 官网）后才能算数
- 处置: 入 blocked_questions 台账; 论文写作前必须人工确认, 不能引用不可核验的文献

### 3. Q-Evolve — Self-evolving LLM agents with in-distribution Optimization
- 出处: arXiv 2606.07367（2026-06-05）; TU Eindhoven + Liverpool + MIT-IBM Watson
- 问题: 稀疏延迟奖励下的长程决策 credit assignment
- 方法: 自进化框架——混合 off-policy 数据上训练 in-distribution IQL critic → advantage 作 step-wise process reward → behavior-proximal 策略优化; 迭代自举不加剧分布漂移
- 记忆形态: **无外部记忆**——进化对象是策略权重（附录 "Memory cost" 指计算开销）
- 验证机制: in-distribution 约束（RL 稳定性意义）, 非知识固化防漂移
- **vs VGMC**: 进化目标正交（权重 vs 外部规则记忆）; Q-Evolve 可作相关工作区隔, 其 critic 思路与 VGMC 的"固化门控小模型"（docs/30 §2.2）有方法论呼应, 可引为对照。**差异化成立**

### 4. STATE-Bench（微软, 场景最贴）——**未能验证存在**
- arXiv/OpenAlex/Crossref 以多组关键词（STATE-Bench / enterprise tasks / improve with experience）检索均无对应条目; 最接近命中为 Agent-Diff（2602.11224, 企业 API 任务基准）与 MEMTRACK（2510.01353, 多平台状态追踪）, 均非目标
- 处置同 CAIS: 入台账, 人工核验前不得引用。若存在且为"agent 随经验在企业任务上变好"的基准/场景论文, 则是 VGMC 的**动机引用**而非机制竞争者

### 补扫三篇
- **Self-Evolving Coding Agents 综述**（arXiv 2608.03392, 2026-08-04）: 对象中心分类学（框架/记忆/技能工具/模型/工作流进化）+ 进化时机与证据两维。§3.2 Memory Self-Evolution 综述的形态 = 经验库/轨迹记忆/仓库记忆（SWE-Exp、EvoCoder、EvoRepair 等）, **全部为 NL/轨迹形态的检索复用, 无一固化为确定性可执行规则**; 综述明言框架级自进化"需要 validation、rollback 与 robustness checks"——为 VGMC 验证门提供领域共识背书。§6 开放问题含"长期记忆/技能/协同"与"超越短基准的评估"。**差异化成立且有空隙佐证**
- **Evo-Memory**（arXiv 2511.20857, UIUC + Google DeepMind）: 自进化记忆的流式基准; 统一 10+ 记忆模块; ExpRAG（经验检索基线）+ ReMem（think/refine-memory/act）。记忆 = NL 经验, refine 靠 LLM, 无验证门。**可借鉴**: 流式任务流 + memory-centric 指标（adaptation/efficiency/stability）的评估方法可直接迁移到 VGMC 实验 3 的学习曲线设计
- **MemoryAgentBench**（arXiv 2507.05257, UCSD）: 记忆 agent 四能力基准（accurate retrieval / test-time learning / long-range understanding / selective forgetting）, 增量多轮形式。**可借鉴**: 四能力框架可作为 VGMC 论文评测章的对照维度; 与 VGMC 机制定位正交

## 二、差异化判定

**结论: 差异化成立（附条件）。**

可核验文献中无一覆盖 VGMC 的三要素组合: ① 语义记忆固化为**确定性可执行规则工件**（非 NL）; ② 固化前**回归验证门**（防漂移/反误进化）; ③ **LLM 介入随记忆库增长衰减**的学习曲线度量。最接近的 RecMem 只解决"何时固化"的成本问题且记忆仍为 NL; 综述确认 coding-agent 记忆自进化全线停留在轨迹/NL 检索复用; Q-Evolve 进化权重不进化记忆工件。

**条件/风险**:
1. CAIS 2026 与 STATE-Bench 两个锚点**未能在公开数据库核验**（疑似首轮检索幻觉）——写作前必须人工确认, 否则不得引用。这是本次 M0 的意外收获: 检索型 agent 产出的文献锚点本身需要验证门（与 VGMC 主题同构）。
2. 该方向 2026 年 6-8 月论文密度极高（综述 08-04 才发布）, 投稿前需再做一次增量扫描。
3. S2 API 全程 429, 覆盖面受限; OpenReview/会议官网渠道未覆盖, CAIS 若为 workshop paper 可能漏检。

## 三、可吸收清单（论文写作时用）
1. Evo-Memory 流式评估方法 → 实验 3（学习曲线/LLM 介入衰减）的基准形态
2. MemoryAgentBench 四能力 → 评测章对照维度（VGMC 可声明覆盖 retrieval+test-time learning 并新增 consolidation-safety 维度）
3. 综述分类学 → 相关工作定位图（VGMC = memory self-evolution 分支下"可执行工件+验证门控"新格）
4. RecMem 的认知科学动机（multi-store/CLS）→ 可平行引用支撑"选择性固化"直觉
5. 真实门控数据（apply 5/reject 14/hold 6, 华泰 35.7→100）在已查文献中未见同类报告, 是稀缺实证资产

## 四、NLPCC / CCIR 截稿日
- nlpcc.com.cn DNS 解析失败、ccir.org.cn 502、ccfddl 聚合站 JS 渲染 + GitHub 仓库 404, **API 渠道未获得**。入台账: 需作者浏览器人工查（NLPCC 通常年中截稿, CCIR 通常春季, 以官网为准）。

## 五、对 docs/30 的修订建议
1. §3 相关工作锚点中 CAIS 2026 / STATE-Bench 标注"待核验", 人工确认前不作为差异化论据
2. §2.1 差异点表述维持（验证门 + 可执行规则 + 介入衰减三要素）, 补"检索记忆全线 NL 形态（综述佐证）"
3. 实验 3 评估方法直接对齐 Evo-Memory 流式协议
