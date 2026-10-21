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
- Independent-new-family confirmation: a disjoint set of eight further
  CodeUpdateArena families was frozen before model output. Base passed `7/8`
  families and `44/48` tests; update-info passed `4/8` and `33/48`; paired
  difference `-3`, with 1 versus 4 `test_failure`. Ruling:
  `BOUNDED_NEGATIVE_REPLICATED_NEW_FAMILIES`. This strengthens the bounded
  negative but remains same-source synthetic evidence.
- External-source qualification selects PyMigBench as the stronger real-change
  source because it binds actual repositories and full commit SHAs. VersiCode
  is useful for version-change observability, but its 49,346 editing rows
  collapse to 85 code pairs and contain no behavioral oracle.
- VersiCode observability pilot: eight real name-change families, four
  information conditions and 32 frozen requests. BASE `0/8`, direct prose
  mapping `8/8`, the same mapping as structured fields `7/8`, and target
  package symbol probes `5/8`. The probe used about `4x` BASE tokens and was
  dominated by direct mapping. The one prose/structured discordance is a
  case-level observation, not representation superiority.
- PyMigBench bounded curation attempted 36 real commits with zero model calls
  and zero environment retries. No task produced a passing gold behavioral
  oracle. A dependency-aware single-task revival of `thombashi/datetimerange`
  reached `160 passed / 8 failed` at gold and failed parent collection under
  both declared environments. Ruling:
  `ZERO_TASK_ENVIRONMENT_CONTRACT_INSUFFICIENT`, not a source or hypothesis
  rejection.
- A second PyMigBench task, `emlid/ntripbrowser` `chardet -> cchardet`, was
  qualified after freezing Python, package locks, pycurl/libcurl/SSL tools and
  seven deterministic local tests. Parent/parent and gold/gold both pass `7/7`.
- The behavioral probe found a decisive oracle issue: BASE passed `7/7` hidden
  tests while failing the requested migration because an unimported
  `chardet.detect` raised `NameError` and a UTF-8 fallback masked it. PROSE and
  STRUCTURED both passed tests and the `cchardet` structural gate. Supported
  claim: dependency-migration evaluation needs behavioral plus structural
  checks. No representation superiority is established.
- A zero-model audit of 33 auditable PyMigBench commits found 13 code-only
  changes with no dependency-manifest contract and 19 with target dependencies
  named in manifest diffs. This is task-construction evidence, not model
  capability evidence.

## 3. Evidence Identity

- `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`: authored adaptive environments and
  tests.
- `POST_HOC_RECOMPUTATION_NOT_NEW_EXPERIMENT`: MA-CERD and review corrections.
- `MODEL_INTERFACE_QUALIFICATION_NOT_SCIENTIFIC_RESULT`: 25 model calls used to
  qualify the JSON/tool interface.
- `INVALID_HARNESS_REPLAY`: CodeUpdateArena V1 execution interpretation.
- `POST_HOC_EXECUTION_REVALIDATION_PUBLIC_SYNTHETIC`: CodeUpdateArena V2
  execution of the 16 frozen V1 generations, with zero new model calls.
- `DEV_ONLY_EXTERNAL_VERSION_CHANGE_OBSERVABILITY_ABLATION`: VersiCode
  syntax/name migration and information-representation observations only.
- `PUBLIC_REAL_COMMIT_METADATA_AND_LOCAL_TEST_CURATION`: PyMigBench metadata,
  repository checkout and JUnit evidence; no model calls.
- `PUBLIC_REAL_COMMIT_BEHAVIORAL_CASE_PROBE`: one qualified real-commit
  migration with hidden tests and structural dependency checks.
- Oracle-assisted material is labelled separately and is not actor input.

## 4. Governance And Recovery

- Protected evidence is outside the cleanup tree at
  `D:/AIRcommend/JinRongAgents/_protected_research_20261021_v1`.
- The integration branch is `research/portfolio-integration-v2`. Core commits:
  `550fd91` Paper E, `e7769c8` research/governance evidence, `0e123af` local
  evidence deltas, `8b6203f` adaptive V3, `37ef6b5` CodeUpdateArena V1/V2.
- The same branch name is pushed to `origin` and `gb10`; the exact integration
  tip is the branch head in Git rather than a second status authority.
- Confirmation run-time spec/runner bytes are preserved under
  `research/codeupdatearena_confirmation_v1/run_frozen/`; metadata links were
  corrected after execution without rewriting the frozen receipt.
- Runtime, caches and external source archives were not dumped into Git as
  research truth. CodeUpdateArena source is pinned at
  `836e2d157739fd53f9cde421913eb5949d4eeeb8` with license/data hashes.
- VersiCode and PyMigBench are pinned at
  `8a53b9938707deb4c8398152e9ebc923580783a3` and
  `d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b`. Source qualification and
  license caveats are in `EXTERNAL_CHANGE_SOURCE_INDEPENDENT_REVIEW.md`.
- GB10 holds the full external-source copies and artifact hashes under
  `~/wzh/protected_research_20261021_v1/external_sources/`. Local duplicate
  source caches remain only because recursive deletion was blocked by the
  execution policy; they are not a second source authority.
- Remaining recoverable differences are the local dirty main worktree, the
  protected GB10 VGMC branch material, and the temporary verification worktree.
  No `reset --hard`, forced main update or full-tree clean was used.

## 5. Cost

| Category | Attempts / calls | Accounting tokens |
|---|---:|---:|
| New generation POST | 101 | 57,222 |
| Model identity GET | 4 | not token-billed |
| CodeUpdateArena V1 hidden-test Docker programs | 100 | offline |
| CodeUpdateArena V2 revalidation iterations | 300 | offline |
| CodeUpdateArena independent confirmation | 96 | offline |
| Final V3 bound replay | 450 policy episodes / 1,215 policy-tool calls | offline |
| of which VersiCode observability generation | 32 | 15,917 |
| PyMigBench commit curation | 36 candidate commits | offline |
| PyMigBench single-task revival | 3 test runs | offline |
| NtripBrowser behavioral probe | 3 | 12,612 |
| PyMigBench dependency-contract audit | 33 commits | offline |
| Judge / training / paid API / production Memory | 0 | 0 |

Historical ledgers remain separate: 747 attempts / 1,564,176 tokens and 313
attempts / 324,086 tokens. New generation budget usage is `101/2048` attempts
and `57,222/10,000,000` tokens.

## 6. Next Experiment

Do not rerun VersiCode, CodeUpdateArena or the same prose-update comparison.
The next information-bearing experiment should replicate the hybrid behavioral
plus structural oracle on additional PyMigBench real commits, with target
dependency manifests frozen explicitly. Do not infer prose/structured
superiority from the current single case.
