# Loop C 复审任务 T1R-02：harness_rsi_v1 T1 v2（T1R-01 返工核验）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立复审：不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T2。输出只写 stdout。

## 背景
- 你（同角色）此前对 T1 v1（run 20261014T132249Z_99f3bc6b）给出 **REJECTED**（F1–F8 + 必改①②③④⑤ / 建议⑥⑦⑧ / 不动清单）。
- 执行者已交付 **T1 v2**：`research/harness_rsi_v1/runs/T1/20261014T134731Z_5d8b9400/`（7 件；16 例）。v1 保留不删；v2 receipt 记录 supersedes_run_id。
- 你的职责：独立核验返工是否落实、且未破坏"不动"部分；给出提案（ACCEPTED/REJECTED/PENDING_HUMAN_REVIEW）针对 v2。

## 必读（只读）
`cards/T1.md`、`evaluation/reliability_spec.md`、`reviews/T1R-01/{REVIEW.md, review_receipt.json, ACCEPTANCE_PROPOSAL.json}`、v1 与 v2 的 run 包、被引真源文件。

## 必须独立复算
1. v2 六件产物 vs manifest；run 目录恰 7 件；v2 receipt 的 input_bindings（9 条）实算一致。
2. **返工核验（逐项）**：
   ① INC-11 的 ref 是否为 `research/tatqa_wp0_2026/wp2/LOOP_C_S4C_QUAL_AUDIT_v1.md` 且该文含"投递缺口/未注入采样上下文"关键串；
   ② INC-12/13 的 ref 是否指向 `research/positive_repair_20261011/{POSITIVE_REPAIR_REGISTRY_v1.json, ROUND1_CLOSEOUT_v1.md}` 且含 `ENGINEERING_DISPATCH_FAILURE` 与 `PR-01/PR-04/PR-07`、`Zero POSITIVE / NULL / NEGATIVE` 等关键串；CTRL-01 是否指向 `docs/research/stage_e_matched_fpr_reanalysis_v1.md` 且含 `NOT_IDENTIFIABLE`；
   ③ 全部 source_refs 的 `sha256_canonical`（git_blob_id）是否 = `git rev-parse HEAD:<path>` 实算（逐条）；`sha256_worktree` 是否 = 本树实算；
   ④ INC-13 `observed_fact` 是否含"第一轮"限定与"PR-03 v3 属另一轮"说明；
   ⑤ INC-07 是否补引 `bridge_v2/offline_qualification.py`（第 266 行 `processor(logits, input_ids)` 可验证）与 INCIDENT_2；CTRL-02 是否补引 `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`（含 `FAILED_TRANSFER` 与"下游 res/answer 未重算"）；
   ⑥ INC-12 是否已并入 `G-REPAIR`（并与 INC-13 同组）；
   ⑦ `receipt.E7` 描述是否覆盖哈希域且与 method 一致；
   ⑧ 每例是否新增 `applicability` 字段且与 `expected_category` 分列。
3. **不动项复核**：六族覆盖、三类 expected_category、24/24/24 仅构建计划、无 sealed、B0 零调用、写入边界（git show --name-only a8c036e84）是否仍成立。
4. **回归核验**：v1 中被判"支撑"的 10 例（INC-01/02/03/04/05/06/08/09/10/14）在 v2 中的断言是否仍与其被引件一致（可抽验 3-5 例）。
5. 反证尝试：是否仍有错误归因/过度陈述/声明哈希失配/越界写入/伪造。

## 硬性约束
全程只读；不 git 写；不联网；不调端点/服务/数据库；不进入 T2。避免 `find -exec` 与 `$(...)`（注入防护）；被拒命令如实记录。

## 输出（仅 stdout；三块标记，机器逐字转写；**不要在三块之外添加多余分隔行**）
=== FILE: REVIEW.md ===
（Markdown：范围；逐项结果与命令；F1–F8 返工逐条裁定（已修/未修/部分）；回归结论；发现（若有）；FACT/INFERENCE/UNVERIFIED；对 v2 的判定与理由）
=== FILE: review_receipt.json ===
（JSON：reviewer/runtime；reviewed_artifact_sha256（v2 七件 + T1 卡 + T1R-01 三件）；recomputed；checks；calls（自身会话 1；network/services/db 0；token UNRESOLVED）；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；reviewed_artifact_sha256；scope；justification；dissent）
=== END ===

重申：只写提案；registry/state 由收口者更新。