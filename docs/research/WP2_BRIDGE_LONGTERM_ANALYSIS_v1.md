# WP-2 桥失败：根因分析与长期方案 v1

> date: 2026-10-14 | 作者: Loop D | 触发: 两卡两停（S4S7 → S4b），owner 指示"用相关 skill 找原因、想解法、要长期方案"
> 方法: `systematic-debugging`（四阶段 + "3 次修复失败=质疑架构"规则）+ `structured-output`（结构化输出可靠性层级）；**零模型调用**（纯分析/设计文档）。

## 1. 事实时间线（一手证据，全部已入仓）

- 卡1（S4S7）：1 次请求 → 响应非 JSON 且**未先持久化** → 立即停（1/300 永久计入）。
- 卡2（S4b）：persist-first 重建成功；探针 03 与首题"通过"（解析路线=**首个平衡 JSON 对象**）；中途一次 `delta_source is not a decimal` 工程失败（已修）；**最终重跑：纯散文思维链、512 token 截断、三路线全败 → 同族二次失败 → STOP_THIS_PANEL**（9/300 已计）。
- 小事故两项（探针超限 1 次、1 份 raw 被覆盖）均已如实披露（`S4B_STOP_RECEIPT.json`）。

## 2. 根因（对应 systematic-debugging Phase 1–2）

**证据 1（探针 raw）**: "成功"输出的形态是**混合流**——模型把脚手架（`STAGE=…`）、指令回显、示例回显、以及目标 JSON 混在一起输出；桥靠"抽取第一个平衡对象"侥幸拿到 payload。
**证据 2（失败 raw）**: 加入聊天模板后，模型直接进入"思考"模式（散文 CoT，无 JSON，`finish_reason=length`）。
**证据 3（架构位置）**: 我们的 actor 服务是自建 transformers **纯文本续写**接口——既无工具调用层、也无 JSON mode/语法约束。按 `structured-output` 的可靠性层级，它处于**最底层**（prompted JSON，无强制层），而该 skill 明确要求"对每一个会被机器消费的 hop 使用可强制的层"。

**结论**: 问题不在某一条提示词或某一个解析分支，而在**架构缺少"结构化输出强制层"**。两轮"改提示/改解析/改持久化"都属于症状修复；按 `systematic-debugging` 的"3+ 次修复失败 → 质疑架构"规则，现在应重构接口架构，而非再开第三轮同类修补。

## 3. 长期方案（目标架构，分层）

| 层 | 现状 | 长期设计 | 依据 |
|---|---|---|---|
| L1 生成层（最关键） | 无约束采样 | **引导式解码（JSON schema/grammar 约束）**：首选 `outlines` 挂在现有 transformers 服务内（进程内 logits 约束，CPU 可用，改动最小）；备选 ① vLLM guided_decoding（GPU 被 judge 占用，暂不可行） ② llama.cpp GBNF（未安装，迁移成本大，列为未来选项） | structured-output 层级 #1/#2：能强制就强制 |
| L2 接口层 | "STAGE=…" 纯文本脚手架 | 标准 chat 消息（system/user 角色）+ "仅输出 JSON"硬指令 + **恰 1 个锁定示例**；模板冻结+哈希 | 层级 #3 的规范写法 |
| L3 桥/解析层 | 三路线抽取（无 schema 校验） | 保留三路线作 defense-in-depth + **flat schema 校验**（枚举 tool 名、expression 字符类、字段类型）+ persist-first（已建）+ **每 stage ≤1 次计数格式重试（附解析错误回喂）** | "one retry, not a loop"；"never silently coerce" |
| L4 验证层 | 无 | 离线资格（合成格式语料单测 + 重放 8 份已存 raw——预期：散文样本会被 schema 拒绝，证明分层必要性 + 约束处理器构建/接线测试）；在线资格（≤3 探针，预声明通过标准：3/3 schema 合法、无散文、字段齐全；不过 = 永久停） | verify-before-done 的门 |
| L5 治理层 | — | 新组件（schema/处理器/依赖版本）在 S7 一并冻结哈希；依赖记录（名/版本/license）；格式重试计入请求预算 | 预算透明只增不减 |

## 4. 为什么选这条（而不是"再优化 prompt"）

- `structured-output` 原话: "Prompted JSON fails on ~2–8% of calls… 'Just add ONLY JSON' works 95% of the time. That's the problem." —— 我们的循环要跑数百次，95% 不合格。
- 抽取式解析被该 skill 列为 red flag（"regex to extract JSON… one prompt tweak away from breakage"）——现状正是如此。
- 约束解码把"格式正确"从概率问题变成**机械保证**；解析器随后只做 defense-in-depth，而不是主防线。

## 5. 对科学性的影响：零

- 生成设置（temp 0 / 单发 / 512 / 4096 / 经验块 600 / 无第三轮自动修复）**不变**；
- 接口与 schema 在 S7 前完成冻结（属预冻结接口工程，与既有 S0–S0d 同类）；
- 两次失败尝试与全部 incident 保留在 lineage；预算记账规则只增（格式重试计数）。

## 6. 执行计划

1. **A 轮（已派发，零模型调用）**: 实现 L1–L4 组件 + 离线资格 + 收据。
2. **在线资格（≤3 探针）**: 通过 → 恢复 S4（S4c）；不通过 → STOP_THIS_PANEL 永久（不再第五轮）。
3. 待 owner: 在线资格"开跑"一句话批准即可（预算沿用，9/300 已用、剩 291）。

## 7. 证据指针

`S4S7_EXECUTION_REPORT.md`、`S4_HISTORY_FAILED_ATTEMPT_RECEIPT.json`、`S4B_EXECUTION_REPORT.md`、`S4B_STOP_RECEIPT.json`、`S4_HISTORY_FAILURE_FINAL_RECEIPT.json`、`s4b_run/attempts/**`（含全部 raw）、`S4B_BRIDGE_PROTOCOL_RECEIPT.json`。