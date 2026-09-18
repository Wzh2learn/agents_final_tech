---
name: experiment-observer
description: 自动检查实验日志，提取关键指标（HR/NDCG/sHR/proto cos/ort_loss/group 诊断/τ 退火）、趋势分析和健康度判断。当用户需要分析实验结果、定时 check 进度、或生成实验报告时使用。
---

# 实验日志观察与分析

> 合并自 `skills/experiment-observer` + `code/docs/skills/experiment_log_observer.md`，作为实验日志分析的单一权威 skill。

## 使用场景
- 定时检查实验进度（每 10-40 分钟）
- 实验完成后生成详细报告
- 对比多个实验结果
- 诊断训练异常（proto 塌缩、EMA 漂移、DDP 死锁、分配集中化等）

## 核心观察指标

### 1. Epoch 行提取
```bash
grep -E "Epoch [0-9]+ P" <log_file> | tail -10
```
格式：`Epoch X PY | gen=A ort=B gate=C con=D rtr=E | sHR@10=F | HR@10=H NDCG@10=I | Js *BEST*`

**关键指标解读**：
- `gen_loss`：主 loss，持续下降 = 训练正常
- `ort_loss`：正交 loss，<0.3 = 健康，持续下降 = proto 正交性在学
- `sHR@10`：采样 hit rate（快筛，有 sampled 捷径风险）
- `HR@10`：全词表 hit rate（**主指标**）
- `NDCG@10`：排序质量（**主指标**）
- `*BEST*`：当前 best epoch（会跑 full_eval，HR 有效）

### 2. BEST 统计
```bash
grep -c "BEST" <log_file>
```
- **12** = 正常震荡
- **24** = 过度平滑（反而限制泛化）
- **<10** = 剧烈震荡

⚠️ HR=0 非 best epoch 是正常现象（full_eval 只在 best/last ep 跑）。判断依据：看 `*BEST*` 标记 + eval 时间（2s=非 best，4-6s=best，36-40s=last ep）。

### 3. Group 分配诊断
```bash
grep -E "\[GROUP\] active_groups" <log_file> | tail -5
```
**健康标准**：
- ✅ `active_groups=64/64`（balanced init 生效）
- ✅ `entropy≈4.15`（≈log64 纯均匀，**均匀是 feature 不是 bug**）
- ✅ `max_weight<0.13`（健康分配）
- ⚠️ `max_weight` 缓慢增长（ep1=0.02 → ep30=0.12 健康，0.16 偏集中）
- ❌ `entropy<4.0` 或 `max_weight>0.5` = 分配集中化问题

### 4. τ 退火诊断（仅当启用 Gumbel 温度退火时）
```bash
grep "tau=" <log_file>
```
**健康标准**：
- ✅ τ 从 4.85 线性降到 0.5（30 ep）
- ✅ 配合 entropy 正则化（防止后期分配集中化）
- ❌ 单独用 τ 退火（无 entropy 正则化）会导致 max_weight 过高（0.16 vs 0.12）

### 5. Proto 梯度检查（SRTF）
```bash
grep "\[SRTF-GRAD\]" <log_file> | tail -5
```
- **正常**：0.001-0.1
- **异常**：>100 爆炸 或 =0 死梯度

## 对比基线（模板——填入你自己项目的锚点）

> 基线表是判读的前提：没有锚点，任何读数都无法定性。每行须可溯源到具体 commit / log 路径。

| 基线 | 采样指标 | 主指标 | 排序指标 | 来源 |
|------|---------|--------|---------|------|
| baseline (commit) | 0.xxxx | 0.xxxx | 0.xxxx | logs/... |
| 主方法 | — | 0.xxxx | — | logs/... |
| 外部对照（论文复现） | 0.xxxx | 0.xxxx | 0.xxxx | logs/... |

## 常见误判

1. HR=0 非 best epoch 是正常（full_eval 只在 best/last ep 跑）
2. EMA P2(ep8+)才启用，P0/P1 无 cos/norm print 正常
3. ort<0.3 间接判断 cos<1.0（EMA 修复成功）
4. sHR vs HR 分歧=sampled 捷径，主指标看 HR/NDCG
5. group proto entropy≈4.158（log64 纯均匀）是 feature 非 bug
6. 过度平滑训练（24 BEST）反而限制泛化

## 报告模板

### 进度报告
```
**实验 X**：ep Y/30，进度 Z%
- best epW：sHR A / HR B / NDCG C
- ort_loss D（健康/异常）
- GROUP：active=E/64 entropy=F max_weight=G
- 预计 ~T 完成
```

### 完成报告
```
**实验 X 已完成** ✅（耗时，exit=0）
- best epY：sHR A / HR B / NDCG C
- vs baseline：HR +/-X%
- proto cos=D（健康/趋同）
- 结论：[有效/无效/需进一步验证]
```

## Log 路径约定
- 并行实验：`code/logs/parallel_exp{N}_*.log`
- 批次实验：`code/logs/p0_batch*_*.log`
- Smoke test：`code/logs/smoke_*.log`
- 验证实验：`code/logs/verify_*.log`
