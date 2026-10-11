# Stage E Multi-Leaf Sample-Size Plan v1

> 状态: `TARGET_24_PER_STAGE_MINIMUM_FROZEN` | 更新: 2026-10-10 | 取代/被取代: 将 12/24/50 从统一“power plan”改为 engineering / pooled-primary / per-stage 三档；正式 multi-leaf 未运行

## 1. What is frozen

Primary pooled estimand: leave-one-cluster-out macro-F1 for M/R/N signature separability, with top-1 stage accuracy as the co-primary localization endpoint.

Frozen planning assumptions:

```text
delta = 0.10
cluster-level paired-difference SD = 0.25
alpha = 0.05, two-sided
target power = 0.80
simulation replicates = 200,000
simulation seed = 20261009
```

`FACT`: delta and SD are planning assumptions, not pilot-derived estimates. ICC is `NOT YET DEFINED`; the numbers below are conditional calculations, not unconditional guarantees.

## 2. Tier meanings

| Tier | clusters/stage | injections/cluster/stage | total clusters | total injections | status | scientific use |
|---|---:|---:|---:|---:|---|---|
| MINIMAL | 12 | 2 | 36 | 72 | engineering/smoke | adapter and execution feasibility only |
| TARGET | 24 | 3 | 72 | 216 | pooled-primary inference minimum | formal claim about overall M/R/N signature localization |
| STRONG | 50 | 4 | 150 | 600 | per-stage inference tier | separate confirmatory claims for M, R and N |

The previously reported conditional powers remain:

| Tier | pooled exact / simulated power | per-stage power | approximate 95% CI half-width |
|---|---:|---:|---:|
| MINIMAL | `0.646 / 0.648` | `0.245` | `0.0817` |
| TARGET | `0.917 / 0.916` | `0.467` | `0.0577` |
| STRONG | `0.998 / 0.998` | `0.792` | `0.0400` |

`VALUE`: 12/stage is not a formal main experiment. 24/stage is the minimum frozen target for a pooled M/R/N claim. 50/stage is preferred before claiming that every individual stage is localizable.

## 3. Sensitivity and stopping language

At `delta=.05, sigma=.25`, pooled power is `0.215 / 0.388 / 0.682` for MINIMAL/TARGET/STRONG. At `delta=.10, sigma=.35`, pooled power is `0.385 / 0.667 / 0.935`; STRONG per-stage power is `0.508`.

`UNVERIFIED`: real cluster-difference variance, ICC and effect size. A gate-validation estimate may update a future plan, but sealed outcomes may not be used to tune the design.

## 4. Inference and multiplicity

- Primary pooled macro-F1 uses one preregistered permutation test at `alpha=.05`.
- Top-1 accuracy uses a cluster bootstrap interval and must clear the frozen chance/majority baseline.
- Per-stage top-1 claims use Holm correction across M/R/N and are not authorized at TARGET without a separate power decision.
- Top-k, first-visible-stage distance, propagation depth and silent absorption remain exploratory.
- All injections from one cluster stay in the same fold and bootstrap draw.

## 5. Cost and execution gate

The frozen deterministic fixture and generation smoke require zero GPU and zero paid API calls. Judge-dependent downstream leaves require a separate cost plan before execution.

`MULTILEAF_READY_FOR_EXECUTION_NOT_AUTHORIZED`: TARGET `24 clusters/stage x 3 injections` is frozen as the formal minimum. Execution requires explicit user approval.
