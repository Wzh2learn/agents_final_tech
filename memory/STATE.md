# Current State

> Updated: 2026-09-22 | Scope: repository state only | Runtime: not probed in this session

This file is the short current snapshot. Open decisions and blockers belong in
[`THREADS.md`](THREADS.md); durable decisions belong in [`DECISIONS.md`](DECISIONS.md).
The previous long snapshot is preserved as
[`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

Improve engineering governance and operational reliability on branch
`test/compaction-guard-abort`, one independently verified change at a time.

## Repository state

- Primary product path: counterparty-statement M1 parsing and M2 traceable RAG QA.
- Application: Python 3.12, FastAPI, PostgreSQL/PGVector.
- Canonical HTTP launcher: root `serve.sh`.
- Canonical database variable: `PGDATABASE_URL`; development database: `vector_db`.
- Default HTTP port: `5050`, configurable with `M1_PORT`.
- Documentation entry point: [`../docs/INDEX.md`](../docs/INDEX.md).
- Skill routing: [`../docs/SKILL_ROUTING.md`](../docs/SKILL_ROUTING.md).

## Completed in the current governance pass

- Local quickstart no longer kills an existing process or backgrounds Uvicorn.
- Runtime configuration now agrees on `PGDATABASE_URL`, `vector_db`, and port 5050.
- Docker images include the required `config/` tree.
- Local, Docker, systemd, supervisord, compatibility, and restart launch paths delegate to `serve.sh`.
- Production parser and ingest implementations live in `src/biz/`; legacy script imports and CLIs delegate to those canonical modules.
- Every tracked script is assigned to production, operations, experiments, or archive in `scripts/catalog.toml`, with a test preventing unclassified additions.

## Runtime status

- GB10 is the only authoritative runtime and formal full-test environment.
- No service, model endpoint, database, or live health endpoint was contacted during the changes above.
- Therefore deployment/live status remains unverified in this snapshot.
- Last formally recorded topology and metrics are historical baselines in [`CORE.md`](CORE.md), not a claim that services are currently live.

## Next engineering-governance work

1. Harden skill synchronization and repair skill metadata/validation gaps.
2. Split oversized parser/RAG modules only after stable behavioral boundaries are covered.

## Protected boundaries

- Do not modify `docs/33_导师指导吸收_科研三线升级.md` or
  `docs/34_专利_小论文_大论文协同研究路线.md` in this governance pass.
- TAT-DQA work remains frozen.
- Do not restart or probe production services without explicit authorization.
- Preserve the existing `RAGService`/PGVector knowledge backend and read-only MCP boundary.
- Never commit credentials, private samples, model weights, generated datasets, local databases, or `.env`.

## Verification status

- Local checks are deterministic development evidence only; they are not GB10 runtime proof.
- Focused launcher/runtime contract suite: 8 tests passed on 2026-09-22.
- Known local warning: pytest reports unknown `asyncio_mode` because the optional plugin is absent.
