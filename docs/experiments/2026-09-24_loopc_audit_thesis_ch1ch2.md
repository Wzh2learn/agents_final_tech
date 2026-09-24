# Independent Loop C fabrication/overclaim audit - chapters 1-2 draft (model qwen3.8-max)

> Dispatched 2026-09-24; evidence packet inline; no tools; 1 turn(s), cost $0.4894.
> Verdict: PASS_WITH_NOTES - all completed-experiment claims pointered or anaphorically chained; unfinished items explicitly marked; pointer/hygiene findings fixed in-commit with inline artifact pointers.
> Body verbatim.

# Loop C — Fabrication / Overclaim Audit: Chapters 1–2 Draft v1

**VERDICT: PASS_WITH_NOTES**

No REJECT trigger found: every completed-experiment claim in the draft is either directly artifact-pointered or anaphorically chained to a pointered, accepted artifact, and all are stated in correctly deflated (often negative) form. All unfinished items are explicitly marked. No trained-student, closed-gate, or achieved-significance claims. The formalization section stays inside definitions and delegates propositions to the theory material, whose own limits are respected. Notes below are pointer/hygiene fixes required before v2.

*File/line convention: `ch1_2` = the inline chapter draft (assumed path `paper/thesis_chapters_1_2_draft_v1.md`); line numbers are counted against the provided inline text and are approximate to ±2. `theory` = `paper/method_theory_materials_v1.md` excerpt.*

---

## Five-check summary

**Check 1 — Completed-experiment claims cite in-repo artifacts: PASS with notes.**
- ch1_2:30 — "字符级 OCR 类扰动在**五个阈值下的全部 13 个案例中均不可见**（`paper/teacher_review_draft_v1.md` §5.1，证据来自已验收 artifact）" — pointer present. ✔
- The matched-FPR / affine-equivalence result and the gate case study are also completed-experiment claims; they carry pointers only indirectly (see Findings 1–3). None is presented as pending-when-done or done-when-pending; the defect is missing repeated inline pointers, not misrepresentation.

**Check 2 — Unfinished items explicitly marked: PASS.**
- ch1_2:48–53 (RQ table) — every row carries a "尚缺" column ("8B 主学生训练、A1/A2 双口径、条件 DPO、独立 sealed 未见家族"; "强门控基线、功效分析…"). ✔
- ch1_2:68 — "当前**没有学生训练结果**，且既有记录只含动作事件、不含完整推理轨迹". ✔
- ch1_2:69 — "当前为**机制级成立、功效未闭合**"; ch1_2:120 — "机制级可行、效果未闭合（TH-I4）". ✔
- ch1_2:76 — Ch.5/6 conclusions "受预注册门约束…不以未完成实验冒充结果". ✔
- ch1_2:157 — future replay gap marked `LONGITUDINAL_EVIDENCE_UNAVAILABLE`. ✔
- ch1_2:207 — Stage R row: "池内暂无已核验条目 … 只给边界不给引用". ✔

**Check 3 — Numbers carry pointers or pending markings: PASS with notes.** 13-case/5-threshold numbers are pointered (ch1_2:30); 8B/4B appear only inside a marked goal (ch1_2:68); "112 / 85 / 13", "只有一个受打分 leaf", "parse 树 0、QA 树 5", and "七臂/七个机械门" lack local pointers (Findings 1, 2, 7).

**Check 4 — No trained-student / closed-gate / achieved-significance claims: PASS.**
- No student results claimed anywhere; zero-shot matrix explicitly fenced: ch1_2:171 — "**不把**小模型零样本能力矩阵称为蒸馏结果". ✔
- Gate not claimed closed: ch1_2:161 — "`READY_FOR_INDEPENDENT_ACCEPTANCE`…**不是 `DATA_GO`**，不是训练许可，也不是论文结果——许可证权威性、复核者独立性与身份…仍需独立人工 / Loop 复核". ✔
- No significance claims: ch1_2:52 — "**不主张**已获得稳定显著净收益"; ch1_2:173 — "**不主张**三阶段闭环已获得显著的下游收益（当前为机制案例）". ✔

**Check 5 — Formalization = definitions + stated limits, no theorems beyond cited theory: PASS.**
- ch1_2:130 — "本节给出阅读第 3–6 章所必需的形式化。完整推导、命题与边界见 `paper/method_theory_materials_v1.md`" — §2.9.1–2.9.5 contain only definitions (checkpoint forest, V_ckpt/V_proto trichotomy, matched-FPR protocol, lineage rules, contract semantics). No proposition is asserted in-chapter. ✔
- "仿射等价" is consistently framed as an *empirical* result ("本论文的实证结果是", ch1_2:153), never as a theorem. ✔
- Theory excerpt self-limits are honored: Prop 1's telescoping corollary is explicitly restricted ("只能支持第一个累计局部界；若要…主张全局伸缩界，GB10 正式协议必须额外冻结同一个 $\mathcal D_{\mathrm{reg}}$…不推出 sealed test 泛化"); Prop 2 is tied to `research/phase2_rule_gate_replay.py` with "仍不约束 sealed test，也不等价于在线学习收敛"; SPIBB "不能照搬其安全改进定理"; §5.3 adaptive-reuse budget rules. The chapter imports none of the disallowed stronger forms. ✔

---

## Numbered findings

1. **MEDIUM** — ch1_2:~153 (§2.9.3): "本论文的实证结果是：在该语料上，匹配假阳率后扁平与层级分数呈**仿射等价**。因此原始检出差距（112 / 85 / 13）主要来自阈值摆放". Completed-experiment numbers with no local artifact pointer; traceability rests solely on the header discipline (ch1_2:5) and the anaphor "该语料" → §1.2's cited corpus. Also, 112/85/13 are unlabeled — the reader cannot tell which number belongs to which protocol. Fix: add an explicit pointer (e.g., `paper/teacher_review_draft_v1.md` §5.x / matched-FPR artifact) at both §2.8 (ch1_2:~126) and §2.9.3, and label each number with its protocol.

2. **MEDIUM** — ch1_2:~63 (§1.4.1 item 3): "在匹配假阳率后**没有判别力增益**；其额外定位价值**尚未确立**，因为只有一个受打分 leaf 随注入输入变化". Quantitative completed-experiment claim ("只有一个受打分 leaf") under a heading that asserts artifact support ("有已验收 artifact 支撑") without naming any artifact. Scoping is correct (negative, "尚未确立"); only the pointer is missing. Fix: name the artifact inline.

3. **LOW–MEDIUM** — ch1_2:~52 (§1.3.3 RQ3 "当前可主张"): "门控机制能拒绝已构造的有害候选". Completed case-study result with no in-chapter artifact pointer; the nearest pointer (`research/phase2_rule_gate_replay.py`) exists only in theory §5.2. Mitigations: "不主张已获得稳定显著净收益" in the same row, and ch1_2:~172 "**不把**门控案例研究当作规则自学习的效果验证". Fix: cite the replay/case-study artifact in the RQ3 cell or §2.7.

4. **LOW** — ch1_2:~64 (§1.4.1 item 4): "一套 fail-closed 的软件合同，把数据验收、简单基线、七臂规则门与论文表图接口固化为有机器判据的门". Completed engineering artifact claimed without a repo path (contract script / gate definitions), and "七臂/七个机械门" (also ch1_2:~161) is an unpointered count. Fix: name the contract artifact(s).

5. **LOW** — ch1_2:~76 (§1.5): "第 3、4 章的结论已闭环并有已验收证据". Unqualified "已闭环" sits in mild tension with RQ1's open item "第二数据流或第二 scorer" (ch1_2:~50) and §2.10's "**不主张**跨域或普适性" (ch1_2:~169). Fix: qualify — "在当前单语料、单 scorer 范围内已闭环".

6. **LOW** — ch1_2:~112 (§2.6): "当代模型技术报告（DeepSeek-R1、Qwen2.5、Llama 3）提供了模型侧的实证参照". Named works with no cite keys, under a citation discipline that admits only pool-verified entries (ch1_2:7); §2.12's Stage D row lists only `hinton2015distilling`/`gou2021kdsurvey`/`xu2024kdsurveyllm`. Fix: add keys if and only if pool-verified, else drop the parenthetical. (Contrast with the exemplary handling of Stage R at ch1_2:~207–210: "宁可缺引，不引未核".)

7. **INFO** — ch1_2:~184 (§2.11, $m_\ell$ row): "按树配置给定（parse 树 0、QA 树 5）". Configuration constants stated without a config-artifact pointer. Harmless, but a pointer would make the table self-auditing.

8. **INFO (positive)** — Citation disambiguation is applied consistently: `Li et al., 2025a/2025b` usage in §2.5 (ch1_2:~106) matches the header key map (ch1_2:7) and §2.12 keys (`li2025robustjudge`, `li2025scoringbias`); Amrhein 2022/2023 likewise. Internal number consistency holds: the "13" in §1.2's invisible-case claim reappears coherently in §2.9.3's "112 / 85 / 13". §2.10's non-claim list maps one-to-one onto the RQ table's "尚缺" column — no orphan claims detected.

---

## Disposition

No fabrication indicators: all completed claims are negative-or-scoped and traceable to the cited accepted-artifact chain; all forward claims are double-marked (goal + gap). The two MEDIUM findings are pointer-placement defects against Check 1/Check 3 hygiene, not overclaims — they do not meet the "unmarked completed-experiment claim" REJECT bar because the same results are pointered at first empirical mention (§1.2) and the draft's evidence-discipline header binds all numbers to accepted artifacts. **Required before v2:** resolve Findings 1–2 (inline pointers + protocol labels for 112/85/13); recommended: 3–6.
