# Experiment Log Template (Dashboard Format)

> A single authoritative table of all experiments — successes AND failures.
> Every experiment gets a row. Conclusion is mandatory (even "null result").
> Failed experiments are never deleted — they prevent re-running the same dead end.

## Design Principles

1. **Pre-registered judgment criteria** — define success/failure thresholds BEFORE results come in
2. **Champion configuration** — always know which config is currently "best" and deployed
3. **Supersede, don't delete** — when old baselines become invalid, mark them with reason, don't remove rows
4. **Evidence linkable** — every number must trace to a specific log file or SQL query

## Template

```markdown
# Project Experiment Log

> ⚠️ [Data validity notice if applicable — e.g., "experiments #1-5 based on old data pipeline, numbers are reference only"]

## Judgment Criteria (Pre-registered)

| Criterion | Threshold | Applies to |
|-----------|-----------|-----------|
| Success | > +2pp vs champion | Any new method |
| Quality floor | > baseline - 1pp | Ablation studies |
| Noise band | ±1pp | All comparisons |
| Null result | Within noise band | Closes the direction |

## Baseline Anchors (Reference, do not modify)

| Anchor | Key Metric | Secondary Metrics | Notes |
|--------|-----------|-------------------|-------|
| baseline_v1 | recall@10 = 0.312 | mrr = 0.213 | First healthy baseline |
| champion (exp_X) | recall@10 = 0.334 | mrr = 0.228 | Current production config |

## Experiment Dashboard

| # | Experiment Name | Config (vs baseline) | Status | Key Metric | Core Conclusion |
|:--|:--|:--|:--|:--:|:--|
| 1 | `exp_name_date` | single variable change | ✅ Done | 0.XXX (+Δ) | ✅/⛔/🟡 One-line conclusion |
| 2 | `exp_name_date` | another change | ✅ Done | 0.XXX | ⛔ Why it failed |
| 3 | `exp_name_date` | ... | 🔄 Running | — | — |

## Status Legend
- ✅ Done (has conclusion)
- 🔄 Running
- ⛔ Killed (with reason)
- 🏆 Champion (current best, in production)

## Rules

1. **Experiment naming**: `{model}_{method}_{date}` — must match output/log directory name
2. **Fill immediately**: log the row when training starts, fill results when done
3. **Conclusion is mandatory**: "null result" or "killed due to OOM" counts — blank does not
4. **Single variable**: each row should change exactly ONE thing vs its comparison anchor
5. **Link evidence**: key metric must reference log path or query that produced it
6. **Champion tracking**: mark 🏆 on current best; when champion changes, log the transition
```

## Advanced Patterns

### Pre-registration Discipline
Write judgment criteria BEFORE results arrive:
- **Success line**: metric > X (worth deploying)
- **Quality floor**: metric > Y (method isn't broken)
- **Noise band**: ±Z (below this, result is noise not signal)

### Champion Configuration Tracking
```markdown
## Champion History
| Date | Config | Key Metric | Supersedes | Reason |
|------|--------|-----------|-----------|--------|
| 2026-07-28 | baseline_v2 | 0.285 | — | First healthy baseline |
| 2026-07-29 | +global_neg | 0.299 | baseline_v2 | +1.4pp confirmed by online |
| 2026-08-03 | +logQ | 0.320 | +global_neg | +3pp, three-evidence chain |
```

### Supersede Chain
When old conclusions are overturned:
```markdown
| Old conclusion | New conclusion | Evidence | Date |
|---------------|---------------|----------|------|
| "τ=0.1 is optimal" | "τ=0.1 confirmed optimal, 0.05/0.15 both worse" | exp10+exp13 | 2026-07-30 |
| "LLM prior helps cold-start" | "LLM prior is null — semantic redundancy" | exp9 (4-decimal match) | 2026-07-28 |
```

### Offline↔Online Calibration Notes
Track which offline metrics reliably predict online outcomes:
```markdown
## Metric Reliability (Empirically Calibrated)
| Offline Metric | Online Correlation | Amplitude Discount | Notes |
|---------------|-------------------|-------------------|-------|
| recall@10 | Direction reliable | ~0.67x | Ranking family |
| popular_hit_ratio | Direction UNRELIABLE | — | Must verify online |
| concentration | Weak signal | — | Online barely visible |
```
