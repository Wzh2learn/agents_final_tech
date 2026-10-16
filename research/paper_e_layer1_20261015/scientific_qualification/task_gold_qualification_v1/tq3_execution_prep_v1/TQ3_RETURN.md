# TQ3_RETURN

> 状态：`MATERIALS_PREPARED_AWAITING_RUN_AUTHORIZATION`
> `system_outcome = NOT_RUN`；`scientific_gold_validity = NOT_ESTABLISHED`；`layer2_authorized = false`
> 身份：Loop D（AI）。本轮零模型 / API / 训练调用；除指定 BCE URL 两次抓取尝试外无联网。
> 旧文件（measurement_contract_v2/、ai_assisted_review_v1/、quarantine/、冻结稿、v4）一律未覆盖、未改写。
> 日期：2026-10-16（Asia/Shanghai）

## 1. 修复证据（本轮实际做了什么）

### 1.1 specs_rev1（9 份规格修订）

- 补齐 `question_uid` / `table_uid`：来源 `coordinator/case_provenance.json`；
  9/9 与 raw TAT-QA 记录逐条断言一致（见 `specs_rev1/BUILD_RECEIPT.json` 的
  `uid_verification`）。
- 发现并修正 v2 的 provenance 缺陷：`measurement_contract_v2` 的 9 份规格把
  **语料整文件哈希**填进了逐题字段 `source_table_sha256` / `perturbed_table_sha256`
  （全部等于 `tatqa_tables.json` 的 3e7e0568... 与 `injected_tables.json` 的
  827092cf...，9 份完全相同）。rev1 恢复为**逐题规范哈希**（canonical serialization
  见 REVISION_NOTES），并把两个语料级哈希移到 `corpus_pins` 正确标注；
  缺陷实证记录在 BUILD_RECEIPT.json 的 `v2_pin_observations`。
- 新增 `raw` pin 块（raw 文件名 + 文件哈希 + record/question index）；
  `panel_plan`：Q02/Q03/Q04/Q05/Q10/Q12 = dev 面板输入（进入主指标）；
  Q06/Q08/Q09 = 探索性侧案例（不进入主指标）。
- v2 原位文件保留，rev1 为其执行权威版本（REVISION_NOTES.md 记载全部变更）。

### 1.2 entry_checks（两项过强验收的纠正）

- 纠正对象：`measurement_contract_v2/tools/tq2_offline_checks.py` 中两条断言——
  ①“改动的副本哈希不等 = 已拒绝”；②“字符串含 UNRESOLVED = 已阻断比较”。
  这两条都只是字符串/哈希比较，不是真实入口行为。旧文件未动，纠正记录在
  `entry_checks/ENTRY_CHECKS.json` 的 `supersedes` 字段。
- 新建真实入口 `tools/tq3_scoring_entry.py`（本地、确定性、无模型/无网络：
  load_input 校验 schema/泄漏/pinned-hash；validate_reference_coords；score 评分），
  并用 `entry_checks/tq3_entry_checks.py` 通过**真实入口**执行 7 项检查，7/7 PASS：
  - 12/12 面板输入带 pin 加载成功；
  - 评分夹具 MATCH / NO_MATCH 方向正确（夹具注明非 actor 结果）；
  - 非法坐标 -> `INVALID_REFERENCE_COORDINATES` 拒绝；
  - 改动输入 -> `INPUT_HASH_MISMATCH` 拒绝，**无对象加载、无分数产生**；
  - UNRESOLVED scale -> `BLOCKED_SCALE_UNRESOLVED`，`score=None`（无有效分数）；
  - 泄漏输入 -> `INPUT_LEAKAGE` 拒绝。

### 1.3 Q11 BCE 来源核验（RETRIEVAL_BLOCKED）

- 指定 URL 两次抓取尝试均被 Akamai 地理/风控重定向拒绝（302 -> geo 页，
  “Request Rejected / Requete rejetee”，7380 B；两次响应体字节相同 sha256
  `6a53e737...`）。官方 PDF **未归档**，不声称已归档、不伪造来源。
- 证据保存于 `source_completion/`（两个 blocked HTML、响应头、attempts 回执）。
- owner 转述事实（Bell Wireless Q4 2019=2493、Q4 2018=2407、单位百万加元、
  page 4）登记为 `OWNER_SUPPLIED_SOURCE_STATEMENT`（非已验收 citation）。
- 硬规则已写明：`reference_source_completion`（评分/审计侧）与
  `model_input_supplement`（模型可见输入，必须单独版本化）严格分离；本轮
  未向任何模型输入写入该事实。

### 1.4 dev_panel（12 输入开发性试运行包）

- 输入 12 份：Q02/Q03/Q04/Q05/Q10/Q12 的 original + perturbed；
  全部同字段结构 `{task_id, variant, question, table, paragraphs}`；
  文件级 pin 记录在 `dev_panel/PANEL_MANIFEST.json`。
- 参考答案在 `dev_panel/reference/`（6 份）、评分材料在 `dev_panel/scoring/`（6 份），
  与输入严格分离；未进入任何输入文件（入口有泄漏扫描）。
- 明确标注：`DEVELOPMENTAL_DRY_RUN_NOT_HELDOUT`、非 confirmatory；
  Q06/Q08/Q09 被排除、Q01/Q07/Q11 保持隔离。

## 2. 可运行任务（下一次运行将产生什么）

- 运行卡：`run_card/RUN_CARD_v1.md`（+ `run_card/prompt_templates.md`：
  actor / B / C 三个固定模板）。
- 规模：12 次 actor + 12 次 B 核验 + 12 次 C 核验 = 36 次计划调用；
  基础设施重试 <= 4；总请求上限 40。需更多调用时先缩减范围，不得超额。
- 核验方式：
  - A = 简单规则基线（确定性、无模型）：schema/数值存在性/引用坐标边界；
  - B = 同源模型核验（与 actor 同源；一致性检查 + 可复算时复算）；
  - C = 独立路径任务核验（fresh context；只给输入 + actor 最终 answer，独立解题后比较）；
  - B/C 使用同一份 actor 输出、相同可用证据与可比预算（各 1 次调用/份）。
- 评分：运行后用 `tools/tq3_scoring_entry.py`（确定性）对照 reference/scoring 打分；
  实际运行记录到 `runs/<run_id>/`（含 RECEIPT）。
- 本轮已把“可解释性”做进入口与材料：任何异常（哈希不符、泄漏、未解决 scale）
  都会在入口处被拒绝或无有效分数，而不是靠事后断言。

## 3. 剩余运行授权（仅这些具体缺项）

- G1 模型 pin（actor/B/C 的 id+endpoint+version+解码；B 同源；C 池安排）；
- G2 预算（请求数固定 <=40；token 上限建议 <=150k；费用上限按模型换算）；
- G3 时间窗口与执行者（建议单窗口 <=90 分钟）；
- G4 runner 实现授权（构建 runs/ 与调用脚本，预计 <=1 天）；
- G5 运行环境（GB10 或本机）+ 输出路径 + 凭据访问方式。
- 记录：旧实验授权不挪用；授权缺项清单见 `authorization/AUTHORIZATION_STATUS_v1.md`；
  “全部人工 gold 未建立”不再是本开发性试运行的阻塞理由（按 2026-10-16 裁决）。

## 4. 研究风险（如实登记）

- 样本结构：6 题 x 2 版本为**配对设计**，不是 12 个独立样本；聚类单位为 table（6 张）。
- 参考侧：`reference_validity = NOT_ESTABLISHED`；perturbed 版参考答案依赖暂定的
  PRESERVED 判断（AI，非独立 gold）；指标只能描述性报告，不能当 confirmatory 结果。
- 评分规则为开发级（span 包含、数值容差、日期格式），只用于干跑；不得据此升级 claim。
- C 的“独立路径”来自提示与访问方式（不给 actor 证据/推理），若 C 与 actor 同模型池，
  必须记录“同池”事实；不得仅凭三臂差异推断机制。
- 未被面板覆盖：Q06 的列身份/单位损伤候选、Q08/Q09 的年份/范围歧义（保持探索性）、
  Q01/Q07/Q11 的参考缺口（保持隔离）；Q11 官方来源仍 RETRIEVAL_BLOCKED。
- 运行后若输出含弃权/无法判别，没有 gold 可仲裁——如实报告 UNRESOLVED，不补造答案。

## 5. 锚点文件

- 修订规格：`specs_rev1/REVISION_NOTES.md`、`specs_rev1/BUILD_RECEIPT.json`
- 入口与检查：`tools/tq3_scoring_entry.py`、`entry_checks/ENTRY_CHECKS.json`
- 面板：`dev_panel/PANEL_MANIFEST.json`、`dev_panel/README.md`
- 运行卡：`run_card/RUN_CARD_v1.md`、`run_card/prompt_templates.md`
- 授权：`authorization/AUTHORIZATION_STATUS_v1.md`
- Q11 来源：`source_completion/Q11_SOURCE_COMPLETION.md`、`source_completion/bce_retrieval_attempts.json`
- 全量哈希：`MANIFEST.json`（51 个文件，自排除）

## 6. 唯一下一步

owner 填写 G1-G5（尤其是模型 pin 与预算）→ 实现 runner（G4）→ 按运行卡干跑
（<=40 请求）→ 产出 runs 回执与描述性汇总 → 由 owner 决定是否需要独立复核。
