# Paper E Addendum Draft: Developmental Verification Checks for Financial Table QA

> Draft only. This text does not modify the frozen Paper E manuscript and is not submission-ready evidence of scientific validity.

## A.1 Scope and design

We conducted two bounded developmental checks with the same local Qwen3.6-35B-A3B model in three roles: an actor that answers a financial table question, B that verifies the answer together with its evidence locations, and C that independently solves the task and compares only with the final answer. The two panels answer different questions and are not pooled.

TQ-4 is a calibration panel containing four new tasks from an older development pool with controlled header perturbations and twelve manually constructed answer/evidence candidates. TQ-5 is a source-separation developmental panel containing one original task from each of twelve table UIDs excluded from the recorded 221-table development/test union. TQ-5 is table-disjoint only; report-level independence and training-data independence were not established.

Before either run, the model endpoint, parameters, prompts, materials, scoring rules, schedule, and budgets were frozen. TQ-5 additionally used a pre-run immutable snapshot containing the exact config, runner, scorer, templates, and analyzer. Formal execution and analysis entered through a hash-guarded entrypoint. Raw prompts, responses, request ledgers, receipts, and manifests were retained.

## A.2 Measures

Four dimensions were kept separate:

1. answer/reference matching under the frozen numeric scorer;
2. mechanical legality of evidence locations;
3. citation support, which was not separately adjudicated and is reported as `NOT_ASSESSED`;
4. model verification decisions (`accept`, `alarm`, `abstain`, or `invalid` for parse failure).

Machine output validity was counted independently of HTTP success. A request could be HTTP 200 yet produce invalid JSON. The unit of analysis was the task. TQ-4 contains repeated C stimuli for its constructed candidate pairs; TQ-5 contains no repeated stimuli.

## A.3 Results

### TQ-4 calibration

TQ-4 completed 36 requests with zero retries and 40,205 settled tokens. Across all roles, 35/36 outputs were valid. B had 15/16 valid decisions: 4/4 in the natural-task portion and 11/12 in the constructed-candidate portion. The four natural tasks matched their frozen references and all four evidence sets were mechanically legal. B and C each accepted three and alarmed on one.

For the constructed candidates, the B/C decision matrix was:

| construction | B | C |
|---|---|---|
| correct + legal | accept 3 | accept 2, abstain 1 |
| correct + illegal | alarm 2, invalid 1 | accept 2, abstain 1 |
| incorrect + legal | alarm 2, accept 1 | alarm 1, accept 1, abstain 1 |
| incorrect + illegal | alarm 3 | alarm 1, accept 1, abstain 1 |

One B response failed strict JSON parsing and remains `invalid`. The N1 event shows semantic disagreement between reference matching and both checker alarms, but it does not establish that the reference is wrong or the actor correct. Q03-C3/C4 retain their original construction labels and outcomes, although the direction of the difference operation is semantically ambiguous; they are not counted as confirmed shared misses.

### TQ-5 source-separation developmental panel

TQ-5 completed one run (`20261017T072340Z_5d8942bd`) with 36 requests, zero retries, and 44,867 settled tokens. All 12 actor outputs parsed, but the frozen scorer produced 7 MATCH and 5 NO_MATCH. Evidence was mechanically legal for 11/12 tasks. B produced 10 accept, 1 alarm, and 1 abstain. C produced 9 accept and 3 `invalid` outputs.

| layer | frozen MATCH | evidence legal | B accept / alarm / abstain | C accept / invalid |
|---|---:|---:|---|---|
| difference | 3/4 | 4/4 | 4 / 0 / 0 | 4 / 0 |
| ratio | 2/4 | 3/4 | 2 / 1 / 1 | 2 / 2 |
| percentage change | 2/4 | 4/4 | 4 / 0 / 0 | 3 / 1 |
| total | 7/12 | 11/12 | 10 / 1 / 1 | 9 / 3 |

The five frozen NO_MATCH rows are not treated as five proven errors. T01 uses standard accounting parentheses for a negative point change that the numeric parser reads as positive. T07 asks for total sales while its official derivation uses an affiliate-sales row as denominator, leaving the comparison `UNSCORABLE`. T08 retains reference uncertainty around the phrase "all years" and disagrees across B/C. T10 and T12 round 2.81% and 5.67% to 3% and 5.7%; the questions do not specify precision, so these are frozen-tolerance mismatches rather than independently established semantic errors.

## A.4 Interpretation

The experiments show that financial-table verification requires separate accounting for source-reference quality, numerical presentation conventions, precision policy, evidence-location legality, strict output validity, and checker decisions. A single accept/reject or match/no-match label obscures these failure sources. In particular, B and C receive different evidence surfaces, and their decisions cannot be interpreted as independent human judgments or as citation-support labels.

The results do not establish that C outperforms B, that the checkers share a general blind spot, or that any official reference is invalid. They also do not estimate a confirmatory error rate. The panels are developmental, TQ-5 is only table-disjoint, and all scientific-gold fields remain `NOT_ESTABLISHED`.

## A.5 Limitations and reproducibility

- TQ-4 lacks the exact run-time config snapshot; its behavior is reconstructable from raw prompts/responses and ledgers, but the config hash gap remains.
- TQ-5 was executed from a hash-enforced snapshot and its run manifest embeds all eight execution-file hashes.
- C strict JSON failures were preserved as `invalid`; prose was not mined for decisions and no retry was made.
- Citation support was not assessed separately.
- The corpus fetch receipt does not resolve the upstream tarball commit.
- Total chain use was 72 planned requests, zero retries, and 85,072 settled tokens. TQ-4 and TQ-5 budgets remained separate.

Recommended disposition: retain this text as a methods/limitations addendum only and keep `NO_PROMOTION` for empirical claims until independent human semantic gold and an authorized confirmatory design are available.
