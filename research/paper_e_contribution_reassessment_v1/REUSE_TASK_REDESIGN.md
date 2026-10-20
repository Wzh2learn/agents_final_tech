# Experience-Reuse Task Redesign

Status: `DESIGN_ONLY / NO_NEW_MODEL_REQUEST`.

Subsequent outcome (2026-10-19): the selected visible role-binding direction
was explored and stopped as `NOT_IDENTIFIABLE_WITH_REAL_HISTORY`. This file
remains the design rationale and is not an active run request.

## 1. Why the current panel is at ceiling

The current task contract exposes or fixes nearly every scientific decision before the actor runs:

| decision position | what the current task supplies | remaining actor action | experience-action headroom |
|---|---|---|---|
| Target evidence row | Exact `row_label` and a one-row table projection | Read the supplied row | Very low |
| Period selection | Exact `period_early` and `period_late`, with matching columns | Order the two supplied values | Very low; period order was already corrected in the task reference |
| Requested operation | `requested_quantity=signed_difference` | Assemble `late - early` | Low; strong static rule suffices |
| Unit/scale | Explicit `source_unit`, `target_unit` and `scale_rule` | Preserve the target unit | Very low |
| Tool choice | Output contract restricts the tool to `calc` | Call `calc` | Very low |
| Result consumption | The schema requires the calculator return in `delta_target` | Copy/consume the returned number | Low |
| Evidence scope | No competing rows, periods or denominators | None | None |

The B0 result is therefore not simply "the task is easy." It is the predictable consequence of an intentionally restricted calculation protocol: the task has removed evidence binding, period scope, denominator choice and ambiguity handling from the actor's action space. The remaining behavior is expression construction and faithful result consumption, which a fixed model/runtime already performs at 16/16 on the 16-task panel.

## 2. What the 12 real experiences actually contain

The collection evidence establishes:

- 12/12 complete chains with actual `calc` calls, returned values and consumed answers.
- 12/12 successful first and follow-up attempts with stable plans/answers.
- Independent reference agreement and answer/tool consistency.
- Source-cluster-separated historical records under the accepted restricted protocol.

It does **not** establish feedback-driven correction: every follow-up repeats the identical plan and returned value, and the successful feedback produces no observed action change. The cleaned reuse context correctly removes the former hard-coded `lesson`; the remaining non-repetition is mainly source values and cluster identity.

Consequently:

1. The 12 records are evidence that the real execution chain is available.
2. They are not evidence that experience teaches a general strategy beyond a static `late - early` rule.
3. Their relevance to a new evidence-binding task is partial: they cover calculation and result consumption, not row/period/scope selection.
4. They should be retained as a resource, but the new task may require a new, task-matched history collection.

## 3. Candidate tasks

### Candidate A: fixed row, fixed periods, signed difference

- **User need:** reproduce a specified two-period change exactly.
- **Actor decision:** only expression order and result consumption.
- **Experience effect:** likely redundant with a static rule and the visible contract.
- **Tool insufficiency:** none after the operands are supplied.
- **Reference:** deterministic subtraction and unit conversion.
- **Human semantics:** only notation/precision if added; currently mostly removed.
- **Source/license:** current TAT-QA-derived panel, fixed revision and accepted source clusters.
- **Negative value:** a ceiling confirms little beyond implementation qualification.
- **Disposition:** **Reject as the next research task.** This is the already-tested panel and has no measurable accuracy headroom.

### Candidate B: evidence binding before signed difference (preferred)

- **User need:** answer a financial two-period change when the source contains multiple plausible rows, multiple period columns and mixed unit displays, without being told which cells are the operands.
- **Actor decision:** select the target row and early/late period columns, resolve the requested sign direction and unit convention, then request and consume the calculation.
- **Experience effect:** a real historical case can change the plan by warning about reversed period columns, parenthesized negatives, row aliases, non-adjacent periods and displayed scale. This information can change the actual tool parameters, not merely decorate the prompt.
- **Tool insufficiency:** `calc` computes correctly only after operand binding; it cannot decide which evidence is in scope.
- **Reference:** independently derive the expected row/period coordinates and value from a frozen source table, then recompute `late - early` and the target unit with a deterministic checker. The actor never sees the hidden coordinates or reference.
- **Human semantics:** adjudicate before model access whether row labels are unambiguous, period columns are uniquely named, and unit/scale is stated. Ambiguous cases are excluded or explicitly `UNSCORABLE_FOR_REFERENCE`, not solved after seeing outputs.
- **Source/license:** use the existing fixed-revision TAT-QA source family first, subject to a new exposure/source-cluster qualification. CC BY 4.0 attribution and derived-modification notes remain required. Do not claim report-level independence when report IDs are unresolved.
- **Nearest work boundary:** FinRank, VeriFin and Same-Number Citation Swaps already cover evidence grounding, period/unit/line-item/formula binding and acceptance controls. Candidate B is justified only as a test of whether real experience changes the actor's binding action beyond those controls; it is not a new financial-QA benchmark contribution.
- **Negative value:** if a strong rule performs as well as history, the result is informative: simple operand-binding instructions explain the gain, so no experience-specific mechanism is warranted.
- **Cost/risk/rollback:** more reference construction and semantic triage than Candidate A, but still bounded table evidence and one calculator. Offline construction can stop before any model request; invalid tasks are excluded without changing model conditions.
- **Primary validation metric:** cluster-equal full task success, requiring correct evidence binding, contract-valid output, successful tool execution, answer/reference match and answer/tool consistency.
- **Disposition:** **Select.** It adds one real decision dimension while keeping the task narrowly computational.

### Candidate C: numerator/denominator ratio reconciliation

- **User need:** compute a financial ratio when numerator, denominator, period and percentage basis are not explicit.
- **Actor decision:** choose numerator/denominator rows and periods, reconcile units and decide ratio/percentage semantics.
- **Experience effect:** could teach denominator scope and percent conventions.
- **Tool insufficiency:** the calculator cannot determine the intended financial definition.
- **Reference:** requires a predeclared metric definition and independent derivation.
- **Human semantics:** high; denominator identity, affiliate scope, period alignment and percentage conventions can be genuinely ambiguous.
- **Source/license:** TAT-QA and candidate alternate sources may contain such tasks, but qualification is not closed.
- **Negative value:** failures may reflect ambiguous financial semantics rather than experience reuse, weakening interpretation.
- **Cost/risk/rollback:** highest semantic-gold and source-alignment risk; invites a broader document-understanding project.
- **Disposition:** **Reject for this stage.** Keep as a later extension only after Candidate B shows a real, attributable experience effect.

## 4. Preferred mechanism hypothesis

> In a restricted table-calculation workflow where the operation is fixed but operand binding is not, complete real experience can improve task success only if it changes which row/period/unit operands are passed to the calculator; otherwise its information is behaviorally redundant with static instructions or general context.

This hypothesis is falsifiable:

- If history does not change operand selection or does not improve cluster-equal full success over B0/R/C, the proposed experience channel has no demonstrated value on the task.
- If history changes only output formatting, report an interface-layer effect rather than experience reasoning.
- If history changes operands but those changes are wrong, record a regression and stop claims of beneficial reuse.

Recent tool-memory evidence adds one mandatory confound check: extra calls, extra tokens or repeated attempts can create apparent gains even when memory guidance is wrong or random. A history arm must therefore be call/token-matched to R and C where feasible. If H uses a retrieval or tool-graph mechanism, include a random/no-guidance diagnostic in development before attributing any gain to experience.

## 5. Historical qualification versus relevance

These are separate gates:

1. **Historical evidence qualification:** the trajectory is real, complete, permission-valid and preserves actual plan/tool/answer/feedback/follow-up.
2. **Task relevance:** the historical action contains information applicable to the selected decision position, such as resolving period or operand binding.
3. **Context construction:** the presentation is fixed before future results and does not include hidden references or invented lessons.

An experience can pass gate 1 and fail gate 2. The current 12 pass gate 1; their direct relevance to Candidate B is limited to expression execution and result consumption. Do not call them "evidence-qualified lessons for operand selection."

## 6. Exposure and split design

- The current 16 B0 tasks are exposed development evidence and cannot become a new unseen validation set.
- Researcher reading, deterministic construction and model exposure are recorded separately. Programmatic processing is not automatically model exposure; unknown exposure remains `EXPOSURE_UNKNOWN`.
- History, development and independent validation are isolated by verifiable source clusters. Same-report relationships merge clusters when report identity can be checked.
- When report identity is unknown, claims remain source-cluster-disjoint, not report-disjoint.
- Candidate thresholds and inclusion rules are frozen before model results. No task is retained or replaced because a model failed it.
- The independent validation partition is frozen after offline design/reference qualification and before any model request.

## 7. Minimum identifiable comparison

Use four necessary conditions on the same validation tasks:

| arm | content | what it excludes |
|---|---|---|
| B0 | No added experience/context | Baseline capability |
| R | Short, strong generic operand-binding and calculator rules | The explanation that any instruction helps |
| C | General financial-table context of comparable length, with no solved example | The explanation that extra tokens/domain context help |
| H | Two complete, task-relevant real histories selected by a frozen relevance rule | The proposed experience channel |

Do not automatically restore the old U/E names. The primary comparison is H versus the strongest of B0/R/C on **cluster-equal full task success**. Claiming a real-history contribution requires H to beat B0, R and C consistently and to show the predicted operand-binding behavior change.

The comparison must record calls, tokens, latency and preparation cost separately from accuracy. If H only wins after more calls or more tokens, report a compute/context effect rather than an experience effect. If H is presented as textual insights, keep it as a soft prior and do not turn it into a prescriptive next-tool instruction.

Secondary measures:

- exact row/period/unit binding;
- calculator expression/parameters;
- tool execution status;
- answer/reference match;
- answer/tool consumption consistency;
- correction, regression, `UNKNOWN`, `REFUSE` and invalid-format rates;
- context tokens, latency/cost and experience-preparation cost.

Tasks within a source cluster are not independent samples. Report cluster-level effects and cluster-equal aggregates; task counts remain descriptive. Context lengths and experience counts should be approximately matched where natural, with actual length/cost differences reported. Do not claim token effects are fully controlled by padding.

## 8. Predeclared branches

1. **No genuine experience-action position:** stop the candidate before model work.
2. **Offline reference/semantic qualification fails:** revise only in development; if ambiguity remains, stop the task rather than adjudicate after outputs.
3. **Development B0 reaches ceiling or non-success is confined to one source cluster:** stop as `LIMITED_HEADROOM` / `CEILING_ON_THIS_PANEL`; do not spend the full comparison.
4. **Failures are mainly interface/schema/tool infrastructure defects:** repair or stop as technically invalid; do not count them as experience effects.
5. **H improves formatting only:** report interface benefit only.
6. **H does not beat B0:** the selected experience presentation has no demonstrated value; close the candidate.
7. **H beats B0 but not R:** a static rule explains the gain; stop mechanism development.
8. **H beats C only while C is below B0:** context interference, not historical-experience advantage.
9. **H consistently beats B0/R/C and changes operand binding in the predicted direction:** design one independent replication and ordinary few-shot control; do not proceed directly to training.
10. **Apparent gain with source leakage or isolation failure:** no validation claim; preserve the exploratory result only.
11. **Result is imprecise or source-cluster heterogeneous:** report `UNRESOLVED`; do not expand samples automatically.
12. **H loses its advantage after call/token matching or random guidance matches it:** report a compute/guidance confound and stop the experience-mechanism claim.

## 9. Research decision

The current panel should remain stopped. The research question should move from "does history improve a fully specified subtraction?" to "does complete real history improve operand binding before a fixed calculation, beyond strong rules and general context?" Candidate B is the minimum meaningful next task. Existing experience is partially relevant and may require a new task-matched collection; that is scientifically preferable to pretending the current histories teach decisions they never contained.
