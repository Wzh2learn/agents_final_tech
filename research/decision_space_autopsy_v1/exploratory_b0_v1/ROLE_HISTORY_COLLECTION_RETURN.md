# Role-History Collection Return

> Evidence record only. Current research entry: `docs/research/README.md`.

Status: `PARTIAL_COLLECTION_COMPLETE / NO_ROLE_CORRECTION / STOP_H_NEGATIVE`

## Actual execution

- Fixed runtime identity and existing GB10 model service were used.
- One initial request attempt failed before model response because the local
  port forward was absent. It is preserved as a `CRASH` request record and is
  conservatively counted as one request with zero model tokens.
- The SSH forward was then restored without starting or changing the model
  service. Remote and local `/health` and `/v1/models` both returned HTTP 200.
- The no-replay recovery excluded the complete `cluster_0424` pair and preserved
  the same immutable raw root.
- Twenty model requests completed with raw request/response pairs and immutable
  completion markers.
- The request cap was reached before the sixth task began. No retry or sample
  replacement was issued.

## Complete experience results

Five two-attempt experiences are complete:

| task | cluster | first result | second result | action change |
|---|---|---|---|---|
| `NR_development_0923_N2` | `cluster_0923` | SUCCESS / WRONG_ROLE | SUCCESS / WRONG_ROLE | none |
| `NR_development_0923_P1` | `cluster_0923` | SUCCESS / SUPPORTED | SUCCESS / SUPPORTED | none |
| `NR_development_1498_N2` | `cluster_1498` | SUCCESS / WRONG_ROLE | SUCCESS / WRONG_ROLE | none |
| `NR_development_1498_P1` | `cluster_1498` | SUCCESS / SUPPORTED | SUCCESS / SUPPORTED | none |
| `NR_development_1981_N2` | `cluster_1981` | SUCCESS / WRONG_ROLE | SUCCESS / WRONG_ROLE | none |

All five had valid plans, successful tool execution, numeric/reference agreement
and answer/tool-return consistency. First-attempt non-success is 0; corrections
are 0; role-decision changes are 0.

## Budget accounting

- Before this collection: 292 requests and 310,144 accounting tokens.
- Connection-refused attempt: 1 request, 0 model tokens.
- Recovery model calls: 20 requests, 13,942 accounting tokens.
- Current total: **313/316 requests** and **324,086/2,750,000 tokens**.
- Remaining: 3 requests and 2,425,914 tokens. The remaining request budget is
  insufficient for one complete plan/consume two-attempt trajectory.

The earlier 24-request plan incorrectly treated one two-attempt task as two
requests. Each attempt contains a plan request and a consume request, so a task
costs four requests. The corrected bounded formula is:

```text
requests = tasks * attempts_per_task * 2
```

## Scientific decision

The gate for negative episodic memory is not met. The newly collected material
contains no wrong-role failure followed by role-specific correction, and the
five complete trajectories show no behavioral change after feedback.

Stop `H-negative/random` on the current task family as
`NOT_IDENTIFIABLE_WITH_REAL_HISTORY`. This is a boundary result for the fixed
model, prompts and visible role-binding panel. It is not evidence that real
experience is universally useless.

Further collection on the same visible role task is low-value: the observed
trajectory success is 5/5 and there is no remaining request budget for a full
additional task. Do not weaken the model, alter the output protocol, select
tasks after failures, or manufacture negative histories.

## Evidence locations

- Immutable raw root:
  `D:/AIRcommend/JinRongAgents/agents_final_tech/research/decision_space_autopsy_v1/exploratory_b0_v1/raw/ROLE-HISTORY-V1-20261019`
- Partial result:
  `D:/AIRcommend/JinRongAgents/agents_final_tech/research/decision_space_autopsy_v1/exploratory_b0_v1/raw/ROLE-HISTORY-V1-20261019/HISTORY_PARTIAL_RESULT.json`
- Recovery bundle:
  `D:/AIRcommend/JinRongAgents/agents_final_tech/research/decision_space_autopsy_v1/exploratory_b0_v1/ROLE_HISTORY_RECOVERY_BUNDLE_V1.json`
- Failure-history qualification:
  `D:/AIRcommend/JinRongAgents/agents_final_tech/research/decision_space_autopsy_v1/exploratory_b0_v1/FAILURE_HISTORY_QUALIFICATION_AUDIT.md`
