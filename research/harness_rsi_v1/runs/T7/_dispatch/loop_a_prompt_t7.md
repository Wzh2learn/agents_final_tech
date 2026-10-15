# Loop A 任务：T7 R 独立验收与回滚（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T7.md` 执行；先通读 `reviews/T6R-01/`（重点 ADVISORY-1 与 next_steps）、T6 包（`runs/T6/20261015T012906Z_b9bb8ca6/`）、T5 v3 包（`runs/T5/20261014T233742Z_cb132ce7/` @115f396）、T4 v2 包与 `evaluation/reliability_spec.md`。**完成后必须自检并修到干净再交付。**

## 预算与调用纪律（先读）
- profile=BR：额外便宜请求上限 0、强模型请求上限 1（强评审名额由后续 Loop C 消耗，Loop A **零模型调用**）。网络/远程/生产/数据库/训练/daemon/Loop B 均 0；自动重试 0。
- 只写 `runs/T7/<run_id>/`；候选/配置的修正只写 T7 run 内（隔离区）；**不改 T6/T5/T4 的被审包、不改共享件**；不启用任何东西。

## 前置修正（T6R-01 ADVISORY-1 precondition —— 必须先于对 cand-d44c49dec4d95741 的任何评估）
在 T7 run 内产出一份**候选修正记录 A-1**（最小化、可审计、含改动前后对照）：
- 把"absent receipt block"拆分为 (a) 应计量而缺失（证据完整性问题）与 (b) **合法不可计量**（保持 UNRESOLVED，不得判失败）；
- severe-miss 指标**不得把合法 UNRESOLVED 折算为 severe defect**；
- 要么把问题族重新锚定到真实的 severe-defect-miss 案例，要么对 T1 v3 applicability 的再分类给出理由。
- 若无法忠实完成：该候选标 `NOT_EVALUABLE`，走 NO_PROMOTION 路径，如实报告（不得为产出结果而放宽）。

## 任务范围
1. **配对重放（硬门先行）**：候选（含 A-1 修正如有）vs 基线；评测器/案例/环境身份齐全并绑定（T5 recipes 机制 + T1 v3 16 案 + T4 baseline case-level 数据）。顺序：先硬门（严重漏检=0、合法误拦≤基线、证据完整、无越级、原始记录完整、预算完整）再收益（检测改善/成本）。
   - **集合现实**：selection/sealed 24/24/24 仅计划、未构建 → 如实记 `selection_set=NOT_BUILT`、`sealed=NOT_APPLICABLE/UNRESOLVED`，**不得伪造封存访问**；"选择集选一个、封存只访问一次"在缺失集合下按 NO_PROMOTION / DEFERRED 处理并写明依据。
2. **选择与回滚演练**：按选择规则得出 通过 / NO_PROMOTION（预注册成本比较分支可用时可用）；无论结果，均演练**回滚**：从候选态恢复父版本（T5 v3 @115f396 / T6 父组），验证行为一致、旧证据哈希不变 → `rollback_receipt.json`。
3. **产出**：`pilot_acceptance.json`（六硬门/收益/成本/选择结论与依据）、`rollback_receipt.json`、`review_packet.md`（供强评审）；标准包件（receipt/summary/artifacts_manifest/events/TASK_PROMPT 逐字）。
4. 三轴：DELIVERED / UNREVIEWED / NOT_ENABLED；候选一律不启用；**A3 措辞纪律**：不得把收尾审计通过写作实验或科学成功；R 通过不代表 C/S 有效。

## 完成前自检（硬性）
1. 逐条映射卡 §6：A1（六硬门满足 + 至少修复两个漏检且无回归，或预注册成本比较——按可用证据如实判定与记录）、A2（回滚后行为一致、旧证据哈希不变）、A3（措辞纪律）、A-common。
2. G1 收据守卫：包内每个 `.md` 逐个 rc=0；失配变体运行时派生不落盘；模式声明与交付一致（提交侧将以 git 归一化 mode 落实全部 755）。
3. 重算所有声明哈希（canonical `git rev-parse HEAD:<path>` + run 内 sha256）；写入边界含 gitignore 视野（自查无 .omc/__pycache__/临时目录残留）。
4. 修复记录如实登记；证据不因修复丢失。

## 停止条件
输入漂移、权限不明、需越界访问、需联网/模型/生产/数据库、需运行 daemon、预算不可计 → STOPPED：保留证据、如实报告、不扩范围。不得进入 T8。

## 交付回复（简短）
run 目录绝对路径；A-1 修正结论（或 NOT_EVALUABLE）；配对重放/六硬门结果摘要；选择结论（通过/NO_PROMOTION）与依据；回滚演练结论；self_check（A1/A2/A3/A-common+G1）；usage（模型 0）；未验证面与 UNRESOLVED；阻断（若有）。
