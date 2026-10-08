# Skill Assignment Registry

> 状态: 活跃（机器对账源） | 更新: 2026-09-22 | 取代/被取代: 取代根 AGENTS.md 内嵌长表

仓库 `skills/` 是内容源，`scripts/graph/sync_skills.sh` 是分发实现，本表只维护 Loop 配属。skill 的用途与触发条件以各自 `SKILL.md` 为准，避免在注册表重复说明。

## 配属注册表

| Loop | Harness | skills | 用途 |
|---|---|---|---|
| A | Codex CLI | systematic-debugging, executing-plans, subagent-driven-development, jinrong-docs-sync, m1-gap-triage, m2-rag-playbook, graph-loop-rules, agent-prompt-contracts, research-writing-skill, office-academic-skill, scientific-toolkit-skill, verify-before-done, shift-notes, context-budget, tool-restraint, spec-first, sprint-contract, eval-harness, experiment-autopsy, decision-record, paper-polish-and-audit, recsys-toolkit, paper-review-check, algorithm-description, neat-freak, code-cleanup-helper, skill-doctor, skill-map, agent-rules, cloudflare-deploy, codebase-map, dispatching-parallel-agents, figma, figma-code-connect-components, figma-generate-design, figma-generate-library, figma-implement-design, figma-use, jupyter-notebook, pdf, playwright, playwright-interactive, security-threat-model, skills-best-practices, vercel-deploy, writing-plans, experiment-analysis, research-driven-design, offline-eval-playbook, code-pathology, organize-logs, train-monitor, gpu-env, data-sync, dependency-audit, authz-check, input-validation, secret-scan, init-script-contract, progress-reading-protocol, harness-stripping, structured-output, prompt-caching, pdf-ingestion, planner-spec-expand, skill-merger, skill-hook-trigger, inquiry-methods, socrates, dream-engine, exp-lifecycle, commit-and-pr-hygiene, code-simplification, git-history-ops, db-schema-change, frontend-quality, testing-practices | Active execution set |
| C | Claude Code | requesting-code-review, receiving-code-review, review-codebase, differential-review, spec-to-code-compliance, security-best-practices, jinrong-docs-sync, m2-rag-playbook, agent-prompt-contracts, verify-before-done, self-eval-bias, repo-audit, readme-audit, paper-review-check, audit-cycle, owasp-review, sql-review, feature-list-json, subagent-fanout, using-loopkit, eval-harness, inquiry-methods | Active audit set |
| A | Codex CLI | verification-before-completion | DEPRECATED 2026-08-25; retained for audit history and replaced by verify-before-done |

## Governance

- Only Loop D may add or remove distributed skills.
- Update this registry and `sync_skills.sh` in the same commit.
- Deprecated skills remain visible here but are not distributed.
- Validate metadata with `skill-doctor`; do not suppress existing findings.
