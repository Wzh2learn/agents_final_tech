# TQ-3 最小运行卡 v1 (Developmental Dry Run)

> 状态：`PREPARED_AWAITING_AUTHORIZATION`（未执行；本轮材料收口，零模型调用）
> 日期：2026-10-16。作者：Loop D (AI)。
> 目标：在 12 输入开发性面板上产出真实系统输出与 A/B/C 核验结果，使下一次运行
> 能够产生可解释的真实系统结果。不是确认性实验，不是 heldout，不升级任何科学 claim。

## 1. 运行规模（固定）

- actor：12 次调用（6 题 x {original, perturbed}，每个输入 1 次）。
- B 核验：12 次（对每份 actor 输出 1 次）。
- C 核验：12 次（对每份 actor 输出 1 次）。
- 计划调用合计 36；基础设施错误重试 <= 4；总请求上限 40。
- 若实现需要更多调用：先缩减范围（例如只跑 6 个 original），不得自动超额。

## 2. 固定 actor

- model / endpoint / version / decoding params：`AWAITING_OWNER_PIN`（见 §8 G1）。
- 每个输入一次性调用，使用 `run_card/prompt_templates.md` 的 actor 模板；禁止逐题定制提示。
- actor 输出 schema（固定）：{"task_id": str, "answer": str|number, "evidence": [{"table_row": int, "table_col": int}], "notes": str(optional)}。
- 输出保存：runs/<run_id>/actor/<task_id>_<variant>.json。

## 3. 输入与隔离

- 输入 = dev_panel/inputs_original|inputs_perturbed（12 个文件；PANEL_MANIFEST.json 已 pin 哈希）。
- actor 只能看到输入文件全文（task_id, question, table, paragraphs）。不得获得
  reference/、scoring/、specs_rev1/ 或任何注入信息。
- B/C 使用同一份 actor 输出与相同可用证据（同一输入块）；C 另见 §4 的限制。
- C 不得获得参考答案、derivation、注入来源；不得获得 actor 的 evidence/reasoning
  （只给最终 answer）。B 可以看到 actor 输出的全部字段。

## 4. 四类核验（A/B/C + 简单规则基线）

- A = 简单规则基线（简单规则检查；无模型调用，确定性）：
  (i) actor 输出 schema 合法且含非空 answer；
  (ii) numeric 题 answer 中可提取数字；
  (iii) evidence 坐标（若提供）在输入表范围内。
  任一失败 -> alarm；否则 accept；无 abstain。
  实现：复用 tools/tq3_scoring_entry.py 的 load/校验函数；记录到 runs/<run_id>/A/。
- B = 同源模型核验（12 次调用）：模型与 actor 同源（G1 指定；同家族/同版本）。
  提示见 prompt_templates；要求检查一致性 +（可复算时）从 actor 引用单元格复算；
  输出 accept/alarm/abstain + 理由 + 具体矛盾点。
- C = 独立路径任务核验（12 次调用）：fresh context；只给（输入 + actor 最终 answer）。
  要求独立解题后比较；不得复用 actor 的引用/推理。输出 accept/alarm/abstain + 理由 +
  自己的答案 + 矛盾点。
- 决策函数（B/C 同构）：accept = 核验认为答案与输入证据一致；alarm = 指认具体矛盾点；
  abstain = 证据不足/歧义。无具体矛盾点不得打 alarm；无判断不得打 accept。

## 5. 评分（参考侧；运行后）

- 用 tools/tq3_scoring_entry.py（确定性、无模型）对 actor 输出打分。
- 对照 dev_panel/scoring/*.json 与 dev_panel/reference/*.json；结果按状态记录：
  MATCH / NO_MATCH / INVALID_ACTOR_OUTPUT / BLOCKED_SCALE_*。
- 固定标注：reference_validity = NOT_ESTABLISHED；本面板指标仅为描述性，
  不构成 gold 验证、不构成 confirmatory 结果。

## 6. 指标（描述性；分母固定）

| 指标 | 公式 | 分母 |
|---|---|---|
| actor MATCH 率 | MATCH 数 / 有效输出数 | 12 输入（配对设计，注明非独立样本） |
| B/C alarm/accept/abstain 计数 | 按臂计数 | 每臂 12 |
| A alarm 计数 | 计数 | 12 |
| 成本 | 实际调用数、token、耗时、重试数 | 总请求 <= 40 |

- 不使用标准 FNR/FPR 命名；不把低 U、低 alarm 或格式 PASS 当作科学资格通过。
- original/perturbed 为配对比较（同题两版本），不得当作独立样本量。
- 聚类单位：table（6 张表 / 6 题）；报表时注明。

## 7. 停止规则

- 重试 <= 4 次，仅基础设施错误；禁止内容性重试。
- 端点连续 2 次连接失败：停下并记录部分结果（PARTIAL）。
- 需要 > 40 请求：停止并回报，等待新授权；不得超额。
- 任何情况下不启动 Layer-2、不改冻结稿、不升级 claim、不公开 artifact。

## 8. 授权缺项（AWAITING；不得挪用旧实验授权）

以下字段为必填。给出的建议值（proposed）仅作默认候选，最终以 owner pin 为准：

- G1 模型 pin：actor / B / C 的模型 id + endpoint + version + decoding。
  建议默认：单一低成本执行模型经 OpenAI 兼容端点；B 与 actor 同模型同参数（同源）；
  C 与 actor 同池但独立调用（必须记录“同池/异池”事实）。候选（待选）：
  (a) GB10 本地服务端点（现有已服务模型，需给出确切 id / 量化）；或
  (b) 低成本 API 模型（例如 deepseek 系 flash 档）。由 owner 二选一或另选。
- G2 预算：请求数 <= 40（已固定）；建议 token 上限 <= 150,000（按 40 次 x 约 3.7k 估算）；
  费用上限 = 按 G1 所选模型单价换算（建议 <= 等值 USD 5；具体数字由 owner 填）。
- G3 时间窗口与执行者：建议单窗口 <= 90 分钟；具体日期/时段由 owner 定；
  operator = GB10 Loop A（或本机，由 G5 决定）。
- G4 runner 实现授权：构建 runs/<run_id>/ 与调用脚本（预计 <= 1 天；不改核心 harness）。
- G5 运行环境：建议 GB10（或本机）；输出路径 tq3_execution_prep_v1/runs/<run_id>/；
  凭据/端点访问方式由 owner 确认。
- 完成后产出 runs/<run_id>/RECEIPT.json + 结果汇总；是否需独立复核由 owner 决定。

## 9. 明确不做什么

- 不跑 Q06/Q08/Q09（探索性侧案例）；不跑 Q01/Q07/Q11（保持隔离）。
- 不将本面板称为新 heldout；不做 confirmatory 声称；不把 AI 一致当人工 gold。
- 本卡仅为准备：不在本轮调用模型。
