# Delegation Harness Failure Audit v1

> date: 2026-10-13 | author: Loop D | scope: diagnose why Loop A / Loop C delegations failed in this session; NO harness rebuild
> verdict: **WRONG DISPATCH MECHANISM USED.** The repository already has a designed, verified Loop A/C execution plane; this session used the Codex-app sub-agent facility instead, which is not that plane.

## 1. What was actually attempted, and what happened

| # | Dispatch | Mechanism used | Outcome |
|---|---|---|---|
| 1 | `qual_pr08` (PR-08 fact-check) | app `spawn_agent` | **worked** - returned a real report |
| 2 | `miner_stage_e` / `miner_code` / `miner_finqa` | app `spawn_agent` | worked, with self-recovered identity mix-ups (recorded in their reports) |
| 3 | `pr03_v3` | app `spawn_agent` | **role confusion** - behaved as Loop D, did Track A work instead of its brief |
| 4 | `track_a_figs` | app `spawn_agent` | **no task received** - "I came up empty on an assigned task ... What would you like me to pick up?" |
| 5 | `cite_verify` | app `spawn_agent` (x2) | **no task received** both times - "I'm set up and ready ... What would you like to work on?" |
| 6 | `pr03_v3b` | app `spawn_agent` | **role confusion + unbounded spawn** - spawned its own IEEE-template and language-audit children |
| 7 | `pr03v3_loopc_pre` | app `spawn_agent` | **no task received** - "I don't see a task or objective in this turn yet" |
| 8 | `multileaf_prov` | app `spawn_agent` | **hung** - ~50 minutes, no output, interrupted |
| 9 | `loopc_independent_audit` | app `spawn_agent` | **hung** - ~55 minutes, no output, interrupted |
| 10 | `loopc_tight` | app `spawn_agent` | no output before the user interrupted |

## 2. Root cause

The repository defines Loop A and Loop C as **separate harnesses driven by a scripted launcher**, not as peer sub-agents of the orchestrator:

- `scripts/graph/loop_ac_launcher.sh` (documented in `docs/governance/loop_ac_launcher_v1.md`, status ACTIVE since 2026-10-09) starts a **detached tmux** task on GB10 and runs either
  `codex exec --ephemeral --skip-git-repo-check -C <repo> -p loopa-exec --json` (Loop A) or the `claude` binary (Loop C),
  from a **prompt file**, with `timeout --signal=TERM --kill-after=30s`, and it writes `$HOME/wzh/loop_runs/<task-id>/<role>.log` plus a status JSON.
- The app's `spawn_agent` facility has none of those properties: no prompt-file contract, no outer timeout, and - as observed - inconsistent initial-task delivery and parent-context inheritance.

Every failure mode observed is explained by that mismatch:
- **No-task opens** (3 cases): the child started a fresh session and never received the brief as its first task; a `followup_task` re-delivery sometimes fixed it (`track_a_figs` began running only after the re-issue).
- **Role confusion** (2 cases): the child inherited the parent's framing and behaved as Loop D, including spawning its own children (the unbounded-spawn symptom is a consequence, not a separate defect).
- **Hangs** (2 cases): no outer timeout existed, so a stuck child simply ran until interrupted.

## 3. Answers to the four audit questions

1. **Was role/goal/scope/constraints transmitted correctly?** The briefs were correct in content but were transmited through a channel that does not guarantee first-turn delivery, and the channel has no prompt-file contract. **Transmission = unreliable (channel defect, not content defect).**
2. **Did sub-agents receive complete context?** No, consistently: either nothing (mode A) or the wrong context (mode B). Under the designed launcher the prompt file *is* the task contract, which is exactly the property that was missing.
3. **Were there recursion / role confusion / contamination / ownership problems?** Yes: unbounded child-spawning (one case), role confusion (two cases), parent-context contamination (same two), and ownership blur (the child that did Track A work edited the manuscript outside its brief). All are symptoms of the channel, not of the briefs.
4. **Does it affect later Loop A execution?** **It does not have to.** The designed launcher passes preflight today (`binaries/config present; credentials not read`) and was smoke-verified on 2026-10-09 (codex_rc=0, claude_rc=0, detached self-test PASS). Loop A/C dispatch should go through `loop_ac_launcher.sh`, not the app facility.

## 4. Minimal fix (low-risk, configuration-level only; no harness rebuild)

1. **Dispatch Loop A/C through `scripts/graph/loop_ac_launcher.sh`** with a prompt file: `start a|c <task-id> <prompt-file> <timeout>`; observe with `status` and `logs`.
2. Keep the app facility only for tasks whose outcome is not on the critical path, and always re-issue the brief with `followup_task` plus an "ack first" line if the first reply looks like a fresh session.
3. Never let a delegate touch frozen artifacts unless the brief names that path as owned (the one contamination incident edited the manuscript).
4. Prefer the designed channel for anything that must be *independent* (Loop C) because the designed plane is the one the governance model actually describes.

**Nothing in the repository needed to change for this fix; it is a dispatch-convention correction.**

## 5. Consequence for this session

The outstanding **independent Loop C audit** - the last gap blocking "signable" status - can now be dispatched through the designed launcher instead of being written off. That dispatch is part of this round.