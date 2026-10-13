# WP-2 S0b 聚焦复查 — Loop C（round 2）

> task: `tatqa-wp2-s0b-20261013` | 审计者: GB10 Loop C（独立上下文）| 日期: 2026-10-13 | 总体判定: **PASS**
>
> 落盘说明: Loop C 写入通道再度被其沙箱拒绝（同 round-1 的误判）；本文件正文区为运行日志 `~/wzh/loop_runs/tatqa-wp2-s0b-20261013/c.log` 第 2 行起的逐字节转录（`tail -n +2`，17027 bytes，未改一字）。
>
> Loop D 应裁摘要（非审计内容）: F-2/F-3、F-4、F-8 三项修复全部 PASS（独立手推演 + 收据字节级对账 + git 一手印证）；F-5 状态保持正确，其闭环按 owner 2026-10-13 夜授权由 F-5 轮执行；F-9 注记经 `61e59dbd7` 提交历史一手印证成立；另备档一条等价形"错值"归因残留（F-10），在 F-5 轮一并修复。

## 审计正文（逐字节转录，17027 bytes）
写盘被拒（`Write` 未授权；bash 建档亦被沙箱挡下，且路径**就在**允许工作目录内——与 round-1 记录的同一误判）。按任务卡规定，完整报告置于下文，供转录落盘。

---

# WP-2 S0b 聚焦复查 — Loop C（round 2）

> task: `tatqa-wp2-s0b-20261013` | 审计者: GB10 Loop C（独立上下文）| 日期: 2026-10-13 | 总体判定: **PASS**
>
> 范围（按任务卡）: **只复查** round-1 的 F-2/F-3、F-4、F-8 是否关闭，以及 F-5 状态保持、F-9 注记是否成立。未重做全面审计，未跑 S4+，未改任何被审对象与历史文件。
>
> 红线: 零模型、零网络、零凭证、未 commit、未 push、未执行 S4+。
>
> 落盘说明: Loop C 写入通道被其沙箱拒绝（`Write` 未授权；`touch`/重定向被挡，路径就在允许工作目录内，属沙箱误判，同 round-1）。本报告全文置于任务收据答复正文，待转录落盘为 `docs/research/WP2_PREFREEZE_LOOP_C_AUDIT_v2.md`。

## 0. 复查方法与未验证面

**采用手段**（shell 白名单内）: 直接读取被审代码/收据/协议；`sha256sum` 独立重算哈希；`git status`/`git diff`/`git ls-files`/`git log` 核对历史件与改动面；对新 fixture 期望输出做**逐字段手推演**；对两份收据的同名段落做**字节级摘要比对**。

**未验证面（如实申报）**:

1. **未做进程级重跑**。`python3`（含 `-c`）、`jq`、进程替换均被本会话沙箱拒绝，与 round-1 同。另: `s0_run_fixtures_v2.py` 的落盘行为会覆写 `S0B_FIX_RECEIPT.json`（被审对象），红线禁止，故即便可用也不应原样重跑。替代手段见上。
2. **`~/wzh/tmp/` 不可列**（在允许工作目录之外），故 F-9 注记中"22:41 经 tmp 提示文件派发"这一环无法一手核验；影响评估见 §5。

## 1. F-2 / F-3 — 归因一致性 + 直接形 fixture — **PASS（已关闭）**

### 1.1 代码层面

`checker_v2.score_prepared` 现在两条形态分支对称：

- 等价形（`periods == [early, late]`，`delta_source == -gold.delta_source`，`unit != gold.target_unit`）→ `wrong_unit`（S0 期已有，分支 A）
- **直接形（`periods == [late, early]`，`source_correct`，`target_correct`，`unit != gold.target_unit`）→ `wrong_unit`（本次新增，分支 B）**

判据不是"实现自洽"而是**规范一致**：rev1.3 append §2 L21 明文

> `wrong_unit` remains available when source-unit arithmetic is correct but target-unit arithmetic **or the normalized target-unit label is wrong**.

L20 另立等价形侧。故 rev1.3 自述 `wrong_unit` 覆盖"标签错"（round-1 引述属实），修复把直接形对齐到该自述，方向正确。基契约 v1 §2 表 L35 的旧定义（"`delta_source` correct but `delta_target` wrong"）仍在 checker 中作为另一子分支保留，两者并存而非覆盖。

### 1.2 新 fixture 期望输出 — 独立手推演（不采信 Loop A 自述）

`fixtures/s0b_direct_form_fixtures_v2.json`（sha256 `aecae15fcb3bd00523c458e41471b6815b70b4f158e37c6af8528046b601c95a`，与执行报告一致）单例 `direct_form_same_scale_wrong_unit`。

推演输入: 表 `[["","2025","2024"],["Revenue","2.5","1.2"]]`，`row_index=1`，`period_late={col:1,label:"2025"}`，`period_early={col:2,label:"2024"}`，`source_unit="thousand"`，`target_unit="unit"`；答案 `{"row":"Revenue","periods":["2025","2024"],"delta_source":1.3,"delta_target":1300,"unit":"thousand"}`。

| 步骤 | 推演 | 依据 |
|---|---|---|
| `recompute_gold` | `late=2.5`, `early=1.2`, `delta_source=1.3` | checker.py L189-191 |
| 换算因子 | `thousand→unit` 在允许对集合内；`10^(SCALES[thousand]-SCALES[unit]) = 10^(3-0) = 1000` | checker.py L128-146, L10-16 |
| `delta_target` | `1.3 × 1000 = 1300` | checker.py L192 |
| `gold.target_unit` | `normalize_unit("unit") = "unit"` | checker.py L188, L84-92 |
| `parse_answer` | 5 键齐全、类型合法；`unit = normalize_unit("thousand") = "thousand"` | checker.py L244-270 |
| 行标签 | `"Revenue" == prepared.row_label` | 不触发 L279 |
| 分支 A | `periods` 非 `[2024,2025]` → 跳过 | checker_v2.py L36-41 |
| `correct_other_form` | 同上 → 跳过 | L42-47 |
| `wrong_period` | `periods == [2025,2024] == [late,early]` → 不触发 | L49-50 |
| 源/目标 | `source_correct = (1.3==1.3) = True`；`target_correct = (1300==1300) = True` | L52-53 |
| `source and not target` | False → 跳过 | L54-55 |
| **分支 B** | `True and True and "thousand" != "unit"` → **`wrong_unit`** | L56-61 |

**推演结论 `wrong_unit` = fixture 期望值 = 收据 `actual`。** ✓

**修复前路径**（无分支 B）: 依次落到 `correct` 分支（要求 `unit == target_unit`，False）→ 终端 `return {"outcome": "wrong"}`，与执行报告所载 before 行为 `actual=wrong` **逐字吻合**。✓

执行报告对形态的描述亦准确: 期间序、源差、目标差、量级换算均正确，仅单位标签错。

### 1.3 全量 re-run：无任何用例 not-correct → correct

**代码级证明（充分条件）**: 分支 B 只返回 `wrong_unit`；`CORRECT_OUTCOMES = {"correct", "correct_other_form"}`（checker.py L43），`wrong_unit ∉ CORRECT_OUTCOMES`，故该分支本身永不产生正确结果。其守卫 `unit != gold.target_unit` 与 `correct` 分支的 `unit == gold.target_unit` **严格互斥**，无法抢走原本会判 `correct` 的用例；其可达路径已由 `wrong_period` 前置返回限定为 `periods == [late, early]`，与 `correct_other_form` 要求的 `periods == [early, late]` 亦不相交。唯一被它替换的是终端 `wrong`——同为 not-correct。净效应仅 `wrong` → `wrong_unit` 重归因。

**实证（必要佐证）**: 对 `S0_FIX_RECEIPT.json`（修复前）与 `S0B_FIX_RECEIPT.json`（修复后）同名段落做字节级摘要比对，**四段全等**:

| 段落 | md5（S0 = S0B） | 结果 |
|---|---|---|
| `fixture_results`（全量 obligation 证据） | `e880ff17d3fe2b24cb8b3f33f5e9adc2` | 全等 |
| `metric_pipeline`（含 `outcome_counts`） | `0b6080bbb31e2c2ba268b1ef48361df2` | 全等 |
| `scoring_inputs` | `53d7ce15d30a296aa1fd46a63f29f027` | 全等 |
| `additional_checks`（9 类探针 + 回归辅助） | `1678aaecae357919ac69c590b20cbf9a` | 全等 |
| `dedicated_unit_gate_fixture`（3 例，fixture sha256 `812e537c…`） | — | 逐字段全等 |

即: 在既有 fixture 面上，**没有任何一个输出发生变化**（不只是"没有翻成 correct"，是一字未动）。该 re-run 确实经过改动后的打分器——`run_checks` 带 `SCORE_ITEM_CALL_LOG` 埋点并 `_require("no score_item call sites were exercised")`，`main()` 将 `run_fixtures.checker` 猴补为 `checker_v2`，故全部 `score_item` 调用走的是被改代码。

**"等价形用例仍 PASS"** 亦获证实: unit-gate 三例（`equivalent_form_same_scale_wrong_unit`、`thousand_to_unit_equivalent_form_wrong_unit`、`thousand_to_unit_equivalent_form_valid_unit`）期望/实际/fixture 哈希在两份收据中全等。

**判定: PASS。** F-2、F-3 关闭。严格性主张 `not_correct_to_not_correct_only` 属实。

## 2. F-4 — preservation 布尔的词汇 — **PASS（已关闭）**

### 2.1 格式

四处 preservation 布尔（顶层三项 + `source_receipt.preservation_check` 一项）现已全部经 `run_fixtures._safety_claim` 输出 `{basis, evidence, value}`，`basis` 一律 `"derived"`。该函数强制 `basis ∈ {"derived", "attested: true"}`（run_fixtures.py L103-108），正是 round-1 指出被绕开的词汇门。

与同代码库既有风格一致: v1 自身调用点（run_fixtures.py L676、L893、L932…）同为"字面布尔 + `derived` + 证据串"三元组；契约 §5(e) 要求 "Every safety boolean is either derived from executed behaviour or explicitly labelled `attested: true`"。选 `derived` 而非 `attested: true` 标签正确——这些事实由执行中的哈希行为推出，不是人工背书。

### 2.2 内容与 v1 哈希对账

`old_artifact_hashes` 在 S0 与 S0B 两份收据中**逐字节全等**（8 项），且 8 项哈希与**今日磁盘实测全部吻合**:

| 历史件 | 收据钉 = 磁盘实测 | |
|---|---|---|
| `FIXTURE_RECEIPT.json` | `f862cc0accf37a5e9fff50469d782d21355cb3a96d46314472edd12753531903` | ✓ |
| `WP1_RECEIPT.json` | `a06cf566243743cd77246d0748375460a45c172454de597f424faec827bc059b` | ✓ |
| `adapter.py` | `dbb5b55bbe48c36c9b5854dfe1780e3a9ca09e08ffe58331468d61ce21f52477` | ✓ |
| `checker.py` | `c919845b051a7cfbebfdc782ba4c9dcbd99cac8b950b46f8bd908fcdc2cb12f1` | ✓ |
| `provenance.py` | `75c3dea925e719fce248ee2f2a2febd88e6b44496b9bcd787117f8cab61f4cc3` | ✓ |
| `run_fixtures.py` | `215bae90a01bf8e34dc0adcc8a1f5e7a22f2c4ed29e05f3b307e1556d92dca07` | ✓ |
| `fixtures/synthetic_fixtures.json` | `acbe79d9c0c1123dcfcc4cbc764cd0bcc6a6359fad4530c814d546497f036a85` | ✓ |
| `run_logs/tatqa-wp1c-20261013.log` | `67a86b0ee820f25352907a9d9b88856cd393bfa57fc1ad277bc5e9d3af231b46` | ✓ |

**第二条独立信道**（不依赖收据自述）: `git status` 显示在审目录内**唯一的已跟踪改动**是 `docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md`（即 F-8 修复，见 §3）；`checker.py`、`adapter.py`、`provenance.py`、`run_fixtures.py`、`synthetic_fixtures.json`、`WP1_RECEIPT.json`、`FIXTURE_RECEIPT.json`、`PREREG_DRAFT_SKELETON.md` 以及 **5 份 run_logs**（`tatqa-wp1-*.log` 全套）经 `git ls-files` 确认均已跟踪且干净。round-1 的 C2 主张（历史件 10 项 + 5 份 run_logs 未动）成立。runner 另对 `S0_FIX_RECEIPT.json` 做前置钉校验（`require(sha256 == BEFORE_SHA256["S0_FIX_RECEIPT.json"])`，不符即拒写），该历史收据实测 `1085cde7…` 与钉一致。

### 2.3 残留措辞观察（不阻塞，不重开）

`wp1_run3_receipts_unchanged` / `wp1_run3_logs_unchanged` 的证据串写作 "runner hashes every **pinned** run-3 receipt / the **pinned** run-3 log before writing"。严格讲: runner 在写盘前**记录**这些哈希（`old_artifact_hashes`），但**仅对 `S0_FIX_RECEIPT.json` 做钉比对并失败即停**；run-3 收据/日志的钉并未在 runner 内比对。布尔内容仍为真（§2.2 已由收据外手段独立核验），可核验的证据是那份哈希映射本身，但 "pinned" 一词高估了 runner 侧强制性。建议下次动到该文件时改为 "records the SHA-256 of every run-3 receipt before writing"。**不影响本项判定**——round-1 所提缺陷是"绕开词汇、格式不可核验"，该缺陷已闭合，内容对账一致。

**判定: PASS。** F-4 关闭。

## 3. F-8 — 协议类别枚举与实现一致 — **PASS（已关闭）**

`git diff` 显示协议文档的改动**恰为一行**:

```diff
-- Primary: … (`correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `regressed`, `refused`, `unknown`).
+- Primary: … (`correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong`, `regressed`, `refused`, `unknown`).
```

修复前 7 类、缺 `wrong`——与 round-1 描述逐字吻合。修复后 8 类，与 `checker.py` 的 `OUTCOME_CLASSES`（L44-55，我方直接读取）**集合全等**: `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong`, `regressed`, `refused`, `unknown`。

runner 侧有精确集合对齐校验 `run_protocol_taxonomy_alignment`（`set(declared) == set(checker_v2.OUTCOME_CLASSES)`），收据 `protocol_taxonomy_alignment` 段记录 declared/observed 双列表全等，`protocol_sha256 = 9d52a339…` 与磁盘实测一致。基契约 §7(d) 早已声明八类（含 `wrong`），落后的正是协议文档，现已对齐。

（附注，非缺陷: 该校验为单向——验证 8 类**都出现**，不验证行内无第 9 个名字。我方直接读该行，内容恰为 8 个、无多余项。）

**判定: PASS。** F-8 关闭。

## 4. F-5 — 状态保持（owner/导师决策项）— **PASS（保持正确；仍为 item freeze 前的阻塞前置）**

- `normalize_unit` 与 `UNIT_ALIASES` 位于 `checker.py`，哈希 `c919845b…`，与两份收据之钉及 `PREREG_DRAFT_SKELETON.md` 的软件钉三方一致。`checker_v2.py` 以引用方式再导出（`normalize_unit = checker_v1.normalize_unit`、`UNIT_ALIASES = checker_v1.UNIT_ALIASES`），**无任何覆写**；`recompute_gold`/`prepare_item`（源/目标单位语义所在）同样原样再导出。F-5 涉及面未被触碰。
- `docs/research/WP2_TARGET_UNIT_RULES_DRAFT_v1.md` 状态 `DRAFT_PENDING_OWNER_ADVISOR_DECISION`，正文自述 "does not freeze the rule"；`PREREG_DRAFT_SKELETON.md` 状态 `DRAFT - NOT READY - NO PILOT AUTHORIZATION`，`target_unit` assignment 一栏 `PENDING`。**未冻结**。
- 草案仍载 round-1 的 F-5 数字（352 中 `currency` 36、`null` 312），与执行报告的自行披露一致。

**判定: PASS（状态保持正确）。** 但须明示: **F-5 本身仍是 item freeze 前必须由 owner/导师拍板的阻塞前置项**，本轮不解除、不推断、不代决。S2 草案维持 `DRAFT_NOT_FROZEN`。

## 5. F-9 — 转录件时间线注记 — **PASS（注记成立，记录瑕疵可解释、无科学影响）**

转录件 `WP2_PREFREEZE_LOOP_C_AUDIT_v1.md` L7 的 Loop D 备注所给解释，其**仓库侧环节获 git 历史一手印证**:

- 提交 `61e59dbd7`，时间 **2026-10-13 23:08:34 +0800**，主题 `docs(closeout): WP-2 pre-freeze execution cards (draft, not dispatched) + …`，改动集恰为 4 个文件: `memory/STATE.md`、`memory/THREADS.md`、`research/tatqa_wp0_2026/wp2/loop_a_prompt_prefreeze.md`、`research/tatqa_wp0_2026/wp2/loop_c_prompt_prefreeze_audit.md`。
- 这正是 round-1 报告"审计开始时该文件与 `wp2/` 目录均不存在"的两份卡片——由该次本地收尾提交带入仓库，故此前不存在。
- 卡片 mtime **23:09:18**，在该提交后约 44 秒，与"本地收尾提交后同步"吻合，而非事后补写审计轨迹。
- 卡面自述"尚未派发"与该提交主题自陈的 "draft, not dispatched" **同源一致**: 仓库内副本是派发前草稿，实际派发走 `~/wzh/tmp/` 提示文件。

**无科学影响**: 瑕疵位于任务卡**记录的时间序**，不位于任何被评估量。被审产物本身哈希钉定（§2.2），round-1 的实质审计是在内容已钉定的产物上做的；receipts 与 run_logs 才是执行记录。

**未验证面**: `~/wzh/tmp/` 在本会话允许工作目录之外，22:41 派发提示文件无法一手查看。该环节不承重——即便它有出入，也不改变产物哈希与收据内容的可核验性。

**判定: PASS。** 注记足以解释该记录瑕疵。

## 6. 总体判定

**PASS。**

三项修复（F-2/F-3、F-4、F-8）**全部 PASS**；F-5 状态保持正确、F-9 注记成立。

**必须随判定一同记载**: **F-5 仍为 item freeze 前的 owner/导师前置阻塞项**——`source_unit: currency`/`null` 语义与 `target_unit` 规则未决，352 题中 36 题在现行 `normalize_unit` 下仍不可评分。本判定不解除该前置，亦不授权任何 S4+ 动作。候选 v2 仍为 `DRAFT_NOT_FROZEN`，其隔离收据与全部 S4+ 关卡照旧待办。

### 残留观察（范围外，仅备档，不阻塞）

在 `checker.py` v1 与 `checker_v2.py` 中同样存在: 若答案取等价形（`periods == [early, late]`）、`delta_source` 取正确负值、但 `delta_target` 错误且单位标签正确，则依次跳过分支 A 与 `correct_other_form`，被 `wrong_period` 前置返回截获——尽管其期间表达是合法的等价形。此为基线既有行为，S0/S0b 均未改动它，round-1 亦未列为发现，**超出本轮范围**；此处仅备档，不影响本轮任何判定。

### 红线遵守

零模型调用、零 endpoint、零 judge、零网络、零凭证；未 commit、未 push；未执行 S4+；未改动任何被审对象与历史文件（`S0B_FIX_RECEIPT.json`、`checker_v2.py`、协议、fixture、历史收据与 run_logs 均未触碰）。

---

## 判定汇总

| 项 | 判定 | 要点 |
|---|---|---|
| F-2/F-3 | **PASS** | 直接形/等价形标签错同归 `wrong_unit`，对齐 rev1.3 §2 L21；新 fixture 期望输出我方手推演独立复现；四段 re-run 输出字节全等，无任何用例翻转 |
| F-4 | **PASS** | 四处布尔已过 `_safety_claim` 词汇门（`derived`+证据）；8 项历史哈希收据=磁盘全对账，git 干净面互证历史件未动 |
| F-8 | **PASS** | 协议 diff 恰一行，7→8 类，与 `OUTCOME_CLASSES` 集合全等 |
| F-5 | **PASS（状态保持）** | 未触碰、未推断；**仍是 item freeze 前 owner/导师阻塞前置** |
| F-9 | **PASS** | 提交 `61e59dbd7`（23:08:34, "draft, not dispatched"）一手印证时间线；记录瑕疵，无科学影响 |
| **总体** | **PASS** | 三项修复全关；F-5 前置不解除；不授权 S4+ |

报告因沙箱拒绝未能写入 `docs/research/WP2_PREFREEZE_LOOP_C_AUDIT_v2.md`，全文在此，待转录落盘。
