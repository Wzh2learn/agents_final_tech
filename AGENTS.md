<!-- FOR AI AGENTS - Human readability is a side effect, not a goal -->
<!-- Managed by agent: keep this file concise and move detail to its authority -->
<!-- Last updated: 2026-09-22 | Last verified: 2026-09-22 -->

# Repository Guidelines

**Precedence:** explicit user instructions override repository files; otherwise the closest `AGENTS.md` to the files being changed wins. This root file contains global defaults only.

## Read first

1. [`memory/CORE.md`](memory/CORE.md) — durable architecture and runtime baseline.
2. [`memory/STATE.md`](memory/STATE.md) — short current repository snapshot.
3. [`memory/THREADS.md`](memory/THREADS.md) — sole current ledger for open decisions and blockers.
4. [`docs/INDEX.md`](docs/INDEX.md) — documentation catalog and status labels.
5. [`docs/SKILL_ROUTING.md`](docs/SKILL_ROUTING.md) — project skill selection rules.

`HANDOFF.md` and `memory/archive/` are historical evidence, not current state.

## Commands

| Task | Command | Notes |
|---|---|---|
| Safe local setup/start | `bash scripts/run.sh` | Foreground; refuses an occupied port |
| Start application only | `./serve.sh` | Canonical launcher used by all active deployment paths |
| Focused tests | `PYTHONPATH=src python3 -m pytest <test-file> -q` | Prefer the smallest relevant suite |
| Document lint | `python3 scripts/docs_lint.py --json /tmp/docs_lint_report.json` | Writes report outside the repo |
| Skill validation | `python3 skills/skill-doctor/scripts/skill-doctor.py --root skills --format json` | Existing warnings are tracked debt |

Full test runs may perform optional read-only health probes. GB10 results are authoritative; local results must be labelled local.

## Architecture

| Path | Responsibility |
|---|---|
| `src/web/` | FastAPI routes, templates, static assets |
| `src/biz/` | Application services and orchestration |
| `src/agents/` | In-application agent graph |
| `src/tools/` | Retrieval and document tools |
| `src/storage/` | PostgreSQL/PGVector, persistence, files |
| `src/*_mcp_server/` | Isolated read-only MCP adapters |
| `scripts/` | Operational commands, migration-era production helpers, experiments |
| `tests/` | Pytest unit and contract tests |
| `config/` | Runtime configuration and schema overrides |
| `docs/` | Current docs, experiments, governance evidence, archive |

Keep routes thin and reusable application logic under `src/`. Production parser and ingest logic lives in `src/biz/`; `scripts/m1_statement_parser.py` and `scripts/m1_rag_ingest.py` are compatibility CLIs only. Do not add production imports from `scripts/`.

## Workflow

1. Confirm the task boundary and inspect `git status` before editing.
2. For multi-step work, write an explicit goal, done conditions, exclusions, and stop conditions.
3. Reproduce defects with a failing test before changing behavior.
4. Run the smallest relevant check after each change; inspect the full diff before committing.
5. Use atomic conventional commits and never rewrite shared history without explicit approval.
6. Before claiming completion, run fresh verification and report failures, warnings, and unverified surfaces.

## Boundaries

### Always

- Use Python 3.12 and `PYTHONPATH=src` for direct test execution.
- Use `PGDATABASE_URL`; the development database is `vector_db` and default HTTP port is 5050.
- Preserve the existing `RAGService` and PostgreSQL/PGVector knowledge backend.
- Keep MCP read-only unless an explicitly reviewed task authorizes writes.
- Put current status in `memory/STATE.md`, open items in `memory/THREADS.md`, and durable decisions in `memory/DECISIONS.md`.
- Archive documents with `git mv`; update `docs/INDEX.md` in the same commit.
- Treat `logs/graph/docs_lint_warn_baseline.md` as the known-warning ceiling, never as permission to suppress warnings.

### Ask first

- Restarting or probing production services, model endpoints, or databases.
- Changing public APIs, persistent schemas, CI/CD, dependencies, or worker-count policy.
- Deleting or renaming tracked historical material.

### Never

- Modify `docs/33_导师指导吸收_科研三线升级.md` or `docs/34_专利_小论文_大论文协同研究路线.md` during the current governance pass.
- Reopen frozen TAT-DQA experiments.
- Modify `tests/test_m1_service.py`, `scripts/graph/frozen_hashes.txt`, or frozen schema material without explicit authorization.
- Commit `.env`, credentials, private samples, model weights, generated datasets, logs, or local databases.
- Read or print credential file contents such as `~/.claude/settings.json` or `~/.codex/auth.json`.
- Claim local checks prove GB10 runtime or production behavior.

“Zero endpoint” means zero model calls, canaries, judges, and new runs. If a permitted read-only health probe occurs, report its count explicitly.

## Skills and governance

- Repository `skills/` is the versioned source; distribution lists live in `scripts/graph/sync_skills.sh`.
- Assignment registry: [`docs/governance/SKILL_REGISTRY.md`](docs/governance/SKILL_REGISTRY.md).
- Load no more than five task skills unless a red-line rule requires another.
- Pre-commit guards live in `scripts/graph/hooks/`; do not weaken checks to make a run green.
- `scripts/graph/governance_drift_scan.py` in normal mode writes reports/backlog entries; use `--cron` for a read-only report.

## Scoped AGENTS.md

- [`docs/archive/AGENTS.md`](./docs/archive/AGENTS.md) — archived documentation is read-only history.
- [`skills/agent-rules/AGENTS.md`](./skills/agent-rules/AGENTS.md) — rules for the vendored agent-rules skill.

When instructions conflict, follow the closest scoped file, then this file, then linked descriptive documentation.
