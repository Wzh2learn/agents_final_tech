---
name: gpu-env
description: Activate GPU training environment, check GPU/driver status, verify torch/accelerate/deepspeed are working. Use when starting a new session or troubleshooting environment issues.
when_to_use: new session on a training server, training won't start, CUDA errors, environment verification
---

# GPU Environment Check

## When to use
- New session starts — verify environment is ready before training
- Training/inference launch fails — isolate env vs code issues
- After system updates — confirm drivers and libraries still work

## Procedure

### 1. Activate environment
```bash
source ~/project/env.sh
# Or: conda activate <env_name>
```

### 2. Check Python and Torch
```bash
python -c "import torch; print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print('devices:', torch.cuda.device_count())"
```

### 3. Check distributed training stack
```bash
python -c "import accelerate; print('accelerate:', accelerate.__version__)"
python -c "import deepspeed; print('deepspeed:', deepspeed.__version__)"
```

### 4. Check key environment variables
```bash
env | grep -E 'MASTER_ADDR|MASTER_PORT|WANDB|LD_LIBRARY|NCCL|CUDA'
```

### 5. Check GPU status
```bash
nvidia-smi
```

### 6. Verify project paths
```bash
ls ~/project/code/ ~/project/datasets/ 2>&1 | head -20
```

## Expected results
- `torch.cuda.is_available()` = True
- `torch.cuda.device_count()` = N (matches your hardware)
- NCCL/communication env vars set correctly for multi-GPU
- All project directories exist and are accessible

## Common failures
| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `CUDA not available` | Driver mismatch or env not activated | Check `nvidia-smi` vs torch CUDA version |
| `device_count() = 0` | GPU not visible to container | Check `--gpus` flag or device mapping |
| `NCCL timeout` | Network config for multi-node | Set `NCCL_SOCKET_IFNAME`, check firewall |
| `OOM on import` | Other process using GPU memory | `nvidia-smi` → kill zombie processes |
