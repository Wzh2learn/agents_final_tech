# 协作流程枢纽：研究 Agent ↔ 写作 Agent（the paper）

> **创建**：2026-06-05 | **最后更新**：2026-06-13（合并输出格式规范 + 引用同步）
> **状态**：🟢 活跃（协作流程阶段 0-6 全 ✅，含输出格式规范附录）
> **文档定位**：研究 Agent 精读规范 + 候选阅读清单。
> **权威状态**：见 `SESSION_HANDOFF.md` §0.1（the paper v8 收口）。本文件不再重复 SSOT/Method 口径。

---

## ⚙️ 精读工作流规范（2026-06-05 user 指正，必须遵守）

研究 Agent 上一轮（Session 7）暴露两个流程问题，本轮起严格执行：

**规范 1：PDF 必须先转 Markdown 再精读，不要直接读 PDF**
- 上轮 Agent 下载 PDF 后**直接读 PDF 内容**精读，导致**阅读不全面**（PDF 解析易丢图表/公式/段落）
- 正确流程：`arXiv 检索 → 下载 PDF 到 reading_notes/pdfs/ → 转成 Markdown 全文 → 精读 Markdown`
- 转换工具建议：`marker` / `markitdown` / `pdftotext` 等，转出的全文 md 放 `reading_notes/fulltext/`
- 精读笔记必须基于**转换后的完整 Markdown 全文**，确保不漏内容

**规范 2：Paper 全文统一归位到 `reading_notes/fulltext/`**
- 现状问题：`reading_notes/fulltext/` 目录已存在，但**根目录下仍散落 10 个 `*_fulltext.md` 全文**（如 `AMEM4Rec_2602.08837_fulltext.md`、`Rec2PM_2602.11605_fulltext.md`、`MARS_2605.14401_fulltext.md` 等）未归位
- 要求：①所有 `*_fulltext.md` 全文统一放 `reading_notes/fulltext/`；②把根目录散落的全文 `mv` 进去（mv 不 rm，符合安全三步）；③以后新转换的全文直接落 `fulltext/`
- 目录分工：`pdfs/` 放原始 PDF；`fulltext/` 放转换后的 md 全文；`reading_notes/` 根目录放**精读笔记**（不放全文）

---

## 🎯 本轮主任务（2026-06-05 user 下达）— ✅ 已全部完成

> 5 步任务（查漏→速读转精读→更新 INDEX→固化策略→汇报）已在 Session 7-9 全部完成。
> 详见研究 Agent handoff Session 9 记录。

---

## 📖 新精读标准（2026-06-05 user 定，以后统一遵守）

研究 Agent 每篇精读**至少**必须完整读完并记录：

| 部分 | 要求 |
|---|---|
| **Abstract 摘要** | 全部读完 |
| **Introduction 引言** | **全部内容**读完（不是只读首段） |
| **Contribution 贡献** | 全部读完 |
| **Conclusion 结论** | 全部读完 |
| **Method 方法** | **看情况**大致读（抓核心机制即可，不必逐公式） |

**人机协作闭环**（user 的工作方式，研究 Agent 需配合）：
- user 会先看 `INDEX.md` → 按方向挑感兴趣的精读笔记看
- 若 user 觉得某篇值得深挖 → user 自己读原文 → 补充对应精读笔记
- 因此：**INDEX 必须按方向清晰组织、精读笔记必须覆盖上述 4 个必读部分**，方便 user 快速定位和二次深挖

---

## ✅ 已完成存档

> 已精读论文索引见 `reading_notes/INDEX.md`。以下候选清单为**未精读**论文。

---

## 📚 候选补充阅读清单（Step 1 查漏时参考，**均为未精读**，按需精读）

> 以下论文**尚未精读**（已精读的见上方"已完成存档"表，不在此列）。Step 1 查漏时判断哪些值得补读。
> 编号已与第一节（2026 最新快手 arXiv）区隔，从 C1 开始，避免重号。

### C. 压缩式长序列（喂 the paper §4.4.2 压缩层）

| # | 论文 | 出处 | 年份 | 核心机制 | 落 the paper 哪里 |
|---|---|---|---|---|---|
| C1 | **VQL: End-to-End Context-Aware Vector Quantization Attention for Ultra-Long User Behavior** | arXiv'25 | 2025 | 向量量化 attention 压缩超长序列 | §4.4.2 压缩，对标 Compressor |
| C2 | **CHIME: A Compressive Framework for Holistic Interest Modeling** | arXiv'25 | 2025 | 压缩式整体兴趣建模 | §4.4.2 压缩 |
| C3 | **DMQN: Deep Multiple Quantization Network on Long Behavior Sequence** | SIGIR'25 | 2025 | 多重量化网络 | §4.4.2，量化压缩思路 |
| C4 | **DiffuMin: Diffusion-driven Multi-interest Network for CTR** | RecSys'25 | 2025 | 扩散驱动多兴趣 | §4.4.2 + 多兴趣（advisor关注点） |
| C5 | **ENCODE: Breaking Trade-Off Between Performance and Efficiency in Long-Term User Behavior** | TKDE'25 | 2025 | 性能-效率权衡突破 | §4.4.2 压缩 |
| C6 | **LREA: Low-Rank Efficient Attention on Long-Term User Behaviors** | SIGIR'25 | 2025 | 低秩高效 attention | 对标快手 SOLAR 的低秩路线 |
| C7 | **DV365: Extremely Long User History Modeling at Instagram** | KDD'25 | 2025 | 超长历史建模（Meta/IG） | §4.4.2，工业级压缩 |
| C8 | **PinFM: Foundation Model for User Activity Sequences (Pinterest)** | RecSys'25 | 2025 | 用户行为序列基础模型 | 长序列 foundation model 视角 |
| C9 | **MIRRN: Multi-granularity Interest Retrieval and Refinement Network** | KDD'25 | 2025 | 多粒度兴趣检索精炼 | §4.4.3 多粒度（对标 A 多层记忆） |

---

### D. ★★★ 多兴趣 / 长短期解耦（advisor核心关注：多兴趣+时间分层）

| # | 论文 | 出处 | 年份 | 核心机制 | 落 the paper 哪里 |
|---|---|---|---|---|---|
| D1 | **LIC: Long-Term Interest Clock — Fine-Grained Time Perception** | WWW'25 | 2025 | 细粒度时间感知 | ⚡ 时间分层（advisor关注），§4.4 时间绑定，**第一梯队** |
| D2 | **Trinity: Syncretizing Multi-/Long-tail/Long-term Interests All in One** | KDD'24 | 2024 | 多兴趣+长尾+长期一体化 | 多兴趣融合，relates to memory routing design |
| D3 | **CLSR: 解耦长短期兴趣（快手 WWW'22）** | WWW'22 | 2022 | 自监督解耦长短期，两个独立编码器 | 快手长短期解耦经典，advisor提的"长短期不互扰" |
| D4 | **MIND: Multi-Interest Network with Dynamic Routing (Tmall)** | CIKM'19 | 2019 | 动态路由多兴趣 | 多兴趣鼻祖，multi-interest baseline |
| D5 | **ComiRec: Controllable Multi-Interest Framework** | KDD'20 | 2020 | 可控多兴趣 | 多兴趣经典，baseline |

> 注：ULIM、DILN 已精读（见上方存档表），不在此列。

---

### E. ★★ 端到端 / 生成式大模型（看快手等大厂端到端路线）

| # | 论文 | 出处 | 年份 | 核心机制 | 与 the paper 关系 |
|---|---|---|---|---|---|
| E1 | **BaseModel: Actions Speak Louder than Words (Meta)** | ICML'24 | 2024 | 万亿参数生成式 transducer | A 篇 Decoder backbone，**已用做骨干** |
| E2 | **STCA: Make It Long, Keep It Fast — 10k-Sequence at Billion Scale (Douyin)** | arXiv'25 | 2025 | 抖音 10k 序列端到端 | 端到端长序列，对标 A 篇序列长度 |
| E3 | **LONGER: Scaling Up Long Sequence Modeling in Industrial Recommenders** | RecSys'25 | 2025 | 工业长序列 scaling | 长序列 scaling 视角 |
| E4 | **GenRank: Towards Large-scale Generative Ranking** | arXiv'25 | 2025 | 大规模生成式排序 | 生成式排序 |
| E5 | **Fuxi-α: Scaling Recommendation Model with Feature Interaction Enhanced Transformer** | WWW'25 | 2025 | 特征交互增强 transformer | 生成式 scaling |
| E6 | **MTGR: Industrial-Scale Generative Recommendation (Meituan)** | CIKM'25 | 2025 | 美团工业级生成式 | 工业生成式对比 |
| E7 | **LLaTTE: Scaling Laws for Multi-Stage Sequence Modeling in Ads** | arXiv'26 | 2026 | 多阶段序列 scaling law | 2026 最新，scaling 视角 |
| E8 | **SparseCTR: Unleashing Sparse Attention on Long-term Behaviors** | WWW'26 | 2026 | 稀疏 attention 长序列 | 2026 最新，效率视角 |

> 注：VISTA 已精读（见上方存档表），不在此列。

---

### F. ★★ LLM/外部知识增强 + 推理（看"记忆+推理"方向）

| # | 论文 | 出处 | 年份 | 核心机制 | 与 the paper 关系 |
|---|---|---|---|---|---|
| F1 | **ReLLa: Retrieval-enhanced LLMs for Lifelong Sequential Behavior** | WWW'24 | 2024 | 检索增强 LLM 终身行为 | A 篇 baseline（记忆增强 LLM）|
| F2 | **ReLLaX: Full-stack Optimized LLMs for Lifelong Sequential Behavior** | TORS'25 | 2025 | ReLLa 全栈优化 | ReLLa follow-up |
| F3 | **ReaRec: Think Before Recommend — Latent Reasoning for Sequential Rec** | arXiv'25 | 2025 | 推荐前推理 | 推理增强，看趋势 |
| F4 | **RecZERO: Think before recommendation — Autonomous Reasoning** | NeurIPS'25 | 2025 | 自主推理增强推荐 | 推理增强 |
| F5 | **OnePiece: Bringing Context Engineering and Reasoning to Cascade Ranking** | arXiv'25 | 2025 | 上下文工程+推理 | 上下文工程视角 |

> 注：LIBER、HiT-LBM 已精读（见上方存档表），不在此列。

---

### G. ★ 跨域 / 多模态 / 多行为（补充视角，按需精读）

| # | 论文 | 出处 | 年份 | 核心机制 |
|---|---|---|---|---|
| G1 | **MUSE: Multimodal Search-Based Framework for Lifelong User Interest** | arXiv'25 | 2025 | 多模态检索式终身兴趣 |
| G2 | **DMGIN: How Multimodal LLMs Enhance Large Rec Models for Lifelong Post-click** | arXiv'25 | 2025 | 多模态 LLM + 终身 post-click |
| G3 | **GIST: Cross-Domain CTR via Guided Content-Behavior Distillation** | arXiv'25 | 2025 | 跨域内容-行为蒸馏 |
| G4 | **LCN: Cross Domain LifeLong Sequential Modeling** | KDD'24 | 2024 | 跨域终身序列 |
| G5 | **RAL-CDNet: Retrieval Augmented Cross-Domain LifeLong Behavior** | KDD'25 | 2025 | 检索增强跨域终身 |
| G6 | **Climber: Resource-Optimal Scaling Law for Large Rec Model** | CIKM'25 | 2025 | 资源最优 scaling law |
| G7 | **DAS: Dual-Aligned Semantic IDs (Kuaishou 广告)** | arXiv 2508.10584 | 2025 | 双对齐语义ID（快手广告）|

---

## 精读优先级建议（给研究 Agent，仅针对上方**未读**候选）

> 已精读论文（OneRec/MARM/ULIM/DILN/VISTA/LIBER/HiT-LBM/UxSID/Infini-attention/SOLAR/DualGR/SAGE/VikingMem）不再重做，见"已完成存档"表。

1. **第一梯队**（机制最相关，优先补读）：D1 LIC（时间分层）、C1 VQL（量化压缩对标 Compressor）、C9 MIRRN（多粒度对标多层记忆）
2. **第二梯队**（机制可迁移）：C6 LREA、C4 DiffuMin、D2 Trinity、F3 ReaRec
3. **第三梯队**（差异化对标/baseline）：其余
4. 每篇精读后：出独立精读笔记 → 补机制卡片（接㉞往后，已到㊳）→ 落 the paper §4.x 具体落点 → 建图谱连边 → 攒够后跑 dreams

> ⚠️ 注意：本轮**主任务是上方"消化存量"5 步**（查漏→速读转精读→更新 INDEX→固化策略→汇报）。本候选清单仅供 Step 1 查漏参考，**不是要求逐篇下载精读**——只补 Step 1 判断为"必须补读"的少数论文。

---

*清单来源以快手官方 `Survey-of-ULBM` 仓库为主干，arXiv 编号需研究 Agent 下载时二次核实（部分为 web 检索所得，可能有出入）*

---

## 2026-06-09 协作记录：§1 v9 重构 + §3-§7 级联修改

### 本轮协作内容

1. **§1 v9 重构**（写作 Agent 主导，已完成）
   - 三个 P 重新定义：P1(行为质量异质+兴趣演化) / P2(多时间尺度结构, 全新) / P3(跨类型消费+无 target)
   - advisor v2 底稿为起点，user 审阅后定稿
   - P2 新增数据支撑：研究 Agent 产出 `planning/P2_多时间尺度调研.md`（5 篇 Reference + 统计指标建议）

2. **§3-§7 级联修改**（写作 Agent 主导，✅ 已完成 2026-06-09）
   - §3.3 P 形式化定义已对齐current terminology（P2 去循环引用）
   - §4 project-specific-terms 操作与新 P 的映射关系已全部更新（Write→P1 质量面, Read→P3, Update→P2, Govern→P1 演化面）
   - §5-§7 实验/分析/结论中的 P 引用已全部级联替换
   - §4 吸收研究 Agent 4 处修正建议（Gumbel 选择依据/α 固定/Govern 不反传/β_absorb）
   - Figure 重编号 1-5（按出现顺序）
   - Phase 7 Adversarial Review 通过（12 项检查全清）

3. **分工**
   - **写作 Agent**：§1-§7 全部完成，等实验结果
   - **研究 Agent**：P2 形式化建议已被采纳（去循环引用版本）；§4 修正建议已吸收
   - **实验 Agent**：已启动代码实现，关键约束见写作 Agent handoff §〇

### P2 形式化建议（供写作 Agent §3.3 使用）

**旧 §3.3 的 P2 = "Passive Retrieval"**，新 P2 = "多时间尺度的行为结构"。新 P2 的形式化建议：

> **P2: Single-Scale Temporal Collapse.** 现有方法以固定时间粒度（如最近 $N$ 步窗口或统一压缩）处理用户行为序列 $S_u$，将不同时间尺度的信息坍缩到同一表示空间。然而用户行为天然存在层级时间结构：session 级行为呈现即时性偏差（短期 genre 分布与全局偏好 JS 散度最大），随观察窗口增大逐步趋近长期稳态。形式化地：设 $\mathcal{D}_u^{(\Delta t)}$ 为用户 $u$ 在时间窗口 $\Delta t$ 内的兴趣分布，则 $D_{JS}(\mathcal{D}_u^{(\Delta t)} \| \mathcal{D}_u^{(\infty)})$ 随 $\Delta t$ 单调递减——短期行为携带的即时意图信号和长期行为反映的稳定偏好是**不同层级的信息**，需要分层管理而非等权混合。缺乏按时间尺度解耦存储的机制，等价于强制将 Working Memory 级别的即时意图与 Semantic Memory 级别的核心偏好混为一个向量。

**形式化要点**：
- 核心数学表达：$D_{JS}(\mathcal{D}_u^{(\Delta t)} \| \mathcal{D}_u^{(\infty)})$ 随 $\Delta t$ 递减
- 文献支撑：Atkinson & Shiffrin (1968) 三层时间分工 + DILN (SIGIR'25) 兴趣生命周期实证 + Human-Inspired Memory (Microsoft 2026) 独立收敛到三层时间分区
- 数据支撑（待代码 Agent 跑出）：ML-25M 多时间窗口 JS 散度递减曲线
- 回应的 project-specific-terms 操作：core architecture（Working/Episodic/Semantic 各对应一个时间尺度）+ Update（EMA 使 Semantic 随长期兴趣演化）

**与旧 P2 的关键区别**：旧 P2 "Passive Retrieval" 的形式化是"检索缺乏 prototype"→ 这个论点现在并入新 P3（跨类型消费需要 prototype 桥接）。新 P2 的形式化完全是新的，聚焦时间尺度的结构性差异。

---

### P1 结构性风险——已知但选择不拆分（2026-06-09）

**观察**：P1 合并了"行为质量异质"（空间维度 → Write Gate）和"兴趣演化"（时间维度 → Update+Govern）。两者因果链不同，审稿人可能指出合并过于松散。

**决策**：不拆分。理由：
- 拆分为 P1a+P1b 需要级联修改 §1/§3/§4/§5/§6/§7（4 操作→P 映射全变），代价远大于收益
- P 数量从 3 变 4 增加审稿人认知负担
- 当前结构已被 user 拍板、写作 Agent 落实完毕

**审稿人 FAQ 预案**（若被问到"为什么 P1 合并两个现象"）：

> 行为质量异质和兴趣演化的共同后果是记忆池信息密度随时间持续下降——低质量行为在入口端污染记忆（Write Gate 应对），过时偏好在出口端占据有限容量（Govern 应对），两者构成信息生命周期治理的入口-出口闭环。认知科学中 encoding quality 和 memory decay 也常在同一框架下讨论——Atkinson-Shiffrin 模型的 rehearsal 机制同时应对编码质量与衰减问题。将两者合并为 P1 使论文结构保持"3P × 4 操作"的紧凑映射，避免 P 数量膨胀。

---

### v9 最终状态（2026-06-09 写作 Agent 确认）

- 合并稿 797 行，v9
- current terminology 全文对齐（27 处级联 + 9 项 §5-§7 修正）
- Phase 7 Review 通过（旧 P 标签 / 噪声 / 信噪比 / 管理症状 / Figure 编号 / 交叉引用 = 全零残留）
- §1-§7 文本冻结，下一步：实验 Agent 跑实验 → 填结果 → 写作 Agent 重写摘要 → camera-ready

---

---

## 2026-06-10 外部专家 Review + 各 Agent 分工

### 外部专家评审结论

顶会大佬通读 the paper v9（797 行），给出 **Weak Reject / Borderline Reject**。核心判断：

- **故事线 7.5/10**、**方法完整度 7/10**、**创新辨识度 6.5/10**
- **实验可信度 1/10**（当前为空）→ 补齐后可能到 7/10
- **顶会潜力**：有，取决于实验是否支撑长序列收益 + 低延迟 claim

### 四个致命问题（P0 必修）

| # | 问题 | 分配 | 具体行动 |
|---|---|---|---|
| 1 | **实验为空** | 实验 Agent | 代码适配 v9 已启动；至少跑出 BaseModel baseline + YourProject full + 6 个核心消融 |
| 2 | **"端到端可微"claim 过强** | 写作 Agent | 全文替换为 "learning-compatible" / "differentiable where needed"；区分 trainable neural path 和 async maintenance path |
| 3 | **Write Gate 训练不稳定风险** | 实验 Agent | 补 gate 通过率曲线 + entropy regularization 或 budget-aware loss |
| 4 | **<50ms 延迟无实测** | 实验 Agent | 跑 profiling（D=256 起步），给 P50/P95/P99 + latency breakdown |

### 五个 Method 风险（P1 强烈建议修）

| # | 问题 | 分配 | 具体行动 |
|---|---|---|---|
| 5 | **Semantic Prototype vs multi-interest 边界不硬** | 写作+研究 Agent | §2 补 MIND/ComiRec/SINE/PinnerSage 对比段；明确 prototype = governance anchor ≠ 兴趣表示 |
| 6 | **Usage importance 正反馈偏置** | 研究 Agent | 分析 ω 的 Matthew Effect；§6 补 per-prototype quota 或 diversity penalty 讨论 |
| 7 | **Absorb-before-Evict 可能污染 Semantic** | 研究+实验 Agent | 补 absorb 条件过滤 + "w/o Absorb" 消融 + bad case analysis |
| 8 | **Update EMA 过于简单** | 研究 Agent | §6 Discussion 补 adaptive β 讨论；定位 Update 为"轻量实现" |
| 9 | **Compressor 原创性需实验证明** | 实验 Agent | 消融补 mean pooling / self-attn pooling / learned query / Compressor 对比 |

### 写作层面修正（P1）

| # | 问题 | 分配 |
|---|---|---|
| 10 | "首个"表述改为 "to our knowledge" | 写作 Agent |
| 11 | §2 Related Work 补传统 multi-interest 推荐 | 写作 Agent |
| 12 | §1.2 末尾补 "effectiveness validated in §5-§6" 衔接 | 写作 Agent |
| 13 | Baseline 分层组织（Core / Long-history / Memory） | 实验 Agent |
| 14 | 公开数据集构造低质量 proxy + §6.6 局限说明 | 写作+实验 Agent |

### 锦上添花（P2，不阻塞投稿）

- adaptive β per-prototype（实验 Agent）
- prototype diversity visualization（实验 Agent）
- per-prototype memory quota（实验 Agent）
- cold-start / memory warm-start 分析（实验 Agent）

### 预判审稿人问题（4 个 FAQ 预案）

1. **Novelty**: "combines memory networks + multi-interest + retrieval + eviction" → 强调 lifelong GenRec memory lifecycle formulation + 消融证明闭环必要性
2. **Differentiability**: "eviction and EMA are not differentiable" → 区分 trainable path 和 async maintenance，不硬刚"全可微"
3. **Efficiency**: "too complex for <50ms" → 给 latency breakdown + Write/Update/Govern 不在 request critical path
4. **Public Data Validity**: "datasets don't validate multi-behavior quality" → 公开数据验证演化+长序列，工业数据验证质量异质

---

*协作流程枢纽 · 最后更新 2026-06-10*


---

## 附录：研究 Agent → 写作 Agent 输出格式规范（2026-06-12）

# 研究 Agent → 写作 Agent：精读后动作清单标准格式

> **用途**：研究 Agent 每次完成精读升级后，按本格式输出"动作清单"，写作 Agent 直接据此执行修改。
> **创建**：2026-06-12（写作 Agent 定义，user 待确认）
> **原则**：写作 Agent 只接收这种格式的输入，拒绝无结构的"建议一下""看看要不要改"。

---

## 一、单篇精读后的动作清单模板

```markdown
# 精读动作清单：{论文简称}（如 MIND / ComiRec / GEMs / Rec2PM / LIBER ...）

## 精读笔记路径
`reading_notes/{文件名}.md`

## 精读完成日期
YYYY-MM-DD

## 影响 the paper 正文的位置

### §2 Related Work
- **位置**：§2.x {小节标题}，L{行号范围}
- **当前正文写法**：> 引用当前正文原句
- **精读发现**：{精读后发现的事实偏差/遗漏/过强claim}
- **建议修改为**：> 修改后的句子（或"删除该句"/"新增以下内容"）
- **是否必须修改**：必须 / 可选 / 不建议
- **原因**：{为什么必须/可选/不建议，引用精读笔记的具体证据}

### §4 Method
- **位置**：§4.x {小节标题}，L{行号范围}
- **当前正文写法**：> 引用当前正文原句
- **精读发现**：...
- **建议修改为**：...
- **是否必须修改**：...
- **原因**：...

### §5 Experiments
（同上格式，若无影响则写"无"）

### §6 Discussion
（同上格式，若无影响则写"无"）

### §1 Introduction / §3 Preliminary / §7 Conclusion
（通常不需要改，但如果精读发现影响 P1/P2/P3 定义或贡献声明，也按上述格式列出）

## 新增引用需求
- [ ] 需要新增引用：{作者, 年份, "标题"} → 建议放在 §{x.y} L{行号}附近
- [ ] 需要修改现有引用的表述：{当前引用方式} → {修改后引用方式}

## 红线检查
- [ ] 是否涉及"端到端可微"claim → 已弱化为"learning-compatible"？
- [ ] 是否涉及"首个"表述 → 已加"据我们所知"限定？
- [ ] 是否把"我们抽象出的机制"误写成"对方论文原文贡献"？
- [ ] baseline 描述是否忠实原文，未过度简化？
```

---

## 二、批量精读后的汇总动作清单模板

当研究 Agent 一次升级多篇精读笔记后，用此格式汇总：

```markdown
# 批量精读动作清单（{日期}）

## 本轮升级的论文
| 论文 | 精读笔记路径 | 升级内容 |
|---|---|---|
| MIND | `reading_notes/2019_MIND_速读_2026-06-10.md` | 速读→精读 |
| ComiRec | `reading_notes/2020_ComiRec_速读_2026-06-10.md` | 速读→精读 |
| ... | ... | ... |

## 影响 the paper 正文的汇总表

| 正文位置 | 涉及论文 | 当前问题 | 修改优先级 | 详见 |
|---|---|---|---|---|
| §2.3 L{xx} | MIND, ComiRec | 描述不忠实原文 | 必须 | 下方 §2.3 详细清单 |
| §2.3 末尾 | MIND, ComiRec | 与 Semantic Prototype 区分不够清晰 | 可选 | 下方 §2.3 详细清单 |
| §5.3 L{xx} | GEMs | baseline 描述过度简化 | 必须 | 下方 §5 详细清单 |
| ... | ... | ... | ... | ... |

## §2 Related Work 详细清单
（按 §2.1 / §2.2 / §2.3 / §2.4 / §2.5 逐条列出，每条遵循单篇模板格式）

## §4 Method 详细清单
...

## §5 Experiments 详细清单
...

## §6 Discussion 详细清单
...
```

---

## 三、写作 Agent 接收与执行规范

### 接收规则
1. **只接收上述格式的输入**。无结构的"你看看这段要不要改"一律退回研究 Agent 重新格式化。
2. **"是否必须修改"为三级**：
   - **必须**：精读发现事实性错误、过强 claim、误引 → 写作 Agent 必须执行修改
   - **可选**：可以改可以不改，改了更好 → 写作 Agent 自主判断，改则执行，不改则标注理由
   - **不建议**：研究 Agent 认为当前写法可接受 → 写作 Agent 默认不改
3. **行号以提交时的版本为准**。如果正文在研究 Agent 提交后被修改过，写作 Agent 应先 grep 确认当前行号。

### 执行规则
1. 修改前先 `grep -n` 确认目标行内容。
2. 修改后汇报：文件路径 + 行号 + 改前/改后内容（方法论 8 证据标准）。
3. 涉及红线的修改必须二次核验（如"端到端可微"相关替换）。
4. 修改落盘后，在动作清单文件中标注 `✅ 已执行` + 日期。

### 写作 Agent 不接受的输入
- "帮我看看 §2 有没有问题"（无具体位置、无具体问题）
- "MIND 的描述好像不太对"（无精读证据、无建议修改方案）
- 无精读笔记路径的建议（写作 Agent 无法核验事实来源）

---

## 四、落盘位置与命名规范

- 动作清单统一放 `session/` 协作区
- 命名规范：`ACTION_Research Agent_{论文简称}_{日期}.md` 或 `ACTION_Research Agent_批量_{日期}.md`
- 示例：
  - `session/ACTION_Research Agent_MIND_2026-06-12.md`
  - `session/ACTION_Research Agent_批量_2026-06-12.md`

---

*规范由写作 Agent 2026-06-12 定义。研究 Agent 下次输出精读动作清单时请遵循本格式。*
