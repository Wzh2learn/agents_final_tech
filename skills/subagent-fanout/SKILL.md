---
name: subagent-fanout
description: Parallelize independent sub-jobs across fresh-context subagents instead of one bloated context. Use when a goal branches into many independent pieces.
when_to_use: analyze N items, fix M files, search K sources, anything embarrassingly parallel
---
# Subagent Fan-out
One context loaded with ten jobs' worth of material is the exact shape that triggers context rot. Ten small contexts don't.
- Spawn one subagent per independent unit (one file, one source, one check). Each gets a fresh context window.
- An **orchestrator** synthesizes their results — it never does the per-unit work itself.
- A worker's report is a **claim, not evidence**. The orchestrator verifies findings against first-hand carriers before synthesizing; retractions, downgrades, and direction corrections from that verification are first-class outputs, not embarrassment (reference run: a six-dimension scan's findings survived verification as 1 retracted / 3 downgraded / 1 corrected — forwarded as-is, one false alarm would have shipped).
- Give each worker a tight role and only the input it needs.
- Use ONLY when the pieces are genuinely independent. Sequential dependencies stay in one chain.
Fan-out for breadth (research, multi-file edits, multi-source verification). Keep it serial when step N needs step N-1's output.
