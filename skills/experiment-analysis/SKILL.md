---
name: experiment-analysis
description: |
  Standardized analysis framework for ML experiment results. Follows a 5-step process
  (data alignment → layered analysis → comparison table → causal inference → action recommendation)
  to do deep attribution on training/inference/evaluation results.
  Triggers: "分析实验结果", "analyze experiment results", "compare experiments", "why is this experiment negative",
  "实验归因", "experiment attribution", "ablation analysis".
metadata:
  category: analysis
  tags: [experiment, ml, evaluation, ablation, attribution]
---

# Experiment Analysis Framework

> After every new experiment result, follow this framework step-by-step to avoid missing key signals.

## Instructions

### Step 1: Data Alignment (Ensure Comparability)

Check whether experiments satisfy comparison conditions:

| Metric | Same BS comparable? | Same data comparable? | Cross-config comparable? |
|:---|:---|:---|:---|
| Online metrics (A/B test) | ✅ | ✅ | ✅ (final decision standard) |
| Offline eval (HR/NDCG/MRR) | ✅ | ✅ | ✅ (primary offline metric) |
| Proxy metrics (retrieval quality) | ✅ | ⚠️ sample distribution affects | ✅ |
| Training loss | ✅ | ⚠️ data distribution affects | ❌ cross-BS incomparable |
| Accuracy@K | ✅ | ✅ | ❌ cross-BS incomparable |

If comparability is not satisfied, declare it first, then give conditional conclusions.

### Step 2: Layered Analysis

**Layer 1: Primary Metrics (Final Judgment)**

- Identify the core decision metric (e.g., HR@10, Click@50, NDCG@10)
- Judgment standard: > +X% positive / ±X% noise / < -X% negative (define X for your task)
- Check all TopN tiers — are directions consistent?
- Check multiple evaluation variants — are they directionally aligned?

**Layer 2: Offline Eval Diagnostics (Attribution)**

Core metrics priority:
1. **Representation quality** — embedding uniformity, diversity metrics
2. **Retrieval proxy** — offline approximation of online recall quality
3. **Dimensional utilization** — effective rank, intrinsic dimensionality
4. **Alignment metrics** — how well representations match true relevance

Attribution framework:
- Uniformity ↑ + Proxy ↑ → representation improvement driven
- Alignment ↑ + Uniformity unchanged → alignment improvement driven  
- Uniformity ↓ → representation collapse / degradation
- Proxy unchanged + auxiliary metric ↑ → shortcut learning (no real improvement)

**Layer 3: Training Curves (Process Monitoring)**

- Loss convergence behavior across experiments
- Learning rate schedule effects
- Early stopping indicators
- Divergence between train and eval metrics

### Step 3: Comparison Table (Standard Format)

| Experiment | Key Metric 1 | Key Metric 2 | Primary Eval vs Baseline | Conclusion |
|:---|:---|:---|:---|:---|
| Baseline | X | X | — | — |
| Experiment A | X (Δ) | X (Δ%) | +X% | ✅/❌/≈ |

### Step 4: Causal Inference

Analysis template:
1. What did this experiment change? (data / model / loss / training procedure)
2. How does this change affect representation quality? (direct/indirect/none/negative)
3. Does this change break any existing mechanism? (attention pattern / positional semantics / gradient flow)
4. Pattern matching against known success/failure modes:

**Common success patterns:**
- More diverse training data → better representation uniformity → metric ↑
- Larger batch size → harder negatives → better discrimination
- Loss-side weighting → emphasize hard/high-quality samples → better gradients
- Curriculum learning → easier optimization landscape

**Common failure patterns:**
- Data augmentation that provides shortcuts → proxy ↑ but eval flat
- Model capacity increase without regularization → overfit
- Sequence/structure manipulation → breaks learned positional semantics
- Additive/multiplicative signal injection → doesn't change geometry → no improvement

### Step 5: Action Recommendation

Decision tree:
- Primary metric > +threshold → **Adopt**, use as new baseline
- Primary metric weakly positive + direction consistent → **Stack**, worth combining with other improvements
- Primary metric ≈ 0 → **Abandon**, no signal
- Primary metric weakly negative → **Abandon**
- Primary metric strongly negative + clear attribution → **Learn**, document the failure mode

Standard output format:
```
## Experiment X Analysis

**Result**: Metric = X (vs baseline +/- Y%)
**Attribution**: [uniformity improvement / alignment improvement / no change / degradation]
**Mechanism**: [one sentence explaining why]
**Decision**: [adopt / abandon / needs replication]
**Next step**: [specific action]
```

## Historical Lessons Template

Maintain a running table of validated patterns:

| # | Lesson | Source experiment | Times confirmed | Application |
|:---|:---|:---|:---|:---|
| 1 | [pattern description] | exp_name | N | [when to apply] |

Update this table after every experiment — both successes AND failures contribute knowledge.

## Offline Metric Reliability Ranking Template

| Metric | Applicable scenario | Reliability | Notes |
|:---|:---|:---|:---|
| [metric_1] | all experiments | ⭐⭐⭐⭐⭐ | most reliable |
| [metric_2] | specific conditions | ⭐⭐⭐⭐ | unreliable when [condition] |

## When NOT to use
- Pure code debugging (use `systematic-debugging`)
- Environment issues (use `gpu-env`)
- Data pipeline problems (use `data-sync`)
- Single metric lookup without analysis needed
