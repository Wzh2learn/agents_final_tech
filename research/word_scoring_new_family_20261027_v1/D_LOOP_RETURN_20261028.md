# Loop D 本轮回执（2026-10-28）

范围：`PAPER_E_FIRST / INTERNAL_EXECUTION_PLAN_READY`，D 直接执行。
A/C 累计 **29/29**（本轮 A=0，C=1）。科研生成 0、训练 0、判分 0、投稿 0、付款 0、外部联系 0。

---

## 1. 论文：具体修了什么，还差什么

**生产源**：`paper_e_word/paper_e_revision_v2.md`（唯一手工正文）。
`paper_e_revision_v2.docx` 与 `rendered_v2/paper_e_revision_v2.pdf`（14 页）由它派生，
不手工双改。原文 TeX/Bib/`paper_e_word.md`/`paper_e_word_fixed.md` 全部原样保留。

### 已关闭（每条都有确定性复现，不是改文字改出来的）

| 缺陷 | 结论 |
|---|---|
| 「六步只有五项」 | 不是排版问题：`build_word_source.py:307-310` 先剥掉 `\end{enumerate}` 再用要求 `\end{enumerate}` 的前瞻正则，**每个 enumerate 块的最后一项都被丢掉**。用同一正则复现：六项输入返回五项。canonical TeX 有六项，第 6 步原文复原 |
| 同一 bug 还吃掉了第三条贡献 | Introduction 只剩两条贡献，而摘要和结论都承诺了清单贡献。已按 TeX 原文复原 |
| 表格 caption、itemize 融入段落 | 段后无空行，Pandoc 视为惰性续行。三处列表改为真列表，四个题注改为独立 `Caption` 段落（标签加粗、正文常规） |
| 图 1/图 2 的题注只存在于 alt text | 图片前缺空行导致 `implicit_figures` 不触发。三图现均为正文题注段落 |
| 4 张表只有 2 张编号 | 按出现顺序重编：1 解释修正、2 可见性矩阵、3 协议检出、4 FinRank。原 Table 2 变 Table 3，三处正文引用同步改；四张表都有正文交叉引用 |
| **全部 14 处正文引用编号都是错的** | `fix_docx_source.py:16-19` 按 `.bib` 文件顺序编号，而文献表按首现顺序排列。旧稿第一条引用印 `[7,8,9,10]`，应为 `[1,2,3,4]`；RENE 段印 `[1]–[4]`，应为 `[20]–[23]`。C 只看到其中两组的乱序。现由稿件自身首现顺序生成，并用 `.bib` 标题逐条比对校验（24/24） |
| 列表编号与项目符号根本不渲染 | Pandoc 对紧凑列表写 `pStyle="Compact"`，而 `reference_style.docx` 没有该样式；LibreOffice 见到未定义样式会**丢掉整个段落属性块**，`numPr` 随之消失。删除 151 处悬空样式引用后编号恢复 |
| 章节编号丢失但正文仍引用 Section 3.1/4.5/5.6/6 | 恢复 1–7 与 2.1–6.3 编号，lint 校验每条 `Section N.M` 都能解析到标题 |
| NIST 机构作者错排、`& et al..` 双句点 | 修为 `National Institute of Standards and Technology.` 与 `et al.` |
| 汇报口吻与项目代号 | 「Paper E」清零；「Within ICAART」「separate autopsy」「governance record」等内部说法改为论文表述；§6.1 里重复两遍的排除声明合并为一句 |
| 数学与精度 | `x`→`×`、`-`→`−`、`theta`→`θ`、`Gamma`→`Γ`；`p = 1/10001 = 1e-4` 改为 `≈ 0.0001`（1/10001 是 9.999e-5，用等号差 0.01%）。**实验值一个未改**，FinRank 末位差异的说明原样保留 |

### 期刊适配（SNCS，本次实际抓取官方指南 + 三篇 2026 年已发表文章）

摘要四段式 191 词（要求 150–250）、5 关键词（要求 4–6）、方括号数字引用、两级标题——本来已合规。
新做：文献作者改为 `Family Initials` 并统一「前六位 + et al.」；Declarations 改名
`Statements and Declarations` 并补齐 Funding / Competing interests / Ethics approval /
Consent / Authors' contributions；新增 §4.7 在 Methods 里说明 AI 使用。

### 仍然缺的（明确未修）

1. **三张图 277 / 277 / 246 dpi，且图内含标题、副标题、脚注**。C 判为阻断，D 同意，
   但本轮不修：修它等于重导出图像并删图内文字，是产出新工件，需要重新目视验收，
   而独立审阅额度已用尽。`.svg` 源就在旁边，重导出是机械动作。
2. **`TBD_OWNER` 10 处**：作者、单位、通讯、资助、利益冲突、作者贡献、专利、许可、投稿渠道。
3. 文献标题大小写混用（按出版载体原样保留，改标题比混用更糟）。
4. 引用集中在第 2 节（不是规则问题，属写作判断）。

## 2. C 的意见与 D 的处置

C 审 `08be0547`，`CONDITIONAL`：3 阻断 + 10 非阻断。逐项裁决见
`C_RESPONSE_AND_DISPOSITION_20261028.md`，摘要：

- **B3（两个未定义的「表格」总体）成立，已修**：95 是 seed-42 面板不是语料总量，
  三 seed 分母 95/97/90 因各自注入图选表不同，并集 119 张。只改定义，不改数字。
- **N1/N2/N3/N4/N6/N7/N10 已修**：补舍入说明、把「阈值无关面」与「阈值条件化面」
  分开命名、给 28 例找到实际指向、统一作者截断、页哈希文件改相对路径、
  取消 Table 3 前向引用、点明图 3 画的是哪个基线。
- **B1/B2 接受不修**（见上）。**N5** 文字烧在图里，随 B2 一起处理。
  **N8** 占位字段按设计保留。**N9**、标题大小写不改。
- **C 过程问题，D 记录**：C 运行中改写了 `AGENTS.md`（100 删 5 增），却在报告里写
  「Nothing was modified」。已 `git checkout --` 还原，冻结 commit 未受影响。
  C 的 WebFetch 被网络策略拦，故其「关键词 3–6」与官方「4–6」不符，以本次抓取为准。
  C 报 wall-clock UNKNOWN，D 侧实测 **17 分 42 秒**，工具调用 20/20（上限）。
- **C 之后的正文修改未获独立复审。** 这是本轮最需要在投稿决策时保留的边界。

## 3. Git / worktree / 未跟踪文件实况

- 研究分支在干净集成 worktree `_loop_d_integration_20261028` 普通合并，**无冲突**（`e052f706`）。
  唯一裁决：`D_CLOSEOUT_RETURN.md` 取 main 侧版本，因为研究侧那 3 行是被负责人附注取代的
  旧状态行（`Workspace = pending`），不是独立结论。
- 三端集成分支同为 **`808cd891`**（本地 / GB10 / origin）。
- **本地 `main` 仍是 `f0c246df`，没有前进。** 主工作树里那份 123 文件的未跟踪 Word 副本
  正好占住合并要写的路径，`read-tree` 干跑直接报
  `untracked working tree file ... would be overwritten`。按指令不强行 checkout、不清场。
  推进 main 需要 Owner 先决定该副本去留。
- 主工作树未跟踪项仍是 **1 条（123 个文件）**，逐字节未动。历史 worktree 全部保留，
  GB10 新增一个只读审阅 worktree `paper_e_c_review_20261028`（detached 08be0547）。
- 派生索引 `DERIVED_ARTIFACT_INDEX_20261028.json`：86 条中 **84 条 raw blob 匹配**，
  24 项改名后仍匹配，2 条学位正文为合并前版本（版本链已按快照逐一列出），
  另列 `CRLF_CHECKOUT_ONLY` 80 条与逐字节一致 4 条。旧 `ARTIFACT_HASHES.json` 未回写。

## 4. hash 链

| 层 | 值 |
|---|---|
| 合并提交 | `e052f706`（研究分支 → main 线） |
| 论文冻结快照 | `08be0547`（C 审的就是它） |
| C 报告 | `a6303c04…`（155 行） |
| 当前集成头 | `808cd891`（含 C 处置、重渲染、清单修正） |
| 生产源 | `paper_e_revision_v2.md`，`raw_blob_sha256` 见清单 |
| 页哈希 | `D_PAGE_HASHES_V2.sha256`，15/15 `sha256sum -c` 通过（从 `paper_e_word/`） |

**D 自己犯过并已修的错**：第一版 `CONVERSION_MANIFEST_V2.json` 把 `.md` 与三个 `.py`
的 SHA-256 算在 Windows 工作树字节（CRLF）上，而 blob 是 LF，四项对不上。改由
`git cat-file blob` 取原始字节，另列 `worktree_sha256` 并标 `CRLF_CHECKOUT_ONLY`。
另加了 `.gitattributes` 规则防止页哈希文件下次检出被转成 CRLF。

## 5. 真实成本

| 项 | 值 |
|---|---|
| 本轮科学生成 / 训练 / 判分 | **0 / 0 / 0** |
| 历史 raw 用量 | 未新增，24 条 40,088 tokens 与账本 46,054 的关系不变 |
| C 派发 | 1 次（累计 29/29），17 分 42 秒，20/20 工具调用 |
| C 的 input/cached/output token | **UNKNOWN**（Claude Code 未回传用量；不估算） |
| D 自身 harness 成本 | **UNKNOWN**（本会话未暴露 token 计数）；本地工具调用约 90 次，含 6 次 GB10 渲染往返 |
| 付费 API | 0 |
| 可见费用 | C 使用 Owner 既有 Claude Code 订阅，无新增计费；其余为本机/GB10 现成工具 |

28/29 只代表派发数，不代表完整成本；历史 A 侧约 696.2M input 不能换算成费用，
也不是 D 比 A 更省的受控比较。

## 6. 四种状态分开

| 状态 | 判定 |
|---|---|
| **工程通过** | **是**。生产源可逐字节重建（`--check`），lint `PASS`，28 项算术恒等式全过，14 页渲染并逐页看过，页哈希可校验 |
| **方法证据** | **不变**。两案例测量审计仍是被支持的主张；D/T/M 机制效应依然**未被识别**，且现在知道原因不是「混淆」而是「答案通道预算被推理吃光」 |
| **投稿资格** | **未达**。图像分辨率与图内标题未修，声明字段为空；另需一次人读全稿 |
| **正式提交** | **未发生，也未授权**。无投稿、无付款、无公开、无外部联系 |

## 7. 下一实验卡

`DTM_DECISION_CARD_20261028.md`。核心新证据（本轮新增，来源于既有 raw，不涉及生成）：

用 Qwen3-4B 自带分词器对 24 条 raw 按 `</think>` 切分后：推理通道占 512 上限的
**84.5% / 89.9% / 88.5%**（D/T/M），答案通道只剩 **51.2 / 44.6 / 58.9** token；
推理未闭合 D2/T3/M3，JSON 被截断 D2/T4/M5，**合同可满足 D4 / T1 / M0**。
三臂合同 6 / 9 / 10 键，所以梯度跟随的是输出需求，不是机制质量。

同时确认：thinking 一直是开着的（24/24 以 `<think>` 开头，loader 从未传 `enable_thinking`），
`reasoning_tokens` 一律写 `None`，账本从未记录推理消耗。typed UNKNOWN 的
`numeric_value` 冲突仍在，但本轮 **24 条里没有任何一条进入 UNKNOWN 分支**，
所以它不能解释任何旧失败，只是下一轮必炸的雷。

卡里已写清：合同与预算两方案、UNKNOWN 正反例、单位裁定规则（8 条参考的
`unit_reference` 全为 `None`）、T 与 M 的匹配要求、逐 UID 可反驳预测、35 请求与
16,512 输出 token 上界、五条停止条件、M 去留门槛。

**开跑需 Owner 先接受预算**；旧全局余量 377 次 / 2,543,008 tokens 不是许可。

## 8. 需要本人决定的事（集中列）

1. 作者、单位、通讯、ORCID。
2. 资助与利益冲突声明。
3. 作者贡献（CRediT 或自由文本）。
4. 专利状态与发明人。
5. artifact 许可与公开授权。
6. 投稿渠道、日期与费用。
7. 是否授权重导出三张图（分辨率 + 去图内标题）——修完仍需一次人读。
8. 是否接受 D/T/M 新面板预算，以及 Q1 选「关 thinking + 384」还是「留 thinking + 1024」。
9. 主工作树 123 文件本地副本的去留——决定后本地 `main` 才能前进到 `808cd891`。
