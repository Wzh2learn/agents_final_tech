# Paper E 升级方向 v1

> 日期: 2026-10-15 | 作者: Loop D | 触发: 导师/架构师 2026-10-15 裁决 + owner「升级后的 Paper E 更合理泛化；参考近期相关工作把质量做强；串行推进；配 GB10 Loop A + 独立 Loop C」
> 性质: 只读评估 + 方向与执行设计。**不改**冻结稿数字 / claim / 证据哈希；**不重开** Route B / FinQA binding / PR-03。
> 冻结稿 `paper/saner_rene_manuscript_v1.md`（T1「Visibility Is Not Detection」，SANER RENE NegativeResult）继续作为 **fallback 完整案例稿**，在升级结论落地前不废弃、不覆盖。

## 0. 结论摘要

1. **导师给的三篇工作不够新**：oracle 问题那篇是经典旧文，ACES 是 2022，只有 *Auditing the Audit* 是 2026。方向对，citation 需要换新。
2. **领域「多阶段文档智能管线」撑得住，但要收紧口径**：它准确描述的是**我们自己构造的**那套评测流水线（parsing tree + QA tree，12 scored leaves），content 来自真实公开金融表（TAT-QA 血统，95 tables）；但它是 `n=1` 的 bespoke 构造，外部效度是最大风险，不能外推成「document AI 的通用盲点」。
3. **升级后的科学问题（采纳裁决）**：*共享观测通道的多个 checker，什么时候会一起漏掉任务相关错误、或一起把合理变化误判成错误？补一份不共享原判断路径的独立任务级证据，能否在可比成本下减少这种误判？*
4. **执行**：Layer 1 可行性探针先行（本次 Loop A 任务 + Loop C 独立审计）；Layer 2/3 视 Layer 1 结论再定。串行，不并行铺开。

## 1. 问题一：三篇工作够新吗？

导师引用的三篇，按"近 2 年（2024+）"标准核对：

| 引用 | 年份 | 判定 | 说明 |
|---|---|---|---|
| Test oracle（Offutt, testOracle.pdf） | 经典（约 1999 前） | **不够新** | oracle problem 是 1980s–2010s 的基础工作，做 motivation 可以，不能当近期 near-neighbor |
| ACES（WMT 2022, aclanthology 2022.wmt-1.44） | 2022 | **不够新（4 年前）** | challenge-set 思路正确，需要 2024+ 的迭代版本 |
| Auditing the Audit（arXiv 2607.02586） | 2026-07 | **是新** | 审计程序本身的偏差（无效操作、评分失真、统计配对），直接可用 |

注：**当前稿件本身不旧**——它已引 2026 年多篇（AgentChaos 2608.06790、AgentProcessBench 2603.14465、Chung 2606.15673、GTA-2 2604.15715、Kendiukhov 2603.03493、Du 2606.24381）。旧的是**导师口头给的那三篇**。

### 近年（2025–2026）已验证的替代 / 补充清单

全部经 arXiv 官方 API 于 2026-10-15 逐条核验（id / 发布日期 / 标题均为原文）。用途标注为**可支撑的论点**，不是"已证明我们成立"。

| 用途（可支撑的论点） | arXiv | 日期 | 标题 |
|---|---|---|---|
| 可解码 ≠ 可检测；correction 后"sensitivity≠usability" | 2607.19393 | 2026-07 | Decodable but Not Detectable: A Leakage Fingerprint for Near-OOD Benchmarks |
| 分数差 ≠ 排序能力（更严粒度下 rank reversal） | 2608.11985 | 2026-08 | Auditing Frame-Level AUC in Weakly Supervised Video Anomaly Detection: Granularity, Resolution, and Scene Bias |
| 同源 checker 可能继承作者盲区（明确写成 conjecture） | 2608.28631 | 2026-08 | CrossAudit: A Git-Native, Cross-Vendor Audit Loop for Agentic Science |
| 多 checker 比较需 matched route contrast 才可识别 | 2610.02808 | 2026-10 | ROUTEAUDIT: Interaction-Aware Identification for Budgeted Multi-Verifier Routing |
| judge 只看 rubric 就预判分数 / 不对"反转"更新 | 2609.02942 | 2026-08 | Judging LLM-as-a-Judge: Concerning Rubric Artifacts in LLM-based Automated Text Generation Evaluation |
| judge 验证的统计设计（稀疏重叠 → 从推断到设计） | 2609.31857 | 2026-09 | LLM Judge Validation Under Sparse Overlap: From Inference to Design |
| 构念效度 / 潜结构（人类与 LLM 是否同构） | 2608.15630 | 2026-08 | Do Assessment Instruments Measure the Same Thing for Humans and LLMs? A Latent Structure Analysis |
| benchmark 审计需负对照 + 灵敏度界 | 2609.22183 | 2026-08 | CleanScore: Black-Box Benchmark Audits with Negative Controls and Sensitivity Bounds |
| tie / order 不变性是评测协议的一部分 | 2609.26977 | 2026-09 | Tie Handling Is Part of the Evaluation Protocol: An Order-Invariance Audit for Tie-Heavy Recommender Scores |

**取舍**：方向类 motivation 引 *Auditing the Audit*（2026）；"visibility≠detection" 引 2607.19393；"分数差≠排序能力" 引 2608.11985；"共享盲区是 conjecture 而非定论" 引 2608.28631；"多 checker 比较要 matched contrast" 引 2610.02808；"judge 可能不响应被审对象" 引 2609.02942。正式进 BibTeX 前，每篇仍需读全文（title/作者/venue/DOI 至少双源），**不得只按标题类比**。

## 2. 问题二：领域 / 数据集撑得住吗？

### 2.1 我们实际拥有的

- **自己构造的 staged document-intelligence evaluator**：decode → table structure → field mapping → arithmetic reconciliation → retrieval-grounded QA；12 个 scored leaves 分属 parsing tree 与 QA tree（`paper/method_theory_materials_v1.md`、`docs/research/stage_e_118_quantification_v1.md`）。
- **真实公开金融表 content**：normalized public TAT-QA table base（无客户数据），95 张 injection-carrier tables + 118 条 controlled header perturbations，6 个 defect family；injection 由 `scripts/research/drift_inject.py`（seed 42, ratio 0.3, deterministic）生成（`docs/experiments/2026-08-18_drift_injection_v0.md`）。
- **第二条 dataflow（失败案例）**：FinQA program perturbations，89 rows / 30 clusters；结果 `V=89/89, D=0/89, O=0/89` 是 measurement-object mismatch（`research/finqa_v2_20261010/`）。

### 2.2 站得住的部分

- 领域名称**准确**：这确实是 document-intelligence 的多阶段流水线评测，且 content 有公开数据集血统（不是凭空合成表）。SANER RENE（NegativeResult / Replication）本就接受这种**工程实践型测量研究**。
- 6 个 family + family-resolved visibility 让"分阶段"不是空话：可观测边界按 stage/family 变化，这正是"多阶段"才有的现象。
- 升级方向（共享观测 checker）**天然契合**本领域：field hit-rate matcher、semantic judge、OCR-like normalizer 共享同一套归一化/表示 → 正适合问"它们会不会一起漏"。

### 2.3 站不住 / 薄弱的部分（必须诚实写进 limitations）

- **n=1 + bespoke**：pipeline 是我们自己造的，"多阶段文档智能"描述的是**这套构造**，不是"文档 AI 系统的一般规律"。这是 reviewer 最强的 reject 点（bespoke self-audit / weak external validity），升级的 Layer 3（真正独立环境）才可能缓解。
- **fault space 窄**：只有 **header** 扰动，没有 document decode / segmentation / OCR 级 fault → 不能说"document intelligence 的盲点"，只能说"header-drift 这一族的观测边界"。
- **无自然失败分布**：全是 synthetic injection，不测真实失败分布。
- **第二条 dataflow 失败**：FinQA 没跑通（mismatch），所以目前**没有**第二个可用的独立 pipeline。

### 2.4 建议口径（一句话）

> 领域定成「**一个受控构造的多阶段文档智能评测器**」而不是「文档智能管线」。数据集（TAT-QA 血统表）**足够支撑**这个口径与 RENE NegativeResult 定位；不够支撑任何"document AI 通用"的泛化。升级研究的价值不在扩大领域，而在**把评价误判这件事测准**——这正好绕开 n=1 的外部效度短板。

## 3. 升级后的科学问题与边界（采纳裁决）

**核心问题**：在多阶段文档智能任务中，共享观测 / 表示方式的多个 checker，是否会**共同**漏掉任务相关错误、或**共同**把合理变化误判成错误？补一份独立任务级证据，能否在**可比成本**下改善判断？

**三个必须分清的对象**：

- *影响任务结果的错误*（task-changing error）：答案/指代/单位真的变了，且能对应到具体任务（选错时期、单位换算错、引用了不支持答案的单元格）。
- *不影响任务结果的合理变化*（legitimate change）：任务输入合法变化，正确答案随之改变，或指代不变 → 不是错误。
- *证据不足，不能判定*（insufficient evidence）：语义边界需人工裁决 → 不得用同一模型多问几遍冒充独立 gold。

**两条禁令（来自裁决）**：

1. "对错"由**任务目标 + 原始材料 + 独立核验**定义，**不得**由被审 checker / 同一 judge 自己定义。
2. 合法改变任务输入（正确答案可随之变）与向执行过程注入故障（保持原任务目标、真实重执行）**不能混用**——混用就是下一个 FinQA 式测量错配。

## 4. Layer 1 可行性探针设计（本次执行）

目的：**先回答"独立任务级 gold 到底造不造得出来"**，不急着跑大规模对照。

范围与步骤（详见 `research/paper_e_upgrade_2026/loop_a_L1_feasibility_contract.md`）：

1. 定位冻结 Stage E artifacts（118 injections / 6 families / 95 tables）与 checkpoint forest 配置。
2. 选 **12–16 个 dev probe cases**，覆盖 6 个 family（必含 OCR-like 0/13 与 arithmetic/numeric 族）。
3. 对每个 case：写出"这条扰动可能改变哪个**具体任务**的答案"，再用**表 content + 任务定义**独立判定——**不读被审 checker 的判定**。
4. 三分类：`TASK_CHANGING_ERROR` / `LEGITIMATE_CHANGE` / `INSUFFICIENT_EVIDENCE`。
5. 交付：可行性判定（constructible? yes/no/partial）、可机读 schema、ambiguity 清单、逐条 evidence 依据。

**停止条件**：若独立 gold 造不出来（大量 INSUFFICIENT_EVIDENCE 或无法不依赖 checker）→ Layer 1 = NOT_CONSTRUCTIBLE，记录并报告 owner，**不**硬凑。

## 5. Loop A / Loop C 分工

| Loop | 角色 | 本次任务 | 通道 |
|---|---|---|---|
| A | 执行 | `pe-l1-feas`：Layer 1 可行性探针（只读冻结件，写新 run 目录） | GB10 `loop_ac_launcher.sh start a` |
| C | 独立审计 | `pe-l1-audit`：**独立**重判子集 + 查分类非循环、非 checker 自证 | GB10 `loop_ac_launcher.sh start c`（read-only） |

纪律（依 `docs/research/DELEGATION_HARNESS_FAILURE_AUDIT_v1.md`）：**只用设计车线 launcher，不用 app sub-agent**；Loop A 禁 git 操作；Loop C read-only、不改 Loop A 产物。

## 6. 护栏（本轮不可越）

- 不改冻结数字：95 / 118 / 96 / 0-13 / 1.0 / 0.3333 / 0.1667 / V-D-O 等。
- 不改已冻结 claim；升级稿与冻结稿**并行存在**，升级结论落地需作者级裁决才替换。
- 不重开 Route B / FinQA binding / PR-03；不启动 synthesis / automatic selector。
- 新增研究用独立版本与证据包；不得把旧案例分析当"未见测试"；阈值在 dev 侧定，不看 test 错误后调。

## 7. 与冻结稿的关系

冻结稿（T1）保持 `SUBMISSION_DRAFT_COMPLETE = YES`，是当前唯一**可提交**产物与 fallback。升级工作产出的是**新证据包**，只有 Layer 1 出可行结论、并经作者裁决，才动主稿 framing。在此之前，manuscript / claim matrix / scope lock 一律不动。
