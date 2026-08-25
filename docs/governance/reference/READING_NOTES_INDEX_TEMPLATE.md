# Reading Notes INDEX Template — Systematic Paper Tracking

> A structured index that lets any agent find relevant papers in <10 seconds,
> understand threat level, and decide whether to deep-read the full notes.

## Design Philosophy

- The INDEX is a **lookup table**, not a reading list
- Each paper gets ONE row — enough to decide "do I need to read the full notes?"
- Full notes live in separate files — INDEX only has the pointer
- Organized by **research direction**, not chronologically
- Threat level tells you urgency: 🔴 must address, 🟡 should cite, 🟢 can reference

## Template

```markdown
# Reading Notes Index

> Papers: ~N | Directions: M | Last updated: YYYY-MM-DD
> Purpose: Writing Agent/Research Agent uses this to find relevant work quickly

## Reading Standards (for all new notes)

### Note Template (§0-§8 structure)
- §0: Version info (note version, paper citation, update status)
- §1: One-sentence contribution (paper's own claim, no project mapping)
- §2: Problem definition (what/why/how different from prior work)
- §3: Method structure (input/output/core modules/dataflow)
- §4: Training objective (loss/supervision/end-to-end/auxiliary tasks)
- §5: Experiment design (datasets/baselines/metrics/what's proven/not proven)
- §6: Limitations & attack points (admitted + hidden + reviewer angles)
- §7: Mechanism abstraction (type/reusable mechanisms/boundaries/misuse risks)
- §8: Relationship to our work (how it relates, what to borrow/defend against)

### Threat Levels
| Mark | Meaning | Action |
|------|---------|--------|
| 🔴 | Direct competitor — overlapping track/narrative | Must discuss in Related Work, prepare rebuttal |
| 🟡 | Indirect — same direction, different dimension | Cite in RW, explain orthogonality |
| 🟢 | Low threat / complementary / not competing | Cite as needed, can support our claims |

## Overview

| Direction | Papers | Coverage | Key competitors |
|-----------|--------|----------|----------------|
| A. [Direction 1] | N | 100% | [Paper X 🔴] |
| B. [Direction 2] | M | 80% | [Paper Y 🟡] |
| ... | | | |

## A. [Direction 1] (N papers)

> [One-line description of this research direction]

| # | Paper | Threat | Notes file | Type | Relationship | One-line conclusion |
|---|-------|--------|-----------|------|-------------|-------------------|
| A1 | [Title (Venue Year)] | 🟢 | [link](file.md) | deep-read | [how it relates] | [core takeaway] |
| A2 | ... | 🟡 | ... | skim | ... | ... |

## B. [Direction 2] (M papers)
...
```

## Maintenance Rules

1. **New paper → add row immediately** (even before reading — mark as "unread")
2. **After reading → fill one-line conclusion** (forces synthesis)
3. **Threat level is relative to YOUR project** (same paper can be 🔴 for one project, 🟢 for another)
4. **Review threat levels quarterly** — new papers can elevate old ones from 🟢 to 🟡
5. **Direction grouping > chronological** — reader cares about "what's in my area" not "what came out this month"

## Usage Patterns

### For Writing Agent:
"Find all 🔴 papers" → these MUST be discussed in Related Work with explicit differentiation

### For Research Agent:
"Find papers in Direction B with mechanism type X" → cross-reference for design inspiration

### For Review/Defense prep:
"What are the attack points (§6) of our closest competitors?" → prepare rebuttal ammunition

### For new direction exploration:
"Show me all papers tagged 'memory compression'" → scope the landscape before designing
