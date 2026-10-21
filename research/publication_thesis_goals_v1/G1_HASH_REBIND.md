# G1 Evidence Hash Rebind

Date: 2026-10-21

The pre-submission verifier found stale byte bindings after the verified
workspace integration and the current G1 statistical amendment. No frozen raw
result was edited in this Goal.

| Artifact | Previous binding | Current binding | Reason |
|---|---|---|---|
| `APPLICATION_RESULTS.json` | `fb4a4cf0...` | `5c2e5755...` | Current workspace/GB10-integrated HEAD bytes; file not edited in G1 |
| `APPLICATION_RESULTS_v1_raw_text_overlap.json` | `586148d5...` | `5c58d172...` | Current workspace/GB10-integrated HEAD bytes; file not edited in G1 |
| `SOURCE_MANIFEST.json` | `95a63961...` | `f82ec146...` | Current workspace/GB10-integrated HEAD bytes; file not edited in G1 |
| `saner_rene_manuscript_scope_lock_v1.md` | `dadf4020...` | `21673b54...` | Scope lock amended with the source-table UID statistical evidence |

The complete previous and current hashes are retained in Git history and in the
current claim matrix/figure binding manifest. This is a provenance repair, not
a new scientific result.
