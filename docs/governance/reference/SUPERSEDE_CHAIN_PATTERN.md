# Supersede Chain Pattern — Knowledge Evolution Tracking

> **Core principle**: Never delete old conclusions. Mark them as superseded with a pointer
> to what replaced them and why. This creates an auditable knowledge evolution trail.

## Why This Matters

In long-running research projects, conclusions get overturned regularly:
- An experiment you thought was positive turns out to be noise
- A "validated baseline" gets invalidated by a data pipeline bug
- A design decision made under old constraints becomes wrong under new ones

Without supersede chains:
- Agents re-discover old conclusions (wasting GPU hours)
- Two documents contradict each other with no way to know which is current
- "Why did we stop doing X?" has no answer

## The Pattern

### In experiment logs:
```markdown
| Old conclusion | Current conclusion | Evidence | Date |
|---------------|-------------------|----------|------|
| "Method X improves recall +2%" | "Method X was noise — data had a bug" | exp_rerun_0803 | 2026-08-03 |
| "LR=2e-3 is optimal" | "LR=1e-3 confirmed optimal, 2x has no effect" | exp15 | 2026-07-30 |
```

### In documents:
```markdown
~~Old statement that's no longer true~~ 
**Superseded 2026-08-03**: [new statement]. Evidence: [commit/experiment].
```

### In HANDOFF files:
```markdown
## Supersede log (this session)
- Overturned: "eval cache rebuilds every epoch" → actually frozen after epoch 1 (Bug #3)
- Overturned: "exp5 is our best result" → based on buggy data, invalidated
```

### In memory/rules files:
```markdown
### Rule N (date) — ~~SUPERSEDED by Rule M (new-date)~~
[Original text preserved for audit]
**Why superseded**: [explanation]
**New rule**: see Rule M
```

## Principles

1. **Never delete** — strike through and annotate, don't remove
2. **Always point forward** — superseded entry must say what replaced it
3. **Evidence required** — every supersede needs a commit, experiment, or explicit decision
4. **Timestamp everything** — absolute dates only
5. **The chain is the audit trail** — reviewers/new team members trace the evolution

## Where Supersede Chains Live

| Document type | Chain location |
|--------------|---------------|
| Experiment log | Dedicated "supersede" section at bottom |
| HANDOFF | "Supersede log (this session)" section |
| Rule files | Inline strikethrough + "superseded by" annotation |
| Architecture docs | Version history section with supersede entries |
| Goal cards | §八 Review section |

## Anti-patterns

- **Silent overwrite**: changing a number in a doc without noting what it replaced → future reader has no idea the old number existed
- **Deleting failed experiments**: "it didn't work so I removed the row" → next person tries the same thing
- **Orphan supersede**: marking something superseded without saying what replaces it → reader knows it's wrong but not what's right
- **Supersede chain too deep**: if a conclusion has been superseded 3+ times, collapse into a summary + keep only the latest live entry

## Real Example (Anonymized)

```
Experiment Log — Supersede Chain:

| Date | Old belief | New belief | Evidence |
|------|-----------|-----------|----------|
| 07-28 | "All exp1-5 are valid baselines" | "exp1-5 based on buggy data, reference only" | Data pipeline audit |
| 07-29 | "τ=0.05 might help cold-start" | "τ=0.05 destroys precision, only helps diversity" | exp_tau005 full eval |
| 07-30 | "popularity weighting has a sweet spot" | "α is a switch not a knob — any α>0 kills recall" | 4-point curve |
| 08-03 | "warm-start = equivalent to scratch" | "warm-start systematically -1pp, acceptable but not free" | 3-day chain eval |
```

This chain tells anyone joining the project: "don't try popularity weighting, don't try τ<0.1, don't trust exp1-5 numbers, and warm-start has a known cost."
