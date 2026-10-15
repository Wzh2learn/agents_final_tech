# Loop C 独立评审任务 T8R-01：harness_rsi_v1 T8 R 受控影子边界执行（本卡强评审名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T9。

## 输出格式（硬性，先读；不按此格式 = 评审作废）
你的全部 stdout 会被机械抽取。**必须且仅**输出四个标记块，顺序固定；不要任何前言/总结/结语/额外说明段落：
=== FILE: REVIEW.md ===
=== FILE: review_receipt.json ===
=== FILE: ACCEPTANCE_PROPOSAL.json ===
=== END ===

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T5 v3 @115f396、T6 @ef5e84e、T7 @0579b64 均已验收（T5R-04、T6R-01、T7R-01）。
- 被审对象：T8 run `research/harness_rsi_v1/runs/T8/20261015T041717Z_669349f1/`（12 文件；已提交 `f5da2a7`；**DELIVERY_FULL_SET_755**：全集 12 件交付 mode 100755）。
- 声称：影子状态 `NOT_SATISFIED_NO_THREE_TASK_WINDOWS`（0/3 窗口；逐任务表留空标 NOT_EXECUTED_MISSING_APPROVED_WINDOW）；身份复合组 `sha256:e16cde27ff239da0c7b76f35272e0950e1cb9f0878d464b0ae6629e88d4c4f86`（T5 45/45、T6 30、T7 57 成员）；安装/装载 `NOT_ESTABLISHED_NOT_INFERRED_FROM_REPOSITORY`；回滚 `PASS_SIMULATED_ONLY`；release_proposal=仅建议（启用/分发保留给用户 §7）；usage 0/6、0/2、零外呼。
- Owner 门（被审包自述）：① 三个新获批任务窗口缺；② 启用/分发属用户裁决。

## 必读（只读）
`cards/T8.md`、`MASTER_PLAN.md`（T8 与三任务措辞）、`state/` 与 `registry/` 相关记录、T7/T7R-01、T6/T6R-01、T5 v3、T8 全文（receipt/summary/shadow_comparison/release_proposal/rollback_receipt/self_check_result/events）。

## 工具约束
- 白名单不含 git、mkdir、cp、mv、rm、chmod 等；git 被拒时用替代（字节派生 blob SHA-1、`.git/index` 解析 mode）；被拒命令如实记录。
- scratch 只放仓库外（例：`/home/testuser/wzh/loop_runs/t8r01_recheck_a/`）；不得在被审 run 或仓库内写任何文件；直接 import 用 `python3 -B`；结束时自扫交付树（含 gitignored 视野）并披露。
- 不替包修任何东西。

## 必须独立复算（记录命令与退出码）
1. 计数/哈希/模式：12 文件；manifest 11 条（hash 字段名以实际为准）逐条复算；**全集 755 三层一致**（worktree/`.git/index`/HEAD tree，12/12）。
2. **NOT_SATISFIED 边界诚实性（核心）**：对照权威来源核验"三个新获批任务窗口=0"（卡 `execution_authorized=false`、MASTER_PLAN、registry/state 记录）；**独立搜索**当前授权范围内是否存在被遗漏的可用"新任务窗口"（如有 → 如实升级）；核验没有把可做的工作也标成未满足（identity/rollback/proposal 均已完成）；逐任务表确实为 null/未执行、无伪造痕迹；影子协议的完备性（窗口要素、记录字段、回归停用规则、回滚保持）是否足以直接承接真实窗口。
3. **身份绑定**：独立重算复合组 sha256（应为 `e16cde27…`）；核对 T5 @115f396（45/45）、T6 @ef5e84e（30）、T7 @0579b64（57）成员组与各 commit 下实际树一致；T6/T7 候选哈希与 ACCEPTED 评审记录一致。
4. **A2/A3**：安装态/装载态声明不推断；无安装/装载/全局配置改动（写入边界含 gitignore 视野）；旧证据零改（11 件基线抽查）；零越权请求与 usage 0/6-0/2。
5. **回滚**：复核 `PASS_SIMULATED_ONLY` 语义与哈希恢复证据（base→shadow→base）；确认未触碰共享件。
6. **release_proposal**：仅建议、无启用、无分发；§7 保留条款措辞与卡一致；建议内容无越权的"已就绪即可启用"暗示。
7. **A1/A-common/G1/纪律**：自检汇报与独立实测一致；G1 2 个 .md rc=0；TASK_PROMPT 逐字；修复记录；三轴；FULL-SET 755 策略的内部一致性与对外影响（如：数据文件可执行的副作用，如实记 advisory 或确认无碍）。
8. 新对抗探针（≥1）：如尝试构造一个"在授权范围内可视为真实新任务窗口"的候选并检验其成立性；或检验 0/3 表被误读为结果的可能。

## 输出（重复硬性要求）
只输出四块；块间不加多余分隔符。review_receipt.json 含（review_id="T8R-01"、task_id="T8"、reviewer/runtime、reviewed_artifact_sha256（≥8 件含 sha256/bytes/mode）、recomputed、checks、calls、refused_commands、reviewer_side_effects_disclosed、unverified、verdict）；ACCEPTANCE_PROPOSAL.json 含（decision/blocking_items/advisory_items/scope/justification/dissent/next_steps）。registry/state 由收口者更新；不得进入 T9。
