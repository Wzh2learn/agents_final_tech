---
name: paper-deep-reading
version: 0.1.0
description: |
  论文精读流水线：把一篇 PDF 变成可引用的精读笔记 + INDEX 条目 + 给写作 Agent 的动作清单。
  强制顺序：PDF → Markdown 全文 → 按必读清单精读 → 出 §0-§8 笔记 → 更新 INDEX → 产出 ACTION。
  触发词：精读论文、精读这篇、读这篇 paper、把这篇论文读透、精读笔记、reading notes、
  补读、文献精读、更新 reading INDEX、这篇讲了什么要沉淀。
  示例：精读这篇 arXiv 并出笔记、把 C1 VQL 补读掉给我 ACTION 清单、
  这批 PDF 转 md 后逐篇精读、更新 reading_notes/INDEX.md。
metadata:
  author: user
  category: research-tools
  tags: [paper-reading, reading-notes, literature, research, action-handoff]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch]
---

# Paper Deep Reading — 论文精读流水线

> 一句话：**没有 Markdown 全文就不算精读，没有笔记就不算读过，没有 ACTION 就不算交付。**

## 什么时候用 / 不用

**用：**
- 要精读一篇或一批论文，并沉淀成可检索、可引用的笔记
- PDF 已在手，或需要先检索下载
- 要把精读结论交给写作 Agent 去改正文

**不用：**
- 只是问答式学习、答辩演练 → `socrates`
- 要从论文推导训练策略 → `research-driven-design`
- 要写系统性文献综述（多库检索 + 引用核验）→ `literature-review`
- 要审自己的稿 → `paper-review-check` / `paper-polish-and-audit`

## 目录契约（硬约束）

```
reading_notes/
├── INDEX.md                 # 唯一索引，按研究方向分组
├── <slug>.md                # 精读笔记（放根目录，不放全文）
├── fulltext/<slug>.md       # 转换后的 Markdown 全文
└── pdfs/<slug>.pdf          # 原始 PDF
```

- 禁止根目录散落 `*_fulltext.md`
- 归位用 `mv`，不用 `rm`（安全三步）
- `slug` 约定：`{年份}_{论文简称}_{arxivID}`，如 `2025_VQL_2508.10584`

## 流水线：6 步，顺序不可跳

### Step 0 — 立项（30 秒）

先答三问，写进笔记 §0：

1. 这篇属于哪个研究方向？（对应 INDEX 里的 A/B/C… 分组）
2. 和我们的工作是什么关系？（竞品 / 可借鉴机制 / baseline / 背景）
3. 这次要拿到什么？（一个机制 / 一组数字 / 一句可引用结论）

答不出第 3 问就别急着读——精读是有产出目标的，不是通读。

### Step 1 — 拿到 PDF

- 已有文件：直接进 Step 2，落到 `reading_notes/pdfs/`
- 需要检索：`WebSearch` 找 arXiv 页面 → 核对标题、作者、年份、arXiv ID（**不核实编号不许引用**）→ 下载到 `pdfs/`
- 元数据至少记全：标题、作者、venue、年份、arXiv ID / DOI

### Step 2 — PDF 转 Markdown（不可跳过）

**禁止直接读 PDF 就写笔记。** PDF 解析容易丢图表、公式、段落，上一轮就是这么漏读的。

```bash
# 任选其一，优先生成带标题结构的 md
marker_single reading_notes/pdfs/<slug>.pdf --output_dir reading_notes/fulltext/
# 或
markitdown reading_notes/pdfs/<slug>.pdf > reading_notes/fulltext/<slug>.md
# 兜底
pdftotext -layout reading_notes/pdfs/<slug>.pdf reading_notes/fulltext/<slug>.md
```

**转换验收（三项都过才进 Step 3）：**

- [ ] 章节标题完整（Abstract / Introduction / Method / Experiments / Conclusion 都在）
- [ ] 公式与表格有内容，不是空块或乱码
- [ ] 正文行数合理（一般 400–2000 行；明显偏少说明转换失败）
- [ ] 记下全文 md 的总行数——**笔记里所有证据行号都相对这个文件**

转换失败就换工具重转，不要"凑合读"。

### Step 3 — 精读（必读清单 + 事实卡片）

| 部分 | 要求 | 必须产出 |
|---|---|---|
| **Abstract** | 全部读完 | 一句话贡献（用论文自己的话，先不做项目映射） |
| **Introduction** | **全部内容**读完，不是只读首段 | 问题定义、已有做法的 gap、贡献列表 |
| **Contribution** | 全部读完 | 贡献逐条编号，标注哪几条有实验支撑 |
| **Conclusion** | 全部读完 | 作者自己承认的局限 |
| **Method** | **看情况**，抓核心机制即可，不必逐公式 | 输入 / 输出 / 核心模块 / 数据流 / 关键超参 |
| **Experiments** | 需要引用数字时必读 | 数据集、基线、指标、结论、**没证明什么** |

**事实卡片（引用前必须核）。** 每一条准备写进笔记或正文的结论，都要有一张卡：

```
论点: 该文用低秩分解替代全秩 attention
原文行号: fulltext/<slug>.md L412-418
术语: low-rank efficient attention（低秩高效注意力）
原文引文: "we factorize ... into two low-rank matrices"（≤2 行）
```

**三类标注（混写就是过强 claim 的源头）：**

- `[原文]` 论文明确写了
- `[作者claim]` 论文的主张，但没有实验支撑或只在特定设定成立
- `[我们的推断]` 我们读出来的，不是论文说的

引用时只允许前两类进正文；`[我们的推断]` 必须显式标成"我们抽象出的机制"。

### Step 4 — 写精读笔记（§0-§8）

按 `assets/reading-note-template.md` 落 `reading_notes/<slug>.md`：

| 节 | 内容 |
|---|---|
| §0 | 版本信息：笔记版本、论文出处、更新状态、全文 md 路径与行数 |
| §1 | 一句话贡献（论文自己的 claim） |
| §2 | 问题定义：是什么 / 为什么难 / 与 prior work 的差别 |
| §3 | 方法结构：输入输出、核心模块、数据流 |
| §4 | 训练目标：loss、监督信号、是否端到端、辅助任务 |
| §5 | 实验设计：数据集、基线、指标、证明了什么、**没证明什么** |
| §6 | 局限与攻击点：作者承认的 + 你发现的 + 审稿人可能打的 |
| §7 | 机制抽象：机制类型、可复用部分、边界条件、误用风险 |
| §8 | 与我们工作的关系：可借鉴 / 需防御 / 落正文哪一节 |

§6 和 §7 是全篇最值钱的两节。只复述 §3 的笔记等于没读。

### Step 5 — 更新 INDEX

按 `assets/index-template.md` 改 `reading_notes/INDEX.md`：

- 按**研究方向**分组，不按时间排序
- 每篇一行，必须填：威胁等级 + 笔记文件链接 + 深度（deep-read / skim）+ 关系 + 一句话结论
- 威胁等级：🔴 直接竞品（Related Work 必须正面处理）/ 🟡 同方向不同维度（引用并说明正交）/ 🟢 低威胁或互补
- 新论文先加行（标 unread），读完立刻补一句话结论

### Step 6 — 产出 ACTION（要改正文时）

按 `assets/action-checklist-template.md` 落 `session/ACTION_Research Agent_{论文简称}_{YYYY-MM-DD}.md`，6 列固定表格：

`# | 位置 | 当前写法 | 精读发现 | 建议修改 | 优先级 | 原因`

- **位置**：`§2.3 小节标题，L45-52`，行号以提交时正文版本为准
- **当前写法**：原文引用，不许意译，`grep` 必须能命中
- **精读发现**：只允许五类——事实偏差 / 遗漏 / 过强 claim / 命名冲突 / 引用错位
- **建议修改**：完整可替换的句子，不许写"略""微调"
- **优先级**：`必须`（不改会被审稿人抓）/ `可选`（改了更好）/ `不建议`（思路不成熟）
- **原因**：必须给 `reading_notes/<slug>.md L88` 或全文行号，**不接受"直觉""感觉"**

红线自检（每条 ACTION 都要过）：

- [ ] "端到端可微"类 claim 是否已弱化（learning-compatible / differentiable where needed）
- [ ] "首个 / 第一次"是否已加"据我们所知"
- [ ] 是否把"我们抽象出的机制"写成"对方原文贡献"
- [ ] baseline 描述是否忠实原文，没有过度简化
- [ ] 是否与当前正文术语/结构口径冲突

## 质量门（交付前逐条过）

- [ ] `fulltext/<slug>.md` 存在、非空、验收四项全过
- [ ] 笔记里每个引用行号都能在 fulltext 中 `grep` 到对应内容
- [ ] Abstract / Introduction / Contribution / Conclusion 四部分都有实质内容，不是转述标题
- [ ] 至少 3 张事实卡片，覆盖准备引用的每条结论
- [ ] §6 有"作者没证明什么"，§7 有边界条件和误用风险
- [ ] INDEX 已加行，威胁等级和一句话结论都填了
- [ ] 若要改正文：ACTION 已落盘，6 列无空格，行号已 `grep` 确认

## 反模式

- 直接读 PDF 就写笔记（丢图表公式，且无法给行号证据）
- 只读 Abstract 就总结"贡献"，把作者 claim 当成已验证事实
- 笔记里写"该文提出了 X"却给不出行号
- 把我们的抽象写成对方贡献（引用错位，最容易被审稿人抓）
- 根目录堆 `*_fulltext.md`，笔记和全文混在一起
- ACTION 写"建议优化 §2 相关表述"——无位置、无证据、无替换句
- 精读完不更新 INDEX，下一轮又重读一遍

## 与其他 skill 的关系

| skill | 分工 |
|---|---|
| `pdf-ingestion` | 只解决"PDF 怎么进上下文"；本 skill 解决"读完之后留下什么" |
| `socrates` | 问答式学习与答辩演练；本 skill 是沉淀式精读，产出文件 |
| `research-driven-design` | 拿精读笔记做机制提取与训练策略设计；本 skill 是它的上游 |
| `experiment-autopsy` | 用精读笔记交叉验证实验洞察（读本 skill 的产物） |
| `literature-review` | 多库系统检索 + 综述成文；本 skill 是单篇深挖 |
| `research-writing-skill` | 消费 ACTION 改正文；本 skill 只产出证据和改法 |

## 溯源

本 skill 提炼自仓库内既有规范，条款一字未改语义，只做结构化与流程化：

- `agents_final_tech/docs/governance/reference/RESEARCH_WRITING_WORKFLOW.md` L10-50（精读工作流规范 / 新精读标准，原版）
- `skills-loop-engineering/collaboration/AGENT_COLLABORATION_PROTOCOL.md` §3.1 L289-293（产出归位与流转）
- `skills-loop-engineering/collaboration/ACTION_FORMAT_SPEC.md`（ACTION v2 六列表格与字段定义）
- `skills-loop-engineering/governance/templates/READING_NOTES_INDEX.md`（INDEX 与 §0-§8 笔记结构）
- `skills-loop-engineering/collaboration/CROSS_AGENT_LESSONS.md` L67-71（事实卡片：论点 + 行号 + 译名）

原条款逐字副本见 `references/source-spec.md`。
