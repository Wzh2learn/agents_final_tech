# PROJECT_CLOSEOUT_AND_HANDOFF_v1.md

> date: 2026-10-12 (final neat closeout) | owner: Loop D | scope: SANER Route A submission package + Track P closeout + repo governance
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
| Loop C 审计结果（self-audit） | `research/positive_repair_20261011/LOOP_C_SELF_AUDIT_v1.md` |
| 证据完整性校验器（4 组） | `scripts/verify_claim_evidence.py` |
| 陈旧文件扫描（结论：无需动作） | `research/positive_repair_20261011/STALE_ARTIFACT_SCAN_v1.md` |
| 父目录归档 | `../_archive_2026-10-11/README.md` |
| 匿名 artifact 发布计划（未执行） | `research/positive_repair_20261011/ANONYMOUS_ARTIFACT_RELEASE_PLAN_v1.md` |

## 5. Human-only blockers

- **H1**：共同作者顺序与通讯作者（导师确认）。
- **Venue**：最终 venue 决策（SANER RENE 为默认；CAIN/ICST 为候选）。
- **匿名 artifact URL**：投稿前建立匿名库并做去匿名测试。
- **正式流程**：abstract 注册（10/19 AoE）与 submission（10/23 AoE）必须由 owner 触发；本仓库不得自动提交。

## 6. 已知技术债（2026-10-11 第二轮治理后）

- **已解决：memory/THREADS.md 体积**。888 KB -> 170 KB；日期 <= 09-30 的 202 条按块字节级原样移入 `memory/archive/THREADS_archive_pre_2026-10-01.md`（守恒式：条目 276 = 202 + 74；块字节 908906 = 735658 + 173248）。
- **已解决：Figure 链的跨主机 EOL 漂移**。新增 `.gitattributes`（`docs/research/figures_saner/*.{svg,json,csv} -text`），并用 blob 字节重写了 5 个受影响的文本资产；现在 fig1/fig2/fig3 + manifest 在 LOCAL 与 GB10 的 sha256 完全一致。
- **已改善：PDF underfull**。196 -> 63（表格 p-column 改为 `>{\raggedright\arraybackslash}`）；overfull 保持 0，页数仍为 8。剩余 63 条均为 cosmetic（主要是 artifacts/hash 段落与短末行），不影响版面。
- **已澄清（非债务）：Figure-3 图内 status labels**。经核对 `stage_e_version_b_figure_spec_v1.md`，已批准的 Figure 3 规格只要求两个面板与指定 caption，未要求图内标签；identity 由 caption 承载。判定为可选 polish，不改动冻结图件。
- **未修复（有理由）：figure renderer 的可移植性**。renderer 把自身 sha256 写进输出 metadata，因此任何对 renderer 的修改都会改变图件哈希，属于“重新绑定事件”而非普通修复；已回滚，保持冻结链不动。若未来要重渲染，必须走一次完整的 re-bind + 复核。
- **Subagent/harness**：spawned agent 仍经常收不到任务（role leak / no-task）。委派后必须自行复核；关键审计由 Loop D 直接完成并标注 self-audit。
- **已知小瑕疵**：`figure_source_binding_manifest.json` 记录的 `fig2_source.csv` 哈希（a61d75fd…）与当前 GB10 文件（f788c96a…）不一致。该 CSV 只是 Figure 2 的便利导出，不参与图件渲染或 claim 证据链；保留原样并在此登记，不在投稿前改动。
- **Track P round-1 lineage**：冻结 v2 实现不可执行（`a1_table` shadowing）且 diagnostic bootstrap 计算不可行；已标 `SUPERSEDED_FOR_SCIENTIFIC_INTERPRETATION`，保留 provenance，禁止作为证据。
- **Windows EOL（其余文本资产）**：未纳入 `.gitattributes` 的文本文件在 LOCAL 仍会被规范化；跨主机哈希的权威口径仍是 GB10 raw bytes。

## 7. 后续研究从哪里继续

1. **最近一步（非科研）**：owner 完成 H1 与 venue 决策 → 填匿名 artifact URL → 10/19 注册 abstract → 10/23 投稿。
2. **若要继续 Track P 科研**：PR-04-R（generalization，contract 修复点已知）或 PR-01 v3（checker 修复点已知）；两者都需要一个可靠的 Loop A 委派，且不得影响 submission package。
3. **明确不要重开**：Route B、FinQA binding、PR-03（含任何 metric/baseline/runtime 优化）。
4. **若 venue 改判**：先读 `VENUE_PORTABILITY_NOTE_v1.md`，再决定 reframe 工作量；不要先改稿。
## 8. 依赖/风险债与环境残留（2026-10-11 第二轮治理）

### 外部依赖（不可再分发）
- 语义 judge = Qwen3.6-35B-A3B（Q4_K_M GGUF，127.0.0.1:8004）：第三方权重，引用而非分发；复现需读者自行获取同一模型。
- TeX 工具链不随仓库分发：见 `paper/overleaf_bundle/BUILD_README.md` 的 "Toolchain bootstrap"（tectonic 0.15.0 + sha256），或直接在 Overleaf 编译。
- GB10 是唯一权威运行主机；目前没有第二主机的验证路径（建议未来做镜像 + 二次复算）。

### 父目录 scratch 清理（2026-10-11 已执行）
- 方法：先做全库 token 扫描（1,134 个 repo 文件，排除我自己的盘点文档），区分"被引用的历史证据"与"零引用临时物"。
- **已归档**（移动，非删除）到 `../_archive_2026-10-11/`（自述见其 README.md）：19 个 `_tmp_*`/备份文件 + 8 个零引用目录（`__pycache__`、`_uitmp`、`.workbuddy`、`_stage_e_exec_20261009`、`_overnight_20261010`、`_review_skills_loop_engineering`、`_mcp_out`、`_r1_staging`）。
- **原地保留**（repo 文档仍以文本引用，移动会破坏引用）：`_evidence_strengthening`(58)、`external_stage_d_repro`(54)、`hbkeyan`(36)、`skills-loop-engineering`(21)、`harness_audit_20260905`(14)、`side_backups`(11)、`advisor_send_0826`(5)，以及低引用但含 provenance 的 `_cleanup_backup_20260812`、`_finqa_v2_preresult_freeze`、`_framecheck`、`_rehearsal_files`、`_repair_portfolio_20261011`、`agents_final_tech_test`。
- 注意：本 session 的执行策略禁止删除（连单文件 `Remove-Item` 都被拦），因此采用"归档"而非"清除"；这同时也是对 provenance 更安全的选择。

### 仍未完成清单（诚实记录）
| 项 | 状态 | 说明 |
|---|---|---|
| 独立 Loop C 复核（PR-03 v3 / 溢出审计 / 投稿包） | **已交付，但为 self-audit** | 委派三次全部失败（无输出/卡住），按用户指示由 Loop D 亲自执行：`LOOP_C_SELF_AUDIT_v1.md`，A/B/C 三项 = PASS，且全部为当场机械取证（symtable 证明 shadowing、实测 3.63s×40,000≈40.3h vs 记录 275s、零污染扫描、PDF 文本抽取核验）。**非独立**：真独立复核仍待委派通道恢复后按 packet 执行 |
| PR-03 v3 的 diagnostic bootstrap CI | **不可得** | 冻结 `predict_loco` O(groups^2) 使其计算不可行；结论为点估计判定 |
| claim↔evidence 校验覆盖面 | **已扩展** | `scripts/verify_claim_evidence.py` v2 覆盖 4 组：claim matrix(15) + 图件绑定(20) + 引用一致性(21/21) + prereg pin；`WIDE_EVIDENCE_CHECK = PASS`。仍未覆盖：PDF 正文内数字与 manifest 的逐条对应 |
| preflight v2 | **仅规范** | 已升级为 12 项，但既有实验不会追溯满足；下次实验才生效 |
| precedent 全文核对 | **未做** | 仍停在 abstract 级（IEEE 付费墙）；已登记为 camera-ready 待办 |
| 语言润色（native pass） | **已完成** | 美式拼写统一（localisation→localization 3 处、organisation→organization 2 处）+ 5 处破折号语法修正；重建 tex/bundle/PDF 后仍 8 页 / 0 overfull；所有数字未变。见 `PDF_LAYOUT_AUDIT_v1.md` 的 Language pass 节 |
| memory 维护自动化 | **已完成** | 已创建双周 heartbeat automation `memory-hygiene`：自动检查 THREADS 体积/条目年龄、超阈值则按块字节级归档、校验 STATE/side_handoff/INDEX 的 canonical 路径、扫 repo 与父目录的 scratch、运行证据校验器；无事静默 |
| 单点权威主机（GB10） | **未缓解** | 无镜像 / 无第二主机复算路径；已在依赖清单登记 |
| 父目录剩余非引用物 | **已判定保留** | 见上；不再动 |
