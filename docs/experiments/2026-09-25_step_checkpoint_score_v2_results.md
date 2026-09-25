# 步级 checkpoint 检测器 v2 实测结果 —— 预注册停止条件已触发，本线停止（2026-09-25）

> 状态: 结果件（Loop D）| 规格: 预注册 v2 sha256 `6ee1d06b2e62ba1e0a70c60ac1226c44e7adc4636a3d13db6cbd95b2a5f0a986`
> 运行 head = `aa0adaf3029b7e9a7e7eb4441a803c7ec6a06e79` | 零模型、零端点、零下载 | `observed_ports = []` | 双跑 `cmp` 逐字节相同
> v1 结果件 sha256 `dd753b2226929f23e310e57080cdbf0cd4b2d4dcee0740088193eeabff88c335`、v1 分数件 sha256 `40e75566bce101baffe8c442c16efbf7556c7624af945bbcaf8d8c53e34e20e9` 均已写入产物 `v1_anchors`
> `paper_result = false`：未经独立 Loop C 审计前不得被论文引用

## 1 头条：V2-3 的停止条件已触发

预注册 v2 事先写死：「若 v2 在两种读法下的 pct 形态保真度均仍低于 0.5，则结论固定为
『FinQA 步级 res 的百分号与变体约定在 D-C 批准范围内无法由官方文档确定』，本线停止；
不得开 v3 继续试约定。」

实测（M=1 主语料，pct 形态共 1 478 步）：

| 读法 | pct 形态 match | pct 保真度 | 是否 ≥ 0.5 |
|---|---|---|---|
| `mantissa_direct`（v1 读法） | 44 / 1 478 | **0.0298** | 否 |
| `mantissa_scaled`（v2 新增） | 330 / 1 478 | **0.2233** | 否 |

两读法均远低于 0.5 ⇒ **停止条件触发，步级重执行线停止**。此后唯一合法动作是二选一：
(1) 新申报 FinQA 官方算子代码或文档（超出 D-C 批准范围，需用户批准）；
(2) 放弃该来源的步级重执行路线并如实记录。本件不选，交用户裁定。
按 V2-3，**不得**通过改分母、改容差、改族语义、改故障定义或再换一个百分号读法来提升保真度。

## 2 两读法完整并列上报（V2-1 要求不得只报其一）

M=1 主语料（1 970 条记录）：

| 指标 | `mantissa_direct` | 分母 | `mantissa_scaled` | 分母 |
|---|---|---|---|---|
| `interpretation_fidelity` | 0.16345178 | 1 970 | 0.23705584 | 1 970 |
| `fault_detection_rate` | 0.99068323 | 322 | 0.99357602 | 467 |
| `exact_localization_rate` | 0.47335423 | 319 | 0.52586207 | 464 |
| `inclusive_localization_rate` | 1.0 | 319 | 1.0 | 464 |
| `root_cause_localization_rate` | 1.0 | 319 | 1.0 | 464 |
| `clean_false_flag_rate` | 0.0 | 322 | 0.0 | 467 |

步级：direct 4 583 = match 2 623 + mismatch 1 947 + unevaluable 13；
scaled 4 583 = match 2 909 + mismatch 1 661 + unevaluable 13。

M=8 对照宇宙（212 条）：fidelity 0.15566038（分母 212）/ 0.21698113；detection 1.0 / 1.0（分母 33 / 46）；
exact 0.45454545 / 0.47826087；inclusive 1.0 / 1.0；root_cause 1.0 / 1.0；false_flag 0.0 / 0.0；
pct 形态 match 8/160 与 39/160（保真度 0.05 与 0.2438，同样双双低于 0.5，停止条件在对照宇宙上同样成立）。

## 3 三项交叉验证（说明数字可信，而非说明结论成立）

1. **读法只作用于 pct 层，num 层逐字不变**：num 形态在两读法下同为 match 2 571 / mismatch 518 /
   unevaluable 7（保真度 0.8304），与单测 `test_num_form_verdicts_are_reading_independent` 的构造性断言一致。
   两读法的差异 100% 落在 pct 层（44 → 330）与 divide 族（173 → 382），无溢出。
2. **v1 复现守卫通过**：运行时逐项比对 `mantissa_direct` 与 v1 分数件的 counts / metrics /
   metric_denominators / step_strata，全部相等（否则以 `v1_reproduction_mismatch` fail-closed）。
   ⇒ v2 是 v1 的严格超集，没有借「升版本」悄悄重定义 v1 语义；两份已发布结果可比。
3. **负对照成立**：两读法、两宇宙下 `clean_false_flag_rate` 均为 0.0，忠实例零误报。

## 4 root_cause 指标为 1.0 的机制，以及为什么它不构成好消息

`root_cause_localization_rate`（min(flagged) == 注入 index）在两读法、两宇宙下均为 1.0，
而 `exact` 仅 0.47-0.53。机制在 v1 结果件 §3 已定：`res_scale` 改的是 `res`，下游 `#N` 正从该 `res` 取值，
故注入点下游连带 mismatch（v2 scaled 读法下 res_scale 的 exact = 147/367，而 arg_swap = 97/97）。
`root_cause` 之所以为 1.0，是因为注入点必然是最早被改变的步 —— 这在本故障模型下近乎**构造性成立**，
因此它是一个健全性检查，**不是**一个有信息量的性能结果。任何把它当作「定位能力已解决」的引用都是错的。

## 5 未被解释、且刻意不作归因的残余

num 形态步仍有 518 / 3 096（16.96%）不一致，且该数字在两读法下相同 ⇒ 与百分号约定无关。
可能来源包括算子变体约定、舍入口径或 `#N` 语义的其他分支，但**本件不归因**：
归因需要 FinQA 官方算子语义，而 V2-3 已禁止本线继续追该方向（除非用户批准新申报）。
如实记录为未解释残余，不猜测、不填充、不用总量掩盖。

## 6 本线的净产出（负结果也是产出）

- 一套在检测器存在之前就已冻结的步级故障注入语料（1 970 条，sha `03cf47c3…`，双跑逐字节相同）。
- 一个拒绝在没有预注册规格时发布任何指标的检测器，产物内嵌规格 sha256 与 v1 锚点。
- 一个**真的触发**的停止条件：它没有被放宽、没有被换口径重跑，v1 结果原样保留并被判为可比。
- 一个明确的边界结论：在 D-C 批准范围内，FinQA 步级 res 的百分号与变体约定无法由官方文档确定，
  故步级重执行在该来源上不可识别（not identifiable from public metadata alone）。

## 7 不得主张

- 不得把 detection 0.99068 / 0.99358 或 localization 1.0 说成「步级 checkpoint 检测在 FinQA 上成立」：
  分母是 clean_faithful（322 / 467，占 1 970 的 16.3% / 23.7%），且检测器是单一确定性重执行规则、
  故障是本工具自建的，不是模型能力、不是蒸馏收益、不是 RQ2 证据。
- 不得称本件复现、重算或替代冻结 Stage E 口径（表头注入族判别 vs 推理步检查点，不同测量对象）。
- 不得据本件反推任何动作标签、可学性或训练决策。
- 不得只引用 `mantissa_scaled`（较高的一路）而略去 `mantissa_direct`；两路必须同时出现。

## 8 产物与取证

`score_v2_m1.json` sha256 `9029caa4de508153f8beec4111cb0df82a973ac4071d6c32bf1b398d907031b3`；
`score_v2_m8.json` sha256 `f40c4ab9969104b311af8cb5bd35aeb7c4e4cfbc165be44dd88851dd6ea62ada`
（均在 GB10 `/tmp/step_ckpt_20260925/`，仓外）。输入绑定：corpus `03cf47c3…` / `7f3ad604…`、
layers_manifest `94379823…` / `9fc84f2b…`、预注册 v2 `6ee1d06b…`、v1 结果件 `dd753b22…`、v1 分数件 `40e75566…`。

## 9 红线自查

零模型、零端点、零下载；数据体与产物不入 Git（仓内只记计数、比率与哈希）；未改冻结判据 / 冻结 hash /
冻结 Stage E 口径与数字；未改预注册 v1 与 v2（本件只报结果）；未改协议、注册表、合同与守卫逻辑；
未覆盖 production 脏件；未重启 daemon 与 :5050；逐路径 add，无 `--amend`、无 `--no-verify`；
不外发、不上 arXiv、不公开代码。

## 10 引用门状态变更（append-only，2026-09-25；不原位改上文）

本件头部原写「`paper_result = false`：未经独立 Loop C 审计前不得被论文引用」。该前置条件现已满足：
独立链路审计（qwen3.8-max，packet 178 438 B，sha256 `826905f8…`，审计基线 head `e357e11`）判定
**PASS_WITH_NOTES，无 HIGH 发现**，并显式给出引用门判定「小论文 §6 对 0.0298 / 0.2233 的引用：
可以保留（是）」，理由含数字与 artifact 链一致（0.0298 = 44/1478、0.2233 = 330/1478，审计人自行
算术复核通过）、所引为边界量而非被禁的性能量、两读法同时出现且未取优、untested 与 failed 区分正确。
审计件：`docs/experiments/2026-09-25_loopc_audit_step_checkpoint_chain.md`。

据此本件所载数字的引用门**开启**，但范围严格限于审计人核可的用法：只可作边界量引用，必须带分母，
两读法必须同时出现；detection 0.99068 / 0.99358 与 localization 1.0 仍在 §7 禁令之内，不得引用。
`paper_result` 的语义不变：本件不是论文结果，是边界测量记录。审计提出的 F7 更正同时登记：
§3.3 所称「负对照成立」应读作**定义性核对（analytic identity）**而非经验负对照，
经验负对照的载体是测试断言（`test_clean_faithful_and_no_false_flag_r7` 等）。