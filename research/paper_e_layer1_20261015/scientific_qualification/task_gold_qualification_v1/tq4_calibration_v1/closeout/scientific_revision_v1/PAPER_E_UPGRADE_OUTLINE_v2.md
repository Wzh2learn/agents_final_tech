# PAPER_E_UPGRADE_OUTLINE_v2

> Purpose: one-page contribution argument for a possible case-led section titled **Measurement Misalignment in Document QA Verification**.
> Status: outline only. No frozen manuscript, reference, result, or score is changed. No new model call or panel is authorized.

## 1. Problem and contribution argument

Document QA verification often collapses several distinct questions into one label:

1. does the answer numerically match a stored reference?
2. does the answer cite a real location?
3. does the cited location support the requested quantity and period?
4. does a checker accept the answer under its prompt and output contract?

The TQ-5 cases show these layers separating. T01 preserves the source accounting display while the numeric scorer expects a signed value. T07 has a reproducible stored derivation but no supplied total-sales denominator and an out-of-bounds citation. T08 has a real paragraph citation that is dated outside the table's all-years scope. T10/T12 expose a precision-policy mismatch. C's invalid outputs further show that plausible prose is not a valid decision.

The bounded contribution is therefore:

> A case-led measurement decomposition for document-QA verification that records notation, reference scope, evidence legality, evidence support, output validity, and checker information exposure as separate objects.

This is a measurement-method contribution, not a claim that a new checker is more accurate.

## 2. Roles and corrected method description

- **Actor**: answers the source question from the supplied table/paragraphs and returns an answer plus typed evidence.
- **B**: answer-plus-evidence verifier. In the actual T08 prompt it receives the actor answer, evidence, and notes and is asked to check consistency/recompute.
- **C**: same-model, independent-context answer comparison. It receives the source material and candidate final answer, but not the actor's evidence or notes. It is **not** an independent human solver, oracle, or judge.

The phrase `independent solve` must not be used without this qualification. C's output is a same-model comparison under a different information surface.

## 3. Evidence and case placement

### Main text

- A compact table of the five cases: question constraint, frozen score, evidence legality, B/C outcome, and semantic disposition.
- T01 as the notation/normalization case.
- T08 as the provenance-versus-scope case, with the B/C exposure caveat adjacent to the result.
- One paragraph separating direct artifact facts from semantic interpretation.

### Methods / measurement section

- Define the six objects: numeric reference match, evidence-location legality, evidence support, model decision, strict output validity, and information exposure.
- State the frozen scorer tolerance and the `invalid` rule for parse failures.
- State that citation support is `NOT_ASSESSED` in this run.
- Describe TQ-5 as a table-disjoint developmental panel, not a report-level or training-unseen test.

### Appendix

- T07 case card: missing total-sales denominator, actor notes/final-answer inconsistency, out-of-bounds evidence, C truncation.
- T10/T12 case cards: derivations, rounding, tolerance, and the T10 wrong-period evidence cell.
- Raw prompt surfaces and selected response excerpts for B/C.
- Run IDs, snapshot manifest hash, run manifest hash, request budget, and reproducibility limitations.

### Not suitable for the main claim

- The five cases do not support a total error rate or a superiority comparison.
- C-vs-B differences cannot be attributed to method quality because their prompts expose different information.
- No abstract/conclusion claim should say `first`, `general`, `robust`, `effective`, or `shared blind spot`.

## 4. Literature overlap and gap check

### Overlap already present in local verified material

- Task/data context: `zhu2021tatqa` (TAT-QA) and `chen2021finqa` (FinQA) are already verified in `paper/method_data_references_v1.bib`.
- Metric/meta-evaluation context: `amrhein2022aces`, `moghe2024acesjournal`, and the local related-work matrix cover challenge-set and metric meta-evaluation.
- Measurement/construct validity: local verified arXiv metadata includes `2511.04703`, `2602.15532`, `2603.15121`, `2609.25173`, `2609.13642`, and `2609.33153` (`paper/PAPER_E_RECENT_RELATED_WORK_2026_v1.md`).
- Silent failures and observation contracts: local candidates include `2609.32691`, `2605.17281`, `2609.02246`, and `2610.06163`.
- Document/table evaluation: local candidates include `2605.19309` and `2609.07629`.

These works make a generic claim such as “evaluation metrics can be invalid” or “harnesses can fail silently” insufficient as a novelty statement.

### Potential gap, explicitly pending verification

The local literature pool does not establish that the exact case taxonomy used here — **notation normalization + reference scope + provenance/scope separation + precision policy + strict verifier validity under different information surfaces** — has already been published for document QA verification.

Mark this as `GAP_PENDING_LITERATURE_VERIFICATION`. Do not claim “first” or “novel” until a broader citation search verifies the overlap. The local 2026 candidates are arXiv metadata records; no venue/DOI is asserted.

## 5. Claim ladder

### Safe claim

> In a bounded TQ-5 developmental panel, the same frozen `NO_MATCH` label arose from at least four distinguishable measurement mismatches; source provenance, evidence legality, evidence support, and checker acceptance are not interchangeable.

### Conditional claim

> The case decomposition may be useful as a measurement-method framework for document QA verification.

This requires the five semantic questions to remain explicitly unresolved or independently adjudicated.

### Unsupported claim

> The proposed verification method improves accuracy, finds common checker blind spots, or generalizes to document intelligence.

## 6. Submission gate and final placement

The material is currently stronger as a **thesis measurement-method chapter/appendix** than as a standalone case-type upgrade paper. A standalone paper would need, at minimum:

1. independent semantic adjudication of T01/T07/T08/T10/T12;
2. a verified related-work gap beyond the local candidate pool;
3. a predeclared comparison or a broader case set that supports a bounded case claim;
4. a clear venue fit for a case/negative-result or engineering-measurement paper.

Until those conditions are met, retain `NO_PROMOTION`, keep the frozen Paper E manuscript unchanged, and do not substitute another small sample for the contribution judgment.
