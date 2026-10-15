# Loop A 任务：T5 v3 返工 —— 按 T5R-02 修复 replay-stability blocking + 折叠 4 advisory（执行 + 完成前自检；第三轮独立评审）

你是 Loop A（GB10 上的 Codex CLI 执行层）。T5 v2 run（`runs/T5/20261014T212520Z_3acf4c1d`）被第二轮独立评审 **T5R-02 判 REJECTED（1 blocking / 4 advisory）**。先通读 `reviews/T5R-02/REVIEW.md`、`ACCEPTANCE_PROPOSAL.json`、`review_receipt.json`（并知悉 v1 前史：`reviews/T5R-01/`）。任务卡 `cards/T5.md` 不变；v2 已通过的全部面（执行位交付+mode 记录、外部 pin 语义、15 负例码、四类分离、frozen_protections、T4 消费约束、TASK_PROMPT 逐字性、G1）必须原样保留。

## BLOCKING（T5R-02）—— replay-stability：交付字节上的重放必须零写入且结果一致
事实（评审原文摘要）：
- 交付入口对交付字节直接运行 → rc=3、仅 1 条记录：P01 期望 ACCEPT 实得 REJECT（`FC_OPERATION_TARGET_FAILURE`，tick age 59min）——因 `valid_precheck_call.json` 用 `max_tick_age_minutes=30` 而 `tick_valid.json.observed_at` 是固定过去时间；
- 唯一到 21/21 的路径是 `scratch/prepare_runtime_fixtures.py` **就地改写** manifest 追踪的 SHA-256 绑定夹具 `recipe_fixtures/dispatch/tick_valid.json` → 重放后 manifest 失配；违反 FP-RAW-RECORD-INTEGRITY 的"run 文件只读"声明；
- `recipe_interfaces` 已声明 `max_tick_age_minutes=0`（replay-stable），但交付正例用的是 30（非 replay-stable）；
- disclosure 不对称：summary/提交信息写死"42/42"，README 未写重放前置条件；
- `run_probes.py` 首败即退（return 3），失败时只产 1 条记录。
**v3 必须满足的不变量（硬性）**：
1. **交付字节 + 交付模式上的重放 = 自证**：按 README 记录的入口从交付态直接重放（无任何前置准备）、两遍，均得到完整矩阵且逐项一致；
2. **重放零写入**：重放（含 fresh-delivery 模拟）**不得写任何 manifest 追踪路径**；交付树在重放后逐字节不变——自检含"重放后 manifest 45/45 复算 + 全 run 目录无新写入/无修改"证据；
3. 任何"运行时变体"（如带界 tick）一律在 **scratch 生成**（新文件），绝不就地改写交付夹具；交付夹具保持 replay-stable（如正例用 `max_tick_age_minutes=0`，与 recipe_interfaces 一致）；
4. `run_probes.py`：**收集全部用例后统一判定**（失败也产出完整矩阵），再以非零退出码反映失败；
5. README 写明重放入口、前置条件（应为"无"）与"交付树只读"约定；summary/receipt 的计数主张必须与"无前置条件重放"一致；
6. 时间类依赖全面清查：所有含时间语义的夹具/探针都必须 replay-stable（或运行时在 scratch 生成）。

## Advisory 折叠（T5R-02 的 4 条）
- NEW-1（trust-boundary）：`caller_validator` 需（a）对自身 `--interfaces/--operations` 输入做 SHA-256 pin 校验（常量内嵌或以显式 pin 参数传入并 fail-closed），（b）执行前用 `registered_operations.target.git_blob_id` 校验目标文件身份（不符即拒），（c）把 scope 声明修正为"against the delivered, identity-verified registry"。
- NEW-2：见上第 4 条（全矩阵收集）。
- NEW-3：在 caller_contract 声明"摘要内容充分性不在本校验器范围"；并加一个 pin 来源独立（异源文件）的夹具。
- NEW-4：修 `recipe_interfaces.json` error_surface 缩进。
- 附记（不实施）：评审 dissent-2（将摘要校验绑定到包级 summary.text 哈希）记录为后续可选项，本轮不扩范围。

## 其它要求
- **全量重建**：新 run_id（v3）；`receipt.supersedes` = 链条（v1 REJECTED by T5R-01；v2 REJECTED by T5R-02）+ 本修复清单；
- 标准包件 + TASK_PROMPT（逐字复制本任务书）+ G1（每个 .md rc=0）+ 双轮重放 + 交付树不变证据 + 修复记录（含 v2→v3 差异表）；
- 写入所有权/停止条件/B0 零调用同前；不做 git；不改其他文件；不得进入 T6。

## 交付回复（简短）
v3 run 目录绝对路径；BLOCKING 修复证据（无前置重放两轮矩阵、重放零写入与 manifest 不变证据、run_probes 全矩阵行为）；NEW-1..4 折叠对照；self_check；未验证面与 UNRESOLVED；阻断（若有）。
