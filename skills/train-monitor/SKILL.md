---
name: train-monitor
description: Monitor running training jobs — check GPU utilization, training progress, loss curves, and detect common failures (NaN, OOM, stalled training). Use for periodic health checks during long training runs.
when_to_use: training is running, periodic check, suspect training is stuck or failing silently
---

# Train Monitor

## When to use
- Periodic health check during multi-hour/multi-day training
- Suspect training is stuck (no progress in logs)
- GPU utilization dropping or memory issues
- Need to decide whether to early-stop or continue

## Quick health check (30 seconds)

```bash
# 1. Is the process alive?
ps aux | grep python | grep train

# 2. GPU utilization
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv

# 3. Latest log lines
tail -20 logs/current_experiment.log

# 4. Last checkpoint time
ls -lt checkpoints/ | head -3
```

## Deep check (2 minutes)

### Loss trend
```bash
# Extract loss values from log
grep -E "loss[=:]" logs/current.log | tail -20

# Or parse structured logs
grep "train_loss" logs/current.log | awk -F'=' '{print $2}' | tail -20
```

### Training speed
```bash
# Steps per second / samples per second
grep -E "steps/s|samples/s|it/s" logs/current.log | tail -5

# Time per epoch
grep -E "Epoch.*completed|epoch_time" logs/current.log
```

### Memory pressure
```bash
# Peak GPU memory
nvidia-smi --query-gpu=memory.used --format=csv -l 1 | head -10

# System memory
free -h
```

## Red flags

| Signal | Meaning | Action |
|--------|---------|--------|
| Loss = NaN | Numerical instability | Kill, reduce LR or add gradient clipping |
| Loss plateaus for >5 epochs | Stuck in local minimum | Consider LR schedule change |
| GPU util < 30% | Data loading bottleneck | Increase num_workers, check I/O |
| GPU util = 0% intermittently | DDP synchronization stall | Check NCCL logs, network |
| Memory keeps growing | Memory leak | Profile with torch.cuda.memory_stats() |
| No new checkpoint in 2× expected interval | Training stalled or crashed | Check process, look for errors in log |
| Loss spikes after being stable | Data corruption or learning rate issue | Check recent data batch, LR schedule |

## Periodic monitoring schedule

| Interval | Check |
|----------|-------|
| Every 10 min (early training) | Loss trend, GPU util |
| Every 30 min (stable phase) | Quick health check |
| Every epoch | Full deep check + checkpoint verify |
| After any anomaly | Immediate deep check |

## Log patterns to watch
```bash
# Gradient overflow (mixed precision)
grep -i "overflow\|inf\|nan" logs/current.log | tail -5

# OOM warnings
grep -i "out of memory\|CUDA OOM" logs/current.log

# DDP issues
grep -i "timeout\|NCCL\|hung\|deadlock" logs/current.log

# Checkpoint saves
grep -i "saving\|checkpoint" logs/current.log | tail -5
```
