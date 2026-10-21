# RESEARCH_PORTFOLIO_AND_ADAPTIVE_REVALIDATION_V2 Return

Date: 2026-10-21, Asia/Shanghai
Status: `COMPLETED_WITH_BOUNDED_NEGATIVE_AND_CONTINUE_RECOMMENDATION`

## 1. Three Earlier Lines

- Paper E remains `NARROW_AND_CONTINUE`. Its canonical manuscript is
  `paper/saner_rene_manuscript_v1.md`. The contribution is a bounded two-case
  measurement audit; FinQA is nested, not a third case. `WIDE_EVIDENCE_CHECK`
  passes and the review PDF is 10 pages. Submission still awaits owner actions
  for authors, venue, artifact URL/DOI and registration.
- FinRank remains `STOP_ON_CURRENT_PANEL`. Nothing in this Goal reopens H/K or
  turns the panel result into a general experience-learning claim.
- MA-CERD remains a development baseline plus an unverified selective
  escalation hypothesis. Corrected interpretation is in
  `research/ma_cerd_independent_v1/CORRECTIONS_20261021.md`: resource
  membership is not graph propagation; handling `0.012` is full-set exact
  matching; full-release values are not pure held-out; `o3_relation` is
  oracle-assisted; simulator/trace replay is still unavailable.

## 2. New Research Decisions

- Adaptive V3 is accepted as a corrected DEV_ONLY mechanism comparison:
  spawned-process RPC, opaque IDs, strict full-recompute validation and
  replay-bound receipts. Python 3.9/3.11 pass 24 tests; the final receipt binds
  450 episodes and budgets 0-9.
- On the authored fixtures, unit-cost greedy is sufficient: at three queries
  per fixture it reaches action loss `0`; two-step lookahead has 0 positive
  matched pairs, 7 negative pairs, and mean `greedy_loss - two_step_loss =
  -0.02037`. Stop further complexity on this fixture family.
- CodeUpdateArena V1 generations are preserved, but its executor is
  `INVALID_HARNESS_REPLAY`. The zero-request V2 revalidation blocks candidate
  marker/exit aliases, validates nonce-bound test lifecycles, distinguishes
  assertion failures, and pins the Docker image ID.
- Valid CodeUpdateArena result: base `3/8` families and `33/50` hidden tests;
  update-info `2/8` and `28/50`; paired difference `-1`. Failure taxonomy is 5
  versus 6 `test_failure`. Ruling: `BOUNDED_NEGATIVE_STOP_V2_VALIDATED`.
  This is a public synthetic development result, not natural production drift
  or a universal claim that update information is harmful.

## 3. Evidence Identity

- `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`: authored adaptive environments and
  tests.
- `POST_HOC_RECOMPUTATION_NOT_NEW_EXPERIMENT`: MA-CERD and review corrections.
- `MODEL_INTERFACE_QUALIFICATION_NOT_SCIENTIFIC_RESULT`: 25 model calls used to
  qualify the JSON/tool interface.
- `INVALID_HARNESS_REPLAY`: CodeUpdateArena V1 execution interpretation.
- `POST_HOC_EXECUTION_REVALIDATION_PUBLIC_SYNTHETIC`: CodeUpdateArena V2
  execution of the 16 frozen V1 generations, with zero new model calls.
- Oracle-assisted material is labelled separately and is not actor input.

## 4. Governance And Recovery

- Protected evidence is outside the cleanup tree at
  `D:/AIRcommend/JinRongAgents/_protected_research_20261021_v1`.
- The integration branch is `research/portfolio-integration-v2`. Core commits:
  `550fd91` Paper E, `e7769c8` research/governance evidence, `0e123af` local
  evidence deltas, `8b6203f` adaptive V3, `37ef6b5` CodeUpdateArena V1/V2.
- The same branch name is pushed to `origin` and `gb10`; the exact integration
  tip is the branch head in Git rather than a second status authority.
- Runtime, caches and external source archives were not dumped into Git as
  research truth. CodeUpdateArena source is pinned at
  `836e2d157739fd53f9cde421913eb5949d4eeeb8` with license/data hashes.
- Remaining recoverable differences are the local dirty main worktree, the
  protected GB10 VGMC branch material, and the temporary verification worktree.
  No `reset --hard`, forced main update or full-tree clean was used.

## 5. Cost

| Category | Attempts / calls | Accounting tokens |
|---|---:|---:|
| New generation POST | 50 | 17,698 |
| Model identity GET | 4 | not token-billed |
| CodeUpdateArena V1 hidden-test Docker programs | 100 | offline |
| CodeUpdateArena V2 revalidation iterations | 300 | offline |
| Final V3 bound replay | 450 policy episodes / 1,215 policy-tool calls | offline |
| Judge / training / paid API / production Memory | 0 | 0 |

Historical ledgers remain separate: 747 attempts / 1,564,176 tokens and 313
attempts / 324,086 tokens. New generation budget usage is `50/2048` attempts
and `17,698/10,000,000` tokens.

## 6. Next Experiment

Do not rerun the same authored fixtures or the same eight CodeUpdateArena
families. The next information-bearing experiment requires independent new
families or a different externally grounded change task, with the same strict
execution validity gate. If no such source or reference is available, retain
the bounded negative and stop this candidate rather than spending the remaining
budget on repeated prompts.
