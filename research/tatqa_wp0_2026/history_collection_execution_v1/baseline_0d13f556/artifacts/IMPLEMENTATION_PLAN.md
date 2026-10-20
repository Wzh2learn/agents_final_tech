# Implementation Plan

Status: `COMPLETE`
Execution budget: maximum 4 hours; zero generation/service/judge/training calls.

| step | deliverable | status |
|---|---|---|
| 1 | Freeze goal, scope, and stop rules in `PROMPT.md` | DONE |
| 2 | Reuse pinned raw/candidate/split inputs and materialize 32-task isolated reference manifest | DONE |
| 3 | Implement fixed prompts, strict schemas/parsers, runtime identity preflight, and authorization-gated runner | DONE |
| 4 | Integrate budget -> immutable raw -> plan/tool/consume with crash and overwrite tests | DONE |
| 5 | Run local and GB10 zero-call tests; generate complete hash bundle | DONE |
| 6 | Dispatch one Loop C incremental review; fix blockers and perform targeted re-check only | DONE |
| 7 | Write the short execution-readiness application and final verification | DONE |

## Change Mapping

- Reused read-only sources: pinned TAT-QA raw hashes, `candidate_items_v2.json`, `history_collection_offline_v1/SPLIT_PROPOSAL.json`, and offline calculator/checker/raw-capture contracts.
- New execution artifacts live only under `history_collection_execution_v1/`.
- Prior audit claims remain unchanged; `IMPLEMENTATION_DELTA.md` will map each new execution component to the old component and identify behavior additions.
- Revision 3 is fixed. The 19 designated clusters remain conservatively isolated; their real exposure nature is not reopened.
