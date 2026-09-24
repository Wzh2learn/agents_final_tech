# Independent Loop C fabrication/overclaim audit - proposal + scaffold (model qwen3.8-max)

> Dispatched 2026-09-24; evidence packet inline; no tools; 1 turn(s), cost $0.3616.
> Verdict: PASS_WITH_NOTES - no unmarked completed-experiment claims, no trained-student/closed-gate/significance claims; two Major pointer-granularity findings (zero-shot matrix paths; 7/7 and 5/5 result-level pointers), fixed in-commit with explicit artifact pointers.
> Body verbatim.

# Loop C 独立审计 — 虚构/过度主张检查（开题报告 v1 + 稿件骨架 v1）

**判定：PASS_WITH_NOTES**

无任何「未标注的已完成实验主张」，无已训练学生、无已关闭预注册门、无已达成显著性的表述；三阶段闭环在两处（PROPOSAL §1.3 首句、§9.1）被明确定性为目标框架。强制 REJECT 条件未触发。以下发现均为证据指针粒度问题，不构成虚构。

*定位说明：内联证据无行号，定位采用 文件+章节/表格锚点。严重度：Major（须在下版修复）/ Minor（建议修复）。*

---

## 逐项检查结果

**Check 1（已完成主张须附 in-repo artifact 路径）— 基本通过，2 项 Major、2 项 Minor**

1. **[Major] PROPOSAL §1.3（Stage D 行）、§6 TH-I3；SCAFFOLD 学位创新点 TH-I3** — 「已有 4B/8B/14B 零样本能力矩阵」/「当前有训练前模型矩阵」。这是一项已完成的测量（零样本评测），但两份文件内均无承载该矩阵的具体 artifact 路径，仅依赖页眉的全局指针（`paper/research_asset_map_v2.md` 证据账本）与 `research_story_v2.md` 的分级引用。缓解因素：处处被正确限定为「训练前」「不是蒸馏结果」（§3.3 RQ2、§10）。**要求**：补矩阵结果文件路径（或明确声明其仅存于账本并给出账本内锚点）。
2. **[Major] PROPOSAL §1.3（Stage R 行）、§5.6（RQ3 行）；SCAFFOLD §6.1** — 「对抗建议 7/7 被拒、扩展碰撞候选 5/5 被拒」。已标注为「机制级成立、功效未闭合」（合格的目标/机制标注），但 §5.6 所引 `research/phase2_rule_gate_replay.py` 被自我声明为「仅合同」，即**不是**承载 7/7、5/5 结果的数据 artifact；结果级指针（运行日志或经验收记录）仅能经 SCAFFOLD §6.1 的「小论文 §5.5」间接回指。**要求**：在数字出现处直接给出结果 artifact 路径或小论文 §5.5 的显式回指。
3. **[Minor] PROPOSAL §7.1（第二段）** — 「95 张表、118 个…注入」「96 个注入可见」「13 例」「112 / 85 / 13」「五个阈值」。声明「全部来自已验收 artifact，可追溯」，且 §5.6 自称是「唯一」RQ↔artifact 绑定位并给出 `logs/graph/eval/checkpoint_discrimination_tables_v2 / t2_visibility_sensitivity / t1_eval_baseline_comparison / d3_matched_fpr_stage_a`，SCAFFOLD §3.1–4.3 亦逐节给出同名文件。追溯链存在但数字与指针不共位。**建议**：在 §7.1 各数字后加括注路径。
4. **[Minor] PROPOSAL §5.6（RQ1 状态列）、§1.3（Stage E 行）** — 「已成稿，双模型复审 ACCEPT」「经独立验收」。复审/验收这一完成事件未指名承载其记录的 artifact（如 Loop B/C 验收件路径）。**建议**：补验收记录路径。

**Check 2（未完成项须显式标注）— 通过**

全部未竟项均落入 target / 空槽 / 门 / mechanism-only 四类：§1.3 Stage D「尚未闭环…没有学生模型训练」、Stage R「机制级成立、功效未闭合」；§3.3「还缺什么」列；§5.6「尚不存在；回填位 BF-1」「仅总假设」；§7.3 标题即「尚未取得的关键证据」；SCAFFOLD §4.4/5.1–5.4/6.2/7.3 逐节「空槽」并绑定门名（SOURCE_GO…MODEL_GO、OP-1）。§5.4 对合同脚本的描述均为机制性（代码行为），非结果主张，合格。

**Check 3（数字须有指针或 pending/target 标注）— 通过（除上述发现 1–3 涉及的数字外）**

合规样例：`7 passed`（同位引用 `tests/test_paper_claim_acceptance.py`，含具名测试）；「9 章节 / 10 标记零命中 / 4 交付文件」（同位引用 `claim_manifest_v1.json`）；「7 个机器门、98 个失败码」（同位引用 `phase1a_data_contract.py`）；「六项命中均为 0」（同位引用 `docs/experiments/2026-09-24_phase1a_data_gate_reverification.md`）；「≥5 不一致对、α=0.05、>=2」（同位引用 power/MDE 网格文档）；「250–500 UID」显式标为「处置目标」；sha `3e7e0568…`/`d7612405…` 绑定 `tatqa_tables.json`/`injection_map` 并附溯源文档；「60 条 DPO 对」在 PROPOSAL 无路径但 SCAFFOLD §5.2 同数绑定 `research/dpo_pairs_v0.py` 且标「仅审计素材」——跨文件指针成立，记 Minor（并入发现 1 类整改）。

**Check 4（禁称已训练学生 / 已关门 / 已达显著）— 通过**

全文反向声明密集且一致：「没有学生模型训练、蒸馏基线或训练后评测」（§1.3）；「Phase 1a 数据门当前为 `DATA_NO_GO`」（§7.3）；「不以功效不足冒充显著」「达不到则降 exploratory，不改检验方法」（§7.3、§9.2）；「不主张已获得稳定显著净收益」（§3.3 RQ3）；`READY_FOR_INDEPENDENT_ACCEPTANCE`「不等于 `DATA_GO`、不等于训练许可、不等于论文结果」（§5.4）。注意「评估轨无剩余门」（§5.6）指 Stage E 轨道而非预注册数据门，与 DATA_NO_GO 不矛盾，非违规。

**Check 5（三阶段=目标框架）— 通过**

「三阶段闭环是本论文的**目标框架**，不是现成结果」（§1.3 首句）；§5.1 路线图逐段标注（已成熟 / 待数据门 / 机制已通、功效待闭合）；§9.1「三阶段闭环的大论文（**目标**）」并含止损门降级路径；RQ4「当前只能作为总假设与系统设计」。SCAFFOLD 页眉「写作骨架，不是完成稿」。

---

## 结论

**PASS_WITH_NOTES。** 修复条件（下一版必改）：发现 1、2 须在数字/矩阵出现处补具体结果级 artifact 路径（或显式声明唯一承载文件并回指）；发现 3、4 建议同位加括注。两份文件的克制口径（可写主张 vs 还缺什么双列、空槽与回填位一一对应、「任何数字在对应门通过之前不得进入正文」）符合诚实性要求，未发现虚构证据或过度主张。
