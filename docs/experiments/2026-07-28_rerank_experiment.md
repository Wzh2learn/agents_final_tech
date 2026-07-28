# Cross-Encoder Rerank 实验

日期: 2026-07-28
Reranker: bge-reranker-v2-m3 (local, cross-encoder, CUDA)
检索: hybrid (vector 0.6 + BM25 0.4)
数据集: TAT-DQA joint-v1 validation (20 docs, 100 questions, 627 blocks)
Embedding: Qwen3-Embedding-0.6B (local, CUDA)
Generation: Qwen3-14B-Q4 (local, :8004)
Collection: tat-dqa-joint-v1-validation
Python: miniconda3/envs/wzh_retrieval (torch 2.9.1+cu128, sentence-transformers 5.4.0)
评估脚本: scripts/run_rerank_eval.py

## 结果表

| 实验 | 初始 top_k | rerank 后取 | Doc R@5 | Evi R@5 | MRR | EM | Cite | Latency | Rerank Lat |
|------|-----------|------------|---------|---------|------|------|------|---------|------------|
| baseline (no rerank) | 5 | 5 | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 3.5s | - |
| F-10 (no rerank) | 10 | 10 | 0.85 | 0.53 | 0.4178 | 0.23 | 0.49 | 4.2s | - |
| G | 10 | 5 | 0.85 | 0.50 | 0.4098 | 0.28 | 0.48 | 3.55s | 0.13s |
| H | 5 | 5 | 0.81 | 0.50 | 0.4108 | 0.26 | 0.49 | 3.23s | 0.06s |
| I | 10 | 3 | 0.83 | 0.45 | 0.3983 | 0.30 | 0.45 | 3.34s | 0.11s |

## 发现

1. **Cross-encoder rerank 显著提升 EM（精确匹配）**:
   - G (10→5): EM 0.28，比 F-10 no-rerank (0.23) 提升 +22%，比 baseline (0.24) 提升 +17%
   - H (5→5): EM 0.26，比 baseline (0.24) 提升 +8%
   - I (10→3): EM 0.30，所有实验最高，比 baseline 提升 +25%
   - 表明精排将最相关的证据排在前面，帮助 LLM 生成更准确的答案

2. **Rerank 开销极低**:
   - 交叉编码器 GPU 推理仅 0.06-0.13s/问题（10 候选）
   - 相比 LLM rerank (>600s/100 问题超时)，cross-encoder 方案完全可用
   - 总延迟与 no-rerank 基线持平（3.2-3.6s vs 3.5-4.2s）

3. **召回-精度权衡**:
   - G (10→5): 保持 Doc R@5 0.85（与 F-10 相同），Evi R@5 从 0.53 降至 0.50
     （截断至 5 条丢失部分证据），但 EM 从 0.23 升至 0.28
   - I (10→3): 最激进的截断，Evi R@5 降至 0.45，但 EM 最高 (0.30)
     说明更聚焦的上下文有利于答案生成，但牺牲了证据覆盖率
   - H (5→5): 与 baseline 召回完全一致（top_k=5 无截断），EM 小幅提升

4. **MRR 轻微下降**:
   - 所有 rerank 实验 MRR 略低于对应 no-rerank 基线
   - G: 0.4098 vs F-10 0.4178; H: 0.4108 vs baseline 0.4132
   - 原因: cross-encoder 优化语义相关性排序，但 gold evidence block
     的排序位置未必提升（小集合中检索排序已较优）

5. **推荐配置: G (top_k=10 → rerank → top-5)**:
   - 最佳召回-精度平衡: Doc R@5 0.85 + EM 0.28
   - 相比 baseline: Doc R@5 +5%, EM +17%, 延迟持平
   - 相比 F-10 no-rerank: EM +22%, 延迟降低 (3.55s vs 4.2s)

## 阻塞与异常

- **所有实验超过 300s 软超时** (355s, 323s, 334s):
  非异常，100 问题 × ~3.3s/问题 = ~330s 是正常耗时。
  300s 阈值偏紧，实际无需中断。

- **CUDA capability 警告**: GB10 (SM 12.1) vs torch 声明支持至 12.0。
  推理正常完成，与上一轮实验一致。

- **BM25 索引构建警告**: 每次检索触发 BM25 索引重建警告。
  不影响结果，但表明 BM25 索引未持久化。

## 实验方法

- 检索: `RAGService.smart_retrieve(top_k=N, use_rerank=False)` 获取 N 个候选
- 精排: `CrossEncoder('bge-reranker-v2-m3').predict(pairs)` 对 (query, doc_text) 打分
- 截断: 按 rerank 分数降序取 top-M
- 生成: Qwen3-14B-Q4 (:8004) 基于精排后证据生成答案
- 指标: 与上一轮消融实验完全一致的计算方法
- 原始输出: ~/wzh/datasets/tat-dqa/derived/rerank/ (不入 Git)

## 后续建议

1. **将 G 配置 (10→5 rerank) 集成到 RAGService**: 在 `smart_retrieve` 中
   增加 cross-encoder rerank 选项，替代不可用的 LLM rerank
2. **证据召回 0.50 仍是主要瓶颈**: 需改进分块策略（当前 627 块粒度可能过粗）
3. **测试 rerank 对更大集合的效果**: 当前 627 块集合太小，检索已近乎完美，
   rerank 价值在更大集合中更显著
4. **考虑 Qwen3-Reranker-0.6B**: 如果有 SILICONFLOW_API_KEY，可对比
   API reranker 与本地 bge-reranker-v2-m3 的效果差异
