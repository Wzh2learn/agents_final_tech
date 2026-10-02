# Loop C independent review of the evaluation-track manuscript (model qwen3.8-max)

> Dispatched by Loop D on 2026-09-24 under the goal completion criterion (independent Loop C / dual-model review).
> Mode: evidence packet inline (manuscript + claim manifest + readiness record), no tools, 1 turn(s), cost $0.9051.
> Body below is the session final message verbatim; assembled by Loop D without edits.

# Independent Review — Evaluation-Track Manuscript (`paper/teacher_review_draft_v1.md`)

Reviewed against `paper/claim_manifest_v1.json` and `paper/teacher_review_readiness_v2.md` (all inline). This is a text-level review: the evidence JSON/MD artifacts listed in the manifest were **not** recomputed here, and the readiness record itself states that static checks "不替代原始数字复算或科研有效性审计." All numbers quoted below come only from the three inline documents (or arithmetic on them).

---

## 1. Overall Verdict

**REVISE.**

The manuscript is internally coherent, unusually honest about null results, contains all required sections, carries the internal-review and patent-gate notice, contains none of the ten forbidden markers, and preserves both mandated findings (matched-FPR affine equivalence; OCR-blind 0-of-13) with the correct directionality confirmed by the 2026-09-22 readiness receipt. It is suitable as teacher discussion material after the revisions below. It is not blocking-level broken, but four major issues (abstract criterion caveat, unnamed corpus/judge, incomplete 118-injection outcome accounting, and the 12-leaf vs. pruned-root method–setup bridge) should be fixed before the draft is circulated, and the DOCX must not be sent before the pending Office visual check.

---

## 2. Blocking Issues

**NONE.**

(Note on manuscript §2, Related Work, specifically: no blocking issue there either. Every in-text citation — Amrhein 2022/2023, Moghe 2024, Deviyani & Diaz 2025, Kendiukhov 2026, Du 2026, Ross 2024, Fan 2026, Chung 2026, Wang 2026, Cho 2025, Tan 2026, Zheng 2023, Li 2025a, Li 2025b — resolves to a reference-list entry, and every reference-list entry is cited. No superiority claim, no trained-student claim, no forbidden marker appears in §2.)

---

## 3. Major Issues

**M1. Abstract juxtaposes 96-visible against 112-detected without the different-criterion caveat.**
- **Location:** Abstract: "checkpoint-level analysis makes 96 injections visible … end-to-end, flat, and hierarchical expert-weight aggregation detect 112, 85, and 13 injections, respectively."
- **Evidence pointer:** §5.2 supplies the missing caveat: "end-to-end detection tests whether the final mapping text changes; it is not the canonical-correspondence visibility criterion behind 96/118." The readiness receipt (2026-09-22) shows this exact confusion previously required correction ("补清 96 个可见与 112 个 mapping 文本变化…不是同一计数"), yet the abstract — the most-read section — still invites the apparent paradox 112 > 96.
- **Suggested fix:** Add a short clause to the abstract, e.g., "…detect 112, 85, and 13 injections, respectively, under protocol-specific criteria that are not the checkpoint visibility criterion," or explicitly note the end-to-end signal is a mapping-text change.
- **Severity:** Major.

**M2. Corpus, judge, and primary matcher are never identified.**
- **Location:** §4.1: "The study uses a frozen public tabular base and contains no client data."; §3.1: "a 0–5 judge score mapped to [0,10]"; §5.1: "four edit-distance matcher configurations."
- **Evidence pointer:** No dataset name/version, no judge model/version, and no statement of which matcher configuration produces the headline numbers anywhere in §4 or §5. This undercuts the paper's own closing contribution ("reproducible evidence chains," §7) and the manifest's static-pass caveat that numeric recomputation is outstanding.
- **Suggested fix:** Name the corpus and version, the judge model and version (or state explicitly why identity is withheld in the internal draft and when it will be disclosed), and designate the primary matcher configuration. If withholding is deliberate pending the patent gate, say so in one sentence.
- **Severity:** Major.

**M3. The 118-injection outcome accounting does not visibly close.**
- **Location:** §5.1: "makes 96/118 injections visible … OCR-like perturbations are visible in 0/13 cases … all 13 are silently absorbed"; §3.2 three-outcome taxonomy; §2.3: "We also separate an evaluator blind spot from an invalid mutant."
- **Evidence pointer:** Arithmetic on the manuscript's own numbers: 96 visible + 13 silently absorbed = 109; the disposition of the remaining 9 of 118 is never reported, even though §5.1 says other families range only "from 0.81 to 1.00" (implying additional non-visible, non-OCR cases) and §2.3 introduces an "invalid mutant" category that never reappears in Results. A visibility-profile paper should report the full partition.
- **Suggested fix:** Add a one-row-per-outcome accounting (detected / visible-but-not-detected / silently absorbed / invalid mutant, per family) that sums to 118, or one sentence stating where the remaining 9 fall.
- **Severity:** Major.

**M4. Method description (12 scored leaves, two trees) is not bridged to the experimental instantiation ("pruned parsing-root," one varying leaf).**
- **Location:** §3.1: "Together the trees contain 12 scored leaves."; Table 1 (§5.2): detection signal "Pruned parsing-root drop"; §5.2: "only one scored leaf varies with the input."
- **Evidence pointer:** Readiness receipt: "已按 T1 源码/工件纠正 Table 1 的检测信号，移除从完整树误套的 '2 roots / 12 leaves'" — i.e., the full-tree description was previously mis-applied to the experiment. The current draft fixes Table 1 but §4 never states which leaves are actually instantiated/active on the tabular corpus or what "pruned" removes. Since the affine-equivalence result is *explained by* the single-varying-leaf fact, the reader needs the instantiated tree, not only the framework tree.
- **Suggested fix:** In §4.1 or §4.2, add two sentences: (a) 12 scored leaves is the framework-level count; (b) the tabular experiment instantiates the parsing tree with pruning X, leaving leaf Y as the only input-varying scored leaf.
- **Severity:** Major.

---

## 4. Minor Issues

**m1. Seed-level rates and pooled estimate need their computation stated.**
- **Location:** §5.3: "flat table-detection rates are 0.7895, 0.7835, and 0.7556 … the pooled estimate is 0.7766 with a 95% interval of [0.7270, 0.8227]."
- **Evidence pointer:** Reviewer arithmetic: 0.7835 × 95 and 0.7556 × 95 are not integers (unlike 0.7895 = 75/95 in Table 1), and the unweighted mean of the three rates is 0.7762, not 0.7766. The spread check (0.7895 − 0.7556 = 0.0339) does match. Likely these are bootstrap/pooled quantities, but the text does not say so.
- **Suggested fix:** State the per-seed denominators and the pooling method (e.g., pooled detections over pooled tables, or bootstrap point estimate).
- **Severity:** Minor.

**m2. "Primary setting" is undefined.**
- **Location:** §5.1: "Other families range from 0.81 to 1.00 visibility at the primary setting."
- **Evidence pointer:** §4.1 defines the grid Γ = {0.2, 0.3, 0.5, 0.7, 0.9} but never designates which element is primary.
- **Suggested fix:** Name the primary threshold explicitly in §4.1 or §4.3.
- **Severity:** Minor.

**m3. Excessive and inconsistent numeric precision.**
- **Location:** §5.4 ("1.432574", "0.35714", "1.25605"), §6 ("0.952381", "0.597015").
- **Evidence pointer:** Table 1 and §5.3 use four decimals; these five-decimal/six-decimal values read as raw artifact dumps.
- **Suggested fix:** Round consistently (four decimals) and keep full precision in the artifacts.
- **Severity:** Minor.

**m4. "120 leaf-state cells" is unexplained.**
- **Location:** §5.3: "Judge calibration covers 120 leaf-state cells."
- **Evidence pointer:** No derivation from the 12 leaves (§3.1) or corpus sizes is given.
- **Suggested fix:** One parenthetical explaining the cell count (e.g., leaves × states × sample).
- **Severity:** Minor.

**m5. "Eight paired comparisons" is unexplained.**
- **Location:** §5.1: "Across eight paired comparisons, five disagree."
- **Evidence pointer:** The seven oracle-rejected members are introduced immediately before, but what the eight pairs pair (criteria? judges? instances?) is not stated.
- **Suggested fix:** Define the pairing in one clause.
- **Severity:** Minor.

**m6. Two different "seed" concepts collide.**
- **Location:** §5.4: "PSO repeats the result on all five seeds"; §4.3: "Seed sensitivity uses three injection seeds."
- **Evidence pointer:** Optimizer seeds (5) vs. injection seeds (3) are distinct but the text never says so.
- **Suggested fix:** Write "five optimizer seeds" in §5.4.
- **Severity:** Minor.

**m7. "7/40 versus 4/40" denominators undefined.**
- **Location:** §5.5: "The exploratory pooled column-level comparison is 7/40 versus 4/40 with exact McNemar p=0.375."
- **Evidence pointer:** 40 is presumably pooled collision columns across the 15 collision tables, but this is not stated.
- **Suggested fix:** One clause defining the 40 units.
- **Severity:** Minor.

**m8. "Clean tables" for FPR calibration vs. Table 1's 95/95.**
- **Location:** §3.3: "matched false-positive rates calibrated on clean tables"; Table 1: end-to-end detects "95/95 (1.0000)" tables.
- **Evidence pointer:** If all 95 tables carry at least one of the 118 injections, "clean tables" must mean clean *states/runs* of the same tables; the text does not disambiguate.
- **Suggested fix:** Define the clean condition used for FPR calibration.
- **Severity:** Minor.

**m9. Evidence file named `d3_matched_fpr_stage_a.json` suggests staging.**
- **Location:** Manifest SP-C2 evidence list.
- **Evidence pointer:** The manuscript reports the matched-FPR comparison without mentioning stages; the "stage_a" filename raises the question of whether later stages exist and are unreported.
- **Suggested fix:** Either state in §4.3/§5.2 that stage A is the complete comparison, or extend the manifest pointer set.
- **Severity:** Minor (manifest/disclosure hygiene).

**m10. SP-C3 evidence pointers do not obviously cover all claim components.**
- **Location:** Manifest SP-C3: evidence = `d2_cross_matcher_det.json`, `t4_pso_fair_comparison.json`.
- **Evidence pointer:** The claim covers matcher stability, seed stability, and normalization-driven "five class flips"; a cross-matcher file plausibly covers the first, but neither listed file obviously covers seed sensitivity or normalization flips (the threshold artifact `t2_visibility_sensitivity.json` sits under SP-C1).
- **Suggested fix:** Add or re-map pointers so each claim component has an artifact.
- **Severity:** Minor (manifest-side).

**m11. §5.3 control-state deltas could be misread as contradictory.**
- **Location:** §5.3: "control roots differ by at most 0.22, while individual leaves can move by as much as 7.0."
- **Evidence pointer:** Without stating whether the 7.0 leaf movement is within the control comparison or across a different comparison, the sentence appears to conflict with the ≤0.5 / ≤0.22 caps; the follow-up sentence ("aggregate observation, not … cell-level interchangeability") mitigates but does not fully resolve this.
- **Suggested fix:** One clarifying clause specifying the comparison object for the 7.0 figure.
- **Severity:** Minor.

---

## 5. Claim–Evidence Consistency (SP-C1 … SP-C4)

**SP-C1 — "Defect visibility is type-dependent; OCR-like perturbations fully blind" (supported_with_scope_limit): CONSISTENT.**
- Required tokens all present: "96/118" (Intro, §5.1); "are visible in 0/13 cases" (§5.1, verbatim); "five thresholds" (§5.1; Abstract "all 13 cases across five thresholds"; Γ in §4.1 has five elements; §4.1 confirms the OCR family has 13 members).
- Directionality matches the readiness correction ("OCR 为 0/13 可见、13/13 被吸收"): §5.1 says "visible in 0/13 cases … all 13 are silently absorbed."
- Scope limit honored: §5.1 ("treating whether that blindness is harmful as a boundary question") and §6 limitation 2 ("harmfulness … depends on the equivalence definition").
- Caveats: completeness of the outcome partition (M3); artifacts not recomputed inline. **This finding must remain — it does.**

**SP-C2 — "Hierarchy gives decomposition, not matched-FPR discrimination gain" (supported_as_diagnostic_not_superiority): CONSISTENT.**
- Required tokens all present: 112/118, 85/118, 13/118 (Table 1; Abstract "112, 85, and 13"); "[0,0]" (§5.2 bootstrap CI). Table 1 ratios are internally consistent with the stated denominators (75/95 = 0.7895; 20/95 = 0.2105; 112/118 = 0.9492; 85/118 = 0.7203; 13/118 = 0.1102 — reviewer arithmetic).
- Scope limit honored: Abstract ("additional localization value remains unestablished because only one scored leaf varies") and §5.2 ("cannot demonstrate additional localization value until more than one leaf varies").
- No sentence anywhere claims hierarchical superiority (see §6 below).
- Caveats: M1 (abstract caveat), M4 (instantiated tree), m8 (clean-table definition), m9 (stage_a). **The matched-FPR affine equivalence must remain — it does, in Abstract, §5.2, §6, and §7.**

**SP-C3 — "Blind-family structure stable across tested matchers and seeds; visible-family ranking caliber-dependent" (supported_with_external_validity_gap): PARTIALLY CONSISTENT.**
- Tokens present: "0.7895, 0.7835, and 0.7556" (§5.3); "five class flips" (§5.1, all within date-variation).
- Matcher stability: explicitly stated ("The blind family remains the same under four edit-distance matcher configurations," §5.1). Threshold stability: stated (§5.3).
- **Gap:** the manifest claim asserts stability "across tested matchers **and seeds**," but the manuscript states seed variation only for flat detection rates and never explicitly says the blind family's identity is unchanged across the three injection seeds. Either add that sentence (if the artifacts support it) or narrow the manifest wording to "matchers and thresholds."
- Scope limit honored: §6 discloses the deferred second dataflow and second scorer ("preregistered but are not reported … deferred rather than silently replaced").
- Also see m1 (seed-rate computation) and m10 (evidence pointers).

**SP-C4 — "Evaluation findings routable through gated deterministic consolidation" (mechanism_case_only): CONSISTENT.**
- Tokens present verbatim: "all 7," "all 5," "p=0.375" (§5.5).
- Mechanism-only framing enforced three times: §5.5 ("This is not an efficacy claim"; "neither analysis establishes a significant downstream benefit"), Intro ("We do not claim … significant downstream gains from the gated self-improvement case"), and §5.5's closing ("motivates, but does not answer").
- Numbers match the readiness receipt exactly (15 collision tables, mean paired ACC difference 0.05, 95% interval [0, 0.1056]).
- Caveats: m7 (undefined 40-denominators); the underlying evidence is three dated experiment docs, not recomputed here.

---

## 6. Honesty Checks

1. **Mandated findings retained.** Matched-FPR affine equivalence: present in Abstract, §5.2 (including the [0,0] CI), §6, §7. OCR-blind 0-of-13: present in Abstract ("invisible in all 13 cases across five thresholds") and §5.1 ("visible in 0/13 cases … all 13 are silently absorbed"), with the corrected directionality confirmed by the readiness receipt. ✔
2. **No hierarchical-superiority sentence found.** Full-text scan: the manuscript states the opposite — "Our goal is not to introduce a stronger detector" (Intro), "no discriminability gain at matched false-positive rate" (Intro, contribution 3), "Hierarchical scoring is not a more sensitive detector at the frozen threshold" (§5.2), "The raw flat–hierarchical gap does not establish inferior ranking quality" (§5.2), "We therefore do not claim PSO superiority" (§5.4). Nothing to flag. ✔
3. **No trained-student / distillation results claimed.** The manuscript never mentions student models, distillation, SFT, or DPO; §5.5 is explicitly a mechanism case. This is consistent with the readiness record (local audit: DATA_NO_GO / PILOT_ONLY, not training authorization). Nothing to flag. ✔
4. **Null and adverse results retained, not relabeled.** Preregistered range criterion "fails at 0.7 and 0.9 and is reported as failed" (§5.3); PSO/greedy tie reported as "an informative null" (§5.4); consolidation effect reported as non-significant with p=0.375 and CI [0, 0.1056] touching zero (§5.5); deferred second dataflow/scorer disclosed rather than silently dropped (§6); matching-competition ceiling drop 0.952381 → 0.597015 disclosed (§6). ✔
5. **Judge-calibration caveat is honest.** §5.3 explicitly limits the ≤0.5 result to "reproduction of aggregate dimension scores, not agreement between judges re-evaluating the same original answers," matching the readiness receipt's clarification. (See m11 for one residual ambiguity.) ✔
6. **Internal-review and patent-gate notices present.** Header block: "Evaluation-track evidence draft for internal teacher review, 2026-09-22 … Do not distribute, submit, upload to arXiv, or publish code before the patent-status gate is cleared." Matches manifest `status: evaluation_track_internal_draft` and `release_gate: patent_status_confirmation_required`. Not missing. ✔
7. **Limitations present and specific.** §6 contains four enumerated limitations plus the deferral paragraph. Not missing. ✔
8. **Forbidden markers absent.** All ten markers ("TODO," "append-only," "main thread," "Loop D," "Ruling ", "ruling ", "[logs/graph/eval/", "[docs/experiments/", "主线程," "决策 ") scanned: none occur. The figure links use relative `docs/experiments/figures_paper/` paths, which does not match the bracketed forbidden pattern, and both figure paths match the manifest's `figures` list. ✔
9. **Structural compliance.** All nine `required_sections` present in order; both manifest figures referenced; all four `delivery_files` are accounted for in the readiness record (the .docx and the note are outside this review's inline evidence). ✔
10. **Honesty assessment boundary.** All numeric checks above are text-internal consistency checks; per the readiness record's own caveat, this review does not replace recomputation from the evidence artifacts.

---

## 7. Reviewer-Facing Risks

1. **The [0,0] confidence interval will attract scrutiny.** A degenerate interval reads as suspicious unless the reader accepts the structural argument ("only one scored leaf varies with the input"). Recommend adding a two-sentence derivation of why a single varying leaf forces affine equivalence at matched FPR, hence a point-mass difference. (Ties to M4.)
2. **The 112 > 96 first-read paradox.** A teacher reading only the abstract may conclude the numbers contradict each other; the resolution exists but only in §5.2 (M1). This is the single most likely source of misreading in the draft.
3. **Unnamed corpus and judge (M2)** will be the first questions in any live review and weaken the "reproducible evidence chain" message in §7.
4. **DOCX visual verification is incomplete.** The readiness record states the local machine lacks LibreOffice/soffice and that pagination/overflow/missing-character checks are unverified; the .docx delivery file must not be circulated until the Office-environment check named in the readiness record is done. This review certifies only the Markdown text.
5. **Release gates remain closed.** Patent status unconfirmed; author/affiliation "to be filled in"; target-venue template absent. Any external distribution, arXiv upload, or code release before gate clearance would violate the manuscript's own header notice and the manifest's `release_gate`.
6. **Manifest drift risk on SP-C3.** The "and seeds" wording in the manifest is not mirrored verbatim in the manuscript; a cross-checking reviewer could read this as a manifest overclaim. Fix by aligning wording on one side (§5 of this review).
7. **Artifact verifiability.** Several evidence pointers are dated logs/docs that cannot be machine-checked inline, and the `stage_a` filename (m9) hints at staged analyses; be prepared to show the complete matched-FPR artifact set if the teacher asks.
8. **Reference recency.** Multiple references carry 2026 arXiv identifiers; recipients may be unable to retrieve them quickly. Before circulation, confirm each identifier resolves (procedural check only; this review does not assess the cited works themselves).
9. **Scope discipline is the draft's main asset — protect it in revision.** Every fix suggested above must preserve the negative-result framing (no matched-FPR gain, no significant consolidation benefit, no proven localization value). Do not let copy-editing soften "negative but useful" into an implicit superiority claim, and do not add any trained-student content: the readiness record confirms no training authorization exists.

---

**Summary disposition:** REVISE — no blocking issues; 4 major, 11 minor issues; SP-C1, SP-C2, SP-C4 consistent, SP-C3 partially consistent (seed-stability wording); both mandated findings intact; honesty posture strong; circulation of the DOCX and any external release remain gated.
