# Ground-Truth Isolation — Structural Defense Against Reward Hacking

> If an agent can read the answer key while producing the answer, it optimizes against the key
> instead of the task. This is an **architecture** problem, not a prompt problem — you cannot
> fix it by instructing the agent not to look.

## The Failure Mode

An agent that can see what counts as a correct answer will, over time, route toward the
*surface features* of correctness rather than the underlying quality those features are meant
to signal. Scores go up; held-out performance doesn't.

Critically: **this is not about intent.** A perfectly cooperative agent still drifts this way,
because the gradient of "make the score go up" points at the key when the key is visible.

It shows up at three granularities:

| Granularity | What leaks | Typical symptom |
|-------------|-----------|-----------------|
| **Single session** | Agent reads the scoring rubric before generating | Output mirrors the rubric's vocabulary; fails on a rephrased rubric |
| **Pipeline stage** | Expected outputs appended to the prompt as "negative examples" | Suspiciously high pass rate on the eval set only |
| **Calibration** | Model processed the gold set before reporting confidence | Confidence tracks the key, not its own uncertainty |

In all three the mechanism is identical: **ground-truth material and candidate generation
coexist in one context or one filesystem layer.**

## Why Prompt-Level Fixes Fail

"Do not look at `labeled_data/`" is an instruction, and instructions are:
- forgotten after compaction
- overridden by a later "read all files in the directory to understand the task"
- silently violated by a tool call the agent didn't reason about (a glob, a grep, a `cat *`)

The fix has to be a property the agent *cannot* violate, because the material isn't reachable.

## The Pattern: Tiered Isolation

Borrowed from how evaluation harnesses are actually built for agentic research systems
(Anthropic's automated weak-to-strong researcher, 2026, uses a three-tier sandbox):

| Tier | Where ground truth lives | Valid for |
|------|------------------------|-----------|
| **Tier 1 — Local dev** | Same filesystem as the agent | Development only. **Results are not evidence.** |
| **Tier 2 — Container, redacted** | Removed from the image the agent sees | Integration testing |
| **Tier 3 — Remote, server-side** | Never on the agent's machine; scoring happens server-side | **The only tier whose numbers count** |

The load-bearing design note from that work: the local tier's results "might not be legit"
*because* the agent can find the labeled data on the local filesystem — and the maintainers
wrote that warning into the README rather than trusting the isolation to hold. Treat
tier-1 numbers as smoke tests, never as results.

### Minimum viable version (no infrastructure)

You don't need a remote scoring server to get most of the benefit:

1. **Split the process boundary.** The scorer runs as a separate invocation with the candidate
   output as its *only* input — it never receives the generation context, reasoning trace, or
   the prompt that produced the output.
2. **Split the filesystem boundary.** Ground truth lives outside the agent's working directory.
   If the agent has `Bash(*)`, "outside the working directory" is not enough — put it on a
   different machine or hold it until after generation.
3. **Hold the key until after submission.** Sequence: generate → freeze the candidate (hash it)
   → *then* reveal the key → score. A frozen hash makes "the candidate didn't change after
   the key appeared" verifiable rather than assumed.
4. **Declare the tier in the result.** Every reported number carries which tier produced it.
   A number without a tier is a number you can't defend.

## Related Failure Mode: Shortcut Reliance

Lu et al. (2026, *Nature* 651:914–919), documenting the first fully autonomous AI research
system to pass blind peer review, name a pipeline-scale cousin of this problem: models exploit
**spurious correlations** in the training data, score well on the target metric, and produce
findings that don't hold up. Same shape, different layer — the system optimizes a proxy that
was easier to reach than the thing the proxy stood for.

The defense is the same in kind: the check must be *structurally* unable to see the shortcut.
Which is why "add a rule telling the model not to take shortcuts" is not a defense.

## Checklist

Before trusting any evaluation number produced by an agentic pipeline:

- [ ] Could the generating agent read the answer key, rubric, or gold set? (filesystem, prompt, tool output)
- [ ] Does the scorer receive *only* the candidate output — not the reasoning that produced it?
- [ ] Was the candidate frozen (hashed) before the key became reachable?
- [ ] Is the isolation tier recorded alongside the number?
- [ ] If the answer to any of the above is "I think so" — the answer is no. Verify it.

## Relationship to Other Patterns

| Pattern | Covers | Distinct because |
|---------|--------|-----------------|
| [`../../../skills/self-eval-bias/`](../../../skills/self-eval-bias/) | Same context grading its own output | About *reasoning* contamination; this doc is about *answer-key* contamination |
| [`TRIPLE_AUDIT_PATTERN.md`](TRIPLE_AUDIT_PATTERN.md) | Reviewer anchored by reading the draft first | Anchoring between agents; this is leakage from the eval artifact |
| [`FOUR_CONCEPT_SEPARATION_PATTERN.md`](FOUR_CONCEPT_SEPARATION_PATTERN.md) | Completion impersonating judgment | Once ground truth leaks, even a correctly-typed CheckResult is measuring the wrong thing |
| `DEATH_PATTERN_MATCHER.md` (not imported) | Blind replay of historical cases | Its role separation (case author ≠ executor ≠ answer-checker) is this pattern applied to a replay |

---

**Sources.** Primary: Anthropic automated weak-to-strong researcher (2026) — three-tier sandbox
architecture and the local-mode warning; Lu et al. (2026), *Nature* 651:914–919 — shortcut
reliance in autonomous research pipelines. The framing of these two cases as one architectural
pattern follows the `shared/ground_truth_isolation_pattern.md` synthesis in
[`Imbad0202/academic-research-skills`](https://github.com/Imbad0202/academic-research-skills)
(CC BY-NC 4.0) — that document is credited as the source of the *synthesis*; the text here is
independently written and no content is copied from it.
