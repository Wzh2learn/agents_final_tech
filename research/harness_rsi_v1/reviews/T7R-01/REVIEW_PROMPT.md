# Loop C 独立评审任务 T7R-01：harness_rsi_v1 T7 R 独立验收与回滚（本卡唯一 1 次强评审名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T8。

## 输出格式（硬性，先读；不按此格式 = 评审作废）
你的全部 stdout 会被机械抽取。**必须且仅**输出四个标记块，顺序固定；不要任何前言/总结/结语/额外说明段落：
=== FILE: REVIEW.md ===
=== FILE: review_receipt.json ===
=== FILE: ACCEPTANCE_PROPOSAL.json ===
=== END ===

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T5 v3 @115f396、T6 @ef5e84e 已验收（T5R-04、T6R-01）。
- 被审对象：T7 run `research/harness_rsi_v1/runs/T7/20261015T025839Z_c94af776/`（58 文件；已提交 `0579b64`；`build_manifest.py`/`execute_t7.py`/`self_check.py` 交付 mode 100755，其余 644）。
- 声称：**NO_PROMOTION**——A-1 修正已在任何评估前完成，但候选 `cand-d44c49dec4d95741` 在已授权 T5 v3 闭合操作词表内无法执行其"缺必需收据块"策略 → `NOT_EVALUABLE`；配对重放 T1 v3 16 案 + T4 基线 11 检查×2 轮 22/22 一致；回滚演练 PASS（恢复 T5 v3 @115f396，行为一致、11 件旧证据哈希不变）；集合义务如实（selection_set=NOT_BUILT、sealed=NOT_APPLICABLE_UNRESOLVED、封存访问 0）；模型调用 0（1 强评审名额留给本评审）。
- 上下文：T6R-01 ADVISORY-1 为该候选设了前置条件（评估计划须区分合法 UNRESOLVED 与真缺失；Loop D 裁决把修正折叠为 T7 内的候选修正记录 A-1）。

## 必读（只读）
`cards/T7.md`、`reviews/T6R-01/`（ADVISORY-1 全文与 next_steps）、T6 包与 T5 v3 包、T7 全文（receipt/summary/pilot_acceptance/paired_replay/rollback_receipt/candidate_amendment_A1/amended_candidate/evaluation_fixtures/scratch 含 a1_diagnostic 与 baseline_replay）。

## 工具约束
- 白名单不含 git、mkdir、cp、mv、rm、chmod 等；git 被拒时用替代（字节派生 blob SHA-1、`.git/index` 解析 mode）；被拒命令如实记录。
- scratch 只放仓库外（例：`/home/testuser/wzh/loop_runs/t7r01_recheck_a/`）；不得在被审 run 或仓库内写任何文件；直接 import 用 `python3 -B`；评审结束自扫交付树（含 gitignored 视野）并披露，避免 OMC/pycache 类残留（历史已知问题）。
- 不替包修任何东西。

## 必须独立复算（记录命令与退出码）
1. 计数/哈希/模式：58 文件；manifest 57 条（字段 `sha256_file`）逐条复算；3×755 三层一致（worktree/index/HEAD）。
2. **NO_PROMOTION 合法性（核心）**：独立核验"候选在授权词表内不可执行"的事实——读 amended_candidate.json 与 T5 `registered_operations.json`，验证所需操作确实不在已授权词表中且无等价的已登记组合；自行构造 ≥1 个替代实现尝试（在 scratch）确认无法在词表内表达 E-03 语义；若你能证明存在被忽略的可行路径 → 如实升级报告。核验六硬门逐项判定的诚实性（严重漏检=UNRESOLVED_NOT_EVALUABLE、证据完整性=FAIL 的归因是否准确，READ 'review_packet.md' 与 pilot_acceptance.json 细节）。
3. **A-1 修正充分性**：对照 T6R-01 ADVISORY-1 的四项要求逐条核验（拆分 a/b；合法 UNRESOLVED 不入 severe；不折算；再锚定或理由）；复核 evaluation_fixtures 两个诊断件与 scratch/a1_diagnostic/* 日志（两轮一致）；确认修正先于任何候选评估（时间线/mtime + 记录顺序）。
4. **回滚演练**：复算 rollback_receipt——candidate_state → restored_parent 与 T5 v3 @115f396 原件逐件一致（字节/模式）；父行为 before/after `ACCEPTED_WITHIN_SCOPE`；11 件旧证据的 git blob/SHA-256/bytes/mode 独立复算不变；rollback_drill/restored_parent 三件（caller_validator/recipe_interfaces/registered_operations）与 T5 v3 原件比对。
5. **配对重放抽查**：T1 16 案身份逐案一致；T4 基线 11×2=22/22 退出码；抽查 ≥3 案记录与 T4 v2 baseline 数据一致；T5 父配方 validator 结果复现。
6. **A1/A2/A3/A-common + 纪律**：A1（六硬门+修复漏检或成本比较——NO_PROMOTION 分支下如实）；A2（回滚）；A3（措辞：不得把收尾审计写成实验/科学成功）；G1（.md 逐个 rc=0；跳过项如实）；写入边界含 gitignore；修复记录（2 次 attempt）一致；TASK_PROMPT 与 `runs/T7/_dispatch/loop_a_prompt_t7.md` 逐字节；usage：0 编排调用 + 强评审名额说明；execution_chat=UNRESOLVED。（注：Codex 运行时可能出现自有模型列表刷新日志；非编排调用，如实提及即可。）
7. 新对抗探针（≥1）：如尝试在 scratch 里构造"词表内等价实现"或"被忽略的已登记操作组合"以挑战 NOT_EVALUABLE 结论；或复算证据去重/集合义务声明。

## 输出（重复硬性要求）
只输出四块；块间不加多余分隔符。review_receipt.json 含（review_id="T7R-01"、task_id="T7"、reviewer/runtime、reviewed_artifact_sha256（≥12 件含 sha256_file/bytes/mode）、recomputed、checks、calls、refused_commands、reviewer_side_effects_disclosed、unverified、verdict）；ACCEPTANCE_PROPOSAL.json 含（decision/blocking_items/advisory_items/scope/justification/dissent/next_steps）。registry/state 由收口者更新；不得进入 T8。
