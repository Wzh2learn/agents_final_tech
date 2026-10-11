# Loop C Independent Audit — SANER Route A Reviewer-Attack Claim Audit (Track A item 2)

You are the independent Loop C auditor. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Deliverable = an independent reviewer-attack claim audit for the SANER Route A manuscript. Judge only from this packet; missing evidence -> UNVERIFIED.

## Scope and rules
- Object: the frozen SANER claim set and its evidence boundaries (scope lock, claim matrix, manuscript draft, readiness, risk register, language audit, Version-B proposal below).
- Task: for EACH claim, (a) is the packet evidence sufficient as stated; (b) state the strongest reviewer attack; (c) is the current claim/limitation boundary sufficient, or must wording be narrowed; (d) any forbidden-language or overreach anywhere in the packet.
- Do NOT propose new experiments; do NOT edit any file; do NOT invent evidence or citations.
- Report the 5 most dangerous reviewer attacks overall with recommended pre-prepared responses grounded ONLY in the packet.
- Flag any claim that should be declined (not citable in Route A) and any claim whose manuscript role should be bounded to future work.

## Required output format
## INDEPENDENCE DECLARATION
## PER-CLAIM TABLE (claim id | evidence sufficiency FACT/INFERENCE/UNVERIFIED | strongest attack | minimum required wording change or NONE | manuscript role: cite/bound/decline)
## TOP-5 REVIEWER ATTACKS + PRE-PREPARED RESPONSES
## FORBIDDEN-LANGUAGE / OVERREACH SCAN
## FINDINGS (ordered by severity)
## VERDICT: ENDORSE_CLAIM_SET | ENDORSE_WITH_NOTES | CHALLENGE_CLAIM_SET
## RESIDUAL RISKS / NEXT ACTION
End with the literal line: REVIEWER_AUDIT_COMPLETE

--- BEGIN paper/saner_rene_manuscript_scope_lock_v1.md ---# SANER RENE Manuscript Scope Lock v1

> Status: `FROZEN_SCOPE_NOT_PAPER_BODY`
> Primary route: `A`
> Optional route: `B / READ_ONLY_48H_QUALIFICATION`
> Manuscript hard freeze: `2026-10-20 18:00 Asia/Shanghai`

## Tentative Title

**Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation**

## One-Sentence Thesis

Long-horizon evaluation validity depends on auditing the observation surface itself: controlled perturbations expose family-specific visibility blind spots, hierarchy alone does not guarantee diagnosability, and cross-dataflow transfer fails when visibility and detection measurement objects are not causally aligned.

## Frozen Contributions

1. **Construct separation and observation boundaries.** Separate visibility, detection and harmfulness, quantify family-level visibility and report the OCR-like `0/13` boundary.
2. **Structural identifiability and instrumentation.** Show that single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent and that clean-only matched-FPR equality is not identifiable; show that explicit stage-aligned instrumentation, not hierarchy alone, produces the controlled localization signal.
3. **Measurement-object alignment and failed transfer.** Treat FinQA v2 as a failed-transfer autopsy caused by measurement-object mismatch, and use NIST/TEVV construct-validity language to motivate auditing observation surfaces.

## Allowed Claims

- Controlled evaluator surfaces can hide some defect families while exposing others.
- Visibility, detection and harmfulness are different constructs.
- OCR-like injections were invisible in the frozen Stage E surface: `0/13` across `11` table clusters.
- Single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent in the current construction.
- Clean-only matched-FPR equality is not empirically identifiable when clean score support is zero.
- Explicit stage-aligned instrumentation can produce separable controlled signatures; non-direct leaves do not establish emergent localization.
- FinQA v2 demonstrates a failed transfer/measurement-object mismatch, not protocol blindness.
- NIST motivates evaluation of metric and TEVV effectiveness; it does not certify this project's metrics.

## Forbidden Claims

- Universal blind spots across AI systems.
- Hierarchy localizes natural failures.
- Visibility-detection separation universally transfers across dataflows.
- FinQA confirms protocol blindness.
- A causal-aware checkpoint-selection method has been validated.
- Automatic checkpoint/oracle generation or complete causal discovery.
- Semantic process correctness or harmfulness beyond the stated equivalence contract.
- Stage D/C4 training or PRM performance claims.

## Core Evidence Table

| Claim | Evidence | Status |
|---|---|---|
| 95 tables / 118 injections; 96 visible | `docs/research/stage_e_118_quantification_v1.md` | frozen |
| OCR-like `0/13` across 11 clusters | `docs/research/stage_e_zero_event_uncertainty_note_v1.md` | frozen |
| Family visibility profile | `logs/graph/eval/checkpoint_discrimination_tables_v2.json`, `t2_visibility_sensitivity.json` | frozen |
| Affine/rank equivalence and matched-FPR non-identifiability | `docs/research/stage_e_matched_fpr_reanalysis_v1.md` | frozen |
| Multi-leaf controlled signatures | `docs/research/stage_e_multileaf_result_packet_v1.md` | construct-sensitive |
| Direct-codebook ablation | `docs/research/stage_e_multileaf_signature_ablation_v1.md` | negative/boundary |
| FinQA failed transfer | `docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md`, `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md` | autopsy/design boundary |
| NIST/TEVV framing | `docs/research/nist_measurement_validity_ledger_v2.md` | motivation only |

## Figure Definitions

### Figure 1 — Measurement chain

`NIST / long-horizon motivation -> controlled failure -> checkpoint visibility -> protocol detection -> outcome/harm`

Purpose: explain why final correctness cannot establish observation validity.

### Figure 2 — Defect family × visibility

Rows: six Stage E families. Columns: threshold/visibility surface. Include `0/13` OCR-like boundary and family rates.

### Figure 3 — Instrumentation and measurement-object boundary

Panel A: multi-leaf full/direct/non-direct ablation (`1.0 / 1.0 / 0.3333`).  
Panel B: FinQA failed-transfer boundary (`V=89/89`, `D=0/89`, `O=0/89`) labelled `MEASUREMENT_OBJECT_MISMATCH`, not protocol blindness.

## Role Boundaries

- **FinQA:** failed-transfer autopsy and causal-alignment requirement.
- **Multi-leaf:** controlled evidence for stage-aligned instrumentation and the hierarchy-alone limitation.
- **NIST:** measurement-validity motivation and TEVV effectiveness framing.
- **ITIL:** at most one motivation paragraph on lifecycle governance and continual improvement.

## Limitations

- One frozen public tabular corpus and synthetic controlled perturbations.
- Limited mutation mechanisms; no natural-failure distribution.
- Harmfulness is equivalence-dependent.
- FinQA transfer failed because measurement objects were not causally aligned.
- No positive causal-aware checkpoint-selection method is claimed.
- Per-stage multi-leaf inference is descriptive at the current sample size.

## Out of Scope

- Stage D training / PRM performance.
- Causal-aware checkpoint selection as a validated contribution.
- Automatic checkpoint or oracle generation.
- Complete causal discovery.
- Natural-failure localization.
- Universal cross-system generalization.

Classification note: the formal result class is `SECOND_FLOW_MIXED`; the scientific interpretation is `MEASUREMENT_OBJECT_MISMATCH`, recorded in `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`.
- **FinQA classification:** formal result `SECOND_FLOW_MIXED`; accepted methodological boundary `MEASUREMENT_OBJECT_MISMATCH` is recorded in `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`.

--- BEGIN paper/saner_rene_claim_matrix_v1.json ---
{
  "schema_version": 1,
  "status": "FROZEN_SCOPE_NOT_PAPER_BODY",
  "primary_route": "A",
  "optional_route": "B_READ_ONLY_48H_QUALIFICATION",
  "hard_freeze": "2026-10-20T18:00:00+08:00",
  "title": "Visibility Is Not Detection: Auditing Observation Boundaries in Long-Horizon AI Evaluation",
  "thesis": "Long-horizon evaluation validity depends on auditing the observation surface itself: controlled perturbations expose family-specific visibility blind spots, hierarchy alone does not guarantee diagnosability, and cross-dataflow transfer fails when visibility and detection measurement objects are not causally aligned.",
  "claims": [
    {
      "id": "C1",
      "claim": "Visibility, detection and harmfulness are distinct constructs and the frozen evaluator has family-specific observation boundaries.",
      "evidence": [
        "docs/research/stage_e_118_quantification_v1.md",
        "docs/research/stage_e_observability_metrics_v1.md",
        "logs/graph/eval/checkpoint_discrimination_tables_v2.json",
        "logs/graph/eval/t2_visibility_sensitivity.json"
      ],
      "allowed": true
    },
    {
      "id": "C2",
      "claim": "Single-responsive-leaf flat/hierarchical scores are affine/rank-equivalent and clean-only matched-FPR equality is not identifiable; explicit stage-aligned instrumentation is required for controlled localization.",
      "evidence": [
        "docs/research/stage_e_matched_fpr_reanalysis_v1.md",
        "docs/research/stage_e_multileaf_result_packet_v1.md",
        "docs/research/stage_e_multileaf_signature_ablation_v1.md"
      ],
      "allowed": true
    },
    {
      "id": "C3",
      "claim": "Cross-dataflow transfer requires causal alignment of measurement objects; the current FinQA v2 result is a failed-transfer/measurement-object-mismatch autopsy, not protocol blindness.",
      "evidence": [
        "docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md",
        "docs/research/finqa_causal_exposure_preregistration_proposal_v1.md",
        "docs/experiments/2026-10-11_loop_c_causal_checkpoint_mvp_design_audit.md"
      ],
      "allowed": true
    }
  ],
  "forbidden_claims": [
    "universal blind spots across AI systems",
    "hierarchy localizes natural failures",
    "visibility-detection separation universally transfers",
    "FinQA confirms protocol blindness",
    "causal-aware checkpoint selection is validated",
    "automatic checkpoint or oracle generation",
    "complete causal discovery",
    "Stage D/C4 or PRM performance"
  ],
  "figures": {
    "figure_1": "NIST/long-horizon motivation -> failure -> checkpoint visibility -> protocol detection -> outcome/harm",
    "figure_2": "six defect families x visibility surface; OCR-like 0/13 across 11 clusters",
    "figure_3": "multi-leaf full/direct/non-direct ablation plus FinQA failed-transfer measurement-object boundary"
  },
  "evidence_hashes": {
    "stage_e_118_quantification_v1.md": "39134a1359cd153175f793e0b1d5ff8ebaed5ee8df8e415a79fcfb42a9ff9084",
    "stage_e_zero_event_uncertainty_note_v1.md": "97ccc92ccd7d31b9c3e37b1d8250d439f21d0e79c251f298254355097a57a5b7",
    "stage_e_matched_fpr_reanalysis_v1.md": "611b2c2f2e2cabf62a007e281fcd999f913df2f4e220474f7d1a31a1ce4bc1e9",
    "stage_e_multileaf_result_packet_v1.md": "99ccc81b92db2d5350aafdefb44ce73ec055ab8e33008e54aed5456ec3d9cbb8",
    "stage_e_multileaf_signature_ablation_v1.md": "4d4961d4eb274ce8adaa786920bbb33c41c5b3be473bcc941380f5fafd089c3d",
    "nist_measurement_validity_ledger_v2.md": "84cb4621b1bde099a9a4c76b04c033eb91cd2af1fe25bbf1b63e3a404a145cec",
    "finqa_formal_v3_recompute_audit.md": "2435b838537c8bdbf5d687fb3b6c71e6db35fc0c06a094915f549c801bdfd3a6",
    "causal_checkpoint_design_audit.md": "7ccc685d466f91299e42b77612f216c74cfda1eeeb60e73c2645a176b1005182"
  },
  "route_b_qualification": {
    "status": "NO",
    "decision": "STOP_BRANCH",
    "reason": "No two execution-confirmed downstream stages with source-local/downstream separation and two genuine mechanisms per stage; current C audit finds M aliasing and R/N downstream non-estimability."
  }
}
        "docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md",
        "docs/research/finqa_v2_formal_v3_activation_record_v1.md",

--- BEGIN paper/teacher_review_readiness_v2.md ---
# 小论文内部送审验收结论（方向校准版 v2）

> 结论日期：2026-09-22
> 判定：**评估子稿可作为导师讨论材料，但不应再被称为完整小论文；不可对外投稿或公开。**

## Latest status: 2026-10-07

- Stage E ready for advisor review.
- Office/PDF visual check: PASS.
- Stage D remains `DATA_NO_GO / RQ2 NOT_IDENTIFIED`.
- Only two advisor decisions remain: multi-leaf versus second dataflow; harmfulness definition selection.


## 送审范围

- 主稿：`paper/teacher_review_draft_v1.docx`
- 可追踪文本：`paper/teacher_review_draft_v1.md`
- 中文说明：`paper/teacher_review_note_v2.md`
- 三阶段总叙事：`paper/research_story_v2.md`
- 三阶段方向 Word：`paper/research_story_v2.docx`
- 总架构图：`paper/figures/fig_evaluate_distill_evolve_v1.svg`
- 主张清单：`paper/claim_manifest_v1.json`
- 机械验收结果：`paper/acceptance_report_v1.json`

## 审稿式检查

| 维度 | 结论 | 依据或剩余边界 |
|---|---|---|
| 评估子稿故事 | 通过 | 问题、方法、结果和限制均围绕“评测协议能否看见缺陷”展开 |
| 用户原始三阶段方向 | 未闭环 | 蒸馏尚无训练结果；规则进化只有机制与受限收益证据 |
| Claim–Evidence 结构 | 静态通过 | 5 条主张、73 项章节/措辞/路径/证据检查；不替代原始数字复算或科研有效性审计 |
| 实验诚实性 | 通过 | matched-FPR 等价、PSO null、门控无显著收益均保留 |
| 表述边界 | 通过 | 不再主张已证明额外定位收益；第二数据流/第二 scorer 明示缺失 |
| 老师阅读形态 | 通过 | Word 结构完整；两份 DOCX 已于 2026-10-03 完成 Office 排版/分页视觉验收并 PASS |
| 对外公开 | 阻塞 | 专利状态尚未由用户确认；作者、单位和目标会议模板未填写 |

## 2026-09-22 阅读核对回执

- 逐段核对英文评估稿、中文说明、总叙事和本判定；推荐阅读顺序：中文说明 → 总叙事 → 英文评估稿，先理解目标与现有证据的区别。
- 已修正文 §5.1 的反向表述：OCR 为 **0/13 可见、13/13 被吸收**；旧静态门只认裸数字，现已改为方向性句子并加负控测试。
- 已按 T1 源码/工件纠正 Table 1 的检测信号，移除从完整树误套的“2 roots / 12 leaves”；补清 96 个可见与 112 个 mapping 文本变化、20 张表与13个单注入不是同一计数。
- 已解释校准 0.5 是历史维均分的 control 汇总差异，不是单 cell 或原始答案的跨 judge 一致率；规则效应补为 15 张碰撞表上的平均配对 ACC 差 0.05（5 个百分点），95% 区间 [0, 0.1056]，仍无显著收益主张。
- 英文稿与方向稿 DOCX 均离线重生成，全文段落/表格与对应 Markdown 比对通过。**本机没有 LibreOffice/soffice，Office 视觉核对未完成**；不声称分页、缺字或表格溢出已验，需在有 Office 的环境打开两份 DOCX 后再确认可发送版本。
- 本地 P1 审计不放行训练：动作 SFT/风险预筛为 DATA_NO_GO，DPO 为仅保留审计素材的 PILOT_ONLY；两者都不是训练许可，详细依据见资产账本 §3.1。

## 已确认与待确认

已确认：三阶段主线、4B 仅训练链 smoke、8B 主学生、小模型不替代确定性门，以及成熟评估稿保底。本地审计已交付；后续实验等待用户批准。

导师/用户仍需确认：主指标和非劣/安全容差、训练窗口及资源预算、专利申请状态与权利要求覆盖。DPO 仅在独立偏好数据门通过时执行，不预设 60 对单向偏好足够。

## 2026-09-22 下一轮计划（历史记录）

本地数据审计和内容核对已交付；当时计划由服务器接手剩余测试、两份 DOCX 的 Office 视觉核对。该 Office 项已于 2026-10-03 关闭；Phase 1a/2、数据补充及训练仍按后续明确授权推进，不因本地缺件判另一服务器资产失败。

24–48 小时内部方向包使用成熟评估稿与当前三阶段说明，不等训练；实验完成后的统一初稿另过证据门。数据不足、简单基线已足够、非劣或安全门失败时按现有计划拆稿，不临时改门救结果。

## 2026-10-03 状态附记

本附记更新上文 2026-09-22 的阶段性判断：两份 DOCX 的 Office 视觉验收已完成并 PASS；当前 claim manifest 为 5 条主张，GB10 `validate_paper_claims` 为 PASS / 74 checks，专用验收测试为 9 passed。G-A、G-B、G-C 不批，G-D 只批准 `target_table.csv` 表头作 canonical 参考，G-E 接受 `DATA_NO_GO` / RQ2 `NOT_IDENTIFIED`；V2-3 已关闭。146 列 Q3 review 已完成并封存 corrected ledger `51/58/37`，但 visibility exceptions 保留，只能作为 exploratory evidence，不能作为 Stage D、RQ2 或训练证据。

当前唯一执行计划仍为 `docs/handoff/2026-09-22-paper-research-next-phase.md`；本附记只更新状态，不另立平行计划。

## 2026-10-07 narrative revision and independent-evidence backlog

The Stage E manuscript now leads with the counterintuitive result `Visibility Is Not Detection`: hierarchical checkpoints decompose evidence but do not improve matched-FPR discrimination in the current instantiation. The abstract, introduction, method framing, result heading, limitations structure, and conclusion were synchronized without changing any measured value or claim boundary.

Future evidence required before making broader or stronger claims:

1. **Second dataflow:** a corpus with a real table layer, UID-disjoint split roles, and controlled perturbations must reproduce the visibility profile without changing the frozen criteria.
2. **Independent second scorer:** a scorer independent of the current semantic-judge endpoint must reproduce the frozen leaf-state cells; the stopped step-level route does not satisfy this clause.
3. **Multi-leaf responsiveness:** localization claims require more than one scored leaf to vary with the injected input; otherwise localization remains unestablished.
4. **External scenarios:** later work may test financial audit, compliance review, enterprise table processing, and other long-horizon document workflows. Each scenario must define its own observability and harmfulness criteria before results are compared.
5. **Claim upgrade discipline:** none of these future items may be reported as current Stage E evidence until the artifact, split, scorer independence, and review receipts are complete.

These are future independent-evidence requirements, not missing paragraphs to be filled with planned results.

GB10 rebuilt the identity-converged DOCX and converted it to a 9-page PDF with LibreOffice. The visibility-by-detection matrix remains on one page, formulas and figures render correctly, tables do not split rows, and the appendix is readable. PDF text/bbox checks and sampled page inspection found no overflow. This validates the internal teacher-review layout, not a venue camera-ready.

## Pending advisor decisions

1. **Next evidence priority:** multi-leaf/multi-stage injection versus a second dataflow with a changed pipeline structure. No choice is made in this revision.
2. **Harmfulness definition:** canonical equivalence as primary, reader-referent equivalence as primary, or both reported as parallel constructs. The current paper retains the existing equivalence-dependent wording and does not select a new primary definition.

> SUPERSEDED 2026-10-11: multi-leaf evidence is complete and adopted; Route B is `NO / STOP_BRANCH`; FinQA is `SECOND_FLOW_MIXED` with accepted `MEASUREMENT_OBJECT_MISMATCH` interpretation. The historical bullets below are retained as a dated snapshot.

--- BEGIN paper/submission_review_risk_register_v1.md ---
# 小论文投稿前 reviewer 风险登记 v1

> 状态：内部审稿风险登记，不是投稿许可 | 更新：2026-10-04
> 来源：双模型审稿原件、步级链路审计、投稿包审计、Office 视觉验收
> 判定口径：blocking = 阻止投稿；should-fix = 投稿前应处理；controlled = 已有正文边界；pending-external = 等用户/venue/专利外部确认

## 1 风险表

| id | 风险 | 严重度 | 当前证据 | 状态/处置 |
|---|---|---|---|---|
| RR-01 | matched-FPR `[0,0]` 区间看起来退化，审稿人可能质疑 | should-fix | §5.2 已补 single-varying-leaf 仿射分数推导，明确 `[0,0]` 是退化支持集而非一般等价定理 | **closed**；主稿已补推导，数字/结论不变 |
| RR-02 | 112 > 96 的首读悖论 | should-fix | Abstract 与 §5.2 已明确 checkpoint visibility 与 protocol detection 是不同信号，不是 96 的分区 | **closed**；保留显式解释 |
| RR-03 | 单一公开表格语料、单 varying leaf 的外部效度 | major limitation | §5.2/§6 明确不主张普适性；第二数据流仍 pending | **controlled/open**；必须保留在 Limitations |
| RR-04 | step-level scorer 的低保真度被误读为检测能力 | should-fix | SP-C5 = `attempted_stopped_by_preregistration`；0.0298/0.2233 停止条件触发；detection/localization 禁止作为能力结论 | **closed**；V2-3 已关闭，不开 v3 |
| RR-05 | 匿名预览中的 artifact 路径/模型身份脱敏后，复现细节不够 | should-fix | `submission_draft_arr_www_anonymous_v0.md` 禁词 0；`reproducibility_statement` 列出可公开候选与不外发边界 | **pending-external**；venue 版需补匿名补充材料编号 |
| RR-06 | venue 模板、作者/单位、匿名、专利门未完成 | blocking-submission | `submission_package_audit` 明确 `PENDING_EXTERNAL_ITEMS` | **open**；不得投稿/上传/公开 |
| RR-07 | Related Work 部分 venue 标签未全部核验 | should-fix | `references_v0` 坚持未核 venue 写 `arXiv preprint`；15 条主稿引用集合已机械闭合 | **controlled/open**；venue 官方核验后才能改 |
| RR-08 | 图表在打印尺寸下的可读性 | should-fix | 叙事修订版 DOCX 已重建，GB10 PDF 8 页，抽样 1/4/5/8 页 PASS；Figure 2 与 Table 1 完整 | **closed for internal review**；camera-ready 仍需 venue 版式复验 |
| RR-09 | round5 N-1/N-2 簿记/证据锚点 | minor | N-1 `audit_status=round5` 已更新；N-2 已补 FinQA process structure evidence，claims 74/74 | **closed** |
| RR-10 | Loop B `adv_cross_doc` 间歇 source retrieval 缺失 | operational | `5f82efb` 自然周期 `sources empty`，上一周期同题 PASS | **tracked**；不阻塞论文文本，不隐藏、不重置 |
| RR-11 | 标题/摘要未把反直觉结论放在首屏 | should-fix | 已改为 `Visibility Is Not Detection`，摘要、Introduction、结果标题与 Conclusion 同步 | **closed**；写作层修复，不改数字或 claim |
| RR-12 | 第二数据流、独立 scorer 与多 leaf localization 证据不足 | major limitation | 当前仍为 deferred/unestablished；计划见 `teacher_review_readiness_v2.md` | **open**；只允许 future work，不升级当前主张 |
| RR-13 | 社会价值场景过于单一 | should-fix | 当前只保留金融文档动机；通用场景列入 readiness backlog | **pending**；后续可在不改变技术结论的前提下扩展场景 |

## 2 首要投稿前动作

1. 取得 venue 官方模板/CFP，确定页数、匿名、References 和 supplementary policy。
2. 在不改变 claim/evidence 的前提下生成 venue 版 PDF，补齐作者/单位并复验图表打印尺寸。
3. 专利确认后再决定任何外发、arXiv 或代码公开。
4. 146 列 Q3 已完成 R1/R2/ADJ 并封存 raw/ledger/hash，但带 visibility exceptions；它只作为 exploratory learnability evidence，不进入 Stage E 保底稿结果，也不得升级为 Stage D/RQ2。

## 3 当前判定

没有发现新的 manuscript blocking issue；当前 blocking 全部是外部投稿条件，不能用内部 mechanical audit 绿灯替代。
| RR-14 | 仍被误读为 hierarchical evaluator 方法论文 | should-fix | 标题、Abstract、贡献和 Method 均明确 measurement validity；hierarchy 明示为 instrument | **closed**；身份已收敛 |
| RR-15 | 被误读为 schema-matching robustness 论文 | should-fix | §4.1 明示 schema/header matching 是 perturbation carrier，研究对象是 observation boundary | **closed for positioning**；跨 pipeline 泛化仍是 evidence ceiling |
| RR-16 | visibility / detection / harmfulness 概念混淆 | should-fix | §3.2 增加 visibility × detection 矩阵，harmfulness 明确为 orthogonal annotation | **closed** |
| RR-17 | single responsive leaf 被掩盖 | major limitation | Abstract、§3.1、§5.2、§6.1 和 Conclusion 均明示 localization 未建立 | **controlled/open**；等待导师决策后续证据优先级 |
| RR-18 | null result 被解释为方法失败 | should-fix | §5.2 明示 threshold confounding diagnostic；PSO 明示 informative null；Stage R 明示 boundary case | **closed** |

--- BEGIN paper/submission_language_audit_v1.md ---
# 小论文投稿前语言与术语审计 v1

> 状态：内部静态审计，不替代 venue 格式审查 | 更新：2026-10-04
> 对象：`paper/teacher_review_draft_v1.md` 与 `paper/submission_draft_arr_www_anonymous_v0.md`
> 依据：`paper-polish-and-audit` 检查单；零模型、零外部调用

## 1 术语一致性

| 术语 | 统一口径 | 结果 |
|---|---|---|
| checkpoint-level visibility | 协议是否在中间检查点观测到缺陷 | 一致 |
| protocol-level detection | 聚合分数/映射文本是否越过检测阈值 | 一致 |
| silent absorption | 检查点证据保持而缺陷未被观测到的第三类结果 | 一致 |
| matched-FPR / affinely equivalent | 匹配假阳率后的退化等价观察 | 一致 |
| single-varying-leaf | `[0,0]` 支持集的构造条件 | 一致 |

未发现同义词漂移；Related Work 四簇与主稿方法/结果术语一致。

## 2 强主张与 AI 风格扫描

- `state-of-the-art`、`delve into`、`it is important to note that`、`in conclusion` 命中 0。
- `superior`、`significant`、`robust` 等命中项均位于“not claim / does not establish / not a general”等否定、边界或测量语境，不构成无依据强主张。
- 主稿不使用训练完成、Stage D 闭合、DATA_GO 等结果性措辞；Q3 输入包与未完成项显式保留为边界。

## 3 版本同步

- 主稿、匿名预览、DOCX、claim manifest、acceptance report 由投稿包审计统一检查。
- 匿名预览保留全部 claim tokens；内部路径、hash、模型/端点身份按 redaction map 脱敏。
- 结论段与 Abstract 均强调“decomposition, not better detection sensitivity”，未出现主张漂移。

## 4 结果

未发现 blocking language issue；本次不改主稿。剩余工作属于 venue 官方格式、作者/匿名、专利和 camera-ready 外部项。

## 5. 2026-10-07 narrative revision audit

- Title and abstract now foreground `Visibility Is Not Detection`; the abstract uses the same claim tokens and measured values as the body.
- Introduction contributions now follow the order: three-way distinction, hierarchical evidence instrument, controlled protocol audit.
- Section 5.2 leads with the threshold-artifact interpretation; Section 6 separates scientific limitations from deferred independent evidence.
- No new strong-claim language was introduced. Future dataflow/scorer/localization work is explicitly deferred and does not change current claim status.

## 6. 2026-10-07 identity-convergence review

- The manuscript now states `We study evaluation-protocol validity rather than proposing a stronger detector` in both Abstract and Introduction.
- Contributions are ordered as construct separation, evidence instrument, and protocol audit; hierarchy is explicitly not an algorithmic novelty.
- The mutation-testing comparison now refines surviving/non-detected mutants instead of claiming a universally new third outcome.
- Section 5.5 is a boundary case, Section 6.2 is concise, and detailed deferred-evidence governance is preserved in Appendix A.
- No experiment number, claim token, preregistered stopping rule, or harmfulness definition was changed.

--- BEGIN Version-B revision proposal (reviewer-attack responses section) ---
# Paper E Version-B Revision Proposal v1

> Status: `PROPOSAL_ONLY_PAPER_BODY_UNCHANGED` | Evidence: Stage E quantification + multi-leaf v1 + Loop C audit + signature ablation

## 1. Proposed title

**Visibility Is Not Detection: Quantifying Observation Boundaries in Long-Horizon AI Evaluation**

## 2. Three contributions

1. **Construct separation and observation boundaries.** Separate visibility, detection, and harmfulness as distinct evaluation constructs, and quantify family-level observation boundaries.
2. **Protocol identifiability.** Show that single-responsive-leaf hierarchy scores collapse to an affine/rank-equivalent measurement, while clean-only matched operating points are not identifiable under zero-support clean scores.
3. **Instrumentation-aligned controlled localization.** Using preregistered mapping/retrieval/numeric perturbations, show that explicit stage-aligned checkpoints produce separable visibility signatures; ablation demonstrates that localization disappears without directly instrumented stage signals.

Scientific implication: **Structured evaluation can support diagnosis only when its observation surface is aligned with the failure stages; hierarchical organization alone is insufficient.**

The third contribution must not be shortened to “hierarchy localizes failures.”

## 3. Abstract candidate

Long-horizon AI systems are commonly evaluated by final answers, which conflate three distinct questions: whether an intermediate checkpoint observes a defect, whether the evaluation protocol detects it, and whether the defect is harmful under a stated equivalence contract. We introduce an evaluation-protocol audit that separates these constructs and reports observation boundaries rather than only aggregate accuracy. On a frozen public tabular corpus of 95 tables and 118 controlled injections, 96 injections are checkpoint-visible, while 0/13 OCR-like injections are visible across 11 table clusters. Protocol counts use different detection signals and therefore do not form a single partition of visibility. In the current single-responsive-leaf construction, flat and hierarchical scores are positive affine transformations with identical rankings and ROC geometry; a clean-only matched-FPR operating point is not empirically identifiable because all clean scores are zero. Preregistered mapping, retrieval, and numeric perturbations induce perfectly separable stage-aligned signatures on an explicitly instrumented observation surface. When directly targeted checkpoints are removed, localization collapses to approximately chance, showing that the result reflects stage-aligned instrumentation rather than emergent localization from the remaining hierarchy. Structured evaluation can support diagnosis only when its observation surface is aligned with failure stages; hierarchical organization alone is insufficient.

## 4. Introduction logic

1. Long-horizon AI services move evaluation from a single prediction to a sequence of stages and checkpoints.
2. NIST AI RMF measurement guidance asks whether metrics/TEVV are appropriate and effective; a prerequisite is that the evaluator can observe the target failure mode.
3. Final correctness cannot distinguish robustness from evaluator blindness or silent absorption.
4. Define `V`, `D`, and `H` separately and make their denominators explicit.
5. Quantify family-level and worst-case observation boundaries.
6. Audit whether protocol comparisons are empirically identified once score/threshold structure is considered.
7. Stress the instrument across multiple controlled stages, but disclose when features are a contract-derived codebook.
8. Conclude with a measurement agenda: `Quantify -> Stress-test -> Transfer -> Distill`.

## 5. Evidence table

| Evidence | Status | Paper role |
|---|---|---|
| 96/118 visible, OCR 0/13 over 11 clusters | frozen | headline quantification |
| per-family/micro/worst-family VR | frozen | observation profile |
| visibility x detection cells | frozen, signal mismatch disclosed | diagnostic |
| flat/hierarchy affine/rank equivalence | structural | identifiability audit |
| clean-only matched-FPR equality | `NOT IDENTIFIABLE` | negative boundary |
| M/R/N 24 clusters/stage, 216 injections | controlled | multi-stage stress test |
| LOCO macro-F1/top-1 = 1.0 | controlled | positive but construct-sensitive |
| direct-codebook ablation = 1.0 | exploratory | limitation/negative evidence |
| second dataflow / natural signatures | future | external validity |

## 6. Required limitations

- one frozen public corpus for the quantification result;
- synthetic controlled perturbations;
- harmfulness remains equivalence-dependent;
- OCR uncertainty uses two distinct estimands;
- clean matched-FPR equality is unidentified, not zero-difference confirmed;
- multi-leaf features are contract-derived and perfectly separable by construction;
- no natural-failure localization or hierarchy-localization claim;
- TARGET design supports pooled/macro inference, not separate powered claims for every stage;
- second dataflow, independent semantic scorer and Stage D are separate future work.

## 7. Reviewer-attack responses

| Attack | Response |
|---|---|
| The metrics are invented | report them as a compact decomposition tied to mutation/detection/localization precedents and state which names are project-specific |
| OCR `0/13` is overinterpreted | report raw count, cluster count and two different exact intervals |
| Matched-FPR `[0,0]` proves equality | remove that claim; report structural equivalence and clean-support non-identifiability |
| Multi-leaf localization is tautological | include direct-codebook ablation and restrict the claim |
| Hierarchy is the contribution | keep hierarchy as an evidence instrument, not a detector/localizer |
| Stage D should validate the paper | keep Paper E and Paper D separate until C4-C2 evidence exists |

## 8. ITIL placement

Use one short motivation paragraph only:

- AI-enabled services require lifecycle governance, continual monitoring, oversight and improvement.
- Do not attribute the three advisor slogans to ITIL unless direct official text is found.
- ITIL does not enter the method or novelty claim.

## 9. Decision

Paper E Version B is the clearest near-term route, but only with the construct-sensitive multi-leaf wording. The paper can proceed as `QUANTIFICATION_READY` plus a controlled stress-test section; natural localization and Stage D remain future work.

`DECIDE NEXT LOOP: CONTINUE` to evidence-table/figure production only if no paper-body edit is made without user review.

--- BEGIN paper/teacher_review_draft_v1.md ---
# Visibility Is Not Detection: Auditing Blind Spots in Long-Horizon Document AI Evaluation

> Evaluation-track evidence draft for internal teacher review, 2026-09-22. This document covers the evaluation stage only; the current three-stage paper direction is documented separately. Author and affiliation are to be filled in. Do not distribute, submit, upload to arXiv, or publish code before the patent-status gate is cleared.

## Abstract

Long-horizon document intelligence systems are usually scored on final-answer correctness, which cannot distinguish a defect observed by an intermediate checkpoint from one that was silently absorbed, nor reveal that the evaluator itself was blind to the defect. We study evaluation-protocol validity rather than proposing a stronger detector. Our meta-evaluation separates checkpoint-level visibility, protocol-level detection, and equivalence-dependent harmfulness, using hierarchical checkpoint evidence as an instrument and per-family visibility profiles as the reporting surface. On a frozen public tabular corpus containing 95 tables and 118 synthetic header-drift injections, checkpoint-level analysis yields 96/118 visible injections; 0/13 OCR-like injections were visible across 11 table clusters. End-to-end, flat, and hierarchical protocols detect 112/118, 85/118, and 13/118 injections under different decision signals. In the current single-responsive-leaf instantiation, the flat and hierarchical contrastive scores are positive affine transformations and therefore induce identical rankings and ROC geometry. A clean-only matched-FPR operating point is not empirically identifiable because all 2,382 clean scores are zero; historical fixed-threshold equality is retained only as sensitivity evidence. This diagnosis shows that protocol comparisons without identifiable operating points can create misleading superiority stories: hierarchy decomposes evidence, while detection sensitivity and localization remain separate questions. Our results motivate evaluation reports that publish per-family visibility profiles, explicit construct definitions, validity boundaries, and reproducible evidence chains alongside aggregate scores.

## 1. Introduction

Document intelligence systems are increasingly implemented as pipelines rather than single predictors. A financial document may be decoded, segmented into tables, mapped to a canonical schema, checked for arithmetic consistency, indexed for retrieval, and finally queried by a language model. Each stage can fail independently, while later stages may compensate for or conceal an earlier error. Final-answer accuracy therefore cannot reveal whether the system followed a reliable path.

This creates a second problem that is easier to overlook: the evaluation protocol may itself be unable to observe particular defects. If a perturbed header is normalized back to the original field before the first measured checkpoint, every downstream score can remain unchanged. A correct final answer then has at least two explanations—the pipeline was robust to the perturbation, or the evaluation was blind to it. A single end-to-end score cannot separate these cases.

We study this problem through controlled fault injection. A frozen public tabular corpus contains 95 tables and 118 synthetic header perturbations across six families: alias variation, mixed language, unit suffix, date variation, OCR-like character substitution, and prefix noise. We separate three questions that aggregate scores usually collapse: whether a checkpoint observes a change, whether a protocol turns that observation into a detection decision, and whether the perturbation is harmful under a stated equivalence criterion. This separation exposes a strong family effect: 0/13 OCR-like injections were visible across 11 table clusters. The raw flat--hierarchical gap is instead traced to score and threshold structure; a clean-only matched-FPR operating point is not identifiable on the frozen clean scores.

We study evaluation-protocol validity rather than proposing a stronger detector. We ask the prior question: can the evaluation protocol observe the defect at all, and can it disclose the blind regions that make a result ambiguous? This reframes hierarchy as an evidence instrument rather than an automatic sensitivity gain, and leads to three contributions:

1. **Construct separation.** We distinguish checkpoint-level visibility, protocol-level detection, and equivalence-dependent harmfulness, which aggregate scores usually collapse into one outcome.
2. **Quantified observation boundaries.** We report per-family visibility rate, micro visibility, worst-family visibility, and visibility-conditioned protocol use, so aggregate accuracy cannot hide a family that the evaluator cannot observe.
3. **Structural protocol identifiability audit.** We show that the apparent hierarchical detection advantage in the current single-responsive-leaf setting is explained by score and threshold structure: flat and hierarchical scores are affine/rank-equivalent, while clean-only matched-FPR equality is not empirically identifiable.

This positioning keeps the empirical claim commensurate with the evidence. We do not claim universal coverage, superior hierarchical detection, a formal geometric “blind cone,” or significant downstream gains from the gated self-improvement case.

## 2. Related Work

### 2.1 Meta-evaluation

Machine-translation challenge sets such as ACES evaluate whether a metric can distinguish genuine errors from acceptable variants [Amrhein et al., 2022; Amrhein et al., 2023; Moghe et al., 2024]. Contextual metric meta-evaluation extends this view to local, context-dependent correctness [Deviyani and Diaz, 2025]. More recent studies show that rankings can change with protocol axes, prompt subsets, seeds, or the property a metric is intended to measure [Kendiukhov, 2026; Du et al., 2026; Ross et al., 2024]. We adopt the same meta-evaluation principle but focus on a prior question: whether a long-horizon protocol can observe an injected defect at all.

### 2.2 Process-level and hierarchical evaluation

Process-oriented benchmarks diagnose intermediate behavior in tool-using and web agents rather than scoring only final success [Fan et al., 2026; Chung et al., 2026]. GTA-2 represents a task as recursively aggregated checkpoints [Wang et al., 2026]. Our aggregation follows this structure, while adding deterministic contracts, explicit missing-evidence behavior, and controlled injections that expose the evaluator's sensitivity by defect family.

### 2.3 Mutation testing and fault injection

Mutation testing and metamorphic testing introduce controlled changes to measure whether a test or metric notices them [Cho et al., 2025]. AgentChaos applies programmatic fault injection to agent systems [Tan et al., 2026]. These traditions usually summarize each mutant as killed or surviving. We refine surviving or non-detected mutants by distinguishing silent absorption, unobservability at the scored layer, and equivalence-dependent interpretation, then report those mechanisms by defect family. We distinguish evaluator blindness from mutants whose intended effect is not represented on the scored observation surface. We reserve the term invalid mutant for cases that fail a separate validity audit.

### 2.4 Reliability of semantic judges

LLM judges are useful for open-semantic qualities but exhibit position, verbosity, self-preference, and perturbation sensitivity [Zheng et al., 2023; Li et al., 2025a; Li et al., 2025b]. We therefore reserve deterministic checks for contractible properties, use a judge only for semantic dimensions, hide injected ground truth from the judge prompt, and report the judge's resolution and sample limits explicitly. The distinction from prior process-level work is deliberate: those methods diagnose system behavior, whereas this paper first audits whether the evaluator can observe a controlled defect before interpreting that behavior.

## 3. Method

The conceptual core is a three-way audit of visibility, detection, and harmfulness; the hierarchical checkpoint forest is the evidence instrument that makes the audit reproducible.

### 3.1 Evidence instrument: checkpoint forest

We model the pipeline as two checkpoint trees. The parsing tree covers document ingestion, table structure, field mapping, and arithmetic reconciliation. The QA tree covers retrieval grounding, faithfulness, numeric correctness, citation quality, and appropriate refusal. Together the trees contain 12 scored leaves.

The twelve scored nodes are five in the parsing tree (document status, document throughput, table regression, field hit-rate, reconciliation equations) and seven in the QA tree (retrieval contract, faithfulness judge, numeric contract, number grounding, citation judge, refusal judge, refusal contract), per config/eval_checkpoint_trees.json v0.1.0. The visibility audit exercises the parsing-tree leaves whose evidence is the mapping and regression artifacts; under the frozen drop rule (drop = (H_orig - H_inj) x 10, threshold 2.0) only the field hit-rate leaf responds to header drift, while QA-tree leaves keep their frozen evidence and the QA arm is reported separately (12 calls at the same endpoint). This is precisely why additional localization value remains unestablished in the current instantiation. In Table 1, the label 'Pruned parsing-root drop' denotes exactly this operation: the parsing root is collapsed to its single input-responsive leaf (the field hit-rate leaf) and the drop rule above is applied there.

![Figure 1. Two checkpoint trees used by the evaluation protocol.](../docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg)

Each leaf receives a score in [0,10]. Contractible properties use deterministic checks; semantic properties use a 0–5 judge score mapped to [0,10]. Sibling weights are normalized locally before bottom-up aggregation. Missing evidence is explicit: the parsing tree assigns 0, whereas the QA tree assigns a neutral 5. Hinge leaves affect the stability verdict, not the missing-evidence score. Every leaf stores its evidence and degradation reason.

For node n with children C(n), the recursive score is

\[
S(n)=\sum_{c\in C(n)} \frac{w(c)}{\sum_{j\in C(n)}w(j)}S(c).
\]

For a leaf, S(n) is the mapped contract or judge score. A tree is stable only when at least 90% of its leaves exceed the selected threshold and every hinge leaf scores at least 7. The implementation is deterministic once the evidence artifacts are fixed.

### 3.2 Separating visibility, detection, and harmfulness

Visibility is defined relative to the selected checkpoint evidence surface, whereas protocol detection may use a different downstream signal.

The primary conceptual structure is the following visibility-by-detection matrix:

| Checkpoint evidence | Protocol detects | Protocol does not detect |
|---|---|---|
| Visible | Detected visible defect | Visible but undetected |
| Not visible | Detection through a different signal or predicate | Silently absorbed or unobservable |

Harmfulness is orthogonal to this matrix and is annotated separately as harmful, equivalent, or unresolved under the selected equivalence criterion.

For an injected defect d, visibility and protocol detection are separate observations:

- **Detected:** the selected protocol satisfies its detection predicate, which may test a mapping change or a score threshold.
- **Visible but not detected:** the checkpoint exposes a difference, but the selected protocol does not satisfy its detection predicate.
- **Silently absorbed:** normalization or matching preserves the canonical correspondence, so that checkpoint does not expose the perturbation.

Harmfulness is a separate, **equivalence-dependent** judgment, not a mutually exclusive visibility outcome: canonical-form preservation and reader-referent recoverability need not agree.

The defect visibility profile reports visibility separately for each family. This preserves information lost by a single mutation score and distinguishes a missing checkpoint from a genuinely robust stage.

### 3.3 Evaluating the evaluator

We compare four protocols on frozen evidence: end-to-end roots, a flat leaf average, hierarchical expert weights, and hierarchical searched weights. We measure table-level detection, injection-level detection, mean separation between clean and perturbed states, worst-family behavior, localization, and evaluation cost. Because raw thresholds can manufacture differences, we separately audit (i) structural score/ranking equivalence and (ii) whether a matched-FPR operating point is identifiable from clean scores alone.

The audit further varies the injection seed, visibility threshold, matching algorithm, and scoring normalization. A semantic-judge arm is evaluated separately and never substituted for deterministic evidence when a contract exists.

## 4. Experimental Setup

### 4.1 Corpus and perturbations

The study uses a frozen public tabular base and contains no client data. It includes 95 tables and 118 synthetic injections across six header-drift families. Schema and header matching are the perturbation carrier in this instantiation; the object of study is the evaluation protocol's observation boundary. Each injected record preserves its source table, family, seed, changed field, and expected observation surface.

Concretely, the base is the frozen drift-v0 table set derived from public TAT-QA tables (data/research/drift_v0/input/tatqa_tables.json, sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302); the corpus was frozen before this study's data gates and no new TAT-QA use is introduced. The perturbations are the fully synthetic injection map (data/research/drift_v0/output/injection_map.json, sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e; deterministic, seed 42, ratio 0.3). The primary matcher is the production greedy header matcher (scripts/m1_statement_parser.py, map_headers); the cross-matcher audit adds greedy-normalized, hungarian-production, and hungarian-normalized configurations. Semantic leaves are scored by the M2 judge pipeline (source tag m2_judge in config/eval_checkpoint_trees.json), i.e. Qwen3.6-35B-A3B (Q4_K_M GGUF) served at 127.0.0.1:8004, with 0-5 dimension scores mapped to [0,10]. The primary threshold grid is

\[
\Gamma=\{0.2,0.3,0.5,0.7,0.9\}.
\]

The OCR-like family contains 13 single-token, lowercase Levenshtein-distance-one substitutions with unchanged column values. These properties are mechanically recomputed before interpretation.

### 4.2 Baselines and controls

The protocol baselines are end-to-end scoring, flat leaf scoring, and hierarchical scoring with expert weights. Weight-search controls include equal weights, expert weights, 30 random trials, greedy coordinate ascent, particle-swarm optimization (PSO), and a minimax objective. Assignment controls compare greedy matching with Hungarian global assignment and include a positive solver test.

### 4.3 Statistical discipline

We freeze inputs and decision criteria before reading each result. Confidence intervals are reported on table-level clustered units where available. Seed sensitivity uses three injection seeds. For the clean-only matched-FPR audit, threshold selection may use clean scores only; injected and harmful outcomes are prohibited from calibration. Because the frozen clean supports are degenerate, non-identifiability is reported rather than forced into an empirical equality. Null and adverse findings are retained rather than relabeled as improvements.

## 5. Results

### 5.1 Visibility is strongly defect-type dependent

Checkpoint-level analysis makes 96/118 injections visible, but the aggregate hides a large family effect. 0/13 OCR-like injections were visible across 11 table clusters under all five thresholds; all 13 were invisible under this observation criterion. Other families range from 0.81 to 1.00 visibility at the primary setting. For uncertainty, the injection-level reference estimand is 0/13 with an exact binomial 95% interval of [0, 24.71%] under an independent-injection assumption; the distinct table-level event estimand is 0/11 with an exact binomial interval of [0, 28.49%]. The latter is not a clustered confidence interval for injection-level visibility.

![Figure 2. Defect visibility varies strongly across perturbation families.](../docs/experiments/figures_paper/fig_visibility_spectrum.png)

The blind family remains the same under four edit-distance matcher configurations. However, the ordering of visible families is not invariant: changing the score normalization causes five class flips, all within the date-variation family, whereas switching from greedy to global assignment causes no flips. Thus, the existence of a blind family is stable within the tested matcher family, but the full ranking is protocol-dependent.

The harmfulness label is also criterion-dependent. An instance-level oracle rejects all seven members previously placed in a type-level equivalence class. Across eight paired comparisons, five disagree, and the disagreements align with criterion kind—canonical-form preservation versus reader-referent recoverability—rather than appearing as random case-level noise. We therefore report the evaluator's blindness directly while treating whether that blindness is harmful as a boundary question.

### 5.2 The raw hierarchy gap is a threshold-placement artifact

The raw detection counts are not evidence of protocol discriminability. Table 1 compares three transferable protocols under different decision predicates: end-to-end detection tests whether the final mapping text changes, whereas flat and hierarchical scoring use frozen score-drop thresholds. A changed source-header string can therefore count as end-to-end detection even when the canonical match is preserved, explaining why 112/118 exceeds the 96/118 visibility count. Table-level counts apply all assigned injections together, whereas injection-level counts apply one perturbation at a time; the 20 detected tables and 13 individually detected injections are not nested counts. At the frozen threshold, hierarchical scoring is not a more sensitive detector.

| Protocol | Detection signal | Tables detected | Injections detected |
|---|---|---:|---:|
| End-to-end | Final mapping change | 95/95 (1.0000) | 112/118 (0.9492) |
| Flat | Field-hit-rate drop | 75/95 (0.7895; 95% CI [0.6947, 0.8737]) | 85/118 (0.7203) |
| Hierarchical, expert weights | Pruned parsing-root drop | 20/95 (0.2105; 95% CI [0.1263, 0.2947]) | 13/118 (0.1102) |

The raw flat--hierarchical gap does not establish inferior ranking quality. In the current single-responsive-leaf construction, the hierarchical contrastive score is a positive affine transform of the flat contrastive score with slope approximately 0.375. The scores therefore induce identical rankings and, by implication, identical ROC/AUROC geometry; corresponding thresholds satisfy theta_H = 0.375 theta_F. This is a structural result, not an empirical matched-FPR equality. The derived clean-only reanalysis contains 2,382 usable clean records with both score supports exactly {0}; every positive threshold has observed FPR zero, so the clean set cannot identify a unique operating threshold. Selecting a threshold by harmful TPR would violate the clean-only contract. Historical fixed-threshold sensitivity evidence is retained in Appendix A.4, but the old [0,0] interval is not a clean-calibrated confirmatory result. When more than one leaf varies with the input, neither affine nor ranking equivalence is guaranteed.

The 118 injections close at the checkpoint level as 96 visible plus 22 silently absorbed; by family (injections / visible / absorbed): alias variant 47/43/4, date variant 17/15/2, mixed language 20/20/0, OCR-like 13/0/13, prefix noise 16/13/3, unit suffix 5/5/0 (frozen artifact t2_visibility_sensitivity.json; path in the evidence ledger). The protocol-level counts in Table 1 are measured on different signals and are therefore not a partition of the 96.

We label the affine-equivalence observation a degenerate-case result: it fixes the interpretation of the raw gap under the current single-varying-leaf instantiation and does not establish affine equivalence of the protocols in general.

### 5.3 Sensitivity and reproducibility

The identity of the fully blind family is stable across the threshold grid. Absolute between-family range contracts at high thresholds, as expected when one changed header contributes at most 1/n for a table with n canonical headers. The literal preregistered range criterion fails at 0.7 and 0.9 and is reported as failed.

Across three injection seeds, flat table-detection rates are 0.7895, 0.7835, and 0.7556. Their spread is 0.0339, and the pooled estimate is 0.7766 with a 95% interval of [0.7270, 0.8227]. The seed-42 run reproduces the frozen artifact byte-for-byte.

Judge calibration covers 120 leaf-state cells; this calibration window is distinct from the 28-case semantic boundary analysis reported in Section 6. In the control-state comparison, rejudged summaries of historical 0–5 judgments differ from the frozen dimension means by at most 0.5, meeting the preregistered consistency expectation. This checks reproduction of aggregate dimension scores, not agreement between judges re-evaluating the same original answers. On the derived 0–10 root scale, control roots differ by at most 0.22, while individual leaves can move by as much as 7.0. Agreement is therefore an aggregate observation, not evidence of cell-level interchangeability.

### 5.4 Weight search produces an informative null

PSO and greedy coordinate ascent reach the same mean separation of 1.432574. PSO repeats the result on all five seeds but requires 7,650 evaluations, compared with 67 for greedy search. A minimax variant improves worst-case separation to 0.35714 while reducing mean separation to 1.25605. We therefore do not claim PSO superiority. The result instead shows that objective choice matters more than optimizer sophistication in the present search space.

### 5.5 Boundary case outside the main contribution

This boundary case is not part of the evaluation-track contribution; it only marks where Stage E evidence stops and the broader Stage R question begins.

In a compact feedback example, a gain–collateral gate rejects all 7 adversarial high-confidence mappings and all 5 expanded-collision candidates. Across 15 collision tables, the gated-minus-ungated mean paired difference is 0.05 with a 95% interval of [0, 0.1056], while the exploratory pooled comparison is 7/40 versus 4/40 with exact McNemar p=0.375. This is not an efficacy claim.


## 6. Discussion and Limitations

### 6.1 Scientific limitations

The main finding is methodological. Aggregate evaluation can hide both system defects and evaluator blind spots. A checkpoint forest makes evidence decomposable, while a visibility profile shows which defect families are observable. Yet structure alone does not guarantee sensitivity: in the current single-responsive-leaf construction, flat and hierarchical scores are affine/rank-equivalent, while a clean-only empirical matched-FPR operating point is not identifiable.

Four limitations bound the claim. First, the evidence comes from one public tabular corpus with synthetic perturbations; no cross-domain generalization is claimed. Second, the OCR-like family is blind under the evaluator, but whether each perturbation is harmful depends on the equivalence definition. Third, the semantic boundary analysis uses one judge on 28 cases; mixed-language and unit-suffix families receive no calls in that window (a separate window from the 120-cell judge calibration of Section 5.3). Fourth, matching competition reduces the oracle correctness ceiling from 0.952381 to 0.597015 under shared-header overlays, while global assignment changes no decision, locating the problem in score construction rather than allocation.

### 6.2 Deferred independent evidence

A preregistered second-dataflow extension did not satisfy its structural prerequisites and is therefore not used as evidence. A preregistered independent-scorer route triggered its pre-registered stop condition and is therefore not reported as a capability result. The criterion-relativity claim remains limited to the current evaluator and corpus; the detailed governance record is retained in Appendix A.




## 7. Conclusion

Final correctness cannot tell whether a defect was observed at an intermediate checkpoint, silently absorbed, or invisible to the evaluator itself. We introduced a three-way audit of visibility, detection, and harmfulness, implemented with hierarchical checkpoint evidence and per-family visibility profiles. On 118 controlled injections, observability and detection depend strongly on defect family and decision protocol. The central result is structural rather than a detector ranking: flat and hierarchical scores are affine/rank-equivalent in the single-responsive-leaf setting, while clean-only matched-FPR equality is not identifiable. Long-horizon evaluations should therefore report the protocol's own observation boundary, validity limits, and reproducible evidence chain alongside aggregate system performance.

## References

- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics. arXiv:2210.15615, 2022.
- Amrhein, C., Moghe, N., and Guillou, L. ACES: Translation Accuracy Challenge Sets at WMT 2023. arXiv:2311.01153, 2023.
- Chung, J., Byun, J., Vineet, V., and Kim, S. J. Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking. arXiv:2606.15673, 2026.
- Cho, S., Ruberto, S., and Terragni, V. Metamorphic Testing of Large Language Models for Natural Language Processing. arXiv:2511.02108, 2025.
- Deviyani, A., and Diaz, F. Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy. arXiv:2503.19828, 2025.
- Du, S., Liang, P., Shen, Y., et al. On the Stability of Prompt Ranking in Large Language Model Evaluation. arXiv:2606.24381, 2026.
- Fan, S., Ye, X., Huo, Y., et al. AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents. arXiv:2603.14465, 2026.
- Kendiukhov, I. Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking. arXiv:2603.03493, 2026.
- Li, Q., Dou, S., Shao, K., Chen, C., and Hu, H. Evaluating Scoring Bias in LLM-as-a-Judge. arXiv:2506.22316, 2025.
- Li, S., Xu, C., Wang, J., et al. LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge. arXiv:2506.09443, 2025.
- Moghe, N., Fazla, A., Amrhein, C., et al. Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets. arXiv:2401.16313, 2024.
- Ross, C., Hall, M., Romero Soriano, A., and Williams, A. What Makes a Good Metric? Evaluating Automatic Metrics for Text-to-Image Consistency. arXiv:2412.13989, 2024.
- Tan, G., Sun, Z., Shi, J., et al. AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection. arXiv:2608.06790, 2026.
- Wang, J., et al. GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows. arXiv:2604.15715, 2026.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv:2306.05685, 2023.

## Appendix A. Deferred independent-evidence record

This appendix preserves the internal evidence and preregistration record for deferred extensions. These materials are boundary records, not Stage E results.

### A.1 Reinstatement criteria

Reinstatement criteria, not a timeline: the deferred arms return only when (i) a second dataflow with a table layer passes SOURCE_GO and SPLIT_GO with UID-disjoint layers, and (ii) a second scorer independent of the :8004 judge reproduces the leaf-state cells; until both hold, the arms remain preregistered-but-unreported.

### A.2 Second-dataflow record

Progress against criterion (i) is now measurable, clause by clause. Three corpora answer different clauses and are named separately: the acquisition corpus (FinQA, taken under the approved minimal scope), the action corpus (a schema-matching benchmark of ten table pairs), and the transfer corpus whose missing table layer triggered the original deferral. SOURCE_GO passed on 2026-09-25 for the acquisition corpus, with per-file digests recorded. Its table layer is present and uniform: all 7134 examples carry a non-empty rectangular table whose first row is entirely string-valued, with two to eleven columns, so the clause that deferred the transfer corpus, the absence of a table layer, does not apply to the acquisition corpus. A deterministic, label-blind split instrument now assigns layers whose independence clusters are report-level rather than dataset-level, and on the acquisition corpus the four role layers are geometrically fillable, with 2409 lineage UIDs over 768 report clusters at full population. SPLIT_GO is nonetheless not passed: the acquisition corpus has its own gate and sealed partitions withheld because its registered role list does not include them, while the action corpus, which is the one that carries an action vocabulary, contains ten table-pair clusters and under the frozen hash-threshold bucketing rule leaves the development layer empty, yielding ten independent units. The remaining gap is structural rather than incremental, and it belongs to the label gate rather than to criterion (i): the acquisition corpus publishes no official canonical vocabulary for table columns, so action labels could only be constructed by inventing a schema. Here, a table layer makes samples definable; it does not supply the gold those samples need.

### A.3 Independent-scorer record

Criterion (ii) has not been tested, and one candidate route toward it was stopped by its own pre-registration. A model-free detector, independent of the :8004 judge, was built over a corpus of 1970 frozen step-level records whose contents and fault families were fixed before any detector existed, and whose percent-convention stop threshold was pre-registered before the second detector run produced any output. Its pre-registration fixed a fidelity threshold in advance, and that threshold was not reached: fidelity of the reconstructed step semantics on percent-form results was 0.0298 under one percent convention and 0.2233 under the other (44 and 330 matches out of 1478 percent-form steps, respectively), both below the pre-set 0.5, so the route was stopped rather than re-parameterized. Because that detector measures reasoning-step checkpoints while criterion (ii) concerns reproduction of the frozen header-injection leaf-state cells, the two are different measurement objects; the leaf-state reproduction clause therefore remains untested rather than failed, and what the fired stop condition establishes is the boundary of the step-level route itself. The portion of that corpus with faithful reconstruction covers 322 records of 1970 under the convention yielding 0.0298, and 467 under the one yielding 0.2233, i.e. 16.3% to 23.7%, and is reported to bound the route, not as a capability.

### A.4 Historical matched-FPR sensitivity

The older D3 analysis reported 90/111 for both flat and hierarchical protocols and a zero-difference bootstrap interval under a historical fixed-threshold sensitivity setup. Those numbers remain archived evidence for that setup only. The newer clean-only cross-fitted audit found zero-valued clean score supports and therefore could not identify a unique FPR-constrained threshold. Accordingly, the historical equality is not promoted to a clean-calibrated confirmatory claim and is not used to rank the protocols.

--- END PACKET ---
