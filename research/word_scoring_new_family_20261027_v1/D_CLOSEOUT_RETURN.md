# Loop D Knowledge Closeout

Date: 2026-10-27, Asia/Shanghai
Status: `PAUSED_AFTER_CONDITIONAL_C_REVIEW`

## Impact

This closeout separates completed engineering evidence from unresolved
scientific claims. It prevents the internally rendered Word draft from being
mistaken for submission-ready output and prevents the D/T/M comparison from
being mistaken for a binding-mechanism result.

## Fact Surfaces

| Surface | Status | Evidence |
|---|---|---|
| Code | `changed-and-verified` | Scoring V3, persistent budget, Word source/conversion and 12/12 Scoring-V3 tests are present; focused suites passed |
| Runtime | `verified-local-only` | GB10 Qwen3-4B generation and LibreOffice rendering occurred; no production or external service was used |
| Documentation | `changed-and-verified` | `LOOP_D_RESEARCH_PROMPT.md`, `memory/STATE.md`, `memory/THREADS.md`, `docs/research/README.md` and this return carry one current account |
| Rules | `verified-current` | Parent/project `AGENTS.md` and thin `CLAUDE.md` pointers remain applicable; no rule change was needed |
| Memory | `changed-and-verified` | Project STATE/THREADS/DECISIONS updated; platform-generated memory remains read-only |
| Workspace | `pending-local-untracked-only` | GB10 research-branch conflicts were resolved and pushed at `c644cb4f5`; local and GB10 `main` are synced at `9c92d4cf`. The untracked local `paper_e_word/` copy still prevents a clean research-branch merge into local `main`; historical GB10 worktrees remain preserved |

## Current Scientific State

1. Paper E has a 14-page internally rendered Word/PDF draft and 24 numbered
   references, but C found submission-grade defects: a missing sixth checklist
   step, fused table/list structure, incomplete table numbering/captions, and
   bibliography/citation ordering defects. Status is
   `INTERNAL_RENDER_ACCEPTED_WITH_DEFECTS`, not submission-ready.
2. Scoring V3 is confirmed for the three paired-control families and pure
   rescore. Old V2 results remain historical and are not natural error rates.
3. The eight-family panel is valid as
   `SAME_SOURCE_NEW_TABLE_FAMILIES`; it is not cross-source or
   pretraining-disjoint.
4. The D/T/M mechanism effect is not identified. Arm membership is perfectly
   confounded with 512-token output-budget exhaustion. `M` did not receive a
   fair trial, so neither `STOP_M` nor a method gain is justified.
5. The persistent ledger is structurally valid. Accounting is 27 physical
   reservations, 24 persisted raw rows, 25 reported generate calls with an
   independently supported range of 24-25, and 46,054 consumed input+output
   tokens. One discarded generation is asserted by a hardcoded fault recorder,
   not instrumented at runtime.

For Windows checkout compatibility, 24 generation receipt filenames were
renamed from `D:<uid>.json`, `T:<uid>.json` and `M:<uid>.json` to the matching
`D_<uid>.json`, `T_<uid>.json` and `M_<uid>.json` forms in commit `2b51ae607`.
File contents were unchanged.

## Resource State

- A/C collaboration: `28/28`, exhausted.
- This stage consumed 27 physical reservations and 46,054 input+output
  tokens; training, judge, paid API, service and production calls were zero.
- Conservative global remainder after this stage: 377 physical generation
  attempts and 2,543,008 generation tokens. Training remains
  `2 runs / 3,680,052 tokens` but is not authorized by this closeout.
- A scientifically valid D/T/M rerun requires a new explicit budget and a
  24-call panel with output limits above the observed truncation point.

## Cleanup Candidates - Not Deleted

- Local untracked `research/word_scoring_new_family_20261027_v1/paper_e_word/`:
  redundant with the pushed research branch and contains debug/intermediate
  renders. Keep until the user confirms removal or protected relocation before
  any future research-branch merge into local `main`.
- GB10 historical worktrees:
  `decision_residual_worktree_20261026`,
  `next_research_stage_worktree_20261026`,
  `phase_b_worktree_20261026`,
  `publication_proxy_calibration_worktree_20261026`,
  `adaptive_mechanism_worktree_20261027`.
  Preserve until their unique evidence and branch merge status are reviewed.
- Local visualization temp projects `paper_e_compile_20261027` and
  `managed_paper_e_20261027` outside the repository. These are rebuildable
  compile attempts and can be removed after user confirmation.

## Security Pending

The changed-document scope passed a secret-shape scan. A read-only whole-tree
scan separately detected credential-shaped material in the ignored `.env`
carrier. Values were not copied into project documentation. The file was not
modified or deleted. The owner must decide whether the credentials are live,
rotate them if necessary, and choose a secure storage/cleanup path.

## Next Decision

Choose one path before any new experiment:

1. Paper E first: fix the four Word blockers and non-blocking bibliography/
   caption issues, then prepare Owner submission fields.
2. Mechanism first: request a new 24-call, higher-output budget and rerun the
   frozen D/T/M panel under unchanged Scoring V3.

No further research, generation, submission or cleanup is authorized by this
closeout.
