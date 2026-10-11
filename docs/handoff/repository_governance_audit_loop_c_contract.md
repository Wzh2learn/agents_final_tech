# Task Contract: Repository Governance and Fresh-Context Audit - Loop C

- Task ID: `repository-governance-audit-c-20261011`
- Role: Loop C / GB10 independent governance and reviewer audit
- Mode: read-only except existing test commands
- Inputs: A inventory reports, LOCAL truth addendum, FinQA lineage, scope-lock/claim-matrix, current memory/index/paper assets

## Required Checks

1. Verify LOCAL/GB10 truth table and explain the local-unmounted limitation.
2. Verify dirty/untracked classification is exhaustive and no UNKNOWN is proposed for deletion.
3. Verify FinQA lineage preserves invalid/superseded runs and does not promote them to current evidence.
4. Verify current Paper E scope-lock/claim matrix is canonical; Route B is `NO / STOP_BRANCH`.
5. Verify memory/STATE/THREADS/Dispatch/INDEX consistency and identify stale status references.
6. Verify paper/figure/submission asset status labels.
7. Inspect external repro directories and large-file policy.
8. Review commit groups and identify unsafe or mixed commits.
9. Run/inspect necessary verification:
   - focused tests;
   - docs lint;
   - claim validator;
   - submission audit;
   - frozen-hash validation;
   - index/state checks.
10. Decide:
    - `REPOSITORY_GOVERNANCE = PASS | FAIL`
    - `GIT_SYNC = GO | STOP_GIT_SYNC`
    - remaining blockers.
11. Fresh-context opportunity review:
    > If this were your first look at the repository, what are the three highest-value, most-easily-missed research/submission/experiment opportunities?
    Use only current repo evidence; do not propose execution.

## Output

Return a report containing:

- truth-table verdict;
- asset classification/lineage verdict;
- commit/sync recommendation;
- verification results;
- remaining dirty/external assets;
- governance debt;
- `REPOSITORY_GOVERNANCE`;
- `GIT_SYNC`;
- fresh-context top-3 opportunities;
- Loop D next-step recommendation.

## Forbidden

- Modify scientific artifacts or paper claims.
- Delete/move files.
- Commit/push/merge/rebase.
- Run GPU/training/formal scientific experiments.
- Treat invalid/superseded results as current evidence.

## Success Exit

The audit either certifies governance readiness or identifies exact blockers and safe commit/sync boundaries.
