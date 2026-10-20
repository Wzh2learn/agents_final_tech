# CONTRIBUTION_RULING_v2

> Scope: offline contribution reconstruction from TQ-4/TQ-5 artifacts and cases T01/T07/T08/T10/T12.
> This document supersedes no frozen result, scoring rule, reference, or previous NO_PROMOTION ruling. It changes the contribution judgment and the evidence vocabulary.

## 1. Ruling

**Keep `NO_PROMOTION` for empirical superiority, error-rate, and confirmatory claims.**

The current evidence can support a **case-led measurement-method argument** in a thesis chapter or methods appendix. It does not yet support a standalone case-type upgrade paper with a general conclusion about document-QA verification.

Independent human semantic gold is **not a universal prerequisite for every factual report**. It is a prerequisite for a final semantic-correctness or accuracy claim. The distinction is:

| evidence tier | examples | reporting rule |
|---|---|---|
| A. directly verifiable artifact facts | raw answer strings, table values, reference derivations, parser status, prompt exposure, hashes, budgets, decisions | report as facts with source paths; no human gold required |
| B. bounded semantic observations | accounting parentheses in T01; missing denominator in T07; provenance-versus-scope in T08; rounding in T10/T12 | report as case interpretations and mark `待裁决`/`UNSCORABLE` where the task contract is ambiguous |
| C. method/generalization claims | C is better than B, common blind spot, population error rate, document-AI generality | require independent semantic gold, a predeclared comparison, and broader evidence; currently unsupported |

## 2. Supported local empirical facts

1. **Measurement layers are empirically separable in the saved artifacts.** T01 has a reference `NO_MATCH` but both B and C accept the source-style answer. T07 has a missing denominator and an out-of-bounds citation despite a reproducible stored derivation. T08 has a real paragraph citation but a period/scope mismatch. T10/T12 differ from the frozen score under a precision policy.
2. **The five cases show different causes under the same frozen label.** They cannot be summarized as five model errors. The case matrix preserves the frozen labels and separately records notation, scope, reference, precision, and output-validity evidence.
3. **Provenance and task-scope satisfaction are different axes.** T08's paragraph locates `154.7 million` shares as of 2020-02-21; that fact does not by itself answer `for all years` over the 2017-2019 table. This is a usable measurement distinction even without declaring the reference wrong.
4. **Information exposure is a measured condition.** The T08 B prompt includes the actor answer, evidence, and notes; the C prompt includes the material and final answer only. B/C differences are therefore observations under different surfaces, not method-quality estimates.
5. **Strict output validity is independent of HTTP success.** C-T07 and C-T10 contain plausible prose but fail the frozen JSON contract; they remain `invalid`, not decisions.
6. **The execution provenance is reproducible.** TQ-5 has a hash-enforced config/runner/scorer/template/analyzer snapshot, 83-file run manifest, 8-file execution snapshot, and focused recomputation. TQ-4's run-time config gap remains explicitly open.

## 3. Mechanism explanations that remain hypotheses

- T01 may be a parser/notation normalization failure, but the run did not manipulate notation independently of the task.
- T07 may reflect a malformed question/reference pair or an intended affiliate-sales proxy; no independent semantic adjudication establishes which.
- T08 may reflect a question-scope ambiguity (`all years`) rather than a checker failure.
- T10/T12 may reflect an unstated precision policy in the task, a tolerance-policy mismatch, or both.
- B/C differences may reflect information exposure, prompt framing, or same-model stochastic/context effects. The design does not isolate these mechanisms.

These are useful hypotheses for a thesis discussion, not validated causal explanations.

## 4. Claims that are not supported

- C is superior to B, or B is superior to C.
- The checkers share a common blind spot or produce a general detection failure mode.
- A pooled TQ-4/TQ-5 error rate, accuracy rate, or population estimate.
- Any five-case count as confirmed model errors.
- The official reference is wrong, or the actor is absolutely correct.
- Citation support has been verified; it remains `NOT_ASSESSED`.
- TQ-5 is report-level independent, unseen during model training, or evidence of header-drift causality.
- The result establishes a new benchmark, a new general metric, or a first-ever finding.

## 5. T08-specific contribution wording

The defensible sentence is:

> T08 illustrates that **having a located source is not equivalent to satisfying the task scope**: the actor cites a dated paragraph, while the reference and question require a historical all-years quantity.

The sentence must immediately retain the exposure caveat:

> B sees the actor answer/evidence/notes and alarms on the period mismatch; C sees only the final answer and accepts it. This contrast is an information-surface observation and cannot be attributed to method superiority.

## 6. Paper disposition

### Suitable now

- Thesis chapter or methods appendix: a measurement-object decomposition for document-QA verification.
- A bounded case study using T01/T07/T08/T10/T12, with frozen scores preserved and semantic uncertainty labelled.
- A reproducibility/engineering appendix covering prompt surfaces, strict parsing, snapshot hashes, and the non-equivalence of provenance, legality, support, and model decisions.

### Not suitable now

- A standalone empirical claim that the proposed verification framework improves accuracy or catches shared failures.
- A main-paper abstract/conclusion contribution built on C-vs-B ranking or a total error rate.
- A universal document-intelligence claim, a confirmatory benchmark claim, or a publication-ready case paper without independent semantic adjudication and a verified literature gap.

## 7. Final judgment

**Current disposition: retain as thesis measurement-method material, not a standalone case-type upgrade paper.**

A standalone case paper could be reconsidered only after the five semantic questions are independently adjudicated, the exact literature overlap is verified beyond the local candidate pool, and the evidence is broadened enough to support a bounded case claim. Those are conditions for a future contribution decision, not a reason to run another small sample now.
