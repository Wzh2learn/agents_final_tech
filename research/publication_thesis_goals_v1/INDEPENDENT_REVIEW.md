# Independent Review: Publication And Thesis Goals

Status: `FINAL_LOOP_C_REVIEW`

Scope: `LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021`, Paper E manuscript,
claim matrix/scope lock, G1-G4 artifacts, submission package and resource
ledger. No model or judge call was made. No shared output was modified.

## Blocking Findings

### B1. FinQA cluster unit is contradictory

- `FACT`: Paper E states `89 rows over 30 clusters`
  (`agents_final_tech/paper/saner_rene_manuscript_v1.md:141`).
- `FACT`: the Chinese thesis chapter states `39 clusters` for the same 89 rows
  (`agents_final_tech/research/publication_thesis_goals_v1/G4_MEASUREMENT_AUDIT_CHAPTER_CN.md:42`).
- `INFERENCE`: this is a cross-version statistical-unit conflict. Resolve it
  against the frozen FinQA trace manifest before final submission or thesis
  freeze. Until resolved, the cluster-level sampling description is not
  reliable.

### B2. Submission package audit metadata is stale

- `FACT`: the packaged ICAART PDF is 12 A4 pages. `VENUE_AUDIT.md` and
  `SUBMISSION_CHECKLIST.md` say 10 pages
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/VENUE_AUDIT.md:42`,
  `agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/SUBMISSION_CHECKLIST.md:20`),
  while `MANUSCRIPT_AUDIT.md` correctly says 12
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/MANUSCRIPT_AUDIT.md:29`).
- `FACT`: the canonical Markdown has 21 bibliography bullets, and the revision
  report records 21 citations/entries
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_MANUSCRIPT_REVISION_REPORT.md:48`),
  but `MANUSCRIPT_AUDIT.md` claims 24/24
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/MANUSCRIPT_AUDIT.md:27`).
- `INFERENCE`: these are not venue-limit failures, but they invalidate the
  package-level `PASS` claim until the audit and checklist are synchronized.
  Actual Markdown non-whitespace count is 45,616, below ICAART's 50,000 limit.

### B3. Thesis chapter uses an unsupported significance word

- `FACT`: G4 describes a `显著的族间差异` without a corresponding hypothesis
  test (`agents_final_tech/research/publication_thesis_goals_v1/G4_MEASUREMENT_AUDIT_CHAPTER_CN.md:48`).
- `INFERENCE`: replace it with descriptive wording such as `明显/描述性差异`,
  or add a preregistered test. Do not imply statistical significance from the
  family-rate spread alone.

## Claim And Statistical Boundaries

### Paper E

- `FACT`: the active scope is exactly two counted cases, with FinQA nested in
  Case 1 and explicit forbidden claims
  (`agents_final_tech/paper/saner_rene_manuscript_scope_lock_v1.md:13`,
  `agents_final_tech/paper/saner_rene_claim_matrix_v1.json:134`).
- `FACT`: the manuscript preserves the required separation among visibility,
  detection, harmfulness, score sensitivity, decision stability and
  reproduction gap (`agents_final_tech/paper/saner_rene_manuscript_v1.md:11`).
- `FACT`: the seed analysis uses the correct units: `219/282` is descriptive
  table-run evidence; uncertainty is clustered over 119 source-table UIDs, with
  UID-equal and leave-one-seed-out sensitivity
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_STATISTICAL_AUDIT.md:16`,
  `agents_final_tech/paper/saner_rene_manuscript_v1.md:183`).
- `FACT`: OCR-like `0/13` injection-level and `0/11` table-event intervals are
  explicitly not pooled (`agents_final_tech/paper/saner_rene_manuscript_v1.md:153`).
- `FACT`: FinRank tie results use pairwise percentage points; identity counts
  use occurrences/records and remain labelled post-hoc v2
  (`agents_final_tech/paper/saner_rene_manuscript_v1.md:205`,
  `agents_final_tech/paper/saner_rene_manuscript_v1.md:220`).
- `INFERENCE`: the main quantitative claims are bounded correctly after the B1
  unit conflict is resolved. No claim currently requires a universal method,
  natural-failure rate, detector ranking or validated checklist.

### G2 Candidate: Target-Dependency Consumption

- `FACT`: G2 compares four verifiers on 10 cases: three natural candidates from
  one NtripBrowser migration and seven synthetic mechanism controls
  (`agents_final_tech/research/publication_thesis_goals_v1/G2_CONTRACT_VERIFICATION.md:7`,
  `agents_final_tech/research/publication_thesis_goals_v1/G2_CONTRACT_VERIFICATION.md:37`).
- `FACT`: behavior is `6/10`, static contract `8/10`, runtime consumption and
  hybrid `10/10`, but the document explicitly excludes natural error-rate,
  full-trace and semantic-equivalence claims
  (`agents_final_tech/research/publication_thesis_goals_v1/G2_CONTRACT_VERIFICATION.md:71`).
- `INFERENCE`: the evidence supports a bounded method candidate: controlled
  runtime target-result consumption catches the tested dead-call,
  unused-result and fallback mechanisms while accepting alias/wrapper/dynamic
  forms. It does not yet support a general migration verifier.

### G3 Candidate: Selective Revalidation

- `FACT`: G3 uses 11 controlled states: three natural model outputs from one
  task, one environment failure and seven synthetic controls. Action costs are
  planning units, not measured time
  (`agents_final_tech/research/publication_thesis_goals_v1/G3_DECISION_PROBE.md:23`,
  `agents_final_tech/research/publication_thesis_goals_v1/G3_DECISION_PROBE.md:41`).
- `FACT`: risk-greedy matches full-revalidation decisions at planning cost
  `62` versus `99`, but coverage is `0.818` because two cases remain unresolved
  (`agents_final_tech/research/publication_thesis_goals_v1/G3_DECISION_PROBE.md:68`).
- `INFERENCE`: this establishes only finite-panel headroom for a selective
  evidence-ordering policy. It is not evidence of a learned adaptive method,
  real-task cost saving or generalization.

### G2/G3 Distinction

- `FACT`: G2 asks whether a migration is complete; G3 asks which evidence to
  acquire next, when to stop and when to defer
  (`agents_final_tech/research/publication_thesis_goals_v1/G3_DECISION_PROBE.md:9`).
- `INFERENCE`: they are methodologically distinct candidates: G2's unit is a
  migration candidate with VALID/INVALID/UNRESOLVED outcomes; G3's unit is a
  task-state/action policy with risk, coverage and planning cost. The current
  evidence supports neither as an established thesis innovation.

## Venue Fit

- `FACT`: ICAART explicitly covers AI/LLM reliability and accepts regular
  papers up to 12 pages; the current PDF is exactly 12 A4 pages
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/VENUE_AUDIT.md:27`).
- `INFERENCE`: ICAART is a plausible but not ideal fit. The paper is primarily
  an evaluation/reproducibility audit; add or retain explicit wording that its
  subject is reliable AI/agent evaluation. IEEE Access remains a conditional
  backup because APC and school recognition of Early Access/DOI are unresolved
  (`agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/VENUE_AUDIT.md:63`).
- `FACT`: external submission still depends on live-system recheck, author and
  BUPT affiliation approval, AI disclosure, artifact/license, payment and actual
  conference presentation (`agents_final_tech/research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/OWNER_DECISIONS_REQUIRED.md:3`).

## Non-Blocking Findings

1. The claim matrix does not expose structured per-claim `statistical_unit`,
   `estimand` and `uncertainty` fields; the manuscript/G1 audit supply them in
   prose. Add these fields in the next schema revision.
2. The six-step checklist is consistently marked proposed and unvalidated.
3. G2/G3 use deterministic development probes with zero model/judge calls;
   `RESOURCE_LEDGER.json` records these as offline checks
   (`agents_final_tech/research/publication_thesis_goals_v1/RESOURCE_LEDGER.json:38`).
4. The PDF text, page count and limit were checked read-only. Full visual
   print-size QA remains dependent on the existing package audit.

## Final Verdicts

### Paper E

`CONDITIONAL_GO_FOR_ICAART_AFTER_B1_B2_SYNC`

The scientific claims are bounded and publication-worthy after the FinQA unit
conflict is resolved and package audit counts/pages are synchronized. Do not
expand the paper to answer reviewer demand for a third case.

### Thesis Candidate 2

`GO_AS_CANDIDATE_METHOD_LINE / NO_GO_AS_ESTABLISHED_INNOVATION`

Continue G2 only with multiple real migrations and independent
VALID/INVALID/UNRESOLVED references. If enhanced behavior tests or a simpler
rule suffice, demote it to an evaluation-design finding.

### Thesis Candidate 3

`GO_AS_CANDIDATE_METHOD_LINE / NO_GO_AS_ESTABLISHED_INNOVATION`

Continue G3 only with at least eight previously unused real task families,
measured action costs and equal-risk comparisons against full revalidation,
fixed order and simple baselines. Otherwise stop the strategy candidate and
retain the boundary result.
