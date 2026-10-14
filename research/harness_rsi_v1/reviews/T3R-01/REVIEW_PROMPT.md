# Loop C 独立评审任务 T3R-01：harness_rsi_v1 T3 可信执行与计数（本卡唯一 1 次 Loop C 评审名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改仓库内任何文件（被审 run 包与仓库均只读）、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T4。输出只写 stdout（三块标记，见文末）。

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T-1/T0/T1/T2 已验收（T2R-01=ACCEPTED，blocking=0）。
- Loop A（task `t3-trusted-exec`，rc=0）已交付 T3 run：`research/harness_rsi_v1/runs/T3/20261014T161814Z_245b86ab/`（234 文件；manifest 233 条、自不含）。
- Loop A 已完成"完成前自检"（receipt.self_check：A1/A2/A3/A-common PASS；含两处修复记录 `issues_found_and_fixed`，保留证据在 `qualification_work/PASS_1*`）。
- 你的职责：独立复算 + 反证尝试，输出提案（ACCEPTED/REJECTED/PENDING_HUMAN_REVIEW）。registry/state 不由你写。不进入 T4。

## 必读（只读）
`cards/T3.md`、`contracts/{protocol.json,authority_map.json,execution_policy.md,budget_profiles.json,schemas.json}`、run 全文：先读 `receipt.json`、`summary.md`、`runner_qualification.json`、`permission_matrix.json`、`runner/README.md`、`runner/runner.py`、`runner/run_qualification.py`，再抽查 `qualification_work/`、`events.jsonl`、`artifacts_manifest.json`、`TASK_PROMPT.md`。

## 工具约束与已知环境事实（先读，避免撞墙）
- 你的命令白名单不含 git、mkdir、cp、mv、rm、chmod；git 命令会被拒。被拒命令如实记录并改用替代方法（见下）。禁止用 shell 重定向写 /tmp（会被拒）。
- 需要写 scratch 时：只用 `python3` 调用脚本，scratch/output 放仓库外（例：`/home/testuser/wzh/loop_runs/t3r01_recheck_a/`），不得在被审 run 目录或仓库内创建/修改任何文件。如实披露你创建的全部仓库外路径。

## 必须独立复算（记录命令与退出码）
1. **run 目录计数**：`find research/harness_rsi_v1/runs/T3/20261014T161814Z_245b86ab -type f | wc -l` 应为 234；manifest 233 条（`self_hash_excluded=true`），逐条 SHA-256/字节实算一致；磁盘无遗漏、无多余（scope 以 manifest 声明为准）。
2. **input_bindings 8 条**：git CLI 被拒时用双方法——(a) 字节派生 git blob SHA-1（`blob %d\0`+内容，python3）；(b) 解析 `.git/index` 对应条目（或 .git 对象库交叉验证）。对 `TASK_PROMPT.md` 用 sha256 实算。核对 5 个 contracts + T2 receipt + T2R-01 review_receipt + TASK_PROMPT 与声明一致；核对 `protocol_freeze_check` 与 FROZEN 值一致。
3. **实跑资格（核心）**：用 python3 在仓库外新 scratch 连跑两遍（自分派 pass-id）：
   `python3 research/harness_rsi_v1/runs/T3/20261014T161814Z_245b86ab/runner/run_qualification.py --pass-id LOOPC_A --output <scratchA>/result.json --scratch-root <scratchA>/scratch`
   （第二遍换 `LOOPC_B`/scratchB）。要求：32/32、exit 0、stderr 空、两遍 `normalized_result_sha256` 一致，且**等于**声明的 `0a5963625b637945eaf91610ea3505b7f9b94f4ae2039b265cd149dde8163ed2`。再抽查 `PASS_1_FINAL`/`PASS_2_FINAL` 的 scratch `run_summary` 与 checks 明细，重算两轮 mock transport 分项（14 次：failed/timeout/manual_retry/success/crash）与声明一致。
4. **A1/A2/A3/A-common 逐条核验 + 拒绝面复核**：
   - A1：duplicate_id（exit 2、sentinel 不变、无 run_summary）；crash（exit 4、`request.json`+`crash.json` 保留、INCOMPLETE、crashed=1）；overwrite（preexisting 保留、无 request.json、`overwrite_rejection.json`、计数=1）。建议自行在 scratch 复现关键 case。
   - A2：budget 无旁路（cap=0 仍 transport → exit 5、`transport_calls=0`、`budget_rejection.json`；另自查 runner.py 是否存在绕过 `check_budget` 的路径）；monotonic_counts（`count_history` 单调、失败/超时/手动重试/崩溃全计数）；policy_denied（outside path/network/sealed/production/database 各拒 + 证据文件）；split_accounting（`model_extra_requests` 与 `execution_chat_usage` 分账，UNRESOLVED 不为 0）；persist_before_call（`'x'` 独占、事件顺序 `request_persisted → transport_called`）。
   - A3：LOCAL_DEV_HOST 标注存在，且 GB10 权威绑定/OS 级隔离未声称（runner、qualification、permission_matrix、summary 一致）。
   - 对抗探针（建议；可在 scratch 内构造）：路径穿越 `../` 探测被拒；未知 action type → exit 4 + `unexpected_crash.json`（fail-closed）；未知 policy category 被拒；非法 run_id → exit 6；grep `runner.py` 无 socket/requests/urllib/http 导入；确认 qualification 脚本真实通过 subprocess 执行 runner（非自证）。
5. **披露一致性**：`issues_found_and_fixed` 两处修复与 `qualification_work/PASS_1`、`PASS_1_RETRY`、`PASS_2_FINAL` 证据一致；`_dispatch/loop_a_prompt_t3.md` "早 58 秒、未被修改"的说法可核（mtime 对比）；`execution_policy.json` vs `.md` 命名披露属实。
6. **写入边界与零调用**：run 窗口的仓库内 mtime 扫描——除该 run 目录与既有 `logs/graph` 脏件外无其他新写入；`events.jsonl`/receipt 的零 network/model/production/db/training/remote 声明无相反证据；无伪造 ACCEPTED/freeze/PROMOTED/SCIENTIFIC_PASS（`acceptance_status=UNREVIEWED`、`activation_status=NOT_ENABLED`、三轴正确）。
7. **包自检核对**：receipt.checks 的 20/20 打包自检中，至少重算：JSON/JSONL 全可解析、manifest 完备性、二轮一致性、LOCAL 标注、allowlist、写入边界。

## 反证重点（防自验自证）
- 资格脚本会不会"只输出预设 PASS"？检查 checks 的断言是否来自实际执行结果（exit code、磁盘证据、计数重算）而非常量自证；指出任何"测试与实现同一来源"的循环。
- `permission_matrix` 的 allowlist 声明与 `ensure_path_allowed` 实际实现域是否一致；POLICY_ONLY/非 OS 沙箱免责声明是否完整。
- 发现分 BLOCKING（须修复后重审）/ADVISORY（不影响验收、收口层登记）两类，各附证据与建议；ADVISORY 按 T2R-01 风格附升级条件（若升 BLOCKING 只需重审的最小范围）。

## 输出（仅 stdout；三块标记；块间不要多余分隔符）
=== FILE: REVIEW.md ===
（Markdown：范围与方法；逐项结果（含命令/退出码证据）；实跑复算证据；BLOCKING/ADVISORY 发现；FACT/INFERENCE/UNVERIFIED 分离；对 T3 的判定与理由）
=== FILE: review_receipt.json ===
（JSON：review_id="T3R-01"；task_id="T3"；reviewer/runtime；reviewed_artifact_sha256（T3 关键文件 9 件 + `cards/T3.md` + `protocol.json`，含 sha256 与字节）；recomputed（run 计数/manifest/bindings/freeze/两遍复跑 hash/14 次分项/披露核对/写入边界）；checks（逐条 PASS/FAIL/ADVISORY）；calls（review_session_calls=1；network/services/db/model=0；token UNRESOLVED；本地复跑命令计数如实）；refused_commands；reviewer_side_effects_disclosed（仓库外 scratch 路径）；unverified；verdict（decision + blocking/advisory 计数 + does_not_grant））
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；blocking_items；advisory_items；scope；justification；dissent（含内部备选裁量与理由）；next_steps）
=== END ===

重申：只写提案；registry/state 由收口者更新；不得进入 T4；不得修改任何已评审包。
