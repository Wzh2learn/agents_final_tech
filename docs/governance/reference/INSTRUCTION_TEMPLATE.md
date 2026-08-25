# INSTRUCTION Template — Cross-Session Task Dispatch

> **When to use**: Only for tasks that must cross session/machine boundaries.
> Within a single session, dispatch sub-agents directly — don't write instruction files.
> Typical use: local machine → remote training server (cross-machine, cross-session).

## Naming Convention
`instructions/INSTRUCTION_<topic>_<YYYY-MM-DD>.md`

## Lifecycle
1. Created with status ⏳
2. Detected by `session-reminder` hook on next session start
3. Executed → status 🔄
4. Completed → status ✅, archived to `instructions/archive/`
5. Registered in HANDOFF.md task record

## Template

```markdown
# Commander → {Target Agent}: {Topic}

> Status: ⏳ Pending / 🔄 In Progress / ✅ Closed
> Date: YYYY-MM-DD

## Context (why, which goal this serves)

(1-3 sentences, point to PLAN/HANDOFF entries, don't repeat details)

## Task Checklist

1. [ ] (Specific, verifiable — include full commands and expected output paths)
2. [ ] ...

## Constraints

- Pre-execution checklist (data paths / config diffs / output naming) confirmed with commander
- Resource constraints (GPU scheduling, storage limits)
- Do not touch production namespaces

## Report Requirements

- On completion: evidence for each task (log path / command output / file path)
- No verbal completion accepted — proof or it didn't happen
- Results backfilled to EXPERIMENTS_LOG.md; state changes to HANDOFF.md
```

## Why This Works

1. **Async by design** — target agent reads when it starts, not when commander writes
2. **Hook-detected** — `session-reminder` auto-alerts on pending instructions
3. **Evidence-based closure** — prevents "I did it" without proof
4. **Archival trail** — completed instructions move to archive, audit-friendly
