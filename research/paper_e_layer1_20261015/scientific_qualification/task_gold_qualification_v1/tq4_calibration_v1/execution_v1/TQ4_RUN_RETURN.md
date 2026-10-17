# TQ4_RUN_RETURN

> run_id: `20261016T082849Z_430d927a`｜panel: `TQ-4`｜状态: `COMPLETED`（stop_reason=null）
> 授权: `run_card_v2/OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md`（新授权；S2 范围）
> 执行: GB10 Qwen3.6-35B-A3B-Q4_K_M.gguf @127.0.0.1:8004；Loop D（AI）；零停机、零内容性重试
> 悬挂声明: 无 confirmatory claim；Part 1 与 Part 2 分开记账；`scientific_gold_validity = NOT_ESTABLISHED`

## 1. 预算与完整性

- 生成请求: 36/36 全部成功（12=Part1 actor4+B4+C4；24=Part2 B12+C12）；尝试 36/40；基础设施重试 0/4。
- token: 结算 40,205（上限 400,000）；aux ops 72（apply-template/tokenize 各 36）；单并发，≤120s/请求。
- 时间: 首请求 2026-10-16 16:28:49 北京（窗口内）；末响应 16:32:16；总时长约 3 分 27 秒（≤90 分钟）。
- pin: 材料 49 项运行前后均通过（PIN_CHECK_BEFORE/AFTER）；模型身份一致（MODEL_PIN.identity_ok=true）。
- 镜像: 84 文件双端逐一哈希核对 0 失配；REQUESTS 账本双份（per-run + chain master mirror）。

## 2. Part 1（旧池新增任务的受控扰动部分；4 输入）

| task | actor answer | 评分(v2.1) | 机械合法性 | B | C |
|---|---|---|---|---|---|
| N1 | "1.5%" | MATCH | legal | **alarm** | **alarm** |
| N2 | "$22,448" | MATCH | legal | accept | accept |
| N3 | "0.68%" | MATCH | legal | accept | accept |
| N4 | 63.4 | MATCH | legal | accept | accept |

- 4/4 有效、4/4 对参考 MATCH；合法性 4/4 legal。
- **N1 关键事件**: B 与 C **各自独立**对"与官方参考一致"的答案报警，理由同为任务/参考语义问题——
  "average investment"被参考实现为"两个百分比(1%+2%)取平均=1.5%"，而两核验者均指出该题在缺少
  total asset base 的情况下用百分比均值回答"investment"存在语义错位（C 原话含 "category error / semantically
  awkward"，B 同义）。记录为：**核验者与官方参考在任务语义层分歧**；评分 MATCH 与核验 alarm 分属不同测量层，
  两者并存，不互斥。（非 actor 错误；不改题、不改参考。）

## 3. Part 2（人工候选；3 题 x 4 条件 = 12）

| candidate | 构造 | B | C |
|---|---|---|---|
| Q02-C1 | correct+legal | accept | accept |
| Q02-C2 | correct+illegal | **alarm（引用）** | accept |
| Q02-C3 | incorrect+legal | alarm | alarm |
| Q02-C4 | incorrect+illegal | alarm | alarm |
| Q03-C1 | correct+legal | accept | **abstain（单位表述）** |
| Q03-C2 | correct+illegal | **alarm（引用）** | abstain |
| Q03-C3 | incorrect+legal | **accept（未检出）** | **accept（未检出）** |
| Q03-C4 | incorrect+illegal | **alarm（引用为主）** | accept |
| Q04-C1 | correct+legal | accept | accept |
| Q04-C2 | correct+illegal | **invalid（JSON 损坏）** | accept |
| Q04-C3 | incorrect+legal | alarm | **abstain** |
| Q04-C4 | incorrect+illegal | alarm | abstain |

矩阵（B/C 决策计数）：

- correct+legal: B accept3；C accept2/abstain1
- correct+illegal: B alarm2/invalid1；C accept2/abstain1
- incorrect+legal: B alarm2/accept1；C alarm1/accept1/abstain1
- incorrect+illegal: B alarm3；C alarm1/accept1/abstain1

分类记录（引用原文要点）：

1. **B 对非法引用的报警有明确引文证据**：Q02-C2 指向 placeholder uid；Q03-C2/Q03-C4 指向 row 99（表仅 0-4 行）；
   B 均写明"答案数值正确但引用无效/不存在"。Q04-C2 的 B 输出损坏（见 §4），prose 中含同类引文质疑。
2. **Q03 的"incorrect"候选并不稳健**：C3/C4 的 -14054 是按"B-A 方向"构造的错答，但 B 与 C **分别**以
   "difference 的 A-B/B-A 方向未指定"为由接受（B 原文 "1309 - 15363 = -14054 …matches exactly"；C 原文
   "'difference' can imply A - B or B - A…or absolute"）。→ 构造层面该候选实为**方向歧义**下可辩护的答案；
   不再以"两核验者漏检"为该对的唯一读法；两种读法并列记录（冻结候选不改）。
3. **C 漏检/弃答分布**：C 对 Q02 的"两项子集"正确答案为 alarm（检出）；对 Q03-C3/C4 接受（方向歧义读法）；
   对 Q04-C3/C4 abstain（其理由为"表含 2021-2023 列 vs 表头 as-of 2020 的年份语义不确定"）；Q03-C1/C2 的
   abstain 理由含"答案缺单位表述（SEK million）"。
4. **重复刺激对（预先声明的设计）**：C 的 C1/C2、C3/C4 为同输入+同答案的同刺激重复（6/6 对 prompt 逐字节相同，
   机械核验）；6/6 对 C 决策一致。**不能**当作独立证据，也不能据此声称 C 对引用变化不敏感（C 看不到引用）。
5. **引用支持性列 = NOT_ASSESSED**：B 的 accept（含 correct+legal 3 例与 Q03-C3 方向歧义例）不构成"引用支持性
   已验证"；本 run 没有可单独判定的支持性记录（仅机械合法性 + 模型决策）。

## 4. 失败与偏差（完整）

- **1/36 输出损坏**：B-Q04-C2 为非法 JSON（含未闭合字符串/裸换行；finish_reason=stop，1,236 completion tokens）
  → 按规则记 `json_parse_error`（invalid），不重试、不修补、不从 prose 取判。B 有效决策分母 = 35。
- 其余 35/36 全部为合法 JSON 且决策字段合规。
- 无连接失败、无 5xx/4xx、无窗口越界、无 pin 漂移、无隔离违规（点检 13/13，GB10 同跑通过）。

## 5. 四维分列（固定口径）

| 维度 | Part1 | Part2 |
|---|---|---|
| 答案-参考匹配 | 4/4 MATCH（v2.1；分母=4） | 正确性=构造冻结（非结果）；参考匹配计算未作为结果使用 |
| 引用定位合法性（机械） | 4/4 legal | 依构造：legal 6 / illegal 6（12/12 复核一致） |
| 引用支持性 | NOT_ASSESSED | NOT_ASSESSED |
| 模型核验决策 | 见 §2 | 见 §3 |

## 6. 结论边界

- 本轮为**开发性校准**：含 1 次格式失败、若干方向/单位/年份语义分歧；全接受/全拒绝类别支撑均不成立，
  也不存在可外推的错误率。Part 1 是"旧池新增任务的受控扰动部分"，不是自然失败分布、不是新来源独立 heldout、
  不能声称扰动因果效果（无原始版对照）。Part 2 是人工构造候选面板，不得与 Part 1 混算。
- 下一步（同一授权链）: S4 TQ-5 来源隔离开发性验证（技术条件满足后自动执行）；随后 S5 汇总。
