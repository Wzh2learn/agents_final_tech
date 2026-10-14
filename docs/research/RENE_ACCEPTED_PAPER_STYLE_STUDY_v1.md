# SANER RENE 录用论文风格学习 v1（2026-10-14）

> 目的: owner 指示研究目标会议录用论文的写作风格。素材边界与逐字来源见 `research/rene_style_20261014/SOURCE_MATERIALS_v1.md`（**2/4 篇全文可读**；#1/#4 仅摘要级——IEEE 付费墙）。本件只做"学习与对照检查"，**不改 Paper E 稿**。

## 1. 读取层级

| # | 论文 | 读取层级 |
|---|---|---|
| 1 | Gerhold et al. 2024, The Limits of the Identifiable | 摘要级（本仓两处核验转述） |
| 2 | Hoess et al. 2025, Does the Tool Matter? | **全文**（arXiv:2501.15114，12 页） |
| 3 | Berndt et al. 2026, Can We Classify Flaky Tests...? | **全文**（arXiv:2602.05465，10 页） |
| 4 | Kummita et al. 2026, Static Analysis Traces... | 摘要级 |

## 2. 逐篇笔记

### 2.1 Hoess 2025（全文）
- 标题: 问句 + "Exploring Some Causes of Threats to Validity in Mining Software Repositories"（边界/方法副题）。
- 摘要结构: 背景 3 句 → "This raises the questions if (and to what extent) tools agree..." → "In this study, we use two tools to extract and analyse ten large software projects..." → **具体数字**（"differ by up to 500%"）→ "We find that such substantial differences are often caused by minor technical details." → 代价诚实（"may require considerable efforts"）→ lessons-learned 框架 → 收尾**弱化假设**（"Our findings lead us to hypothesise that similar uncertainties exist in other analysis tools, which may limit the validity of conclusions drawn in tool-centric research."）。
- 语气: 第一人称复数、平实、自我设限（"from a technical point of view"）。

### 2.2 Berndt 2026（全文）
- Index Terms 明确含 "**negative results**"。
- 摘要: 定义 → 问题 → 前期缺口 → "In this study, we evaluated..." → "Our findings indicate that LLMs **struggle** to..." → "**only marginally better than random guessing**" → 人工分析洞见 → "motivate future work ... with additional context, for example, using retrieval-augmented generation or agentic AI."
- Intro: RQ 枚举（RQ1 含 1.1–1.3 子问）→ "Our results suggest that..." 前置总结 → 贡献列表**仅 2 条**（第 2 条= "Discussion of implications for future work"）→ 章节 roadmap → 补充材料链接。
- 语气: 结果直陈 + 弱化动词（struggle/indicate/suggest），无 hype。

### 2.3 Gerhold 2024（摘要级）
- 标题即"限制命题"（"The Limits of the Identifiable: Challenges in ..."）。
- 摘要要点（本仓核验转述）: 扩展到更大更真实文件后精度下降；import-statement 分析仅 ~30%；暴露方法边界。

### 2.4 Kummita 2026（摘要级）
- 复现研究体裁: 得到**与原文不同**的结论（约 1.4× 更快发现漏洞，但在一个 benchmark 上确认更少漏洞）——"复现≠重复，结论可不同"是 RENE 的合法产出形态。

## 3. 跨篇规律（可复用清单）

1. 标题二选一: 问句式（Can We...? / Does the Tool...?）或边界命题式（The Limits of...）；共同点是**不写承诺式标题**。
2. 摘要模板: 背景 2–3 句 → "In this study, we ..." → **具体数字** → 负结果原话 → 边界/启示 → 未来工作动机。
3. 负结果**直讲不糖衣**（struggle / only marginally better / differ by up to 500%）。
4. 贡献列表**短而谦逊**（Berndt 仅 2 条，"讨论启示"可单独成条）。
5. 第一人称复数 + 主动语态 + 低形容词密度；假设用 hypothesise；局限独立成节（threats to validity / lessons learned）。
6. "negative results" 作为关键词/术语合法且常见。
7. Artifact/补充材料常态可链接；篇幅 10–12 页量级（与 RENE 10+2 一致，arXiv 含附录略多）。
8. 结语收在"边界 + 未来工作动机"，不喊口号。

## 4. 对 Paper E 的对照检查（只检不改）

| 项 | Paper E 现状 | 对照结论 |
|---|---|---|
| 标题 | "Visibility Is Not Detection: Auditing Observation Boundaries..." | 边界命题式，与 Gerhold 同族 ✓ |
| 摘要 | 数字密度高；负结果前移（"Three of these findings are negative or boundary results"）；"We claim no ..." 显式收窄 | 与两篇样本同法，且更显式 ✓ |
| 贡献 | 3 条（第三条= failed-transfer autopsy） | 与 Berndt 短清单一致 ✓ |
| 语气 | 第一人称；无 hype 词（AI 味 pass 已清） | ✓ |
| 局限 | §6.1 + Appendix A | 对应 threats-to-validity 惯例 ✓ |
| 差异（非缺陷） | 技术名词密度更高；摘要略长于样本（~250 词 vs ~200–230） | RENE 官方页未见词数硬限；保持现状 |

→ **学习结论**: 现有稿与本会议 RENE 风格同族，无必须修改项；本件留作后续写作/ rebuttal 的风格参照。

## 5. 边界

- 2/4 篇为全文读取；#1/#4 仅摘要级（付费墙），未采用任何非公开渠道；未做统计式文体比较；未改稿。
- arXiv 版与 IEEE 出版版可能存在排版差异（页数、模板），不影响风格结论。