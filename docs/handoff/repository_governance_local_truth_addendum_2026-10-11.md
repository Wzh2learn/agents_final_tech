# Repository Governance LOCAL Truth Addendum — 2026-10-11

> Scope: LOCAL `D:/AIRcommend/JinRongAgents/agents_final_tech`
> Complements `docs/handoff/repository_governance_and_sync_2026-10-11.md`
> Read-only inventory; no commit or push performed by this addendum

## LOCAL Git Truth

| Field | Value |
|---|---|
| Path | `D:/AIRcommend/JinRongAgents/agents_final_tech` |
| Branch | `main` |
| HEAD | `e97340387888290e69fbfff122ab163de971b37e` |
| Remote | `origin` = `https://github.com/Wzh2learn/agents_final_tech.git` / `git@github.com:Wzh2learn/agents_final_tech.git` |
| Upstream | `origin/main` |
| Ahead / behind | `0 / 0` |
| Staged | `0` |
| Unstaged modified | `23` paths |
| Deleted | `0` |
| Untracked | `24` top-level paths/directories, including `research/causal_checkpoint_selection_mvp_20261011/` |
| Worktrees | `agents_final_tech` at `e973403`; `agents_final_tech_test` at `a92e170` |
| Stash | `0` |
| Submodules | `0` |

## LOCAL Dirty/Untracked Inventory

The LOCAL dirty set is materially smaller than the GB10 dirty set. The following LOCAL-only or shared surfaces were observed:

- modified governance/docs: `docs/INDEX.md`, `docs/SKILL_ROUTING.md`, `docs/governance/reference/SESSION_HANDOFF_TEMPLATE.md`, `docs/governance/reference/TIERED_EVAL_PATTERN.md`;
- modified memory/governance: `memory/CORE.md`, `memory/DECISIONS.md`, `memory/STATE.md`, `memory/THREADS.md`, `side_handoff.md`;
- modified engineering scripts: `scripts/docs_lint.py`, `scripts/graph/graph_orchestrator.sh`, `scripts/graph/loop_d_daemon.sh`, `scripts/graph/loop_d_monitor.sh`, `scripts/graph/status.sh`, `scripts/deploy_proxy_gb10.sh`, `scripts/setup_codex_gb10.sh`, `scripts/switch_codex_model.sh`;
- deleted/renamed legacy supervisors: `scripts/supervisor_m1.sh`, `scripts/supervisor_qoder.sh` -> `scripts/archive/loop_ac_supervisor_*_legacy.sh`;
- untracked research/governance outputs: new research notes, FinQA/Stage E contracts, figures, task contracts, preflight tooling and the causal checkpoint MVP;
- untracked paper outputs: SANER scope lock and claim matrix.

Exact path-level classification is in the GB10-generated `docs/handoff/repository_asset_classification_2026-10-11.json`; the LOCAL side is a subset/overlap requiring hash comparison before any sync commit.

## Reconciliation State

- LOCAL and GB10 share the same HEAD and upstream position.
- No history divergence exists at the commit level.
- Dirty/untracked content differs; no file was deleted or overwritten by the inventory.
- `UNKNOWN` files are not proposed for deletion.
- Any sync/commit remains blocked until Loop C confirms authority/lineage and D reviews the commit groups.

## External Assets

The local workspace contains `external_stage_d_repro`-style material and generated research artifacts. Large datasets, checkpoints, caches and raw outputs must remain outside Git. Metadata/manifests should be committed only after authority review.

## Final LOCAL-only classification before commit

- Commit manifest: 335 paths across `G0` through `G6`, including two deliberate legacy-supervisor archive deletions plus their archived copies. No `G7` external/large path is included.
- Additional current governance/scientific records included: formal-v3 activation record, measurement-object mismatch autopsy, Loop C governance contract, local truth addendum, STATE history snapshot, the Stage-E inquiry task card, and three historical Loop C prompt records.
- `SUPERSEDED_DUPLICATE_DO_NOT_COMMIT` (8 byte-identical copies of canonical `research/*_20261009` files): `multileaf_power_analysis.py`, `prm_reference_smoke.py`, `stage_e_matched_fpr_reanalysis.py`, `validate_stage_e_method_revision.py`, `finalize_loop_c_conditions.py`, `loop_a_prompt.md`, `repair_loop_c_conditions.py`, `resolve_final_conditions.py` under the hyphenated `2026-10-09` directories.
- Tracked package/source surfaces whose raw SHA differs across hosts solely because checkout EOL presentation differs are not semantic diffs when Git blob identity and normalized content agree. The authoritative paper hash ledger is bound to GB10 raw bytes and is valid on both current worktrees after byte synchronization.
- The archived qoder supervisor has one adjudicated metadata edit: remove the UTF-8 BOM and replace the stale mutual-exclusion comment with an archive-context comment. This is source metadata only and does not alter execution history or scientific artifacts.
- No UNKNOWN path is deleted. External datasets, checkpoints, model caches, raw outputs, stashes and worktrees remain preserved outside the commit set.
