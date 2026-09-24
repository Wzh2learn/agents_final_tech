# Independent Loop C re-audit of the schema role ruling and draft after byte-faithful fix (model qwen3.8-max)

> Dispatched 2026-09-24 against commit b5646de; evidence packet inline; no tools; 1 turn(s), cost $0.1068.
> Verdict: PASS_WITH_NOTES - 17-line excerpt byte-faithful including inner fences and trailing spaces; excerpt_fidelity caliber consistent; charter checks 2-6 hold.
> Body verbatim.

## 复审结论：PASS_WITH_NOTES

（复核范围：commit b5646de 修正后的协议件 §6 与 schema 草案 JSON；全部依据内联证据，未使用工具，未获取任何仓库/数据内容。）

### 核验项 1：§6 引文逐字节保真 —— 通过

将 §6 四反引号外层围栏内的引文与内联 README 真值（31-47 行）逐行逐字符比对，17 行全部一致：

| README 行 | 比对结果 |
|---|---|
| 31 | `The dataset is stored as json files in folder "dataset", each entry has the following format:` 逐字符一致 |
| 32 | 空行，两侧一致 |
| 33 | 内层围栏 ` ``` `（开），已含在引文内 ✓ |
| 34-36 | `"pre_text"` / `"post_text"` / `"table"` 三行一致 |
| 37 | `"id": ... for this report. ` —— **行尾空格在两份文本中均在**（`report.` 后一个空格再换行）✓ |
| 38 | 空行一致 |
| 39-45 | `"qa": {` 块七行（question/program/gold_inds/exe_ans/program_re/`}`）逐字符一致，两空格缩进一致 |
| 46 | 内层围栏 ` ``` `（闭），已含在引文内 ✓ |
| 47 | `In the private test data, ... no reference provided. ` —— **行尾空格在两份文本中均在** ✓ |

外层围栏为 ````` ````markdown `````（4 反引号），内层两条 3 反引号围栏行被正确包裹、不破坏外层围栏；引文后注明的区间「31-47 行逐字保真摘录」与实际相符。**b5646de 所修复的缺陷（内层围栏、行尾空格）已确认消除。**

### 核验项 2：excerpt_fidelity 字段与 JSON 有效性 —— 通过

1. `excerpt_fidelity` 明确陈述保真口径：「byte-faithful lines 31-47 including markdown fence lines and trailing whitespace; outer 4-backtick fence in protocol doc」——与 §6 实际呈现方式（4 反引号外层围栏、含围栏行、含行尾空格）逐项吻合。
2. JSON 语法有效：全部键加引号、数组/字符串闭合正确、无尾逗号、单一根对象。（`excerpt_fidelity` 与 `verbatim_excerpt_location` 排在同一行，属排版美观问题，不影响有效性——见备注。）
3. 溯源字段未变且与 §6 一致：`czyssrs/FinQA @ 0f16e2867befa6840783e58be38c9efb9229d742`、`README.md`、`6518 B`、sha256 `eb86779c…64605`、`excerpt_lines [31,47]`——五要素双处互相印证。
4. `verbatim_excerpt_location` 指向协议件 §6「quoted verbatim」，与核验项 1 的比对结果一致。

### 核验项 3：原章程检查 2-6 持续成立 —— 通过

1. **字段清单（检查 2）**：`fields` 九项（pre_text、post_text、table、id、qa.question、qa.program、qa.gold_inds、qa.exe_ans、qa.program_re）与引文 34-45 行完全对应，无增删。
2. **溯源（检查 3）**：见核验项 2 第 3 条，双处一致。
3. **BLOCKED 判定一致性（检查 4）**：§6 首段与 JSON `current_corpus_ruling` 同述——当前 drift-v0（TAT-QA 衍生）语料包 schema 角色 = BLOCKED；同引 NExTplusplus/TAT-QA `@870accc4…`、README.md 4689 B、sha256 `85c39817…4d5f`、README 第 48 行仅记 facts/mapping、详表在 ACL2021 论文与项目网站（核验引文池之外）、`m1_table_schema` 候选维持拒绝。两处哈希/字节数/行号完全一致，无漂移。
4. **范围诚实（检查 5）**：JSON `scope` 标明 P1_FUTURE_PACKAGE 且「NOT the current drift-v0 corpus package」；`draft_status` = DRAFT_COMPLETE_PENDING_PACKAGE_BINDING，与 §6「草案完备、待打包绑定；不在本阶段绑定」一致；`private_test_note` 声明 private test 仅 question 字段（README 第 47 行）且排除于任何 schema 绑定——与引文第 47 行原文相符。
5. **不取数据本体（检查 6）**：§6 明记「仅引 README/LICENSE 官方文档，不引 dataset/*.json 数据本体」；JSON 全部溯源仅指向 README.md，无任何 dataset 文件引用。本次复审亦未进行任何仓库或数据获取。

### 备注（不阻断）

1. JSON 中 `excerpt_fidelity` 与 `verbatim_excerpt_location` 位于同一物理行，语法有效但排版不一致，建议下次提交时分行。
2. 内联协议件正文的中文部分以 mojibake（M-序列）呈现，属传输/显示层伪影；可解码片段（如「仅引 README/LICENSE…不引 dataset/*.json 数据本体」）语义与判定一致，不构成内容缺陷。
3. 行尾空格与逐字节同一性的核验以上游提供的内联真值为基准（本次无工具、无法重新哈希）；两份文本在该基准下字符级一致。

**最终裁定：PASS_WITH_NOTES** —— b5646de 的字节级保真修复确认到位，§6 引文与 README 31-47 行逐字符一致（含两条内层围栏与 37/47 行尾空格），JSON 有效且溯源、BLOCKED 判定、范围诚实、不取本体各项均未回退。
