---
status: 阶段 B 交付（端点窗, 仅 :8004）
date: 2026-09-06
card: docs/experiments/2026-09-01_d3_matched_specificity_card.md
card_id: TASK-20260901-D3
artifact: logs/graph/eval/d3_matched_fpr_stage_b.json
ledger: logs/graph/eval/d3_stage_b_call_ledger.jsonl
script: research/paper_d3_stage_b_judge.py
phase: B_endpoint_window_8004
endpoint_calls: 31
---

# D3 阶段 B：judge 重打分窗（28 例判定 + 8 行 DR4 对照）

> 派发: Loop D 2026-09-06 13:5x · **仅阶段 B**（阶段 A 已交付 `51cbed9`, 本窗零重跑）
> 测量契约: 卡加编 3 C3-1..C3-6（零现场定义空间）; 判据文本零改动
> 窗口: 2026-09-06 14:4x（白天错峰端点窗）; `:8004` 唯一端口, `:8006`/`:8008` 零触碰
> **⚠ C3-3 两条方向性分歧触发同时命中 → 本窗按上报纪律即时上报 Loop D, 不等 autopsy 排期（见 §0/§7）**

## 0 一页结论（只收集 + 确定性聚合; 结论判定归 Loop D）

冻结清单 28 调用（J-N1 21 + J-N2 7, J-N3 零调用）全部 `status=ok`, 零 invalid、零重试、零截断。
判定分布如下, 均为**描述性统计**, 不构成对旧判据的改动:

| 子组 | 含义 | judge equivalent | judge meaning_changed |
|---|---|---|---|
| **J-N1 静默吸收 15** | D1 HI ∧ `absorption_silent` | **14** | 1 |
| **J-N1 阈值稀释 6** | D3 a3 `single_drop10 == 0.0` | 0 | **6** |
| J-N1 合计 21 | 零信号有害注入语义危害性复判 | 14（66.7%） | **7（33.3%）** |
| **J-N2 等价 7** | 现行 E 集 = DR4 diff 7 例 E→H | **4（57.1%）** | 3（42.9%） |

**四条读数**:

1. **J-N1 内部按机制二分彻底翻转**: 阈值稀释 6/6 判为有害（占比→绝对额类, 如
   `% of associated net revenues → 营业总收入`）; 静默吸收 14/15 判为等价。且静默子组
   14 例的**形态高度同质**——全部是纯字符级扰动（`equty`/`capitai`/`divdend`/`operat1ng`/
   `liabilitie5`）, judge 一致给「拼写错误不影响语义指向」。
   ⇒ 零信号集内**真正语义有害的疑似只有 1 例**（`567a03c7#1` `Exercise Date →
   Exercise date 2021-期末日期`, 属追加而非扰动）。
2. **触发 ① 命中**: J-N2 有效判定 4/7 为 equivalent ≥ 4 ⇒ 与 DR4 oracle（7 例全 HARMFUL）方向相反。
   逐例看分歧集中在**缩写/单位类**（`amort`、`dividend`、`US$→US [1]`）,
   一致集中在**删除限定语/货币符号类**（`£m → m【】` ×2、`Free cash flow (pre-spectrum) → cashflow`）。
   ⇒ judge 与 DR4 oracle 的分界实际落在「缩写是否算改口径」这一判定标准歧义上, 非随机噪声。
3. **触发 ② 命中**: J-N1 有效判定 14/21 为 equivalent ≥ 11 ⇒ 动摇有害集选取与 D4 oracle 的
   「非等价即有害」隐含假设。
4. **8 行 DR4 对照 = 3 agree / 5 disagree**（零 unresolved）; 唯一 H→E 例
   `3789d7da#1` 按加编 2 澄清以确定性证据入账（`visible=true / absorbed=false / match_tier=0`,
   零 judge 调用）, 与 DR4 oracle=E 方向不一致, 如实记 disagree。

**给 Loop D 的判断输入（本窗不裁定）**: 三条证据线（现行类型级 E / DR4 实例级 oracle / 本窗 judge）
在 8 例 diff 上互不完全一致 ⇒ 缺陷类型标签与实例级危害性之间存在**口径缺口**; 纯字符级拼写扰动
是否应计入「有害注入」集, 需要显式裁定（影响 D4 oracle 与 S-2 的 111 检出分母）。

## 1 前置检查与契约遵循（G-1 口径, 派发内记账）

| 项 | 结果 | 证据级别 |
|---|---|---|
| 端点健康 `GET :8004/v1/health` | `{"status":"ok"}` | 独立请求（不计数） |
| 模型断言（零现场换模型） | `/v1/models` 实况 = `Qwen3.6-35B-A3B-Q4_K_M.gguf` 一致 | 独立请求（不计数） |
| C3-1 运行时硬断言 A1–A6 | **6/6 PASS** | 独立重算（清单/并集/不相交/逐字锚点/H→E 排除/uid8 1:1） |
| C3-2 防泄漏白黑名单 | `holds=true`, `hits=[]`（28 prompt 骨架全扫） | 独立扫描 |
| C3-2 prompt 契约自证 | 占位符词表精确 = 5 白名单值; 28 prompt_sha 全唯一; 绑定零违规 | 逐例游标重建（非抽样） |
| C3-2 渲染规则 | prompt 1236–2022 B, `table_truncated` 全 false（零表 >40 行） | 字段存值 |
| 冻结输入只读 | 6 件 sha 前后相等（含阶段 A 工件） | 独立重算哈希 |
| 卡 sha 钉死 | `22eaa5117b84…` = `CARD_SHA_EXPECT` | 独立重算哈希 |

前置 `--stage preflight` 已在全零调用下跑通（A1–A6 + leak_guard + 契约自证全绿）后开正式窗。

## 2 canary 与调用计数（C3-5 自证）

- canary: 冻结 prompt, 1 次推理探针, `parsed={"ok": true}`, 199 ms, 计数 31 号位。
- **计数器 = 31 ≤ 200 硬门**（预期单跑上界 57）。
- 分解: canary 探针 3 + 正式 call 记录 28 + invalid 重试 **0** = 31。
- **恒等式 `counter_total == canary_probes + call_lines` = true**;
  `ledger_reserve_lines(31) == counter_total(31)` = true ⇒ 零计数外推理请求。
- 账本 `d3_stage_b_call_ledger.jsonl` **append-only 共 62 行**（reserve 31 / call 28 / canary 3）,
  两次开窗的探针痕迹完整保留, 未清空、未重写。

**开窗次数如实记账**: 本工件经 **3 次开窗调用**收口 = 首次正式窗 29 次（canary 1 + 正式 28）
+ 装配缺陷修复后复跑 2 次 canary 探针。28 例正式判定**只发过一次**（payload 字节相同 ⇒
判定不可变, 后续由账本复用, `resumed_cases = 28`）。

## 3 执行期缺陷与修复（两处, 均非判据改动）

1. **占位符正则漏数字**（首跑前修掉）: `\{([a-z_]+)\}` 无法匹配 `{col_1based}` →
   改 `\{([a-z_][a-z_0-9]*)\}`; 契约自证的 `vocabulary_exact` 门即为此而设。
2. **`Ledger._append` 内存镜像不同步**（收口时命中 GG10）: 只写盘不更新 `self.records`,
   导致 `ledger_rows` 快照漏计本次调用写的行 → 计数恒等式算成 30 ≠ 1+28 而 **GG10 FAIL、
   `all_pass=false`, 工件未收口**。修复 = `_append` 同步 append 内存镜像（根因修复, 非放宽门）;
   复跑后 31 = 3+28 成立。
   ⇒ 该门起了它该起的作用: 第一次产物确实不自洽, 被拦住了。

## 4 J-N1 逐例（21 例）

| key | original → injected | verdict | conf |
|---|---|---|---|
| `1fe3e1d6#2` | Number of equity shares → Number of equty shares | equivalent | high |
| `21c316d6#2` | Dividend per Share → divdend per Share | equivalent | high |
| `3c609073#1` | …capitalized dry-docking → …capitaiized… | equivalent | high |
| `3c609073#3` | …operating equipment → …operat1ng… | equivalent | high |
| `44c7c9ef#1` | Operating Leases → operat1ng Leases | equivalent | high |
| **`567a03c7#1`** | Exercise Date → **Exercise date 2021-期末日期** | **meaning_changed** | high |
| `5fe2c49e#1` | Operating Leases → operat1ng Leases | equivalent | high |
| `5fe2c49e#2` | Capital Leases → capitai Leases | equivalent | high |
| `68b8d514#1` | Grant Date → Grant date 2019-报表明细日期 | equivalent | high |
| `6a5e5192#0` | Equity-settled → equty-settled | equivalent | high |
| `6f9a0eb1#0` | Capital expenditures → capitai expenditures | equivalent | high |
| `c0f66238#3` | …equity compensation plans… → …equty… | equivalent | high |
| `d2bba753#0` | Capital stock → capitai stock | equivalent | high |
| `d7d65228#3` | Cash dividend per share → Cash divdend per share | equivalent | high |
| `e11338f6#0` | …Financial Liabilities → …liabilitie5 | equivalent | high |
| `24ff90f9#2` | % of associated net revenues → turnover | meaning_changed | high |
| `24ff90f9#4` | % of associated net revenues → 营业总收入 | meaning_changed | high |
| `32cfcadb#2` | As a % of Segment Revenue (1) → 营收 | meaning_changed | high |
| `32cfcadb#4` | As a % of Segment Revenue (1) → 营业总收入 | meaning_changed | high |
| `97176853#2` | As a % of Revenue (1) → 营业总收入 | meaning_changed | high |
| `97176853#4` | As a % of Revenue (1) → turnover | meaning_changed | high |

注: 全 21 例 confidence = high; 静默子组 14/15 的 equivalent 判定共用「拼写错误不改语义」这一条理由,
`567a03c7#1` 与 `68b8d514#1` 同为「日期列追加文字」形态却判定相反（m_c / eq）, 属边界样本。

## 5 J-N2 逐例（7 例, validity audit）

| key | original → injected | verdict | vs DR4 oracle |
|---|---|---|---|
| `50e78448#2` | US$ → US [1] | equivalent | **disagree**（oracle HARMFUL） |
| `54c494f7#2` | Accumulated Amortization → amort | equivalent | **disagree** |
| `5e60c056#0` | £m → m【】 | meaning_changed | agree |
| `73a817fc#1` | Dividends Paid(1) → dividend | equivalent | **disagree** |
| `b5aae4e9#0` | £m → m【】 | meaning_changed | agree |
| `e67f7bf2#4` | Free cash flow (pre-spectrum) → cashflow | meaning_changed | agree |
| `e9730ea3#2` | Accumulated Amortization → amort | equivalent | **disagree** |

同形对（`£m → m【】` 与 `amort` 各出现两次）判定**自洽一致**——同输入同输出, 佐证 temp=0 下
judge 稳定; 分歧不是逐例随机, 而是**按扰动族**成块出现。

## 6 8 行 DR4 对照表（冻结格式）

| key | direction | current | dr4_oracle | 证据 | agreement |
|---|---|---|---|---|---|
| `3789d7da#1` | H→E | H | E | det: visible=T / absorbed=F / tier=0 | disagree |
| `50e78448#2` | E→H | E | HARMFUL | judge: equivalent(high) | disagree |
| `54c494f7#2` | E→H | E | HARMFUL | judge: equivalent(high) | disagree |
| `5e60c056#0` | E→H | E | HARMFUL | judge: meaning_changed(high) | agree |
| `73a817fc#1` | E→H | E | HARMFUL | judge: equivalent(high) | disagree |
| `b5aae4e9#0` | E→H | E | HARMFUL | judge: meaning_changed(high) | agree |
| `e67f7bf2#4` | E→H | E | HARMFUL | judge: meaning_changed(high) | agree |
| `e9730ea3#2` | E→H | E | HARMFUL | judge: equivalent(high) | disagree |

`3789d7da#1`（Revenues→sales, alias_variant）: 确定性通道判为已检出而 oracle 判等价 ⇒ 方向不一致,
按加编 2 澄清**零 judge 调用**, 以确定性证据列呈现。

## 7 触发上报（C3-3 上报纪律, 非判据）

- **触发 ① 命中**: J-N2 equivalent 4/7 ≥ 4/7（与 DR4 oracle 方向相反）。
- **触发 ② 命中**: J-N1 equivalent 14/21 ≥ 11/21（零信号集多数实为无害 ⇒ 动摇有害集选取与 D4 oracle）。

两条均已于本窗收口汇报中即时上报 Loop D, 不等 autopsy 排期。**本窗不据此改任何判据、不重新归类
任何注入**（收集与判定分离, C3-6）。

## 8 成本与口径（S-4 参考, 仅本窗实测）

- tokens: prompt 18 136 / completion 1 011（28 有效调用合计）。
- latency: min 796 / median 1 072 / max 1 301 ms（canary 199 ms）。
  latency 属次要指标（受负载/缓存污染, S-4）, 只作窗口健康旁证。
- 口径注记（承 C3-4）: 本窗 judge = `:8004` Qwen3.6-35B-A3B temp=0, 与历史四维 judge 基线
  （4.94–5.0, 含 `:8006` xhigh 档）**不同口径, 不作跨比较**; 本窗 `:8006` 零调用。

## 9 红线自查

| 红线 | 结果 |
|---|---|
| 阶段 A 零重跑 | ✅ 本窗只执行阶段 A 冻结的 28 调用需求清单; 阶段 A 工件只读（sha 前后等） |
| 仅 `:8004` | ✅ `ports_observed=[8004]`, `endpoint_violations=[]`（socket 层护栏） |
| `:8006` 零触碰 | ✅ 五条件条款未启用; 8006/8008 不在 ports |
| 预算 ≤200 硬门 | ✅ 31, 计数器 + JSONL 实时落账, 恒等式自证 |
| canary 异常即停 | ✅ 未触发（3 次探针均 `ok`） |
| J-N3 零调用不夹带 | ✅ `jn3_calls=0` |
| 判据零改动 | ✅ E-1..E-4 / S-1..S-8 / R1-R4 / D1-D2 零改动; 本窗只收集 + 确定性聚合 |
| 甲方标识零进入 | ✅ `client_token_hits=[]` / `id_token_hits=[]`（92 676 字符扫描） |
| 防泄漏 | ✅ 28 prompt 白名单骨架零命中禁用词族 |
| TAT-DQA 冻结线 | ✅ 零触碰（本窗只读注入语料冻结工件） |
| git 纪律 | ✅ 逐路径 add; 禁 `-A` / 禁 `--amend` |
| 对外零发送 | ✅ `outbound_sent=false` |

## 10 复现

```bash
venv/bin/python research/paper_d3_stage_b_judge.py --stage preflight   # 零调用前置自证
venv/bin/python research/paper_d3_stage_b_judge.py --stage window      # 开窗（账本复用则只发 canary）
venv/bin/python scripts/graph/hooks/summary_recompute_guard.py check docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md
```

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d3_matched_fpr_stage_b.json
sha256: e0cec25e39d801bae161f9fd954a30b93b16daa9ccc7fbe52f432b918bba3797
claims:
  gates.all_pass = true
  meta.call_counter_total = 31
  payload.call_counter_total = 31
  payload.call_counter_breakdown.canary_probes_all_invocations = 3
  payload.call_counter_breakdown.invalid_retries = 0
  payload.call_counter_breakdown.resumed_cases_reusing_append_only_ledger = 28
  payload.call_counter_breakdown.new_inference_calls_this_invocation = 1
  payload.call_counter_breakdown.identity_counter_eq_canary_plus_call_records = true
  payload.call_counter_breakdown.ledger_lines_total = 62
  payload.measurement_contract.jn3_calls = 0
  payload.jn1_confirmation_rate.numerator = 7
  payload.jn1_confirmation_rate.valid_denominator = 21
  payload.jn2_equivalent_rate_supports_current_E.numerator = 4
  payload.jn2_meaning_changed_rate_supports_dr4_oracle_H.numerator = 3
  payload.dr4_agreement_tally.agree = 3
  payload.dr4_agreement_tally.disagree = 5
  payload.dr4_agreement_tally.unresolved_invalid_final = 0
  payload.window_abort = None
  payload.leak_guard.hits = []
  payload.redline_self_check.ports_observed = [8004]
  payload.redline_self_check.endpoint_8006_zero_touch = true
  payload.redline_self_check.outbound_sent = false
END-SUMMARY-GUARD -->
