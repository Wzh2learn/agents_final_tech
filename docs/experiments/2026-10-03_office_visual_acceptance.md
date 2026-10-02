# Office 视觉验收：两份导师向 DOCX（2026-10-03）

> 批次归属：`0fdd79b`（STATE 快照刷新）之后的 Office 视觉验收；缺陷修复提交 `3df1134`，导师稿 DOCX 重建提交 `9b19167`。本件落档于 head `9b1916760`。
> 环境口径：渲染与哈希在 GB10 执行（唯一权威环境）；本机只查看导出 PNG、做 git 操作与文本编辑，未在本机运行验收。
> 结论：**PASS** —— 导师稿 8/8 页、故事稿 4/4 页逐页检查完成；3 处缺陷已修复并有回归测试；1 项非阻断观察（跨页表格未重复表头行）。

## 1. 对象与冻结值

| 对象 | 页数 | 字节数 | sha256（head `9b1916760`） |
|---|---|---|---|
| `paper/teacher_review_draft_v1.docx` | 8 | 97 762 | `7880429716bc0bb4727b3d09e70125de8f5145df948d78987c92782bee76f2ef` |
| `paper/research_story_v2.docx` | 4 | 43 731 | `311e0f625e785432f8dd3277faa466e60a4919b0a02034725bb48a0c5bea6a00` |

- 导师稿 DOCX 的最近两次变更：`2377447`（09-25 旧版）→ `9b19167`（本批重建）。
- 故事稿 DOCX 自 `a0f4d3d`（2026-09-24 01:04）以来未变更，本次 4 页渲染直接对应当前在库版本。
- 两份 DOCX 的 sha256 在 GB10 与本机工作树副本逐字一致。

## 2. 渲染复现与「被检查像素 = 在库文件」对照

GB10 命令（head `9b1916760`；输出目录为一次性 `mktemp -d`）：

```bash
soffice --headless --convert-to pdf --outdir "$R" paper/teacher_review_draft_v1.docx paper/research_story_v2.docx
pdftoppm -png -r 100 "$R/teacher_review_draft_v1.pdf" "$R/tr"
pdftoppm -png -r 100 "$R/research_story_v2.pdf" "$R/story"
```

- PDF 页数 8 / 4；PDF sha256：导师稿 `fc68a903cf2b1b37fc7e2d7d29f9e631f56fb22f96c554fd85df6ddeca0efc77`、故事稿 `d1532c5bcd3365dbcb13e6d7c2b4a6053d6affa526e75c885686ebcab59ef51c`。
- 重渲染 12 张 PNG 与逐页查看所用副本 **12/12 逐字节一致**（全值见下），即「被检查的像素 = 当前在库 DOCX 的确定性渲染」。

```
tr-1    7e0a3c1cff1d8d535c46fc8fe6a722ee9233f07778224ca72afee6314e9a0083
tr-2    3c91216310c310a42ecc1f42079bb879464d79402f625c19f4e0190073572d27
tr-3    f3283d0bebe2604c725e69be1f8e999b1e09743ac7229ebda4e2f65bca5c7099
tr-4    6dd71dadbcee604eae9d94444db3cc7036d24a0beda8091e0dcc96bc9e4bd0ba
tr-5    a03ebc7f879bf64afcefef8ce9278a6558d851cb11e22b924250a9bf5d04ec4d
tr-6    3a5ad6188bab319323eff71767ce1d7a6eb1c1a73c27247ae724a3f117399d71
tr-7    f4fe08caab620a6b1db43ed7005f3593252c06347dd09ab3ea496646ba70319d
tr-8    4c39174d7bf4bfb32e6c52dd22a422bc49571973a1c6d7569b9f83bfbed39927
story-1 9c8d627258dddcd0002411edf0582e3075e56de8def21a14fa3244c4f2bf3073
story-2 7f66628bab6c7983cdecaba5e987e05e5d1a89f51d477f0c4070f236966c0ace
story-3 2ca13626c4385f4ac733721c68b90c9fed8bc7430b5175fb5b2d3268a2984255
story-4 7e1502bd7c3815c01042b9cac31dd919b488955bb8311150307c64a81acdf329
```

## 3. 修复前实测的 3 处缺陷与修复（`3df1134`，均为导师稿）

| # | 位置 | 修复前（旧渲染 p4/p5/p6 实测） | 修复 | 落点（--numstat） |
|---|---|---|---|---|
| O1 | p4 §4.1 | 公式显示为 `|Gamma={0.2,0.3,0.5,0.7,0.9};`（竖线 + 原始命令名，不是公式） | 新增闭集 `render_math()`：brace-matched `\frac`、`\sum/\prod/\int` 下标、转义与希腊字母翻译；未知命令保持可见、不静默丢弃 | `research/build_teacher_review_docx.py` +90/−1 |
| O2 | p5→p6 Table 1 | Flat 行的置信区间尾段 `0.8737])` 单独落在续页首行，同行前两格为空（行被跨页劈开） | 新增 `prevent_row_split()`（`w:cantSplit`），接入全部 4 个表格构建器 | 同上 |
| O3 | p5 Figure 2 | `absorbed=` 计数为柱内白色小字：有色柱上勉强可见，ocr-similar（比率 0、无柱体）上白底白字完全不可见——「13/13 absorbed」事实被吞；图题仍为历史脚本版本且含工件文件名 `checkpoint_discrimination_tables_v2.json` | `absorbed` 折入柱顶标签；`ylim` 1.16 → 1.30；PNG 重生成后图题与当前脚本对齐 | `research/paper_figures_draft.py` +5/−4；PNG 重生成 |
| — | 回归测试 | 三处修复以 docx 级断言覆盖 | 新增 `tests/test_teacher_review_docx_rendering.py`（4 项） | +43 |

图件新旧哈希（同一路径 `docs/experiments/figures_paper/fig_visibility_spectrum.png`，git blob 可复核）：

- 旧（`0fdd79b`，blob `6550cf1d`）：`c0b1ec3d8f521d54f9e5bb4ec74365c816af8eaa3542b1f4b37d568551d3c36e`，55 226 B。
- 新（`9b1916760`，blob `cd686b11`）：`d9da2f7b2e290d557f14ef14bc163850f5c6a55117432137848e8b49a0e27226`，55 352 B。

## 4. 修复后逐页复验

**导师稿（8/8 页）**

- p1–p2：标题、摘要与 §3 前两节排版正常，无残留标记。
- p3–p4：公式以 Unicode 呈现——p3 实测 `S(n)=Σ_{c∈ C(n)} (w(c))/(Σ_{j∈ C(n)}w(j))S(c).`，p4 实测 `Γ={0.2,0.3,0.5,0.7,0.9};`；无 `\frac`/`\sum`/`|Gamma` 残留。
- p5：Figure 2 六柱顶部标签全部可见（`0.00 n=13 absorbed=13`、`0.81 n=16 absorbed=3`、`0.88 n=17 absorbed=2`、`0.91 n=47 absorbed=4`、`1.00 n=20`、`1.00 n=5`）；Table 1 的 End-to-end 与 Flat 两行完整。
- p6：续页首行为完整的 `Hierarchical, expert weights` 行，无断行、无空首格；5.3–5.5 正文完整。
- p7–p8：正文与参考文献无溢出、无遮蔽。

**故事稿（4/4 页）**

- §7、§8 完整；p3→p4「论文图表计划」表按行分页，Figure 1–4 与 Table 1 行各自完整。

非阻断观察：两处跨页表格均未启用 `tblHeader`（续页不重复表头行）。不影响可读性与本次验收；如需处理，走后续独立小批。

## 5. 偏离声明（图 PNG 的本机重生成）

- `fig_visibility_spectrum.png` 在本机以 matplotlib 3.9.4 重生成（GB10 repo `venv` 与系统 python3 均无 matplotlib，批内实测 ImportError）；输入为已跟踪冻结 JSON `logs/graph/eval/checkpoint_discrimination_tables_v2.json`。
- 该 PNG 为论文展示件，不在 `scripts/graph/frozen_hashes.txt`（18 项）内；差异限于样式（图题、柱顶标签、ylim），数据不变（95 表 / 118 注入、每柱 rate 与 n 不变）。
- 本批未改任何实验数字、判据、冻结 hash、数据体；DOCX 重建仅消费修复后的构建器与图件。

## 6. 结论与后续

- 两份导师向 DOCX 在 head `9b1916760` 下 **视觉验收 PASS**；定向回归 `tests/test_teacher_review_docx_rendering.py` + `tests/test_paper_claim_acceptance.py` 合计 13 passed（GB10 实测）。
- 全量 GB10 复跑（pytest / docs_lint / validate_paper_claims）由本批台账行记录，本件不充当全量验收证据。
- 下一自然 Loop B 周期将覆盖本批 head；不手工触发。
