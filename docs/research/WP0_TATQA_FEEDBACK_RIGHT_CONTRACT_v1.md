# WP-0 TAT-QA Feedback-Right Contract v1

> date: 2026-10-14 | author: Loop A under owner-authorized defaults | status: `IN_FORCE_FOR_WP2`
> supersedes: `WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_DRAFT_v1.md` for WP-2 execution and future pilot preparation
> boundary: governs which actually executed history/development episode material may appear in E/C contexts; authorises no new model call, pilot, publication, training, or write-back by itself

## 1. Purpose and authority

This contract turns the advisor draft's five open decisions into the frozen WP-2 v1 rule. The original draft remains unchanged as historical evidence. Any later change creates a new version and a new hash; this file is not silently edited after freeze.

## 2. Definitions

- **Episode**: one actually executed two-period task attempt on an origin disjoint from every development and test origin, including the actor's selected evidence, executed `calc` trace, final answer fields, checker verdict, and accounting metadata.
- **Feedback**: only the material explicitly allowed in Section 3. Gold values and hidden derivations are never feedback.
- **Correction**: a change to a new attempt that was actually executed. A hypothetical fix, post-hoc rationalisation, or unwritten alternative is not a correction.
- **Opaque id**: an actor-facing identifier derived from the frozen mapping; it does not contain or expose the raw TAT-QA uid or origin id.

## 3. Allow-list for E/C material

1. **Historical answers.** Show only actually executed attempt fields: `row`, `periods`, `delta_source`, `delta_target`, and `unit`, plus the checker verdict. Never display a gold value, checker-recomputed gold, hidden recomputation, or a comparison to gold.
2. **Tool trajectory.** Show the calculator's executed parameters and returned value in full. The tool trajectory is limited to the actual `calc` call recorded by the frozen runner.
3. **Corrections.** Show only an actually executed correction attempt and its complete tool trajectory. Do not present a before/after diff, hypothetical correction, or claimed correction that was not run.
4. **Retention and reuse.** Retain episodes for WP-2 execution, audit, and the degree thesis record. De-identified excerpt publication is not authorised here; any publication or external release requires a separate owner authorisation and must follow the applicable licence record.
5. **Attribution.** The existing derivative-marking requirement from `docs/datasets/tatqa_licence_record_v1.md` is retained verbatim: “The drift-v0 injection map and any task projection are *derivatives*; the artifact must state that the tables are derived from TAT-QA and that perturbations were added by this project.” The text is not rewritten for convenience.

## 4. Hard forbidden material

1. Any test or development item's gold value, answer derived by the checker, hidden recomputation result, or an item sharing its origin with a test item.
2. Any correction that was not actually executed.
3. Anything derived from an actor's own test-run outputs.
4. Raw TAT-QA uid or raw origin id in actor-facing text.
5. Unlicensed/private material or an unauthorised publication action.

## 5. Episode recording schema

Each executed episode is recorded as one canonical LF-terminated JSON object with:

```json
{
  "episode_id": "opaque",
  "origin_ref": "opaque_mapping_reference",
  "arm_role": "history",
  "task": {
    "period_late": "",
    "period_early": "",
    "requested_quantity": "",
    "target_unit": ""
  },
  "tool_trace": {
    "params": {},
    "returned_value": null,
    "trace_ref": ""
  },
  "answer": {
    "row": "",
    "periods": [],
    "delta_source": null,
    "delta_target": null,
    "unit": ""
  },
  "verdict": {
    "class": "",
    "source": "checker",
    "checker_version_hash": ""
  },
  "correction": {
    "executed": false,
    "steps": [],
    "execution_ref": null
  },
  "licence_note": "The drift-v0 injection map and any task projection are *derivatives*; the artifact must state that the tables are derived from TAT-QA and that perturbations were added by this project.",
  "sha256": ""
}
```

## 6. Frozen execution interpretation

- E may show one or two related real history episodes selected by the frozen structural rule.
- C must show the same format and the same number of real history episodes, selected from unrelated origins, with E/C lexical-token delta at most 5%.
- Both E and C may contain exactly the Section 3 feedback fields; neither may contain a gold value.
- Static S-arm unit/period rules are not feedback and are frozen separately in the WP-2 preregistration.

## 7. Stop rules

- A blocked, missing, or fabricated feedback field -> `FEEDBACK_RIGHT_NOT_SATISFIED`; do not improvise.
- Any gold leakage, raw-origin leakage, or unexecuted correction in an actor-facing block -> `STOP_THIS_PANEL`.
- Any publication or external release attempted under this file alone -> stop and report `PUBLICATION_NOT_AUTHORISED`.
