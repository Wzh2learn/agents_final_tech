# Loop C Joint Review Task

Task ID: `publication-proxy-calibration-c-20261026`
Date: 2026-10-26, Asia/Shanghai
A snapshot: `3a21a7186f9e20ef8feb62edae0d62987fe4bf30`
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `a38252322189ccb00a1a45b7611f693ada292faf`
Authority LF SHA256: `9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974`

## Ownership And Boundary

Perform exactly one joint independent review of the fixed A snapshot. Own
only:

- `research/publication_proxy_calibration_20261026_v1/audits/C_JOINT_AUDIT.md`
- `research/publication_proxy_calibration_20261026_v1/audits/TASK_RESULT_C.json`
- focused audit fixtures/recompute scripts under the same `audits/` directory.

Do not edit A source, labels, manuscripts, raw, receipts, thesis text, memory
ledgers, frozen evidence, or the unique prompt. Do not train, generate model
answers, contact external services, or run production checks. Other loops may
work in the repository; do not revert unrelated changes.

## Review Questions

### Paper E

Independently check whether `paper_e_sncs/` is a genuine, reviewable SN
Computer Science journal-derived submission package:

- complete manuscript versus excerpt/placeholder;
- actual compiled PDF page count and build identity;
- structured abstract length and Purpose/Methods/Results/Conclusion contract;
- journal-relevant methods, related work, results, limitations, declarations,
  AI disclosure, cover letter, artifact terms and owner placeholders;
- two-case scope, numerical claims, citations, post-hoc/clustered identity,
  contribution boundary and unresolved reproduction gaps.

Distinguish editable-source completeness from compiled-PDF completeness. A
one-page reportlab rendering is not automatically a submission PDF. Do not
accept copied original ICAART source as proof that the SNCS manuscript was
adapted.

### P1 Rule Execution

Recompute the full 24-question result from the frozen inputs and public actor.
Check that the actor receives only question and complete visible table text,
uses no UID branches, hidden gold, preselected row IDs or per-case constants,
and implements the frozen rules rather than expected answers.

Verify separately:

- 4 genuine repairs;
- 19 previously numeric-correct items and any damage;
- the direction-reference conflict;
- numeric correctness versus unit/direction/citation completeness;
- UNKNOWN/ambiguity behavior;
- actual test discovery and execution. A command that reports `Ran 0 tests` is
  not a passing test receipt.

State whether 23/24 is numeric program correctness only or complete semantic
answer correctness.

### P2 Proxy Calibration

Check R7/R8 repairs, the two known matcher counterexamples, 12-UID pre-output
selection, source/reference identity, exposure boundary, and formal preflight.
Reconcile every call/token claim with raw receipts.

Most importantly, classify the preflight failure correctly. Determine whether
the missing runner/adapter/scorer contract is an in-scope engineering
qualification gap that should be implemented before generation, or a
scientific observation showing the proxy has no information value. Do not
accept `stop this generation candidate` merely because an implementation was
absent. Report what can and cannot be concluded with zero model calls.

## Required Judgment

Return one verdict:

- `ACCEPTED`;
- `CONDITIONAL`;
- `REJECTED`.

List blocking defects separately from non-blocking limitations. For each
finding give exact file/line or artifact path, evidence, impact, and the
smallest responsible follow-up. Include:

- independent counts and hashes;
- actual commands and exit status;
- calls/tokens/training and unmeasured cost categories;
- Paper E publication readiness;
- P1 result identity and boundary;
- P2 engineering-versus-scientific disposition;
- whether the old-failure reserve is justified for a bounded A remediation.

Independent AI review is AI review, not human gold or venue acceptance.
