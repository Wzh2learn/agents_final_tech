# 步级 checkpoint 检测器 v1 实测结果（严格按预注册 v1 执行，2026-09-25）

> 状态: 结果件（Loop D）| 规格: 预注册 v1，sha256 `1f579c6cbaeb74a952df7fb777e5d3b80e7f6ddcc26d99fb57a0a7c6f76a5b84`（本件不改规格一字）
> 运行 head = `1afc8c3ffcb45bbc48828c20a9df8161042f5ba9` | 零模型、零端点、零下载 | `observed_ports = []` | 双跑 `cmp` 逐字节相同
> `paper_result = false`：未经独立 Loop C 审计前不得被论文引用

## 1 头条数字（每项都带分母，R5.5）

| 指标 | M=1 主语料 | 分母 | M=8 对照 | 分母 |
|---|---|---|---|---|
| `interpretation_fidelity` | 0.16345178 | 1 970 | 0.15566038 | 212 |
| `fault_detection_rate` | 0.99068323 | **322** | 1.0 | **33** |
| `exact_localization_rate` | 0.47335423 | 319 | 0.45454545 | 33 |
| `inclusive_localization_rate` | 1.0 | 319 | 1.0 | 33 |
| `clean_false_flag_rate` | 0.0 | 322 | 0.0 | 33 |

关键限定：detection 与 localization 的分母是 `clean_faithful` = 322 / 1 970（16.3%），**不是** 1 970。
脱离该分母的任何引用都不成立。步级对账：4 583 步 = match 2 623 + mismatch 1 947 + unevaluable 13。
负对照成立：忠实例零误报。M=8 步级：498 = 278 + 220 + 0。

## 2 保真度低的原因已被分层定位（本件的主要产出）

- `res` 形态：num 3 096 步 → match 2 571（83.0%）/ mismatch 518 / unevaluable 7；
  **pct 1 478 步 → match 44（3.0%）/ mismatch 1 429** / unevaluable 5；bool 8 → match 8；other 1 → unevaluable 1。
- op 族：**divide 1 812 → match 173（9.5%）/ mismatch 1 638**；minus 1 463 → 1 299（88.8%）；
  add 961 → 879（91.5%）；multiply 321 → 262（81.6%）；exp 4 → mismatch 4；compare_larger 8 → match 8；
  sum 5 → match 2 / unevaluable 3；average 5、max 2、min 2 → **全部 unevaluable**。
- 变体位：0 → 86 步（match 80 / mismatch 6）；1 → 2 280（match 1 297 / mismatch 975，42.8%）；
  2 → 2 217（match 1 246 / mismatch 966，43.6%）。

三条结论：

1. 不忠实几乎全部集中在「pct 形态的 res」与「divide 族」，不是全局语义失败
   （num 形态 83.0% 忠实，minus / add 88-91% 忠实）。
2. 变体位——即 R3 刻意不语义化、只作分层的那一位——在 1 与 2 上的 mismatch 比例几乎相同
   （42.8% vs 43.6%），故**变体位不是解释变量**；R4 的百分号约定才是。这正好验证了 R3
   「把变体位作为分层维度上报，使解释偏差显形而非被总量掩盖」的设计意图。
3. average / max / min 三族全部 9 步均为 UNEVALUABLE，因为其实参含自由文本或 `none`（R2 不猜测）。
   稀有族的可测性受参数形态限制，如实报告，不用总量掩盖。

## 3 exact 与 inclusive 的差距有确定机制，不是噪声

- 故障族：`arg_swap` → faithful 34 / detected 31 / **exact 31** / inclusive 31（exact = 100%）；
  `res_scale` → faithful 288 / detected 288 / **exact 120** / inclusive 288（exact = 41.7%）。
- 步数（exact / detected）：2 步 118/217、3 步 28/75、4 步 3/15、5 步 2/12、6 步 faithful 0。

机制：`res_scale` 改的是某步的 `res`，而下游步的 `#N` 正是从该 `res` 取值（R2），于是注入点下游
每一步都连带 mismatch，flagged 集合必然大于 {注入点} ⇒ exact 失败而 inclusive 成功；
`arg_swap` 只改实参不改任何 `res`，下游取值不变，flagged 恰为 {注入点} ⇒ exact = 100%。
步数越深层数越多、exact 越低，与观测单调一致。

⇒ 这不是检测器缺陷，而是 `exact` 这一指标在存在 `#N` 传播时的**定义**问题；处置见预注册 v2。

## 4 产物与取证

- `score_m1.json` sha256 `40e75566bce101baffe8c442c16efbf7556c7624af945bbcaf8d8c53e34e20e9`；
  `score_m8.json` sha256 `7c70cd148b45c0944b5d46978d79f412e378cbe1e579a0c98dd7b270923dd60a`
  （均在 GB10 `/tmp/step_ckpt_20260925/`，仓外）。
- 输入绑定：corpus_m1 `03cf47c3…`（1 970 条）、corpus_m8 `7f3ad604…`（212 条）、
  layers_manifest `94379823…` / `9fc84f2b…`；预注册件 sha256 已写入产物 `prereg` 块，
  故结果无法与产生它的规格脱钩。
- 确定性：`score_m1.json` 与 `score_m1_rerun.json` 经 `cmp` 逐字节相同。

## 5 不得主张

- 不得把 0.99 / 1.0 说成「步级 checkpoint 检测已解决」：分母是 322，且这是单一确定性重执行检测器
  在自建注入上的表现，不是模型能力、不是蒸馏收益、不是 RQ2 证据。
- 不得称本件复现、重算或替代冻结 Stage E 口径（表头注入族判别 vs 推理步检查点，不同测量对象）。
- 不得据本件反推任何动作标签、可学性或训练决策。
- v1 的 0.1635 保真度不得被替换、淡化或隐藏；v2 必须同时保留 v1 全部结果（R8）。

## 6 红线自查

零模型、零端点、零下载；数据体与产物不入 Git（仓内只记计数、比率与哈希）；未改冻结判据 / 冻结 hash /
冻结 Stage E 口径与数字；未改预注册 v1；未改协议、注册表、合同与守卫逻辑；未覆盖 production 脏件；
未重启 daemon 与 :5050；逐路径 add，无 `--amend`、无 `--no-verify`；不外发、不上 arXiv、不公开代码。
