# 步级 checkpoint 检测器预注册 v1（在产生任何分数之前冻结，2026-09-25）

> 状态: 预注册件（Loop D）| 冻结时刻：本件提交时，仓内与 GB10 上不存在任何检测器输出
> 被冻结的输入: 语料 v1（`docs/experiments/2026-09-25_finqa_step_checkpoint_corpus_v1.md` §3 的 sha256）
> 纪律: 本件一经提交只可换版本（v2 新文件），不得原位修改；实现与结果件必须逐条引用本件条款号

## 0 为什么先冻结

先看检出数字再定检测器、容差或分母，就是把基准调成结果。故本件在测量发生前写死：
算子语义、参数解析文法、数值比较规则、百分号约定、指标定义、分层口径、分母纪律与正反例清单。
实现批若发现本件有错，必须新开 v2 并说明差异，不得在跑完之后再改本件。

## 1 输入与绑定（R1）

- 语料: GB10 `/tmp/step_ckpt_20260925/corpus_m1.jsonl`，sha256 `03cf47c3576b7c42f4fddebc31dc4b3be1ee6cb9b38a9fa8b15850e80a900d3f`，1 970 条记录（主语料）。
- 对照宇宙: `corpus_m8.jsonl`，sha256 `7f3ad6043b2bc0eceaf3ffe94859defb8435c62808db4879685d6080c384ed04`，212 条。
- 层绑定: 摘要件内 `inputs.layers_manifest_sha256`（M=1 `94379823654a6e75a925e65b367a802e29cd4016a2d85e6a949849b32a6d760b`）；运行时须重算并比对，不符即 fail-closed。
- 源绑定: `finqa/train.json` `49f237eb…`、`finqa/dev.json` `a847fb7e…`，运行时断言。
- 运行器必须安装零连接守卫，`observed_ports = []`；零模型、零 canary、零 judge。

## 2 参数解析文法（R2，穷尽实测词汇）

实测（全 10 960 步）参数形态：数值字面量 8 149、`#N` 引用 3 818、`const_*` 1 322（17 个不同 token）、
其余 339 个不同非数值串（其中 `none` 238，另有 `net sales`、`operating profit`、`12%`、`beginning balance` 等自由文本）。

| 形态 | 解析规则 | 不可解析时 |
|---|---|---|
| `^[+-]?(\d+\.?\d*|\.\d+)$` | 十进制精确值（Decimal，不用二进制浮点） | — |
| `^([+-]?(\d+\.?\d*|\.\d+))%$` | 尾数除以 100（见 R4 百分号约定） | — |
| `const_<int>` | 该整数；`const_m1` = -1（实测 20 次） | 未知 const token → 该步 UNEVALUABLE |
| `#N` | 取本例第 N 步（0 基）的 `res`，递归按本文法解析；N 越界或指向不可解析的 res → 该步 UNEVALUABLE | 同左 |
| `none` | 不猜测、不当 0、不当空 | 该步 UNEVALUABLE |
| 其他自由文本 | 不猜测、不做字符串相似度、不查表 | 该步 UNEVALUABLE |

`UNEVALUABLE` 是显式状态，必须计数并单独报告，不得当作正确、不得当作错误、不得静默丢弃。

## 3 算子语义（R3，10 族；变体位只作分层不作语义）

实测 op 名形如 `<family><variant>-<position>`，变体位取值 1（5 624）/ 2（5 202）/ 0（134）。
本件不为变体位赋予不同语义（批准范围内无官方算子文档可据；README 摘录只描述条目字段），
只按族定义语义，并把变体位作为分层维度上报，使任何变体相关的解释偏差在分层里显形而非被总量掩盖。

| 族 | 语义 | 备注 |
|---|---|---|
| `add` | a1 + a2 | 交换族 |
| `minus` | a1 - a2 | 非交换 |
| `multiply` | a1 * a2 | 交换族 |
| `divide` | a1 / a2 | 非交换；a2 = 0 → 该步 UNEVALUABLE（不产生 inf、不当 0） |
| `sum` | a1 + a2 | 实测仅 2 参数形态；若出现多于 2 参数 → UNEVALUABLE |
| `average` | (a1 + a2) / 2 | 同上 |
| `max` / `min` | max(a1,a2) / min(a1,a2) | 交换族 |
| `exp` | a1 的 a2 次幂 | 非交换；结果非有限或非实数 → UNEVALUABLE |
| `compare_larger` | a1 > a2 → `yes`；a1 < a2 → `no`；相等 → UNEVALUABLE（不预注册平局判定） | 布尔族 |
| 未知族 | UNEVALUABLE | 不得回退到按加/减猜测 |

## 4 数值比较与百分号约定（R4）

- 比较用 Decimal 精确算术；两侧均可精确表示时要求相等，否则用相对容差 `1e-9`（一次写死，跑后不调）。
- 百分号：`res` 带 `%` 时，其尾数与重算值的尾数比较（`"1%"` 比 1，不比 0.01）；
  当该 `res` 作为 `#N` 被下游消费时，取尾数除以 100（实测样例 `divide(100,100)` 得 `"1%"`，
  下游 `divide(3.8,#0)` 得 380，与 3.8 / 0.01 一致；此为本件唯一依据，作为解释假设显式记录）。
- 该约定是重建的解释，不是官方文档；其保真度由 R5 的 `interpretation_fidelity` 度量并如实上报，
  保真度低本身是结论，不得据此换约定重跑（换约定等于调参救结果）。
- `res` 为 `yes`/`no` 时按布尔比较；`res` 属实测 7 个畸形值（空串 2、`( 0.60 )`、`ye`、`312.9 %`、`2.3:1`、`n0`）
  时该步 UNEVALUABLE，不做修复性解析。

## 5 指标定义（R5，分母写死）

对每条语料记录，先跑 clean（`steps_clean`），再跑 mutant（`apply_fault(steps_clean, fault)`，
必须复用适配器的 `apply_fault`，不得另行实现变异）。逐例分类：

1. `clean_unfaithful`：clean 运行中任一步 UNEVALUABLE，或任一步重算值与其 gold `res` 不符。
2. `clean_faithful`：clean 运行全部步可解析且逐步相符。
3. 指标只在 `clean_faithful` 子集上定义（其余进 `clean_unfaithful` 桶并报告占比）：
   - `interpretation_fidelity` = clean_faithful / (clean_faithful + clean_unfaithful)；
   - `fault_detection_rate` = mutant 运行中被判不一致步集非空的例数 / clean_faithful 例数；
   - `exact_localization_rate` = 被判不一致步集恰等于 {注入 index} 的例数 / 被检出例数；
   - `inclusive_localization_rate` = 注入 index 属于被判不一致步集的例数 / 被检出例数；
   - `clean_false_flag_rate` = clean 运行中被判不一致的例数 / clean_faithful 例数（按定义应为 0，作负对照）。
4. 两个 localization 指标同时预注册、同时上报，不得只报表现好的那个。
5. 任何指标不得在排除 `clean_unfaithful` 或 UNEVALUABLE 后当作全量结论陈述；引用时必须带分母。

## 6 分层口径（R6）

按以下维度各自分层上报，稀有层单列、不并入 other：op 族（10 族全列）、变体位（0/1/2）、
每例步数（2..6）、故障族（res_scale / arg_swap）、partition（proposal_train.train / dev）、
`res` 形态（num / pct / bool / other）。M=8 对照宇宙单独一份，且须声明其只有 5 个 op 族在层。

## 7 实现必须带的正反例（R7，缺一项即验收不过）

正例：clean 且忠实的 2 步 divide 例判为 clean_faithful；`const_m1` 参与运算可解析；`#N` 链可解析；
pct 链按 R4 可解析；注入 res_scale 的忠实例被检出且 exact localization 命中；
注入 arg_swap 于 minus 的忠实例被检出。
负例：`arg1 = none` 时该步 UNEVALUABLE 且不计入正确；divide 除数为 0 时 UNEVALUABLE；
compare_larger 两值相等时 UNEVALUABLE；未知 op 族 UNEVALUABLE；
clean 忠实例不得被误报（clean_false_flag_rate = 0）；
语料 sha 或层摘要被篡改时 fail-closed 且 exit 非 0；`--commit` 非 40-hex 时不写文件。
确定性：双跑摘要与逐例结果均须逐字节相同；产物无墙钟字段。

## 8 本件不授权的事（R8）

- 不授权任何模型调用、任何端点访问、任何下载（含 FinQA 官方算子代码：超出 D-C 批准范围，需新申报）。
- 不授权把结果称为对冻结 Stage E 口径的复现或替代；两者是不同测量对象。
- 不授权由本检测器结果反推任何动作标签、可学性、蒸馏或 RQ2 结论。
- 不授权在保真度不理想时更换 R4 约定、R3 语义或 R5 分母后重跑并只报新结果；
  若确需变更，必须新开 v2、说明动因、并同时保留 v1 结果。

## 9 交付顺序（R9）

1. 本件提交（此刻无任何检测器输出）；
2. 实现 `research/finqa_step_checkpoint_scorer.py` 与 R7 全部正反例单测，GB10 跑通；
3. 在主语料与对照宇宙上各跑一次，产出摘要件（只含计数、比率、分层与哈希）；
4. 结果件逐条引用本件条款号，并如实报告 `interpretation_fidelity`（无论高低）；
5. 独立 Loop C 审计（生成者不自验）后方可被论文引用；引用前一律 `paper_result = false`。
