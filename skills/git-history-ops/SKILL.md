---
name: git-history-ops
when_to_use: '"it worked last week"', 'a regression, unclear which commit broke it', '"revert this"', 'a bad deploy, one commit broke prod, undo without losing other work', 'rebase, squash, "update my branch", interactive rebase, force-push'
description: Work with git history safely — bisect to the commit that introduced a bug, revert precisely without losing unrelated work, and rebase/rewrite only what is safe to rewrite. Use when something worked before and broke, a specific commit needs undoing, or before any history rewrite.
---

# Git History Operations

Three operations on the history of a repo. All three share one rule: **never destroy work to fix a
smaller problem**. Pick the operation that matches the question you are actually answering.

## 1. Locate: which commit introduced this?

1. Find a known-good commit and a known-bad one. Confirm both by actually checking out and testing.
2. `git bisect start; git bisect bad <bad>; git bisect good <good>`.
3. At each step, run the SMALLEST test that distinguishes good from bad. Mark `git bisect good/bad`.
4. When git names the first bad commit, read its diff. The bug is in those lines — don't guess elsewhere.
5. `git bisect reset`. Report: the commit, the line, the one-sentence cause.

Automate it: `git bisect run ./repro.sh` if you have a script that exits non-zero on the bug.
Bisect answers *where*, not *why* — read the diff before theorizing.

## 2. Undo one change, keep the rest

Don't `git reset --hard` away three good commits to undo one bad one.

- **Single commit** — `git revert <sha>` creates an inverse commit; history stays intact and shared-branch-safe.
- **One file from a commit** — `git checkout <good-sha> -- path/to/file`.
- **Hunk-level** — `git checkout -p` to revert specific changes, keep the rest.
- **A merge** — `git revert -m 1 <merge-sha>` (pick the mainline parent).

On a shared branch, always revert (forward), never rewrite history. Reproduce the breakage first so
you revert the RIGHT thing, then verify the revert actually fixes it.

## 3. Rewrite history, only where safe

1. **Backup first** — `git branch backup/<name>` before any rewrite. Free undo.
2. Rebase onto the latest base: `git fetch; git rebase origin/main`.
3. Resolve conflicts one commit at a time. Test after the rebase, not just that it "completed".
4. **Never rewrite shared history** — if others pulled the branch, rebasing it forces them into pain.
   Rewrite only your own un-pushed/un-shared commits.
5. Push with `--force-with-lease`, never bare `--force` (lease refuses if someone else pushed).

If anything goes sideways: `git reflog` finds the pre-rebase state; `git reset --hard backup/<name>`
restores it.

## Choosing the operation

| Situation | Operation |
|---|---|
| Don't know which commit broke it | Bisect (1) |
| Know the commit, it's already pushed/shared | Revert (2) |
| Know the commit, it's local-only and unshared | Revert or interactive rebase — revert is still safer |
| Need to clean up your own unpushed WIP | Interactive rebase (3) |
| Need to remove a commit others have pulled | Revert (2), never rewrite |

## Completion

Report which operation ran, the evidence it produced (first-bad commit SHA and diff, or the revert
SHA and the passing test, or the backup branch name), and the state of the branch afterwards
(`git log --oneline -3` plus `git status`).
