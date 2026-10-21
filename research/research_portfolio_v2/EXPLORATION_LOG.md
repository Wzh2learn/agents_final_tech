# Research Portfolio Exploration Log

Goal: `RESEARCH_PORTFOLIO_AND_ADAPTIVE_REVALIDATION_V2`
Started: 2026-10-21, Asia/Shanghai
Status: `S3_EXTERNAL_CHANGE_ACTIVE`

This is the concise execution log for the current Goal. It does not replace
`memory/STATE.md`, `memory/THREADS.md`, or `docs/research/README.md`.

## S0: Protection and Corrections

- Real-time start recorded at `2026-10-21 10:44:33 +08:00`.
- Protected evidence package:
  `D:/AIRcommend/JinRongAgents/_protected_research_20261021_v1`.
- The package contains Git refs, staged and unstaged binary diffs, real
  untracked content, SHA-256 manifests, GB10 VGMC deltas, and the temporary
  `jr_verify_3003faa` patch/HEAD.
- Credential-like paths were excluded from the untracked content archive.
- Five sample files, including an 80 MB cache and a paper draft, were
  extracted and matched both source and manifest hashes.
- Dated scientific corrections are in
  `research/ma_cerd_independent_v1/CORRECTIONS_20261021.md`.

## Current Scientific Boundaries

- Paper E remains `NARROW_AND_CONTINUE`.
- FinRank history remains `STOP_ON_CURRENT_PANEL`.
- MA-CERD resource membership is a development baseline; selective
  escalation remains a hypothesis requiring new evidence.

## S1 Qualification

- Nearest-work boundary checked against BudgetPM, PACMI and Invalidation
  Contracts. The retained A/B question is action-loss query selection and
  local revalidation when dependency/change contracts are incomplete, not
  budgeted observation selection or graph invalidation in general.
- CodeUpdateArena is qualified only as a bounded public synthetic API-update
  adapter. Source commit, MIT license, data hash and execution constraints are
  recorded in `EXTERNAL_SOURCE_CODEUPDATEARENA.json`.
- Eight deterministic development families were selected before model output
  in `CODEUPDATEARENA_DEV_FAMILIES.json`.
- Model/interface qualification is preregistered for 2026-10-21 11:30-12:30
  Asia/Shanghai, with 24 reserved attempts across the existing :8004 and
  :8006 services. These are interface qualification calls, not scientific
  evidence.

## S2 Observed Results and Stops

- Adaptive budget sweep is DEV_ONLY. At budget 3 per scenario, unit-cost
  greedy reached action loss `0.0` with 27 total queries; two-step lookahead
  remained `0.1296` with 27 queries and reached zero only at budget 6. Random
  checking remained `0.3704` at budget 3. The authored fixtures therefore
  support simple greedy over two-step lookahead, not a complex policy claim.
- Independent review blocked V2 scientific comparison because policy objects
  could inspect evaluator internals and semantic scenario IDs leaked outcome
  classes. See `ADAPTIVE_ENV_INDEPENDENT_REVIEW.md`.
- Real model query-policy scout V1 used 3 requests and repeated
  `inspect_dependency(total)`; the fixed evidence contract rejected the
  duplicate.
- Scout V2 used 6 requests. It avoided the first duplicate but repeated a used
  query despite an explicit no-repeat contract and filtered legal list, then
  stopped on `illegal_query`. Partial performance over two scenarios is not a
  scientific comparison because the V2 environment retains the review's
  leakage defects.
- Ruling: `STOP_MODEL_QUERY_POLICY_CURRENT_INTERFACE`. Do not run scout V3
  until actor capability isolation and opaque identifiers are implemented.

## Paper E State

- Canonical source is `paper/saner_rene_manuscript_v1.md`.
- Independent recommendation is `NARROW`; the bounded two-case measurement
  audit remains worth continuing, while universal-method or generic Agent
  claims are rejected.
- The final source, claim matrix, scope lock, readiness gate, citations and
  derivative PDF are synchronized. `WIDE_EVIDENCE_CHECK` passes.
- The PDF remains 10 pages with non-fatal underfull warnings. Submission,
  author order, venue and artifact DOI remain owner actions.

## V3 Corrected Mechanism Result

- V3 moves policy execution behind spawned-process canonical JSON RPC and uses
  stable opaque actor identifiers. Independent tests cover capability
  isolation, semantic-label mutation, result tampering and receipt replay.
- Python 3.9 and 3.11 each pass 22 tests. The deterministic replay contains
  450 policy episodes over nine families and budgets 0-9; receipt verification
  passes with 19 source hashes.
- Across 90 matched-budget/scenario pairs, two-step lookahead has zero positive
  pairs, seven negative pairs and mean `greedy_loss - two_step_loss = -0.02037`.
  `greedy_sufficient=true`, `two_step_adds_paired_benefit=false`.
- Ruling: stop further complexity on the authored mechanism environment. The
  next information-bearing step is the preregistered CodeUpdateArena synthetic
  public adapter comparing `base` versus `update_info` under real generated
  code and hidden unit-test execution.

## External Adapter Result

- CodeUpdateArena source and eight-family selection were frozen at commit
  `836e2d157739fd53f9cde421913eb5949d4eeeb8`. Oracle execution passed all
  8 families and 50 hidden tests before model calls.
- The single bounded run used 16 generation requests and 9,986 accounting
  tokens with zero retries and zero infrastructure failures.
- `base` passed 3/8 families and 28/50 hidden tests. `update_info` passed 2/8
  and 22/50. The paired all-tests-pass difference is `-1`.
- Ruling: `BOUNDED_NEGATIVE_STOP`. In this model/configuration and public
  synthetic task set, adding update information did not improve code
  adaptation and reduced one passing family. This does not establish that
  update information is universally harmful.
- Cumulative new-goal accounting is 50 attempts and 17,698 tokens. No further
  requests are warranted on the same eight families.
- Independent review invalidated the first execution interpretation: generated
  code could fake the result marker or exit before hidden tests, and assertion
  failures were mislabeled as runtime failures. Preserve V1 raw generations but
  treat its executor metrics as `INVALID_HARNESS_REPLAY`. A zero-request V2
  re-execution is required before using the paired result scientifically.
- V2 blocks marker forging/early exits with candidate AST rules and trusted
  nonce-bound test lifecycle markers, pins the Docker image ID, and separates
  assertion failures from runtime/marker failures. The zero-request replay
  confirms `3/8` versus `2/8`, paired difference `-1`; base failures are 5
  `test_failure`, update-info failures are 6 `test_failure`.
- Valid ruling: `BOUNDED_NEGATIVE_STOP_V2_VALIDATED`. Update information did
  not improve this frozen model/configuration on the eight development
  families. This remains a bounded synthetic result, not a universal harm
  claim.

## Independent-New-Family Confirmation

- Eight further CodeUpdateArena families were frozen before model output,
  disjoint by update ID and covering seven remaining change types plus
  `re.sub:add-function`.
- Oracle execution passed 8/8 families and 48 hidden tests before generation.
- The strict confirmation used 16 requests and 10,995 tokens with zero retries
  and zero infrastructure failures.
- Base passed `7/8` families and `44/48` hidden tests; update-info passed `4/8`
  and `33/48`. The paired difference is `-3`, with 1 versus 4 `test_failure`.
- Ruling: `BOUNDED_NEGATIVE_REPLICATED_NEW_FAMILIES`. This strengthens the
  bounded negative but remains same-source synthetic evidence.
- At this checkpoint, cumulative new accounting was `66/2048` attempts and `28,693/10,000,000`
  tokens. The next comparison should use structured preconditions or
  executable checks, not another prose-only update arm.

## External Change Source Qualification

- VersiCode is pinned at `8a53b9938707deb4c8398152e9ebc923580783a3`.
  Its editing payload has 49,346 rows per direction but only 85 unique code
  pairs and only `name_change` records. It is qualified for observability
  ablation, not behavioral correctness.
- PyMigBench is pinned at `d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b`.
  It has real repository/full-commit migration records and structured change
  metadata, making it the preferred behavioral source after executable task
  qualification.
- Independent source review and license/provenance limits are in
  `EXTERNAL_CHANGE_SOURCE_INDEPENDENT_REVIEW.md`.

## VersiCode Observability Pilot

- A pre-model review found exact gold-code substring leakage in one task. That
  task was removed, the validator was strengthened, and revision 3 passed the
  targeted re-review before any model request.
- The frozen run used eight unique dependency/name-change families and four
  arms: BASE, prose mapping, structured mapping and target-package probe
  evidence. There were 32 requests, zero retries and 15,917 accounting tokens.
- Correct symbol migrations were BASE `0/8`, prose `8/8`, structured `7/8`
  and probe `5/8`. The deterministic nearest-name rule was `4/8`.
- Probe evidence succeeded exactly when the target symbol appeared in the top
  candidates and cost about `4x` BASE tokens. Direct mapping dominated it in
  both accuracy and cost.
- The single prose/structured discordance is not evidence that prose is
  generally superior. VersiCode has no behavioral execution oracle; the result
  is limited to syntax and hidden target/old symbol use.
- Independent post-run review reproduced all 32 raw outcomes and token totals.

## PyMigBench Behavioral Curation

- A bounded 36-commit curation used zero model calls and zero failed-environment
  retries. It retained zero tasks because no gold revision reached a valid
  all-tests-pass behavioral oracle.
- A one-task dependency-aware revival of `thombashi/datetimerange` ran parent
  and gold exactly once. Parent collection failed on a historical
  `DataProperty` API mismatch; gold produced `160 passed / 8 failed` because
  tzdata and timezone semantics were not fixed by the declared environment.
- Ruling: `ZERO_TASK_ENVIRONMENT_CONTRACT_INSUFFICIENT`. Do not repair the
  environment after observing failures. The next task must freeze Python,
  package locks, tzdata, timezone and tests before model calls.
- Cumulative new accounting is `98/2048` attempts and
  `44,610/10,000,000` tokens.

## Next Actions

1. Freeze one PyMigBench task environment end to end and require gold
   all-tests-pass before any behavioral model request.
2. Keep VersiCode as a bounded nonbehavioral observability pilot; do not rerun
   its four arms.
3. Preserve Paper E, FinRank and MA-CERD rulings unchanged.
