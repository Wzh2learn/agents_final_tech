# Loop C 独立评审任务 T5R-03：harness_rsi_v1 T5 v3 返工（第三轮独立评审；v1 被 T5R-01、v2 被 T5R-02 先后 REJECTED）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T6。

## 输出格式（硬性，先读；不按此格式 = 评审作废）
你的全部 stdout 会被机械抽取。**必须且仅**输出以下四个标记块，顺序固定；不要输出任何前言、总结、结语、清单或额外说明段落；摘要放进 REVIEW.md 块内：
=== FILE: REVIEW.md ===
=== FILE: review_receipt.json ===
=== FILE: ACCEPTANCE_PROPOSAL.json ===
=== END ===

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T4 v2 已验收（T4R-01）。
- 前史：T5 v1 REJECTED（T5R-01：执行位丢失致 17/17 不可复现；X06 伪造摘要穿透）→ v2 修复该 2 blocking（T5R-02 证实两者已闭合）但被判 REJECTED（replay 不稳定：陈旧 tick + 就地改写 manifest 绑定夹具，42/42 不可从交付字节复现）→ **v3 = 本轮返工对象**。
- 被审对象 = T5 v3：`research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/`（46 文件；已提交 `ebd2710`；`recipe_fixtures/dispatch/watcher.sh` 交付 mode 100755）。声称：**无前置重放**（README 记录的 `scratch/verify_replay.py` 入口，四轮 23/23=92、归一化一致、两树重放前后不变、manifest 45/45）；P01 用 `max_tick_age_minutes=0`，P09 的 60 分钟界 tick 只在外部 runtime 目录生成；run_probes 全矩阵收集（首败也 23 条）；NEW-1（interfaces/operations 内嵌 pin、目标 git_blob_id 复核、scope 修正）、NEW-3（异源 pin）、NEW-4（缩进）已折叠。

## 必读（只读）
`cards/T5.md`、`reviews/T5R-01/` 与 `reviews/T5R-02/`（前两轮全文——重点复现两轮 blocking 判定链）、T5 v3 全文（receipt/summary/repair_record/v2_v3_diff/recipe_interfaces/registered_operations/recipe_fixtures/README/run_probes/caller_validator/scratch 含 replay 证据）。

## 工具约束
- 白名单不含 git、mkdir、cp、mv、rm、chmod 等；git 被拒时用替代（字节派生 git blob SHA-1；`.git/index` 解析 mode）；被拒命令如实记录。
- scratch 只放仓库外（例：`/home/testuser/wzh/loop_runs/t5r03_recheck_a/`）；**work-root 必须不存在且位于交付树外**（verify_replay.py 拒绝覆盖与树内路径——被拒尝试也要如实记录）；不得在被审 run 或仓库内写任何文件。
- 不替包修任何东西（mode/时间/内容皆不允许）；先验证交付态，再运行。

## 必须独立复算（记录命令与退出码）
1. 计数/哈希/模式：46 文件；manifest 45 条逐条 SHA-256+bytes+mode 实算；处置 required_executables。
2. **replay-stability 核心**：运行交付入口 `scratch/verify_replay.py --run-root <v3> --work-root <外部新路径>` → rc=0、四轮 23/23、`tree_unchanged=true`、两树 manifest 45/45；**独立二次验证**：直接用交付 CLI 跑 `run_probes.py`（README/脚本用法）对交付树两遍 → 各 23 条且一致，运行后对交付树做全量 sha/mtime 扫描证明零写入；核对 P01 max_tick_age=0 与 P09 外部 runtime tick 的实现；确认 run 内无任何 prepare/改写路径。
3. **NEW-1 信任边界对抗**：自造 ≥2 个攻击：（a）替换（副本）registered_operations.json 的目标路径/内容 → 必须 `FC_INPUT_IDENTITY_MISMATCH`（或等价）且目标零执行；（b）替换目标文件本身（scratch 内副本+改字节）→ 执行前按 git_blob_id 复核被拒；核对内嵌 pin 常量与交付文件实测一致；核对 scope 措辞。
4. **前两轮闭合回归**：watcher 交付 100755（index/工作树）；X06A/B/C 与 Z01（交付自带）在重放矩阵中的表现；E10 异源 pin 正例；15 原负例码精确；四类分离；frozen_protections；TASK_PROMPT 与 `runs/T5/_dispatch/loop_a_prompt_t5_v3.md` 逐字节比对；G1 每个 `.md` rc=0；无裸 PASS/无越级；usage 零声明与 92 计数自洽；写入边界（含 gitignore 视野）。
5. **新对抗探针（≥3 新负例 + ≥1 新正例，自构造）**：如陈旧 tick（scratch 生成过期 observed_at → 必拒）；runtime-root symlink/越界；pin 类型畸形；合法新调用（有界 age 正常）→ 接受。
6. 披露核对：repair_record 与 v2_v3_diff 与实测一致；receipt.supersedes 链条（v1/v2 两次 REJECTED）准确。

## 输出（重复硬性要求）
只输出四块；块间不加多余分隔符。review_receipt.json 含（review_id="T5R-03"、task_id="T5"、reviewer/runtime、reviewed_artifact_sha256（≥12 件含 sha256/bytes/mode）、recomputed、checks、calls、refused_commands、reviewer_side_effects_disclosed、unverified、verdict）；ACCEPTANCE_PROPOSAL.json 含（decision/blocking_items/advisory_items/scope/justification/dissent/next_steps）。registry/state 由收口者更新；不得进入 T6。
