# Current State

> Updated: 2026-09-22 | Scope: repository state only | Runtime: not probed in this session

This file is the short current snapshot. Open decisions and blockers belong in
[`THREADS.md`](THREADS.md); durable decisions belong in [`DECISIONS.md`](DECISIONS.md).
The previous long snapshot is preserved as
[`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

Make the repository's research work serve the conference paper and master's
thesis directly. The canonical execution and acceptance entry is
[`../docs/research/README.md`](../docs/research/README.md).

## Repository state

- Primary product path: counterparty-statement M1 parsing and M2 traceable RAG QA.
- Application: Python 3.12, FastAPI, PostgreSQL/PGVector.
- Canonical HTTP launcher: root `serve.sh`.
- Canonical database variable: `PGDATABASE_URL`; development database: `vector_db`.
- Default HTTP port: `5050`, configurable with `M1_PORT`.
- Documentation entry point: [`../docs/INDEX.md`](../docs/INDEX.md).
- Skill routing: [`../docs/SKILL_ROUTING.md`](../docs/SKILL_ROUTING.md).

## Completed in the current governance pass

- The conference-paper teacher-review package is complete: clean Markdown and
  DOCX manuscripts, a Chinese review note, claim manifest, acceptance report,
  and internal-readiness decision are linked from `docs/research/README.md`.
- The paper acceptance gate verifies 4 claims and 49 section, wording, evidence,
  figure, and delivery-file checks without model, service, or database calls.
- The master's-thesis scaffold now maps each chapter to the small-paper evidence
  it may inherit and the independent evidence it must still add.
- Local quickstart no longer kills an existing process or backgrounds Uvicorn.
- Runtime configuration now agrees on `PGDATABASE_URL`, `vector_db`, and port 5050.
- Docker images include the required `config/` tree.
- Local, Docker, systemd, supervisord, compatibility, and restart launch paths delegate to `serve.sh`.
- Production parser and ingest implementations live in `src/biz/`; legacy script imports and CLIs delegate to those canonical modules.
- Every tracked script is assigned to production, operations, experiments, or archive in `scripts/catalog.toml`, with a test preventing unclassified additions.
- Skill distribution stages and validates each copy before activation, preserves the previous install for rollback, and rejects unsafe single-skill paths.
- Skill routing names only installable top-level skills, and `skill-doctor` audits nested bundled skills without counting them as active installs.

## Runtime status

- GB10 is the only authoritative runtime and formal full-test environment.
- No service, model endpoint, database, or live health endpoint was contacted during the changes above.
- Therefore deployment/live status remains unverified in this snapshot.
- Last formally recorded topology and metrics are historical baselines in [`CORE.md`](CORE.md), not a claim that services are currently live.

## Next work

1. User reviews and sends the internal package to the advisor when appropriate;
   the agent does not send it externally.
2. Apply advisor feedback only to the affected manuscript sections, then rerun
   the paper acceptance gate and regenerate the DOCX.
3. If the advisor requires stronger external validity, preregister either a
   second dataflow or a second scorer before any new run.
4. Continue the thesis with TH-I3 strong baselines after the conference-paper
   story is stable; keep TH-I4 conditional on its preregistered gate.

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
- Paper acceptance gate: 49/49 checks passed; focused paper tests: 3 passed on
  2026-09-22. The DOCX contains one embedded PNG plus a native Word checkpoint
  table; no visual Office renderer was available locally.
