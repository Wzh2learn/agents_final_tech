# CLAUDE.md Template for Multi-Agent Research Projects

> This template shows the structure of an effective CLAUDE.md for coordinating multiple AI agents
> on a long-running research project. Adapt the sections to your project's specific needs.

## Template Structure

```markdown
# Project: [Your Project Name]

## 路径注册表 / Path Registry
> Single source of truth for where things live. Agents read this to avoid guessing paths.

| Purpose | Path |
|---------|------|
| Source code | `code/` |
| Experiment logs | `code/logs/` |
| Paper drafts | `draft_papers/` |
| Session state | `<project>_session/` |
| Datasets | `datasets/` |
| Config | `config.yaml` |
| Reading notes | `reading_notes/` |
| Planning docs | `planning/` |

## Agent 分工 / Agent Responsibilities

| Agent | Role | Primary files | Handoff file |
|-------|------|--------------|--------------|
| Commander (Human+AI) | Strategy, prioritization, cross-agent coordination | All SESSION_HANDOFF* | SESSION_HANDOFF.md |
| Research Agent | Literature survey, method design, ablation planning | reading_notes/, planning/ | SESSION_HANDOFF_研究.md |
| Code Agent | Implementation, debugging, experiment execution | code/ | SESSION_HANDOFF_代码.md |
| Writing Agent | Paper drafting, polishing, figure generation | draft_papers/ | SESSION_HANDOFF_写作.md |

## 当前状态 / Current State
> Keep this section updated every session. Fresh agents read this first.

- **Phase**: [Research / Implementation / Experiment / Writing / Submission prep]
- **Priority queue**: [P0 tasks in order]
- **Blockers**: [What's blocking progress]
- **Last session**: [What happened, who did what]

## 规则 / Rules

1. **SSOT**: All state on disk. Don't "remember" — know where to read.
2. **Handoff files**: Update your SESSION_HANDOFF at end of every session.
3. **No cross-boundary edits**: Research Agent doesn't touch code/. Code Agent doesn't touch draft_papers/.
4. **Verify before claiming done**: Run the check, read the output, then claim.
5. **When stuck**: Report to Commander with what you tried. Don't guess.
```

## Why This Structure Works

1. **Path Registry** eliminates path-guessing hallucinations
2. **Agent Responsibilities** with explicit file boundaries prevents conflicts
3. **Current State** gives cold-start agents instant context (30-second orientation)
4. **Rules** encode hard-won lessons as constraints (not suggestions)

## Evolution Pattern

Start minimal (5-10 lines). Add rules only when something breaks. Every rule should trace back to
a real failure — if you can't point to the incident, the rule is premature.
