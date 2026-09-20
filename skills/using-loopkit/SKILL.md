---
name: using-loopkit
description: Use when starting any conversation in a loopkit-enabled project - establishes how to find and use loopkit's skills, requiring skill invocation before ANY response including clarifying questions.
---

# Using Loopkit

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a loopkit skill applies to what you are doing, INVOKE it.

IF A SKILL APPLIES, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This overrides "just answer quickly" instincts. Not negotiable.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or reading files. If it turns out wrong for the situation, drop it.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Where the skills live

Skills are files at `.claude/skills/<name>/SKILL.md`. Each has YAML frontmatter with `name` and `description` (the description is a trigger phrase, not a summary). Load a skill by reading its SKILL.md when its trigger matches your task.

## Skill routing (by task shape)

| Task shape | First skill |
|---|---|
| "Fix this bug" / test failing / crash | `systematic-debugging` |
| "It broke between two commits" | `git-history-ops` |
| "Flaky test" | `testing-practices` |
| "Add a feature" / write anything new | `spec-first`, then `testing-practices` |
| "Refactor" / dead code / deep nesting | `code-simplification` |
| About to claim done / commit / open PR | `verify-before-done` + `self-eval-bias` |
| Review a diff | `verify-before-done`, `commit-and-pr-hygiene` |
| Frontend / UI work | `frontend-quality` |
| Security touch | `owasp-review`, `authz-check`, `input-validation`, `secret-scan`, `dependency-audit` |
| Data / SQL / migrations | `sql-review`, `db-schema-change` |
| Docs / changelog / README | `commit-and-pr-hygiene`, `decision-record`, `readme-audit` |
| Git ops | `git-history-ops`, `commit-and-pr-hygiene` |
| Test suite gaps | `testing-practices` |
| Running out of context | `context-budget`, `tool-restraint` |
| Parallel work | `subagent-fanout` |
| Starting a fresh project / major feature | `planner-spec-expand`, then `feature-list-json`, then `init-script-contract` |
| Bootstrapping into an existing multi-session project | `progress-reading-protocol` |
| Entering an implementation sprint | `sprint-contract` |
| Calibrating a reviewer / evaluator | `eval-harness` |
| New Claude/Sonnet/Opus model landed | `harness-stripping` |

Full list: `ls .claude/skills/`.

## Red Flags — STOP and check for a skill

| Thought | Reality |
|---|---|
| "This is just a simple question" | Questions are tasks. Check first. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I remember this skill" | Skills evolve. Read the current SKILL.md. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "Tests pass, we're good" | `verify-before-done` says: run the exact command, read the output, then claim. |
| "I'll do both features while I'm in here" | `spec-first` says: one goal spec on disk per session. Never two at once. |
| "The reviewer will let this slide" | `self-eval-bias` says: assume it will confidently praise. Calibrate first. |

## Priority when multiple skills apply

Process skills first (spec-first, systematic-debugging, planner-spec-expand, sprint-contract), then implementation skills (frontend-quality, sql-review, etc.), then finishers (verify-before-done, self-eval-bias, commit-and-pr-hygiene).

- "Let's build X" → `planner-spec-expand` → `feature-list-json` → `sprint-contract` → domain skills → `verify-before-done`.
- "Fix bug Y" → `systematic-debugging` → fix → `verify-before-done`.
- "Session open in existing project" → `progress-reading-protocol` → `sprint-contract` → work.

## User instructions win

CLAUDE.md, AGENTS.md, and direct user requests override loopkit skills. Only skip a skill workflow when the user has explicitly said to.
