---
name: commit-and-pr-hygiene
description: Turn a change into reviewable output — atomic commits with why-messages, user-facing changelog entries, and a PR body a reviewer can approve fast. Use before opening a PR, cutting a release, writing release notes, or when the history is messy.
when_to_use: before a PR, messy history, "squash this", commit message help, cutting a release, writing release notes, summarizing a branch, "write the PR body", review prep
---

# Commit and PR Hygiene

Three outputs, one job: make a change readable to the next person. The commit explains *why*,
the changelog explains *what the user notices*, the PR body explains *what to verify*.

## 1. Commits (atomic, why-first)

- **Atomic** — one logical change per commit. Refactor and behavior change go in separate commits.
- **Message** — subject says WHAT in imperative ("Fix null pointer in user lookup"), body says WHY. "Fix bug" is useless.
- **Specific** — "Fix login failing when email has uppercase chars" tells the next person exactly what happened.
- Reorder/squash WIP and "fix typo" commits into the real changes (`git rebase -i`).
- Never mix an unrelated fix into a feature commit.

A good history is a debugging tool: `git bisect` and `git blame` only work if commits are atomic
and messages explain intent.

## 2. Changelog (user-facing)

Read the actual diff/commits, not the commit messages (they lie).

- Group into: **Added · Changed · Fixed · Removed · Security** (skip empty groups).
- Each line: user-facing impact, not implementation. "Fixed login failing for emails with uppercase
  characters" — not "fixed bug in user lookup".
- Lead with what the user notices. Bury internals.
- Call out breaking changes loudly, with the migration step.
- Link the PR/issue. No marketing fluff.

Output: markdown ready to paste. If a change has no user impact, leave it out.

## 3. PR description

A reviewer should understand the change without reading every line. Structure:

- **What & why** — the problem and the approach, 2-3 sentences.
- **Changes** — bullet the meaningful ones (skip noise like formatting).
- **How to verify** — the exact steps/commands the reviewer runs to confirm it works.
- **Risks / out of scope** — what could break, what you deliberately didn't do.
- **Screenshots** for UI.

Flag any decision the reviewer should weigh in on. Keep the PR small — if the diff is huge, say what
could be split out. No "fixes stuff".

## Completion

State which of the three outputs you produced (commit series / changelog / PR body), and for each:
the exact text, and what evidence it was derived from (diff, commit list, or issue link).
