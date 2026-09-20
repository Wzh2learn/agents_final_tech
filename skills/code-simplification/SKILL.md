---
name: code-simplification
when_to_use: cleanup, "remove unused", before refactoring, dead branches, over-abstraction, a 200-line diff for a small ask, premature generality, arrow-shaped code, 3+ nested ifs, a function that's hard to follow
description: Reduce existing code — cut premature abstraction, flatten deep nesting, delete provably dead code — without changing behavior. Use during cleanup, before a refactor, or when a diff is bloated or a function is hard to follow.
---

# Code Simplification

Three cuts to the same end: less code that says the same thing. All three are behavior-preserving
refactors — if behavior changes, it is not a simplification, it is a rewrite under a misleading name.

## 1. Cut premature abstraction

Over-engineering is the default failure mode.

- **Premature abstraction** — a class/strategy/factory for one caller. Inline it. Abstract on the THIRD use, not the first.
- **Speculative config** — a parameter/flag/env var for something that never changes. Hardcode it until there's a real reason.
- **Speculative generality** — hooks, callbacks, or extension points with no second implementer.
- Mirror code is often cheaper than the abstraction that unifies it: two similar call sites are not
  yet a pattern.

## 2. Flatten nesting

Deep nesting hides bugs in the branches you didn't read.

- **Guard clauses** — handle the invalid/edge cases first and return early. The happy path drops to the left margin.
- **Invert conditions** — `if (!valid) return;` instead of wrapping the whole body in `if (valid) {...}`.
- **Extract** — a nested block with its own name is a function trying to get out.
- Target: no function needs more than ~2 levels of indentation to be read top-to-bottom.

## 3. Delete dead code

1. **Prove it's dead** — no references (grep the symbol across the repo, including dynamic/string usage and tests). Unused export ≠ dead if it's a public API.
2. Check it's not feature-flagged off (dead today, alive when the flag flips).
3. Delete it AND its now-orphaned tests, imports, and config.
4. Run the full suite + a build. Dead code removal should change behavior in exactly zero ways.

Bias to delete: every line someone has to read is a cost. But never delete what you can't prove is
unreachable — say "I think X is unused, confirm?" instead of guessing.

## Order of operations

Delete dead code first (it shrinks the surface), then flatten (it exposes structure), then de-abstract
(you now see the real call sites). Re-run the suite after each step so a regression is attributable to
one cut.

## Completion

Report each cut made, with: the symbol/block removed or restructured, the evidence it was dead or
single-use (grep result, caller count), and the test command output proving behavior is unchanged.
