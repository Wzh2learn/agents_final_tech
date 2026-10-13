# WP-0 TAT-QA Feedback-Right Contract (DRAFT v1)

> date: 2026-10-13 | author: Loop D | status: `DRAFT_FOR_ADVISOR_APPROVAL - NOT IN FORCE` | no execution, no model call. Nothing here authorises sampling, runs, or training.
> parents: [task card](thesis_experience_v1_task_card.md) Sec.3.2, [package](WP0_TATQA_PACKAGE_v1.md) Sec.5-7, [adapter/checker contract](WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md).

## 1. Purpose

Define, before any pilot, exactly what "historical feedback" may be shown to the actor in the experience arms (E/C), where it may come from, and how it is recorded. The card currently leaves this as an owner decision ("历史任务答案可按获准反馈权限使用；未来测试答案不能进入"). This draft turns that into a checkable contract. It does not choose for the advisor; open questions are Sec.6.

## 2. Definitions

- **Episode**: one actually-executed two-period task attempt on an origin disjoint from all test origins, including the task statement, the actor's chosen row/periods/unit and calculator parameters, the calculator's return value, the final answer, and the outcome verdict.
- **Feedback**: the recorded outcome information about an episode that may be shown to the actor (see Sec.3 allow-list).
- **Correction**: a recorded change from a failed episode attempt to a corrected attempt that was **actually executed** (not a written-up rationalisation).
- **Independent verification**: the outcome verdict was produced by the checker/tool traces without the actor's participation (the checker recomputes gold from the table).

## 3. Allow-list (proposed) - what E/C may show

1. Task statement, the two period labels, and the requested quantity/target unit.
2. The actor's actually-chosen row/periods/unit relation and calculator parameters, with the tool return value.
3. The outcome verdict per the checker taxonomy (`correct` / `correct_other_form` / `wrong_unit` / `wrong_period` / `refused` / `unknown`).
4. Either (a) a corrected attempt that was actually executed, with its tool trace, or (b) the episode without correction, clearly marked as uncorrected.
5. Static unit/period rules for the S arm (not feedback; frozen at development).

## 4. Forbidden (hard) - never shown, never recorded as feedback

1. Any test item's gold, answers, or derived values; any item sharing an origin with any test item.
2. Corrections that were not actually executed (no fabricated, inferred, or written-up-only corrections).
3. Anything derived from the actor's own test-run outputs.
4. Unlicensed or private material (TAT-QA only, under CC BY 4.0).

## 5. Provenance and recording format (proposed schema)

One JSON object per episode, frozen before the pilot:

```
{episode_id, origin_ref (opaque hash; raw id never shown to the actor), arm_role: history,
 task: {period_late, period_early, requested_quantity, target_unit},
 tool_trace: {params, returned_value, trace_ref},
 answer: {delta_source, delta_target, unit},
 verdict: {class, source: "checker", checker_version_hash},
 correction: {executed: true/false, steps, execution_ref},
 licence_note: "TAT-QA (CC BY 4.0); derivative marking per licence record",
 frozen_at, sha256}
```

Blinding rule: the actor sees opaque episode ids only; mapping to origins stays in the frozen pool manifest. Attribution text for any released excerpt follows `docs/datasets/tatqa_licence_record_v1.md`.

## 6. Open decisions for the advisor (these are the contract's blanks)

1. May historical **answers** (not just verdicts) be shown at all, and in what form (full value / sign only)?
2. May the **tool trace** (parameters + returned value) be shown, or only the logical fields (row/periods/unit)?
3. Corrections shown as full before/after, or as the corrected attempt only?
4. Retention and reuse window for episodes; any restriction on publishing de-identified excerpts?
5. Confirm the attribution text and the derivative-marking sentence in the licence record.

## 7. Status and stop rules

- UNAPPROVED: until the advisor signs Sec.6, no episode may be collected, no context block may be built.
- If any allowed item cannot be constructed without violating Sec.4, stop and report `FEEDBACK_RIGHT_NOT_SATISFIED`; do not improvise.
- This contract governs E/C arms only; B and S arms need no feedback material.
