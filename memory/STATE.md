# Current State

> Updated: 2026-09-23 | Scope: main alignment and Phase 1a data-supplement precheck | Runtime: no GB10/service operation

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions:
[`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md).
The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

Keep `test/compaction-guard-abort` aligned with current `main` while completing the highest-value repository-only prerequisite for the paper line. The selected work is the Phase 1a private data-supplement precheck: turn the existing `DATA_NO_GO` gap list into a deterministic contract before consuming another GB10 window.

This is software and governance preparation, not a Phase 1a learnability run. It produces no training data, model output, baseline score, or paper-facing experimental result.

## Git state

- Pre-delivery baseline: local `main`, freshly fetched `origin/main`, and local `test/compaction-guard-abort` were `061d8819bd7c3b03159f6f0df183887be57edef6`; `HEAD...origin/main = 0/0`.
- Pre-delivery `origin/test/compaction-guard-abort` was `0aee20d`. The repository-only Phase 1a contract is delivered on that test branch; use `git rev-parse HEAD origin/test/compaction-guard-abort` for the exact published head.
- Alignment used fast-forward history only. No reset, rebase, stash, or cleanup was used.
- Protected `docs/33*`, `docs/34*`, frozen tests, schemas, and `scripts/graph/frozen_hashes.txt` remain untouched.

## Repository baseline

- Product: M1 counterparty-statement parsing and M2 traceable RAG QA.
- Python 3.12, FastAPI, PostgreSQL/PGVector; root `serve.sh` is the launcher.
- Database contract: `PGDATABASE_URL`, development `vector_db`; HTTP default 5050.
- Production parser/ingest live in `src/biz/`; scripts are compatibility CLIs.
- Research authority is layered: research README resolves conflicts, story defines claims, asset map tracks evidence, and the existing handoff controls execution.
- Code in Git does not prove GB10 skills, hooks, services, private data, or runtime state are installed or healthy.

## Research maturity

- Stage E: mature evaluation subdraft with 95 tables/118 injections and bounded claims.
- Stage D: no trained-student result. Existing zero-shot matrices are not distillation evidence.
- Stage R: rejection/collision mechanism evidence exists; stable net benefit and long-term rollback evidence do not.
- P1 local audit covers 37 historical artifacts, but action-SFT/risk remain `DATA_NO_GO` and DPO remains audit-only `PILOT_ONLY`; training exports are empty.
- Phase 1a remains `DATA_NO_GO`; Phase 2 is unstarted. The internal direction package remains separate from an experiment-backed full paper.
- Patent release approval is unconfirmed, so no submission, preprint upload, or public core-code release is allowed.

## Current repository-only delivery

- `research/phase1a_data_contract.py` checks eight artifact roles and seven gates: artifact integrity, five-layer UID/sample isolation, independent correctness/adjudication, licence permission, confidence provenance, pre-approved analysis, and parser-contract provenance.
- The checker blocks common Python socket entry points, emits deterministic aggregate-only JSON, rejects unsafe paths and output overwrite, and never exports sample bodies.
- It has only two outcomes: `DATA_NO_GO` and `READY_FOR_INDEPENDENT_ACCEPTANCE`. The latter is deliberately not `DATA_GO`, training permission, GB10 acceptance, or a paper result.
- `tests/test_phase1a_data_contract.py` uses synthetic private-package fixtures and covers happy path, each gate family, leakage/path/hash failures, malformed inputs, network blocking, deterministic output, no-overwrite behavior, and CLI failure status.
- The authoritative package schema and GB10 procedure are in `docs/experiments/2026-09-23_phase1a_data_no_go.md`; the tool is registered in the research entry, asset map, code map, and existing handoff.

## Local verification

- Focused contract suite: 19 passed. Combined research/governance suite under `.venv`: 55 passed. Both emitted only the repository's existing unknown `asyncio_mode` warning.
- Python compilation passed; paper claim validation passed 49/49.
- The system-Python combined attempt stopped during collection because `python-docx` is absent; the same scope passed under the repository `.venv`, which contains the declared document dependency.
- Local `docs_lint` remains 1 fail/1 warn because this machine's Codex skill installation is out of sync and protected `docs/34*` is stale. Neither condition was hidden or modified; they are not failures introduced by this source change.
- Endpoint/model/service/database calls: 0. No real or private dataset was read.

## GB10 boundary

- GB10 is not connected or probed in this batch. The bounded SSH attempt recorded on 2026-09-23 in the inherited main-line documents timed out.
- The last known production snapshot was `e5ab809`; current checkout, dirty files, processes, Loop B cycle, control queue, private data, and Loop C Lead status are unverified.
- The local cached `gb10/main=3dabbc7` ref is stale metadata, not live evidence. Do not claim a READY card or infer that the queue is active or idle.
- The earlier closeout audit remains `INCONCLUSIVE`; the prior four-test A-2 result is only `SCOPED_PASS`, not a whole-project network guarantee.

## Next gates

1. When GB10 is restored, first obtain a fresh read-only status and create a clean isolated worktree at the reviewed commit; preserve production dirty files.
2. Mount the private supplement package read-only and execute the focused test plus two `strace`-wrapped prechecks documented in the data-gate report.
3. Require byte-identical reports, zero `connect` syscalls, seven mechanical PASS gates, and independent review of licence authority, reviewer identity/adjudication, analysis approval, and parser provenance.
4. A mechanical pass only permits reconsidering the data gate. Phase 1a learnability, Phase 2 replay, 4B/8B training, endpoints, service changes, and publication still require their own authorization.
5. Office visual review of the two advisor DOCX files remains outstanding and is independent of this code contract.
