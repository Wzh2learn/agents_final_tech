# TQ-4 运行卡 v2 (Calibration Run)

> 状态：`PREPARED_AWAITING_AUTHORIZATION_V2`（未执行；本文件不授权运行）
> 日期：2026-10-16。作者：Loop D (AI)。
> 重要：**不能复用 TQ-3 单次授权**；须按 `AUTHORIZATION_ITEMS_v2.md` 取得新的独立授权与窗口后才可运行。

## 1. 运行规模（固定）

- Part 1（自然任务）：4 题（N1-N4，冻结于 `panel_v2/natural/`）x {actor, B, C} = 12 次。
- Part 2（人工候选）：12 份候选（Q02/Q03/Q04 各 4 份，冻结于 `panel_v2/candidates/`）x {B, C} = 24 次（无 actor）。
- 合计计划 36 次生成请求；基础设施错误重试 <= 4；总请求上限 40；单并发；单请求超时 120 秒。
- 两部分分开记账、分开评价；不合并为单一"自然错误率"。

## 2. 固定模型（提案；运行前须重新核对）

- 沿用 TQ-3 配置作为提案：GB10 `http://127.0.0.1:8004/v1`，`Qwen3.6-35B-A3B-Q4_K_M.gguf`（run 前重新核对文件哈希/模型 ID/model_path；漂移即停，不自行换 pin）。
- 请求参数与 TQ-3 相同：temperature=0、top_p=1、seed 冻结、max_tokens=2048、stream=false、response_format=json_object、chat_template_kwargs={enable_thinking:false}。
- 预算：总 token 上限提案 400,000；单请求 prompt <= 8192、生成 <= 2048、发送前预留 10240；费用上限 USD 0（本地服务）。

## 3. 窗口（新窗口；待授权）

- 单窗口；允许启动时段 09:00-18:30（Asia/Shanghai）；从首个生成请求起 <= 90 分钟；20:00 前停止。
- 具体日期/时段由 owner/总规划师在授权项中填写；不得使用 TQ-3 已完成的窗口或授权。

## 4. 输入与隔离

- Part 1 模型可见输入 = N1-N4 的 **perturbed** 变体；original 与 reference/scoring 仅参考侧。
- Part 2 B/C 可见输入 = `panel_v2/candidates/inputs/Q02|Q03|Q04.json`（perturbed 副本）。
- 隔离：仅白名单字段（task_id, question, table, paragraphs）；不得出现 reference/scoring/注入元数据；
  B 可见候选/actor 完整输出（含 evidence）；C 仅见最终 answer。C 的标签固定为"同模型、独立上下文、可见候选答案"。

## 5. 输出 schema v2（证据协议 v2）

- actor/candidate 输出：`{"task_id":..., "answer":..., "evidence":[{"kind":"cell","table_row":<0基>,"table_col":<0基>} | {"kind":"paragraph","paragraph_uid":"<输入段落 uid>"}], "notes":...}`。
- 机械层（无模型）：`check_evidence_legality` 只记"合法/非法+原因"；支持性由 B/C 判定并单独记录（见 `evidence_protocol/EVIDENCE_PROTOCOL_v2.md`）。

## 6. 调度（固定）

- Part 1：先 4 次 actor（N1->N4），完成后 B/C：每份输出按序交替 B->C / C->B。
- Part 2：逐候选 B/C，交替 B->C / C->B；candidate 顺序按 candidates_v1.json 冻结顺序。
- 全部请求独立上下文；不携带上一题内容。

## 7. 评分与评价（固定）

- Part 1：actor 输出用 `scorer_v2/tq4_scoring_entry.py` 评分（MATCH/NO_MATCH/UNSCORABLE_*/BLOCKED_*）；
  机械合法性列单独记录；B/C 决策单独记录。
- Part 2：12 候选的 B/C 决策按 (answer_kind x evidence_legality) 交叉记录；机械合法性列单独记录；
  预注册目标见 `CANDIDATE_BUILD_SPEC_v1.md`（不按结果调题）。
- 报告口径：所有比率注明分母；MATCH 不等于"完整正确"；不签发 gold。

## 8. Runner 增量规格（相对 tq3_runner.py）

1. 两部分调度器（Part 2 无 actor；candidate 载荷构造）；
2. 提示模板 v2（actor 输出 schema v2；B/C 文本沿用 v1）；
3. 评分调用切换到 scorer_v2；合法性层输出（offline）；
4. 结果聚合按 Part 1 / Part 2 分离输出（RESULTS 两部分独立小节）；
5. 预算/账本/隔离/续跑机制照搬 TQ-3（已验证）；
6. 输出目录：`tq4_calibration_v1/runs/<run_id>/`；运行回执入口 `tq4_calibration_v1/TQ4_RUN_RETURN.md`。

## 9. 停止条件与纪律

- 同 TQ-3：连续 2 次连接失败、模型身份漂移、预算上限、pin 漂移/参考泄漏、窗口结束 -> 停止并保留部分结果。
- 不重启/修改现役服务；不引入新依赖/权重；不把 Q06/Q08/Q09 未决语义转为正/错标签；不以外观为目的反复调题。
