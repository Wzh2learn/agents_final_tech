# Current State

> Updated: 2026-09-22 | Scope: repository governance | Runtime: not probed

This is the current snapshot. Open decisions belong in [`THREADS.md`](THREADS.md),
durable decisions in [`DECISIONS.md`](DECISIONS.md), and the previous long snapshot
in [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

P1 local audit and advisor-content review are delivered; remaining tests and
Office visual review are handed to the server. Research entry:
[`../docs/research/README.md`](../docs/research/README.md).

## Repository baseline

- Product: M1 counterparty-statement parsing and M2 traceable RAG QA.
- Python 3.12, FastAPI, PostgreSQL/PGVector; root `serve.sh` is the launcher.
- Database contract: `PGDATABASE_URL`, development `vector_db`; HTTP default 5050.
- Production parser/ingest live in `src/biz/`; scripts are compatibility CLIs.
- Startup paths delegate to `serve.sh`; Docker includes `config/`; local startup
  does not kill an occupied port or silently background Uvicorn.
- Script ownership is in `scripts/catalog.toml`; top-level `research/` is separate.
- Skill distribution stages/validates before activation; code existence does not
  prove the current machine's skills, hooks or daemons are installed.

## First-round governance outcome

- Document authority is separated: INDEX navigates, research README resolves
  conflicts, story defines claims, asset map tracks evidence, the existing
  `docs/handoff/2026-09-22-paper-research-next-phase.md` controls execution.
- Advisor materials and thesis chapters now follow that plan; historical roadmaps
  and side handoffs no longer dispatch old work or duplicate the current ledger.
- `docs/architecture/codebase_map.md` maps product, research and governance code,
  inputs, side effects and focused tests, without stale size/health claims.
- `run_tabular_inference.py` is classified as a production MCP subprocess.
- VGMC few-shot tests use synthetic fix/meas inputs, not remote corpus assets;
  real assertions reject measurement leakage, an eleventh fix table and bad labels.
- A/C prompts and orchestrator help use current authorities and task authorization;
  start no longer claims A/C were launched. Business agents are a separate graph.
- Dispatch precheck requires JSON receipts bound to watcher path, SHA256, zoned
  observation time and integer-zero exit status; it never executes the watcher.
  Synthetic receipts verify the contract, not actual deployment or scheduling.
- Story Markdown, SVG, generator and direction DOCX agree on 8B main student,
  4B smoke-only, candidate proposal/prescreen and the final deterministic gate.
  Word paragraphs/tables match fresh generation; Office visual review is unverified.
- Governance closure and P1 local audit are not training-data readiness,
  independent production Loop B/C acceptance, training or research-effect proof.

## Research maturity

- E: mature evaluation subdraft; 95 tables/118 injections, bounded claims.
- D: no trained student results. Existing zero-shot matrix is not distillation.
- R: rejection/collision mechanism evidence, not stable significant net benefit
  or a completed long-term versioned rollback loop.
- P1 local audit now covers 37 artifacts: 494 scored gated events/48 uids;
  DPO 60 pairs/36 uids, all skip>map_to. All 23 arm ledgers match final rules.
- Sixteen conflict groups are quarantined; 17 accepted targets disagree with stored
  canonical references, and 6 DPO pairs reject reference-matching mappings.
- Action-SFT/risk views are DATA_NO_GO; DPO is audit-only PILOT_ONLY; training exports
  remain empty. All 95 tables are historical; new validation/test/future layers are missing.
- Complete source/context, independent correctness/licence checks and real metric-specific
  power remain outstanding; only hypothetical uid-level MDE sensitivity was computed.
- Plan order: Phase 1 data audit → Phase 1a learnability → Phase 2 gate baselines →
  approved 4B smoke/8B experiments. A3 is conditional; Phase 6 controls splitting.
- The internal direction package is separate from the experiment-backed full draft.
  No materials were sent; patent release approval remains an independent gate.

## Verification record and server handoff (2026-09-22)

- Before the user's pause: 17 data-audit tests and 11 paper/asset tests passed locally.
  Two audit outputs are byte-identical; details/hashes are in the asset map §3.1.
- Remaining tests and Office visual review are server-side; no more local test runs.
- Earlier governance regression: 160 passed, 1 real-corpus test deliberately deselected;
  governance/catalog/receipts/VGMC/paper/runtime/module boundaries/aggregation/drift.
- Paper static acceptance: 49/49. This checks structure/wording/paths, not new effects.
- All 16 checkpoint files and DPO hashes match the plan's pre-change snapshot.
- `git diff --check` and dispatch `bash -n` pass; protected docs/33, docs/34,
  frozen tests/hash manifest and original experimental artifacts are unchanged.
- docs_lint still reports 1 existing local skill-installation FAIL and 1 protected
  docs/34 date WARN; not an all-green lint claim. No suppression/global sync applied.
- Pytest retains its existing unknown `asyncio_mode` warning. The existing `.venv`
  provides python-docx; no dependencies were installed or changed.
- Endpoint/model/service/database/health-probe calls: 0. No GB10 or Office validation.

## Exclusions and next action

- The user states corpus/model/runtime assets are on another server. This round
  neither verifies nor retrieves them; missing local copies are not research failure.
- New paper-facing baselines/replay remain GB10 work even at zero endpoint calls;
  local work is existing-fact audit and synthetic code testing only.
- Plan §10 now hands off remaining tests/Office review to the server; Phase 1a/2,
  data expansion and training all await the user's further approval.
- Do not modify docs/33, docs/34 or frozen TAT-DQA, publish research, change global
  installs, or touch services without the required separate authorization.
- The latest instruction requests a Git commit after document handoff;
  Git history and branch alignment are authoritative for delivery status.
