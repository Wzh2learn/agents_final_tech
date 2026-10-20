# Decision-Space Autopsy

Status: `COMPLETE_NO_MODEL_REQUESTS`

## Question

Why did the old fixed-calculation panel and Candidate B both reach a 16/16 development ceiling?

## Method

This is a deterministic task/reference analysis, not a model experiment. It compares:

- the 16 future-test tasks used by the first B0 panel;
- the 16 development tasks used by Candidate B B0;
- all unselected eligible TAT-QA reserve source clusters.

The analysis reports prompt disclosure and effective choice-set size. It does not call a formal entropy model.

## Results

| panel | tasks | row supplied | periods supplied | operation supplied | unit/scale supplied | mean row x period-column choices | mean row x period-pair choices | single choice after prompt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| old fixed calculation | 16 | 16 | 16 | 16 | 16 | 2.000 | 1.000 | 16/16 |
| Candidate B development | 16 | 16 | 16 | 16 | 16 | 19.000 | 11.375 | 16/16 |

Candidate B increased the raw table choice set but did not increase the post-prompt decision space:

- the question names the target row verbatim;
- both requested periods appear verbatim;
- the instruction requires the signed change;
- the unit and scale are uniquely inferable from the table header.

The actor therefore performs exact label matching and one calculation. Historical experience has no material action left to change.

## Natural ambiguity scan

After excluding the 16 Candidate B development/future clusters and all old designated roles, 26 eligible reserve clusters remain.

- Same numeric value in different row/period roles: 6 cases in 5 clusters.
- Same signed delta in different row/period-pair roles: 4 cases in 4 clusters.
- Union of collision clusters: 5.

The available TAT-QA reserve pool is therefore insufficient for an 8-cluster future-validation panel. It can support a bounded development study only.

## Interpretation

`FACT`: both panels collapse to one effective choice after prompt disclosure.

`INFERENCE`: repeated ceiling results are caused by low decision-space, not evidence that experience is universally useless.

`DECISION`: stop the one-table/two-period signed-difference task family. Do not add arbitrary noise or lower model capability to manufacture errors.

## Next route

Design one natural role-binding task around same-number/same-delta citation swaps:

- numeric values are held fixed;
- the disputed action is whether the cited row/period/unit role supports the requested claim;
- correct behavior includes `SUPPORTED`, `WRONG_ROLE`, `UNKNOWN` and clarification/abstention;
- current calculation histories are insufficient because they contain no wrong-role correction.

The TAT-QA reserve pool can support development only. Independent validation requires either three additional eligible source clusters or a separately approved source qualification.
