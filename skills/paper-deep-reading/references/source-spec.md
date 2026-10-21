# 原条款副本（溯源用，勿修改语义）

> 本文件逐字保留 `paper-deep-reading` skill 提炼所依据的原始条款。
> 上游文档若变更，以原文档为准，并同步修订本文件与 `SKILL.md`。

---

## 一、精读工作流规范

**出处**：`agents_final_tech/docs/governance/reference/RESEARCH_WRITING_WORKFLOW.md` L10-24
**创建**：2026-06-05（user 指正，必须遵守）

### 规范 1：PDF 必须先转 Markdown 再精读，不要直接读 PDF

- 上一轮 Agent 下载 PDF 后**直接读 PDF 内容**精读，导致**阅读不全面**（PDF 解析易丢图表/公式/段落）
- 正确流程：`arXiv 检索 → 下载 PDF 到 reading_notes/pdfs/ → 转成 Markdown 全文 → 精读 Markdown`
- 转换工具建议：`marker` / `markitdown` / `pdftotext` 等，转出的全文 md 放 `reading_notes/fulltext/`
- 精读笔记必须基于**转换后的完整 Markdown 全文**，确保不漏内容

### 规范 2：Paper 全文统一归位到 `reading_notes/fulltext/`

- 要求：①所有 `*_fulltext.md` 全文统一放 `reading_notes/fulltext/`
- ②把根目录散落的全文 `mv` 进去（mv 不 rm，符合安全三步）
- ③以后新转换的全文直接落 `fulltext/`
- 目录分工：`pdfs/` 放原始 PDF；`fulltext/` 放转换后的 md 全文；`reading_notes/` 根目录放**精读笔记**（不放全文）

---

## 二、新精读标准

**出处**：同上 L34-50
**创建**：2026-06-05（user 定，以后统一遵守）

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

## 三、Research Agent 产出归位与流转

**出处**：`skills-loop-engineering/collaboration/AGENT_COLLABORATION_PROTOCOL.md` §3.1 L289-293

- 产出归位：精读笔记→`reading_notes/`；全文→`reading_notes/fulltext/`；PDF→`reading_notes/pdfs/`
- 禁止：根目录散落 `*_fulltext.md`
- 流转给 Writing Agent 必须走 ACTION 格式（§0.5）
- 精读标准：Abstract/Introduction/Contribution/Conclusion 必读全，Method 抓核心
- 动作清单推荐表格形式（位置|当前写法|精读发现|建议修改|优先级|原因，避免重复段落冗余）

---

## 四、ACTION 格式（v2 表格版）

**出处**：`skills-loop-engineering/collaboration/ACTION_FORMAT_SPEC.md`
**创建**：2026-06-15；**v2 更新**：2026-06-26（段落式 → 6 列表格）

原则：写作 Agent 只接收这种格式，拒绝无结构的"建议一下""看看要不要改"。

字段要求：

| 字段 | 必填 | 说明 |
|---|---|---|
| 位置 | ✅ | `§章节号 小节标题，L行号` |
| 当前写法 | ✅ | 引用正文原句，不允许意译，grep 必须能命中 |
| 精读发现 | ✅ | 事实偏差 / 遗漏 / 过强 claim / 命名冲突 / 引用错位 |
| 建议修改 | ✅ | 修改后的完整句子，不允许"略""微调" |
| 优先级 | ✅ | 必须 / 可选 / 不建议 |
| 原因 | ✅ | 精读笔记行号或公开论文证据，不接受"直觉""感觉" |

---

## 五、精读笔记结构（§0-§8）与威胁等级

**出处**：`skills-loop-engineering/governance/templates/READING_NOTES_INDEX.md`

- §0 版本信息（笔记版本、论文引用、更新状态）
- §1 一句话贡献（论文自己的 claim，不做项目映射）
- §2 问题定义（是什么 / 为什么 / 与 prior work 差别）
- §3 方法结构（输入输出 / 核心模块 / 数据流）
- §4 训练目标（loss / 监督 / 端到端 / 辅助任务）
- §5 实验设计（数据集 / 基线 / 指标 / 证明了什么 / 没证明什么）
- §6 局限与攻击点（作者承认的 + 隐藏的 + 审稿人角度）
- §7 机制抽象（类型 / 可复用机制 / 边界 / 误用风险）
- §8 与我们的关系（怎么相关，借鉴什么、防御什么）

威胁等级：🔴 直接竞品（必须讨论+准备 rebuttal）/ 🟡 间接（引用+说明正交）/ 🟢 低威胁或互补。

---

## 六、事实卡片纪律

**出处**：`skills-loop-engineering/collaboration/CROSS_AGENT_LESSONS.md` L67-71

- **场景**：研究 Agent 曾在 Related Work 引用某 baseline 的一个 Challenge，写作 Agent 核对精读笔记时发现原论文表述与引用不符
- **教训**：精读笔记是引用事实的唯一权威来源（SSOT）。凭印象引用竞品机制容易过强 claim 或错位归因。精读时若没记录具体行号证据，写作 Agent 无法验证
- **建议**：精读必产出"事实卡片"（论点 + 原文行号 + 译名），写作 Agent 引用前 grep 笔记确认。无笔记支撑的引用标 🟠 建议补

---

## 七、副本差异说明（2026-10-19 核查）

| 副本 | 状态 |
|---|---|
| `agents_final_tech/docs/governance/reference/RESEARCH_WRITING_WORKFLOW.md` | 原版，含真实论文名（AMEM4Rec_2602.08837 / Rec2PM_2602.11605 / MARS_2605.14401） |
| `skills-loop-engineering/collaboration/RESEARCH_WRITING_WORKFLOW.md` | 脱敏版，论文名替换为 `{PaperA}` / `{PaperB}` |
| `agents_final_tech_test/docs/governance/reference/RESEARCH_WRITING_WORKFLOW.md` | 与脱敏版一致 |

三份均为 412 行，规范条款一字不差，仅 5 处示例/论文名不同。

**`research-paper-pipeline`**：治理文档（`AGENT_COLLABORATION_PROTOCOL.md` 路由表）标注为"写论文/顶会/精读"可用，但仓库与 `agents_final_tech` git 历史中均查无此路径。本 skill 即为其"精读"职责的落地实现。
