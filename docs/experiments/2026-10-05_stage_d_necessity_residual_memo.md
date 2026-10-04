# Stage D necessity residual memo（2026-10-05）

> Status: `PILOT_ONLY / TRAINING_NOT_AUTHORIZED`
> Input: B0-B4 exploratory v2 predictions and Stage D necessity gate
> Scope: training-readiness judgment only; no new experiment numbers and no model execution

## 1. Risk-constrained answer

Under the approved `risk_limit = 0.10`:

| Slice | B4 harmful-map rate | Risk admissible | B4 correct-map coverage |
|---|---:|---|---:|
| quarantine + LOO primary | 0.0616 | PASS | 0.2603 |
| whole-pair INVALID + LOO | 0.0615 | PASS | 0.2538 |
| quarantine + salted split | 0.1053 | FAIL | 0.3158 is not admissible coverage |

Therefore the best currently supported answer is: **primary risk-constrained coverage is 0.2603; stable cross-slice risk-constrained coverage is not established.**

## 2. B4 residual decomposition

The existing primary predictions contain:

- 146 evaluated rows;
- 51 gold `map_to`;
- 38 correctly mapped targets;
- 13 gold `map_to` not correctly covered;
- 35 action errors;
- 9 harmful `map_to` predictions.

The 13 gold-map residuals are distributed over 8 of 10 pairs. One pair contributes 6/13 residuals; seven other pairs contribute one each; two pairs contribute zero.

This is evidence of residual, but not yet evidence of a stable residual that warrants a dedicated student. The largest pair contributes 46.2% of the residual, and the mandatory salted split is based on only two test pairs.

## 3. When A2 becomes worth training

A2 should be requested only if the following can be demonstrated after the data and power gates:

1. **Risk constraint**: A2 point harmful-map rate and its cluster-bootstrap 95% upper bound are both `<= 0.10` in the primary analysis and the whole-pair sensitivity.
2. **Coverage improvement**: A2 improves correct-map coverage over B4 with a positive lower cluster-bootstrap bound in the primary analysis; the improvement is not driven by one pair alone.
3. **Target preservation**: target exact among gold `map_to` is not worse than B4 beyond a preregistered margin.
4. **Residual distribution**: the gain appears in multiple independent pairs, with a preregistered maximum share from any one pair.
5. **Split stability**: the direction survives the mandatory salted/group sensitivity, even if that analysis remains exploratory.
6. **Comparison discipline**: A1 and A2 use the same model, tokenizer, template, data budget, seed list, and update budget; the main contrast is checkpoint filtering, not extra data or extra compute.

If these conditions are not met, the correct disposition is `SIMPLE_SUFFICIENT`, `NO_CLEAR_SIGNAL`, or `PILOT_ONLY`, not an automatic A0-A2 launch.

## 4. Current decision

`stage_d_necessity = NOT_ESTABLISHED`.

The current evidence supports preparing an A2 readiness package, but it does not support starting A0/A1/A2/A3. The package must remain a dry-run, mock, format, code-path, and resource-planning artifact until MODEL_GO, TRAINING_GO, the data gates, and the residual rule are separately approved.
