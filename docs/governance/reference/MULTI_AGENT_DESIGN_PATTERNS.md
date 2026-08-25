# Multi-Agent Design Patterns

> Patterns distilled from running a 4-layer agent hierarchy on a 2-month research project.
> Each pattern traces to a real failure that it prevents.

## Pattern 1: SSOT (Single Source of Truth)

**Problem**: Agents "remember" facts from earlier in the conversation but those facts become stale.
After context compression, the agent confidently states outdated information.

**Solution**: All state lives on disk. Agents don't "remember" — they "know where to read."

```
❌ Agent holds project state in context
✅ Agent reads CLAUDE.md/AGENTS.md/SESSION_HANDOFF at start of every session
```

**Implementation**:
- Every fact has exactly one authoritative file
- When in doubt, re-read the file rather than trusting context
- `grep '[ ]' SESSION_HANDOFF.md` to verify what's actually incomplete

## Pattern 2: Stigmergy (Trace-based Communication)

**Problem**: Direct agent-to-agent messaging creates synchronization nightmares.
Agent A sends a message to Agent B, but B's session expired. Message lost.

**Solution**: Agents communicate through files on disk, not direct messages.
Like ants leaving pheromone trails — the next agent follows the trace.

```
❌ Agent A tells Agent B "I've finished X"
✅ Agent A writes to SESSION_HANDOFF_A.md: "X is done, results in path/to/output"
   Agent B reads SESSION_HANDOFF_A.md at session start
```

**Key files**:
- `SESSION_HANDOFF_<role>.md` — per-agent state
- `CLAUDE.md` — shared project state (Commander maintains)
- `AGENTS.md` — shared technical context

## Pattern 3: 30-Second Cold Start

**Problem**: Fresh agent sessions spend 5-10 minutes "getting oriented" — reading random files,
asking clarifying questions, re-deriving project state.

**Solution**: Standardize the opening sequence. Fixed 6-step protocol, same every session.

```
1. pwd (confirm location)
2. Read SESSION_HANDOFF (prose state)
3. git log --oneline -20 (ground truth)
4. Count remaining work items
5. Run init/env check
6. Smoke-test the last "completed" feature
```

**Why it works**: Cost is 2-4K tokens. Payoff crosses over after 4 sessions.
Skip step 6 and you'll build on top of silently broken work.

## Pattern 4: File Boundary Enforcement

**Problem**: Multiple agents editing the same files creates merge conflicts and semantic drift.
Research Agent "helpfully" tweaks the code. Code Agent "helpfully" edits the paper.

**Solution**: Hard boundaries on which agent can write to which paths.

```
Research Agent: reading_notes/, planning/, paper analysis docs
Code Agent: code/, scripts/, configs
Writing Agent: draft_papers/, figures/
Commander: CLAUDE.md, SESSION_HANDOFF.md (top-level only)
```

**Enforcement**: In CLAUDE.md rules section. Agents that violate boundaries get corrected.

## Pattern 5: Instruction → Output → Feedback Loop

**Problem**: Commander gives vague instructions. Agent produces output that doesn't match intent.
Commander re-explains. 3 iterations wasted.

**Solution**: Structured instruction format with explicit output spec.

```markdown
## INSTRUCTION: [Commander] → [Target Agent]
Date: [ISO]
Priority: P0/P1/P2

### Context
[Why this task matters right now — 2 sentences max]

### Task
[Specific deliverable — what exactly to produce]

### Output spec
- Format: [markdown / code / analysis table]
- Location: [exact file path to write to]
- Length: [approximate scope]

### Constraints
- Do NOT: [explicit anti-goals]
- Must: [hard requirements]

### Done when
- [ ] [Checkable predicate 1]
- [ ] [Checkable predicate 2]
```

## Pattern 6: Anti-Hallucination Verification

**Problem**: Agent reports "task complete, all tests pass" without actually running the tests.
Or worse: agent runs tests, they fail, agent reports "done" anyway.

**Solution**: Verify agent claims against VCS reality.

```bash
# After agent claims "X is done":
grep '[ ]' SESSION_HANDOFF.md          # Check unchecked items
git diff --stat                        # What actually changed?
git log --oneline -5                   # What was actually committed?
```

**Rule**: Never trust an agent's self-report. Read the diff yourself.
This is the `verification-before-completion` skill applied to inter-agent trust.

## Pattern 7: Curriculum Phase Gating

**Problem**: Agents jump to complex work before foundations are solid.
Writing Agent starts polishing prose before the method is finalized.
Code Agent adds features before the baseline reproduces.

**Solution**: Explicit phases with gates. No phase advance without gate passing.

```
Phase 0: Baseline reproduction (gate: matches paper numbers ±1%)
Phase 1: Core method implementation (gate: trains without crash, loss decreases)
Phase 2: Ablation experiments (gate: main result beats baseline)
Phase 3: Paper writing (gate: all tables have final numbers)
Phase 4: Submission prep (gate: paper compiles, all refs resolve)
```

## Pattern 8: Compression-Safe State

**Problem**: Long conversations get compressed. Details from turn 5 are gone by turn 50.
Agent confidently acts on compressed (lossy) information.

**Solution**: Anything that matters lives on disk, not in conversation context.

```
❌ "Earlier we decided to use EMA with momentum 0.99"
✅ Decision recorded in docs/decisions/003-ema-momentum.md
   Agent re-reads the file when it needs the parameter
```

**Heuristic**: If you'd need to tell the next agent about it, write it to a file now.

## Composing Patterns

These patterns compose. A typical session uses:
- **Cold Start** (Pattern 3) → **SSOT** (Pattern 1) → **do work** → **Stigmergy** (Pattern 2) → **Handoff**

A typical Commander review uses:
- **Anti-Hallucination** (Pattern 6) → **Instruction** (Pattern 5) → **Boundary** (Pattern 4)

Start with Patterns 1-3. Add the rest as failures demand them.
