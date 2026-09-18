---
name: offline-eval-playbook
version: 1.0.0
description: |
  Offline evaluation judgment playbook: multi-slice evaluation (full/covered/intersection),
  gate guards, metric interpretation toolkit (hit/miss decomposition, expose ratio probe,
  mrr-ndcg shape classifier, @K tail analysis, immune metrics), pre-registered judgment
  discipline, and common engineering pitfalls in offline eval pipelines.
  Triggers: offline eval, evaluation playbook, judgment criteria, hit/miss analysis,
  recall interpretation, evaluation gate, metric calibration, offline-online gap.
  Source: 10+ batch evaluations across 2 months of industrial recommendation experiments.
metadata:
  category: ml-research
  tags: [evaluation, offline-eval, metrics, judgment, recommendation]
---

# Offline Evaluation Judgment Playbook

> Elastic disclaimer: numeric anchors are from specific batches — re-verify anchors before citing in new contexts.
> This skill stores METHODOLOGY, not readings. Experiment results live in EXPERIMENTS_LOG.

## 一、Three Slices (same numbers, three interpretations — every conclusion must declare which slice)

| Slice | Denominator | Purpose |
|---|---|---|
| Full slice | All GT users, uncovered count as 0 | **Trend only** — coverage holes + population composition pollute, don't use for direct judgment |
| Covered re-calibration | Full reading × N_total/N_covered | Restore quality of actually-served population (math: uncovered recall=0 strictly holds) |
| **Intersection slice** | Users covered by BOTH models (denominators exactly equal) | **Primary judgment** — pure quality comparison |

**Iron rule**: When a coverage-fixing operation shows "full-slice caught up", you MUST decompose by layer (each layer's win/loss) before concluding "quality unchanged" — full-slice tracking confounds deep quality changes with coverage recovery.

## 二、Gate Guards (check gates BEFORE reading metrics)

Run these before interpreting any numbers — if gates fail, the entire batch is suspect:

- **Embedding count** = verify eval denominator matches expectations
- **Result row count** = query_count × K (e.g., ×100 for top-100); mismatch = visibility window incident, batch invalidated
- **Pool verification** = pool items match expected count bit-for-bit
- **Coverage check** = matches anchor bit-for-bit = population correctness self-proof
- **Space consistency** = judgment anchors must be reproduced from same retrieval space (±0.03% = bit-level match)

## 三、Calibration Between Local Eval and Online Eval

- Absolute values are incomparable (different candidate pools = different exam difficulty)
- Only direction and band membership (within/outside noise band) can be cross-validated
- Empirical shrinkage: **same-population ~1.25×, full-population ~3×** (local → online amplitude shrinks)
- Metrics inflated by eval-target-subset-of-pool: use only for within-pool comparison, never extrapolate

## 四、Metric Interpretation Toolkit (from 10+ batch evaluations)

### 1. Hit/Miss Decomposition
Offline GT hit ≠ online value. "Hit" (user recently clicked) = repeat recommendation, structurally suppressed by diversity merging (~37% win rate < miss ~51%). **Miss-only recall is the true online value proxy**.

### 2. Expose Ratio Probe
`expose_r30 ÷ click_r30` = damage amplification factor (healthy ~0.97; failure-level: 1.54). Abnormal rise = damage concentrated on new content side. Expose compresses model differences 50-75% (coarse mirror), click is the magnifying glass.

### 3. MRR−NDCG Shape Classifier
- MRR amplitude > NDCG = **head-type** (mild improvement, all normal improvements show this)
- Reverse (NDCG holds better than MRR) = **full-rank collapse signature** (only at failure level)

### 4. @K Tail Value
`(r100−r30)/r30` = quota adjustment impact estimator. Weak head + hits shifting backward = window truncation signature.

### 5. GT-count Weighted Recall
When median GT interactions = 1, weighted ≈ uv_hr × median. If Δ unchanged before/after weighting = conclusion not hijacked by single-click users.

### 6. Immune Metrics (catch execution bugs, NOT model judgments)
- History ratio: shared shape across all models = behavioral regularity, not model signal
- Category diversity: stable across model variants = not worth interpreting differences
- Popular hit: population composition effect dominates; generational dark trend exists

## 五、Pre-registered Judgment Discipline

### Judgment criteria MUST be pre-registered in three tiers:
```
Success: ≥ +X% (worth deploying)
Explainable: −X% to −Y% (degradation has known mechanism)
Falsification: < −Y% (direction killed)
```

### Judgment line prerequisite checklist (8 cases, battle-tested):

1. **Anchor four-piece set**: anchor's metric name / denominator / retrieval pool / space — all must match
2. **Control not yet available → don't judge**: if pre-registered comparison hasn't produced numbers yet, don't substitute
3. **Cross-coverage contamination**: different coverage between two models → per-user means contain structural bonus, decompose first
4. **Denominator scope mismatch**: if mechanism acts on shallow population, don't judge with deep-only denominator
5. **Automated judgment needs pre-check**: machine-driven judgment must auto-verify space/population match before executing
6. **Full-slice parity ≠ quality parity**: can be "coverage recovery × quality dilution" canceling out — always decompose
7. **Anchor population must be same-source**: same-population judgment requires bit-for-bit source verification
8. **Proxy variable validity**: before using proxy to judge target, verify ① causal chain completeness ② sensitivity axis alignment

## 六、Engineering Pitfalls (each one hit in production)

| Pitfall | Signature | Fix |
|---|---|---|
| Visibility window race condition | Result has rows but ranked table shows 0 | Double-COUNT guard + retry |
| Lazy table existence check always true | Skips materialization, reports "not found" later | Use explicit `exist_table` |
| AVG without COALESCE on LEFT JOIN | NULL excluded → inflated average | Sanity-check against anchor |
| Bare CROSS JOIN | Cartesian product explosion | Small table with `/*+ mapjoin */` |
| INNER JOIN on hit table | expose@100=100% (false positive) | Always LEFT JOIN |
| Partition exists ≠ data ready | Read returns 0 rows silently | Check `last_data_modified_time` |
| LIFECYCLE auto-recycle | Zombie table (0 rows) / external table pointing to deleted storage | Pre-run COUNT + external table audit |
| Peak-hour queue starvation | Instance gets 0 workers for 30+ min | Reduce mapper split size, schedule for off-peak |

## 七、Delivery & Logging Discipline

- Every evaluation result → backfill to EXPERIMENTS_LOG with: judgment line used, gates passed, slice declared, correction records
- Numbers cited across sections must verify metric name + denominator match (don't mix slices)
- Reproducibility: re-run coverage bit-for-bit + full-slice reading within <0.1% (retrieval tie noise band)
