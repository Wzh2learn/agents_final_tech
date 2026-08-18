# GTA-2 检查点树构建 SOP + 本项目四层映射草案

> K1 只读精读产出之一。来源：arXiv:2604.15715v1（GTA-2, SJTU/上海AI Lab/腾讯, 2026-04-17）。
> 提取文本 2749 行已分块通读（摘要 / §2 / §3 全节 / §4 / §5 / §6 / §7 / 附录 .1–.6），
> 公式与数字以原文为准；图/表里丢失的信息均已标注。未读或压缩部分见文末"精读范围声明"。

---

## 0 一句话结论

GTA-2 的递归检查点树把"开放长流程交付物"拆成可验证的结果导向子目标树，只让 LLM judge 看最终交付物给每片叶子打 0–10 分，再用 Algorithm 1 自底向上归一化加权聚合出 Root Score——本项目的解析树（文档→表→字段→勾稽）与 QA 树（检索→忠实→数值→引用→拒答）正好是它的两棵特例。

---

## 1 检查点树构建 SOP（从原文提炼，可操作）

GTA-2 的构建与评估协议散在 §3.3.3（formulation）、§3.3.4（construction）、§3.3.5（deliverable-centric evaluation）、Algorithm 1、图 10/17/18/19、§6.4–6.5。下面是一条端到端流水线。

### Step 0 任务与工具前置（前置条件）
- 任务必须：真实性（真实用户需求）、多模态输入、可用工具集内可解（图 1；§3.2 design principles）。
- Tool Solvability 检查：核对整条工具链从开始到结束每一步都能执行，最终解必须由这些工具得出（图 18 任务级 QC 第 1.3 条）。
- 本项目对应：解析链只依赖 `scripts/m1_statement_parser.py` 现有 parser 族（txt/xlsx/pdf/html/msg/OCR 兜底）；QA 链只依赖 :5050 `m2_service` 的检索 + 生成路径，不假设工具集外能力。

### Step 1 任务分解：目标导向的检查点树（§3.3.3 + 图 10 第 1 条）
- 检查点必须是"目标状态"而非"动作序列"（goal-oriented）。原文例子：checkpoint 只限定"生成 2.5–3.5 分钟音频"，不许提到具体工具调用。
- 树：task → sub-task 层级，每个 sub-task 有 `requirement`（可验证要求）+ `weight`（从 {1,2,3} 选）+ 可嵌套的 `sub_tasks`。
- 复杂度规模（图 10 第 3 条）：简单 2–4 个 checkpoint；中等 5–7 个、通常两层嵌套；难 8–10 个。附录（图 14/15 配套）另提 6–15 叶子：易 6–8 / 中 9–12 / 难 13–15。
- 粒度硬约束（图 14-15 的 Checkpoint Design Requirements）：
  - 叶子必须是"一步内可完成"的单个原子动作；
  - 每片叶子可被 LLM judge 客观评估；避免含糊/主观判据；
  - 各 checkpoint 必须有歧义消除的完成判据，聚焦可测输出而非过程描述；
  - 检查点应能映射到具体工具链。

### Step 2 检查点质量验证（自动 + 人工，§3.3.4 + 图 17/18）
- 自动验证三约束（§3.3.4 Task Validation and Checkpoint Regeneration）：
  1. checkpoint 结果导向而非动作导向；
  2. 评估标准不得引用工具调用；
  3. 任务描述不得预写执行步骤。违者迭代重写并重新生成检查点树。
- 人工质量检查四类（图 18）：
  1. Task-level：Clarity & Unambiguity / Realism & Practicality / Tool Solvability；
  2. Workflow-specific：结构化有效性（branching/dependency 至少其一且管道合理）、检查点定义质量（"检索并总结了 3 篇相关论文的关键思想"可验证，"做了些研究"不行）；
  3. Answer & Tool-chain：评估可行性——给定最终输出，评审员能否一致判定对错或满意；
  4. Deliverable 检查：要求聚焦可测输出（对照 §3.3.5 与图 18 第 3 条）。
- 阈值"7 分算过"是后验挑的，不是构造期的硬约束（见 Step 6 的讨论）。

### Step 3 权重分配（{1,2,3} 重要性 + 兄弟级归一化）
- 原文只给了规则与理由：weight ∈ {1,2,3}（图 10 第 2 条；图 14 的 "Assign appropriate weights (1-3) based on importance"）；兄弟节点先归一化再加权平均（Algorithm 1 第 10–12 行）。理由=「重要性」(importance)。
- 原文没有给出任何"权重如何定"的启发式（无公式、无 default 表）；这是一个开放设计点 → K5（PSO 落点）可在这补：用判别力/敏感度目标搜权重。
- 我们自己的草案建议：每棵子树权重先按"对下游使用的关键性"定 1/2/3，再在同一父节点下归一化；勾稽级权重给最高，因为它是最终可信度的闸门（见 §3 映射）。

### Step 4 deliverable 提取与预备（§3.3.5 + 图 19）
- 最终交付物 D 与检查点树一起交给 judge；judge 只评交付物（不看推理链/工具日志）。
- 对多模态产物原文采用特定预处理（图 19 prompt 第 1–2 行）：
  - 所有生成的文件与图片上传；视频转为若干图像帧；音频只检查存在性。
- 缺失文件必须低分（图 19："If required files are missing, give a low score"）。
- 本项目对应：解析链的"交付物"= 解析结果结构（json + 勾稽 checks）；QA 链的"交付物"= 模型答案文本 + sources 列表；judge 输入 = 答案 + 检索上下文 + 来源列表 + 期望（见 §4 QA 树）。

### Step 5 LLM judge 叶子打分（Algorithm 1 第 4–9 行 + 图 19）
- 输入三元组：I ← (D, Requirements(n), Rubric(n))（Algorithm 1 第 6 行）；输出 s_n ∈ [0,10] 整数分 + 简短理由。
- 图 19 实际 prompt（照抄）：
  ```
  You are a professional LLM Agent evaluator. All of the generated files and images from the LLM Agent are uploaded,
  videos are converted to several image frames, and audio files are checked for existence.
  Original task: {task}
  Final answer: {final_answer}
  Checkpoint requirement: {req}
  Please score this checkpoint from 0 to 10. If required files are missing, give a low score.
  Only output valid JSON: {"score": number, "analysis": "short explanation (<80 words)"}
  ```
- judge 用強 LLM（GPT-5.2），每叶子只评一次（k=1）；换 Gemini-2.5-Flash 做鲁棒性验证，排名 Spearman ρ=1.0（§6.4.3 表 13），与人工 ICC 0.83–0.93（表 11/12）。

### Step 6 Algorithm 1 递归聚合（公式照抄，原文 §3.3.5 / Algorithm 1）
```
Algorithm 1 Recursive Checkpoint Scoring
Require: Checkpoint tree T with root r; final deliverable(s) D; LLM judge M
Ensure: Final score S(r) ∈ [0, 10]
 1: function EvalTask(T, D, M)
 2:    return ScoreNode(r, D, M)
 3: end function
 4: function ScoreNode(n, D, M)
 5:    if IsLeaf(n) then
 6:        I ← (D, Requirements(n), Rubric(n))
 7:        s ← LLMJudge(M, I)                     ▷ s ∈ [0, 10]
 8:        return s
 9:    end if
10:    C ← Children(n)
11:    w ← [Weight(c) | c ∈ C]
12:    w ← NormalizeWeights(w)                    ▷ Σ_c w_c = 1
13:    S ← 0
14:    for all c ∈ C do
15:        sc ← ScoreNode(c, D, M)
16:        S ← S + Weight(c) · sc                 ▷ use normalized weights tree
17:    end for
18:    return S
19: end function
```
- 叶子：s_n = LLMJudge(M; D, Req(n), Rubric(n)) ∈ [0,10]。
- 非叶子：s_n = Σ_{c∈Children(n)} w̃_c · s_c，其中 w̃_c = w_c / Σ_{c'∈Children(n)} w_{c'}, Σ_c w̃_c = 1（公式同 长流程.md 与 Algorithm 1 第 10-16 行）。
- 根：S_root = s_r ∈ [0,10]。可执行要点：
  1. 先把每片叶子按请求打 0–10→存值；
  2. 自底向上 DFS，每个非叶子节点把自己的 children 权重归一化（除以兄弟和），再加权求和；
  3. 根即全任务分；同一棵树同时得到 Root / Leaf SR（§6 讨论）。
- 本 SOP 的可执行校验：任何子树分都可以由它的叶子分 + 权重重算出来（幂等，无 LLM 参与）——这条性质是 K2 评测协议形式化的基础（聚合脚本不依赖 LLM）。

### Step 7 阈值与成功率（§4.2.2 + §6.4.1）
- Root SR = (1/N) Σ_i 𝟙[S_root^(i) > k]，默认 k=7；Leaf SR = #{leaf ℓ: s_ℓ > k} / #all leaves；Tool SR = #valid tool calls（无 sys-error/syntax-err）/ #all tool calls。
- k 的选择：阈值敏感性实验（图 8），k=5 聚类、k=9 全零、k=7 区分度最佳；个别模型对阈值敏感（Claude-Sonnet-4.5 在 k=6 最高、k=7 掉到近最低）。
- 建议：本项目先不硬编"7 分"，沿用现有 0–5 四维 judge + 各自判定语义（见 §4），只在 K2 形式化时做阈值敏感性图。

### Step 8 迭代优化信号（§6.5，非必须但推荐）
- 把叶子级低分当"细粒度失败诊断"反馈给 agent 重跑：GPT-5 初稿 2.83 → 粗反馈（只说不对）2.93（+4.05%）→ checkpoint 细反馈 3.15（+12.03%）。
- 说明：同一套 checkpoint 树可同时当评估器和优化器。对应本项目：勾稽 FAIL / unmapped 高 / judge 低维 → 回填 schema/synonym 或改写 prompt（即 docs/30 VGMC 自学习闭环的"回归门禁 → 规则落库"的已有流程）。

### Step 9 失败归因（§5.3，平行维度）
- 阶段级（表 8）：PLAN / REASON / EXECUTE / GROUNDING / REFINE / ASSEMBLE / HANDOFF / VERIFY / OTHER；EXECUTE（33–34%）+ HANDOFF（17–25%）占比最大，REASON 仅 3–7%。
- 三级失败分解（表 10）：A 叶子级局部失败 / B 组合失败（子目标基本完成但整合不成） / C 交付物级失败（格式/打包/提交不合规）。标签由 LLM（GPT-5）按附录 .3 的 tier 分类 prompt 打（图 20 照抄见下）。
  ```
  You are classifying one checkpoint by failure depth tier.
  Allowed tiers and labels:
   • A: Leaf-level failure (local sub-goal not completed; e.g., incorrect extraction, missing section, or failed substep)
   • B: Mid-level composition failure (sub-goals are mostly completed, but integration or coordination across components fails)
   • C: Root-level deliverable failure (final output fails in packaging, formatting, or submission compliance)
  Guidelines: Use the requirement text as the primary signal. Use structural context (leaf status, depth, parent) as auxiliary.
  If the requirement mainly concerns final handoff, file export, formatting, filename, or submission compliance, prefer C.
  If the requirement mainly concerns combining multiple completed parts into a coherent module/page/report/workflow, prefer B.
  If the requirement is atomic or local (e.g., a single extraction, check, section, or substep), prefer A.
  A non-leaf node can still be classified as A if its requirement is semantically local.
  Output: {"tier": "A|B|C", "tier_label": ..., "confidence": 0.0-1.0, "reason": "≤60 words"}
  ```
- 对我们最有用的转移：C 级（交付物/格式/打包不合规）对应本项目"勾稽 FAIL / 输出格式不合规"；B 级对应"表间不一致 / 跨文档聚合没对齐"；A 级对应"单表解析错 / 单个字段错"。

---

## 2 验证数据（便于引用原文）

- 规模：GTA-Atomic 229 任务 / 728 步 / 14 工具；GTA-Workflow 132 任务 / 37 工具 / 1156 叶子（§3.4 表 4）。
- 结果：最强 Gemini-2.5-Pro Root SR 14.39%（Root Score 3.64）；Tool SR 91.20% → 反差"调对工具 ≠ 任务干成"（表 6）。
- harness 对比（表 7）：同底座 Claude-Sonnet-4.5，Lagent Root SR 0% → OpenClaw 50%；Root Score 2.49 → 6.82；Leaf SR 10.14% → 73.55%。
- judge 可信度（表 11/12/13）：Root 层 HumanAvg vs LLM judge Pearson 0.966 / ICC(2,1) 0.928 / MAE 0.744；76.7% 任务误差 ≤1 分；换 judge 模型排名 Spearman ρ=1.0。成本 ~$5/132 任务（表 14）。
- 反馈实验（表 15）：见 Step 8。
- 复杂度影响（图 4/5）：任务叶子从 3–7 增到 13–19 时 Leaf SR 下降（Gemini 例外）；交付物类型差异：PDF/Text/HTML 高、Struct. Data（CSV/XLSX/JSON）2.62 与 PPTX 2.79 最低。
- (图/表信息丢失标注：图 1/2/3/6/7 中布局示意无法从文本重现；图 4/5/8 数值已提取为文字；表 13 只保留了 Gemini/DeepSeek/Qwen 三行与 Spearman/Kendall ρ=1.00 结论。)

---

## 3 本项目四层检查点映射草案（解析树）

> 依据：`scripts/m1_statement_parser.py`（ParsedDoc/ParsedTable、best_schema_match→mapping/hits/unmapped、reconcile→checks+disposition）、`scripts/m1_scenario1_regression.py` 门禁、`tests/baselines/scenario1_baseline.json`。均为现状核实，非虚构。

### 3.1 解析树层级定义

| 层级 | 检查点（叶子/中间） | 可验证判据（现有产物） | 聚合角色 |
|---|---|---|---|
| 文档级 | 解析成功 ok + kind + 页数/图数 + 耗时 | `doc.ok`；PDF 页数（parse_pdf 的 `pdf.page_count`）；OCR 引擎日志（elapsed_s per engine）；`needs_ocr`/`ocr_used`/`ocr_engine` | 根下第一层：文档没解析出来整树归零 |
| 表级 | 表边界识别 + 表头识别 | `doc.tables` 列表；每表 `headers` 非空；`find_tables`→text→coord→OCR 的策略链生效 | 中间层：决定表数/每表行数列数 |
| 字段级 | 映射命中 + unmapped 归零 | `match.hits`、`hit_rate`、`mapping`、`unmapped`；LLM fallback 的 `llm_extracted`（默认关） | 中间层：决定字段可用度 |
| 勾稽级 | 恒等式通过 | `reconcile` checks（市值勾稽/币种一致/日期格式/静默错配嫌疑；每项 disposition=real_pass/skipped/fail） | 顶层汇总：最终可信度闸门 |

### 3.2 权重设置建议（带理由）

| 节点 | 建议权重基 | 理由 |
|---|---|---|
| 文档级 解析成功 | 3 | 硬闸门：ok=False 则无后续可评（图 19 "If required files are missing, give a low score" 同构） |
| 文档级 页数/耗时 | 1 | 信息性指标，非质量；归并到一个"解析效率"叶子 |
| 表级 表边界 | 2 | 表数缺失/多出来都说明策略链失败（Gap1 NCAMC 垂直布局靠坐标重建） |
| 表级 表头识别 | 2 | 与字段级强相关，但在"表找到了但表头错"时单独诊断 |
| 字段级 映射命中 | 3 | 直接决定字段可用度；scenario1 门禁本身按 hit_rate 判定（同步位） |
| 勾稽级 各恒等式 | 3 | 最终可信度闸门；市值勾稽 fail 即整份解析不可信（jiaxing 合计行重复计数案例） |
| LLM fallback 成功数 | 2（仅当开 --llm-fallback 时参与） | 说明 unmapped 收敛；默认关闭不参与 |

- 归一化：按 Algorithm 1 同父节点内归一化（文档级三兄弟、勾稽级四 check 内各自归一）。具体数值留给 K2 JSON schema 的 `weight` 字段（{1,2,3}）采原文约束。
- 说明：以上权重是"建议草案"，原文只约束取值范围与归一化机制，不约束具体取多少（Step 3 已注明）。

### 3.3 映射到现有门禁的对照
- scenario1 回归门禁（`scripts/m1_scenario1_regression.py`）≈ 字段级 + 表级：确定性样本（嘉合×8 / NCAMC / HTML×3）table_count 与逐表命中率精确一致；OCR 样本（华泰/TraFax/WaveFax）±10pp 容差（tolerance.ocr_hit_rate_pp）。
- 勾稽 reconcile（`reconcile()`）已是现成的"勾稽级"检查点集合（4 项 check + disposition 三态）。
- 差异：现门禁是"逐来源独立判定 PASS/FAIL"，没有层级；K2 升级点就是把这些判定换成树 + Algorithm 1 聚合，得到"解析 Root Score"（0–10 或归一化 0–1）。

---

## 4 本项目四层检查点映射草案（QA 树）

### 4.1 层级定义（对齐现有四维 judge）

| 节点 | 对应现有资产 | 新增定义 |
|---|---|---|
| 检索质量 | retrieval sources（`m2_service.retrieve` → `smart_retrieve` + rerank）| 检查点=检索是否命中应命中的样本/表；可用确定性 check `source_required` 或 RAGAS Context Precision/Recall 对照（指标公式.md 第四类） |
| 忠实度 | judge dim 1 `faithfulness`（只允许用检索上下文，禁止参考期望答案）| 同现有 rubric；脱敏掩码补全猜测视为扣分（现有已覆盖） |
| 数值正确性 | judge dim 2 `numeric_correctness`（唯一允许看期望值的维度）；确定性 check `exact_numeric`；NF 数值忠实度（`number_grounding.check_answer`，掩码感知）| 现状：确定性 exact_numeric + judge numeric_correctness 双轨；NF 是"数值 claim 与检索落地"的确定性核验，对应 GTA-2 的"结果导向"叶子 |
| 引用质量 | judge dim 3 `citation_quality`（来源非空、具体、与来源列表一致）| keep；"拒答题来源为空不扣分"豁免保留 |
| 拒答恰当性 | judge dim 4 `refusal_appropriateness`（不可答题明确拒答；可答题不误拒）| keep；可加确定性 check：`unanswerable` 题必须含"未找到/无法回答"字样（现有 `refusal_expected`） |

### 4.2 树形组织（与四维平铺的差别）
- 现 judge 是"整答级四维平铺"（每维 0–5，`:8004` temp=0）。GTA-2 式组织建议：
  - 根 = QA Root Score；
  - 中间 = 四维（faithfulness / numeric_correctness / citation_quality / refusal_appropriateness）+ 数值忠实度 NF 作为 numeric_correctness 子树的一支（确定性优先，LLM judge 只处理无法确定性的部分）；
  - 叶子 = 单题单维判定（现 judge 结构天然就是叶子级）；新增"若需递归"的聚合层（多题多轮可加权）。
- 权重建议：数值正确性 ≥ 忠实度 > 引用质量 ≈ 拒答恰当性（理由：反编造是甲方底线，NF 已是确定性闸门；引用/拒答是已有豁免规则的第二层）。同一父节点内归一化。
- 回归门禁对照：run_eval.sh 第 2 步确定性 16/16、第 3 步 NF、第 4 步四维 judge —— 与 GTA-2 的"叶子判定 + 聚合"结构一致，只是还没有聚合层与权重。

### 4.3 与 GTA-2 的三类 SR 对应（一页映射）

| GTA-2 指标 | 公式（原文） | 本项目对应 | 备注 |
|---|---|---|---|
| Root SR | (1/N) Σ 𝟙[S_root>k], k=7 | 解析 Root SR=「解析树聚合后超阈值样本比例」；QA Root SR=「QA 树聚合后超阈值题比例」 | k 待 K2 用敏感性实验定（不直接抄 7） |
| Leaf SR | #{leaf: s_ℓ>k}/#all leaves | 解析 Leaf SR=「表级/字段级/勾稽级叶子通过率」（现 scenario1 门禁的 per-source 命中率可映射）；QA Leaf SR=「四维各维通过题数/总题数」（现 judge 每维 0–5，可设每维通过线比如 ≥4） | 细粒度诊断 = GTA-2 的"哪棵子树拖后腿" |
| Tool SR | #valid tool calls / #all tool calls | 本项目不是"工具调用"场景；对应替代 = 引擎级/调用级成功率：OCR 引擎链成功（`ocr_engine_log`）、检索链路（vector/bm25/fallback）成功、`m1_scenario1_regression` 各源调用成功 | 用途同原文：戳破"步骤都执行了但交付失败" |

- 额外可得（建议 K2/K6 论证）：Score/Cost = S_root / 总成本（原文表 7 用）；效率类：Total Time。

---

## 5 精读范围声明（GTA-2 篇）

- 页数：PDF 31 页正文+附录（文本 2749 行）。已读：摘要、§1、§2、§3 全部子节、§4 全、§5 全、§6 全、§7、附录 .1/.2/.3（prompts 图 9/10/17/18/19/20）、.4（失败分类定义）、.5（任务示例）、.6（GTA-Atomic 构造）。
- 跳过：参考文献（§8 起）未逐条读；表格 16/17 工具清单只提取了与 SOP 相关的分类信息（未逐行核对）；pdf 布局图（图 1/2/3/4/5/6/7/8）无法从文本完全恢复，关键数值均已用文字标注。
- 图表信息丢失处均已标注"(图/表N: 内容简述)"（见 §2 与各节内标注）。
