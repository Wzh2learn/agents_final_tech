# Current State

> Updated: 2026-09-22 | Scope: main fast-forward and GB10 acceptance stop | Runtime: no restart

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions:
[`DECISIONS.md`](DECISIONS.md); prior snapshot: [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

`origin/test/compaction-guard-abort` was fast-forwarded into `main` and pushed.
GB10 acceptance stopped on governance drift, four pytest failures and a zero-endpoint
violation. Phase 1a/2 did not start. Entry: [`../docs/research/README.md`](../docs/research/README.md).

## Git and GB10 checkout state

- Local and origin `main` are `0aee20d`; `--ff-only`, 17 commits, 88 files, `+7955/-4408`.
- Frozen paths/docs 33–34 are unchanged; four pre-existing local user assets stay uncommitted.
- GB10 production stays at `3dabbc7`: six dirty files include intersecting
  `logs/graph/dispatch_log.md`; no pull/stash/reset/clean occurred.
- Clean detached worktree `agents_final_tech_accept_0aee20d` at `0aee20d` held acceptance.

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

## GB10 acceptance evidence and stop (2026-09-22)

- Focused offline contracts: 159 passed, exit 0; scope covered data/paper claims,
  production/runtime boundaries, isolated launch fixtures and governance routing.
- `git diff --check`, changed Python compilation and changed Bash `bash -n` passed.
  Paper claim validator passed 49/49; these checks do not prove research effects.
- Skill sync failed 1/97 (`skill-doctor` install drift); docs_lint was 1 fail/1 warn.
  Skill-doctor found 0 errors/139 warnings and exited 1. No install mutation or suppression.
- Full pytest ran once: `590 passed, 14 skipped, 4 failed`; failures lacked ignored
  `injected_tables.json` in the worktree. Production has SHA256
  `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9`;
  it was not copied/generated/linked and tests were not rerun.
- Network trace: allowed PG `:15432` ×6 and HTTP `:5050` ×1; forbidden `:8004`
  ×5 and `:8007` ×1; DNS `:53` ×4 and GitHub SSH `:22` ×4. Forbidden attempts
  violate the zero-endpoint contract even though completed inference was not proven.
- No daemon/service restart, crontab change, model load, judge, canary, training,
  Phase 1a, Phase 2, old receipt recomputation or paper publication occurred.

## Next-session boundary

- Acceptance is **blocked**; Phase 1a/2 require approved skill-drift, data-access and hard network-isolation resolutions.
- Do not regenerate old artifacts; only four failed tests need diagnostic rerun unless authorized.
- Preserve production dirty files; no pull while dispatch log intersects, and no stash/reset/clean.
- Training, model/endpoint tests, restarts, frozen/protocol changes and publication remain unauthorized.

## Strict closeout (2026-09-23)

- GB10 production checkout is aligned with `origin/main` at `d351d7e09e738f16727f17d5aa3dc35646989731` (ahead/behind `0/0`); `0aee20d` is an ancestor. The next Loop B natural cycle recorded `git_alignment=PASS`; this was observed from the cycle report, not inferred from Git alone.
- A-3 is closed: after the authorized one-item installation sync, `scripts/graph/sync_skills.sh --check` returned `PASS: 97`; A=76/C=21, missing=0, orphan=0. Only the GB10 Codex installation copy of `skill-doctor` changed; repository skills and Claude installation were unchanged. Full-root warnings remain and were not suppressed.
- A-2 is **SCOPED_PASS** only. The exact nodes were `tests/test_vgmc_adversarial.py::test_adv_map_deterministic_nested_wrong_target`, `tests/test_vgmc_collision_overlay.py::test_overlay_merge_adds_columns_and_entries`, `tests/test_vgmc_collision_overlay.py::test_overlay_none_is_identity`, and `tests/test_vgmc_collision_overlay.py::test_real_overlay_artifact_loads`; all four passed (exit 0). The command used `strace -f -e trace=connect`; forbidden ports `8004/8006/8007/8008/4096` were each observed zero times, as were allowed `5050` and PG `15432` (total connect syscalls 0). The test fixture used synthetic corpus helpers because the isolated worktree lacks `injection_map.json`; `load_corpus()` and the broader suite were not covered. This cannot be generalized to full pytest, production, or future experiments.
- Phase 1a is formally `DATA_NO_GO`; no baseline result table was produced and Phase 2 was not started. The structured data-gate report is `docs/experiments/2026-09-23_phase1a_data_no_go.md`.
- No backend agent session remains running. Production accumulative files, rolling reports, and the external alignment backup remain traceable and are not treated as source commits.

### Next-round entry gates

1. **Data supplement:** reopen Phase 1a only after complete source tables/schema, licence/provenance, independent correctness labels, and disjoint manifests are supplied and accepted.
2. **A-2 scope expansion:** if a broader test or experiment range is requested, establish new hard network-isolation evidence for that exact range; do not reuse this scoped pass as a global guarantee.
3. **Loop C Lead:** governance, control-plane, documentation, archive candidates, and experiment design may proceed while Phase 1a remains `DATA_NO_GO`; Phase 2 and training remain closed.
