# AGENTS.md Template for Multi-Agent Research Projects

> AGENTS.md is the machine-readable companion to CLAUDE.md. While CLAUDE.md tells agents what to do,
> AGENTS.md tells them their operational context: hardware, software, experiment history, code map.

## Template Structure

```markdown
# AGENTS.md — Machine Context

## 环境 / Environment

| Key | Value |
|-----|-------|
| Machine | [hostname] |
| GPUs | [count × model] |
| Python | [version + path] |
| PyTorch | [version] |
| CUDA | [version] |
| Working dir | [path] |

## 代码地图 / Code Map

| Module | Path | Description |
|--------|------|-------------|
| Model | `code/model.py` | Main model forward/backward |
| Memory | `code/memory/` | Memory subsystem (write/read/update/govern) |
| Data | `code/data/` | Dataset + DataLoader |
| Training | `scripts/run.py` | Training entry point |
| Config | `code/config.py` | All hyperparameters |
| Eval | `code/eval/` | Evaluation metrics |

## 实验历史 / Experiment History

> Condensed table of experiments run. Agent reads this to avoid re-running failed approaches.

| # | Date | Config | Result | Conclusion |
|---|------|--------|--------|------------|
| 1 | 2026-06-01 | baseline | HR=0.35 | Baseline established |
| 2 | 2026-06-05 | +feature_A | HR=0.38 | +8.5%, adopted |
| 3 | 2026-06-08 | +feature_B | HR=0.34 | Negative, abandoned |

## 已验证的知识 / Verified Knowledge

> Hard-won facts. Each traces to a specific experiment or debugging session.

- [Fact 1]: discovered in exp #N, verified by [evidence]
- [Fact 2]: discovered during debugging session [date]

## CLI 速查 / Quick Commands

```bash
# Train
torchrun --nproc_per_node=N scripts/run.py --config configs/main.yaml

# Eval
python scripts/eval.py --checkpoint best.pt --dataset test

# Monitor
tail -f logs/current.log | grep "Epoch"
```
```

## Design Principles

1. **Flat facts, not narratives** — agents parse structured data better than prose
2. **Include failed experiments** — prevents agents from re-trying known-bad approaches
3. **Code map is a lookup table** — not documentation, just "where is X"
4. **CLI commands are copy-pasteable** — no placeholders that need filling
5. **Update after every significant experiment** — stale AGENTS.md causes wasted GPU hours
