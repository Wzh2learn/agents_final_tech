# Stage R / RQ4 static protocol v1（2026-10-05）

> Status: `STATIC_PROTOCOL_READY_NOT_RUN` | `Phase 2 NOT_RUN` | `RQ4 NOT_CLOSED`
> Scope: protocol and analysis plan only; no rule replay, no model calls, no new data

## 1. Stage R arms

The seven arms remain fixed:

1. `no-gate`
2. `gain-only`
3. `collateral-only`
4. `confidence-only`
5. `fixed-dual`
6. `independent-gate-validation`
7. `rollback-versioning`

The primary confirmatory contrast is the **strongest preregistered baseline** versus **independent-gate-validation + rollback-versioning**. The other five arms are mechanism ablations and must not be mixed into the same confirmatory family.

## 2. Candidate order and state isolation

- One candidate multiset is consumed by every arm.
- The primary order is the hash-bound order in the frozen candidate manifest.
- Mandatory order sensitivity: `original`, `reverse`, and seeded permutations for `42`, `43`, `44`.
- A permutation may reorder candidates but may not add, remove, duplicate, or edit candidates.
- Each arm has an independent rule state. `gain`, `collateral`, and `gate_delta` are recomputed from that arm's current state after every decision.
- A rule id, source UID, candidate id, and accepted/retained status must be unique within an arm and never copied as a cross-arm counterfactual score.

## 3. Gate and rollback rules

- `gain-only`, `collateral-only`, `confidence-only`, and `fixed-dual` retain their named gate semantics.
- `independent-gate-validation` accepts or rejects against the frozen independent validation contract.
- `rollback-versioning` maintains a best gate-validation snapshot. Rollback occurs only when the predeclared validation budget is exceeded or a safety stop fires.
- `rollback_budget`, validation query budget, and candidate risk cap remain `PENDING_USER_APPROVAL`; no default is inferred.
- A rollback restores the complete rule snapshot and retained-rule set. Partial state restoration is invalid.

## 4. Required metrics

Report each arm and each order/seed sensitivity:

- UID-any-harm rate and one-sided upper bound;
- valid-rule retention;
- rule-level harmful acceptance as a descriptive rate only;
- validation queries and rollbacks;
- time/step to first harmful consolidation;
- maximum validation-set drawdown;
- retained-valid / retained-harmful rules;
- cumulative cost and worst family.

## 5. Stop conditions

Stop and preserve null/adverse results when:

- any candidate order is not the exact frozen multiset;
- rule state diverges from the recomputed source gain/collateral state;
- a sealed or gate-validation result is reused to tune a candidate or threshold;
- rollback loses a complete snapshot;
- UID-any-harm or validation drawdown crosses its predeclared stop limit;
- resource, process, log, or output limits are exceeded;
- a model or network call is attempted outside the approved window.

## 6. RQ4 C0/C1/C2/C3

| Group | Actor | Persistence |
|---|---|---|
| C0 | teacher | no persistence |
| C1 | teacher | strong gate + rollback |
| C2 | student | no persistence |
| C3 | student | strong gate + rollback |

All four groups use the same candidate stream, evaluation time, quality/risk/cost definitions, and independent state rules. The primary contrasts are:

- teacher versus student at fixed persistence;
- no persistence versus strong gate + rollback at fixed actor.

RQ4 is not closed unless RQ2 and RQ3 have independent evidence. Evaluation-only is not a runtime arm equivalent to distillation-only.

## 7. Prohibited wording

Do not write:

- `safe persistent improvement` before the formal Phase 2 state trajectory and power gates pass;
- `RQ3 confirmed` from mechanism-only rejection evidence;
- `RQ4 closed` from C0–C3 planning or one-sided results;
- a rule-level harmful rate as a UID-level safety claim;
- cost proxy as measured latency or GPU cost;
- sealed-test numbers as development tuning evidence.

## 8. Current boundary

`DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, and `Phase 2 NOT_RUN` remain. This protocol does not authorize replay, training, model dispatch, or external release.

## 9. Initial Phase 2 budget (approved values, not yet frozen for formal run)

- `candidate_risk_cap = 0.10`.
- `rollback_budget = accepted_candidates * 0.05`, bounded to at least 1 and at most 10 rollbacks.
- `validation_query_budget = candidate_count * 1.10`; the extra 10% is a preregistered reserve.
- `validation_drawdown_stop = 0.05`.
- Primary order is the frozen candidate manifest. Sensitivity orders are original, reverse, and seed 42/43/44 permutations.

Pilot-scale adjustment is allowed for rollback budget and validation query budget before formal Phase 2. Neither these values nor `candidate_risk_cap` may change after harmful/retention outcomes are observed. Every adjustment requires config, hash, reason and effective time before execution.