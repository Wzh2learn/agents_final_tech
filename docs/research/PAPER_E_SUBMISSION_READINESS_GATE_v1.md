# Paper E 最终投稿门禁 v1

> 2026-10-12｜`SUBMISSION_BLOCKED_SCIENCE / REVISIONS_NOT_APPLIED`
> 本文判定当前投稿资格，不修改稿件，不新增实验或自动投稿。科学依据为 [作者级裁决](SANER_SCIENTIFIC_ADJUDICATION_v1.md)；现稿为 [canonical manuscript](../../paper/saner_rene_manuscript_v1.md)，当前机器记录为 [claim matrix](../../paper/saner_rene_claim_matrix_v1.json)。后二者尚未落实裁决，不能以旧 PASS 覆盖新发现的科学问题。

## 1. 当前是否可以投

**当前不能按现稿注册摘要或提交论文。** 当前摘要、C2 与结论仍混淆结构等价和部署工作点未确定；其他必要解释修正也未落实。旧 `SUBMISSION_DRAFT_COMPLETE=YES` 只说明当时投稿包机械完成，不代表今天科学可签署。

最大风险是 reviewer 发现：正仿射分数已经确定对应决策/ROC 关系，论文却把 clean 校准退化写成 blanket non-identifiability。它直接伤及中心贡献可信度。第二风险是把非响应、chance-level 分数或复算 PASS 分别误读为有害漏检、零信息或有效迁移。

收窄后的论文仍可成立为**指定 staged document-intelligence evaluator 的测量有效性审计**。本门禁不保证新颖性、录用或学位要求；按现有裁决，没有必须新增实验才能完成的 claim 修复。

RENE 适配性仍须作者判断：FinQA 的失配诊断不是有效执行实验中的“零效果”，不能独自承担 negative-result 能力证据；数值可复现也不能掩盖目标未被测量。修好逻辑后，仍可能受到贡献强度和研究严谨性的质疑。

| 资格面 | 当前状态 | 放行所需证据 |
|---|---|---|
| 科学解释 | **BLOCKED** | 下列必改项落实；作者可签署 C1–C3 的窄结论。 |
| 全稿与派生包一致 | **PENDING** | 稿件、matrix、scope lock、摘要注册包、TeX/PDF 与相关图注不再保留旧推断；原始数字与证据身份不变。 |
| 格式、引用、匿名 | 旧包有 PASS；修订包未核验 | 对最终同一版本重新做必要编译、版面、引用、匿名与证据对应检查；不追跑实验。 |
| 外部流程与权限 | **PENDING_OWNER** | 作者顺序/通讯作者、venue、artifact 可用性与事实时态、注册/提交分别获 owner 决定。 |

[venue requirements](../../paper/SANER_RENE_2027_REQUIREMENTS.md) 是既有核对记录；本轮未重新核验官网、期限或平台状态。正式外发前按最终 venue 的官方要求核对，不从历史日期推定仍可提交。

## 2. 必改：不靠 limitations 一句话抵消主文

| 项目 | 推荐的 claim-level 原则 | 必须传播的位置 |
|---|---|---|
| **A2 / BLOCKING：C2** | 拆开未舍入正仿射结构、记录秩关系、对应阈值/ROC 等价，以及退化 clean 面板上现行程序未选定唯一部署点。相同 FPR 的任意阈值不保证相同 TPR；`FPR=α` 与 `FPR≤α` 不混用。舍入、比较符和容差边界保留。 | contribution、matrix、abstract、§5.2/§6.1、conclusion；不能只补 caveat。 |
| **A1 / MAJOR：non-direct** | 撤回“零阶段信息”。保留冻结分数与 tie 规则；说明可分 M 与 R/N、不能分 R 与 N。full/direct 同为 1.0 不支持 hierarchy 性能增量。post-hoc 结果仍是 post-hoc。 | §5.5、§6.3、图注、摘要/结论涉及定位的概括。 |
| **A3 / MAJOR：OCR-like** | 保留冻结 scored surface 的 0/13；披露已有单 judge 的 13/13 equivalent。它支持良性吸收的替代解释，不是独立无害 gold；非响应也不是已证有害 false negatives。 | C1 的解释、结果/limitations，以及摘要/结论中可能暗示有害盲点之处。 |
| **A4 / MAJOR：案例比较** | 七项 judge–DR4 比较与一项 visibility–equivalence 比较分开。撤回同质 5/8 分歧率及排除随机噪声的机制推断；保留原始案例。 | 正文、承担解释的 caption/ledger；无须给摘要增加比例。 |
| **A5 / MAJOR + MINOR：FinQA** | 谓词有定义，所消费的下游 result/answer 未随扰动重算。V/D/O 可复算，但不估计执行扰动后的 detection ability。旧 audit 的正迁移解释停止承担证据；数值 PASS 与历史分类保留。 | C3/matrix、§5.6/§6.3、证据归属；摘要/结论只保留 mismatch 边界。 |
| **A6 / MAJOR：经验范围** | 经验结论落到本 evaluator 与受控扰动。long-horizon 仅作动机；推荐收窄标题，具体措辞由作者决定。 | 标题范围、摘要开头、贡献适用域和结尾外推。 |
| **A7 / MINOR：availability** | “已发布/已向 reviewers 提供”必须有实际可访问证据；否则按真实状态写。匿名 URL 建立、公开与投稿不是本轮动作。 | Data Availability、artifact 声明及注册材料。 |

## 3. 可改与禁止修改

**可改：** 不改变含义的语言/排版、术语一致性、局部说明顺序与已有材料导航。它们不能延迟必改项，也不要求重渲染冻结图件。标题具体用词可由作者选择，但经验范围必须准确。

**本次投稿收尾禁止：**

- 改原始数据、样本总体、split/join、分母、评分、tie、阈值、权重或冻结结果来救叙事；重标旧探索性/post-hoc 结果为确认性结果。
- 为保留 long-horizon、harmful blindness 或 hierarchy advantage 标签追加实验、重开 PR-03/Route B/FinQA/TAT-DQA，或把 thesis pilot 并入当前小论文。
- 将旧 90/111、退化 `[0,0]`、FinQA numerical PASS、repair 次数变为新的能力/迁移证据。
- 删除失败记录，改写历史审计 PASS，或把 Loop D self-audit 描述为独立 Loop C 验收。
- 未获改稿范围授权即编辑论文/claim/scope；未获外发授权即上传、注册或提交。

## 4. 未来 WP-E 的最短入口与作者验收

先读规则/当前状态 → 本门禁 → [科学裁决 §10](SANER_SCIENTIFIC_ADJUDICATION_v1.md#10-哪些修改改变-contribution--abstract--conclusion) → canonical 稿/matrix/[scope lock](../../paper/saner_rene_manuscript_scope_lock_v1.md)；只为具体 claim 追溯裁决证据索引。工作范围沿用 [蓝图 WP-E](THESIS_EXECUTION_BLUEPRINT_v1.md)，不增加实验工作包。

导师/owner 先授权具体稿件修订范围；Loop A 才执行文本与派生包同步，逐项记录裁决落实位置、保留数字和未决项。需要改变冻结图件或身份绑定时先报告，不能静默重绑。

最终作者验收须覆盖：A2 逻辑已改、A1/A3/A4/A5/A6 解释已对齐、A7 事实准确、所有承担 claim 的材料一致；必要独立复核真实完成或明确保留缺口，不能用 self-audit 充当独立验收。owner 另行决定是否接受剩余审稿风险与正式外发。**本文本身不使 WP-E 获准，也不使当前稿件变成 ready。**

---

## 12. 修订落实记录（2026-10-13，Loop D 执行）

> 本节由执行轮追加，记录 A1–A7 的落实情况与新资格状态。原有 §1–§11 判定文字保留为历史依据，不追改。

**落实动作：** 对 canonical manuscript、claim matrix、scope lock、abstract 注册包执行 A1–A7 文本修订，并重生成 `.tex` / bundle / PDF。**未新增实验、未改动任何数字、未改变证据来源、未恢复任何已关闭 claim。**

| 项 | 落实位置 | 关键改动 | 数字 |
|---|---|---|---|
| A2 (BLOCKING) | abstract、贡献段、§5.2、§6.1、结论、matrix C2、scope lock 贡献2+allowed claim | 拆为「正仿射/秩结构等价（unrounded、秩一致、对应决策等价）」+「clean 面板退化使已登记部署工作点未选定」，并保留 `FPR=alpha` 与 `FPR<=alpha` 的区分；删除 blanket non-identifiability 与 "cannot rank" | 0.375 / 2,382 / {0} 不变 |
| A1 | abstract、Fig-3 图注、§5.5、§6.3、matrix C2、scope lock | 删除 "carries no stage information"；改为 non-direct 在冻结 tie-as-incorrect 规则下可区分 M 与 R/N、不能区分 R 与 N | 0.3333 / 0.6667 / 1.0 不变 |
| A3 | abstract、§5.1、§6.1 limitations、matrix C1、scope lock | 披露单 judge 的 13/13 referential-equivalence；明确非响应不等于已证有害 false negative；保留两个 estimand | 0/13、0/11 不变 |
| A4 | §5.1 | 拆成 7 项 judge–DR4（**4 分歧 / 3 一致**，回源 `2026-09-06_d3_matched_fpr_stage_b.md` L122–132 确证）与 1 项 visibility–equivalence（零 judge 调用）；撤回 5/8 同质比例与排除噪声的机制推断 | 原始案例保留 |
| A5 | abstract、§5.6、§6.3、matrix C3、scope lock | 谓词改为「有定义、可执行、可复算」；错配定位为「所消费的下游 result/answer 字段未随扰动重算」；移除 "undefined" | V/D/O 不变 |
| A6 | 标题、abstract 开头、贡献适用域、结论外推、matrix thesis、scope lock | 经验对象收窄为 staged document-intelligence evaluator；long-horizon 降为动机；结论改为设计建议而非经验定律 | 无 |
| A7 | Data Availability | 改为「prepared for release / planned to be made available」；明示匿名库与 DOI 尚未建立 | 无 |

**新资格状态**

| 资格面 | 状态 |
|---|---|
| 科学解释 | `REVISIONS_APPLIED / INDEPENDENT_VERIFICATION DELIVERED`（2026-10-13：v2 CONDITIONAL → 9 项修复 → v3 items/claim PASS；一处单字图注按审计裁定修复并复验；见 `LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`） |
| 全稿与派生包一致 | 已同步 manuscript / matrix / scope lock / abstract 包 / tex / bundle / PDF（同一版本） |
| 格式、引用、匿名 | 本次重编译后复验：9 页（正文含附录 ≤10，references 约 1 页 ≤2）、0 overfull、引用 21/21 解析、无 `??`、metadata 匿名、禁语 0 |
| 外部流程与权限 | `PENDING_OWNER`（作者顺序/通讯作者、venue、匿名 artifact URL、注册与提交授权） |

**更新（2026-10-13）：独立 Loop C 复核已交付**（设计 launcher 通道）：v2 = CONDITIONAL（9 项残留）→ 全部修复（commit 6655201）→ v3 = item application PASS / claim boundary PASS；package 残余仅一项由审计方裁定的单字图注修复（删除 "also"），已落实并由双端机器校验复验（`PRE_SUBMISSION_AUDIT = PASS`、`WIDE_EVIDENCE_CHECK = PASS`）。完整记录：`LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`。**仍未完成：** A7 的匿名 URL 未建立；标题最终措辞仍属作者决定（本记录采用候选 T1）；native-speaker 终审未做。

**本记录不使稿件变成 ready，也不授权任何外发动作。**
