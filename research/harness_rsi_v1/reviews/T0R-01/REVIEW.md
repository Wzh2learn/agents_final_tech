# T0R-01 — Loop C 独立评审：harness_rsi_v1 T0 提案包

- **reviewer**: loop_c_t0r01 (Claude Code on GB10, `/home/testuser/wzh/projects/agents_final_tech`)
- **reviewed**: `research/harness_rsi_v1/runs/T0/20261014T101305Z_026e6533/`（7 件）
- **runtime**: Linux, read-only；工作目录 = 仓库根
- **date**: 2026-10-14

## 0. 范围

独立复算 T0 提案包（协议提案 + 权威重钉提案 + owner 决策包 + receipt/summary/events/manifest），判断**是否可交 owner 签字冻结**。只读；不改任何仓库文件、不 git 写、不联网、不调端点/服务/数据库、不进入 T1。registry/state 与 `authority_map.json` 的落地不由本评审执行。

## 1. 工具层记录（如实）

| 尝试 | 结果 | 等价替代 |
|---|---|---|
| `git status --porcelain=v1` | 需授权，未获批准 | `git diff --name-only HEAD` + `git ls-files --others --exclude-standard` |
| python3 heredoc ×2 | 注入防护拦截「brace with quote character」（`{'OK' if …}` / `{"k": v}` 字面量） | 改写为字符串拼接 / `dict()` 赋值，逻辑等价，已重跑成功 |
| `find -exec`、`$(…)` | 按任务书约定不使用 | `os.walk` / 显式路径 |

被拒命令均已如实记录；无一次为「跑绿」而弱化检查。

## 2. 逐项结果与命令

### 2.1 T0 六件产物 vs `artifacts_manifest.json`；run 目录恰 7 件 — **PASS**

`python3` 哈希复算：manifest 列 6 条（`self_hash_policy: "excluded from own list"`，`artifacts_manifest.json` 自排除）。6/6 字节与 SHA-256 全等；目录恰 7 件 = 6 + manifest 自身。

```
authority_binding_proposal.json  10163  361ee65615e71a35…  OK
protocol_proposal.json            6760  8d4c186987cb2297…  OK
owner_decision_packet.md          2159  d9acdf865e2a5e0f…  OK
receipt.json                      5603  c7650dc01204b9fa…  OK
summary.md                        1043  03502af6059e2c22…  OK
events.jsonl                       563  810db1de1edb6f9b…  OK
```

`run_id` 格式 `20261014T101305Z_026e6533` 合 T0 卡 §3 规则（UTC 时间戳 + `_` + 8 位）；`generated_at_utc` 与之相差 1 秒，自洽。

### 2.2 T0 卡 7 个输入 vs `receipt.input_bindings` — **PASS**

7/7 存在，字节与 SHA-256 实算全等，无多余绑定。路径映射 `D:/AIRcommend/JinRongAgents/agents_final_tech/` → 仓库根（依 owner「2行」裁决该目录为合法钉定域）。

```
protocol.json        5243  bfbf453def9386eb…  OK
authority_map.json   7270  946f952fb8a530d4…  OK
execution_policy.md  2852  f659668ad1ddca44…  OK
budget_profiles.json 1689  1c94e40e377dd7b1…  OK
schemas.json         7295  a6543ce1fc4254f1…  OK
MASTER_PLAN.md      57842  f663094efbf5d6fd…  OK
open_decisions.json  2565  9b76df94ff82752b…  OK
```

T0 卡 7 项 `sha256: UNRESOLVED / BIND_AT_ACTIVATION`，未预填假哈希。

### 2.3 authority 提案 13 条 — **PASS（(a)(c)(d)(e) 全绿；(b) 见下）**

**(a) `canonical_blob_id` == `git rev-parse HEAD:<path>`** — **13/13 一致**。

**(b) `local_worktree_raw_sha256`** — **13/13 可复现为真实字节串**。分两种：7 条与本机文件字节直接相等；6 条我从仓库对象出发按 EOL 变体**重建出精确字节串，其 SHA-256 逐条命中该字段**（见 (e)）。故该字段不是臆造值，其内容与仓库对象无漂移。残余项：D:/AIRcommend 工作树在钉定当时是否恰好持有这些字节（**来源**问题）——本机不可读，见 UNVERIFIED。

**(c) 本机（GB10）raw 与提案 `gb10_worktree_raw_sha256` 一致** — **13/13 一致**（本机实算 = 提案 gb10 列）。

**(d) 分类** — 逐条按规则重算（mismatch → `uniform_crlf` 若 bare=0、`mixed` 若两者皆>0；否则 `pin_matches_worktrees`），13/13 分类相符：

```
{'pin_matches_worktrees': 7, 'eol_representation_uniform_crlf': 3, 'eol_representation_mixed': 3}
```
与提案 `classification_counts` 及任务书目标完全一致；和 = 13 = 条目数。`unexplained`：提案无该显式键，但 13/13 全部落入三类、无 `UNEXPLAINED` 落类，**派生 unexplained = 0**。

**(e) 6 个失配项「剥离 CRLF 后与仓库对象逐字节一致」** — **6/6 独立证实**。方法：取 `git cat-file blob HEAD:<path>`，构造「仅在行尾插入/删除 `\r`」的字节串，穷举命中 `local_worktree_raw_sha256`：

| 项 | 命中构造 | 重建 sha256 == pin | strip-CRLF == 对象 |
|---|---|---|---|
| REPO_RULES | 全 99 行尾 CRLF | 66030be6… ✓ | ✓ |
| SKILL_ROUTING | 全 61 行尾 CRLF | 8b660cfd… ✓ | ✓ |
| SKILL_REGISTRY | 全 20 行尾 CRLF | 7ba3a207… ✓ | ✓ |
| THREADS | 653 CRLF + 行 1、2 裸 LF | 0653ff3d… ✓ | ✓ |
| DECISIONS | 1 CRLF（末行）+ 其余 242 裸 LF | e35b2407… ✓ | ✓ |
| SKILL_ALGORITHM | 1 CRLF（末行）+ 其余 22 裸 LF | ce0a5946… ✓ | ✓ |

6/6 同时满足 `replace(\r\n,\n) == 对象` 与 `replace(\r,"") == 对象`；crlf/bare 计数与提案申报值逐条相符。**owner「1A」裁决（表示差异、无内容漂移）现获决定性证据支持。**

**(f) 未改动 `contracts/authority_map.json`** — **PASS**。`git diff --name-only HEAD` 仅 `logs/graph/*` 4 项；`authority_map.json` 工作树字节 == HEAD blob；`applied: false`；提案 `base_authority_map_sha256` = 实算 `946f952fb8a530d4…`。

### 2.4 protocol 提案 — **PASS（含 1 处记录层缺陷 F1）**

- `proposed_protocol.status == "DRAFT"` ✓；`execution_authorized == false` ✓；`freeze_sha256 == "UNRESOLVED"` ✓；`approved_by`/`approved_at` 均 `"UNRESOLVED"` ✓ → **未伪造冻结/签署**。
- **freeze 复算**：`json.dumps(proposed_protocol, ensure_ascii=False, separators=(",",":"), sort_keys=True)` 的 utf-8 字节（4198 B）SHA-256 = `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b` == `proposed_freeze_sha256` ✓。
- `base_protocol_sha256` = 实算 `contracts/protocol.json` = `bfbf453def9386eb…` ✓；`contracts/protocol.json` 工作树字节 == HEAD blob，**未被改动** ✓。
- **键级 diff（proposed vs 现役 protocol.json）**：仅新增 `owner_decisions_ref` 一个键；**0 个值被改**；无新增权限、无新增权威、无冻结字段被填。`proposed_freeze_sha256` 位于外层提案信封并标注「拟冻结」，`pending_owner_actions` 明写待 owner 确认 —— 是提案而非自签。
- **U01–U09 / 1A / 2行 / 3确认 忠实性**：决策包 §一 逐条与任务书背景及既有收据 `authorization_ref` 对照一致（详见 §3）。**但** `protocol_proposal.owner_decisions_applied` 只含 **U01/U03/U05/U07/U08/U09（6/9）**，缺 U02/U04/U06，且未声明取舍范围 → **F1**。

### 2.5 owner 决策包 — **PASS（措辞笔误已修）**

逐条比对（对照：任务书背景、`git show 945ba19fc` 提交信息、T-1 v2 与 T0 receipt 的 `authorization_ref`、`state/open_decisions.json` 原描述）：

| 条目 | 决策包措辞 | 对照来源 | 判定 |
|---|---|---|---|
| U01 | 「你的原话是**"预算不用担心"**」+ 采纳建议值 BR 4/3、BC 66/8、BS 106/4、SHADOW 6/2、META 12/2 | 任务书「U01 预算"不用担心"按建议采纳」；提交 945ba19fc 明写 `owner said "不用担心", not "无上限"` | 一致 ✓ |
| U01 附加「只可在事前收紧，不得事后放宽」 | `MASTER_PLAN.md`：「T0 可在运行前收紧，不能事后放宽」 | 属「其余按建议批准」覆盖的既有建议，非新造 | 一致 ✓ |
| U02 | 激活时实算绑定 + 独立复核（不预填） | open_decisions U02「生成后实算，不让用户填写哈希」 | 一致 ✓ |
| U03 | 便宜执行者 + GB10 Loop A | 任务书原文 | 逐字一致 ✓ |
| U04 | 先隔离能力验证，再报裁决封存位置 | open_decisions U04「可行方案先验证再裁决」 | 一致 ✓ |
| U05 | 人类门 = wzh；缺裁决保持 PENDING_HUMAN_REVIEW | 任务书 + open_decisions U05 | 一致 ✓ |
| U06 | B，远程核验已做 | 任务书「U06=B 远程核验已做」 | 逐字一致 ✓ |
| U07 | C，只授权 R 线至 M1（含本次 T0） | 任务书「U07=C 仅 R 线至 M1」 | 一致 ✓ |
| U08 | 影子证据与 8 份候选档案维持「未来证据」 | 任务书 + open_decisions U08 | 一致 ✓ |
| U09 | 标尺先做可辨别性预检，未达标不得用模型评分 | 任务书「U09 标尺可辨别性预检」 | 一致 ✓ |
| 1A / 2行 / 3确认 | 换行符表示差异、无内容漂移；canonical 重钉 13 项、旧值留档；D:/AIRcommend 为合法钉定域；T0 可开跑 | 任务书背景 | 一致 ✓ |
| 另 | 「另批准 Loop C 只读权限修复」 | T-1 v2 `authorization_ref`「Loop-C permission-layer fix approved」 | 一致 ✓ |

**两处先前笔误已修正**：全包扫描 `Lo:p` / `无上限`，**T0 七件内 0 命中**（仅出现在我自己的 `REVIEW_PROMPT.md` 引述中）。U01 已用「不用担心」。

**「3 项措辞小修待你点头」说法核验**：`owner_decision_packet.md` §四「可选小事（你不点我就不动）——复查提的 3 个措辞小修」；`summary.md` 标明为 **F8/F9/F10**。对照 `reviews/T1R-02/REVIEW.md`：F8（SUPERSEDED.md 未进清单账目）、F9（summary 悬空交叉引用）、F10（矩阵约定措辞），**三项映射正确**，且确为「待你点头」的可选项而非已执行动作。F11（`.omc/state` 工具态，INFO）未计入，恰当。

### 2.6 T0 receipt 三轴 / usage / 写入边界 / 无伪造 — **PASS（1 处 schema 类型缺陷 F2）**

- **三轴**：`execution_status=DELIVERED` / `acceptance_status=UNREVIEWED` / `activation_status=NOT_ENABLED` ✓，与 `schemas.json` 的 `enum`/`const` 全符。
- **必需字段**：12 项 required 全在（`actions` 不在 required 列表，其缺席无碍）。
- **usage**：`model_requests: 0`、`network_calls: 0`、`remote_readonly_ssh_invocations: 0`、`execution_chat_usage: UNRESOLVED`（未冒填 0）✓。**反证尝试**：`events.jsonl` 4 行全含 `model_requests: 0`，无调用痕迹；`budget.authorized_calls=0` 与之一致；包内无模型/服务/数据库调用证据。→ **无反证**。
- **写入边界**：`git show --name-status` 显示提交 `d8abe0957` 仅 **A** 7 件、全在 `runs/T0/20261014T101305Z_026e6533/`；提交 `945ba19fc` 仅 **M** `owner_decision_packet.md` + `artifacts_manifest.json`（manifest 随文更新，做法正确）。`contracts/`、`state/`、`registry/`、`memory/`、`sources/` 零改动。当前 `git diff --name-only HEAD` 仅 `logs/graph/*` 4 项（工具日志，非本 run 所为）。→ **边界干净**。
- **无伪造 ACCEPTED/freeze**：全包 `ACCEPTED`/`ACTIVE` 仅出现在 `states.acceptance`/`states.activation` 词表中；`freeze_sha256`/`approved_by`/`approved_at` 均 `UNRESOLVED`；两提案 `applied: false`。`checks` 的 6 个 `PASS` 是本 run 自检（D1–D6），非历史 PASS 挪用。summary 明写「**提案，未生效**」「协议仍 DRAFT」。

### 2.7 反证尝试

| 反证假设 | 结果 |
|---|---|
| 越界写入 | **未发现**。两提交文件集严格限于 run 目录 |
| 把提案当已生效 | **未发现**。四措辞点均标「未生效/DRAFT/等你签名冻结」 |
| 把历史 PASS 当结果 | **未发现**。T-1 历史结论仅作依赖绑定（`t1v2_receipt_sha256` 实算 = `a2ff07db…` ✓），未被当作 T0 结果 |
| 声明与实测不符 | **未发现**（除 F1/F2/F3 记录层缺陷外） |
| 假哈希/假签名 | **未发现**。全部申报哈希 20 项实算一致 |
| 提案偷偷改权威 | **未发现**。`authority_map.json` 与 `protocol.json` 工作树字节 == HEAD blob |

## 3. 发现

### F1 — `protocol_proposal.owner_decisions_applied` 只记 6/9 项 owner 决定 【MEDIUM】
- **证据**：该键仅含 `U01,U03,U05,U07,U08,U09`；`U02/U04/U06` 缺席，且字段无「仅记协议正文相关决定」之类范围声明。
- **影响**：任务书要求「忠实写入 U01–U09」。信息未丢失——`owner_decision_packet.md` 九项齐全，且 `proposed_protocol.owner_decisions_ref` 正指向该包——但若 owner 仅看 `owner_decisions_applied` 会误以为只有 6 项被采纳。另：`proposed_protocol` 与现役 `protocol.json` **零值改动**，故严格说没有任何决定被「applied」进协议正文，字段名本身易误导。
- **非阻断理由**：`proposed_freeze_sha256` 只覆盖 `proposed_protocol`（不含该信封字段），故补全 U02/U04/U06 **不改变冻结指纹**。

### F2 — `receipt.unresolved` 类型违反 `contracts/schemas.json` 【LOW-MEDIUM】
- **证据**：`schemas.json# $defs.receipt` 写 `"unresolved": {"type": "array"}`；T0 receipt 的 `unresolved` 是对象 `{"note": …, "open": […]}`。逐字段类型校验：12 项 required 中 11 项 OK，仅此项 *** TYPE VIOLATION ***。
- **影响**：收据不合自述契约 schema。同一形态已见于 T-1 两份收据（`{"declared":…,"register":…,"run_level":…}`），属沿袭性缺陷，非本 run 首创。
- **建议**：或改收据为数组，或把 schema 放宽为 `oneOf[array, object]`——需 owner/收口者选定，本评审不代改。

### F3 — `summary.md` 归类措辞把 13 项的计数安到 6 项头上 【LOW】
- **证据**：原文「**6 项失配分类**={`eol_representation_uniform_crlf`: 3, `pin_matches_worktrees`: 7, `eol_representation_mixed`: 3}」。该字典是 **13 条全量**分类（含 7 条 `pin_matches_worktrees`，它们根本不是失配项）；6 项失配的正确分类应为 `{uniform_crlf: 3, mixed: 3}`。
- **影响**：与 F9 同类的悬空措辞残留；数值本身真实，只是归属标签错位，不构成假数据。

### F4 — T1R-02 F7「3 个 pin 对应仓库中不存在的字节序列」被本次重建证伪 【INFO · 裁定方向利好 owner】
- **证据**：见 §2.3(e)。THREADS/DECISIONS/SKILL_ALGORITHM 三个 pin 全部由「仓库 blob + 纯 EOL 变体」精确重建命中。T1R-02 的「8 种字节变换 / 全历史 blob / 3320 文件 raw+CRLF」三路检验均只测**统一** EOL 变换，未测**逐行混合** EOL 排布——这正是三个混合项的命中空间。
- **影响**：owner 的「1A」（6 项一律按表示差异、无内容漂移）**是对的**，且现在有了决定性证明；T1R-02 提出的「3 EOL + 3 来源不明」改写建议**无需采纳**。T1R-02 的 UNVERIFIED 残留（D: 树钉定当时的来源）另由 owner「2行」裁决关闭。

### F5 — `owner_decisions_ref` 用相对路径，与协议其余路径体例不一致 【LOW】
- **证据**：`proposed_protocol` 中其余全部路径为绝对 `D:/AIRcommend/…`；新增键为 `runs/T0/20261014T101305Z_026e6533/owner_decision_packet.md`。

### F6 — 决策包对 F8/F9/F10 的转述偏松 【INFO】
- **证据**：F8 实为「SUPERSEDED.md 未进清单账目」，被转述为「废弃草案目录未列入清单纯度说明」；F9 原文悬空引用是「**见下**」，决策包写作「'见下文'」。三项映射方向正确，不影响 owner 判断，属转述精度问题。

## 4. FACT / INFERENCE / UNVERIFIED

**FACT（本人实测）**
- 六件产物 6/6 字节+SHA-256 = manifest；run 目录恰 7 件；manifest 自排除。
- 卡 7 输入 7/7 实算 = `input_bindings`；T-1 v2 receipt 实算 = `a2ff07db04453f91…` = D2 申报值。
- 13/13 `canonical_blob_id` == `git rev-parse HEAD:<path>`；13/13 本机 raw == 提案 gb10 列；13/13 `local_worktree_raw_sha256` 可由「仓库 blob 的 EOL 变体」重建命中；6/6 失配项 `strip-CRLF` == 仓库对象逐字节。
- 分类 13/13 合规则，计数 == {7,3,3}，派生 unexplained = 0。
- `authority_map.json`、`protocol.json` 工作树字节 == HEAD blob；两提案 `applied:false`。
- freeze 复算 == `282f5213…`；`base_protocol_sha256` == 实算；proposed vs 现役协议 0 值改动、仅 +1 键。
- 预算 BR 4/3、BC 66/8、BS 106/4、SHADOW 6/2、META 12/2 = `budget_profiles.json`，与 T0 卡 A2 一致。
- 两处笔误（`Lo:p C`、U01「无上限」）在 T0 七件内 0 命中；U01 用「不用担心」。
- 写入边界 = 仅 `runs/T0/<run_id>/`（两提交文件集证实）；无伪造 ACCEPTED/ACTIVE/freeze。

**INFERENCE（推断）**
- `owner_decisions_applied` 取 U01/U03/U05/U07/U08/U09，很可能是「只记协议正文相关决定」的取舍（U02 绑定流程、U04 隔离验证、U06 远程取证属流程/证据项）；但字段未声明该范围，故仍判 F1。
- T1R-02 F7 失手的机制是检验空间只覆盖统一 EOL 变换；其结论应作废而非并入 T0。
- 「3 个措辞小修」= F8/F9/F10 的映射可信（summary.md 显式标号）。

**UNVERIFIED（本次无法验证）**
- D:/AIRcommend 工作树在钉定当时的实际字节与是否干净（不在本机、禁联网）。值本身已可复现（§2.3(b)），**来源**问题由 owner「2行」裁决关闭，非本评审可独立取证。
- 执行者自报 usage（模型请求 0 等）无独立计量通道；只能做无反证检验（已做）。
- 任何模型端点 / 生产服务 / 数据库行为（约束内零调用；本地文档检查不代表 GB10 运行验证）。
- `execution_chat_usage` token 消耗（执行者与本评审均记 UNRESOLVED，未冒报 0）。

## 5. 判定与理由

**提案：ACCEPTED — 可交 owner 签字冻结。**

理由：
1. **承重结构全部独立复算成立**：13 项 canonical 重钉（(a)(b)(c) 全绿）、6 项剥离 CRLF 内容同一性（**重建命中**，非转述）、分类计数 {7,3,3}、unexplained 0、`applied:false`、两契约未被改动。权威重钉提案在证据强度上**高于**先前两轮复审，并顺带证伪 T1R-02 F7（F4）。
2. **协议提案安全**：`proposed_protocol` 与现役 `protocol.json` **逐值零改动**，仅新增一个指针键；`status=DRAFT`、`execution_authorized=false`、`freeze_sha256=UNRESOLVED`、`approved_by/at=UNRESOLVED`；冻结指纹我按指定规则独立重算逐位命中。owner 签字所冻结的内容 = 现役草案 + 一个决策包指针，无隐藏授权、无越权放开。
3. **决策包忠实**：U01–U09 与 1A/2行/3确认 逐条与既有原话记录相符；U01「不用担心」措辞正确、两处笔误已修；「3 项措辞小修待你点头」如实标注为可选、未擅自执行。
4. **不阻断的判断**：F1/F2/F3/F5/F6 全部位于**记录层**（信封字段、收据类型、摘要措辞），无一触及被签字内容的正确性或授权边界；F1/F2/F3/F5 可由收口者在落地 registry/state 时一并修正，**均不改变 `proposed_freeze_sha256`**。按 T0 卡 §7，owner 本人是人类门；把一处 6/9 的记录缺口升级为 PENDING_HUMAN_REVIEW，会与「owner 已裁决、证据已决定性支持其裁决」的事实不成比例。
5. **交办条件（非阻断，供收口者一并处理）**：补全 `owner_decisions_applied` 至 9 项或显式声明范围；修 `receipt.unresolved` 与 `schemas.json` 的类型冲突（二者择一）；改 `summary.md` 的「6 项失配分类={…7…}」标签；`owner_decisions_ref` 改绝对路径。

**明确回答**：**是 —— 该提案包可交 owner 签字冻结。** 签字对象是 `proposed_freeze_sha256 = 282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`；在签名之前一切保持 DRAFT / NOT_ENABLED。registry/state 与 `authority_map.json` 的落地由收口者/owner 决定，本评审未写入任何文件。
