# HISTORY_COLLECTION_DESIGN_v1

> Date: 2026-10-17 Asia/Shanghai
> Status: `DESIGN_ONLY / COLLECTION_NOT_AUTHORIZED / MODEL_REQUESTS=0`
> Purpose: make one future decision possible: whether to authorize a new, bounded real-history collection.
> Scope: TAT-QA two-period signed-difference tasks with explicit unit handling. This is not a pilot, method experiment, training run, or scientific result.

## 1. Research target

The future question is:

> After evidence-qualification filtering, does real historical experience improve future independent-task performance relative to no extra context, general rules, generic domain context, and unfiltered real experience?

The present document specifies only the collection and qualification chain. It does not claim that historical experience is useful, that E is superior to U, or that a new mechanism is necessary.

## 2. Frozen source boundary

- Source: TAT-QA, `https://github.com/NExTplusplus/TAT-QA`.
- Upstream revision: `870accc41953dcde885aabeb963d94aabdc0fbc3`.
- Raw files on GB10:
  - `data/research/tatqa_raw_2026/tatqa_dataset_train.json`
    - size 12,845,647 bytes
    - sha256 `2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69`
  - `data/research/tatqa_raw_2026/tatqa_dataset_dev.json`
    - size 1,637,431 bytes
    - sha256 `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`
- Licence: CC BY 4.0 at the pinned revision. Every derived artifact must retain attribution, source revision, and a derivative/modification note.
- SEC EDGAR and all other sources are out of scope for this design.

The upstream-to-file correspondence is verified at design time. Every future collection run must recheck the two local hashes before its first request. A hash mismatch is a stop condition, not an invitation to download a replacement.

## 3. Task contract

One collection item is a constrained tool task:

1. The table exposes two unambiguous periods.
2. One row and target quantity are fixed before model access.
3. The operation is a signed difference: `late_value - early_value`.
4. Source and target units are explicit; any scale conversion is deterministic and recorded.
5. The reference is independently recomputed from table cells by a checker that does not consume actor output.
6. Tasks with ambiguous row, period, unit, operation direction, or reference validity are excluded before any model request.

Allowed task fields:

```json
{
  "item_id": "opaque",
  "source_cluster_id": "opaque",
  "task": {
    "row_label": "fixed row",
    "period_late": "fixed period",
    "period_early": "fixed period",
    "requested_quantity": "signed_difference",
    "source_unit": "explicit unit",
    "target_unit": "explicit unit",
    "scale_rule": "deterministic expression"
  },
  "evidence": {
    "table": "minimal table projection"
  }
}
```

The actor-visible item must not contain `source_cluster_id`, raw UID, report mapping, split role, qualification level, ranking position, or hidden reference values.

## 4. Source clusters and splits

### 4.1 Unit of analysis

The independent unit is a **source cluster**. Multiple rows, tasks, attempts, and repeats inside one cluster are observations, not independent samples.

### 4.2 Cluster construction

Construct clusters before any model result is read:

1. If a verified report ID exists, all records from that report form one cluster.
2. Add an edge for exact normalized table identity, exact normalized paragraph-set identity, or deterministic near-duplicate evidence.
3. Merge connected components. Do not split a component merely to reach a desired sample count.
4. For same-company/cross-period records, merge or exclude when evidence is reused or table/context similarity is high.
5. Freeze the canonicalizer and thresholds before selection.

Proposed deterministic near-duplicate rule for the future implementation:

- Unicode NFKC, lowercase, collapse whitespace, and remove punctuation for cell/paragraph text.
- Represent a record by multisets of normalized cell 5-grams and paragraph 5-grams.
- Add a near-duplicate edge when table Jaccard `>=0.90` **and** paragraph Jaccard `>=0.80`.
- Exact identity edges override thresholds.
- Connected components are the source clusters.

The persistent replay builder is not implemented in this phase. The following is a read-only design recomputation used only to qualify source availability.

Read-only design recomputation on the 182-record candidate manifest produced 182 singleton connected components under these thresholds. After excluding the 22 old WP-2 role origins, 160 history-candidate components remain and 154 contain at least two usable rows. This is sufficient in record count for the 12-cluster **history collection** target. It is not evidence for the future pilot: the entire 182-record manifest was an exclusion source for TQ-5 and therefore cannot provide new unseen test clusters. Raw TAT-QA records also expose no report ID.

The recorded TQ exclusion union is reproducible from four pinned sources and contains 221 UIDs (canonical sorted-UID sha256 `416bdf247a242ded47b7edc32e5a39554547f9715bdf683685bf2df3d8d674f3`). Together with the 12 TQ-5 selected UIDs, this leaves 2,246 raw records outside recorded TQ exposure. That is a raw-record count only and does not establish task or source-cluster sufficiency.

Applying the WP-0 task contract to those 2,246 records (two or more period columns, a unit marker, and at least one row with two parseable period values) yields **0 remaining task-eligible records**. All records satisfying this constrained task shape are already inside the 221-UID exposure union. Therefore the current TAT-QA source/task combination has **0 unexposed future-pilot clusters**. Before any history collection is spent, the owner must either bind a different future-task source or approve a precisely revised task scope; otherwise there is no independent future task on which to evaluate the collected history.

### 4.3 Exposure and split isolation

The following materials are exposed and cannot enter a new unseen confirmation set:

- all TQ-4/TQ-5 materials and prompt-debugging cases;
- all old WP-2 role assignments and raw/plan/consume traces;
- every material used in manual or AI diagnosis, bridge debugging, or prompt tuning.

Old raw/plan/consume trajectories are engineering fixtures and failure records only. They are prohibited from U/E experience contexts. Missing feedback or corrections must not be reconstructed.

History, development, and future-test sets must be disjoint at the source-cluster level. Public data cannot be described as unseen during model pretraining.

## 5. Real experience chain

A new experience is eligible only when all stages exist:

```text
frozen task
  -> actor selects actual field/period/unit/tool parameters
  -> tool executes those parameters without gold correction
  -> actor receives and consumes the actual return value
  -> independent deterministic checker emits feedback
  -> a subsequent real attempt is executed when the protocol requires one
  -> all raw requests/responses and receipts are retained
```

Required record:

- immutable task and source-cluster identifiers;
- model/runtime/template/tool/checker hashes;
- actor plan parameters and raw response;
- exact tool input, output, status, and timing;
- actor answer that consumes the tool result;
- checker feedback generated independently of the actor;
- one real correction attempt after a failure, if used;
- full success/failure/UNKNOWN state and cost accounting.

Rules:

- A first success is an execution-feedback-recheck record. Do not fabricate a failure to manufacture a correction story.
- A first failure permits one real correction attempt. A failed correction remains in the pool as a failure.
- Missing raw, feedback, or required follow-up execution makes the trajectory incomplete and ineligible.
- Preserve successes, failures, refusals, UNKNOWN states, and invalid outputs. Do not curate only successful corrections.

## 6. Feedback whitelist v2

This design versions the feedback policy separately; it does not modify the old contract.

### Visible

- minimal source evidence and task requirements;
- actor-selected field, periods, unit, and tool parameters;
- actual tool return value and actor answer;
- permitted checker category and feedback-source description;
- actual subsequent attempt and its execution result.

### Hidden

- future-test references, hidden derivations, checker-internal values;
- historical gold values or checker-recomputed answers in actor-facing context;
- unexecuted corrections, model self-evaluation presented as execution feedback;
- test-output-generated experience or another arm's output;
- raw UID, origin/report mapping, arm identity, qualification class, or selection rank.

An actor-derived historical answer may numerically equal a reference without being leakage. Audit the information path rather than rejecting solely on numeric equality.

## 7. Model and tool pins

Design actor:

```text
model: Qwen3.6-35B-A3B-Q4_K_M.gguf
sha256: 4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d
```

This pin is inherited for design continuity, not effect-based model selection. Before collection, bind and verify:

- tokenizer and chat template;
- llama-server/runtime binary;
- generation parameters;
- prompt schema;
- calculator implementation and version;
- deterministic checker and unit/period adapter;
- raw capture and request/response correspondence logic.

The two-stage tool protocol is:

1. Plan request emits tool name and parameters only.
2. Calculator executes those exact parameters and returns the real result or error.
3. Consume request receives the actual return value and produces the final answer.
4. Every arm uses the same interface, complete task evidence, and request cap.
5. Tool errors are returned as errors, never silently corrected to gold.
6. No score feedback or post-test repair is shown during the task.

## 8. Future comparison arms

| arm | fixed content | explanation |
|---|---|---|
| B0 | no extra context; base task and tool instructions | raw ceiling and context interference |
| R | frozen field/period/unit/calculation rules | whether simple rules suffice |
| C | generic domain terms, units, and tool documentation; no solved examples or history | generic context and token-budget effect |
| U | two unfiltered real experiences from the same eligible mother pool | ordinary real-experience reuse |
| E | two evidence-qualified experiences selected from the same mother pool | incremental value of the qualification policy |

Matching requirements:

- U/E each use exactly two experiences per task with identical schema, field order, and selection procedure.
- Retrieval relevance is identical; only the qualification filter differs.
- R/C use two corresponding context blocks.
- All enhanced arms match added actor-token count within 5%; added blocks are capped at 2,048 tokens.
- No filler text, repeated padding, or deletion of failures to force matching.
- Task evidence is identical across arms. Sessions are independent and state-reset.
- Report collection, filtering, human review, and inference costs separately.

These arms do not fully remove ordinary few-shot effects. If E appears useful, a later separately authorized comparison must remove feedback/correction while retaining task and actual answer.

## 9. Collection budget draft

This budget is a request for the next gate and is **not active**.

| stage | scale | hard limits |
|---|---|---|
| current design | 0 model requests | max 4 preparation hours |
| new collection package | 12 source clusters x 1 task; each task up to two two-stage attempts = 48 requests; 3 two-stage qualification fixtures = 6 requests; total cap 54 | total tokens <=600k; input <=8192; output <=2048; retries 0; concurrency 1; one Beijing-time window <=90 min |
| later exploratory pilot | 8 source clusters x 2 tasks x 5 arms x 2 requests = 160 requests | total tokens <=1.7M; same per-request limits; retries 0; concurrency 1; one Beijing-time window <=120 min |

Each stage requires its own approval and exact Beijing-time window. Quotas do not transfer. Failed requests count. Unknown usage is charged at the reserved maximum. Judge calls, training calls, and external paid experiment APIs are zero.

Fixture requests may validate protocol, tool consumption, logging, scoring, and accounting. They never enter the experience pool or scientific denominators.

## 10. Future pilot measures

Primary measure: source-cluster-equal-weight task success. Success requires correct field, period, quantity, unit, and value under the frozen contract.

Also report:

- field/period/unit selection accuracy;
- tool-parameter correctness;
- answer-to-tool-return consistency;
- corrections and regressions versus each arm;
- refusals, UNKNOWN, format-invalid outputs, timeouts, and reference-unscorable cases;
- paired cluster differences, intervals, and actual costs.

Refusals and UNKNOWN remain in the denominator. If a reference is unscorable, report the validity gap and conservative bounds; do not silently convert it to a model error.

Exploratory continuation threshold:

- E improves by at least 12.5 percentage points over each of B0/R/C/U on cluster-average performance;
- at least 3/8 clusters are net positive for each comparison;
- no single cluster contributes more than half of the corrections;
- behavior change aligns with task improvement after conservative treatment of unresolved cases.

This is a resource threshold, not a significance test or mechanism proof.

## 11. Stop rules

Stop generation-side execution when any of the following occurs:

- model, input, prompt, tool, or checker identity differs from the frozen values;
- test references, cross-arm outputs, or unauthorized feedback enter model context;
- raw is lost/overwritten or request-response identity cannot be established;
- plan-to-tool-to-consume evidence is not trustworthy;
- source isolation or experience eligibility is invalidated;
- request, token, or time-window limits are reached.

Normal wrong answers, failed corrections, refusals, and predeclared invalid outputs are research outcomes and do not trigger automatic retries. Format-invalid model output is distinct from infrastructure failure to save/parse evidence; the latter stops the run.

Run-eligibility exclusions may be applied before the first request. After scientific requests begin, do not top up sample counts.

## 12. Required engineering changes before collection

This list is planning only:

1. Implement a deterministic source-cluster builder and freeze its canonicalizer/thresholds.
2. Produce an exact exposure register and cluster-disjoint split.
3. Implement a new isolated two-stage collection runner; do not modify the old WP-2 runner.
4. Bind model/runtime/template/tool/checker hashes in a collection manifest.
5. Implement atomic per-request raw capture with unique IDs and overwrite protection.
6. Implement the independent deterministic checker and reference-unscorable states.
7. Validate only with clearly marked engineering fixtures before any real collection.
8. Freeze the collection protocol and budget receipt before the first scientific request.

None of these changes is authorized or implemented in this directory.
