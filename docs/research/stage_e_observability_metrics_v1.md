# Stage E Observability Metrics v1

Status: analysis-only; frozen Stage E values and claim boundaries are unchanged.

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

## 1. Measurement objects

`FACT`: Stage E must keep three objects separate:

1. **Checkpoint visibility** — whether the frozen intermediate representation records a change for a given injection at a stated threshold or absorption rule.
2. **Protocol detection** — whether a frozen decision predicate issues a positive detection.
3. **Operational harmfulness** — whether the D1 operational class is `H`, `HI`, or `E` under the frozen criterion/equivalence paths.

`INFERENCE`: none of these objects substitutes for another. A detection may occur when the named checkpoint is blind because the decision predicates use different information; conversely, visibility does not imply a threshold crossing or a harmful consequence.

## 2. Minimal metric set

| Metric | Unit and denominator | Definition | Primary use |
|---|---:|---|---|
| Micro visibility | injection, `n=118` | `visible_frozen / 118` | headline observable-region rate |
| Micro blindness | injection, `n=118` | `blind / 118` | complement of micro visibility |
| Family visibility | injection within family | `visible_frozen / family_n` | family blind-region profile |
| Macro family visibility | six families | unweighted mean of the six family rates | prevents family size from hiding OCR |
| Threshold visibility | injection, by `gamma` | `visible_by_gamma[gamma] / denominator` | operating-point sensitivity |
| Detection | injection, `n=118` | protocol-positive / 118 | protocol-specific sensitivity |
| Visibility × detection cells | injection, `n=118` | `VD`, `VU`, `BD`, `BU` | construct stress test |
| Conditional detection | injection | `P(D|V)`, `P(D|B)` | asks whether detection changes with visibility |
| Blindness among misses | injection | `P(B|not D)` | identifies what dominates undetected cases |
| Matched-FPR difference | harmful `H∪HI`, `n=111` | flat TPR minus hierarchical TPR after clean calibration | operating-point-valid protocol comparison |

`FACT`: table-level detection remains `95`, injection-level visibility/detection remains `118`, and matched-FPR harmful evaluation remains `111`. These are distinct denominators and are never combined into one partition.

## 3. Formula and uncertainty policy

For an injection record `i`, let `V_i` be `visible_frozen`, and let `D_i^p` be protocol `p`'s frozen detection.

```text
V = sum(V_i)
B = 118 - V
P(D=1 | V=1) = sum(V_i and D_i) / sum(V_i)
P(D=1 | V=0) = sum((1-V_i) and D_i) / sum(1-V_i)
P(V=1 | D=1) = sum(V_i and D_i) / sum(D_i)
P(V=0 | D=0) = sum((1-V_i) and (1-D_i)) / sum(1-D_i)
```

`FACT`: the checked script uses `(uid, col)` as the join key and computes 2,000 table-cluster bootstrap replicates with seed `20260830`. Tables, not injections, are resampled; all injections belonging to a sampled table are retained together.

`INFERENCE`: cluster-aware intervals are descriptive uncertainty for this frozen corpus. They do not turn 118 injections into 118 independent units and do not establish population generalization beyond the corpus.

`VALUE`: for a zero-event family such as OCR-like, report the raw `0/13`, the number of independent table clusters (`11`), a grouped cluster-event exact interval, and the degenerate cluster-bootstrap interval separately. Do not present `[0,0]` bootstrap or a naive Bernoulli interval as population certainty.

## 4. Reporting rules

- `FACT`: report raw numerator/denominator before any percentage.
- `FACT`: report family rates beside micro and macro summaries.
- `FACT`: report threshold-conditioned visibility separately from absorption-based `visible_frozen`.
- `VALUE`: report detection conditional on visibility rather than subtracting `112-96`.
- `VALUE`: keep matched-FPR results on the harmful `111` denominator and raw frozen-threshold results on `118`.
- `UNVERIFIED`: semantic harmfulness-conditional blindness is not identifiable because the operational `H/HI/E` labels partly depend on detection/equivalence paths and the semantic-boundary analysis covers only 28 judged cases with no mixed-language or unit-suffix calls.

## 5. Negative and unavailable results

`FACT`: no exact published precedent was found that defines this project's combined checkpoint-visibility, family-profile, and matched-protocol metric set.

`INFERENCE`: the set is therefore a project-defined meta-evaluation metric battery, constrained by mutation-testing denominator validity, fault-localization separation, measurement meta-evaluation, and NIST TEVV governance—not copied from a single external standard.

`UNVERIFIED`: inter-rater reliability, a second independent implementation, and external-corpus calibration remain absent.

## 6. Reproducibility

- Script: [`quantify_stage_e.py`](../../research/stage_e_stage_d_20261009/quantify_stage_e.py)
- Summary: [`analysis_summary.json`](../../research/stage_e_stage_d_20261009/analysis_summary.json)
- Source receipt: [`source_data_receipt.json`](../../research/stage_e_stage_d_20261009/source_data_receipt.json)

`FACT`: the script reads only named frozen JSON artifacts, verifies anchor counts, and performs zero model, judge, GPU, database, service, paid-API, or package-install calls.
