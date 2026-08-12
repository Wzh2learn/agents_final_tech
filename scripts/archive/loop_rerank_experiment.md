# 过夜任务：Cross-Encoder Rerank 实验

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
上一轮消融实验发现：
- 向量/BM25/混合权重在 627 块小集合上无差异
- top_k=10 提升召回（Doc R@5: 0.85, Evi R@5: 0.53）
- LLM rerank (Qwen3-14B) 超时不可用
- 本地已有 bge-reranker-v2-m3 在 ~/wzh/models/hf/bge-reranker-v2-m3

本轮目标：部署 cross-encoder reranker，验证精排能否在 top_k=10 基础上提升精度。

## 约束

- 不得触碰 test_gold / test split
- 不得下载新模型（bge-reranker-v2-m3 已在本地）
- 不得修改 CUDA、驱动
- 结果写入 docs/experiments/2026-07-28_rerank_experiment.md
- 不要 push

## 执行步骤

### Phase 0: 验证 reranker 模型可用

```bash
cd ~/wzh/projects/agents_final_tech
source venv/bin/activate

# 检查模型文件
ls ~/wzh/models/hf/bge-reranker-v2-m3/ | head -10

# 检查 sentence-transformers 或 FlagEmbedding 是否可用
python3 -c "from sentence_transformers import CrossEncoder; print('CrossEncoder OK')" 2>/dev/null || \
python3 -c "from FlagEmbedding import FlagReranker; print('FlagReranker OK')" 2>/dev/null || \
echo "NEED_INSTALL"
```

如果需要安装，在 venv 中安装 `sentence-transformers`（已在 wzh_retrieval 环境中可用，
也可以直接用 conda run -n wzh_retrieval）。

### Phase 1: 编写 rerank 评估脚本

创建 `scripts/run_rerank_eval.py`，功能：
1. 加载 validation 集（同上一轮：20 docs, 100 questions）
2. 对每个问题，先用 hybrid 检索取 top_k 候选（top_k=10）
3. 用 bge-reranker-v2-m3 对候选做 cross-encoder 打分
4. 按 rerank 分数重排，取 top-5
5. 计算指标：Doc R@5, Evi R@5, MRR, EM, Cite Rate, Latency

关键实现：
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("/home/testuser/wzh/models/hf/bge-reranker-v2-m3")

# 对每个 query 的 top-k 候选做 rerank
pairs = [(query, doc_text) for doc_text in candidates]
scores = reranker.predict(pairs)
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:5]
```

### Phase 2: 运行实验

| 实验 | 配置 |
|------|------|
| G | hybrid top_k=10 + bge-reranker-v2-m3 rerank -> top-5 |
| H | hybrid top_k=5 + bge-reranker-v2-m3 rerank -> top-5 |
| I | hybrid top_k=10 + bge-reranker-v2-m3 rerank -> top-3 |

每组记录完整指标。

### Phase 3: 结果汇总

写入 `docs/experiments/2026-07-28_rerank_experiment.md`：

```markdown
# Cross-Encoder Rerank 实验

日期: 2026-07-28
Reranker: bge-reranker-v2-m3 (local, cross-encoder)
检索: hybrid (vector 0.6 + BM25 0.4)
数据集: TAT-DQA joint-v1 validation (20 docs, 100 questions)

## 结果表

| 实验 | 初始 top_k | rerank 后取 | Doc R@5 | Evi R@5 | MRR | EM | Cite | Latency |
|------|-----------|------------|---------|---------|-----|-----|------|---------|
| baseline (no rerank) | 5 | 5 | 0.81 | 0.50 | 0.4132 | 0.24 | 0.48 | 3.5s |
| F-10 (no rerank) | 10 | 10 | 0.85 | 0.53 | 0.4178 | 0.23 | 0.49 | 4.2s |
| G | 10 | 5 | ? | ? | ? | ? | ? | ? |
| H | 5 | 5 | ? | ? | ? | ? | ? | ? |
| I | 10 | 3 | ? | ? | ? | ? | ? | ? |

## 发现
## 阻塞与异常
```

### Phase 4: 提交

```bash
git add docs/experiments/2026-07-28_rerank_experiment.md scripts/run_rerank_eval.py
git commit -m "exp: cross-encoder rerank (bge-reranker-v2-m3) on TAT-DQA validation

Top-k recall + cross-encoder precision: 10->5, 5->5, 10->3.
Local model, no downloads, no test_gold touched."
```

## 停止条件

- reranker 模型文件不存在或加载失败 -> BLOCKED
- 单个实验超时 > 300s -> 跳过，记录 TIMEOUT
- 全部完成 -> 正常结束

## 不要做的事

- 不要下载新模型
- 不要 push
- 不要碰 test split
- 不要修改 RAGService 核心逻辑（rerank 在 eval 脚本中独立实现）
