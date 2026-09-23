# Phase 1a 数据门复核：`DATA_NO_GO` 经穷尽搜索**确认成立**，但 gate 1 的证据基础是「隔离路径口径」

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: **不取代、不修改、不解除** `docs/experiments/2026-09-23_phase1a_data_no_go.md` 的 `DATA_NO_GO` 结论
> 用途: 上一轮实证「隔离验收 worktree 会静默缺少 production 拥有的 gitignored 大件」并因此产生 4 个假失败。本件据此复核：`DATA_NO_GO` 审计是否也受同一环境影响？**结论分两半且方向相反**——决定性门**确认成立**（比原来更强，因为是穷尽搜索而非沿用），但 gate 1 的证据基础确为隔离路径口径，故**外部补充数据的索取范围可以收窄**。
> 边界: 全程只读。**未改 `DATA_NO_GO` 报告一个字节、未解除或削弱其结论、未改任何判据**；未启动 Phase 1a/2；未批准任何数值。本件**只记录 aggregate 计数与哈希，不记录任何行级内容或样本文本**（与合同 “It never writes sample text into the report” 同口径）。

## 1 为什么要复核

`DATA_NO_GO` 报告 “Assets actually found” 一节写：

> In the isolated VGMC path, `injected_tables.json` is present with the previously recorded SHA256, but **`injection_map.json` is absent**.

其门槛表 gate 1 亦写 “Source tables and an auditable injection map are incomplete **in the isolated input path**”。两处都**自带隔离路径限定词**，措辞是诚实的。但上一轮实测发现：`injection_map.json` **在 production 里是存在的**（36 004 字节），把它复制进隔离 worktree 后 4 个 VGMC 测试立即由 `FileNotFoundError` 转为通过。

⇒ 于是必须回答一个此前无人验证的问题：**gate 1 判「不完整」，是数据真的不完整，还是审计环境不完整？** 若属后者，外部数据 owner 会被要求重新交付一份**其实已经存在**的东西。

## 2 审计确实跑在隔离 worktree 内（trace 实证）

报告 “Evidence and boundaries” 指明审计 trace 留存于 GB10 `/tmp/phase1a.stderr`。该文件**仍在**（2 568 730 字节，mtime 09-23 00:31）。对其做路径频次统计：

```text
 36  /home/testuser/wzh/projects/agents_final_tech_accept_d351d7e   <- 隔离验收 worktree
  9  /home/testuser/wzh/projects/agents_final_tech                  <- production
  7  /home/testuser/wzh/projects/agents_final_tech_accept_0aee20d
```

⇒ 审计主体在 **`agents_final_tech_accept_d351d7e`** 这个隔离 worktree 内执行，与报告自述的 “isolated VGMC path” 一致。另注：`grep -in injection_map /tmp/phase1a.stderr` **零命中**，故「absent」这一判断的具体取证命令行未留在 trace 内，无法从 trace 直接复核其取法；本件因此改为**直接对 production 与全盘做正向存在性搜索**（§3、§4），不依赖 trace 反推。

## 3 正向确认：production **已有** gate 1 所指的两类工件（含哈希）

| 角色 | production 路径 | 字节 | sha256 | mtime |
|---|---|---|---|---|
| `source_tables` | `data/research/drift_v0/input/tatqa_tables.json` | 1 442 890 | `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` | 2026-08-18 |
| `injection_map` | `data/research/drift_v0/output/injection_map.json` | 36 004 | `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e` | 2026-08-18 |
| （相关）注入语料 | `data/research/drift_v0/output/injected_tables.json` | 2 568 361 | `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9` | 2026-08-18 |
| （相关） | `data/research/drift_v0/sample_injected_tables.json` | 105 471 | `58660f445983cdeeaf16a31e75bc01c1f8acc13b1d5e63b85db5e0a1b9d31317` | 2026-08-18 |
| （相关） | `data/research/drift_v0/output/report.json` | 543 | `1a82f8e9c295413e8b350e345c42c2c7e29c2e24eba3522246af8b6b0f9a862f` | 2026-08-18 |

`injection_map.json` 的**结构与规模**（aggregate only）：

```text
top keys      : mapping, meta
meta          : deterministic = true
                input        = "data/research/drift_v0/input/tatqa_tables.json"
                ratio        = 0.3
                seed         = 42
                version      = "v0"
mapping       : 118 条
每条 entry 键 : col, injected, original, row, seed_component, source_key, type, uid, variant
distinct uid  : 95
type 分布     : alias_variant 47 / mixed_lang 20 / date_variant 17 / prefix_noise 16 / ocr_similar 13 / unit_suffix 5
```

⇒ 这**正是** gate 1 所要求的 “an auditable injection map”：有确定性与种子、有输入溯源、有版本、逐条带 `uid`/`row`/`col` 与 `original`→`injected` 对应。其 **118 条注入 / 95 个 uid** 与计划件 §1.1 所记 Stage E「95 张表、118 个受控注入」**逐项吻合**，故它就是既有的那份权威注入图，不是别的东西。

## 4 决定性门确认成立：穷尽搜索**零命中**（`DATA_NO_GO` 不动）

gate 2「Independent correctness — Correct `map_to`/`hold` labels are all null」是决定性的那一道。对它及其余缺失角色做**正向存在性搜索**，而非沿用旧结论：

```text
搜索范围: production data/ · logs/graph/eval/ · ~/wzh/datasets · ~/wzh/m1_samples
         以及 ~ (maxdepth 6, 排除 venv/ 与 skills/)
gold_action              命中 0     <- 独立正确性标签：全盘无任何工件
label_ledger             命中 0
confidence_manifest      命中 0
parser_contract_receipt  命中 0
analysis_plan            命中 0
phase1a_manifest         命中 0     <- 全盘不存在任何 Phase 1a 包根
```

并直接核 `injection_map.json` **自身是否携带标签字段**：其 entry 键的并集为 `{col, injected, original, row, seed_component, source_key, type, uid, variant}`，与合同 `LABEL_FIELDS`（`sample_id/uid/col/gold_action/gold_target/quality_grade/reviewers/adjudication`）的交集为 **NONE**。

⇒ **注入图是「扰动真值」，不是「独立正确性标签」。** 它能告诉你哪个单元格被改成了什么，但合同要求的是带 ≥2 个独立 reviewer 身份、必要时经独立 adjudicator 裁决的 `gold_action`/`gold_target` 标签账本——**这类工件在 GB10 全盘为零**。

**结论：`DATA_NO_GO` 成立，且本件的确认强度高于原报告**（原报告为隔离路径内的审计观测，本件为跨 production 与全盘的正向穷尽搜索）。**本件不解除、不削弱、不建议解除该结论。**

## 5 但 gate 1 的证据基础确为隔离路径口径 ⇒ 外部索取范围可收窄

把 §3 与 §4 合起来看，9 个必需角色的实况是：

| 角色 | GB10 实况 | 是否仍需外部交付 |
|---|---|---|
| `source_tables` | **已有**，1 442 890 B，sha `3e7e0568…` | **否**（可直接绑定既有哈希） |
| `injection_map` | **已有**，36 004 B，118 条 / 95 uid，meta 完整，sha `d7612405…` | **否**（同上） |
| `schema` | **有一个候选**：`~/wzh/m1_samples/m1_table_schema.json`，14 253 B，sha `79bc3a17f6285e2b6071b5e8a3df5ae3927ce049f1d31c016c16e0a628ce9a3b`，top keys = `_comment` / `header_meta_fields` / `tables`，mtime 2026-08-08 | **待判**：它是 M1 生产表 schema，是否即 drift_v0 语料所需的 `schema` 角色属**语义判断**，本件不代判 |
| `label_ledger` | 全盘 0 命中；无任何 `gold_action` 工件 | **是**（且为决定性缺口） |
| `licence_record` | 仓内/数据区仅第三方库自带 LICENCE 文本，无本项目许可记录 | **是** |
| `confidence_manifest` | 0 命中 | **是** |
| `analysis_plan` | 0 命中 | **是**（且其字段集仍待决策 5 裁定） |
| `parser_contract_receipt` | 0 命中 | **是** |
| `learnability_feature_ledger` | 0 命中，且**仓内无任何生成器**（见姊妹件） | **是** |
| `phase1a_manifest.json`（包根） | 全盘 0 命中 | **是**（包根本身尚不存在） |

⇒ **可直接收窄的部分**：`source_tables` 与 `injection_map` **不必**要求外部重新交付——它们已在 production、可哈希绑定、且上一轮已实证复制进 worktree 后 VGMC 代码路径正常工作。`schema` 有一个待判候选。**真正必须由外部产生的 = 5 个角色（`label_ledger`、`licence_record`、`confidence_manifest`、`analysis_plan`、`parser_contract_receipt`）+ `learnability_feature_ledger` + 包根 manifest**，其中 `label_ledger` 的独立正确性标签是决定性缺口。

这不改变 `DATA_NO_GO`，但把「补什么」从 9 角色收窄到 **6 角色 + 1 包根 + 1 待判**，**直接减少外部交付工作量与来回轮次**。

## 6 建议（均需授权，本件未执行任何一项）

1. **按报告 §13 自己规定的 resume order 重跑一次审计**：该节原文要求 “establish a clean isolated worktree at the reviewed commit, **mount the private package read-only**, run the focused tests…”。上一轮与本件均证实：隔离 worktree **默认不含** `data/` 的 8 个 gitignored 大件，故必须先按安全门 §6.2 完整复制并逐文件核 sha256，再跑审计——否则 gate 1 会以「隔离路径口径」被再次记为不完整。
2. **给 `DATA_NO_GO` 报告追加（append-only）一条复核注记**：说明 gate 1 的两类工件在 production 已存在且哈希已记（§3 表），gate 2–6 经全盘穷尽搜索确认仍成立（§4），故结论不变、但外部索取范围按 §5 收窄。**不改既有正文与结论。**
3. **裁定 `schema` 角色**：`~/wzh/m1_samples/m1_table_schema.json`（sha `79bc3a17…`）是否即所需 `schema`；若不是，则 `schema` 回到「必须外部交付」一类。
4. **与既有「文档更正批」合并处理**：该批已含 4 项（角色数 8→9、命令块解释器、计划件 §Phase 2、`minimum_uid` fail-open 处置），本件 §6.2 注记与 §6.3 裁定可作为第 5、6 项并入，避免多次触碰同一权威件。

## 7 数据卫生声明（如实记）

本件调查过程中，为判断 `injection_map.json` 的结构曾打印其 entry 键与 `type` 分布；其中一次按 `injected` 字段取值时**意外输出了若干行级表头字符串**（该字段实为「注入后的列名文本」而非布尔标志）。这些字符串**一律未写入本件、未写入任何台账、未进入任何提交**；本件只保留计数、类型分布、uid 数与哈希。该语料输入为 `tatqa_tables.json`（TAT-QA 系公开语料），非甲方私有件；但为免口径含糊，仍按「aggregate only」处理，并在此如实记录该次输出。

同时更正一处易误用点：`injected` **不是**布尔标志，而是注入后的列名文本；`original` 为原列名文本。任何后续工件若要判定「是否被注入」，应使用 entry 的**存在性**或 `type` 字段，不能把 `injected` 当布尔用。

## 8 复现

```bash
ssh jinrong-dev
# 存在性（正向）
sha256sum ~/wzh/projects/agents_final_tech/data/research/drift_v0/input/tatqa_tables.json \
          ~/wzh/projects/agents_final_tech/data/research/drift_v0/output/injection_map.json
# 缺失性（穷尽、可复现；排除 venv/ 与 skills/ 的无关命中）
for N in gold_action label_ledger confidence_manifest parser_contract_receipt analysis_plan phase1a_manifest; do
  printf "%-24s %s\n" "$N" "$(find ~ -maxdepth 6 -iname "*${N}*" 2>/dev/null | grep -v /venv/ | grep -v /skills/ | wc -l)"
done
# 审计 trace 的路径频次（证明审计跑在隔离 worktree）
grep -oE "/home/testuser/[A-Za-z0-9_./-]*" /tmp/phase1a.stderr | sort | uniq -c | sort -rn | head
```

注：`/tmp/phase1a.stderr` 与本件引用的其它 `/tmp` 取证件**均非持久**，重启即失。故本件把全部哈希、计数与搜索命令写入正文，使结论可在 `/tmp` 清空后独立重做。

## 9 红线自查

- 未改 `DATA_NO_GO` 报告、预注册件、任何代码或配置一个字节；**未解除、未削弱、未建议解除 `DATA_NO_GO`**——本件结论是该门**确认成立**。
- 未改冻结判据/阈值/oracle/冻结 hash；未启动 Phase 1a/2；未批准任何数值、未填任何 `UNSET`；未授权训练或端点。
- 全程只读：未复制、未移动、未修改 production 任何文件；未 pull production（仍 `e5ab809` + 5 脏件）；未重启 daemon `1816933` 与 `:5050` `1868428`；未改 crontab；未重置 Loop B。
- 零模型调用、零 canary、零 judge、零起 run；未派发任何 Loop A/B/C 卡。
- 本件**不含任何行级样本内容**，只有计数、类型分布、uid 数、字节数与 sha256；调查中一次意外输出的行级表头串未入任何工件（§7 如实记）。
- 未动 `docs/33`、`docs/34`；四件用户资产零触碰；逐路径 add、无 `-A`/`--amend`/`--no-verify`。

---

## 10 追加（同日，append-only）：§5 的 `schema` 待判项已可用机械证据**关闭**

本件 §5 把 `~/wzh/m1_samples/m1_table_schema.json` 列为 `schema` 角色的**待判候选**，并注明「它是 M1 生产表 schema，是否即 drift_v0 语料所需的 `schema` 角色属语义判断，本件不代判」。该判断现已可用**机械证据**关闭，故按 append-only 追加本节；§5 原表格文字**不回改**（保留作轨迹）。

### 10.1 方法（aggregate only，不打印任何名称或行级内容）

只比较三类**聚合量**：标识符**基数**、标识符的 **Unicode 文字类别分布**（CJK / Latin / digit / other）、以及与语料的**交集大小**。**全程不打印任何表名、列名或行级内容**，以免重演 §7 记录的那次意外输出。

### 10.2 实测

| 工件 | 字节 | 顶层结构 | 标识符数 | 文字类别分布 | 与 schema 表标识符的交集 |
|---|---|---|---|---|---|
| `~/wzh/m1_samples/m1_table_schema.json`（候选） | 14 253 | dict，top keys = `_comment` / `header_meta_fields` / `tables`；`tables` 为 list；`header_meta_fields` 15 项 | **5** | **CJK 4 / Latin 1** | — |
| `data/research/drift_v0/input/tatqa_tables.json`（= `source_tables`） | 1 442 890 | list，len 2479 | **2479** | **digit 2317 / Latin 162，CJK 0** | **0** |
| `data/research/drift_v0/output/injected_tables.json` | 2 568 361 | list，len 2479 | **2479** | digit 2317 / Latin 162，CJK 0 | **0** |
| `data/research/drift_v0/output/injection_map.json` | 36 004 | dict，keys = `mapping` / `meta` | 115 | digit 89 / Latin 26，CJK 0 | **0** |

### 10.3 判定：该候选**不是** drift_v0 语料的 `schema` 角色

两条**互相独立**的证据同向：

1. **交集为 0**：候选 schema 的 5 个表标识符与三个语料工件的标识符集合**无任何交集**（`tatqa_tables` 0/5、`injected_tables` 0/5、`injection_map` 0/5）。
2. **文字类别不相交**：候选 schema 的标识符 **4/5 为 CJK**（中文报表类型名），而语料 2479 个标识符中 **CJK 为 0**（全为 digit/Latin 的 TAT-QA 系标识）。两者属**不同语言域**，不可能是同一套表的 schema。

**一处如实的自我限定（不夸大证据）**：`5 vs 2479` 的**基数差本身不作为判据**——候选 schema 的 `tables` 很可能枚举的是**表类型/模板**而非表实例，故基数不可直接比较。判定只依据上面两条（交集为 0 + 文字类别不相交），这两条与「类型 vs 实例」的解释无关。

### 10.4 对 §5 的影响：`schema` 回到「必须外部交付」，待判项归零

§5 原表把 `schema` 记为「**待判**」。据本节，该行应读作：

| 角色 | 修订后的实况 | 是否仍需外部交付 |
|---|---|---|
| `schema` | 唯一候选 `m1_table_schema.json`（sha `79bc3a17…`）经机械比对**判定不适用**（不同语言域、零交集） | **是** |

⇒ **外部索取范围由「6 角色 + 1 包根 + 1 待判」确定为「7 角色 + 1 包根」**，且**角色可得性上已无任何待判项**：

- **已在 production、可哈希绑定、不必外部交付（2）**：`source_tables`、`injection_map`
- **必须外部产生（7）**：`schema`、`label_ledger`、`licence_record`、`confidence_manifest`、`analysis_plan`、`parser_contract_receipt`、`learnability_feature_ledger`
- **另需（1）**：包根 `phase1a_manifest.json`（全盘 0 命中，尚不存在）

其中 `label_ledger` 的独立正确性标签仍是**决定性缺口**（§4 已用穷尽搜索证实全盘无 `gold_action` 工件）。

⇒ 附带意义：`DATA_NO_GO` 报告的补充合同（经 `2026-09-24_phase1a_supplement_contract_role_gap.md` 更正为 9 角色后）中，**2 个角色可由既有 production 工件直接绑定、7 个必须新交付**。这使该文 §6.2 建议的 append-only 更正注记可以把话说死，不再留「`schema` 待判」的悬空项。

### 10.5 本节复现与取证

```bash
ssh jinrong-dev
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/schema_role_check.py
```

| 文件（GB10 `/tmp`，仓外，不 commit） | sha256 |
|---|---|
| `schema_role_check.py` | `7ed9bfa48c9e083f2dc5484cacb7d52007db1734c91926f390c68e4d19f94ccc` |

脚本内**不含任何打印标识符内容的语句**（只打印 `len()`、文字类别 `Counter`、交集基数），故其输出本身即 aggregate-only，可安全转录。

### 10.6 本节红线自查

- 全程只读：未修改、未移动、未复制 production 任何文件；未 pull production（仍 `e5ab809` + 5 脏件）；未重启 daemon `1816933` 与 `:5050` `1868428`；未改 crontab；未重置 Loop B。
- **未改 `DATA_NO_GO` 结论**——本节只关闭一个**角色可得性**的待判项，该门仍成立且其决定性依据（§4）未变；未改任何代码、判据、阈值、oracle、冻结 hash；未启动 Phase 1a/2；未批准任何数值、未填任何 `UNSET`；未授权训练或端点。
- 未改 §5 原文（append-only；修订以本节 §10.4 的表为准，并明示其与 §5 原行的对应关系）。
- 零端点、零模型调用、零 canary、零 judge、零起 run；未运行任何测试或实验；未派发任何 Loop A/B/C 卡。
- **未打印任何表名、列名或行级内容**；输出仅为基数、文字类别分布与交集大小。
- 未动 `docs/33`、`docs/34`；四件用户资产零触碰；逐路径 add、无 `-A`/`--amend`/`--no-verify`。
