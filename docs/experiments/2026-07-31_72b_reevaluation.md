# 72B Re-evaluation (2026-07-31)

## Setup
- 72B: Qwen3-72B-Instruct Q4_K_M, :8006, -c 4096 -ngl 999
- 35B: Qwen3.6-35B-A3B, :8004, -c 65536
- 3 short financial extraction queries, temp=0.1, max_tokens=100

## Results

### Q1: ??????????=22168543.90???????????????

| Model | ms | Response |
|-------|-----|----------|
| 35B | 1705 |  |
| 72B | 23778 | 2
 255000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 |

### Q2: ??????????=600057,??=????; ??=170446,??=?????????????

| Model | ms | Response |
|-------|-----|----------|
| 35B | 1686 |  |
| 72B | 23800 | 1. 1001 1 1 1 1 01 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1  |

### Q3: ????????????=1.5450??????????????

| Model | ms | Response |
|-------|-----|----------|
| 35B | 1678 |  |
| 72B | 23857 | 1. 1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
 |

## Analysis

- 35B avg: 1690ms | 72B avg: 23812ms | ratio: 14.1x
- 72B at ~4 t/s generation speed (vs 35B MoE much faster)
- 72B uses ~46GB RAM (vs 35B ~20GB)

### Quality

- Q1: 35B=`` | 72B=`2
 255000000000000000000000000000000000000000000000000000000`
- Q2: 35B=`` | 72B=`1. 1001 1 1 1 1 01 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1`
- Q3: 35B=`` | 72B=`1. 1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1`

## Conclusion
- 72B generation speed ~4 t/s is unacceptable for interactive use
- Memory 46GB leaves only ~26GB for other services on 121GB GB10
- Quality difference (if any) does not justify the cost
- **Recommendation: 72B NOT suitable for any always-on role**
- If needed for batch M2 generation: on-demand only, kill after use
- Current 35B+14B architecture remains optimal
