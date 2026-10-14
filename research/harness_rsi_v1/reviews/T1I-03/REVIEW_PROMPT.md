# Loop C 复审任务 T1R-03：harness_rsi_v1 T1 v3（T1R-02 残余项返工核验）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立复审；不修改任何文件、不 git 写、不联网、不调端点/服务/数据库、不进入 T2。输出只写 stdout。

## 背景
- 你对 T1 v2（run 20261014T134731Z_5d8b9400）给出 REJECTED：唯一残余缺陷 = `source_refs[].sha256_worktree` 信息字段自身携带"检出表示域"，2/33 与本树不符（`positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json` ×2），违反 A-common 语义。
- 执行者交付 **T1 v3**：`research/harness_rsi_v1/runs/T1/20261014T141004Z_2647a7e1/`（16 例；supersedes v2 与 v1）。改动=移除 `sha256_worktree`（仅留 canonical git_blob_id）、E7 描述更新、supersedes/prior_review 指针改 v2、schema 字符串升 v3、summary 抬头。

## 必读（只读）
`cards/T1.md`、`reviews/T1R-02/{REVIEW.md, review_receipt.json, ACCEPTANCE_PROPOSAL.json}`、v1/v2/v3 三个 run 包、被引真源。

## 必须独立复算
1. v3 六件产物 vs manifest；run 目录恰 7 件；receipt.input_bindings 9/9 实算。
2. **残余项核验**：`incidents.jsonl` 中 `sha256_worktree` 出现次数必须为 **0**；每 ref 仅含 `{path, exists, tracked, sha256_canonical, sha256_canonical_domain}`；33/33 `sha256_canonical` == `git rev-parse HEAD:<path>` 实算；E7 描述与 method 一致且覆盖"单一声明域"。
3. **最小改动核验**：v3 与 v2 的差异是否**仅限**上列意图项——建议用程序化 diff（如逐行比较：把 v2 incidents 中 worktree 键剔除后与 v3 比较应逐例等价；矩阵/分组除 schema 串与生成时间外等价）。
4. **不动项**：六族覆盖、三类 expected_category、24/24/24 仅构建计划、无 sealed、B0 零调用、写入边界（`git show --name-only` 本提交）。
5. 回归抽验（≥3 例）：INC-11/12/13 与 CTRL-01 的被引真源关键串仍在；INC-06 三源互证仍成立。
6. 反证尝试：任何错误归因/过度陈述/声明哈希失配/越界写入/伪造。

## 硬性约束
只读；不 git 写；不联网；不调端点/服务/数据库；不进入 T2。避免 `find -exec` 与 `$(...)`。被拒命令如实记录。

## 输出（仅 stdout；三块标记；块之间不要多余分隔符）
=== FILE: REVIEW.md ===
=== FILE: review_receipt.json ===
=== FILE: ACCEPTANCE_PROPOSAL.json ===
=== END ===

（REVIEW.md 含：范围；逐项结果；残余项裁定；最小改动 diff 结论；回归；发现（若有）；FACT/INFERENCE/UNVERIFIED；判定与理由。两个 JSON 按此前格式：reviewer/runtime、reviewed_artifact_sha256（v3 七件 + T1 卡 + T1R-02 三件）、recomputed、checks、calls、unverified、verdict；提案含 decision/scope/justification/dissent。）
重申：只写提案；registry/state 由收口者更新。