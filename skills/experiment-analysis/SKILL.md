---
name: experiment-analysis
description: Analyze ML experiment results — periodic log watching (HR/NDCG/sHR/proto cos/ort_loss/group diagnostics/tau annealing), a 5-step attribution framework (data alignment -> layered analysis -> comparison table -> causal inference -> action), and health judgment. Use to interpret results, check progress, compare experiments, or explain why an experiment was negative.
when_to_use: 分析实验结果, analyze experiment results, 实验归因, experiment attribution, ablation analysis, 为什么有效/为什么无效, periodic progress check during a run, generating an experiment report, training looks stuck or anomalous
---

# Experiment Analysis

Two halves of one job: read the run as it happens, then attribute the result once it lands.
Follow the attribution half step-by-step after every new result to avoid missing key signals.

## Part A — Online monitoring (while the run is live)

### Epoch line extraction
```bash
grep -E "Epoch [0-9]+ P" <log_file> | tail -10
```
Format: `Epoch X PY | gen=A ort=B gate=C con=D rtr=E | sHR@10=F | HR@10=H NDCG@10=I | Js *BEST*`

Key readings:
- `gen_loss`: primary loss, steadily decreasing = training normal
- `ort_loss`: orthogonality loss, <0.3 = healthy, decreasing = proto orthogonality is being learned
- `sHR@10`: sampled hit rate (fast screen, has a sampled-shortcut risk)
- `HR@10`: full-vocabulary hit rate (**primary metric**)
- `NDCG@10`: ranking quality (**primary metric**)
- `*BEST*`: current best epoch (runs full_eval, HR is valid)

### BEST statistics
```bash
grep -c "BEST" <log_file>
```
- **12** = normal oscillation; **24** = over-smoothed (limits generalization); **<10** = violent oscillation.

HR=0 on a non-best epoch is normal (full_eval only runs on best/last ep). Judge by the `*BEST*` marker
plus eval time (2s = non-best, 4-6s = best, 36-40s = last ep).

### Group allocation
```bash
grep -E "\[GROUP\] active_groups" <log_file> | tail -5
```
Healthy: `active_groups=64/64` (balanced init), `entropy~4.15` (near log64 = uniform, **uniform is a
feature not a bug**), `max_weight<0.13`. Warn on slow `max_weight` growth (ep1=0.02 -> ep30=0.12 healthy,
0.16 concentrated). Fail on `entropy<4.0` or `max_weight>0.5`.

### Tau annealing (only when Gumbel temperature annealing is enabled)
```bash
grep "tau=" <log_file>
```
Healthy: tau falls linearly 4.85 -> 0.5 over 30 ep, paired with entropy regularization. Tau annealing
alone (no entropy regularization) drives `max_weight` too high.

### Proto gradient check
```bash
grep "\[SRTF-GRAD\]" <log_file> | tail -5
```
Normal: 0.001-0.1. Anomalous: >100 (exploding) or =0 (dead gradient).

### Log path conventions
- Parallel runs: `code/logs/parallel_exp{N}_*.log`
- Batch runs: `code/logs/p0_batch*_*.log`
- Smoke test: `code/logs/smoke_*.log`
- Verification: `code/logs/verify_*.log`

## Part B — Post-hoc attribution (after the result lands)

### Step 1: Data Alignment (Ensure Comparability)

Check whether experiments satisfy comparison conditions:

| Metric | Same BS comparable? | Same data comparable? | Cross-config comparable? |
|:---|:---|:---|:---|
| Online metrics (A/B test) | yes | yes | yes (final decision standard) |
| Offline eval (HR/NDCG/MRR) | yes | yes | yes (primary offline metric) |
| Proxy metrics (retrieval quality) | yes | sample distribution affects | yes |
| Training loss | yes | data distribution affects | no (cross-BS incomparable) |
| Accuracy@K | yes | yes | no (cross-BS incomparable) |

If comparability is not satisfied, declare it first, then give conditional conclusions.

### Step 2: Layered Analysis

**Layer 1: Primary metrics (final judgment)** — identify the core decision metric (HR@10, NDCG@10, ...);
define the >+X% positive / +-X% noise / <-X% negative band for your task; check all TopN tiers and
evaluation variants for directional consistency.

**Layer 2: Offline eval diagnostics (attribution)** — representation quality (embedding uniformity,
diversity), retrieval proxy, dimensional utilization (effective rank, intrinsic dimensionality),
alignment. Attribution: uniformity up + proxy up => representation-driven; alignment up alone =>
alignment-driven; uniformity down => collapse; proxy flat + auxiliary up => shortcut learning.

**Layer 3: Training curves (process monitoring)** — loss convergence, LR schedule effects, early-stop
indicators, train/eval divergence.

### Step 3: Comparison Table (Standard Format)

| Experiment | Key Metric 1 | Key Metric 2 | Primary Eval vs Baseline | Conclusion |
|:---|:---|:---|:---|:---|
| Baseline | X | X | - | - |
| Experiment A | X (delta) | X (delta%) | +X% | adopt/abandon/approx |

A baseline table is the precondition for reading anything: without an anchor, no number can be
qualified. Every row must trace to a specific commit / log path.

### Step 4: Causal Inference

Template: (1) what did this experiment change (data / model / loss / procedure)? (2) how does that
affect representation quality (direct/indirect/none/negative)? (3) does it break any existing mechanism
(attention pattern, positional semantics, gradient flow)? (4) match against known patterns.

Common success: more diverse data => better uniformity; larger batch => harder negatives; loss-side
weighting => emphasize hard/high-quality samples; curriculum => easier optimization landscape.

Common failure: augmentation providing shortcuts => proxy up, eval flat; capacity up without
regularization => overfit; sequence/structure manipulation => breaks positional semantics; additive
signal injection => geometry unchanged => no improvement.

### Step 5: Action Recommendation

- Primary metric > +threshold => **Adopt**, use as new baseline.
- Weakly positive + direction consistent => **Stack** with other improvements.
- Approximately 0 => **Abandon**, no signal.
- Weakly negative => **Abandon**.
- Strongly negative + clear attribution => **Learn**, document the failure mode.

Standard output:
```
## Experiment X Analysis
**Result**: Metric = X (vs baseline +/- Y%)
**Attribution**: [uniformity / alignment / no change / degradation]
**Mechanism**: [one sentence]
**Decision**: [adopt / abandon / needs replication]
**Next step**: [specific action]
```

## Common misreads

1. HR=0 on a non-best epoch is normal.
2. EMA prints only from a certain phase on; missing cos/norm early is normal.
3. `ort<0.3` indirectly implies `cos<1.0`.
4. sHR vs HR divergence = sampled shortcut; trust HR/NDCG.
5. group proto entropy ~4.158 (log64) is a feature, not a bug.
6. Over-smoothed training (24 BEST) limits generalization.

## Report templates

Progress:
```
**Experiment X**: ep Y/30, progress Z%
- best epW: sHR A / HR B / NDCG C
- ort_loss D (healthy/anomalous)
- GROUP: active=E/64 entropy=F max_weight=G
- ETA ~T
```
Completion:
```
**Experiment X complete** (duration, exit=0)
- best epY: sHR A / HR B / NDCG C
- vs baseline: HR +/-X%
- proto cos=D
- Conclusion: [effective / ineffective / needs more validation]
```

## When NOT to use
- Pure code debugging (use `systematic-debugging`)
- Environment issues (use `gpu-env`)
- Data pipeline problems (use `data-sync`)
- A single metric lookup with no analysis needed
