# B. Deterministic Recompute and Provenance Audit

Date: 2026-10-23, Asia/Shanghai
Scope: offline file reading, deterministic counting/statistics, source and hash verification.
Model/judge/training calls made by this worknote: **0**.
Mutable/frozen source files changed: **0**.

This worknote separates direct recomputation from source claims. It does not
upgrade an AI judge or an independent AI review to human gold.

## Executive Findings

1. The G3 depth-2 result `5/43` at 40/400 expansions is compatible with a
   same-budget random selector. Under sampling 40 of 400 with 43 useful items,
   the exact expectation is `4.3`, the exact hypergeometric
   `P[X >= 5] = 0.4347520938`, and the discrete equal-tail 2.5%/97.5%
   quantiles are 1 and 8. The existing "weak learnable signal" wording is not
   supported by this comparison.
2. `G3_VISIBLE_FEATURE_PREDICTION_V5.py` does not execute the protocol's
   nested per-fold cost-matched threshold. Inner thresholds are recorded but
   final decisions use globally averaged out-of-fold scores and one top-10%
   threshold over all 400 rows. The reported operating point is count-matched
   to 40 actions, not cost-matched to context characters.
3. The G3 oracle result is reproducible: always-expand has BOTH `187/400` and
   mean context `64,338.065` chars; oracle-selective has BOTH `187/400` and
   mean context `37,292.0075` chars while expanding the 43 target-useful rows.
   This establishes target-defined coverage/cost headroom only. It does not
   establish downstream action gain, and "no target gain" is not "no useful
   information".
4. G2 fixed-state completions recompute to:
   plain fact/action `2/8`, `1/8`; evidence-decision fact/action `3/8`, `1/8`.
   These are auxiliary semantic-judge/contract-validation counts, not human
   gold or independent executable outcomes.
5. `G2_FIXED_STATE_INDEPENDENT_REVIEW.json/md` contains a lineage conflict.
   It reports 7 reasonable action rows for each arm and says the two
   `09949c3c` action rows were changed to reasonable abstention. The current
   validated file instead has plain action `1 grounded / 6 reasonable / 1
   unnecessary refusal` and decision action `1 grounded / 5 reasonable / 2
   unnecessary refusals`; both `09949c3c` action rows remain unnecessary
   refusals. The review also records a stale SHA-256 for the validated file.
6. G2 and G3 BM25 implementations are not identical. G2 strips stopwords and
   short tokens; G3 retains them and adds session/time prefixes. The observed
   dim1 top-5 BOTH rates are G2 `0.430` and G3 `0.4675`; this difference cannot
   be attributed to a method effect.
7. The cumulative ledger is arithmetically closed at `536` accounting/physical
   calls and `3,713,363` accounting tokens, with `113` judge calls.
8. G3 call 2 raw request/response bytes exist and their computed hashes match
   the aggregate model-results declaration. Its local `call_receipt.json` does
   not itself declare body hashes. G3 call 1 raw bytes are lost; its
   `15,621` usage is supported by GB10 llama-server task `2810516`, but that
   log is outside the Git evidence package and remains a provenance weakness.

## 1. G3 Depth-2 Versus Same-Budget Random

Direct result source:
`research/publication_thesis_goals_v1/revision_v5/G3_VISIBLE_FEATURE_PREDICTION_RESULTS_V5.json`

- Population: 400 rows.
- Target-positive rows: 43.
- Decision budget: exactly 40 rows (`round(400 * 0.10)`).
- Depth-2 tree: 40 selected, 5 target positives, 35 target negatives.
- Same-budget random baseline without replacement:
  - expected positives: `40 * 43 / 400 = 4.3`
  - `P(X = 5) = 0.1860897516`
  - `P(X >= 5) = 0.4347520938`
  - exact 2.5% and 97.5% quantiles: 1 and 8
  - `P(1 <= X <= 8) = 0.9740350985`

Interpretation: `5/43` does not distinguish the tree from same-budget random
selection. This does not prove the visible features contain no signal. It
shows this experiment did not identify signal beyond random variation at its
operating point. The strongest stable statement is:

> In a 400-row development diagnostic, the depth-2 visible-feature selector
> found 5 of 43 target-useful expansions at 40 expansions; this is compatible
> with a same-budget random selector and is not evidence of a learnable policy.

## 2. Predictor Implementation Versus Protocol

Sources:

- `G3_VISIBLE_FEATURE_PREDICTION_PROTOCOL_V5.json`
- `G3_VISIBLE_FEATURE_PREDICTION_V5.py`
- `G3_VISIBLE_FEATURE_PREDICTION_RESULTS_V5.json`

Protocol claim:

- "5 outer stratified folds with three-fold inner cost-matched threshold
  selection, repeated over 5 fixed seeds"
- "at most 10% EXPAND decisions per training fold"

Actual code path:

1. `repeated_predictions()` calculates an inner OOF threshold separately in
   each outer fold and stores it in `fold_receipts`.
2. It trains on the outer training split and scores the outer test split.
3. It does not use the stored fold threshold to make test-fold decisions.
4. It averages each row's five outer-fold scores.
5. `main()` calls `cost_matched_threshold()` once on all 400 averaged scores.
   This selects the top 40 rows globally.

Therefore the final metrics are a development ranking diagnostic with global
OOF score averaging and a global 10% action-count operating point. They are not
nested frozen-threshold test predictions.

The function name `cost_matched_threshold` is also misleading for the reported
metric: it controls the number of EXPAND actions. The two models each select 40
rows but have different predicted context costs:

- logistic regression: `1,203,502` chars
- depth-2 tree: `1,194,603` chars
- always-expand top-5: `11,850,080` chars

The source data and protocol hashes are internally bound:

- predictor protocol SHA-256:
  `a601992202ee32b663927255b018a66c31a000408899e4445d5366cb8ac41b6b`
- result file SHA-256:
  `56f6a59a4ce8ba2ff597579bbf0cafb1e951af839258332f5138f469a6f11a34`
- result-declared protocol hash matches the current protocol file.

## 3. G3 Oracle and Context-Cost Recompute

Source:
`research/publication_thesis_goals_v1/revision_v5/G3_OFFLINE_RESULTS_V1.json`

Rows were recomputed by policy from the 2,000 row records:

| Policy | Rows | Expand | Target-useful expand | Final BOTH | Mean context chars |
|---|---:|---:|---:|---:|---:|
| keep top-3 | 400 | 0 | 0 | 144 | 34,712.865 |
| always expand top-5 | 400 | 400 | 43 | 187 | 64,338.065 |
| visible gap rule | 400 | 9 | 1 | 145 | 35,365.9175 |
| oracle gain rule | 400 | 43 | 43 | 187 | 37,292.0075 |
| oracle pair rule | 400 | 43 | 43 | 187 | 37,292.0075 |

The oracle policies use hidden `relevant_session_index` / expansion outcomes.
They diagnose attainable target coverage and input-size savings under this
evaluation target. They do not show:

- improved downstream answers or actions;
- that the other 357 expansions have no useful information;
- that a deployable selector can recover the oracle choices.

Offline provenance:

- source:
  `/home/testuser/wzh/protected_research_20261021_v1/stale_probe_20261023/T1_T2_400_FULL.json`
- source size: `305,908,212` bytes
- source SHA-256:
  `5f3ec375179e20e2e94469e018189188f34e2e7e5f21cbecbd99fcfa648c1876`
- source hash independently recomputed on GB10 and matches
  `G3_PROTOCOL_V1.json` / `G3_OFFLINE_RESULTS_V1.json`.
- `G3_OFFLINE_RESULTS_V1.json` and `G3_OFFLINE_DOUBLE_RUN_V1.json` are
  byte-identical:
  `07486af674c774841e3bd62a7bb588087d1ab02310fadc3a2b95dcb0100a18c5`.
- protocol SHA-256:
  `41cc670db422a5dc345301a54fdb6cab7939dbbf78eb7daf0a8d4da88f0ce84d`.

## 4. G2 Fixed-State Recompute

Source:
`research/publication_thesis_goals_v1/revision_v5/G2_SEMANTIC_JUDGE_VALIDATED_V5.json`

Direct row counting gives:

| Representation | Question | Grounded | Reasonable unknown/clarify | Unnecessary refusal | Stale/unsafe |
|---|---|---:|---:|---:|---:|
| plain fact bundle | fact | 2 | 5 | 0 | 1 |
| plain fact bundle | action | 1 | 6 | 1 | 0 |
| evidence-decision bundle | fact | 3 | 3 | 0 | 2 |
| evidence-decision bundle | action | 1 | 5 | 2 | 0 |

Thus the stable count-level statements are:

- plain: fact `2/8`, action `1/8`
- evidence-decision: fact `3/8`, action `1/8`
- action completion delta `0/8`
- fact completion delta `+1/8`, with wins/losses on different cases

This does not establish a representation gain. The representations do not
expose identical information, and the semantic classification remains an
auxiliary AI judge plus contract-level post-validation.

### Independent-review conflict

`G2_FIXED_STATE_INDEPENDENT_REVIEW.json` records the reviewed validated file
hash as:

`f275b1b02e22fdb61a348421d7644feb0d32b75dd08cd8d116f97ba33ab89322`

The current worktree file hash is:

`d3779c28877d087d2103e57c715ec14b047d48616d3dd8d893bb9bc643eff241`

The current committed Git object content, normalized to repository line endings,
also does not have the review's declared hash. More importantly, the counts
conflict:

- review: both action arms `1 grounded / 7 reasonable`
- current validated rows: plain `1/6/1`, decision `1/5/2`
- current `09949c3c` plain-action and decision-action rows are
  `UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE` in both raw and validated
  verdicts

Disposition: retain the independent review as historical/auxiliary evidence,
but do not use its action-category tally as the current result. Its stale hash
and count mismatch should be recorded as an explicit lineage correction.

## 5. G2/G3 BM25 Differences

Sources:

- `g2_retrieval_policy_probe_v5.py`
- `G3_incremental_evidence_probe.py`
- `G2_RETRIEVAL_POLICY_RESULTS_V5.json`
- `G3_OFFLINE_RESULTS_V1.json`

Implementation differences:

| Property | G2 retrieval-policy BM25 | G3 incremental-evidence BM25 |
|---|---|---|
| tokenization | lowercase alphanumeric | lowercase alphanumeric |
| stopwords | large fixed set removed | retained |
| tokens of length <=2 | removed | retained |
| document prefix | none | `session N time <timestamp>` |
| indexed message roles | not indexed as text | role labels indexed |
| BM25 constants | k1 1.5, b 0.75 | k1 1.5, b 0.75 |
| tie behavior | earlier session wins | earlier session wins |

Observed dim1 top-5 BOTH rates:

- G2 `original_bm25_top5`: `0.430` (`172/400`)
- G3 `always_expand_top5`: `0.4675` (`187/400`)

This `0.0375` difference is confounded by retrieval implementation. It must
not be attributed to G2 versus G3 method behavior. The G2 result also lacks a
declared source-data path/hash, so exact source identity with G3 is not proven
from the G2 output alone.

## 6. G3 Provenance Gap

Call 1 (`18866d40-4641-4c2b-a8d5-fa6f2fa4913d`):

- request and response raw bytes are absent;
- failure receipt records prompt `15,109`, completion `512`, total
  `15,621`;
- GB10 `/tmp/llama-8004-vision.log` currently contains task `2810516` with
  exactly `15,109 + 512 = 15,621`;
- the log is outside the protected/Git evidence package and is mutable.

Call 2 (`18ef1a92-4489-477c-8ad7-257bc4795ee8`):

- raw `request.bin` exists, size 40,099, SHA-256
  `643aacdbcbed6e9f35e8156324101548aef4cfb3f9b6fa89a30e84476427b600`;
- raw `response.bin` exists, size 1,292, SHA-256
  `346b2ed481a93ff16f317378a88d85c7944f70494e6a9199775c8c616e4848d4`;
- both hashes are declared in `G3_INCREMENTAL_EVIDENCE_RESULTS_V1.json` and
  match recomputation;
- the raw directory's `call_receipt.json` contains usage/parse fields but no
  request/response hash fields.

Ruling: there is a self-describing raw-receipt gap and a missing call-1 raw
chain, not a complete call-2 hash gap. This is an engineering/provenance
limitation. It is not evidence of a model-policy scientific failure.

## 7. Ledger Recompute

Source:
`research/publication_thesis_goals_v1/RESOURCE_LEDGER.json`

Increment arithmetic:

- revision v2: `1` attempt, `1,849` tokens, `0` judge calls
- revision v3 increment: `76`, `217,096`, `0`
- revision v4 increment: `349`, `2,831,240`, `67`
- revision v5 increment: `110`, `663,178`, `46`
- totals: `536` attempts, `3,713,363` tokens, `113` judge calls

Cross-check against cumulative revision snapshots:

- v3 total `77 / 218,945`
- v4 total `426 / 3,050,185`
- v5 total `536 / 3,713,363`

All values agree. Training, paid API, and production Memory writes remain
zero in this ledger.

## 8. Evidence Identity and Limits

Directly recomputed:

- hypergeometric random comparison;
- policy row counts and mean context characters;
- G2 semantic row counts;
- file SHA-256 values;
- ledger increment arithmetic;
- G3 source file hash on GB10;
- G3 call-2 raw hashes and aggregate declarations.

Source-supported but not independently reconstructed:

- call-1 exact usage from the live GB10 llama-server log;
- original actor/judge semantic validity.

Not established by these checks:

- learnability of the G3 selector;
- downstream value of oracle-selected expansions;
- semantic or human gold correctness of G2 classifications;
- method equivalence of the G2 and G3 retrieval panels.

## Frozen-State Check

- Local repository HEAD at audit:
  `9e43b0380588adc5b4b5b6c14481ae636349cb96`
- GB10 repository HEAD at audit:
  `9e43b0380588adc5b4b5b6c14481ae636349cb96`
- Local status before worknote write: clean.
- No frozen node, protocol, raw response, old result, or score was modified.

