# Session Handoff Template

> Every agent session ends by writing a handoff file. The next session starts by reading it.
> This is the bridge between sessions — without it, every fresh context burns 5-10 minutes
> reconstructing state from scratch.

## Template

```markdown
# SESSION_HANDOFF — [Agent Role]
# Last updated: [ISO timestamp]
# Session: [session identifier or agent instance]

## Done this session
- [x] [What was completed, with specific file paths and results]
- [x] [Another completed item]

## In progress (not done)
- [ ] [What was started but not finished]
  - Status: [specific — what works, what doesn't]
  - Blocked by: [if anything]

## Known issues discovered
- [Issue 1]: [description, where it manifests, impact]
- [Issue 2]: [description]

## Recommendations for next session
1. [Highest priority task] — reason: [why this first]
2. [Second priority] — reason: [dependency/urgency]

## Notes for next agent
- [Gotcha that isn't captured elsewhere]
- [Environment quirk discovered]
- [Decision made that could be revisited]
- [Spec ambiguity resolved one way — document which way]
```

## Rules

1. **Write at end of EVERY session** — no exceptions, even if "nothing happened"
2. **Never delete history** — append and update, don't overwrite
3. **If handoff and git disagree, trust git** — handoff can be truncated by crashes
4. **Be precise about "in progress"** — "button works" vs "button renders but state doesn't refresh"
5. **Include file paths** — "fixed the bug" is useless; "fixed race condition in memory/update.py:142" is actionable
6. **Use absolute dates** — never "yesterday" or "last week"

## Anti-patterns
- Rewriting from scratch each session (loses audit trail)
- Vague status ("mostly done", "should work")
- Missing the "notes for next agent" section (highest-leverage field)
- JSON format (tried and abandoned — models write better prose than JSON for handoffs)
