# LC-GOV-002 — governance / archive inventory (mapping only)

> Executed 2026-09-24 by Loop D as a zero-model, read-only mapping (model calls 0, endpoints 0).
> The card's Loop A dispatch remains deferred pending a sandbox-scoping ruling for report-only agents;
> this execution therefore carries the same discipline as other Loop D relayed cards: independent audit PENDING.
> Card constraint honored: **nothing moved, deleted, renamed or re-registered**. Paths and line counts measured at commit 4ce848a (main).

## 1 Governance documents (docs/governance/)

| path | lines | status header (first 6 lines) | last commit |
|---|---|---|---|
| 2026-09-07_execution_plane_boundary.md | 86 | absent | 63bd8f7 (2026-09-08) |
| 2026-09-10_backlog_ledger_and_loop_restart_proposal.md | 257 | present: active proposal + ruling notes, original text preserved verbatim | 5af5b7c (2026-09-12) |
| 2026-09-11_serving_stack_provenance.md | 290 | present: active evidence record (read-only provenance, not config management) | ecce985 (2026-09-12) |
| 2026-09-24_gb10_experiment_safety_gates.md | 121 | present: active | c9c4536 (2026-09-24) |
| SKILL_REGISTRY.md | 20 | present: active machine-reconciliation source | 19867ad (2026-09-22) |
| audit/harness_audit_20260905/{AUDIT_REPORT,CRITIQUE,EVIDENCE,RESUME}.md | 156/80/210/72 | absent (audit bundle, baseline-pinned) | 2458eca (2026-09-06) |
| reference/ (21 templates and guides) | 52-684 each | mostly absent; RESEARCH_WRITING_WORKFLOW.md carries an active status line | 735813b (2026-08-25), except HOOK_AUTHORING_GUIDE.md db76cc3 (2026-09-12) |

Notes: docs_lint [2] requires status headers only for top-level live docs under docs/, so the absent
headers in reference/ and audit/ are compliant, not defects; they are recorded here for completeness.
SKILL_REGISTRY.md is the machine source for docs_lint [5] and sync_skills reconciliation.

## 2 Memory layer (memory/)

| file | lines | role |
|---|---|---|
| CORE.md | 54 | model topology and standing red lines |
| DECISIONS.md | 218 | ruling register |
| STATE.md | 93 | current-state summary |
| THREADS.md | 744 | active ledger (append-only) |

## 3 Archive (docs/archive/)

38 markdown files, all pre-2026-08 legacy or closed-out material (numbered project docs, legacy READMEs,
review reports, migration kits). Indexed by directory per docs/INDEX.md rule; no per-file ledger maintained.
No candidate inside archive/ requires action.

## 4 Archive / promotion candidates (observations only, no action taken)

1. docs/governance/loop_c_lead_architecture.md **does not exist on main**: it lives only on branch
   gb10/loop-c-lead-20260923 (commits 99d408a, dc20ab1) together with scripts/loop_c_lead.py and
   scripts/loop_c_lead.sh. Promotion candidate when the Loop C lead branch is merged; until then the
   control plane is documented only on that branch and in ~/.jinrong-loop-c CHECKPOINT.md.
2. docs/governance/2026-09-07_execution_plane_boundary.md lacks a status header and has not moved since
   2026-09-08; candidate for a status-line addition (not an archive move) in a future neat batch.
3. reference/ templates are untouched since 2026-08-25 except the hook guide; consolidation is a neat-batch
   decision, explicitly out of scope here.

## 5 Red lines observed

No file moved, deleted, renamed or re-registered; no INDEX.md edit; no memory edit; model calls 0;
no endpoint contact; findings limited to observations above.

## Loop D correction (2026-09-24, after independent audit REJECT)

The audit (qwen3.8-max packet session) refuted two entries; both corrections below are made with direct
probe evidence at commit 4ce848a, and the affected claims in the tables above are superseded by this
section.

- F1 (CRITICAL, accepted): the status-header probe used for the table matched only the Chinese key
  "状态"; docs/governance/2026-09-07_execution_plane_boundary.md carries an English-key header on line 2
  ("status: 活跃（裁定件, 边界冻结）"), inside the first-six-lines scope. Corrected entry: status header
  PRESENT; the document is compliant. Observation 2 of section 4 is WITHDRAWN: there is no missing
  status line and no remediation is proposed. Root cause: probe pattern, not the document.
- F2 (MAJOR, accepted): docs/governance/reference/ contains 19 entries at 4ce848a (18 markdown files plus
  multi-tool-sync.sh), not 21. Corrected entry: 19 entries (18 md + 1 sh); the md-only count is 18.
  Root cause: manual miscount while grouping the listing.
- Probe methodology corrected for future mappings: status probes must match both "状态" and "status:" keys,
  and directory counts must come from git ls-tree, never from manual grouping.
- No other table entry, observation or red-line statement is changed; the no-move/no-delete discipline
  stands, and the commit touching this report remains report-only.
