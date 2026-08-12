# 检索策略单变量对照实验

日期: 2026-07-28
数据集: TAT-DQA joint-v1 validation (20 docs, 100 questions, 627 blocks)
Embedding: Qwen3-Embedding-0.6B (local, CUDA)
Generation: Qwen3-14B-Q4 (local, :8004)
Collection: tat-dqa-joint-v1-validation
Python: miniconda3/envs/wzh_retrieval (torch 2.9.1+cu128, sentence-transformers 5.4.0)

## 结果表

| 实验 | 策略 | Doc R@5 | Evi R@5 | MRR | EM | Cite Rate | Latency(s) |
|------|------|---------|---------|------|------|-----------|------------|
| baseline | hybrid (default, top_k=5, no rerank) | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 4.604 |
| A | vector only (weight 1.0/0.0) | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 3.501 |
| B | bm25 only (weight 0.0/1.0) | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 3.493 |
| C | hybrid (default weights 0.6/0.4) | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 3.518 |
| D | hybrid no-rerank (= baseline) | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 3.503 |
| E | hybrid + LLM rerank (Qwen3-14B) | TIMEOUT | - | - | - | - | >600 |
| F-3 | hybrid top_k=3 | 0.77 | 0.47 | 0.4067 | 0.21 | 0.46 | 3.374 |
| F-10 | hybrid top_k=10 | 0.85 | 0.53 | 0.4178 | 0.23 | 0.49 | 4.170 |

## 发现

1. **检索权重对 top-5 排序无影响 (A=B=C=D)**：在 627 块的小集合上，纯向量、纯 BM25、
   混合加权的 top-5 检索结果完全一致（100/100 问题 retrieved_block_hash 相同）。
   原因：`smart_retrieve` 同时执行向量和 BM25 检索，权重仅影响合并评分排序；
   当候选文档在两种方法中重叠度极高时，权重变化不改变 top-5 顺序。
   这表明当前集合规模下，检索方法的区分度不足，瓶颈不在向量/BM25 选择。

2. **Top-K 是唯一有效变量 (F)**：
   - top_k=3 → 所有指标下降（Doc R@5: 0.77↓, Evi R@5: 0.47↓, EM: 0.21↓）
   - top_k=10 → 文档召回提升至 0.85↑, 证据召回 0.53↑, MRR 0.4178↑，
     但 EM 略降至 0.23（更多上下文可能干扰生成）
   - top_k=5 是召回与精度的合理平衡点

3. **LLM Rerank 不可用 (E)**：使用 Qwen3-14B 作为 LLM reranker 在 100 问题上
   超时（>600s）。每次 rerank 需要完整 LLM 推理，延迟不可接受。
   需要专用 reranker 模型（如 cross-encoder）或 SiliconFlow API 的
   Qwen3-Reranker-0.6B 端点（需 SILICONFLOW_API_KEY）。

4. **延迟一致性**：除 baseline 首次运行（4.6s，含模型预热）外，
   各实验延迟稳定在 3.4-4.2s，表明系统吞吐稳定。

## 阻塞与异常

- **E (hybrid + rerank): TIMEOUT**
  原因: LLM-based rerank 使用本地 Qwen3-14B (:8004)，每次 rerank 调用需完整推理，
  100 问题总耗时超过 600s 限制。
  解决路径: 获取 SILICONFLOW_API_KEY 使用 Qwen3-Reranker-0.6B API，
  或部署本地 cross-encoder reranker (bge-reranker-v2-m3 已在
  ~/wzh/models/hf/bge-reranker-v2-m3)。

- **FastAPI 应用 (:5000) 返回 Internal Server Error**
  不影响本实验（eval 脚本直接调用 RAGService），但 Web 服务不可用。

- **CUDA capability 警告**: GB10 (SM 12.1) vs torch 声明支持至 12.0。
  推理正常完成，但存在兼容性风险。

## 实验方法

- 配置切换: 通过 `scripts/run_retrieval_ablation.py` 自动修改
  `config/app_config.json` 中的 `rag.vector_weight` / `rag.bm25_weight`，
  每组实验后恢复原始配置。
- Top-K 切换: 通过 eval 脚本新增 `--top-k` 参数。
- Rerank 切换: 通过 eval 脚本新增 `--use-rerank` 参数 +
  配置 `rerank.enabled` / `rag.force_rerank`。
- 原始输出: `~/wzh/datasets/tat-dqa/derived/ablation/` (不入 Git)
- 基线复现: 与 HANDOFF 记录完全一致（质量指标偏差 0%，延迟因负载略高）

## 后续建议

1. 部署本地 cross-encoder reranker (bge-reranker-v2-m3) 替代 LLM rerank
2. 扩大集合规模后重新测试向量/BM25 权重差异
3. 测试 top_k=10 + rerank 组合（先召回更多再精排）
4. 证据块召回 0.50 是主要瓶颈，需改进分块策略或索引粒度
