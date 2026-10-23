# Loop D V5 Execution Plan

Date: 2026-10-23, Asia/Shanghai

Status: `EXECUTION_START_NOT_FINAL_RETURN`

Starting HEAD: `df58512a7a84251446d7377eee5f71a405aa6544`

Resource start: 426 accounting attempts and 3,050,185 tokens used against the
current 4,096 / 20,000,000 planning capacity. Remaining capacity is 3,670
attempts and 16,949,815 tokens; this is a ceiling, not a spending target.

## 1. G1 Paper E Submission Handoff

- Recheck the official ICAART route, deadline, track, submission entry, template,
  anonymization, AI disclosure, fees and presentation requirements from live
  official sources.
- Produce one Owner-ready handoff containing final PDF identity, submission
  fields, author/affiliation placeholders, disclosure wording, artifact plan,
  fees/presentation and unresolved legal/school items.
- Keep the two-case manuscript boundary. Do not add G2/G3 material to Paper E.
- Only submission, identity commitments, payment, public release and presentation
  commitments remain external actions.

## 2. G2 Evidence Recovery Versus Reasoning/Action

Measurement first:

- Review the three real judge counterexamples against raw evidence, hidden
  benchmark references and generated answers.
- Freeze a five-way evaluation object: grounded task completion, stale/unsafe
  advice, reasonable UNKNOWN or clarification, unnecessary refusal despite
  sufficient evidence, and interface/format failure.
- Build a minimal calibration set with fixed No, fixed UNKNOWN, empty answer,
  cautious generic answer, old fact, new fact, correct paraphrase, unsupported
  detail and fact-correct/action-wrong cases.
- Preserve V4 results. Report judge false accepts, false rejects and
  inconsistencies separately from deterministic validation.

Mechanism experiment:

- Hold retrieval and recovered state fixed when comparing fact questions with
  action questions. This isolates state-to-action transfer.
- Separately run an end-to-end comparison using actual retrieval.
- Compare original BM25 top-5, one strong transparent evidence-recovery baseline,
  and one candidate mechanism. Do not exhaustively grid-search.
- Record completion, unsafe advice, coverage, reasonable UNKNOWN/clarification,
  input/output tokens, calls, preprocessing and latency.
- Oracle evidence/state probes remain diagnostics only.

Confirmation:

- Only after development iteration, freeze prompt, evaluator, baseline and UID
  selection. Use unused UID/user/task groups or an independent source.

## 3. G3 Independent Research Candidate

- Select a problem distinct from G2's state-to-action transfer, using actual
  remaining errors or executable assets.
- Preferred first qualification target: incremental evidence arrival and
  selective revalidation/retention beyond exact cache, or a small learning
  diagnosis on evidence-anchored state/uncertainty extraction.
- Require a strong non-learning/simple baseline and real development evidence.
- Merge with G2 if the question, module and measured increment are the same.

## 4. G4 Thesis Writing

- Update the contribution matrix and thesis scaffold with G2/G3 continue, merge,
  replace or stop judgments.
- Write actual problem, neighbor, method, evidence and limitations prose; do not
  promote candidates before evidence.
- Keep Paper E as the mature first point and maintain a 2027-04 submission
  schedule.

## 5. Evidence And Review

- All model, judge, repair, teacher and training calls are entered in
  `RESOURCE_LEDGER.json`.
- Raw requests/responses and failures remain versioned in revision_v5 or on GB10
  protected research.
- Repair `STALE_RETRIEVAL_POLICY_RESULTS_V3.json` or correct the ledger path and
  record its real hash.
- One independent scientific review checks claims, counterexamples, baselines and
  contribution boundaries, not only schema/tests.
