# Loop A 任务：T6 有界提案与统一档案（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T6.md` 执行；先通读 `meta/optimizer_policy.md`（改进器策略草案）、T5 已验收包（`runs/T5/20261014T233742Z_cb132ce7/`，T5R-04 ACCEPTED @115f396）与 T4 v2（`runs/T4/20261014T184810Z_c9dcfe0e/`，T4R-01）。**完成后必须自检并修到干净再交付。**

## 预算与调用纪律（先读）
- 本卡 profile=BR：额外便宜请求上限 4、强模型请求上限 0。**本轮不发起任何额外模型调用**（用量记 0/4；理由：候选由现有证据离线构造；卡 A3 要求不运行 C/S 模型批次）。网络/远程/生产/数据库/训练调用均 0；自动重试 0。任何设计若"需要模型调用"才成立：停下、如实记 UNRESOLVED、不得调用。
- B0 式写入纪律：只写 `runs/T6/<run_id>/`；`meta/lessons.jsonl`、`meta/nogoods.jsonl` 为未来共享存放点，本卡**只读引用说明、不写入**（写入留待未来授权，在 receipt 声明）。

## 任务范围（bounded v1）
1. **`archive_implementation/`——共用谱系与失败缓冲机制**（本地、确定性、仅标准库；附 README 与未验证面）：
   - candidate/evaluation 唯一 ID 与**父代内容寻址**（父版本 = 内容哈希组；至少覆盖 T5 v3 @115f396 与 T4 v2 的 canonical id；含验证命令）；
   - 失败缓冲：lessons（经验）与 nogoods（被拒候选 = 拒绝原因 + **版本适用条件**；"拒绝 ≠ 永远无效"，条件满足可再提；**重复已证失败包必须被拒**）；
   - **选择性上下文导出**（"完整档案不进入任务上下文"）：给定候选 → 导出最小相关切片（含示例与机制字段）并留证；
   - **跨方向引用去重计数**：同一证据被多候选引用只计一次；提供计数机制与演证；
   - 机制须以本地 fixture 演证（含至少 1 个被拒样例：如与已证失败包重复的候选 → nogoods 拒绝且 not enabled）。
2. **首批候选（本批 ≤2；全卡上限 4）**：
   - 从**开发失败**选择一个具体问题（须引用精确证据出处：T4 baseline 画像的漏检/未验证面、T1 案例族、或 T4/T5 评审链暴露的工程失败族；selection rationale 写入 candidate_index）；
   - 每候选 = **一个对象**（预检 recipe 或证据交付 recipe 二选一）+ **三个条目**；条目只准引用 T5 `registered_operations.json` 的已登记操作；如某条目需要扩展操作词表，标注"需未来授权"且**不得在本卡改动任何共享件**；
   - 每候选包含：父版本定位、改动清单（3 条目）、对六项硬门的目标影响、评价计划（T7 将如何配对测量；本卡不执行）、成本记录、版本适用条件；写入 `candidate_packages/<candidate_id>/`；
   - `candidate_index.json` 汇总（含 selection rationale、候选状态、去重后的引用计数）。
   - 若证据不足以支撑 2 个合格候选，可只提 1 个或如实报 0 个——**不得为凑数造候选**。
3. 标准包件：receipt.json（输入绑定：卡片 6 输入 + T5/T4 依赖 + TASK_PROMPT；checks；usage（模型 0/4）；UNRESOLVED；authorization_ref=owner「继续…你自己设定goal去执行吧」+ R 线 U07=C）、summary.md、artifacts_manifest.json、events.jsonl、TASK_PROMPT.md（逐字复制本任务书）。
4. 三轴：DELIVERED / UNREVIEWED / NOT_ENABLED；候选一律**不启用**。

## 完成前自检（硬性）
1. 逐条映射卡 §6：A1（每候选可定位父版本/改动/评价/成本）、A2（拒绝候选不启用；跨方向引用不重复计数）、A3（C/S 机制可复用但零模型批次→usage 0/4 与"无模型调用"证据）、A-common。
2. G1 收据守卫：包内每个 `.md` 逐个 `python3 scripts/graph/hooks/summary_recompute_guard.py check <path>` rc=0；失配变体运行时派生、不落盘。
3. 重算所有声明哈希（tracked 用 canonical `git rev-parse HEAD:<path>`；run 内文件 sha256；模式若声明需与交付一致）。
4. 写入边界：含 gitignore 视野的扫描；`git status` 仅出现 `runs/T6/<run_id>/`（外加既有 logs 脏件与未提交 T4 v1 目录）。
5. 修复记录如实登记（修复前后对照）；证据不得因修复丢失（保留 attempt/失败件）。

## 停止条件
输入漂移、权限不明、需越界访问、需联网/模型/生产/数据库、需运行 daemon（含 Loop B）、预算不可计 → STOPPED：保留证据、如实报告、不扩范围。不得进入 T7。

## 交付回复（简短）
run 目录绝对路径；archive 机制演证摘要（含被拒样例与去重计数）；候选数量与各自对象/三条目摘要；self_check（A1/A2/A3/A-common+G1）；usage（模型 0/4）；未验证面与 UNRESOLVED；阻断（若有）。
