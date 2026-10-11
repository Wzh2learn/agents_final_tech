# PROJECT_CLOSEOUT_AND_HANDOFF_v1.md

> date: 2026-10-11 | owner: Loop D | scope: SANER Route A submission package + Track P closeout + repo governance
> HEAD at closeout: see `git rev-parse HEAD` (this file is committed in the same commit). LOCAL = origin/main = GB10.
> 本文件是 fresh-session 的第一入口；细节状态见 memory/STATE.md，未决事项见 memory/THREADS.md，导航见 docs/INDEX.md。

## 1. 当前项目真实状态

- `PRIMARY_ROUTE = SANER Route A`（submission type = `RENE: NegativeResult`）。
- `SUBMISSION_DRAFT_COMPLETE = YES`。已编译 PDF、页面数已核验、引用已解析、图已目视验证、匿名化与 PDF metadata 审计 PASS。
- Venue：SANER 2027 RENE 为默认（advisor 正在参与最终 venue 决策；只读 portability note 已备）。
- H1 = PARTIALLY_RESOLVED（第一作者 王中华 已定；共同作者顺序/通讯作者待导师回复）；H2 = CLOSED。
- Track P 已收束：PR-03 v3 = NEGATIVE，Evidence Ladder = LEVEL_0，无第四轮 recovery；spillover audit = CLEAN。
- 运行环境：GB10 为唯一正式运行/验证环境；LOCAL 负责文本/git/静态审计；当前三端已对齐。

## 2. 已成立的核心结论（可引用）

- Visibility、detection、harmfulness 是三个不同 measurement objects（construct separation）。
- Stage E：95 tables / 118 injections / 96 visible；OCR-like `0/13` across 11 clusters（frozen scored surface）。
- Single-responsive-leaf：flat 与 hierarchical 为 positive affine/rank transform（slope 0.375, Spearman 1.0）；clean-only matched-FPR operating point `NOT_IDENTIFIABLE`（2,382 clean rows）。
- Multi-leaf：72 clusters / 216 injections；full vector 1.0、direct codebook 1.0、non-direct 0.3333（tie 0.6667）、majority baseline 0.1667、any-response 0.0 → 结论是“显式 stage-aligned instrumentation 提供可分 signature”，不是 hierarchy 产生 localization。
- FinQA second flow：V=89/89、D=0/89、O=0/89 → `MEASUREMENT_OBJECT_MISMATCH`（failed transfer，不是 protocol blindness）。
- FORBIDDEN（不得写入）：hierarchy localizes failures；universal blind spots；FinQA confirms protocol blindness；causal-aware checkpoint selection validated。

## 3. 分支台账（避免误用旧结果）

| 分支 | 状态 |
|---|---|
| SANER Route A（submission） | ACTIVE |
| Route B（automatic causal checkpoint-selection MVP） | CLOSED / STOP_BRANCH |
| Track P positive repair portfolio | CLOSED（0 genuine positives；LEVEL_0） |
| PR-EXP-01 / PR-EXP-04 / PR-EXP-07 | FROZEN（NOT_EVALUABLE / INVALID）；不再重启 |
| PR-EXP-03 round-1 (v2) | INVALID gate provenance / NOT_EVALUABLE；其 metrics/receipt 标 SUPERSEDED_FOR_SCIENTIFIC_INTERPRETATION |
| PR-EXP-03 v3 | NEGATIVE；CLOSED；manuscript_role = DECLINE_CITE；不得进入稿件 |
| FinQA binding / governance 问题 | CLOSED；不重开 |
| Stage D / Stage R | 未闭合，但不是 Route A 的前置 |

## 4. Canonical 资产（唯一入口）

| 需要 | 权威路径 |
|---|---|
| Venue 官方要求 | `paper/SANER_RENE_2027_REQUIREMENTS.md` |
| Claim 边界（唯一权威） | `paper/saner_rene_claim_matrix_v1.json` |
| Scope lock | `paper/saner_rene_manuscript_scope_lock_v1.md` |
| Manuscript 源文件（科学内容以此为准） | `paper/saner_rene_manuscript_v1.md` |
| 投稿 bundle（tex + bib + figures + 已编译 PDF） | `paper/overleaf_bundle/` |
| 已验证引用 | `paper/saner_rene_references.bib` + `research/positive_repair_20261011/reference_verification_v1.md` |
| 图（hash 绑定） | `docs/research/figures_saner/` + `figure_source_binding_manifest.json` |
| 版面审计 | `research/positive_repair_20261011/PDF_LAYOUT_AUDIT_v1.md` |
| Abstract 注册包 | `research/positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md` |
| Track P registry | `research/positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json` |
| PR-03 spillover audit | `research/positive_repair_20261011/PR03_SPILLOVER_AUDIT_v1.md` |
| PR-03 v3 结论 | `research/positive_repair_20261011/PR-03_v3_RESULT_v1.md` |
| Venue portability（只读） | `research/positive_repair_20261011/VENUE_PORTABILITY_NOTE_v1.md` |
| 匿名 artifact 发布计划（未执行） | `research/positive_repair_20261011/ANONYMOUS_ARTIFACT_RELEASE_PLAN_v1.md` |

## 5. Human-only blockers

- **H1**：共同作者顺序与通讯作者（导师确认）。
- **Venue**：最终 venue 决策（SANER RENE 为默认；CAIN/ICST 为候选）。
- **匿名 artifact URL**：投稿前建立匿名库并做去匿名测试。
- **正式流程**：abstract 注册（10/19 AoE）与 submission（10/23 AoE）必须由 owner 触发；本仓库不得自动提交。

## 6. 已知技术债

- **Subagent/harness**：本 session 多次出现 spawned agent 未收到任务（role leak / no-task delivery），导致 Loop C 独立审计与 Loop A 委派不可靠。当前策略：可委派但必须自行复核输出；关键审计由 Loop D 直接完成并标注为 self-audit。
- **Track P round-1 lineage**：冻结的 v2 实现不可执行（`a1_table` shadowing bug），其 diagnostic bootstrap 计算上不可行；已 supersede，保留仅为 provenance。
- **Build**：编译产物有 196 个 cosmetic underfull \hbox（不影响版面）；Figure-3 图内 status labels 未渲染（caption 已承载 identity，环境缺字体）。
- **memory/THREADS.md**：约 900 KB、起点为 [10-09]，需在下一次 neat pass 做归档裁剪（历史条目转入 archive/）。
- **Windows EOL**：6 个 tracked 文件存在 CRLF stat churn，已在 closeout 提交中刷新。

## 7. 后续研究从哪里继续

1. **最近一步（非科研）**：owner 完成 H1 与 venue 决策 → 填匿名 artifact URL → 10/19 注册 abstract → 10/23 投稿。
2. **若要继续 Track P 科研**：PR-04-R（generalization，contract 修复点已知）或 PR-01 v3（checker 修复点已知）；两者都需要一个可靠的 Loop A 委派，且不得影响 submission package。
3. **明确不要重开**：Route B、FinQA binding、PR-03（含任何 metric/baseline/runtime 优化）。
4. **若 venue 改判**：先读 `VENUE_PORTABILITY_NOTE_v1.md`，再决定 reframe 工作量；不要先改稿。