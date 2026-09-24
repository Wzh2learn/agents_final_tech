# 两份 DOCX 的 Office 视觉验收（GB10 LibreOffice，2026-09-24）

> 状态: 证据件（2026-09-24, Loop D）| 环境: GB10 `soffice` + poppler + CJK 字体（80 项 CJK 字体实测在位）
> 关闭的缺口: `paper/teacher_review_readiness_v2.md`（2026-09-22）中「本机没有 LibreOffice/soffice，Office 视觉核对未完成」一行。
> 密级: 仅限内部审阅。本件不改变任何稿件内容、不重生成 DOCX、不新增任何数字。

## 1 为什么在 GB10 做

readiness v2 把「两份 DOCX 的 Office 排版/分页视觉验收」列为送审前最后一项机械缺口，而本机无
LibreOffice。GB10 实测 `soffice`、`libreoffice`、`pdftotext`、`pdfinfo`、`pdftoppm` 均在位，且
`fc-list` 含 80 项 CJK 相关字体，故视觉验收在 GB10 完成。GB10 是唯一权威验收环境。

## 2 方法（隔离、只读、零模型）

- 隔离 worktree `agents_final_tech_accept_1627a54`（提交字节，`git status` 空），**不碰 production**。
- 转换命令（每个文件独立 profile，输出全部落 `/tmp/docx_vis_20260924`，仓外）:
  `soffice --headless -env:UserInstallation=file:///tmp/docx_vis_20260924/profile_<name> --convert-to pdf --outdir /tmp/docx_vis_20260924 <docx>`，两次均 rc=0。
- 机械检查: `pdfinfo`（页数/页面尺寸/加密）、`pdftotext -layout`（文本层）、`pdfimages -list`（位图数）、
  Python 计 U+FFFD 与换页符；再用 `pdftoppm -png -r 80` 渲染逐页 PNG 并由 Loop D 目视。
- 输入字节: `paper/teacher_review_draft_v1.docx` sha256 前 16 位 `f33be93d8159cbfb`；
  `paper/research_story_v2.docx` 前 16 位 `311e0f625e785432`。
- 模型调用 0；除本地转换外无任何端点访问；未写任何仓内文件。

## 3 机械结果

| 项 | teacher_review_draft_v1 | research_story_v2 |
|---|---|---|
| 页数 | 7 | 4 |
| 页面尺寸 | 612 x 792 pts (letter) | 612 x 792 pts (letter) |
| 加密 | no | no |
| 文本层字符数 | 23 752 | 8 168 |
| 换页符数 | 7 | 4 |
| 位图数（pdfimages） | 2（两张必需图件） | 0（总架构图以矢量 SVG 置于原生表格，故无位图；已目视确认在位） |
| U+FFFD | 0 | 0 |
| 必需章节在文本层 | 9/9 各恰好 1 次 | 三阶段标题、RQ 边界表、定位节均在位 |

必需章节定位（teacher_review_draft_v1 文本层行号）: Abstract :11、1. Introduction :32、
2. Related Work :69、3. Method、4. Experimental Setup、5. Results :179、
6. Discussion and Limitations :261、7. Conclusion :283、References :295。

## 4 目视结果

- 第 1 页: 标题三行、作者占位横线、内部审阅与专利门提示段（斜体）排版正常，无溢出、无缺字。
- 第 5 页: Figure 2（按注入家族的可见性谱柱状图）图例、轴标、逐柱数值标注齐全；协议对照表
  （Protocol / Detection signal / Tables detected / Injections detected）四列带框线、无列溢出。
- 第 7 页: References 列表完整，逐条带 arXiv ID，悬挂缩进正常。
- research_story_v2 第 2 页: 中文正文、RQ 四行边界表、章节标题均正常渲染，**无 tofu、无溢出**。

## 5 一项图件内部观察（记录，不在本件修）

Figure 2 中逐柱底部的 `absorbed=N` 标注与柱体填充在 80 dpi 下部分重叠，可读但偏紧。这是
**已提交位图图件内部**的排版细节，不是 DOCX 布局缺陷；修它会改动冻结证据链上的图件，须单独成批
并自带验收，故本件只记录不动手。

## 6 判定与不主张

- 判定: 两份 DOCX 在 commit `1627a54` 上的 Office 视觉验收（机械 + 目视）**通过**；readiness v2 的
  「视觉未验」一行对这两份文件**关闭**。
- 不主张: 不代表 Word 原生渲染与 LibreOffice 完全一致；不代表印刷色彩配置已验；作者、单位、目标会议
  模板**仍按专利门要求留空**，venue 未经官方源核实不写入。
## 加记（2026-09-24，修订提交 4de4741 后的第二次转换）

- 输入 DOCX 因七处审稿修订而变更：新 sha256 = `87ea0770cb5b8fb15519caf4b925bcea1c2d6dac74fd0b7c5bc8aaa2c095d0f3`；
  本件 §2/§3 记录的 `f33be93d8159cbfb` 对应 commit `1627a54` 上的 DOCX，两者不冲突、各归其提交。
- 重转换（同法：隔离 worktree `accept_4de4741`、独立 UserInstallation、输出落 /tmp 仓外）：
  **8 页** letter（原 7 页，增页来自修订段落）；U+FFFD 0；Abstract / 1. Introduction / 7. Conclusion /
  References 均在文本层；修订句（判据差异注记、家族核算、恢复判据等）在 PDF 文本层在位（跨行折行属排版）。
- GB10 在 `4de4741` 的权威验收：`tests/test_paper_claim_acceptance.py` + `tests/test_research_story_assets.py`
  共 **17 passed**；`docs_lint` rc=0 / 0 fail / 1 warn（docs/34 时效 warn 未消警）。
- §6 判定对新 DOCX 继续成立；§5 的 Figure 2 柱底标注观察不变（仍留单独批）。
