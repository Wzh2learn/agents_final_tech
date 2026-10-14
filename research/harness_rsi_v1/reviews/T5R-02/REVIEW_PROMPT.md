# Loop C 独立评审任务 T5R-02（重派 B）：harness_rsi_v1 T5 v2 返工（第二轮独立评审）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T6。

## 输出格式（硬性，先读；不按此格式 = 评审作废）
你的全部 stdout 会被机械抽取。**必须且仅**输出以下四个标记块，顺序固定；不要输出任何前言、总结、结语、清单或额外说明段落；若想写摘要，放进 REVIEW.md 块内：
=== FILE: REVIEW.md ===
...（Markdown 正文）
=== FILE: review_receipt.json ===
...（JSON 对象）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
...（JSON 对象）
=== END ===

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T4 v2 已验收（T4R-01 ACCEPTED）。
- T5 v1（`runs/T5/20261014T195445Z_60c8e213`）被 T5R-01 REJECTED（2 blocking：交付执行位丢失致 17/17 不可复现；自洽伪造摘要 X06 穿透 A2；另 6 advisory）；v1 保留在磁盘、不进 git（评审包在 `reviews/T5R-01/`）。
- 被审对象 = T5 v2：`research/harness_rsi_v1/runs/T5/20261014T212520Z_3acf4c1d/`（46 文件；已提交 `e0d2523`，`recipe_fixtures/dispatch/watcher.sh` 以 git mode 100755 交付）。声称：模式已交付并记入 manifest（`required_executables`）；fresh-delivery 模拟 21/21×2=42/42（每轮 ACCEPT=4/REJECT=17）；摘要接受要求"声明==实测==外部 pin"（无 pin→`FC_ARTIFACT_NOT_PINNED`、错 pin→`FC_PIN_MISMATCH`、正确 pin→接受）；6 个 advisory 全部折叠。
- Loop D 对 BLOCKING-2 的裁决（卡 §7）：接受须绑定生产者控制之外的外部 pin；威胁边界（不防调用方自递假 pin）须显式声明。

## 必读（只读）
`cards/T5.md`、`reviews/T5R-01/`（前轮 REJECTED 全文——重点复现其 2 个 blocking 的判定链）、T5 v2 全文（receipt/summary/recipe_interfaces/registered_operations/recipe_fixtures/README/run_probes/caller_validator/scratch）、T4 v2 适配器与 T4R-01。

## 工具约束
- 白名单不含 git、mkdir、cp、mv、rm、chmod 等；git 被拒时用替代（字节派生 git blob SHA-1；`.git/index` 解析可读 mode 字段）；被拒命令如实记录。
- scratch 只放仓库外（例：`/home/testuser/wzh/loop_runs/t5r02b_recheck_a/`）；不得在被审 run 或仓库内写任何文件；披露全部仓库外路径。
- 运行 .sh/.py 用 `python3 -c 'import subprocess; ...'` 包装。**不得"替包修模式"**：先验证交付态（watcher.sh 交付为 100755/X_OK；index/工作树一致），再运行探针。

## 必须独立复算（记录命令与退出码）
1. 计数/哈希/模式：46 文件；manifest 45 条逐条 SHA-256+字节+`mode` 实算；磁盘无遗漏/多余。
2. BLOCKING-1 复现验证（核心）：复跑 T5R-01 原命令链 P01（`dispatch_precheck_adapter --watcher <v2>/recipe_fixtures/dispatch/watcher.sh --tick-marker <v2>/..../tick_valid.json --max-tick-age-min 0`）→ rc=0；全量探针矩阵两遍（fresh-delivery 模拟按 manifest 恢复模式 + current-tree）→ 21/21×2、ACCEPT=4/REJECT=17 一致；核对 receipt/summary 计数；对抗质检：核查是否还有其它"合同要求可执行"元素被漏标（读目标工具合同源）；index mode 佐证（`git ls-files -s` 或解析 `.git/index` 的 mode 字段，应为 100755）。
3. BLOCKING-2 复现验证（核心）：自构造 ≥3 个新探针：自洽伪造-无 pin→拒；自洽伪造-错 pin→拒（`FC_PIN_MISMATCH`）；正确 pin→接受；另试 2 个破坏尝试（pin 类型畸形/缺失 pin 字段）→必须 fail-closed；核对威胁边界声明与实现一致；**并检验宽读法边界**（如"文本+hash+pin 同时伪造"在已声明的威胁边界内如何呈现——如实记录，若超裁决范围按 diss ent/escalation 机制写清）。
4. Advisory 闭合核验（A1-A6 逐条）：ADV-1 mode 记录；ADV-2 有界 tick 正例；ADV-3 cwd 固定证据；ADV-4 修复记录工件；ADV-5 措辞（grep 无被禁派生字段消费）；ADV-6 gitignored 路径扫描证据。
5. 回归：原 15 负例 fail_closed_code 精确；四类交付字段分离；frozen_protections 不减少；TASK_PROMPT 与 `runs/T5/_dispatch/loop_a_prompt_t5_v2.md` 逐字节比对；G1 每个 `.md` rc=0；无裸 PASS、无越级；usage 零声明与探针计数自洽。
6. 对抗面：fresh-delivery 模拟是否真从交付态重建；`scratch/reproduction/` 两条 v1 复现件对照成立；写入边界（含 gitignore 视野）。

## 输出（重复硬性要求）
只输出四块：`=== FILE: REVIEW.md ===`、`=== FILE: review_receipt.json ===`、`=== FILE: ACCEPTANCE_PROPOSAL.json ===`、`=== END ===`；块与块之间不加多余分隔符；review_receipt.json 含（review_id="T5R-02"、task_id="T5"、reviewer/runtime、reviewed_artifact_sha256（≥12 件含 sha256/字节/mode）、recomputed、checks、calls、refused_commands、reviewer_side_effects_disclosed、unverified、verdict）；ACCEPTANCE_PROPOSAL.json 含（decision/blocking_items/advisory_items/scope/justification/dissent/next_steps）。registry/state 由收口者更新；不得进入 T6。
