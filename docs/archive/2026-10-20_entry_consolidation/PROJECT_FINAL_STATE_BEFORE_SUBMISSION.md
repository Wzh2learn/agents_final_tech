# PROJECT FINAL STATE BEFORE SUBMISSION

> Evidence record only. Current routing is `docs/research/README.md`; this file
> is not a competing project or research entry.

> date: 2026-10-13 | owner: Loop D | status: `FROZEN_FOR_SUBMISSION_PREP / PENDING_OWNER_ACTIONS`
> 版本锚点：本文件所在提交即冻结版本；用 `git log -1 --oneline -- PROJECT_FINAL_STATE_BEFORE_SUBMISSION.md` 取哈希。LOCAL = origin/main = GB10（tree hash 一致）。2026-10-13b：Loop C 独立复核交付；TAT-QA WP-0 A1–A6 闭合（见 `docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`、`docs/research/WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`）。

## 1. 当前版本（canonical）

| 资产 | 路径 | 状态 |
|---|---|---|
| 稿件（科学内容为准） | `paper/saner_rene_manuscript_v1.md` | FROZEN（A1–A7 + 三类 reviewer 表达加固已落实） |
| 投稿包 | `paper/overleaf_bundle/`（tex + bib + 3 图资产 + 已编译 PDF） | 9 页 / 0 overfull / 自包含 |
| Claim 边界 | `paper/saner_rene_claim_matrix_v1.json` | C1–C3 已按裁决重写；15 条证据哈希 exact |
| Scope lock | `paper/saner_rene_manuscript_scope_lock_v1.md` | 标题/thesis/贡献/允许 claim 已同步 |
| Abstract 注册包 | `research/positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md` | 标题+摘要为新版；余 owner 项 |
| Venue 要求 | `paper/SANER_RENE_2027_REQUIREMENTS.md` | primary-source 核实记录 |
| 投稿清单 | `docs/research/SUBMISSION_READY_CHECKLIST_v1.md` | 10 项 PASS |
| 机器审计 | `scripts/pre_submission_audit.py` | `PRE_SUBMISSION_AUDIT = PASS` |
| 独立审计记录 | `docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md` | v2 CONDITIONAL → 9 项修复 → v3 items/claim PASS；一处单字图注按审计裁定修复并双端复验 |
| 匿名 artifact（备而未发） | `research/artifact_release_2026/` | 12 项就绪 + 2 项 GB10 数据体 |

## 2. 已完成事项

- **科学修订 A1–A7**（依据 `SANER_SCIENTIFIC_ADJUDICATION_v1.md`）：结构等价与校准退化拆分（A2 BLOCKING）、non-direct 部分信息（A1）、OCR 良性吸收披露（A3）、两类比较拆分 4/7（A4）、谓词有定义（A5）、经验范围收窄（A6）、availability 事实校正（A7）。数字、证据来源、冻结结果零改动。
- **表达加固（三类 reviewer adversarial review）**：负结果可引用句（W1）、动机句移到 scope 之后（W2）、摘要后果句阻断三种naive over-reading（W3）。
- **投稿包重建与审计**：tex/bundle/PDF 重生成；`pre_submission_audit.py` 四组（evidence / anonymisation / format / artifact）PASS；引用 21/21；禁语 0；metadata 匿名。
- **Artifact 准备**：manifest（含 sha256）+ 组装脚本 + 发布门清单，未发布。
- **WP-0**：资格报告（`SOURCE_INSUFFICIENT`）、候选分析（排序/许可/gap/最小设计）、入口包。
- **治理**：`memory/THREADS.md` 888KB→170KB 归档；父目录 scratch 归档到 `_archive_2026-10-11/`；`.gitattributes` 固定哈希敏感文件；双周 `memory-hygiene` 自动化。

## 3. 未完成事项（明确的缺口，不得声称已完成）

| 缺口 | 性质 | 影响 |
|---|---|---|
| 真独立 Loop C 复核 | **已交付（2026-10-13）** | 经设计 launcher：v2 CONDITIONAL → 9 项残留全修复 → v3：items PASS / claim boundary PASS；一处单字修复按裁定落实并双端机器复验（`LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`） |
| 匿名 artifact 发布 | owner | 数据体在 GB10；许可范围未签；URL 未建立 |
| 作者信息 | owner | 共同作者顺序/通讯作者未定；camera-ready 才恢复署名 |
| 语言终审 | **已完成（2026-10-13，模型执行终审）** | 14 处语法/习语/标点修正（纯表达层，零数字/claim 变化）；重编译 + 全量审计 PASS；人类母语通读仍可选 |
| RENE precedent 全文 | 未做 | 仅读 abstract（IEEE 付费墙），已登记 camera-ready 待办 |
| Stage D / Stage R | 未闭合 | 与本投稿无关，不构成前置 |

## 4. Owner decisions（仅这四类需要你）

1. **匿名 artifact 是否发布**（外部发布 + 不可逆）
2. **标题最终措辞**（当前 T1；T2/T3 一行切换）
3. **venue 最终拍板**（SANER RENE 默认）
4. **WP-0 来源族选择**（TAT-QA / MultiHiertt = 许可复核；SEC EDGAR = 新数据采集，需另授权）

## 5. 禁止修改事项（冻结护栏）

- 不改任何冻结数字：96/118、0/13、2,382、0.375、1.000、0.3333、0.6667、0.1667、89/89、112/118、75/95、20/95、以及 Appendix A 的历史记录。
- 不改证据来源与哈希绑定；不改 split/join、分母、阈值、tie 规则、权重。
- 不把 post-hoc/exploratory 结果改标为确认性结果。
- 不恢复已关闭路线：Route B、FinQA binding、PR-03（含任何 metric/baseline/runtime 优化）。
- 不新增实验、不新增数据采集、不启动 Memory/SFT/DPO。
- 不改 claim 边界（`saner_rene_claim_matrix_v1.json`）除非有新的作者级裁决。
- 独立复核已交付（记录：`docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`）；不得超出该记录表述（一处单字修复按审计方裁定落实，无第三次模型复核）。
- 不执行注册/投稿/上传（owner 触发）。

## 6. 入口顺序（下一位模型）

1. 本文件（冻结状态与护栏）
2. `docs/research/SUBMISSION_READY_CHECKLIST_v1.md`（投稿前 10 项）
3. `docs/research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md`（资格面 + §12 落实与独立复核记录）
4. `paper/saner_rene_claim_matrix_v1.json`（claim 权威）
5. `docs/research/RENE_ADVERSARIAL_REVIEW_v1.md` + `RENE_REVIEWER_RISK_SIMULATION_v1.md`（审稿防御）
6. WP-0：`docs/research/WP0_ENTRY_PACKAGE_v1.md` → `WP0_QUALIFICATION_REPORT_v1.md`（§10）→ `docs/research/WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`
