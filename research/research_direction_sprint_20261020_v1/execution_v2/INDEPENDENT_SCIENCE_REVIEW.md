# Independent Science Review After C3 / B0 V4

Status: `COMPLETE_TARGETED_REVIEW`

Date: 2026-10-20, Asia/Shanghai

Scope: read-only scientific review of C3, B0 V4, references V3, real-trace
feedback, open research probes, and the existing Paper E decision boundary.
No model, judge, training, service, or network request was made. This review
writes only this file.

Evidence labels:

- `FACT`: directly supported by frozen artifacts or raw records.
- `INFERENCE`: a bounded interpretation of those facts.
- `UNVERIFIED`: not established by the reviewed evidence.

## Executive Verdict

1. The prior literal-percent scorer blocker and arbitrary-pair derivation
   blocker are closed with red/green evidence.
2. B0 V4's `5/7`, plan `7/7`, and consume `6/7` accounting is accurate.
3. ESD_006 is a real sufficient-evidence abstention. ESD_012 is a real model
   serialization/output-budget failure, not an evidence-selection failure.
4. The FULL_VISIBLE experiment measures complete-candidate selection and
   consumption only. It does not measure active acquisition, hidden-evidence
   retrieval, or reproduce B0 V2.
5. H should stop on this panel and move to feedback-contract semantics or a new
   natural task population. The preregistered H gate is not met.
6. The new evidence strengthens Paper E's measurement-boundary motivation but
   does not change its bounded continuation ruling or upgrade it to independent
   validation.

## 1. Prior Blocker Closure

### 1.1 Literal `%` unit normalization

`FACT`: closed. The implementation now maps literal `%` to percent at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/finrank_contract.py:410`.
The red/green pair records the old miss and corrected match at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/C3_VERIFICATION.json:22`.
B0 V4 ESD_004 is now successful with values `8.7%` and `20.8%` at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/results/B0_V4_MINIFIED_JSON/B0_RESULT.json:302`.

`FACT`: the historical B0 V3 score remains `4/7`; the unit-fixed and full-checker
post-hoc scores are separately reported as `5/7`
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/C3_RETURN.md:36`).

### 1.2 Arbitrary arithmetic in `answer_tool_consistency`

`FACT`: closed for explicit derived answers. Ordinary numeric facts now require
a literal value in returned evidence at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/finrank_contract.py:518`.
Reference-derived facts require declared operands, operators, formulas, and
operand values in returned evidence at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/finrank_contract.py:553`
and `agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/finrank_contract.py:652`.

`FACT`: the former false pair `10127 / 846 ~= 11.97` is rejected after the fix,
while the explicit revenue/cost derivation is accepted
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/C3_DERIVATION_GREEN.json:13`).
The frozen reference V3 contains explicit subtraction and margin formulas
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/C3_VERIFICATION.json:63`).

`INFERENCE`: the specific blocker is closed. Residual limitation: literal
numeric support is value-based rather than a full label/unit/period-to-source
binding. This does not reopen the arbitrary-pair defect, but full provenance
claims remain stronger than the checker.

### 1.3 Minified JSON at `max_tokens=256`

`FACT`: the instruction fix was sent. The request explicitly forbids whitespace
outside strings, pretty-printing, indentation, fences, and commentary at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/raw/B0_V4_MINIFIED_JSON/consume_B0_V4_MINIFIED_JSON_ESD_012_41c3063d2e3a/request.json:6`.

`FACT`: not behaviorally closed. ESD_012 still pretty-printed, reached
`finish_reason=length`, used `completion_tokens=256`, and emitted a truncated
JSON prefix at
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/raw/B0_V4_MINIFIED_JSON/consume_B0_V4_MINIFIED_JSON_ESD_012_41c3063d2e3a/response.json:4`.

`INFERENCE`: the prompt-only remediation is insufficient for this observed
output. This remains a blocker to calling B0 V4 a fully clean serialization
baseline, but not to preserving the `5/7` development observation.

### 1.4 C2 reproducibility

`FACT`: C2 source was not snapshotted before drift into C3. C3 now freezes its
source artifacts in
`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/BUNDLE_C3_B0_V4_FIX1.json:19`.

`INFERENCE`: C3 is reproducible from its bundle; C2 remains reproducible only
from preserved raw/results, manifests, and hashes. This is a historical
reproducibility limitation, not a blocker to the present scientific ruling.

## 2. B0 V4 Result Audit

`FACT`: the formal result is `5/7`, with 14 requests, no stop reason, and two
non-successes (`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/results/B0_V4_MINIFIED_JSON/B0_RESULT.json:1`).
Every task contains a minimal sufficient set in its plan; six tasks cite a
sufficient consume set. The only consume-sufficiency miss is ESD_012 because
consume parsing failed.

`FACT`: successful tasks are ESD_001, ESD_002, ESD_003, ESD_004, and ESD_010.
The layer accounting `7/7` plan, `6/7` consume, and `5/7` answer match is
therefore correct
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/C3_RETURN.md:48`).

### ESD_006

`FACT`: plan selected the sufficient `cand_005`, lookup returned the relevant
revenue/cost evidence, and consume validation passed. The actor returned
`UNKNOWN` with no facts, so both required V3 atoms are missing
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/results/B0_V4_MINIFIED_JSON/B0_RESULT.json:379`).

`INFERENCE`: this is an actor abstention despite sufficient evidence, not a
reference, derivation-checker, or evidence-selection failure. The underlying
reason for abstention is `UNVERIFIED`; one fixed-generation observation cannot
identify calibration, prompt sensitivity, or model uncertainty.

### ESD_012

`FACT`: plan selected `cand_001,cand_005`, the minimal sufficient set, and lookup
returned both. The generated content contained the expected method and
2.42/3.33/4.12 facts, but the JSON was truncated and failed parsing
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/results/B0_V4_MINIFIED_JSON/B0_RESULT.json:525`).

`INFERENCE`: root cause is model structured-output compliance under the fixed
256-token completion budget. It is not evidence-acquisition failure or an HTTP,
raw-store, or tool-chain failure. The result class
`ENGINEERING_SCHEMA_OR_TOOL` describes the parser boundary, not the causal
owner.

### ESD_001 limitation

`FACT`: V3 continues to require numeric values although the question asks which
components accounted for the two largest shares. C3 explicitly leaves this
question/reference ambiguity unchanged
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/C3_RETURN.md:68`).

`INFERENCE`: ESD_001 may be reported as successful under the frozen reference,
but it is not clean evidence that numeric values were question-required. This
is non-blocking only if the reference scope is stated.

## 3. FULL_VISIBLE Estimand Boundary

`FACT`: actor V3 explicitly names the estimand
`COMPLETE_CANDIDATE_SELECTION_AND_CONSUMPTION` and excludes active acquisition
and V2 reproduction
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/finrank_dev/TASKS_ACTOR_V3.json:845`).

`INFERENCE`: valid claims are limited to selecting and consuming from a complete
visible candidate set. Invalid claims include hidden-evidence retrieval,
active-search ability, historical acquisition benefit, or a longitudinal
V2-to-V4 capability improvement. V2 changed visibility and reference scope;
V3/V4 additionally changed output instructions and checker behavior.

`INFERENCE`: equal candidate bytes do not make B0 and the deterministic rule
compute-equivalent. The rule is a same-information selection control, not an
upper bound on model ability.

## 4. H Decision

`FACT`: the real-trace feedback analysis requires at least two comparable
residual evidence-selection failures and at least two complete task-matched
real histories before H
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/open_research_probes/real_trace_feedback_v1/REAL_TRACE_FEEDBACK_REPORT.md:63`).

`FACT`: B0 V4 has `7/7` plan sufficiency. Its two failures are abstention and
serialization, not comparable evidence-selection decisions. No task-matched
executed correction histories are present.

`INFERENCE`: both H gates fail. Stop H on this panel. Do not convert ESD_006 or
ESD_012 into history-learning cases.

`FACT`: open probes instead support set-valued sufficiency plus scope precision,
deprioritize active acquisition until it beats lexical at equal cost, and stop
the tested score-disagreement policy
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/open_research_probes/OPEN_RESEARCH_PROBES.md:50`).

`INFERENCE`: redirect work to feedback-contract semantics on naturally occurring
alternate sufficient sets and to a new task population where applicability
conditions change. Whether experience learning helps remains `UNVERIFIED`.

## 5. Paper E Decision Boundary

`FACT`: the external audit already limits Paper E to a two-case, bounded
measurement-audit contribution and retains the need for a genuinely frozen
independent application
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md:220`).
The revision draft likewise labels deferred material as boundary evidence, not
evaluation-track results
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_REVISION_DRAFT.md:270`).

`FACT`: the new C3/open-probe results are development-only, post-hoc, or
deterministic finite-panel evidence. Real-trace feedback explicitly disclaims
experience-learning benefit
(`agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/open_research_probes/real_trace_feedback_v1/REAL_TRACE_FEEDBACK_REPORT.md:50`).

`INFERENCE`: the new evidence strengthens the paper's motivation that score,
observation, and claim contracts determine interpretation. It does not change
the Paper E ruling, supply the missing prospective independent application, or
justify stronger benchmark/model claims. Paper E may continue in its bounded
two-case form; these artifacts may be cited only as development or boundary
evidence.

## Remaining Blockers And Non-Blocking Limits

### Remaining blockers

1. Clean structured-output baseline: ESD_012 still truncates after the minified
   instruction. A different serialization/output-budget contract is required
   before calling the panel output-clean.
2. H collection: no residual evidence-selection population and no complete
   task-matched real correction histories. H must remain stopped.
3. Stronger Paper E validation: no new prospectively frozen independent
   application. The existing continuation boundary remains binding.

### Non-blocking limitations

1. ESD_001 question/reference numeric-value ambiguity.
2. Literal fact support checks values more strongly than source label/unit/period
   provenance.
3. C2 exact source reproduction is unavailable after source drift; C3 has a
   frozen source bundle.
4. Seven development tasks, one fixed generation per stage, and
   `human_confirmed=false` prevent statistical or independent-generalization
   claims.

## Final Scientific Ruling

`FACT`: the deterministic scorer/derivation repairs are verified, B0 V4's
reported counts and two failure records are accurate, and no forbidden research
calls were made.

`INFERENCE`: B0 V4 is the final C3 development observation for
complete-candidate selection/consumption, not a clean universal baseline and not
evidence for historical-experience benefit.

`FINAL`: close the unit and arbitrary-derivation blockers; keep serialization
reliability and H/Paper E validation blockers open. Stop H on this panel,
preserve the FULL_VISIBLE estimand limit, and continue Paper E only under its
existing bounded measurement-audit ruling.
