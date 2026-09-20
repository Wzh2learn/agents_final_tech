---
name: eval-harness
when_to_use: tuning a prompt, changing a skill, comparing two models, regression-testing a workflow, "does this actually work better?", standing up an evaluator/critic agent, noticing evaluator scores drift upward across iterations, grading skill/PR/diff output and wanting reproducible verdicts
description: Build a repeatable eval loop that grades agent output with an LLM judge against a fixed baseline, and keep that judge honest by calibrating its rubric with concrete pass/fail anchors. Use when tuning a prompt or skill, comparing models, regression-testing a workflow, or when an evaluator's scores drift lenient over a long run.
---

# Eval Harness

Every prompt tweak in a long-running agent looks like an improvement in the moment. The only way to
know is a graded run against fixed inputs. Loopkit already ships `.claude/agents/verifier.md` — that is
your grader. Do not rebuild it.

## Part A — The three-stage loop

```
inputs.jsonl  ->  runner  ->  outputs.jsonl  ->  verifier (per row)  ->  verdicts.jsonl  ->  diff vs baseline
```

Each stage writes to disk. No stage holds the whole run in context.

### Stage 1 — inputs.jsonl
One JSON object per row: `{"id": "case-01", "input": "...", "expected": "..."}`.
- 20-100 cases is enough for a signal. More is nice, not required.
- Include known-hard cases, edge cases, and a couple of trivial ones as sanity anchors.
- Freeze the file. Rev the eval with a suffix (`inputs-v2.jsonl`) when you change it. Never edit in place — you lose the baseline.

### Stage 2 — runner
A dumb loop: for each row, call the model with the current prompt/skill, capture output, write
`{"id": ..., "output": ...}` to `outputs.jsonl`. No grading here — just capture.
- Same temperature every run (usually 0 for evals).
- Same seed / model version.
- Log the git SHA of the prompt/skill under test in the file header.

If the runner is smart it will bias the eval. Keep it dumb.

### Stage 3 — verifier
Fan out one subagent per row (see `subagent-fanout`). Each gets the input, the expected output (or spec),
the actual output, and the verifier system prompt from `.claude/agents/verifier.md`.
Verifier returns strict JSON: `{"pass": bool, "why": "..."}`. Collect into `verdicts.jsonl`.

### Diff vs baseline
Two runs of the same eval on two prompt versions -> compare pass rates per case:
- **Overall pass rate** — the headline.
- **Regressions** — cases that were green and went red. These block ship.
- **New passes** — cases that were red and went green. These justify ship.
- **Flappy cases** — inconsistent across reruns. Investigate.

A change that raises the mean but adds regressions is usually a loss.

## Part B — Calibrating the grader

An evaluator agent that reads the generator's reasoning drifts lenient. The generator explains why the
code is good; the evaluator, priming on that prose, starts nodding along. By sprint 8 the "skeptical
critic" is a rubber stamp. The fix is not "tell the evaluator to be stricter" — that works for one
iteration. The fix is **anchoring the rubric with concrete pass/fail examples the evaluator re-reads
every invocation**, and **re-prompting from scratch on a fixed cadence** so drift can't accumulate.

1. **Write the rubric as a scored checklist, not prose.** Each criterion gets a name, a one-line definition, and a binary or 1-3 score. Prose rubrics drift; checklists don't.
2. **Anchor every criterion with 2 concrete examples — one pass, one fail.** Real examples from prior runs, not invented ones. The evaluator reads these every invocation. This is the calibration.
3. **Forbid reading the generator's reasoning before scoring.** The evaluator sees the artifact and the rubric. Score first, then optionally read the reasoning to write the critique.
4. **Require the evaluator to quote the artifact in every verdict.** "Fails criterion 3 because <quoted line>" — not "fails criterion 3."
5. **Re-prompt from scratch every N iterations.** Empirically N=5 works. Kill the evaluator's context, reload system prompt + rubric + examples fresh. Do not compact; compaction preserves the drift.
6. **Log verdict distributions.** Track pass rate per criterion per sprint. A criterion that goes 40% -> 90% without a spec change is drift, not improvement.
7. **Spot-check with a held-out fail.** Every ~10 sprints, feed the evaluator an artifact you know fails. If it passes, the calibration has decayed — regenerate the example set from recent real runs.

### Calibration anti-patterns
- **"Be skeptical" with no examples.** Words don't calibrate. Examples calibrate.
- **Letting the evaluator read the planner's plan.** Same drift as reading the generator's reasoning.
- **One shared context across many gradings.** Batch-grading in one context is where leniency compounds fastest.
- **Invented examples.** Fake examples don't anchor to the artifact distribution the evaluator actually sees.
- **Scoring on a 1-10 scale.** The evaluator will cluster at 7. Use binary or 1-3.

## Red flags (harness level)

- **Grader is the same model that produced the output, with the same prompt.** Self-grading is lenient; use a different persona or model tier.
- **Eval passes 100% on day one.** Cases too easy, or grader is a rubber stamp. Add adversarial cases.
- **Eval takes >30 minutes.** Fan out; a serial 100-case eval is a serial bottleneck.
- **Grader sees your prompt under test.** It will grade what you wanted, not what happened. Feed it only spec + input + output.
- **Baseline lost.** Commit `verdicts.jsonl` to git.

## When NOT to do this
- One-off script — build a checklist, not a harness.
- Prompt that changes daily and won't stabilize — evals need a fixed target.
- Task where "correct" isn't checkable (open-ended creative writing) — use human eval or a rubric-based grader, not pass/fail.
- Single-shot grading with a fresh context every call — there's no drift to prevent and the examples are overhead.

## Completion

Report: the frozen inputs file and its case count, the runner's captured git SHA, the verdict
distribution per case, the regressions and new passes versus baseline, the verdict file path, and —
when part B applied — the rubric's criteria with their anchors and the last held-out-fail spot check.
