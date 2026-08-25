# Memory File Template — Project Iron Rules & Lessons

> A single authoritative file for hard-won lessons that must survive across sessions.
> Not a journal — only validated, repeatedly-proven rules belong here.

## When to write to this file
- A lesson has been learned through real failure (not theoretical risk)
- The same mistake has happened 2+ times
- A user/commander has explicitly stated a rule
- A constraint is non-obvious and would be violated without this record

## When NOT to write here
- Temporary state (use HANDOFF.md)
- In-progress plans (use PLAN docs)
- Code documentation (use code comments/README)
- Single-occurrence notes (not yet proven as a pattern)

## Format

```markdown
# Project Memory (Iron Rules + Lessons)

> Shared across all agent sessions. Read on session start.
> Only add validated lessons — if it hasn't caused 2+ failures, it's not ready.

## Iron Rules (user-emphasized, never violate)

### 1. [Rule title] (date established)
- [Specific, actionable rule — what to do/not do]
- [Evidence/source of the rule]
- [Exception conditions, if any]

### 2. [Another rule]
...

## Resource Constraints (hardware/environment facts)

- [GPU count, memory, storage limits]
- [Validated batch sizes, speed benchmarks]
- [Known driver/library incompatibilities with evidence]

## Lessons Learned (pattern: problem → root cause → fix → evidence)

### [Topic] (date)
- **Problem**: [What went wrong]
- **Root cause**: [Why — with evidence, not guessing]
- **Fix**: [What to do instead]
- **Evidence**: [Commit hash / log path / experiment that proved it]
- **Times hit**: [N — threshold for hook escalation is 3]
```

## Maintenance Rules
1. Use absolute dates (never "yesterday" or "last week")
2. Each entry must have evidence (commit, log path, or experiment reference)
3. When a lesson gets its own hook → note "automated by [hook-name]" and stop repeating it
4. Review quarterly — remove rules that no longer apply (code/infra changed)
5. Supersede, don't delete — mark old entries with "superseded by [new entry]"
