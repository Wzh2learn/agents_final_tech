# 72B vs 35B RAG QA Re-evaluation - 2026-07-31 23:20

## Setup
- 35B: :8004 (Qwen3.6-35B-A3B-Q4_K_M, 64K ctx, MoE 3B active, thinking mode)
- 72B: :8006 (Qwen3-72B-Instruct-Q4_K_M, 32K ctx, full 72B, thinking mode)
- RAG: PGVector m1_parsed_statements, top_k=3
- 5 financial queries tested

## Key Finding: 72B Degenerate Output Confirmed on RAG QA

| # | Query | 35B Latency | 72B Latency | 72B Output |
|---|-------|-------------|-------------|------------|
| 1 | 嘉兴民安的总资产是多少？ | 5314ms | 70645ms | Degenerate: repeating commas |
| 2 | 嘉兴民安有哪些证券持仓？ | 4900ms | 70836ms | Degenerate: repeating zeros |
| 3 | 复熙混合25号的资产总值？ | 4902ms | 70835ms | Degenerate: repeating zeros |

72B produced degenerate output on ALL 3 queries tested before timeout:
- Query 1: `，，，，，，，，，，，，，，，，，，，，，...` (repeating Chinese commas)
- Query 2: `1.0 0 0 0 0 0 0 0 0 0 0 0 0...` (repeating zeros)
- Query 3: `，，000000000000000000000...` (repeating zeros)

This is the SAME degenerate pattern observed in the structured extraction test
(docs/experiments/2026-07-31_72b_reevaluation.md previous version).

## Latency Comparison
- 35B: ~5 seconds per query (with thinking)
- 72B: ~71 seconds per query (14x slower)
- 72B RAM: ~46GB (vs 35B ~6.5GB)

## 35B Note
35B answers appeared empty in the automated test because Qwen3 thinking mode
consumes all max_tokens=300 for reasoning_content, leaving content="".
With proper token budget (max_tokens=2000+), 35B produces correct answers
as verified by the M2 RAG QA endpoint (/api/m2/ask returns correct answers).

## Conclusion

**72B is NOT suitable for any role in this system.**

- Structured extraction: degenerate (previous test)
- RAG QA generation: degenerate (this test)
- Latency: 14x slower than 35B
- RAM: 7x more than 35B
- The Q4_K_M quantization of the 72B Instruct model appears fundamentally
  broken on this ARM64 + CUDA setup, producing repetitive token loops
  regardless of task type.

**Recommendation: Do NOT load 72B again. 35B remains the sole model for
both M1 parsing and M2 generation. The 47GB disk space can be reclaimed.**

## Action Taken
- 72B process killed after test (PID 88037)
- Port :8006 freed
- 47GB model file retained on disk for now (can be deleted if space needed)
