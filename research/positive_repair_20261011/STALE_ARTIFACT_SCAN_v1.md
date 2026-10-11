# STALE_ARTIFACT_SCAN_v1.md

> date: 2026-10-12 | method: staleness = last commit touching the path (git history, not mtime, because a fresh checkout resets mtime); usage = inbound basename reference count over 1,158 repo text files + the top-level handoff docs
> verdict: **NO ACTION REQUIRED in the repository**; the zero-reference/old files are already in their designated historical locations

## Scan result
- files not touched in >= 21 days: **497**
- of those, **zero inbound references: 164**
- untracked files in the repository: **0** (nothing to sweep)
- parent-workspace scratch: handled separately (see `_archive_2026-10-11/`)

## Why no move is proposed
`docs/INDEX.md` states the repository convention: current state lives in `memory/STATE.md`, navigation in `docs/INDEX.md`, and **historical process goes to Git, `docs/experiments/` or `docs/archive/`**. Every zero-reference/old file found already sits in one of those designated historical locations, so archiving them again would break the documented structure and the index without adding clarity.

## Candidate inventory (top zero-reference / >=21d, grouped)
| Group | Examples (age, size) | Recommendation |
|---|---|---|
| `docs/archive/**` (already archived) | `README_legacy_1115lines.md` (72d, 37KB), `codex_migration_pack_all_in_one.md` (87d, 36KB), `CODE_REVIEW_COMPREHENSIVE_20260118.md` (260d, 26KB), `experiments/phase3_*` (60d) | leave; already the archive |
| `docs/governance/reference/**` | `AGENT_COLLABORATION_PROTOCOL.md` (47d, 43KB), `CROSS_AGENT_LESSONS.md` (47d, 34KB), `RESEARCH_WRITING_WORKFLOW.md` (47d, 24KB), `COMMANDER_PLAYBOOK.md` (47d, 19KB) | leave; governance reference shelf. Optionally add one INDEX row if the owner wants them discoverable |
| `docs/experiments/2026-08-*` historical records | `2026-08-19_dspark_eval_artifacts/*.json` (53d, 36KB+35KB), `2026-08-13_advisor_package_review.md` (58d, 20KB), `2026-08-06_audit_loop_c_flash_fixes.md` (66d, 13KB), `2026-08-19_dspark_route_v_probe.md` (53d), `2026-07-29_m1_verify_and_mcp.md` (74d) | leave; historical experiment records are index-covered by convention |
| `memory/archive/STATE_*` snapshots | `STATE_2026-08-31_pre_night.md` (42d, 20KB), `STATE_2026-08-30_daytime_w2.md` (42d, 18KB), `STATE_2026-08-30_001x.md` (42d, 17KB) | leave; archived state snapshots are the intended record |
| loose scripts with no callers | `scripts/record_demo_video_v2.py` (58d), `scripts/run_m2_rag_eval.py` (84d), `scripts/record_demo_video_v3.py` (47d), `scripts/walkthrough_m1_v2.py` (43d), `research/p1_correctness_backfill.py` (44d) | leave for now; if the owner wants a leaner `scripts/`, these five are the safest first candidates (no inbound references, one-off demo/eval helpers) |

## Note on one tracked-looking oddity
`docs/26_选择题体验设计.md` displays as mojibake in some consoles but is a normal tracked file; it is not a duplicate.

## What WOULD be worth doing (owner decision, low value)
1. Add INDEX rows for `docs/governance/reference/**` if those four documents should remain discoverable.
2. Retire the five callerless scripts listed above if a leaner scripts/ tree is wanted.
Both are cosmetic; neither affects the submission package or the evidence chain.