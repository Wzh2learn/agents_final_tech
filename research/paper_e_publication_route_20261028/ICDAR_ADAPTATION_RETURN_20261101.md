# ICDAR 顺序备投：文档分析定位工作稿

> 2026-11-02 更新：随 ICINT 正文同步材料说明及 AI 使用披露候选，现役 [LNCS 工作 PDF](icdar_adapted_20261101/main.pdf)为 9 页，SHA-256 `99755c1399bf64d6fc7facf239d11fd343975ffc0eab91a233aae11589781598`。新版已重新编译及逐页检查，作者披露及终审仍待确认。以下 2026-11-01 的 8 页和 hash 是修改前快照。

2026-11-01。此稿是 Paper E 的备投准备，只有 ICINT 正式拒稿或确认撤稿后才考虑向 ICDAR 投递；不是另一篇独立论文，也尚未投稿。

## 工作稿做了什么

[工作正文](paper_e_icdar_working.md)从现役 ICINT 正文派生，由[生成脚本](prepare_icdar_adaptation_20261101.py)固定锚点生成，不覆盖 [ICINT 审阅稿](icint_latex/main.pdf)。主要变化：

1. 在标题、引言和讨论中突出文档评测的观察表面、阶段判定和阈值尺度，并说明 FinRank/BEIR 为互补的排序案例，而不是独立的文档图像评测验证。
2. 更具体地比较 SCORE 的语义解析评价与 Soric 等人的表格提取评测；本稿仍不声称提出了更好的解析指标。
3. 按[冻结的逐注入结果](../../logs/graph/eval/checkpoint_discrimination_tables_v2.json)重算并补入六个家族的 visible/injected 数量；这些是一个 seed、95 张表中的 118 次注入，不是 118 个独立来源或真实 OCR 错误率。
4. 补出阶段对齐控制的直接目标叶及留一簇验证口径；保留单响应叶、单一语义裁判、事后统计及复现差距等关键边界。
5. 删除两段重复解释，FinRank 和 BEIR 核心数值与已更正的 TF-IDF MAP 归属保持一致。

## 构建与审阅状态

- [LNCS 审阅 PDF](icdar_adapted_20261101/main.pdf) 8 页，SHA-256 `481646ae79a9b2d95a205bfe3c66a4ff52c8b03da6d672ad63ab8e949b872ead`；[TeX 源](icdar_adapted_20261101/main.tex)由 `build_icdar_latex.py --source paper_e_icdar_working.md --output .../main.tex` 生成。
- 本机 Tectonic 0.15.0 加载了从 [Springer 官网](https://link.springer.com/series/558/information-for-authors-and-editors)下载、SHA-256 为 `04ec99046ad9867f6cd54ffd1ef8c47c767b327d1baec77536db0528cd492fa2` 的 `llncs.cls`，编译日志显示 v2.25。第三方模板不纳入仓库，复现时需重新获取并核验；模板 ZIP SHA-256 `42afb32ed4fadc9e209134ec65dab1bd2a7ead42f9a3f8abb184f250c4a197b9`。
- 构建 exit 0，无 overfull，出现一处 underfull vbox 与本机 Fontconfig 提示。8 页均已渲染并检查整体布局，表格页另作放大检查；这些不等于正式投稿系统校验。
- pypdf 文本检查确认六类计数和 TF-IDF 的 `0.2200 → 0.1162` 出现在 PDF；作者完整姓名和北邮英文全名的文本检查未命中，PDF 无 Author 元数据。双盲仍需检查自引、完整元数据及外部材料链接。
- 文档限定为结构化表格数据，没有新增图像 OCR 或新的泛化实验；与主会受众的贴合度仍应由首次读者及作者审查。若 ICINT 退稿，应按真实评审意见重新检查正文、模板、统计和学校时间线，不能直接把本工作稿视为最终投稿包。

[ICDAR 征稿](https://icdar2027.org/call-for-papers)当前上限为含参考文献 17 页、双盲并采用 LNCS；具体节点见[路线计划](PUBLICATION_PLAN_ZH.md)，投稿前再次核验。
