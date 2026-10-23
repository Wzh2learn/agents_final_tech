# Research Baseline And Reuse Map

Date: 2026-10-23, Asia/Shanghai

Status: `RESEARCH_BASELINE_READY_WITH_LOCAL_GAPS`

Evidence identity: `DERIVED_GOVERNANCE_BASELINE_FROM_FROZEN_OR_DATED_ARTIFACTS`.
This document does not certify a new method, thesis contribution, human gold,
blind review, or Paper E submission.

Local, `origin/main`, and GB10 were observed at
`9e43b0380588adc5b4b5b6c14481ae636349cb96` on 2026-10-23. Exact refs,
status, hashes, and lineage are in `RECONCILIATION.json`.

## 1. Stable Research Questions

| ID | Research question | Relationship to old work |
|---|---|---|
| `RQ-M` | Measurement validity: under defensible scoring/visibility contract changes, which defects and decisions remain stable? | Paper E. FinQA and FinRank are two bounded cases. |
| `RQ-U` | Evidence sufficiency and reliable use: after old state is invalidated, can the system recover enough current facts/constraints for a grounded, safe, appropriately uncertain action? | Continues only the old G2 measurement-repair line. |
| `RQ-A` | Task utility and cost of evidence acquisition: when the next check may change the decision, which evidence should be acquired under token/tool/time cost? | Continues old G3 incremental evidence as a separate acquisition problem. |
| `ALT-L` | Learning fallback: can a small model learn a verifiable evidence-use/check-selection condition on a new task? | Fallback mechanism study, not a fourth certified contribution. |

RQ-U and RQ-A stay separate only while their outcomes remain distinct. RQ-U
holds evidence/state fixed and tests sufficient-state recovery plus action use.
RQ-A chooses whether to acquire evidence and tests downstream utility plus total
cost. If retrieval changes and state/action are rewritten in one pipeline, merge
the claims and do not count the pipeline twice.

## 2. Scientific Conclusion Table

| Research question | Source/task identity | Independent unit | Actual execution | Strongest conclusion | Strongest simple baseline / competition | Ruling | Nonclaims | Reusable assets | Evidence needed to re-enter |
|---|---|---|---|---|---|---|---|---|---|
| Paper E measurement validity | TAT-QA-derived staged document evaluation plus FinRank revision `916dc27e...`, arXiv `2608.07400v1` | Source-table clusters for Case 1; record/source clusters for Case 2 | Frozen deterministic analysis, source-informed post-hoc audit, two-environment reproduction, claim matrix, private artifact | A two-case audit separates visibility, detection, criterion-relative harmfulness, score-contract sensitivity and decision stability; the reproduction gap remains unexplained | Flat/hierarchical equivalence under one responsive leaf; released scorer and alternate tie/source contracts | `NARROW_AND_CONTINUE / SUBMISSION_HANDOFF_READY` | General agent-evaluation theory; universal benchmark failure; blind validation; learning method | `PAPER_E_CANONICAL`, `PAPER_E_CLAIM_MATRIX`, `PAPER_E_ARTIFACT`, `PAPER_E_HANDOFF` | Owner identity/affiliation and external submission action |
| FinRank H/K experience reuse | Historical pool plus fixed 16-task/8-source-cluster panel | Task-source cluster | B0 16/16; H/K stopped; U/E stopped on identical context | This panel has a ceiling and does not identify an accuracy increment from history | B0 and sufficient generic rules | `STOP_ON_CURRENT_PANEL` | History is generally useless; models cannot fail; unrun H/K have zero benefit | B0 runner, task bundles, source clusters, authorization/ledger | New family with a real experience action site, unseen clusters, matched K/R/H-U/H-S information and cost |
| MA-CERD selective escalation | Controlled dependency traces and handling queue | Object/trace family | Membership baselines, allowed-set replay, dated corrections; no independent trace replay | `resource_ids` membership is not dependency-edge propagation. `0.012` is full allowed-set exact match; 241/250 rows only defer. Subset legality is not task success | Resource membership, always-defer, allowed-set enumeration | `STOP_CURRENT_METHOD_LINE / KEEP_BOUNDARY` | Graph propagation works; escalation ranking is proved; policy acceptance equals simulator execution | Membership runner, action parser, corrections, trace inventory | Independent trace replay with separate enumeration, action, execution, risk and cost |
| Adaptive V3 active revalidation | Authored mechanism fixtures | Transition/family fixture | Offline replay with fixed repairer and paired decisions | Greedy transparent policy is sufficient on current fixtures; two-step lookahead has no positive paired gain | No-op/full/changed-key/BFS/greedy/random | `STOP_COMPLEX_PLANNER / KEEP_ENVIRONMENT` | Real distribution or general active-check superiority | Replay env, repairer, cost accounting | New natural/preregistered families and downstream loss |
| CodeUpdateArena adaptation | Public synthetic API updates, frozen adapter | Repository/update family | Executor correction, development and new-family runs | Current prose-update arm is a bounded negative result after fixing execution | Alias-aware static plus repository/behavior | `STOP_CURRENT_PROSE_UPDATE_ARM` | API adaptation generally fails; natural production drift; method superiority | Adapter, manifests, tests, failure receipts | New update/action family with strong-baseline blind spot and independent checker |
| VersiCode observability | Eight name-change families | Change family | Parser/API observability probes | Syntax/API-name changes are observable in these families | Plain diff and static name checks | `KEEP_AS_OBSERVABILITY_BOUNDARY` | Behavioral correctness; prose/structured superiority | Frozen inputs, parser, observation fields | Behavior-changing families with executable oracle |
| PyMigBench / real migration | NtripBrowser; Partridge `09e89d9...`/`daefcbe...` | Repository migration family | Source/test replay, paired controls, natural candidates | Tests can miss contract incompleteness; alias-aware static plus behavior is already 6/6 on Partridge | Repo tests, alias-aware static, behavior contracts | `KEEP_AS_BOUNDARY_AND_TASK_SOURCE` | Hybrid oracle generally sufficient; Paper E third case | Pinned sources, tests, oracle boundary, replay scripts | Multiple independent families and a post-baseline method gap |
| Scope evidence reuse | 20 authored fixture-to-short transitions | Controlled transition | Scope, always-full and exact-cache replay | The 30-versus-35 saving is exactly explained by exact-input cache plus miss revalidation | Same 15 CORRECT/5 ABSTAIN, 30 probes and 20 identical decisions | `CLOSE_SCOPE_PANEL` | Scope inference adds utility; learned expiry works | Policy, fingerprints, exact-cache falsifier | Shared cache identity but different valid checks/actions |
| STALE/state card | Generated/expert-edited STALE 400 scenarios; CUPMem direct neighbor | UID development case, not natural family | Fixed-evidence/fixed-state actor, auxiliary judge, E2E one-call/two-stage | Two-stage reduces observed stale/unsafe output but trades toward abstention/refusal; generated bundles sometimes omit positive current facts | One-call, plain, equal-information structured, reasonable-abstention | `CONTINUE_RQ_U_DEVELOPMENT_ONLY / NO_METHOD_GAIN` | New Memory architecture; facts automatically transfer; safety equals accuracy | STALE data, visibility split, contract, runners, raws | Equal-information sufficient-versus-extracted facts and unseen UIDs |
| Incremental evidence acquisition | Same STALE T1/T2 400 development set; ranks 4-5 | UID development unit | 400-row replay; interface attempt with two failed calls | Oracle coverage/cost headroom exists; no deployable selector is established | Never/always/same-budget-random/visible/cheap strong | `KEEP_RQ_A_WITH_HEADROOM / NO_POLICY_CLAIM` | `5/43` proves learning; 357 rows have no information; oracle chars equal total cost | Runner, BM25 variants, oracle diagnostics, receipts | Valid KEEP/EXPAND interface, random control, fixed reader and unseen-family gain |
| Valentine/VGMC/DPO | Valentine ZIP audit, 146-column Q3 review, VGMC and DPO builders | Conservative origin cluster | ZIP inspection and label/replay audits | Independence/native trajectory requirements fail; Q3/DPO labels are not confirmation labels | Origin grouping and provenance gates | `DATA_NO_GO_FOR_OLD_LABEL_REUSE` | All learning invalid; Q3 is gold; 60 pairs are independent | Manifests, audits, replay builders, label lessons | New native, bidirectional, independently checked supervision |
| PRM/training smoke | PRM800K smoke, Qwen3-4B, LoRA r=8 | Problem groups; arms overlap | Two-step GB10 SFT chain with adapters and held-out loss | Dataset-selection-training-checkpoint-eval plumbing works only | No-training and generic SFT | `REFERENCE_TRAINING_SMOKE_ONLY` | Effect size, learning gain, distillation, paper evidence | Runner, configs, adapters, receipts | New task/data, disjoint arms, adequate steps and non-training baselines |

## 3. Corrections That Control Future Interpretation

| Issue | Audited fact | Adopted correction | Consequence |
|---|---|---|---|
| G3 depth-2 tree | Selecting 40/400 with 43 positives gives random expectation `4.3`; hypergeometric `P(X>=5)=0.434752`, central 95% range `1-8` | `5/43` is compatible with random variation, not a learnable signal | Card 2 requires same-budget random and a strong cheap baseline |
| G3 predictor protocol | Inner thresholds are stored, but final decisions use globally averaged OOF scores and one top-10% cutoff over all 400 rows | Development ranking diagnostic, not nested frozen threshold execution; 10% actions is not cost matching | Freeze an online rule and match action/tool/token cost |
| G3 oracle | Always top-5: 187/400 BOTH and 64,338 mean chars; oracle-selective: 187/400 and 37,292 | Coverage/cost headroom only; 357 expansions can contain unmeasured useful information | Measure downstream gain and complete cost |
| G2 recovery | Plain facts/actions `2/8`,`1/8`; decision `3/8`,`1/8`. Book bundle drops a positive current preference; `09949c3c` compresses nuanced state to binary | Separate old-state invalidation, sufficient current facts/constraints and downstream use | Card 1 compares sufficient facts with actually extracted facts |
| G2 review count | Current action labels are plain `1/6/1` and decision `1/5/2` for completion/reasonable/unnecessary refusal | Historical `1 + 7 reasonable` for both arms is a misreading; `09949c3c` is also misdescribed | Preserve historical review; use case-level JSON for current counts |
| G2/G3 BM25 | G2 removes stopwords/short tokens; G3 retains them and adds session/time prefixes. BOTH is 0.430 versus 0.4675 | Different implementations; method cannot explain the difference | Card 2 freezes one retrieval contract |
| G3 provenance | Call 2 raw has no receipt body hash; call 1 raw lost, usage 15,621 recovered from server task `2810516` | Engineering/provenance gap and `UNEVALUATED_NO_VALID_DECISION`, not accuracy | Repair interface/provenance before policy interpretation |

## 4. Reusable Asset Map

| asset_id | path/host | version | verified content/date | access | environment/input | license/pollution | executable entry | stage | reuse cost | owner/todo |
|---|---|---|---|---|---|---|---|---|---|---|
| `PAPER_E_CANONICAL` | `paper/saner_rene_manuscript_v1.md` | SHA `3A914D04...C77AF5` | unique two-case manuscript, 2026-10-23 | available | Markdown/TeX | internal draft | package build entry | submission | low | Owner identity/submission |
| `PAPER_E_CLAIM_MATRIX` | `paper/saner_rene_claim_matrix_v1.json` | SHA `5D2BA487...131CA` | claim/evidence pointers checked | available | manuscript artifacts | post-hoc stays labeled | `research/validate_paper_claims.py` | submission gate | low | keep synchronized |
| `PAPER_E_ARTIFACT` | `research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/` | 2026-10-21/23 package | PDF/manifest/stats/reproduction located | private | local+GB10 | release/license Owner-only | package receipts/audits | submission | low-medium | release decision |
| `STALE_400_DEV` | GB10 `protected_research_20261021_v1/stale_probe_20261023/T1_T2_400_FULL.json` | SHA `5f3ec375...c1876`, 305,908,212 B | protocol/replay hash checked | GB10 protected | actor fields + hidden refs | generated/expert-edited; extensively developed | G3 `offline` CLI | RQ-U/RQ-A dev | medium | new unseen confirmation split |
| `G2_MEASUREMENT_CONTRACT` | `revision_v5/G2_EVALUATION_CONTRACT.md` | V5 | five outcome classes/vector checked | available | calibration + auxiliary judge | AI judge not gold | semantic judge/validator | RQ-U measurement | low | add sufficient-fact vector |
| `G2_FIXED_STATE_RUN` | `revision_v5/g2_fixed_state_transfer_fixed_slots_20261023_v5/` | 8 UID x 2 bundles x 2 questions | raw/receipts/labels checked | available | Qwen3.6, BM25 top-5 | development and same-family judge | fixed-state runner | RQ-U dev | medium | not held-out |
| `G2_E2E_REVIEW` | `revision_v5/G2_E2E_TOP5_INDEPENDENT_REVIEW.*` | 16 UID x 2 arms | aggregate/rows checked | available | outputs + AI review | AI review, not human reference | direct JSON/MD read | diagnosis | low | current summary correction |
| `G3_EVIDENCE_RUNNER` | `revision_v5/G3_incremental_evidence_probe.py` | SHA `B2C6CB84...60D1` | CLI and hidden-field contract checked | available | STALE_400_DEV; optional `:8004` | hidden indices eval-only | `offline`/`run-model` CLI | RQ-A dev | low | valid interface + reader |
| `G3_EVIDENCE_RESULTS` | `revision_v5/G3_OFFLINE_RESULTS_V1.json` | SHA `07486AF6...18C5` | 400 rows + byte-identical double run | available | derived from STALE_400_DEV | coverage/cost only | G3 runner | RQ-A evidence | low | no information-free claim |
| `G3_MODEL_RECEIPTS` | `revision_v5/G3_MODEL_*` | 2 calls, 0 valid decisions | usage/provenance checked | partial | Qwen3.6 `:8004` | call 1 raw lost; call 2 hash undeclared | run-model CLI | interface | medium | repair receipt |
| `PARTRIDGE_REPLAY` | protected `09e89d9...`, parent `daefcbe...`; V2 runners | pinned commits | source/tests/variants previously run | protected+local | Python/pytest | MIT; six objects not population | V2 migration runners | task source | medium-high | more families |
| `NTRIP_MIGRATION_CASE` | `research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/` | qualification v2 | commit/env/provenance reports | available | pinned source/tests | one case; false-positive behavior tests | qualification entry | boundary | medium | retain as failure case |
| `ADAPTIVE_V3_ENV` | `research/adaptive_revalidation_v3/` | v3 | replay/budget receipts | available | authored fixtures | synthetic only | README replay entry | RQ-A baseline | low-medium | real families |
| `MA_CERD_CORRECTIONS` | `research/ma_cerd_independent_v1/CORRECTIONS_20261021.md` | dated correction | membership/set-match checked | available | old results | no independent trace replay | deterministic scripts | boundary | low | no revival without trace |
| `CODEUPDATEARENA_ADAPTER` | `research/codeupdatearena_adapter_v2/` + protected source | adapter v2 | spec/executor/negative reports | protected | Python/repo/tests | synthetic; current arm exhausted | `run_adapter.py` | learning fallback | medium | new action/update only |
| `SCOPE_EXACT_CACHE` | `revision_v4/RESEARCH_SPRINT_RETURN.md`, `revision_v2/THIRD_CONTRIBUTION_SCOPE_REUSE_PROBE.json` | 20 transitions | exact-cache falsifier checked | available | zero-model replay | authored transitions | existing replay | closed | low | new cache-invalidation task |
| `LORA_SMOKE_CHAIN` | `research/stage_e_method_revision_20261009/run_prm_reference_training_smoke.py`, `research/prm_reference_training_smoke_20261010/` | runner SHA `900f17df...` | configs/metrics/audit checked | available; data/model GB10 | Torch/TRL/PEFT/Qwen3-4B | pending non-commercial license; overlapping arms; 8 rows/2 steps | training runner | ALT-L plumbing | medium-high | new data and disjoint arms |
| `OLD_VGMC_Q3_DPO` | `research/vgmc_*.py`, `research/valentine_q3_review_package.py`, `research/dpo_pairs_v0.py` | historical | builders/limits located | replay only | Valentine/Q3 artifacts | conflicting/one-way labels; lineage gaps | offline builders | lessons | high | not direct labels |
| `PRM_SMOKE_REFERENCE` | GB10 `.../sources/prm800k/phase2_test.jsonl` | SHA `6b172efa...aaad` | referenced by smoke config | GB10 protected | JSONL/grader/model | license pending; smoke only | training runner | smoke | high | license before expansion |

Top reuse set: `STALE_400_DEV`, `G2_MEASUREMENT_CONTRACT`,
`G2_FIXED_STATE_RUN`, `G3_EVIDENCE_RUNNER`, `G3_EVIDENCE_RESULTS`,
`ADAPTIVE_V3_ENV`, `LORA_SMOKE_CHAIN`, `PAPER_E_ARTIFACT`.

### Asset Qualification Addendum

- `STALE_400_DEV` is executable for development replay, but its benchmark data
  license is not recorded locally and every current UID panel is exposed. It is
  not ready for release, training claims, or fresh confirmation.
- `MACERD-PUBLIC-ZIP` (`MA_CERD_Gold_Dataset_v1.0.0_ZENODO_FINAL.zip`, SHA-256
  `f0373675...ab62c`) is internally manifest-consistent and is the authoritative
  reusable copy. The extracted `release/` tree fails its validator because
  `README.md` and three documentation files drift; use the ZIP or repair under a
  new version, never silently rewrite frozen originals.
- Partridge is MIT and NtripBrowser is BSD-3-Clause. Partridge includes a
  disclosed pytest compatibility patch in test files; module and patch hashes
  remain run-bound. Both real-migration panels are development/exposed.
- VersiCode has conflicting root/README/ZIP license signals and no qualified
  behavioral oracle; its `eval()` evaluation scripts are not a safe oracle. It
  supports only the existing syntax/API-name ablation until provenance is fixed.
- PyMigBench curation code is reusable, but `TASKS.json` is
  `FROZEN_ZERO_TASKS`: 36 candidates were attempted and 0 retained. There is not
  yet an executable PyMigBench benchmark.
- Qwen3-4B/8B plus PEFT/TRL is reusable infrastructure. Q3, VGMC, DPO and PRM
  labels are not new gold; the local VGMC source corpus is also missing.

## 5. Failure Lessons As Experiment Constraints

| Failure lesson | Evidence | Required constraint |
|---|---|---|
| Fixed No/UNKNOWN/empty can inflate success | G2 contract, V4 controls | Include fixed-No/UNKNOWN/empty/generic-cautious baselines; primary is grounded completion |
| Stale detection is not sufficient state recovery | book case, `09949c3c` | Score invalidation, positive facts, constraints and action use separately |
| Tool call is not result consumption | Partridge counterexample | Bind actual module/result and paired valid target outcomes |
| Safer may mean answering less | G2 E2E distributions | Report risk-coverage and unnecessary refusal at matched coverage |
| Versions/rows are not independent samples | UID reuse, generated STALE | Split by source/family and use paired family differences |
| Relevant evidence, utility and total cost differ | G3 43/400, oracle chars | Report coverage, downstream action, tokens/tools/index/preprocess/latency |
| Cheap controls can erase mechanisms | exact cache, alias-aware static 6/6 | Run strongest transparent and same-budget random controls |
| Oracle is diagnosis, not deployment | G3 oracle, hidden state refs | Separate oracle table; never expose hidden labels |
| Development cannot become retrospective confirmation | STALE used across V3-V5 | Freeze first, then use untouched UID/source clusters |
| Interface failure is not a scientific negative | G3 two failed calls | Qualify schema/canary and preserve failed raw |
| Tests/ledger are not contribution | PRM smoke, governance | Require comparison and independent scientific review |

## 6. Bounded Nearest-Neighbor Comparison

| Neighbor | Covered by prior work | Remaining local question | Required comparison | Reading identity |
|---|---|---|---|---|
| STALE/CUPMem | Generated/expert-edited stale-memory benchmark; structured write-time state adjudication; observed/inferred deltas; propagation-aware search; constrained readout | Which stage loses sufficient current information, and when does recovered information change an action under fixed evidence? | Temporal/contradiction rule or CUPMem-like structured state versus equal-information plain/structured extraction | Full-text deep read in `reading_notes/2026_STALE_2605.06527.md`; not a natural deployment trace |
| Adaptive retrieval/active checking | Selecting additional context/checks under budget | Does KEEP/EXPAND improve downstream action per total cost beyond always/never/random and cheap heuristics? | Same-budget random, always top-5, score-gap/recency/query-coverage, cost-aware candidate | Local Adaptive V3 and G3; exact external implementation must be selected before method claim |
| Data filtering/supervised selection | Filtering examples or steps from observable quality fields | Can checkable feedback teach evidence use without conflicting legacy labels? | No-training, generic SFT, visible simple filter, feedback-filtered supervision | PRM smoke proves plumbing only, not filter efficacy |

Literature coverage is a design constraint, not a novelty certificate. STALE has
full-text coverage; adaptive retrieval and filtering comparisons must be narrowed
to a selected implementation before any novelty statement.

## 7. Experiment Card 1: State Information-Loss Localization

Status: `READY_FOR_DEVELOPMENT_START / CONFIRMATION_INPUT_LOCAL_GAP`.

**Question.** With identical legal evidence, where does RQ-U fail: invalidating
old state, omitting sufficient current facts/constraints, or using a correct
state in the action?

**Actual assets and paths.** `STALE_400_DEV`;
`research/publication_thesis_goals_v1/revision_v5/G2_EVALUATION_CONTRACT.md`;
`g2_fixed_state_transfer_fixed_slots_20261023_v5/`;
`G2_E2E_TOP5_INDEPENDENT_REVIEW.*`. Hidden references are evaluator-only.

**Environment/input.** GB10, fixed Qwen3.6 configuration, one BM25 top-5
package per UID under a frozen tokenizer/index. Actor input excludes `M_old`,
`M_new`, `explanation`, and `relevant_session_index`.

**Reference/data identity.** The hidden current-state reference supports a
researcher-side sufficient-fact set and constraint checklist, not one gold
action. Multiple valid actions are allowed. The 400 rows and prior 8/16 UIDs are
`DEVELOPMENT_EXPOSED`; confirmation needs untouched UIDs/source clusters.

**Arms.**

1. `SUFFICIENT_FACTS`: minimal sufficient facts/constraints from the same legal evidence.
2. `EXTRACTED_PLAIN`: actual fixed actor extraction in plain slots.
3. `EXTRACTED_STRUCTURED`: identical facts/constraints in structured slots.
4. `REASONABLE_ABSTENTION`: asks for the one missing constraint when insufficient; otherwise answers.

**Strong baseline/competition.** Temporal-contradiction rule and
reasonable-abstention policy. Plain versus structured is interpretable only
after sufficient versus actually extracted facts is isolated.

**Metrics.** Primary: safe grounded action completion. Secondary: invalidation,
positive-fact/constraint recall, constraint violations, unnecessary refusal,
reasonable clarification, coverage, tokens and latency. Pair by UID and cluster
by source/type.

**Resources.** 8-16 UIDs x 4 arms x one recovery and one action, no automatic
retry: 64-128 accounting attempts, capped at 128. Calibrated judge calls are
additional and not gold.

**First command.**

```powershell
venv\Scripts\python.exe -m pytest -q `
  research/publication_thesis_goals_v1/revision_v5/test_g2_fixed_state_transfer_probe_v5.py `
  research/publication_thesis_goals_v1/revision_v5/test_g2_evaluation_contract.py
```

Then create a new versioned equal-information runner; do not modify V5 outputs.

**Stop condition.** If sufficient facts do not improve action over extracted
facts, the remaining bottleneck is downstream use. If sufficient facts improve
but representations tie, stop representation work. If reasonable abstention
matches at equal coverage, stop the state-card mechanism.

## 8. Experiment Card 2: Effective Evidence Expansion And Total Cost

Status: `READY_FOR_DEVELOPMENT_START_AFTER_INTERFACE_CONTRACT`.

**Question.** Can the system predict when ranks 4-5 will change a real decision,
and reduce total cost without hiding task failure?

**Actual assets and paths.** `STALE_400_DEV`;
`research/publication_thesis_goals_v1/revision_v5/G3_incremental_evidence_probe.py`;
`G3_OFFLINE_RESULTS_V1.json`; `G3_MODEL_*`;
`research/adaptive_revalidation_v3/`.

**Environment/input.** GB10 protected 400-row JSON; fixed BM25 retaining
stopwords and session/time prefixes; top-3 initial and ranks 4-5 candidate. The
candidate interface must return `KEEP`, `EXPAND`, or `ABSTAIN` plus a valid
reason code and cannot see hidden labels.

**Reference/data identity.** Hidden `relevant_session_index` measures old/new
pair visibility. A fixed reader separately measures factual/action change.
Neither is a gold plan. All 400 rows and the earlier 8 UIDs are development;
confirmation uses untouched UIDs and preferably another source/release.

**Arms.**

1. `KEEP_TOP3`.
2. `ALWAYS_EXPAND_TOP5`.
3. `SAME_BUDGET_RANDOM`, matching action count and incremental cost distribution.
4. `CHEAP_STRONG`: score-gap, query coverage, recency/update cue or fixed-threshold logistic/rule.
5. `CANDIDATE`: valid cost-aware KEEP/EXPAND/ABSTAIN.
6. `ORACLE_GAIN`: diagnostic only.

**Strong baseline/competition.** Same-budget random is mandatory. Depth-2
`5/43` is not a win: random expectation is 4.3 and exact `P(X>=5)=0.434752`.

**Metrics.** Primary: paired downstream decision utility at matched total cost.
Secondary: old/new coverage, useful-expansion precision/recall, factual/action
change, false change, abstention, input/output tokens, tools, index/preprocess
time, selector latency and wall clock. The 357 no-label-gain rows have unmeasured
utility, not zero information.

**Resources.** First 64 UIDs x five non-oracle arms with fixed reader. Rules use
zero selector calls; candidate canary precedes up to 64 calls. Estimate 64-128
attempts and under 0.8M tokens; judge is additional.

**First command.**

```powershell
ssh jinrong-dev "cd wzh/projects/agents_final_tech && ./venv/bin/python research/publication_thesis_goals_v1/revision_v5/G3_incremental_evidence_probe.py offline --data /home/testuser/wzh/protected_research_20261021_v1/stale_probe_20261023/T1_T2_400_FULL.json --protocol research/publication_thesis_goals_v1/revision_v5/G3_PROTOCOL_V1.json --output research/research_baseline_governance_20261023/dev_check_g3_offline.json"
```

This command is deterministic qualification, not a new scientific result. The
next experiment must freeze a new output path and contract.

**Stop condition.** Stop if the candidate fails to beat same-budget random and
the strongest cheap baseline on downstream gain at equal cost. Coverage-only
gain is retrieval value. Gain from more calls/tokens is a resource effect.

## 9. Experiment Card 3: Small-Model Learning Alternative

Status: `READY_FOR_DATA_QUALIFICATION_AND_DRY_RUN / TRAINING_NOT_YET_STARTABLE`.

**Question.** On a new independently checkable task, can a small model learn a
conditional evidence-use/check-selection rule that survives partial condition
change better than generic supervision?

**Proposed task.** A new public/reconstructable document or update family with a
minimal action and executable checker: select the next evidence check, then
perform a constrained calculation/repair. Preferred candidate: a new
CodeUpdateArena-style action/update family or public document-state task. Do not
reuse the exhausted prose-update arm.

**Actual assets/paths.** `LORA_SMOKE_CHAIN`;
`research/codeupdatearena_adapter_v2/`; Partridge V2 replay; G2 contract;
Adaptive V3 replay.

**Environment/input.** GB10, Qwen3-4B, LoRA r=8 or separately frozen small
configuration; pinned model/tokenizer hashes; source/task-family split;
executable checker. Isolated outputs; no production Memory write.

**Reference/data identity.** Supervision comes from executed checker outcomes
and visible evidence relations. Teacher labels are proposals until independently
checked. A new task/source is required; old STALE analyses and exhausted tasks
cannot be renamed as fresh train/confirmation data.

**Arms.**

1. `NO_TRAINING`.
2. `GENERIC_SUPERVISION`.
3. `SIMPLE_FILTER`, using visible non-oracle fields only.
4. `CANDIDATE_SUPERVISION`, checker-verified conditional examples with true/false/unknown guards.

**Why legacy labels cannot be reused.** Q3 `51/58/37` is exploratory with
visibility/independence gaps. The 60 DPO pairs use synthetic reconstruction and
have single/conflicting directions. VGMC lacks native same-sample
trajectory/checkpoint/correctness bridges. They provide replay and failure
constraints, not direct training labels.

**Metrics.** Primary: executable success on unseen families. Secondary: guard
precision/recall and unknown calibration, false transfer under changed
conditions, regression on unchanged conditions, check cost, contract validity,
and paired base-versus-trained difference. Inspect condition learning versus
answer templates.

**Resources.** Data qualification 32-64 cases; two 2-step smoke arms only after
license/data checks. Meaningful first comparison: at most three seeds with steps
fixed before confirmation; report GPU time, tokens, adapter and inference cost.
The historical 8-row/2-step run is not a scientific training budget.

**First command.**

```powershell
venv\Scripts\python.exe research/validate_stage_d_training_readiness.py --help
```

This validates the existing entry point. After new task qualification, create a
versioned config and run the same validator with `--config`; keep
`training_execution_authorized=false` in this governance phase. The PRM runner
is an engineering reference, not the new task runner.

**Stop condition.** Stop if supervision is not independently checkable, lineage
isolation fails, or no-training/cheap-filter is sufficient. Stop the learning
claim if new-family gains vanish or are template copying.

## 10. Recommended Order For The Next One To Two Weeks

1. **Main attack: Card 1.** It explains current G2 without presuming a Memory
   architecture and separates recovery from action use.
2. **Independent candidate: Card 2.** Repair KEEP/EXPAND and run same-budget
   random with a fixed reader. Its decision is whether to acquire evidence.
3. **Learning fallback: Card 3 after data qualification.** Train only when a new
   executable task has real headroom, checker-backed labels and unseen families.

Paper E continues in parallel through the existing handoff. If Card 1 collapses
to retrieval-only effects and Card 2 has no downstream utility, merge the
negative evidence into RQ-U/RQ-A limits and find a new task rather than splitting
one pipeline into two thesis contributions.

