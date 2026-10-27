# Loop D Knowledge Closeout

Date: 2026-10-27, Asia/Shanghai
Status: `PAUSED_AFTER_CONDITIONAL_C_REVIEW`

## Impact

This closeout separates completed engineering evidence from unresolved
scientific claims. It prevents the internally rendered Word draft from being
mistaken for submission-ready output and prevents the D/T/M comparison from
being mistaken for a binding-mechanism result.

## Fact Surfaces

| Surface | Status | Evidence |
|---|---|---|
| Code | `changed-and-verified` | Scoring V3, persistent budget, Word source/conversion and 12/12 Scoring-V3 tests are present; focused suites passed |
| Runtime | `verified-local-only` | GB10 Qwen3-4B generation and LibreOffice rendering occurred; no production or external service was used |
| Documentation | `changed-and-verified` | `LOOP_D_RESEARCH_PROMPT.md`, `memory/STATE.md`, `memory/THREADS.md`, `docs/research/README.md` and this return carry one current account |
| Rules | `verified-current` | Parent/project `AGENTS.md` and thin `CLAUDE.md` pointers remain applicable; no rule change was needed |
| Memory | `changed-and-verified` | Project STATE/THREADS/DECISIONS updated; platform-generated memory remains read-only |
| Workspace | `pending-local-untracked-only` | GB10 research-branch conflicts were resolved and pushed at `c644cb4f5`; local and GB10 `main` were synced at `481b87ce` before the handoff commit. The research branch and `main` are divergent from merge-base `9c92d4cfc` (`main`-only 4 / research-only 7). The untracked local `paper_e_word/` has 38 same-name branch mirrors plus 85 unique debug/historical renders; it is not a whole-directory duplicate. Historical GB10 worktrees remain preserved |

## Current Scientific State

1. Paper E has a 14-page internally rendered Word/PDF draft and 24 numbered
   references, but C found submission-grade defects: a missing sixth checklist
   step, fused table/list structure, incomplete table numbering/captions, and
   bibliography/citation ordering defects. Status is
   `INTERNAL_RENDER_ACCEPTED_WITH_DEFECTS`, not submission-ready.
2. Scoring V3 is confirmed for the three paired-control families and pure
   rescore. Old V2 results remain historical and are not natural error rates.
3. The eight-family panel is valid as
   `SAME_SOURCE_NEW_TABLE_FAMILIES`; it is not cross-source or
   pretraining-disjoint.
4. The D/T/M mechanism effect is not identified. Arm membership is perfectly
   confounded with 512-token output-budget exhaustion. `M` did not receive a
   fair trial, so neither `STOP_M` nor a method gain is justified.
5. The persistent ledger is structurally valid. Accounting is 27 physical
   reservations, 24 persisted raw rows, 25 reported generate calls with an
   independently supported range of 24-25, and 46,054 consumed input+output
   tokens. One discarded generation is asserted by a hardcoded fault recorder,
   not instrumented at runtime.

For Windows checkout compatibility, 24 generation receipt filenames were
renamed from `D:<uid>.json`, `T:<uid>.json` and `M:<uid>.json` to the matching
`D_<uid>.json`, `T_<uid>.json` and `M_<uid>.json` forms in commit `2b51ae607`.
File contents were unchanged.

## Resource State

- A/C collaboration: `28/28`, exhausted.
- This stage consumed 27 physical reservations and 46,054 input+output
  tokens; training, judge, paid API, service and production calls were zero.
- Conservative global remainder after this stage: 377 physical generation
  attempts and 2,543,008 generation tokens. Training remains
  `2 runs / 3,680,052 tokens` but is not authorized by this closeout.
- A scientifically valid D/T/M rerun requires a new explicit budget and a
  24-call panel with output limits above the observed truncation point.

## Cleanup Candidates - Not Deleted

- Local untracked `research/word_scoring_new_family_20261027_v1/paper_e_word/`:
  38 same-name files mirror the pushed research branch and 85 files are unique
  debug/historical renders. Keep the entire directory until each class is
  reviewed; only the mirrored class is a potential removal candidate.
- GB10 historical worktrees:
  `decision_residual_worktree_20261026`,
  `next_research_stage_worktree_20261026`,
  `phase_b_worktree_20261026`,
  `publication_proxy_calibration_worktree_20261026`,
  `adaptive_mechanism_worktree_20261027`.
  Preserve until their unique evidence and branch merge status are reviewed.
  `word_scoring_new_family_worktree_20261027` is the current research evidence
  worktree, not an additional historical cleanup candidate.
- Local visualization temp projects `paper_e_compile_20261027` and
  `managed_paper_e_20261027` outside the repository. These are rebuildable
  compile attempts and can be removed after user confirmation.

## Security Pending

The changed-document scope passed a secret-shape scan. A read-only whole-tree
scan separately detected credential-shaped material in the ignored `.env`
carrier. Values were not copied into project documentation. The file was not
modified or deleted. The owner must decide whether the credentials are live,
rotate them if necessary, and choose a secure storage/cleanup path.

## Next Decision

Choose one path before any new experiment:

1. Paper E first: fix the four Word blockers and non-blocking bibliography/
   caption issues, then prepare Owner submission fields.
2. Mechanism first: request a new 24-call, higher-output budget and rerun the
   frozen D/T/M panel under unchanged Scoring V3.

No further research, generation, submission or cleanup is authorized by this
closeout.

## 新对话交接

更新：2026-10-27，Asia/Shanghai
状态：`HANDOFF_READY / PAUSED_AFTER_CONDITIONAL_C_REVIEW`

### 1. 当前状态、完成项与边界

- 已完成：Word 路线形成 14 页内部渲染 DOCX/PDF；Scoring V3 通过三类配对
  控制；8 UID / 8 table family 的曝光与冻结可追溯；D/T/M 各 8 条 raw
  已真实执行并持久化；持久预算 guard、故障记录和跨机渲染收据已保存。
- 尚未完成：Paper E 仍有 checklist、表格/列表、表图编号/标题和书目排版
  缺陷，**尚非投稿终稿**。D/T/M 三臂与 512-token 输出截断完全共线，
  **不能判断 M 或 binding 机制有效或无效**。新 24-call 高输出重跑尚未执行。
- 待授权：Paper E 作者/单位/通讯、AI 披露、artifact/DOI 公开、正式投稿、
  付款、展示及学校认定；任何新 A/C 派发、模型生成、训练或新增预算。
- 凭据状态：`HISTORICAL-CREDENTIAL-CARRIERS / UNPROCESSED`。只记录忽略的
  `.env` 存在凭据形状内容，未读取、未复制、未修改、未删除。

### 2. 新对话最少必读

仓库根目录：`D:/AIRcommend/JinRongAgents/agents_final_tech`。
标注 `research branch` 的文件当前位于
`research/word-scoring-new-family-20261027`，固定 commit
`c644cb4f57f24c943b469cda5a6fea3b8a105db8`；当前 `main` 工作树可能不含这些
文件，可用 `git show c644cb4f:<repo-relative-path>` 读取，或在获准的工作树中
检查该分支，不要误判为证据缺失。

| 顺序 | 用途 | 准确路径 |
|---|---|---|
| 1 | 唯一现役指令与暂停状态 | `docs/research/LOOP_D_RESEARCH_PROMPT.md` |
| 2 | D 交接入口与科学边界 | `research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md` |
| 3 | A 实作报告 | `research/word_scoring_new_family_20261027_v1/A_RETURN.md`、`A_RETURN.json`（research branch） |
| 4 | C 独立审阅 | `research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md`、`TASK_RESULT_C.json`（research branch） |
| 5 | 原始生成与重评结果 | `research/word_scoring_new_family_20261027_v1/generation/results/RAW_RESPONSES.jsonl`、`RAW_EXTRACTION_RECEIPT.json`、`scoring_v3/results/DIAGNOSTIC_ROWS.jsonl`、`DIAGNOSTIC_SUMMARY.json`（research branch） |
| 6 | 当前预算收据 | `research/word_scoring_new_family_20261027_v1/generation/GENERATION_RECEIPT.json`、`INTERFACE_FAULT_RECEIPT.json`（research branch） |
| 7 | 外部持久账本 | GB10 `/home/testuser/wzh/research_runs/persistent_budget/word_new_family_20261027/ledger.jsonl`，receipt 记录 SHA256 `c7bd1f7207b610ad17c194727a8d0affdb0105996ed2e97603cfeea408ca71ac` |
| 8 | 历史聚合账本 | `research/publication_thesis_goals_v1/RESOURCE_LEDGER.json`；保持与本轮独立账本分列 |
| 9 | Paper E 内容主源 | `research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex`，由 `research/word_scoring_new_family_20261027_v1/paper_e_word/CONVERSION_MANIFEST.json` 标为 canonical source |
| 10 | Paper E Word 源与产物 | `research/word_scoring_new_family_20261027_v1/paper_e_word/paper_e_word.md` 为原始抽取源，`paper_e_word_fixed.md` 为转换派生源，`paper_e.docx` 与 `rendered_final/paper_e.pdf` 为内部渲染产物（research branch；本地另有未跟踪副本） |

Hash 口径补充（2026-10-27）：manifest 中的 SHA256 按 Git 原始 blob
字节计算。Windows 工作树对文本文件做 CRLF 转换后，`Get-FileHash` 或
`git hash-object` 可能不同；例如 `paper_e_sncs.tex` 的 raw Git blob 为
`f1993042...`，Windows 工作树为 `008c4749...`。`git show <commit>:<path> |
sha256sum` 与 manifest 一致，Word 源、转换派生源、DOCX 和 PDF 的核心 blob
也一致。后续身份核对应以 raw Git blob 或 manifest SHA256 为准，不把 CRLF
表示差异误判为内容漂移。

Artifact identity is a multi-receipt chain: `CONVERSION_MANIFEST.json` binds
the canonical TeX and Word input source, while `D_WORD_RENDER_RECEIPT.md`
binds `paper_e_word_fixed.md`, `paper_e.docx` and `rendered_final/paper_e.pdf`.
`validation/ARTIFACT_HASHES.json` still contains 24 pre-`2b51ae607`
`generation/receipts/D:<uid>.json`-style paths. Do not rerun that manifest
literally without applying the recorded D/T/M receipt rename map.

### 3. Git 与工作区

- `main`：本次交接前已核实本机、GitHub、GB10 均为 `481b87ce66b8`；本次
  交接文字形成新的 containing commit，精确终态以 `git rev-parse HEAD` 和
  `git rev-parse origin/main` 为准。
- 研究分支：`research/word-scoring-new-family-20261027` 在 GB10 与 GitHub
  均为 `c644cb4f57f24c943b469cda5a6fea3b8a105db8`，冲突已解决并保持 clean。
- 本地未跟踪副本：`research/word_scoring_new_family_20261027_v1/paper_e_word/`。
  保留原位，不删除、不迁移、不强行合并；后续先比较其与 research branch 的
  hash 和独有 debug/render 文件。
- GB10 历史 worktree 保留原位：
  `/home/testuser/wzh/decision_residual_worktree_20261026`、
  `/home/testuser/wzh/next_research_stage_worktree_20261026`、
  `/home/testuser/wzh/phase_b_worktree_20261026`、
  `/home/testuser/wzh/publication_proxy_calibration_worktree_20261026`、
  `/home/testuser/wzh/adaptive_mechanism_worktree_20261027`、
  `/home/testuser/wzh/word_scoring_new_family_worktree_20261027`。
- 本地临时项目保留原位：
  `C:/Users/王中华/.codex/visualizations/2026/10/17/01a148ab-31ed-7163-a3e4-ef4188f7c215/paper_e_compile_20261027`、
  `C:/Users/王中华/.codex/visualizations/2026/10/17/01a148ab-31ed-7163-a3e4-ef4188f7c215/managed_paper_e_20261027`。

### 4. 协作与资源

- A/C 协作：`28/28`，已耗尽；没有剩余派发额度。
- 本轮物理预留：`27`；持久 raw：`24` 行；报告的真实 generate call：`25`，
  独立可支持范围为 `24-25`。
- 本轮消耗：`46,054` input+output tokens；训练、judge、付费 API、服务/端点、
  生产调用均为 `0`。
- 保守全局余额：`377` 次物理生成、`2,543,008` generation tokens。原 36 次
  子预算还剩 9 次预留，但不足以执行 C 要求的 24-call 高输出重跑。
- 历史训练状态仍为 `2 runs / 3,680,052 training tokens`，本交接不授权追加
  训练。历史 80/48 事故和 340-token 差额继续原样保留。
- 在新的明确授权前：不派发 A/C，不调用模型，不训练，不投稿，不付款，不公开，
  不做外部联系，不清理或迁移上述现场。

新对话应从本节开始，先核实 research branch 证据可读取、本地未跟踪副本的
身份，以及 Paper E 内容主源到 Word 产物的 raw Git blob hash 链；随后才选择
修 Paper E 或申请新 D/T/M 预算。

## 独立 Loop C 交接复核与 D 回应

独立 C 以零对话上下文复核了交接，结论为“可接续但证据归位未完全闭环”。
D 已独立确认其三项关键发现：

- `main` 与 `research/word-scoring-new-family-20261027` 从
  `9c92d4cfc` 分叉，当前分别为 `b487a9b5` 与 `c644cb4f`；后者不是最新
  `main` 的后代，新对话必须显式读取两边。
- 本地 `paper_e_word/` 为 123 个文件，其中 38 个与研究分支同名镜像、
  85 个是额外 debug/历史渲染，不能整目录称为冗余。
- `2b51ae607` 将 24 个冒号 receipt 路径改为 Windows-safe 路径；旧
  `ARTIFACT_HASHES.json` 的 24 个键尚未更新，属于已知映射债。

D 对 C 的两项判断作边界修正：GB10 会话清理结果已在本对话中由 D 实测
复核（OpenCode 0、A/C 进程 0、备份 `SHA256SUMS` PASS），因此对当前现场
不是“未验证”；`loop_runs` 保留 205 MB 日志与 sidecar session 清理也不
矛盾，前者是科研证据，后者是已完成 QA/eval 会话。

D 采纳的架构建议：Loop D 保持主脑；Loop A/C 演化为有边界的独立 Agent，
不作为加载全局上下文的大型工具。A 只接隔离实作，C 只接固定快照独立审查；
机械校验交给确定性脚本。所有主/子 Agent、工具调用、重试和生成必须统一
记账。具体上下文上限属于治理建议，不是实测阈值。

新 Loop D 的第一项工作是证据归位与授权核对：确认 4/7 分叉、38/85 文件
分类、24 个 receipt 改名映射和 raw hash 链；随后再按 Paper E 优先或申请
新 D/T/M 预算二选一。

## GB10 陈旧对话清理回执

日期：2026-10-27，Asia/Shanghai。用户已在候选报告后明确授权归档和清理。

- Loop A/C 一次性任务均已终态，活动 tmux 和 `codex exec` / `claude -p`
  进程为 0；`word-scoring-new-family-a/c-20261027` 及 Phase B A/C 均保留
  `done` status/log，不做删除。
- 3 份 Codex rollout、1 份 Codex history、1 份 Claude transcript 已从活动
  目录移至 GB10
  `/home/testuser/wzh/backups/agent_conversation_cleanup_20261027/`，
  `SHA256SUMS` 全部校验通过；Claude project memory 未移动。
- OpenCode sidecar QA/eval session 清理前 50 条，使用项目
  `scripts/opencode_session_cleanup.py --purge-all` 删除 50 条，清理后为 0；
  清理前元数据保存在同目录 `opencode_sessions_before_cleanup.json`。
- `coding-jinrong`、`graph-loop-b`、`opencode-serve`、`thinking-proxy`、
  `vllserve` 保持运行。`/home/testuser/wzh/loop_runs` 的 191 份 status
  和约 205 MB 日志作为科研证据原位保留。
