# Next Development Run Card Draft

Status: `SUPERSEDED / HISTORICAL_DESIGN_ONLY`

This generic development card was overtaken by the bounded same-number
role-history run. Current status and stop evidence are in
`docs/research/README.md`.

This card is a design proposal. It does not authorize actor/judge requests, service startup, collection, pilot, training or online memory writes.

## 1. Decision this card would support

Does complete real history improve **operand binding before a fixed financial calculation** beyond no context, a strong generic rule, and general context?

The task is intentionally narrow: a table contains multiple candidate rows and period columns, but the actor must choose the evidence operands before calling `calc`. It is not an open-document-understanding study.

## 2. Fixed task contract

- Source family: fixed-revision TAT-QA raw material only, with CC BY 4.0 attribution and derived-modification note.
- Input: a bounded table projection containing candidate rows and multiple period/unit columns; no hidden reference coordinates or answers.
- Construction rule: distractor rows/periods and task difficulty are derived only from frozen source structure under a label-blind rule, then fixed before references are exposed or model outputs exist. They are never tuned from model success or failure.
- User question: identify a named financial quantity's signed change between two named periods and report the requested unit.
- Required actor actions: select row, select early/late periods, resolve sign direction and unit/scale, call `calc`, consume the returned value, emit the frozen output contract.
- Tool: existing `calc`; no function-calling change and no new service.
- Output contract: `calc` / `ANSWER` / `UNKNOWN` / `REFUSE`; non-answer numeric/unit fields are explicit `null`; `max_tokens=256`, thinking disabled through the already qualified template switch.
- Reference: independently derived from frozen source coordinates and deterministic arithmetic before model access.
- Semantic gate: ambiguous row alias, period naming, denominator/scale convention or source identity is excluded or marked `UNSCORABLE_FOR_REFERENCE` before any model call.

## 3. Source and exposure gates

1. Build source clusters over the full fixed-revision source set and all known exposure records before task selection.
2. Record exposure as `ID_SCAN_ONLY`, `PROGRAMMATIC_ONLY`, `DESIGN_OR_DIAGNOSTIC`, `MODEL_OR_FEEDBACK_EXPOSED`, `EXPOSURE_UNKNOWN` with evidence, not by presence in an exclusion list.
3. History, development and independent-validation partitions are cluster-isolated. Same-report links merge clusters where verifiable; report-level independence is not claimed without report IDs.
4. The existing 16 B0 tasks and 12 history trajectories are exposed development material. They cannot be relabeled as unseen validation tasks.
5. Task/reference/manifest, model/runtime, prompt/schema and raw-capture hashes are frozen before the first request in any future run.

## 4. Development phase

Purpose: establish that the new task has measurable headroom and that its reference is buildable. This phase is offline until separately authorized.

- Development panel: 8 source clusters, 2 tasks per cluster = 16 tasks.
- B0 only: 2 requests per task (plan + consume) = 32 requests if a future online development run is approved.
- Fixed order and all future arm contents must be frozen before B0.
- Stop after B0 if 16/16 succeeds (`CEILING_ON_THIS_PANEL`) or if non-success is fewer than 2 tasks or confined to one source cluster (`LIMITED_HEADROOM`).
- Do not inspect B0 failures and then change task semantics, selection rules, experience presentation or prompts.
- Technical qualification failures (unparseable response, identity mismatch, broken tool trace, raw loss) are not scientific non-success and do not justify spending more requests.

## 5. Confirmatory comparison, only after development headroom

Same 16 tasks, one run, one frozen task order and cluster-balanced presentation:

| arm | content | requests |
|---|---|---:|
| B0 | no context | 32 |
| R | fixed generic operand-binding rule | 32 |
| C | fixed general financial-table context, no solved example | 32 |
| H | two complete task-relevant real histories selected by a frozen relevance rule | 32 |

Each task/arm uses plan + consume, no retries. If a task-matched historical pool does not exist, a separate history-collection design and authorization are required before H can run; the current 12 restricted calculation histories cannot be presented as operand-selection lessons.

All arms must be call/token-budget matched where feasible. If H is implemented with retrieval, tool-graph guidance or repeated self-correction, development must include a random/no-guidance diagnostic before any experience attribution. If H is plain textual context, report actual context length and preparation cost and do not claim that token effects are fully controlled.

Primary metric: **cluster-equal full task success**. A success requires all of: correct row/period/unit binding, valid output, successful tool execution, reference match and answer/tool consistency.

Secondary metrics: operand coordinates, tool expression, tool status, answer/reference match, answer/tool consistency, correction/regression, `UNKNOWN`, `REFUSE`, invalid format, context length, latency and accounting cost. Cost is a co-primary attribution diagnostic: an H gain that disappears after call/token matching is a compute or context effect, not evidence of experience reuse.

Independent unit: source cluster. Report cluster-equal estimates and the raw task count; do not treat two tasks in one cluster as independent evidence.

## 6. Budget proposal (not authorization)

- Offline design, deterministic reference checks, fixture tests and Loop C review: **0 model requests**.
- Conditional development B0: **32 requests**, roughly 13k tokens based on the prior B0 accounting, but reserve the actual frozen budget.
- Conditional four-arm comparison: **128 requests**, up to 1.7M tokens as a conservative cap.
- Optional task-matched history collection: separate proposal, not included in this card. The prior 12-history collection cost 54 requests and 26,384 accounting tokens; a new collection would require a new source/identity and budget ruling.

The current authoritative ledger is 100/228 requests and 163,016/2,450,000 tokens. The global cap remainder is 128 requests; the separate reuse diagnostic sub-budget has 96 unused requests because 32 of its 128 were spent on B0. Neither figure is automatically permission to run this card. Any future run needs a fresh authorization, fixed window, unique run identity and non-overwriting raw root.

## 7. Stopping rules

- No genuine action position for history: stop before model work.
- Reference ambiguity or source/exposure uncertainty: stop or exclude predeclared cases; never adjudicate after seeing outputs.
- Development ceiling or one-cluster-only headroom: stop; do not run R/C/H.
- Interface, schema, tool or raw-integrity failure: stop the run as technically invalid; do not count as model failure.
- H improves formatting only: report interface effect only.
- H fails to beat B0: stop the current experience presentation.
- H beats B0 but not R: static rules explain the gain; stop mechanism development.
- H beats C only while C is below B0: report context interference, not history advantage.
- H beats B0/R/C with predicted operand changes: design one independent replication and ordinary few-shot control; no training or production memory write.
- Leakage, identity drift, cluster isolation failure, budget/window overrun: stop new requests and preserve partial evidence.
- Normal wrong answers, refusals and identifiable format errors are recorded results, not automatic retry triggers.

## 8. Required future packet before activation

1. `SOURCE_AND_EXPOSURE_QUALIFICATION`: source hashes, cluster evidence, exposure classes and frozen split.
2. `TASK_REFERENCE_FREEZE`: hidden coordinates, deterministic reference, semantic adjudication record and checker hash.
3. `RUNTIME_IDENTITY`: model artifact, tokenizer/template, effective parameters, tool and schema hashes.
4. `PROMPT_AND_CONTEXT_FREEZE`: B0/R/C/H contents, lengths, selection rule and ordering.
5. `LEDGER_AND_RAW_PROTOCOL`: unique request IDs, immutable raw capture, crash recovery and accounting.
6. `INDEPENDENT_INCREMENTAL_REVIEW`: one review of the new task/reference/protocol; blocker count must be zero before any request.
7. `CONTROL_COST_MATCHING`: planned call/token/context budgets and any random/no-guidance diagnostic required by the H implementation.

The card remains `DRAFT / ONLINE_NOT_AUTHORIZED` until an owner issues a new bounded run decision.
