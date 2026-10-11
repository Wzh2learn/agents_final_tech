# Repository Governance and Sync — 2026-10-11

> Status: `LOOP_A_INVENTORY_COMPLETE_PENDING_LOOP_D_REVIEW`
> Task: `repository-governance-inventory-a-20261011`
> Mode: read-only repository research; generated governance reports only
> Authoritative runtime: GB10 `/home/testuser/wzh/projects/agents_final_tech`
> Local path: `D:/AIRcommend/JinRongAgents/agents_final_tech`

## Skill loading

Loaded exactly four task skills plus the repository red line: `graph-loop-rules`, `progress-reading-protocol`, `jinrong-docs-sync`, and `verify-before-done`. `progress-reading-protocol` server-start/smoke steps were intentionally not executed because this task is read-only and production/model/database probes require separate approval. No sub-agent was used.

## Executive result

- The GB10 branch is `main` at `e97340387888290e69fbfff122ab163de971b37e`, exactly level with `origin/main` (`0 ahead / 0 behind`); HEAD is the divergence point with its upstream.
- The pre-output worktree contains 39 `M`, 2 `D`, 355 `??`, 0 staged, 0 renamed and 0 unmerged entries. Ignored inventory contains 69,317 paths, dominated by `venv/` and `.omc/`.
- The Windows LOCAL repository is not mounted in this environment, so every LOCAL Git/file fact is `UNKNOWN_UNMOUNTED`, never inferred from GB10. This is a required Loop D blocker for a true two-repository truth table.
- The final machine-readable classification contains 399 dirty/untracked entries after the three required generated reports exist, and `UNKNOWN` count is `0`.
- No file was deleted, moved, staged, committed, merged, rebased or pushed. UNKNOWN files, if any remain, are held with `delete=false`.
- FinQA lineage is reconstructed in [`../research/finqa_v2_asset_lineage_v1.md`](../research/finqa_v2_asset_lineage_v1.md); its scientific-autopsy node is explicitly missing its required report.

## Two-repository truth table

| Field | LOCAL `D:/AIRcommend/JinRongAgents/agents_final_tech` | GB10 `/home/testuser/wzh/projects/agents_final_tech` |
|---|---|---|
| Path available | `false` — no `/mnt/d`, `/d` or equivalent mount | `true` |
| Branch | `UNKNOWN_UNMOUNTED` | `main` |
| HEAD | `UNKNOWN_UNMOUNTED` | `e97340387888290e69fbfff122ab163de971b37e` |
| Remote | `UNKNOWN_UNMOUNTED` | `origin git@github.com:Wzh2learn/agents_final_tech.git` |
| Upstream | `UNKNOWN_UNMOUNTED` | `origin/main` |
| Ahead / behind | `UNKNOWN_UNMOUNTED` | `0 / 0` |
| Staged | `UNKNOWN_UNMOUNTED` | `0` |
| Unstaged modified | `UNKNOWN_UNMOUNTED` | `39` |
| Deleted | `UNKNOWN_UNMOUNTED` | `2` |
| Untracked | `UNKNOWN_UNMOUNTED` | `355` before generated outputs |
| Ignored | `UNKNOWN_UNMOUNTED` | `69317` |
| Worktrees | `UNKNOWN_UNMOUNTED` | 6 worktrees listed below |
| Stash | `UNKNOWN_UNMOUNTED` | 2 stashes |
| Submodules | `UNKNOWN_UNMOUNTED` | 0 |
| Recent commits | `UNKNOWN_UNMOUNTED` | latest 20 inspected; HEAD `e97340387` |
| HEAD/upstream divergence point | `UNKNOWN_UNMOUNTED` | `e97340387888290e69fbfff122ab163de971b37e` |
| LOCAL↔GB10 divergence point | `NOT_COMPUTABLE_PATH_UNAVAILABLE` | `NOT_COMPUTABLE_PATH_UNAVAILABLE` |

The expected local↔remote relationship cannot be converted into an exact local↔GB10 relationship without reading the LOCAL worktree. `git ls-remote` or GB10 HEAD equality would not establish LOCAL dirty-state equality.

### GB10 Git inventory

- Worktrees: primary `main` at `e97340387`; detached `4ce848adb`, `7b113feaf`, `d351d7e09`; branch `gb10/lc-research-20260924` at `1f8070e21`; branch `gb10/loop-c-lead-20260923` at `815dda50e`.
- Stashes: `de9996e819` (`2026-08-29`, `pre-e4e3a60-runtime-overlap`) and `99a3b1dc9e` (`2026-07-16`, `pre-opencode-mcp-sync-2026-07-16`).
- Submodules: zero.
- Recent HEAD chain begins `e97340387`, `d3e3a914c`, `fe48a92ab`, `a3bd5caff`, `8a36913dc`, `bcb7be776`, `8c0b248dd`, `69f93c3e1`, `3e571913e`, `c39b301d3`.
- The exact latest-20 records and all worktree/stash metadata are embedded in `repository_asset_classification_2026-10-11.json`.

### Ignored inventory

| Top-level bucket | Ignored paths |
|---|---:|
| `venv/` | 66294 |
| `.omc/` | 1391 |
| `research/` | 1132 |
| `logs/` | 161 |
| `docs/` | 106 |
| `tests/` | 101 |
| `src/` | 76 |
| `scripts/` | 23 |
| `.ocr_cache/` | 11 |
| `data/` | 8 |
| `.pytest_cache/` | 5 |
| `dify/` | 5 |
| `.agent-of-empires/`, `.env`, `.qoder`, `sessions.db` | 4 |

Path-only inventory was used for `.env`; no credential file contents were read or printed.

## Classification result

| Category | Entries |
|---|---:|
| `CONFIG` | 2 |
| `FIGURE_TABLE` | 11 |
| `HANDOFF_MEMORY_GOVERNANCE` | 22 |
| `INVALID_RUN_PRESERVED` | 12 |
| `LOG_CACHE_TEMP` | 6 |
| `PAPER_SOURCE` | 13 |
| `PREREG_FREEZE` | 54 |
| `RESEARCH_NOTE` | 100 |
| `RESULT_ARTIFACT` | 69 |
| `SCIENTIFIC_DATA` | 34 |
| `SOURCE_CODE` | 64 |
| `TEST` | 12 |
| `UNKNOWN` | 0 |
| **Total** | **399** |

Coverage is exhaustive and mutually exclusive: all 398 pre-existing dirty/untracked paths plus the classification JSON itself are present exactly once. LOCAL presence remains `UNKNOWN_UNMOUNTED` for every entry; GB10 presence is `true`.

Every entry in the JSON report records path, owner/source, GB10 presence, LOCAL presence, Git status, SHA-256 when present, size, category, authoritative status, reproducible status, paper status where applicable, and separate `commit/archive/ignore/delete/external` recommendation flags.

Key interpretation rules:

- `INVALID_RUN_PRESERVED` means authoritative historical evidence of a failed execution, never current scientific evidence.
- `PREREG_FREEZE` means frozen scope/manifest/contract material, not execution authorization.
- `EXTERNAL_REPRO` and large raw/model/source copies stay outside Git even when present under `research/`.
- `UNKNOWN` never receives `delete=true`.
- The two deleted supervisor scripts are held for Loop D; their untracked `scripts/archive/*_legacy.sh` counterparts are reviewed as an archive proposal, not executed as a deletion.

## Paper and claim assets

| State | Exact assets |
|---|---|
| Current claim/scope authority | `paper/claim_manifest_v1.json`, `paper/saner_rene_claim_matrix_v1.json`, `paper/saner_rene_manuscript_scope_lock_v1.md`, `paper/research_asset_map_v2.md` |
| Current teacher-review package | `paper/teacher_review_draft_v1.md`, `paper/teacher_review_draft_v1.docx`, `paper/teacher_review_readiness_v2.md`, `paper/teacher_review_note_v2.md`, `paper/teacher_review_finalization_v1.md` |
| Current submission preview/control | `paper/submission_draft_arr_www_anonymous_v0.md`, `paper/submission_readiness_arr_www_v1.md`, `paper/submission_language_audit_v1.md`, `paper/submission_package_audit_v1.json`, `paper/submission_redaction_map_v1.json`, `paper/submission_references_arr_www_v1.md`, `paper/submission_review_risk_register_v1.md` |
| Current supporting material | `paper/research_story_v2.md`, `paper/research_story_v2.docx`, `paper/dataset_protocol_v1.md`, `paper/figure_plan_v1.md`, `paper/method_theory_materials_v1.md`, `paper/method_data_references_v1.bib`, `paper/related_work_contribution_matrix_v1.md`, `paper/reproducibility_statement_arr_www_v1.md`, `paper/thesis_proposal_v1.md`, `paper/thesis_ch1_ch2_draft_v1.md`, `paper/thesis_manuscript_scaffold_v1.md`, `paper/thesis_rq2_rq4_execution_matrix_v1.md` |
| Figures/tables | `paper/figures/fig_evaluate_distill_evolve_v1.svg`, `paper/figures/fig_rule_gate_replay_v1.svg`, plus untracked `docs/research/figures_multileaf/` PNG/SVG/manifest |
| Historical/superseded | `paper/draft_v0_s1_s2_s6.md` and `paper/references_v0.md`; retain, do not delete |
| Historical derived audit | `paper/acceptance_report_v1.json`; preserve as prior acceptance evidence, not the current package audit |
| Advisor drafts | `paper/advisor_discussion_brief_2026-10-09.md`, `paper/advisor_decision_tables_2026-10-09.md`; `INTERNAL_ONLY` / `RECOMMENDATION_ONLY` |

Route A is the current manuscript route. `paper/saner_rene_manuscript_scope_lock_v1.md` is `FROZEN_SCOPE_NOT_PAPER_BODY` with primary route `A`. Route B is `B_QUALIFICATION = NO / STOP_BRANCH` in [`../research/route_b_read_only_qualification_2026-10-11.md`](../research/route_b_read_only_qualification_2026-10-11.md). Submission previews are not submission-ready: the package audit reports `PASS / PENDING_EXTERNAL_ITEMS / NOT_READY_FOR_SUBMISSION`.

## FinQA authority conflicts for Loop D

1. **Missing autopsy output.** `research/loop_c_finqa_v2_result_autopsy_task_contract.md` exists, but no report implementing its required four-way classification and `FACT / INFERENCE / UNVERIFIED` output was found.
2. **Semantic evidence mismatch.** `paper/saner_rene_claim_matrix_v1.json` C3 cites `docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md` for failed-transfer/measurement-object mismatch, while that audit explicitly says the separation transfers and supports `SECOND_FLOW_MIXED`. The missing autopsy is therefore the unresolved bridge between technical result and claim-level mismatch interpretation.
3. **Current-state conflict.** `memory/STATE.md` is the current-status authority but still carries `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN=NO`, “no third rerun authorized” and `END_TO_END_PREFLIGHT_PASS_CANDIDATE_PENDING_LOOP_C` statements alongside later artifacts showing formal v3 execution and a Loop C PASS. Its header remains `Updated: 2026-10-08` although 10-11 entries are appended. Loop D must reconcile chronology and authority without deleting history.
4. **Route B wording.** The scope lock labels Route B as an optional read-only qualification; the newer qualification is explicitly `NO / STOP_BRANCH`. The qualification controls Route B, but Loop D may add a supersession pointer in a later governance edit.
5. **Navigation gap.** `docs/INDEX.md` is the navigation authority and contains the binding-v2 and governance audit references, but does not yet provide a dedicated entry for the formal-v3 recomputation/lineage package. This report and the INDEX registration are proposed in the same logical commit group.
6. **LOCAL truth gap.** No LOCAL repository mount exists here, so LOCAL branch/HEAD/dirty/worktree/stash/submodule facts cannot be verified.

No conflict above was “fixed” by changing a scientific result, claim or frozen artifact.

## External and reproducibility inventory

### GB10 external root

- Root: `/home/testuser/wzh/external_stage_d_repro` — present, approximately 220 MiB, not a Git worktree.
- Top-level evidence groups: `adapters/`, `audit/`, `receipts/`, `reports/`, `source_cards/`, `unified_schema/` and `scripts/`.
- Top-level bulk groups: `datasets/` 46 MiB, `repos/` 165 MiB, `vendor/` 1.1 MiB, `.omc/` session state, and empty `envs/`.
- Current external status evidence: H1 `EXT_D_REPRO_H1_REVIEW_READY`, H2 `EXT_D_REPRO_H2_DECISION_READY`, while `audit/loop_d_review_receipt_v1.md` preserves the earlier global `EXTERNAL_REPRODUCTION_BLOCKED` judgment. These are scoped statuses, not a repo-authority upgrade.

Large external files:

| Bytes | Path |
|---:|---|
| 47,349,288 | `/home/testuser/wzh/external_stage_d_repro/datasets/agent_distillation/Qwen2.5-32B-Instruct_agent_trajectories_2k.jsonl` |
| 31,971,255 | `/home/testuser/wzh/external_stage_d_repro/repos/agent_tuning/.git/objects/pack/pack-c76915be12c92b3686c174e6831f31aa62bf0057.pack` |
| 16,889,853 | `/home/testuser/wzh/external_stage_d_repro/repos/toolalpaca/data/train_data.json` |
| 14,206,504 | `/home/testuser/wzh/external_stage_d_repro/repos/agent_tuning/AgentBench.old/src/tasks/webshop/web_agent_site/envs/chromedriver` |
| 8,436,384 | `/home/testuser/wzh/external_stage_d_repro/repos/agent_tuning/eval_heldout/science-world/data_utils/goldpaths-all.zip` |

Repo-external by design: cloned upstream repositories, dataset bodies, PDFs/source snapshots, model weights/checkpoints, vendor packages, raw smoke outputs, network logs and session state. Keep the external metadata/receipt layer repo-external too, because current repository evidence references it by exact absolute path: `receipts/`, `reports/`, `source_cards/`, `unified_schema/`, acquisition/provenance manifests, Loop C/D receipts and artifact SHA-256 lists. The repository may retain small in-repo summaries and hash bindings, but this task did not copy or move them.

Candidate orphan/scratch inventories:

- `/tmp/loop_c_recompute/` — four unmanifested scratch files used by the formal-v3 recomputation; non-authoritative, keep outside Git, review for later archival only.
- `/tmp/external_stage_d_repro_artifacts_v1.tgz` — 47 KiB external artifact archive; keep external.
- `/home/testuser/wzh/backups/TASK-20260910-A4A5A4W/repro/` — 468 KiB historical harness reproduction backup; referenced by repository history but not self-contained in Git; keep external and do not delete.
- `/home/testuser/wzh/external_stage_d_repro/smoke/` intermediates (`h1_adapter_prechange_20261009`, `h1_old_output_baseline_20261009`, `h1_output`, `h2_output`, `h2_output_final`, `output`) — receipt-linked intermediates; remain repo-external pending Loop D manifest review.
- Windows LOCAL external/temp/repro counterparts — `UNKNOWN_UNMOUNTED`; no deletion or sync recommendation can be made.

## Commit and sync plan

No commit is authorized before Loop D. The exact per-path lists are machine-readable in `repository_asset_classification_2026-10-11.json` under `commit_groups`; every path is listed literally, not by glob.

| Group | Purpose | Plan |
|---|---|---|
| `G0_REQUIRED_REPORTS` | This report, classification JSON, FinQA lineage, task contract and INDEX registration | Candidate single governance commit after Loop D review |
| `G1_CURRENT_GOVERNANCE` | STATE/THREADS/DECISIONS, authority map, preflight, handoff, dispatch ledger | Review chronology conflicts first; then one governance commit |
| `G2_FINQA_FREEZE_INVALID_HISTORY` | Freeze packets, binding-v2/v3 contracts, both invalid-run packets and receipts | Preserve byte-for-byte; commit only after hash/authority review |
| `G3_FINQA_FORMAL_SCIENCE` | Formal-v3 result, Loop C recomputation, causal proposal, claim boundary | Loop D must resolve the missing-autopsy conflict before claim commit |
| `G4_OTHER_RESEARCH` | Stage E, multi-leaf, PRM, agent-distillation, metadata and research notes | Split into evidence/research/code sub-batches if Loop D requests |
| `G5_PAPER` | Paper sources, previews, audits, scope lock and claim matrix | One paper-package commit after claim/submission review |
| `G6_ENGINEERING_TESTS` | Config, scripts, tests and launchers | Engineering-only review; no production service change |
| `G7_EXTERNAL_LARGE_HOLD` | Raw sources, datasets, checkpoints, large results and scratch | `external=true` or `ignore=true`; never `commit=true` |
| `G8_DELETED_UNKNOWN_HOLD` | Two deleted supervisors and any UNKNOWN | `delete=false`; restore/archive decision belongs to Loop D |

Required output paths for the candidate report commit are exactly:

- `docs/handoff/repository_asset_classification_2026-10-11.json`
- `docs/handoff/repository_governance_and_sync_2026-10-11.md`
- `docs/research/finqa_v2_asset_lineage_v1.md`
- `docs/INDEX.md`
- `docs/handoff/repository_governance_inventory_loop_a_contract.md`
- `logs/graph/dispatch_log.md`

## Verification

| Command/check | Result |
|---|---|
| `python3 -m pytest ...` with system Python | Failed before collection: `No module named pytest`; corrected below |
| `PYTHONPATH=src ./venv/bin/python -m pytest tests/test_paper_claim_acceptance.py tests/test_submission_anonymous_preview.py tests/test_submission_package_audit.py tests/test_finqa_v2_execution_freeze.py tests/test_finqa_v2_scorer_runtime_binding_v2.py tests/test_formal_experiment_preflight.py tests/test_multileaf_formal_contract.py -q` | `59 passed`, exit 0, Python 3.12.3 |
| `./venv/bin/python research/validate_paper_claims.py --json` | `PASS`, `79/79`, 5 claims, exit 0 |
| `./venv/bin/python research/audit_submission_package.py --output /tmp/loop_a_submission_audit.json` | `PASS 10/10`; `PENDING_EXTERNAL_ITEMS`; exit 0 |
| Read-only verification of `scripts/graph/frozen_hashes.txt` | 5/5 checked, 0 violations, 0 malformed, exit 0 |
| `bash scripts/graph/hooks/index-guard.precommit.sh` | exit 0; no staged new scripts |
| `bash scripts/graph/dispatch_precheck.sh --help` | exit 0; watcher contract usage printed |
| Python AST parse for `skill_router.py` and `summary_recompute_guard.py` | PASS |
| `bash -n` for `index-guard.precommit.sh` and `dispatch_precheck.sh` | PASS |
| `summary_recompute_guard.py check docs/experiments/2026-09-01_d3_matched_fpr_stage_a.md` | 1 receipt block verified, exit 0 |
| `git diff --check` | exit 2; 604 whitespace/line-ending findings across `docs/INDEX.md` (177), `docs/governance/reference/SESSION_HANDOFF_TEMPLATE.md` (64), `docs/SKILL_ROUTING.md` (61). Not repaired because they are pre-existing dirty surfaces outside this report-only task. |
| `python3 scripts/docs_lint.py --json /tmp/docs_lint_report_loop_a_final.json` | `PASS 0 fail / 6 warn`, exit 0; six pre-existing warnings retained and none suppressed |
| Final JSON/schema/path coverage check | `PASS 22/22`: JSON valid, 399 unique paths exactly match expanded Git status, counts match, `UNKNOWN=0`, no deletion recommendation, commit groups cover every path exactly once, lineage/routes/conflicts/external inventory valid, required outputs indexed, and no placeholders remain |

Endpoint/model/database/training/PRM/Stage-D/scientific new-run counts for this task: `0`. No full test suite or production probe was run; the 59-test result is local focused evidence only.

## Loop D stop conditions

Stop before any commit or sync if any of the following remains unresolved:

- LOCAL truth table cannot be read;
- the scientific-autopsy output cannot be located;
- STATE chronology conflicts are not adjudicated;
- claim matrix C3 remains semantically unsupported by its cited formal-v3 audit;
- any UNKNOWN is proposed for deletion;
- a large/raw/external asset is proposed for Git without an explicit reviewed exception;
- Route B is treated as anything other than `NO / STOP_BRANCH`.

## Final reconciliation snapshot for Loop C (2026-10-11)

This section supersedes the pre-commit status above for current-state decisions while preserving that first-pass inventory as history.

### Authority closure

- Route A is the sole SANER manuscript route. Route B is `B_QUALIFICATION=NO / STOP_BRANCH`.
- FinQA formal-v3 remains the technical result `SECOND_FLOW_MIXED`; accepted interpretation is `MEASUREMENT_OBJECT_MISMATCH`. Both INVALID runs are preserved and are not scientific evidence.
- `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md` is the interpretation authority. `paper/saner_rene_claim_matrix_v1.json` is the claim-scope authority. `paper/saner_rene_manuscript_scope_lock_v1.md` is the manuscript scope authority. `paper/research_asset_map_v2.md` is the asset ledger. These roles are distinct and not interchangeable.
- The FinQA lineage now points to the materialized autopsy and preserves the superseded `CONTRACT_ONLY_OUTPUT_MISSING` state only in Git history.

### Reconciliation and verification

- LOCAL and GB10 begin at `e97340387888290e69fbfff122ab163de971b37e`, `main`, `0/0` against `origin/main`.
- The exact commit manifest contains 335 paths in seven logical groups. Eight byte-identical local duplicate scripts are held as `SUPERSEDED_DUPLICATE_DO_NOT_COMMIT`; G7 external/large assets remain outside Git.
- GB10 full pytest: `929 passed / 13 skipped / 1 deselected / 10 warnings`, exit 0.
- Paper claims: `PASS 79/79`, 5 claims. Submission package: `PASS 10/10`, `PENDING_EXTERNAL_ITEMS`, not submission-ready.
- Docs lint: `PASS 0 fail / 6 existing warnings`. STATE is 100 lines and INDEX is 180 lines. Frozen hashes: `5/5`, 0 violations.
- `git diff --check` is clean in LOCAL. GB10 dirty-worktree output contains CRLF/EOF presentation warnings on preserved legacy surfaces; no frozen artifact was rewritten.
- `skill-doctor`: `0 errors / 139 warnings`; `skill-map`: 240 skill files discovered across source/install roots. No auto-fix was used.

### Commit plan and current gate

The planned commit order is `G2 FINQA immutable history`, `G3 FinQA formal/autopsy`, `G4 other research`, `G5 paper`, `G6 engineering/tests`, `G1 governance/memory`, `G0 reports/index`. The two legacy supervisor moves are archive operations; the qoder archive comment/BOM cleanup is accepted as metadata-only and non-semantic.

Final cross-host verdict: `PASS / RECEIPT_VERIFIED`; `GIT_SYNC=LOGICAL_COMMITS_AUTHORIZED`. The earlier direct-live `CONDITIONAL` verdict is superseded by [`2026-10-11_cross_host_receipt_verification.json`](../experiments/2026-10-11_cross_host_receipt_verification.json). The actionable recordkeeping mismatches are closed and the exact 335-path candidate set is machine-readable in [`repository_governance_commit_manifest_2026-10-11.json`](repository_governance_commit_manifest_2026-10-11.json). The independent C receipt is [`../experiments/2026-10-11_loop_c_repository_governance_final_audit.md`](../experiments/2026-10-11_loop_c_repository_governance_final_audit.md). GB10 live repository state and in-repo receipts were directly checked; LOCAL is represented by the same-schema deterministic receipt. The receipts capture the immediately pre-commit snapshot. No commit, push, force operation, stash cleanup, worktree cleanup or external-data transfer has occurred.
