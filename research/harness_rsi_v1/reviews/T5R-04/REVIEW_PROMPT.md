# Loop C 独立评审任务 T5R-04：harness_rsi_v1 T5 v3 修正后交付态（聚焦复评；v1/v2/v3 前史三次 REJECTED 链条见下）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T6。

## 输出格式（硬性，先读；不按此格式 = 评审作废）
你的全部 stdout 会被机械抽取。**必须且仅**输出四个标记块，顺序固定；不要输出任何前言/总结/结语/额外说明段落：
=== FILE: REVIEW.md ===
=== FILE: review_receipt.json ===
=== FILE: ACCEPTANCE_PROPOSAL.json ===
=== END ===

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）。前史：T5 v1 REJECTED（T5R-01）→ v2 REJECTED（T5R-02）→ v3 REJECTED（T5R-03：manifest 模式自证失效——4 个文件声明 100755 未随交付落地，入口 rc=3；T5R-02 的 replay 阻塞经其独立复现已确认闭合，无完整性指控）。
- **Closer 修复（在 ebd2710 之上的 115f396，纯模式补丁）**：4 个文件（`run_probes.py`、`scratch/adversarial_checks.py`、`scratch/self_check.py`、`scratch/verify_replay.py`）补 100755（0 内容变更）；GB10 工作树 chmod 755（umask 渲染校正）；清理评审窗口遗留的 `__pycache__/caller_validator.cpython-312.pyc`（gitignored，创建于 2026-10-15T00:28:44Z，T5R-03 会话窗口，未在其副作用声明中披露）。Closer 复跑官方入口：rc=0、四轮一致、两树 45/45、extras []、failures []、pycache 未复生。
- 被审对象 = **修正后的交付态**：`research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/` @ HEAD `115f396`。
- 上一轮 4 个 advisory（restore_modes 盲点、umask 模式混合、guard-rail 错误包络、logs/ 观测盲区）为已记录 advisory，不要求修改；如你认为其中任何一项因本次修复变为 blocking，请如实升级。

## 必读（只读）
`reviews/T5R-03/`（重点其 blocking 与事实链）、`reviews/T5R-01/`、`reviews/T5R-02/`、T5 v3 全文（receipt/summary/repair_record/v2_v3_diff/scratch 的 replay 证据）。

## 工具约束
- 白名单不含 git、mkdir、cp、mv、rm、chmod 等；替代方法（字节派生 blob SHA-1、`.git/index` 解析含 mode）；被拒命令如实记录。
- scratch 只放仓库外（例：`/home/testuser/wzh/loop_runs/t5r04_recheck_a/`）；work-root 必须不存在且位于交付树外；不得在被审 run 或仓库内写任何文件。
- **你自己的直接 import 请加 `-B`/`PYTHONDONTWRITEBYTECODE=1`**（避免再现 pycache 残留）；对交付入口本身的运行保持 README 原样（prerequisites=NONE）。评审结束前自扫交付树（含 gitignored 视野）确认无残留并如实披露。

## 必须独立复核（聚焦，记录命令与退出码）
1. **模式修正核实**：46 文件/45 entries；对 4 个文件与 watcher.sh 核 worktree/index/HEAD 三层 mode 一致=755；其余 41 条逐条 mode 仍匹配；字节/SHA 45/45（证明 115f396 为纯模式补丁、blob 内容未改——方法如实记录）。
2. **官方入口复跑**：`scratch/verify_replay.py --run-root <v3> --work-root <外部新路径>` → rc=0；四轮 23/23 归一化一致；两树 manifest passed 且 failures=[]、extra=[]；运行后含 gitignore 视野的全树扫描（find 含 __pycache__/.*/等）无新增；`tree_unchanged` 语义独立复核（你自己的 before/after scан，勿只信其输出）。
3. **六个 surfaces 复现**：replay_summary.json / self_check_result.json / events.jsonl / receipt.json / summary.md / repair_record.md 的 45/45 主张与你的实测一致；无相反主张残留。
4. **回归抽查**：交付 CLI `run_probes.py` 两遍 → 各 23 条一致；抽查 P01（ACCEPT）、X06A/B（NOT_PINNED/PIN_MISMATCH）、Z01（INPUT_IDENTITY_MISMATCH）与 ≥2 个拒绝码；G1 每 .md rc=0；usage 零声明与计数自洽；四类分离与 frozen_protections 未被触动。
5. **修复披露核实**：closer 记录（模式补丁 + pycache 清理 + 归因）与现场事实一致；如发现任何不符，如实报告。
6. 可选（有界）：在 scratch 模拟 umask 022 vs 002 的 fresh-clone 行为以量化 ADVISORY-2 的可移植性边界（不改包）。

## 输出（重复硬性要求）
只输出四块；块间不加多余分隔符。review_receipt.json 含（review_id="T5R-04"、task_id="T5"、reviewer/runtime、reviewed_artifact_sha256（≥12 件含 sha256/bytes/mode）、recomputed、checks、calls、refused_commands、reviewer_side_effects_disclosed、unverified、verdict）；ACCEPTANCE_PROPOSAL.json 含（decision/blocking_items/advisory_items/scope/justification/dissent/next_steps）。registry/state 由收口者更新；不得进入 T6。
