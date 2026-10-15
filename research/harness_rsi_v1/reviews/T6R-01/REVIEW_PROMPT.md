# Loop C 独立评审任务 T6R-01：harness_rsi_v1 T6 有界提案与统一档案（本卡唯一 1 次 Loop C 评审名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T7。

## 输出格式（硬性，先读；不按此格式 = 评审作废）
你的全部 stdout 会被机械抽取。**必须且仅**输出四个标记块，顺序固定；不要任何前言/总结/结语/额外说明段落：
=== FILE: REVIEW.md ===
=== FILE: review_receipt.json ===
=== FILE: ACCEPTANCE_PROPOSAL.json ===
=== END ===

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T5 已验收（T5R-04 @115f396）；T4 v2 已验收（T4R-01）。
- 被审对象：T6 run `research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/`（31 文件；已提交 `ef5e84e`；`archive_implementation/{archive.py,self_check.py}` 交付 mode 100755，其余 644；GB10 工作树按 umask 渲染后由 closer 校正为精确 755——与 T5 同模式，供参考）。
- 声称：archive 机制（父内容组、失败缓冲、选择性导出、证据去重）；候选 2 条记录 = 1 条真实提案（证据交付对象；3 条目，其中 1 条标注"需未来授权"）+ 1 条故意重复包被 `REJECTED_DUPLICATE_NOGOOD`（not enabled）；额外模型请求 0/4；零网络；G1 全绿。

## 必读（只读）
`cards/T6.md`、`meta/optimizer_policy.md`、T5 v3（@115f396）与 T4 v2 包、T5R-04、T6 全文（receipt/summary/candidate_index/candidate_packages/archive_implementation 全部含 fixtures 与 demo_outputs/repair_attempts）。

## 工具约束
- 白名单不含 git、mkdir、cp、mv、rm、chmod 等；git 被拒时用替代（字节派生 blob SHA-1、`.git/index` 解析 mode）；被拒命令如实记录。
- scratch 只放仓库外（例：`/home/testuser/wzh/loop_runs/t6r01_recheck_a/`）；不得在被审 run 或仓库内写任何文件；披露全部仓库外路径；你自己的直接 import 用 `python3 -B` 或 `PYTHONDONTWRITEBYTECODE=1`（避免 pycache 残留），评审结束自扫交付树（含 gitignored 视野）。
- 不替包修任何东西。

## 必须独立复算（记录命令与退出码）
1. 计数/哈希/模式：31 文件；manifest 30 条逐条 SHA-256+bytes+mode；2×755（archive.py/self_check.py）与 28×644 在 worktree/index/HEAD 三层一致。
2. **archive 机制实弹复跑（核心）**：按 `archive_implementation/README.md` 用法在 scratch 重跑：父组校验（T5 v3=45 成员、T4 v2=64 成员，均 PASS）、重复包拒绝（`REJECTED_DUPLICATE_NOGOOD`、`activation_enabled=false`）、选择性导出（不复制完整父包/完整档案）、证据去重（raw 6 / unique 5 / duplicate pair 1）。逐项与 demo_outputs 对照。
3. **A1 逐候选核验**：`cand-d44c49dec4d95741`（真实提案）与 `cand-20a78eae4dda3ca9`（拒绝样例）各自可定位：父版本（内容寻址）、改动（3 条目）、评价计划、成本；条目只引用 T5 registered_operations 的 op_id（2 条现存 + 1 条"需未来授权"标注且未改动任何共享件）；问题选择 rationale 与证据出处一致（如涉 T1-INC-14，核对与 T1 v3 案例内容一致性；rationale 弱则记 advisory）。
4. **A2 对抗**：自造 ≥3 个攻击——（a）复制被拒候选改 ID 重投（内容去重是否仍拒？机制与语义如实记录）；（b）"条件重开"路径（新父组/新证据条件下允许重开——验证机制可行使且不误放行）；（c）试图把被拒候选置 enabled=true → 必须失败；另抽查跨方向引用去重计数的正确性（同证据多引用只计一次）。
5. **A3/预算**：usage 0/4 便宜、0 强、零网络/远程/生产/数据库/训练/daemon/Loop B；C/S 机制"可复用但未运行其批次"的证据。
6. **回归与披露**：card §6 A1/A2/A3/A-common 全项；G1（4 个 .md rc=0）；TASK_PROMPT 与 `runs/T6/_dispatch/loop_a_prompt_t6.md` 逐字节；8 条 repair_attempts 与 repair_record 一致；写入边界（含 gitignore 视野）；三轴 DELIVERED/UNREVIEWED/NOT_ENABLED；候选全部未启用。
7. 新对抗探针（≥1）：如篡改候选包字段后 index/校验的行为（fail-closed？）。

## 输出（重复硬性要求）
只输出四块；块间不加多余分隔符。review_receipt.json 含（review_id="T6R-01"、task_id="T6"、reviewer/runtime、reviewed_artifact_sha256（≥12 件含 sha256/bytes/mode）、recomputed、checks、calls、refused_commands、reviewer_side_effects_disclosed、unverified、verdict）；ACCEPTANCE_PROPOSAL.json 含（decision/blocking_items/advisory_items/scope/justification/dissent/next_steps）。registry/state 由收口者更新；不得进入 T7。
