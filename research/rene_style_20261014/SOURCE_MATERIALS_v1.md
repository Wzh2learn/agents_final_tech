# RENE 风格素材 v1（2026-10-14）

> 目的: 为 `docs/research/RENE_ACCEPTED_PAPER_STYLE_STUDY_v1.md` 提供**来源可核验**的素材。边界: 仅公开渠道（arXiv API / Crossref / 直连下载）；未绕过付费墙；本 session 中 web_search 工具返回空、S2/DBLP/OpenAlex 多处 429 或空结果，改用 arXiv API + Crossref；未采用不可核验的二手转述。

## 1. 可得性矩阵

| # | 论文 | 全文可得性 | 素材文件/来源 |
|---|---|---|---|
| 1 | Gerhold, Solovyeva, Zaytsev. The Limits of the Identifiable (SANER RENE 2024; DOI 10.1109/SANER60148.2024.00022) | **不可得**（IEEE 付费；arXiv 未检索到） | 摘要级：本仓 `paper/saner_rene_manuscript_v1.md` §2.3（此前核验阶段由官方摘要改写）+ `research/positive_repair_20261011/related_work_verification_v1.md`（DOI/作者/venue 4 源核验） |
| 2 | Hoess, Paradis, Kazman, Mauerer. Does the Tool Matter? (SANER RENE 2025; DOI 10.1109/SANER64311.2025.00067) | **arXiv 全文** arXiv:2501.15114（12 页） | `research/rene_style_20261014/hoess2025_tool_matter.pdf`；摘录 `..._excerpts.txt`（下载于 2026-10-14） |
| 3 | Berndt, Bekmyradov, Gemulla, Kessel, Bach, Baltes. Can We Classify Flaky Tests Using Only Test Code? (SANER RENE 2026; DOI 10.1109/SANER67736.2026.00016) | **arXiv 全文** arXiv:2602.05465（10 页） | `research/rene_style_20261014/berndt2026_flaky_tests.pdf`；摘录 `..._excerpts.txt`（下载于 2026-10-14） |
| 4 | Kummita, Schiebel, Bodden, Miao, Wei. Static Analysis Traces can Help Dynamic Symbolic Execution (SANER RENE 2026; DOI 10.1109/SANER67736.2026.00114) | **不可得**（IEEE 付费；arXiv 未检索到） | 摘要级：同 #1 两个来源 |

工具记录: arXiv API `https://export.arxiv.org/api/query`（命中 #2/#3）；Crossref `api.crossref.org`（#1/#4 title 核验，无 abstract 字段）；IEEE/Unpaywall/S2 不可用或 429。

## 2. 两篇 arXiv 摘要（逐字，来自下载的 PDF 第一页）

### #2 Hoess 2025
> Software repositories are an essential source of information for software engineering research on topics such as project evolution and developer collaboration. Appropriate mining tools and analysis pipelines are therefore an indispensable precondition for many research activities. Ideally, valid results should not depend on technical details of data collection and processing. It is, however, widely acknowledged that mining pipelines are complex, with a multitude of implementation decisions made by tool authors based on their interests and assumptions. This raises the questions if (and to what extent) tools agree on their results and are interchangeable. In this study, we use two tools to extract and analyse ten large software projects, quantitatively and qualitatively comparing results and derived data to better understand this concern. We analyse discrepancies from a technical point of view, and adjust code and parametrisation to minimise replication differences. Our results indicate that despite similar trends, even simple metrics such as the numbers of commits and developers may differ by up to 500%. We find that such substantial differences are often caused by minor technical details. We show how tool-level and data post-processing changes can overcome these issues, but find they may require considerable efforts. We summarise identified causes in our lessons learned to help researchers and practitioners avoid common pitfalls, and reflect on implementation decisions and their influence in ensuring obtained data meets explicit and implicit expectations. Our findings lead us to hypothesise that similar uncertainties exist in other analysis tools, which may limit the validity of conclusions drawn in tool-centric research.

### #3 Berndt 2026
> Flaky tests yield inconsistent results when they are repeatedly executed on the same code revision. They interfere with automated quality assurance of code changes and hinder efficient software testing. Previous work evaluated approaches to train machine learning models to classify flaky tests based on identifiers in the test code. However, the resulting classifiers have been shown to lack generalizability, hindering their applicability in practical environments. Recently, pre-trained Large Language Models (LLMs) have shown the capability to generalize across various tasks. Thus, they represent a promising approach to address the generalizability problem of previous approaches. In this study, we evaluated three LLMs (two general-purpose models, one code-specific model) using three prompting techniques on two benchmark datasets from prior studies on flaky test classification. Furthermore, we manually investigated 50 samples from the given datasets to determine whether classifying flaky tests based only on test code is feasible for humans. Our findings indicate that LLMs struggle to classify flaky tests given only the test code. The results of our best prompt-model combination were only marginally better than random guessing. In our manual analysis, we found that the test code does not necessarily contain sufficient information for a flakiness classification. Our findings motivate future work to evaluate LLMs for flakiness classification with additional context, for example, using retrieval-augmented generation or agentic AI.

（Index Terms 含: "software testing, flaky tests, large language models, classification, **negative results**"。）

## 3. 来源 URL
- arXiv:2501.15114 — https://arxiv.org/abs/2501.15114（PDF https://arxiv.org/pdf/2501.15114，下载 2026-10-14）
- arXiv:2602.05465 — https://arxiv.org/abs/2602.05465（PDF https://arxiv.org/pdf/2602.05465，下载 2026-10-14）
- Crossref: https://api.crossref.org/works/10.1109/SANER60148.2024.00022 与 .../SANER67736.2026.00114（2026-10-14 访问；无 abstract）
- RENE ledger（4 源核验记录）: research/positive_repair_20261011/related_work_verification_v1.md
## 4. 版权与入库口径
- 两篇 arXiv **PDF 本体不入 Git**（第三方版权；URL 已记录、可随时复取）；**文本摘录**（`*_excerpts.txt`）作为研究引用素材入 Git；本目录 `.gitignore` 已声明 `*.pdf`。