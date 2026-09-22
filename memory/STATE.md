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

- The evaluation-track teacher-review package is complete, but the user has
  restored the conference paper's intended three-stage direction: large-model
  process evaluation, small-model distillation, and verification-gated rule
  evolution. `paper/research_story_v2.md` is the current narrative authority.
- The paper acceptance gate verifies 4 claims and 49 section, wording, evidence,
  figure, and delivery-file checks without model, service, or database calls.
- The master's-thesis scaffold now maps each chapter to the small-paper evidence
  it may inherit and the independent evidence it must still add.
- The three-stage asset map and Figure 1 distinguish established evaluation
  evidence, untrained distillation assets, and mechanism-only rule-evolution
  evidence. A distillation MVP preregistration exists but has not been executed.
- The sole next-phase execution plan is
  `docs/handoff/2026-09-22-paper-research-next-phase.md`; navigation, narrative,
  evidence ledger, execution and historical policy have separate authority.
  Only action-policy/rule-candidate distillation is currently proposed.
- Raw JSON was recounted locally: 494 gated gain/collateral events across 48
  source-table uids; 60 DPO pairs across 36 uids, all preferring skip to map_to.
  Counts are verified, not a completed data audit or DATA_GO decision.
- Data audit, zero-endpoint learnability probes and seven rule-gate baselines
  precede any training request. 4B is smoke-only; 8B is the primary student.
  A3 is conditional, and proposal/train, gate-validation, sealed test and
  future replay must remain separate. Plan Phase 6 controls early stop/split.
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

1. Execute plan §10 / Phase 1: zero-endpoint data audit, provenance/label
   reconstruction, four-layer uid manifests and per-view data/MDE gates.
2. Run Phase 1a learnability probes, then Phase 2 state-aware rule-gate replay;
   neither authorizes model calls or a training window.
3. Prepare the 24–48-hour internal direction package independently of training:
   mature evaluation draft plus current story Markdown. Its older direction
   DOCX must be regenerated and checked if a current Word version is needed.
4. Only after offline gates and user approval, run 4B smoke and 8B experiments
   (A3 conditional). Apply the plan's immediate split triggers and 10-04 cutoff.

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
- Paper acceptance gate: 49/49 checks passed; both focused paper suites: 6 passed
  on 2026-09-22 using the existing `.venv` (Python 3.12.3). System Python lacks
  python-docx; no dependency or global configuration was changed.
- docs_lint: 1 existing local skill-installation failure and 1 known protected
  docs/34 stale-date warning; not an all-green governance result. See THREADS.
- Endpoint/model/service/database/health-probe calls: 0. Protected docs/33 and
  docs/34 are unchanged. No Office visual rendering or GB10 runtime validation.
