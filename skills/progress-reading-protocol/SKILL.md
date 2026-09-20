---
name: progress-reading-protocol
description: Run the fixed 6-step session-opening sequence (pwd, read progress, git log, count remaining features, init.sh, smoke-test the last feature) and, when the smoke test fails, the broken-window recovery that reverts and re-opens the feature before any new work. Use at the very first tool calls of a fresh coding session, after a context reset or crash, or before picking up new work.
when_to_use: very first tool calls of any fresh coding-agent session, rehydrating after a context reset or crash mid-project, verifying a claimed-shipped feature before picking up new work, start of any session in a multi-session project, right after reading progress notes and running init.sh
---

# Progress-Reading Protocol

You have no memory of the previous session. The repo does. Every fresh session burns 5-10 minutes
reconstructing state unless you follow a fixed opening sequence — with the sequence, it drops to 30-60
seconds. The cost is 2-4k tokens at the top of every session; the payoff crosses over past four sessions
on the same project.

Skipping steps is the failure mode. Sessions that skip the smoke-test step (6) reliably build new
features on top of silently broken ones — the region this skill's second half exists to close.

## When to apply

- First tool calls of any coding-agent session in a multi-session project.
- After a context reset, compaction, or crash mid-project — treat the resumed context as a fresh session.
- Before you write a single line of new code. No exceptions for "quick fixes."

## Procedure — run in order, no skipping

1. **`pwd`** — confirm you are in the project directory. You may only edit files below this path.
2. **Read the progress/shift-notes file** — the previous session's prose handoff.
3. **`git log --oneline -20`** — see what was actually committed. If the progress file and the git log disagree, trust the git log. The progress file can be truncated by a crashed write; the log is append-only.
4. **Count remaining features** — e.g. `cat feature_list.json | jq '[.[] | select(.passes==false)] | length'`. Adjust the field name to the project's schema. This anchors you to the source of truth for completion state.
5. **`./init.sh`** — bring up the dev server. If this fails, fixing it is your only job this session. Do not skip to feature work with a broken environment.
6. **Smoke-test the most recently "completed" feature** — drive it end-to-end via browser automation, `curl`, or the actual CLI. Not unit tests. If it fails, invoke part B below.

Only after all six steps pass do you pick new work.

## Part B — Broken-window recovery (step 6 failed)

Across shift-notes-driven sessions, agents sometimes mark a feature complete after unit tests pass —
even when the feature is end-to-end broken. The next session opens the repo, sees a green git log, and
builds on top of a broken foundation. By the time anyone notices, three features are stacked on the crack.

**The check:** before picking new work, exercise the most recently "completed" feature end-to-end.
If it fails, treat it as your only job this session.

1. **Read the last "done" entry** in the shift notes / feature list (whichever the project uses).
2. **Drive the feature end-to-end** using the actual runtime path — browser automation, HTTP request, CLI invocation. Not the unit test.
3. **Compare observed behavior to the spec** — the `steps` field on the feature, or the acceptance criteria in the spec.
4. **If it works** — proceed to normal work selection. Note the check in the shift notes ("verified feature N still green").
5. **If it fails** —
   - `git revert` the commit that claimed completion (do not force-push).
   - Set that feature's status back to `not-done` in the feature list.
   - Note in shift notes: "reverted feature N, cause: <one line>".
   - Fix it. That is your entire session.

Do not pick new work on top of a broken previous feature. Ever.

### What "end-to-end" means

The check must exercise the path the user actually takes. Anything less is theater.

| Feature shape | Valid check | Invalid check |
|---|---|---|
| Web UI button | Playwright click -> observe DOM | `expect(handler).toHaveBeenCalled()` |
| HTTP endpoint | `curl` the route -> check status + body | Unit test on the handler function |
| CLI flag | Invoke the binary with the flag -> observe output | Import the parser, assert on the AST |
| Background job | Trigger it -> wait -> assert side effect | Assert the job function returns |

### Red flags — the check is not doing its job

- **You're reading tests instead of running the feature.** Tests can pass while the feature is broken (wrong route, missing CORS, config mismatch). Drive the runtime.
- **You add a mock to make the check pass.** The mock is the bug. Remove it, watch the failure, that's the real state.
- **You "fix" by editing the feature list to match reality** ("oh it never supported X"). No. Revert. Re-open. Fix the code or negotiate scope in the spec, not the ledger.
- **You skip the check because "it worked yesterday".** Yesterday's session doesn't run today's dev server.

## Anti-patterns

- **"I already know this repo, I'll skip the read."** You do not. The context you have is the context in front of you.
- **Reading the progress file but not the git log.** The prose lies; the log does not.
- **Running `init.sh` and assuming success without smoke-testing a feature.** The dev server can start clean while every route is broken.
- **Smoke-testing with unit tests.** Unit tests can pass while the feature is end-to-end broken.
- **Batching the 6 steps into "let me just get oriented."** The steps are cheap because they are fixed. Improvising the orientation is where tokens leak.

## Cost

Roughly 2-4k tokens and 30-60 seconds of wall-clock at the top of every session. Payback crosses over
past ~4 sessions on the same project. The broken-window check alone is 30-90 seconds per session in a
healthy project, and roughly 4x fewer premature completions when enforced.

## Related

- `shift-notes` — the ledger this protocol reads and writes.
- `verify-before-done` — run this on the current session's diff *before* claiming done, so the next session doesn't have to recover.

## When NOT to apply

Single-shot sessions with no prior state, or the very first session of a project (there is nothing to
read yet — run the initializer instead).

## Completion

State the six steps and their results in order, name the feature smoke-tested and the runtime path used,
and say explicitly whether part B ran (and if so, the revert SHA and the feature's new status).
