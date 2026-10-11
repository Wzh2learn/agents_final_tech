# FinQA Causal-Exposure Preregistration Proposal v1

> Status: `PROPOSAL_FROZEN_NOT_EXECUTED` | Task: `finqa-causal-exposure-design-a-20261010`
> Feasibility: `EXECUTOR_FEASIBILITY_CONDITIONAL` | Execution authorization: `NO`
> Scope: design and frozen proposal only | Window: zero model/API/database/training calls and no formal experiment
> Old result preserved exactly: `FAILED TRANSFER DUE TO MEASUREMENT-OBJECT MISMATCH`

## Mode and completion boundary

**Mode:** `inquiry-methods` with `first-principles` as the primary method and `minimal-experiment` as the secondary method used only to specify future validation tests. The loaded inquiry references are `references/problem-solving.md`, `references/decision.md`, and `assets/output-contracts.md`. Additional proposal skills loaded are `research-driven-design` and `structured-output`.

**Boundary:** this document is a reviewable proposal, not a human execution decision, execution authorization, experiment, or result. No causal-exposure scorer output, `V`, `D`, `O`, eligibility outcome, clean-replay outcome, or estimand was produced.

## Frozen scientific question

When a controlled FinQA perturbation is allowed to causally propagate through program execution into the fields consumed by the frozen detection rule, what is the relationship between checkpoint visibility and protocol detection?

No direction for `D` is assumed. The proposal does not target or optimize a non-degenerate `VxD` distribution.

## Evidence boundary

### Sources read

1. The task contract `research/loop_a_finqa_causal_exposure_design_contract.md`.
2. The frozen statistical plan `research/finqa_v2_20261010/FINQA_V2_ANALYSIS_PLAN.md`, especially the unchanged `V` and `D` definitions at lines 43–44.
3. The independent observation scorer `research/finqa_independent_observation_scorer_v2.py`, which defines `step_result_consistency` and `answer_consistency` from paired clean/mutant fields.
4. FinQA structure evidence `docs/datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md`.
5. The reconstructed step scorer and its pre-registration/results `research/finqa_step_checkpoint_scorer.py`, `docs/experiments/2026-09-25_step_checkpoint_scorer_preregistration_v2.md`, and `docs/experiments/2026-09-25_step_checkpoint_score_v2_results.md`.
6. Existing feasibility artifacts `docs/research/finqa_v2_overlap_feasibility_v1.md` and `docs/research/finqa_v2_causal_join_audit_v1.md`.
7. Approved public source identity evidence `docs/experiments/2026-09-25_source_go_p1p2_staging.md` and the two staged FinQA JSON files.

### Checks run

- Read-only source hashes were re-verified: `finqa/train.json` is `49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6`; `finqa/dev.json` is `a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51`.
- A static schema/dependency rescan (`THIS_RE_VERIFICATION`) counted 7,134 records, 10,960 steps, 2,894 multi-step records, 65 raw `op` tokens, 3,818 `#k` references, zero forward references, and zero out-of-range references.
- A static token-form scan counted 15,840 numeric literals, 324 percent literals, 1,464 constants, 3,818 step references, 238 `none`, and 236 free-text arguments. It counted 6,841 numeric, 3,980 percent, 132 boolean, and 7 other step results.
- Existing source hashes and proposal source hashes were recorded in the machine-readable ledger.

### Checks not run

- No clean replay over the mother pool.
- No P or N mutation execution.
- No `V`, `D`, or `O` scoring.
- No model, API, endpoint, database, training, download, or production-service call.
- No modification of frozen FinQA v2 artifacts, split, sample IDs, scorer semantics, thresholds, metrics, results, or Paper E.

## First-principles findings

### Confirmed facts

1. The frozen detection inputs are unchanged. `V = 1` iff at least one of the five observation fields is `1`; `D = 1` iff `step_result_consistency == 1` or `answer_consistency == 1` (`FINQA_V2_ANALYSIS_PLAN.md:43-44`).
2. The independent scorer sets `step_result_consistency` from any paired `res` difference and `answer_consistency` from paired terminal-answer difference (`research/finqa_independent_observation_scorer_v2.py:117-121`). Thus propagated executor outputs can enter `D` without changing the detection rule.
3. The source contains 7,134 records and 2,894 multi-step records. The structure artifact also records 10,960 steps, step keys `(op,arg1,arg2,res)`, and terminal `exe_ans` types `float=7000`, `yes=80`, `no=54`.
4. The reconstructed candidate executor supports ten normalized families and a documented argument grammar, but the official FinQA operator implementation is not among the approved staged files.
5. The earlier reconstructed step-reexecution line stopped at its pre-registered threshold: percent-form fidelity was `44/1478` and `330/1478` under the two readings, and numeric-form mismatch remained `518/3096`. The result document states that step re-execution on that source is not identifiable from public metadata alone.
6. Existing overlap and join counts are feasibility counts only. They are not causal-exposure eligibility, `V`, `D`, or primary-scientific outcomes.

### Inferences

1. `E` is not causally exposed to `D` under a fixed gold-program/argument path: evidence may change `evidence_required_hit`, but program arguments, execution, `res`, terminal answer, and therefore the two `D` inputs remain fixed.
2. `P` and `N` are candidate causal exposures only when an admitted deterministic executor recomputes the target result, every dependent downstream result, and the terminal answer. Causal exposure does not imply `D=1`; absorption, unchanged rendering, or an unsupported path remains possible and must be reported through the pre-registered counts.
3. Full P/N executor feasibility is conditional because the official arithmetic/serialization contract and an all-record exact clean replay are absent from existing evidence.

### Value judgments

1. Controls are diagnostic infrastructure and must never enter primary estimands.
2. Fail-closed exclusion is preferable to inventing missing FinQA semantics.
3. The proposal is ready for Loop C challenge, not for execution.

### Unverified assumptions

1. A future authority packet can supply official operator code or an equivalently reviewed execution contract.
2. A future implementation can enforce exact clean replay and deterministic propagation without manual `res` or `answer` writes.
3. The later outcome-blind eligibility procedure can produce a unique, split-safe report-cluster mapping for the selected records.

## E/P/N causal classification

| Family | Injection | Downstream computation | Classification before outcomes |
|---|---|---|---|
| `E` | evidence block/representation mutation | fixed gold program and arguments; no P/N recomputation path | `NOT_CAUSALLY_EXPOSED_TO_D`; visibility-only or instrumentation control |
| `P` | legal operator mutation | executor recomputes target `res`, all `#k` descendants, and terminal answer | `CANDIDATE_CAUSALLY_EXPOSED_TO_D_CONDITIONAL_ON_REPLAY` |
| `N` | legal numeric-literal or argument-reference mutation | executor recomputes target `res`, all `#k` descendants, and terminal answer | `CANDIDATE_CAUSALLY_EXPOSED_TO_D_CONDITIONAL_ON_REPLAY` |

`E` is not placed in the primary `D` analysis. A separately specified deterministic evidence-to-argument extraction stage would be a different pipeline and would require a new reviewed contract; none is part of this proposal.

### Required explicit graph

```text
E: evidence mutation -> fixed gold-program/argument path -> unchanged res -> unchanged answer -> unchanged D input
P: operator mutation -> executor recomputes target/downstream res -> executor derives answer -> D input
N: argument mutation -> executor recomputes target/downstream res -> executor derives answer -> D input
```

The canonical causal path required by the contract is:

```text
injection target -> downstream computation -> res -> answer -> D input
```

For controls B and C, the graph is explicitly non-scientific: B changes an upstream observation field; C directly perturbs `res` or `answer` solely to prove detector reachability.

## Program re-execution feasibility audit

### Existing candidate semantics, not official semantics

`research/finqa_step_checkpoint_scorer.py:103-159` currently implements this candidate grammar:

| Input/operation | Candidate rule |
|---|---|
| numeric literal | finite `Decimal` |
| percent literal | mantissa divided by `100` |
| `const_d` / `const_md` | integer `d` or `-d` |
| `#k` | result of prior step `k`; percent result consumed as mantissa/100 |
| `none`, free text | unresolved; never guessed or set to zero |
| `add` / `sum` | `a1 + a2` |
| `minus` | `a1 - a2` |
| `multiply` | `a1 * a2` |
| `divide` | `a1 / a2` at precision 50; zero divisor unresolved |
| `average` | `(a1 + a2) / 2` at precision 50 |
| `max` / `min` | numeric maximum / minimum |
| `exp` | `a1 ** a2`; non-finite or invalid results unresolved |
| `compare_larger` | tie unresolved; otherwise `yes` iff `a1 > a2`, else `no` |

The same implementation treats unknown families, unresolvable arguments, malformed results, non-numeric result forms, and undefined operations as `UNEVALUABLE`. Its `1e-9` numeric comparison tolerance is a historical scorer rule; it does not define the future exact clean-replay gate.

### Why feasibility is conditional

1. The staged source contains only `train.json` and `dev.json`; the approved staging does not contain official FinQA execution code.
2. The prior reconstructed line triggered its own stop condition and did not establish percent/variant/rounding semantics.
3. Numeric-form mismatch also remained unexplained, so percent handling alone is not the missing contract.
4. Terminal-answer derivation from the final program step, including percent, boolean, and seven other result forms, is not specified by an admitted executor.
5. Exact serialization needed for “every `res` and terminal answer exactly reproduced” is not frozen.
6. Legal same-arity `P` replacement sets and type-preserving `N` mutation sets are not frozen.

Therefore the required status is `EXECUTOR_FEASIBILITY_CONDITIONAL`.

### Missing contract

The following must be supplied and hash-bound before P/N execution can be admitted:

1. Official or independently reviewed raw-operator semantics for all 65 raw tokens and family/variant/position encoding.
2. Exact arithmetic, rounding, percent rendering, precision, and comparison rules.
3. Complete argument grammar, including numeric literals, percent literals, constants, `#k`, `none`, and free text.
4. Deterministic downstream recomputation and terminal-answer derivation for every result form.
5. Exact serialization/equality rule for clean replay; no post-hoc repair is allowed.
6. Fail-closed error semantics and the fixed exclusion code list.
7. Legal P mutation targets/replacements and N mutation targets/value/reference rules, selected without outcomes.
8. Provenance that only the executor writes `res` and terminal `answer`.
9. All-record exact clean replay and deterministic two-run evidence before mutation admission.
10. An outcome-blind report-cluster uniqueness and split-safety contract.

### Clean replay gate

A record passes only if, under the admitted executor contract:

1. every gold step `res` is reproduced exactly;
2. the terminal `exe_ans` is reproduced exactly;
3. no unsupported or ambiguous construct is encountered;
4. two clean executions are byte-identical;
5. no hand-written or repaired output is present.

Any failure excludes the record with an explicit code before any P/N mutation is constructed. The mother-pool denominator is not reduced silently.

### Propagation gate

A P or N mutation is admitted only when:

1. the mutation target is legal under the frozen mutation grammar;
2. the dependency closure and downstream execution path are known;
3. the executor alone recomputes target and descendant `res` values and terminal answer;
4. a second run is byte-identical;
5. the paired artifacts contain no manual `res` or `answer` edit.

If any condition fails, the case is not a substantive causal-exposure case.

## Outcome-blind eligibility and eligible rate

### Mother pool

`MOTHER_POOL = 7,134` hash-bound FinQA train/dev records. This is the declared denominator and was fixed from source structure before any new `V/D/O` outcome access.

### Eligibility predicate

A record is eligible only if all conditions are true:

1. `len(program_steps) >= 2`;
2. deterministic clean replay reproduces every gold `res` and terminal answer exactly;
3. the planned mutation is a legal `P` or `N` operation;
4. the mutation target and complete downstream execution path are known;
5. report-cluster group is unique and split-safe;
6. the eligibility input contains no `V`, `D`, `O`, correctness, expected effect, result-class, or target-cell information.

### Eligible-rate declaration

```text
causal-exposure eligible rate =
  causal_exposure_eligible_count / 7134
```

Current state:

- `causal_exposure_eligible_count = NOT_ESTIMABLE_PRE_EXECUTION`
- `causal-exposure eligible rate = NOT_ESTIMABLE_PRE_EXECUTION`
- multi-step structural base = `2894/7134`

The eligibility count must be frozen before any `V`, `D`, or `O` computation. Existing P/N overlap counts (`6794` and `6929`) and join counts are not substituted for this predicate.

## Controls

| ID | Role | Intervention | Allowed interpretation |
|---|---|---|---|
| `A_SHAM` | `CONTROL` | unchanged/sham paired artifact | measurement sanity; expected `V=0`, `D=0` |
| `B_V_POSITIVE` | `CONTROL` | visible upstream/evidence-only instrumentation change | visibility instrumentation only; no substantive `D` claim |
| `C_D_POSITIVE` | `CONTROL` | direct `res` or terminal-answer perturbation | proves detector reachability only |
| `D_P_N_CAUSAL` | `PRIMARY` | executor-propagated legal P/N mutation | only population for primary estimands |

Controls must carry distinct IDs, `case_role=CONTROL`, and a separate control report. They are never pooled into primary estimands. Control C may bypass program propagation by design; that does not authorize substantive manual edits.

## Pre-registered estimands only

Primary scientific population: `D_P_N_CAUSAL` only.

1. `V` count and rate.
2. `D` count and rate.
3. `VxD` table counts and cell rates for `(0,0)`, `(0,1)`, `(1,0)`, `(1,1)`.
4. `P(D=1 | V=1)`.
5. `P(D=1 | V=0)` if identifiable; otherwise `NOT_IDENTIFIABLE`.
6. Per-family profiles for `P` and `N`: `V` count/rate, `D` count/rate, and the four-cell `VxD` table.
7. Causal-exposure eligible count and rate over the declared mother pool.
8. Clean-replay validity count/rate and every exclusion count by frozen code.

No additional scientific metric, target cell distribution, threshold search, localization statistic, hierarchy statistic, harmfulness measure, semantic-correctness measure, or result-dependent subgroup is authorized.

## Required future proposal tests

These are specification tests for later implementation; they were not run here.

| Requirement | Future test | Pass condition |
|---|---|---|
| Clean replay exactness | replay each hash-bound record and compare every generated `res` and terminal answer to gold under the frozen serializer | all required outputs exact; any mismatch excluded with code |
| Deterministic P/N propagation | execute each admitted P/N pair twice and compare serialized dependencies/results/answer | two runs byte-identical; downstream recomputed by executor |
| No manual `res`/`answer` editing | deny mutation-manifest writes to result/answer fields; audit provenance and paired-artifact diffs | substantive mutations contain only P/N target fields; executor owns outputs |
| Controls remain separate | assert disjoint control/primary IDs and query primary estimands with `case_role=PRIMARY` only | sham and D-positive controls never enter primary denominator |
| Eligibility is outcome-blind | static input allowlist plus invariance test that changes only synthetic `V/D/O/correctness` fields | eligible IDs and reason codes remain identical |
| Unsupported operations fail closed | unit cases for unknown op, unresolved arg, percent ambiguity, zero divisor, tie, malformed/other result, answer ambiguity | explicit exclusion; no guessed output and no silent pass |

Additional acceptance tests must verify frozen source hashes, split/group uniqueness, zero endpoint calls, no frozen-artifact drift, and zero scientific outputs before execution authorization.

## Stop conditions

Execution remains stopped if any of the following is true:

1. deterministic official/reviewed P/N semantics are unavailable;
2. exact clean replay cannot reproduce all gold outputs;
3. a causal path requires manual `res` or `answer` editing;
4. eligibility can access `V`, `D`, `O`, correctness, or expected effect;
5. controls cannot be separated from substantive cases;
6. the missing executor contract remains incomplete.

Current status: `STOP_CONDITION_ACTIVE_PENDING_LOOP_C_CHALLENGE_AND_EXECUTOR_CONTRACT`.

## Required proposal outputs

1. `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`
2. `research/finqa_causal_exposure_20261010/finqa_causal_exposure_design.json`
3. `research/finqa_causal_exposure_20261010/finqa_causal_exposure_feasibility.json`
4. `research/finqa_causal_exposure_20261010/finqa_causal_exposure_source_ledger.json`
5. `research/finqa_causal_exposure_20261010/FINQA_CAUSAL_EXPOSURE_LATER_EXECUTION_TASK_CARD_NOT_EXECUTED.md`
6. `research/finqa_causal_exposure_20261010/finqa_causal_exposure_proposal_receipt.json`

## Recommendation, conditions, risk, exit, first action

**Recommendation:** submit this frozen conditional proposal to fresh-context Loop C for challenge; do not execute it.

**Conditions:** proceed only after the missing executor contract is supplied, clean replay is exact and deterministic, eligibility is demonstrably outcome-blind, controls are segregated, and a separate execution authority is granted.

**Largest risk:** a reconstructed executor could appear deterministic while using unverified FinQA semantics, making apparent propagation a measurement artifact.

**Exit condition:** stop permanently for this proposal if any stop condition remains unresolved; do not repair `res` or `answer` manually and do not relax clean replay.

**First action:** Loop C should independently audit the `EXECUTOR_FEASIBILITY_CONDITIONAL` classification, the 7,134 denominator, the E/P/N graph, and the proposed fail-closed tests against the source ledger.

