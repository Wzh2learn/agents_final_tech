---
status: 阶段 B 收口抽验（Loop D, 零端点）
date: 2026-09-07
card: docs/experiments/2026-09-01_d3_matched_specificity_card.md
card_id: TASK-20260901-D3
contract: 加编 3 C3-1..C3-6（抽验接口 = C3-6 ①②③④）
target_report: docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md
target_artifact: logs/graph/eval/d3_matched_fpr_stage_b.json
target_artifact_sha256_lf: e0cec25e39d801bae161f9fd954a30b93b16daa9ccc7fbe52f432b918bba3797
target_payload_sha256: 2e4a828ca5c07ea20a3828a65c800d2fec8e804720d2e49247f6f8cdc99531b7
target_ledger: logs/graph/eval/d3_stage_b_call_ledger.jsonl
spotcheck_artifact: logs/graph/eval/d3_stage_b_closeout_spotcheck.json
spotcheck_script: research/paper_d3_stage_b_closeout.py
phase: closeout_loop_d
endpoint_calls: 0
---

# D3 阶段 B 收口抽验（Loop D, C3-6 接口全项）

> 执行: Loop D 2026-09-07（主线程续接; 旧线程 `01a04e13` 因 Codex session 结构损坏弃用, 见 §11 F-0907-4）
> 范围: **只抽验 Loop A 已交付工件**——零重跑、零新端点调用、零判据改动、零重新归类
> 判定纪律: 收集与判定分离照旧; 本次只做「测量契约遵循 + 数字可复算」核验, **不裁定 judge 与 DR4 谁对**（归 autopsy）

## 0 一页结论

**27/27 抽验项全 PASS（`all_pass=true`）⇒ 阶段 B 测量契约遵循成立、数字全部可独立复算, 可正式关闭, 进入 D3 autopsy（停一次, 另批）。**

- **C3-6① prompt 逐例比对不抽样**: 28/28 由「卡 C3-2 冻结模板 + 冻结源工件（D1 注入表 / tables_v2 uid8 映射 / GB10 sha 校验语料镜像）」**独立重建后 byte-equal**; 占位符词表精确 5 项; 28 个 `prompt_sha256` 独立重算全等且唯一; 防泄漏骨架区零命中（独立词表扫描）。
- **C3-6② 计数器 ≤200 工件自证 + JSONL 逐行**: 计数器 **31 ≤ 200**（单跑预期上界 57）; 账本 **62 行** = reserve 31 + call 28 + canary 3; reserve 计数 **1..31 连续无跳号**; 双恒等式成立（`counter == canary + call_records`、`reserve_lines == counter`）⇒ 零计数外推理请求; invalid 重试 **0**; 28 例各恰好一次有效判定; 账本 28 行 `prompt_sha256` 与工件逐例相同（跨文件一致）。
- **C3-6③ 端点隔离**: `ports_observed=[8004]` / `endpoint_violations=[]` / GG6·GG7·GG13 全 true; 工件全文 URL 端口集独立提取 = `{8004}`（`:8006`/`:8008`/`:5050` 零触碰）; 本抽验脚本自身 socket 层封死、出站尝试 **0**。
- **C3-6④ 证据级别标注**: 27 项逐项标注（独立重算 19 / 存值一致 6 / 字段存在 2, 见 §3）。
- **两条方向性触发独立重算后确认命中**（① J-N2 equivalent 4/7 ≥ 4/7; ② J-N1 equivalent 14/21 ≥ 11/21）——已于 09-06 即时上报（THREADS `#D3-STAGE-B-CLOSEOUT`）, 本次复算同值, **不改任何判据**。
- 4 条 finding（观察器静默失效 / Windows EOL 假 FAIL / agreement 规则文档缺口 / 旧 session 损坏）见 §11, 均**不影响阶段 B 数字有效性**。

## 1 仓库与三方状态（收口时点）

| 项 | 值 |
|---|---|
| 本地 HEAD（收口前） | `20d74f6`（派发证据入账; 阶段 B 交付未拉） |
| 本地 HEAD（`git pull --ff-only` 后） | `39307d4` |
| origin/main | `39307d4` |
| GB10 | `39307d4`（Loop A 交付链 `cc7a700` → `654dc90` → `fa32a57` → `c501b10` → `39307d4`） |
| 拉取方式 | `git fetch` + `git merge-base --is-ancestor` 确认可快进 + `git pull --ff-only`（无 merge commit、无 stash、无 reset） |
| 工作区残件（**原样保留, 未提交未回滚**） | `side_handoff_20260827.md`(M) / `side_handoff_20260829.md`(M) / `IMPLEMENTATION_PLAN.md`(??) / `PROMPT.md`(??) / `_d3b_dispatch.sh`(??) |

残件处置归属: 两份侧线手递件按 09-06 批复「由侧线更新、主线程收口时只登记入账」; `_d3b_dispatch.sh` 为派发脚本本地副本（全文已逐字入 THREADS `#D3-STAGE-B-DISPATCH`）; `IMPLEMENTATION_PLAN.md` / `PROMPT.md` 为 08-29 路线沉淀期的执行状态页（内容已被 `docs/34` + 蓝图 + 计划三件取代）。四者统一归 **neat 收口卡**处置, 本次不动。

## 2 C3-6 抽验接口四项（逐条判定）

| 接口项 | 判定 | 关键证据 | 证据级别 |
|---|---|---|---|
| ① 契约遵循: 卡 prompt 全文 vs 工件 `prompt_text` 逐例比对（不抽样） | **PASS** | S-04/S-05（system + user 模板逐字取自卡, byte-equal + sha 双等）; S-09（28/28 独立重建 byte-equal, 零表截断）; S-10（sha 重算 + 唯一）; S-11（防泄漏独立扫描零命中） | 独立重算 |
| ② 调用计数器 ≤200 工件自证 + JSONL 逐行核对 | **PASS** | S-15（62 行逐行: 种类计数 / reserve 1..31 连续 / 双恒等式 / 零重试 / 28 例各一次 / 跨文件 sha）; S-16（canary 冻结 prompt sha 与卡一致, 3 次探针全 ok 且计数入账） | 独立重算 |
| ③ `:8006` 零触碰自证（工件断言 + ports 自证） | **PASS** | S-20（`ports_observed=[8004]` / `endpoint_violations=[]` / GG6·GG7 true / 工件 URL 端口集 = `{8004}`）; S-01（本脚本 socket 封死, 出站尝试 0） | 存值一致 + 独立扫描 |
| ④ 抽验报告逐项标注证据级别 | **PASS** | 本文 §3 + 工件 `payload.checks[].evidence_level`（三级图例见工件 `evidence_level_legend`） | 字段存在 |

## 3 27 项抽验清单

| # | 抽验项 | 结论 | 证据级别 |
|---|---|---|---|
| S-01 | 本抽验脚本零端点自证（socket 封死 + 零出站尝试） | PASS | 独立重算 |
| S-02 | 卡 sha 钉死: 现盘 == 冻结期望 `22eaa511…` == 工件 before/after | PASS | 独立重算 |
| S-03 | 冻结输入 6 件只读（GG9; JSON 件按 LF 归一, 语料件用 GB10 sha 校验镜像） | PASS | 独立重算 |
| S-04 | system prompt 逐字取自卡 C3-2（byte-equal + sha） | PASS | 独立重算 |
| S-05 | user 模板逐字取自卡 + 占位符词表精确 = 5 项 | PASS | 独立重算 |
| S-06 | J-N1 21 例清单: 卡逐字 == 工件 == 实际调用键（集合与顺序） | PASS | 独立重算 |
| S-07 | J-N2 7 例清单: 卡完整 key == 工件 == 调用键; `3789d7da#1` 不在 28 例内; J-N3 = 0 | PASS | 独立重算 |
| S-08 | C3-1 硬断言 A1–A6 独立复算（并集 21 / E7==DR4 / 不相交 / 逐字锚点 / H→E 排除 / uid8 1:1） | PASS | 独立重算 |
| S-09 | **prompt 28/28 独立重建 byte-equal（不抽样）** | PASS | 独立重算 |
| S-10 | `prompt_sha256` 逐例重算 + 28 唯一 | PASS | 独立重算 |
| S-11 | C3-2 防泄漏白黑名单独立扫描（骨架区 + uid/uid8） | PASS | 独立重算 |
| S-12 | C3-3 per-call 冻结字段 17 项齐备 + status 词表合法 | PASS | 字段存在 |
| S-13 | `raw_response` 独立保守解析 == 工件 `parsed`（28/28; 词表 + rationale ≤200） | PASS | 独立重算 |
| S-14 | C3-4 模型设置逐例一致（model / temperature=0 / max_tokens=512）+ 契约存值 | PASS | 存值一致 |
| S-15 | **C3-5 账本逐行核对 + 双恒等式 + ≤200 + 零重试 + 28 例各一次 + 跨文件 sha** | PASS | 独立重算 |
| S-16 | canary 冻结 prompt sha + 3 次探针全 ok + 计数入账 | PASS | 独立重算 |
| S-17 | 判定聚合独立重算（交叉表 / 比率分母 / confidence / tokens / latency） | PASS | 独立重算 |
| S-18 | 8 行 DR4 对照独立重建（7 judge + 1 确定性）+ 逐行 agreement + tally | PASS | 独立重算 |
| S-19 | 方向性触发独立重算（① ≥4/7; ② ≥11/21） | PASS | 独立重算 |
| S-20 | 端点隔离（ports / violations / GG6·GG7·GG13 / URL 端口集） | PASS | 存值一致 |
| S-21 | 甲方标识零进入（GG12; 独立 AST 取 D1 冻结 token 表, 扫工件 + 账本 + 报告） | PASS | 独立重算 |
| S-22 | `payload_sha256` 独立重算 + digest 自洽 + 工件文件 sha | PASS | 独立重算 |
| S-23 | 13 门逐门存值核对 + `all_pass` + `window_abort=null` | PASS | 存值一致 |
| S-24 | 报告 Markdown 关键数字 12 项与独立重算逐项一致（F06 家族防误誊） | PASS | 存值一致 |
| S-25 | 报告 §4/§5 逐例 verdict 表（21+7 行）与工件一致 | PASS | 独立重算 |
| S-26 | STATE.md 阶段 B 节（11 项）+ THREADS `#D3-STAGE-B-CLOSEOUT`（8 项）与独立重算一致 | PASS | 存值一致 |
| S-27 | 报告 §6 8 行对照表（direction / 证据 / agreement）与独立重建逐行一致 | PASS | 独立重算 |

分布: 独立重算 19 / 存值一致 6 / 字段存在 2。**judge verdict 一律按「judge 证据」处理, 未作为 ground truth 写入任何判定。**

## 4 调用会计（全部机械重算, 不引用报告散文）

| 量 | 重算值 | 冻结口径 | 判定 |
|---|---|---|---|
| 计数器合计 | **31** | ≤200 硬门; 单跑预期上界 1+28+28=57 | PASS |
| canary 推理探针 | **3** | 计数（C3-5） | 如实记账（3 次开窗） |
| 正式 judge 调用记录 | **28** | 冻结 21+7+0 | PASS |
| invalid 重试 | **0** | ≤28, 字节相同 payload | PASS |
| J-N3 调用 | **0** | 冻结 0（不夹带） | PASS |
| 账本总行数 | **62** | append-only, 未清空未重写 | PASS |
| reserve 行 | **31**（计数 1..31 连续） | == 计数器 | PASS |
| 恒等式 | `31 == 3 + 28` ∧ `reserve 31 == counter 31` | C3-5 自证 | PASS |
| 每例有效判定次数 | 28 例各 **1** 次 | 不填补、不重复 | PASS |
| 开窗次数 | **3**（首窗 canary 1 + 正式 28; 装配缺陷修复后 canary 2） | 如实记账 | 已入账 |
| 本次交付调用（`new_inference_calls_this_invocation`） | **1**（仅 canary; `resumed_cases=28` 复用 append-only 账本） | 28 例正式判定只发过一次 | PASS |
| 成本 | tokens prompt 18 136 / completion 1 011; latency min 796 / median 1 072 / max 1 301 ms | S-4 次要指标 | 旁证 |

## 5 J-N1（21 例零信号「有害」注入语义危害性复判, 描述性）

- 判定分布: **equivalent 14 / meaning_changed 7**（valid 21, invalid 0）; confidence 全 high。
- 机制二分（按卡冻结子组独立重算）: 静默吸收 15 例 = **equivalent 14 / meaning_changed 1**; 阈值稀释 6 例 = **meaning_changed 6/6**。
- 形态观察（不改判）: 静默子组 14 例 equivalent 高度同质 = 纯字符级拼写扰动（`equty`/`capitai`/`divdend`/`operat1ng`/`liabilitie5`）; 稀释 6 例为「占比 → 绝对额」类口径改变。
- **本次收口不据此重归类任何注入、不改动 H/E/HI 三分类底表、不改动 S-2 检出分母 111。** 「纯字符级扰动是否计入有害集」= autopsy 议题（需用户裁定）。

## 6 J-N2（7 例现行 E 集 validity audit, 描述性）

- 判定分布: **equivalent 4 / meaning_changed 3**（valid 7, invalid 0）。
- 分歧**按扰动族成块**: 缩写/单位族（`Accumulated Amortization → amort` ×2、`Dividends Paid(1) → dividend`、`US$ → US [1]`）全 equivalent; 删限定语与货币符号族（`£m → m【】` ×2、`Free cash flow (pre-spectrum) → cashflow`）全 meaning_changed。
- 同形对判定自洽一致（同输入同输出）⇒ temp=0 下 judge 稳定, 分歧非逐例随机噪声。
- 分界实质落在「缩写是否算改口径」这一**判定标准歧义**——此句为 autopsy 输入, 非本次结论。

## 7 8 行 DR4 对照（Loop D 独立重建, 与工件/报告逐行一致）

| key | direction | current | dr4_oracle | 证据（本次独立取值） | agreement |
|---|---|---|---|---|---|
| `3789d7da#1` | H→E | H | E | deterministic: visible=true / absorbed=false / match_tier=0（源 tables_v2, **零 judge 调用**） | disagree |
| `50e78448#2` | E→H | E | HARMFUL | judge: equivalent（high） | disagree |
| `54c494f7#2` | E→H | E | HARMFUL | judge: equivalent（high） | disagree |
| `5e60c056#0` | E→H | E | HARMFUL | judge: meaning_changed（high） | agree |
| `73a817fc#1` | E→H | E | HARMFUL | judge: equivalent（high） | disagree |
| `b5aae4e9#0` | E→H | E | HARMFUL | judge: meaning_changed（high） | agree |
| `e67f7bf2#4` | E→H | E | HARMFUL | judge: meaning_changed（high） | agree |
| `e9730ea3#2` | E→H | E | HARMFUL | judge: equivalent（high） | disagree |

tally = **3 agree / 5 disagree / 0 unresolved**。`3789d7da#1` 按加编 2 澄清以确定性证据入账（零调用追加）, 方向不一致如实记 disagree, 未以 judge 补判。

**agreement 规则出处注记（F-0907-3）**: judge 行规则 = `(verdict == meaning_changed) == (oracle == HARMFUL)`; 确定性行规则 = visible ∧ ¬absorbed ∧ tier==0 而 oracle=E ⇒ disagree。两式**只固化在 Loop A 实现与本抽验实现中, 卡加编 2/3 只有列名无散文定义**。本次两实现独立同式且结果同值, 不构成数字风险; 但 D4 卡必须在冻结节写明该谓词, 否则「一致/不一致」不可复核。

## 8 方向性触发（C3-3 上报纪律, 非判据）

| 触发 | 冻结阈值 | 独立重算 | 命中 |
|---|---|---|---|
| ① J-N2 有效判定 equivalent（与 DR4 oracle 全 HARMFUL 反向） | ≥ 4/7 | **4/7** | **命中** |
| ② J-N1 有效判定 equivalent（动摇有害集选取与 D4 oracle「非等价即有害」隐含假设） | ≥ 11/21 | **14/21** | **命中** |

两条已于 09-06 14:4x 即时上报（不等 autopsy 排期）, 本次复算同值。**上报 ≠ 改判**: 判据、oracle、阈值、分类底表全部零改动。

## 9 边界例与异常清单（交 autopsy, 本次不裁定）

1. `567a03c7#1`（Exercise Date → Exercise date 2021-期末日期）: 静默吸收子组内**唯一** meaning_changed, 形态为「追加文字」而非字符级扰动 ⇒ 零信号集内真正语义有害疑似仅此 1 例。
2. `68b8d514#1`（Grant Date → Grant date 2019-报表明细日期）: 与上例**同形态**却判 equivalent ⇒ 同形反判, judge 内部一致性边界样本。
3. `3789d7da#1`（Revenues → sales）: 唯一 H→E, 确定性通道判已检出而 oracle 判等价 ⇒ 三证据线（类型级 E / 实例级 oracle / judge）互不完全一致的核心例。
4. 同形对 `54c494f7#2` / `e9730ea3#2`（amort）与 `5e60c056#0` / `b5aae4e9#0`（£m→m【】）: 判定自洽一致 ⇒ temp=0 稳定性旁证。
5. 家族成块分歧: 缩写/单位族全 disagree, 删限定语/货币符号族全 agree ⇒ 分界 = 判定标准歧义。
6. 执行期两处装配缺陷（占位符正则漏 `{col_1based}` / `Ledger._append` 内存镜像不同步致恒等式 30≠1+28 被 GG10 拦下）: 均已根因修复且**未放宽任何门**; 本次对恒等式与占位符词表独立复算通过 ⇒ 缺陷未污染交付数字。

## 10 主张边界（收口时点, 供 T7 与 autopsy 引用）

**目前实验支持**

- 在冻结测量契约下, 28 例判定可完整复现核验: prompt 逐字可重建、计数可逐行核账、端点隔离可自证、聚合可独立重算（本次 27/27）。
- 「零信号 = 有害」这一隐含假设**在实例级不成立**: J-N1 21 例中 14 例被 judge 判为等价, 且按机制分层（稀释 6/6 有害 vs 静默吸收 14/15 等价）。
- 缺陷类型标签（类型级 E）与实例级危害性（DR4 oracle / judge）之间存在**可测量的口径缺口**: 8 行 diff 上 3 agree / 5 disagree。
- judge 在 temp=0 下对同形输入稳定（同形对自洽）, 分歧按扰动族成块而非随机。

**目前实验不支持**

- 不支持「judge 或 DR4 任一方为 ground truth」——两者是**两条独立证据线**, 本次未裁定谁对。
- 不支持「分层协议在检出维度优越」（承 W1/W2 既有降级措辞, 本窗未新增检出主张）。
- 不支持把本窗 judge 分数与历史四维 judge 基线（4.94–5.0, 含 `:8006` xhigh 档）作跨比较（C3-4 口径注记）。
- 不支持据本窗重归类任何注入、改动 H/E/HI 底表、改动 S-2 检出分母 111, 或改动 D4 oracle——需 autopsy + 用户裁定。
- 不支持把「纯字符级扰动无害」写成结论: 本窗只证明 judge 如此判定, 未证明其判定为真。

## 11 Findings（本次收口新增, 均不影响阶段 B 数字有效性）

- **F-0907-1 观察器静默失效（机制级, 影响后续所有窗口）**: `/tmp/d3b_watcher.sh` 权限 **0644 无执行位**, 而 crontab 以 `*/5 * * * * /tmp/d3b_watcher.sh` **直呼路径**注册 ⇒ cron 每 5 分钟 permission denied 静默失败。后果: `loop_a_d3b_done.json` 从未落盘、`/tmp/loop_a_d3b_state` 从未生成、crontab 自清逻辑从未执行（残留至今）。对照证据: 前 8 个窗口 watcher（`w1/w2/d1/d2/d2r2/d3r2/dr4/dr4c`）权限均为 **0775** 且 done 件齐备; 本窗两脚本经 **scp 文件传输**落地（`d3b_dispatch.sh` 同为 0644）, 派发脚本以 `bash /tmp/d3b_dispatch.sh` 调用故无碍, watcher 被 crontab 直呼故失效。派发前置检查只验了 `bash -n` 语法, **未验执行位、未验首次 tick**。
- **F-0907-2 Windows EOL 造成冻结件 sha 假 FAIL**: 本机 `core.autocrlf=true`, 4 件冻结 JSON 输入的工作树字节 sha 与 GB10 记录不等, **LF 归一后 4/4 全等**（阶段 B 工件本地 raw `61b2c1b3…` / LF `e0cec25e…`, 后者与 Loop A 报告收据值逐字相同; 账本 62 处 CRLF）。仓库既有 `summary_recompute_guard` 已用 `sha256` + `sha256_lf` 双口径吸收此差异（本机 `check` 通过）⇒ 手工核对必须走双口径或 LF 归一, **GB10 为字节权威**。
- **F-0907-3 agreement 谓词缺散文定义**: 见 §7 注记。建议 D4 卡冻结节显式写明两式（judge 行 / 确定性行）, 并把「谓词入卡」列为派发硬前置。
- **F-0907-4 旧主线程 session 结构损坏（工具级, 与研究无关）**: 旧线程 `01a04e13` rollout 链第 2 段第 569 行存在一条缺 `call_id` 的 `function_call_output`（heartbeat 注入产物）, 被后续 episode 继承 ⇒ 每轮 API 400 `Invalid 'call_id'`; 该线程已弃用, 相关 heartbeat automation 已由用户删除（`~/.codex/automations` 现为空）, 原件已备份未改动。**运行态影响**: 阶段 B 交付后约 29 小时主线程无法执行收口, 收口由本续接线程完成。

## 12 红线自查（本次收口自身）

| 红线 | 结果 |
|---|---|
| 零端点 | ✅ 抽验脚本 socket 层封死, 出站尝试 0; 未新增任何 `:8004`/`:8006`/`:8008` 调用（`endpoint_calls=0`） |
| 零重跑 | ✅ 未执行 `--stage window`; 阶段 A/B 工件只读 |
| 冻结件零改动 | ✅ 6 件输入 sha（LF 归一口径）== 工件 before == after; 卡 sha `22eaa511…` 钉死一致 |
| 判据零改动 | ✅ E-1..E-4 / S-1..S-8 / R1-R4 / D1-D2 / 加编 1-3 全不动; 未重归类任何注入 |
| 收集与判定分离 | ✅ 本次只做契约遵循 + 数字复算; 「谁对」归 autopsy + 用户裁定 |
| 甲方数据零进入 | ✅ 独立 AST 取 D1 冻结 token 表扫工件/账本/报告, 零命中 |
| TAT-DQA 冻结线 | ✅ 零触碰（未解冻、未读取 joint-v1） |
| git 纪律 | ✅ 逐路径 add; 禁 `-A`; 禁 `--amend`; 未回滚任何非本次改动（两份侧线手递件与三件未跟踪残件原样保留） |
| 对外零发送 | ✅ 零外发（GB10 交互仅 ssh/scp 内网只读取证） |

## 13 收口判定与下一步

**判定: 阶段 B 可正式关闭。** 依据 = C3-6 四项接口全 PASS + 27/27 抽验全绿 + 13 门 `all_pass=true` + 数字全部可独立复算 + 零判据改动。

**停一次**（每段 autopsy 纪律）。下一步需用户批准后才动:

1. **D3 autopsy**（另批）: 核心问题 = 「harmful / equivalent 是否依赖 scorer / matcher 的等价类定义」, 以及该 scorer dependence 应写成**机制主张**还是**claim boundary**; 输入 = §9 六项边界例 + §5/§6 家族分层 + §7 三证据线缺口 + §8 两条触发。
2. 用户裁定 D3 的论文解释（含「纯字符级扰动是否计入有害集」, 影响 D4 oracle 与 S-2 分母 111）。
3. **D4 transfer 预注册卡**（只拟不执行）: oracle + 协议 + 阈值一次性冻结、见结果禁改; 必须吸收 §7 谓词入卡（F-0907-3）与本次机制分层证据; 解冻条款显式覆盖第二变化叶（仅 validation split / test 零触碰 / 完成即恢复冻结）。
4. 机制修复（不占研究队列, 建议随下一窗口派发前置落地）: watcher 统一以 `bash /tmp/x_watcher.sh` 注册或创建即 `chmod +x`; 派发前置检查加「执行位 + 首次 tick 实证」两项; 清理 GB10 残留 crontab 行（本次未动, 保留失效现场作证据）。

## 14 复现

```bash
# 零端点; 语料冻结件仅在 GB10, Windows 侧需先取 sha 校验镜像（3e7e0568…）
python research/paper_d3_stage_b_closeout.py                       # GB10（语料件在盘）
python research/paper_d3_stage_b_closeout.py --corpus <mirror>     # Windows（镜像 sha 必须 == 3e7e0568…）
python scripts/graph/hooks/summary_recompute_guard.py check docs/experiments/2026-09-07_d3_stage_b_closeout.md
```

## 15 更正注记（09-07 侧线抽验 + 决策 4A/5A）

> 性质: **只追加, 不回改原文, 不动收据**。决策 4A = 收据保持 v1 原状（不重跑审计脚本、不重铸 `payload_sha256`、不改 SUMMARY-GUARD 块）, 可复现性以 §14 为准。以下更正以本节为准, 原文对应句保留不改。侧线独立抽验已核过: 三方对齐、工件字节/哈希、计数恒等式、判定分布、DR4 8 行、两条触发、tokens/latency、prompt 28/28、端点隔离、F-0907-1 现场**全部成立**; 本节三条更正均不影响阶段 B 数字有效性, 不需返工重跑。

### 15.1 证据级别计数更正（F06 家族）

§2 C3-6④ 行与 §3 表末所写「独立重算 19 / 存值一致 6 / 字段存在 2」**有误**; 正确值 = **独立重算 21 / 存值一致 5 / 字段存在 1**（合计仍 27）。依据 = 结构字段机械计数 `payload.checks[].evidence_level`（实测 `independent_recompute=21` / `value_match=5` / `field_exists=1`; 唯一 `field_exists` = S-12）。误因 = 收口时按印象手数、未以结构字段为准（F06 家族「手抄数字」同型; 对策 = A21 关键数值绑定工件字段不手抄）。**判定不受影响**: 27 项结论与 `all_pass=true` 均不依赖该分布计数。

### 15.2 claim boundary 措辞锁死（审稿面）

§10「支持」列的「『零信号 = 有害』在实例级不成立」与「不支持」列的「本窗只证明 judge 如此判定, 未证明其判定为真」**不可并存**（前者读作已证否, 后者才是正确限定）。**论文可用口径锁定为后者**, 冻结表述:

> 在冻结 judge 协议（C3-2 模板 / C3-4 `:8004` A3B temp=0）下, 21 例零信号注入中 14 例被判 equivalent ⇒「零信号即有害」的**隐含假设在实例级不可维持**; 且该判定依赖 scorer / matcher 的等价类定义（依赖性归 autopsy + F-0907-3）。

禁止把 judge verdict 或 DR4 oracle 任一方写成 ground truth; 禁止据本窗重归类注入、改 H/E/HI 底表或改 S-2 检出分母 111。

### 15.3 权限数字更正

§11 F-0907-1 中 `0644` 应为 **`0664`**（实测 `-rw-rw-r--`: `/tmp/d3b_watcher.sh` 821 B、`/tmp/d3b_dispatch.sh` 1702 B 同）; 对照前 8 窗 watcher（w1/w2/d1/d2/d2r2/d3r2/dr4/dr4c）均为 **`0775`（`-rwxrwxr-x`）**。机制结论不变: **无执行位 + crontab 直呼路径 ⇒ cron 每 5 分钟 permission denied 静默失败**（`loop_a_d3b_done.json` 与 `/tmp/loop_a_d3b_state` 从未生成、自清从未执行）。

### 15.4 决策 4A 下不修工件的两条已知残留

- 收据 `meta` **无 `reproduce` 字段**（实测 `meta` 键集 = `card_id / endpoint_calls / generated / name / phase / script / target_artifact_sha256 / target_payload_sha256 / version`; 严格说是「字段缺席」而非 `reproduce = null`）⇒ 复现口径以本报告 **§14** 为准（GB10 与 Windows 两条命令 + 期望镜像 sha `3e7e0568…`）; 决策 4A 下不重铸收据、不生成 v2。
- S-01 `detail.http_clients_imported = ["urllib"]` **属 stdlib 传递引入, 非本脚本使用 HTTP 客户端**: 实测裸解释器 `urllib in sys.modules = False`, 而 `import pathlib` 后为 True（`pathlib` 传递引入 `urllib.parse`）; 本脚本 import 集 = `ast / hashlib / json / re / socket / sys / datetime / pathlib`, 无任何 HTTP 客户端, 且 **S-01 的 PASS 条件只看 `socket_attempts == []`**（实测 `[]`）⇒ S-01 结论不变。注: 侧线原表述「环境噪声」按实测收紧为「`pathlib` 传递引入」, 属措辞精确化, 不改判定。

### 15.5 决策 5A 现场处置（GB10, 记账指针）

`*/5 * * * * /tmp/d3b_watcher.sh` 已摘除（前后逐字对照与取证清单见 THREADS `#D3B-CRONTAB-REMOVED-5A`）; watcher 与 dispatch 脚本**本体与权限原样保留作证据**（仍 0664）, 未补建 done 件, 未清理 /tmp 其他件; 备份 `/tmp/crontab_pre_d3b_20260907.bak` 与摘除后镜像 `/tmp/crontab_post_d3b_20260907.txt` 留存。机制修复（watcher 注册形态改 `bash /tmp/x_watcher.sh` 或创建即 `chmod +x`; 派发前置检查在 `bash -n` 之外新增**执行位实证 + 首次 tick 实证**两项）**不在本轮做**, 记入 THREADS 未决, D4 拟卡时内嵌为派发硬前置, 不新开 docs/29 A 编号。

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d3_stage_b_closeout_spotcheck.json
sha256: 25918a12b69203b53c626cdcade3c2fd7503a38e68ce8142d40a715d95d7dc93
sha256_lf: 88cb5b801275b396c4d52f2b3f970665786dc335ddb767adb555b3f2839010d8
claims:
  payload.all_pass = true
  payload.n_checks = 27
  meta.endpoint_calls = 0
  payload.zero_endpoint = true
  payload.recomputed_summary.call_counter_total = 31
  payload.recomputed_summary.canary_probes = 3
  payload.recomputed_summary.formal_calls = 28
  payload.recomputed_summary.invalid_retries = 0
  payload.recomputed_summary.ledger_lines = 62
  payload.recomputed_summary.prompt_rebuild_byte_equal = 28/28
  payload.recomputed_summary.verdict_cross_tab.J-N1.equivalent = 14
  payload.recomputed_summary.verdict_cross_tab.J-N1.meaning_changed = 7
  payload.recomputed_summary.verdict_cross_tab.J-N2.equivalent = 4
  payload.recomputed_summary.verdict_cross_tab.J-N2.meaning_changed = 3
  payload.recomputed_summary.dr4_tally.agree = 3
  payload.recomputed_summary.dr4_tally.disagree = 5
  payload.recomputed_summary.dr4_tally.unresolved_invalid_final = 0
  payload.recomputed_summary.triggers.trigger_1_jn2_ge_4of7 = true
  payload.recomputed_summary.triggers.trigger_2_jn1_ge_11of21 = true
END-SUMMARY-GUARD -->
