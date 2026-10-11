# Graph Loop Authority Map v1

> Status: active governance reference | Updated: 2026-10-10 | Supersedes: no prior authority map
> Scope: FinQA v2 and the Graph Loop handoff/preflight path. Historical artifacts remain immutable.

## Rule

Every object below has exactly one current authority. Other files may summarize it, but they must carry an `AUTHORITY_REF` and a `SUPERSEDED` marker when stale.

| Object | Current authority | Owner | Update point | Downstream rule |
|---|---|---|---|---|
| Current status | `memory/STATE.md` | Loop D | end of each Graph Loop | A/C read before dispatch |
| Open blockers / decisions | `memory/THREADS.md` | Loop D | when a blocker changes | do not duplicate in task prose |
| Durable decisions | `memory/DECISIONS.md` | Loop D/user | after adjudication | cite decision id, not chat text |
| Navigation | `docs/INDEX.md` | Loop D/docs-sync | same change as new/archived docs | one entry per live authority |
| Claims | `paper/claim_manifest_v1.json` plus the matching result receipt | Loop D/user | after C verdict | result class must match evidence |
| Handoff | `docs/governance/reference/SESSION_HANDOFF_TEMPLATE.md` | Loop D | every session end | include authority paths, hashes, gates and stop state |

## FinQA Authority Register

| Authority object | Path | SHA-256 | Status | Superseded | Superseded by | Owner |
|---|---|---|---|---|---|---|
| Analysis plan | `research/finqa_v2_20261010/FINQA_V2_ANALYSIS_PLAN.md` | `57f8b0d68195ec471842d4b6a4092c657876e9f133d0c1724f8aa5b2289d1e61` | `FROZEN_FOR_INDEPENDENT_LOOP_C_AUDIT_NOT_EXECUTION_AUTHORIZATION` | `NONE` | `NONE` | Loop D |
| Frozen sample manifest | `research/finqa_v2_20261010/finqa_v2_frozen_sample_manifest.json` | `802798a3621fa995feddee31c02fae5bd4e30f80473ca282e3c6c3809a618b18` | `FROZEN_SAMPLE_IDS_AND_JOINS_NOT_EXECUTION` | `NONE` | `NONE` | Loop A |
| Split manifest | `research/finqa_v2_20261010/finqa_v2_split_manifest.json` | `aa69ca1371922f2be0cfd44bf592ff2ace27ea9f6b46c957befe837a658573ab` | `DETERMINISTIC_GROUP_DISJOINT_SPLIT_FROZEN_NOT_EXECUTED` | `NONE` | `NONE` | Loop A |
| Causal join audit | `research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json` | `280c563c5e701cf81f75d85664f6880f8133723693ddbc63a641db804a909ca7` | `JOIN_CANDIDATE_IDENTIFIED_NOT_FROZEN` | `NONE` | `NONE` | Loop A |
| Scorer source | `research/finqa_independent_observation_scorer_v2.py` | `b48ed17c4aae2a1d70312e9c93c113d0e45b60d2429e83627162e78337d667e5` | `FROZEN_SCORER_SEMANTICS_NOT_EXECUTED` | `NONE` | `NONE` | Loop A |
| Scorer binding manifest | `research/finqa_v2_20261010/finqa_v2_scorer_binding_manifest.json` | `2ec7caceda048b71ade13780f97f33888122fe02b253aad380e32a7a1f949a8b` | `INDEPENDENT_SCORER_BINDINGS_FROZEN_NOT_EXECUTED` | `NONE` | `NONE` | Loop A |
| Binding-v3 runtime contract | `research/finqa_v2_20261010/binding_v3/FINQA_V2_RUNTIME_BINDING_INTERFACE_V3.md` | `144f45714ca2ab28de763661353bede65597ca63a673201a35a1fc952c08d7a1` | `SUPERSEDING_BINDING_ONLY_QUALIFICATION_INTERFACE_PENDING_LOOP_C_REVIEW` | `research/finqa_v2_20261010/binding_v2/FINQA_V2_ARTIFACT_BINDING_CONTRACT_V2.md` | `NONE` | Loop A |
| Current historical task card | `research/finqa_v2_20261010/binding_v2/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md` | `555fdb792b2545f163fb88033b940e6cc4d52db1ca3910d5a31e2259108a246a` | `SCORER_BINDING_GO_PASS_READY_NOT_EXECUTED` | `NONE` | `NONE` | Loop D |
| Bootstrap seed/replicate plan | `research/finqa_v2_20261010/finqa_v2_analysis_plan.json` | `02607daed45d19aae9697302122cf37493c1d6ddd8d2078ac3a4084b3ff64b35` | `FROZEN_PRERESULT_ANALYSIS_PLAN_NOT_EXECUTED` | `NONE` | `NONE` | Loop D |
| Previous invalid-run receipts | `research/finqa_v2_20261010/results/finqa_v2_formal_execution_receipt.json`<br>`research/finqa_v2_20261010/results_binding_v2_rerun/finqa_v2_formal_execution_receipt.json` | `2d94d30003f9de563402c71b34b58dc492e8e545682278ffb6f1c40d3d87320f`<br>`8a0017e1ae5f065fe73a01bb1af1a0f5033199fbe25369263d4184c27d8eb071` | `FORMAL_RUN_INVALID` | `NONE` | `NONE` | Loop A |

## Supersession Rules

- `FINQA_V2_FORMAL_RESULT_REPORT.md` and the first invalid receipt remain `INVALID_BUT_PRESERVED`; they are not scientific results.
- The raw/normalized binding-v2 contract is superseded for runtime wiring by binding-v3, but its raw provenance and lossy normalization audit remain valid historical evidence.
- A task card is authoritative only for execution scope; it cannot override the analysis plan, manifests or scorer source.
- Chat messages, `loop_runs/*.log` and agent summaries are evidence pointers only. A conclusion becomes project state only after it is materialized under `docs/experiments/` or the applicable authority path and indexed.

## Required Handoff Fields

Each Loop D -> A -> C -> D handoff must include:

1. authority paths and SHA-256 values;
2. assumptions and immutable/mutable fields;
3. exact allowed and forbidden actions;
4. preflight level and command;
5. required output paths;
6. stop conditions;
7. evidence class;
8. result/claim boundary.

## Current FinQA Status

- SOURCE/ID/JOIN/SPLIT/analysis-plan/scorer-semantics: inherited and not reopened.
- Raw/normalized hash mismatch: diagnosed as a binding-domain issue; binding-v2 retained.
- Runner metadata seam: known root cause `RUNTIME_METADATA_NOT_FORWARDED_TO_BINDING_SEAM`; binding-v3 qualification is the current engineering task.
- No formal scientific rerun is authorized while `RUNTIME_BINDING_INTEGRATION_GO` is unresolved.
