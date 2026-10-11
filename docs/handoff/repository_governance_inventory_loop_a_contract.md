# Task Contract: Repository and Research Asset Governance Inventory - Loop A

- Task ID: `repository-governance-inventory-a-20261011`
- Role: Loop A / GB10 mechanical inventory and classification
- Mode: read-only repository research; generated governance reports only
- Scope: LOCAL `agents_final_tech`, GB10 authoritative repo, external repro directories

## Inputs

- LOCAL repo: `D:/AIRcommend/JinRongAgents/agents_final_tech`
- GB10 repo: `/home/testuser/wzh/projects/agents_final_tech`
- `/home/testuser/wzh/external_stage_d_repro`
- local external/temp/repro counterparts
- `memory/STATE.md`, `memory/THREADS.md`, `logs/graph/dispatch_log.md`, `docs/INDEX.md`
- `docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md`
- paper/claim/scope-lock assets
- hooks: `summary_recompute_guard.py`, `index-guard.precommit.sh`, `skill_router.py`, `dispatch_precheck.sh`

## Required Inventory

For LOCAL and GB10 record:

- repo path, branch, HEAD, remote/upstream;
- ahead/behind;
- staged/unstaged/untracked/deleted/ignored;
- worktrees, stash, submodules;
- recent commits and divergence point.

Classify every dirty/untracked file into:

`SOURCE_CODE`, `TEST`, `CONFIG`, `SCIENTIFIC_DATA`, `RESULT_ARTIFACT`, `PREREG_FREEZE`, `INVALID_RUN_PRESERVED`, `PAPER_SOURCE`, `FIGURE_TABLE`, `RESEARCH_NOTE`, `HANDOFF_MEMORY_GOVERNANCE`, `LOG_CACHE_TEMP`, `EXTERNAL_REPRO`, `UNKNOWN`.

For each file record:

- path, owner/source, local/GB10 presence;
- authoritative status;
- reproducible status;
- commit/archive/ignore/delete/external recommendation.

Do not delete UNKNOWN.

## Asset Lineage

Create a complete FinQA lineage:

`v1 freeze -> invalid run #1 -> binding_v2 -> invalid run #2 -> binding_v3 -> end-to-end preflight -> formal v3 result -> scientific autopsy -> measurement-object-mismatch conclusion -> causal-exposure proposal -> STOP/design-only`.

Record supersedes, superseded-by, status, hash, authoritative flag and scientific interpretation.

## Paper and Current Assets

Classify current/superseded/derived paper files, figures, tables, submission previews and claim manifests. Ensure Route A scope-lock is current; Route B is `NO / STOP_BRANCH`.

## External Assets

Inspect `/home/testuser/wzh/external_stage_d_repro` and local external/temp/repro dirs. Record large files, orphaned experiments and which metadata/manifests should remain repo-external.

## Required Generated Outputs

1. `docs/handoff/repository_asset_classification_2026-10-11.json`
2. `docs/handoff/repository_governance_and_sync_2026-10-11.md`
3. `docs/research/finqa_v2_asset_lineage_v1.md`
4. commit plan with logical groups and exact paths;
5. verification command/results.

## Allowed Actions

- Read-only Git/repo/directory scans.
- Generate classification/lineage/handoff reports.
- Run focused tests, docs lint, claim validators, submission audits, freeze/hash checks.
- Identify safe commit/sync groups.

## Forbidden Actions

- Delete, move or rewrite scientific artifacts.
- Commit, merge, rebase or push before Loop D review.
- Change frozen scientific results or claims.
- Treat invalid/superseded runs as current evidence.
- Add new scientific experiments or methods.

## Success Exit

A complete truth table, classification, lineage, external-asset inventory, commit plan and verification report exist, with all authority conflicts explicitly surfaced for Loop D.
