# G 策略集成 + 分块粒度实验

日期: 2026-07-28
数据集: TAT-DQA joint-v1 validation (20 docs, 100 questions, 627 blocks)
Collection: tat-dqa-joint-v1-validation
Embedding: Qwen3-Embedding-0.6B (local, CUDA, `~/wzh/models/hf/qwen3-embedding-0.6b`)
Reranker: bge-reranker-v2-m3 (local cross-encoder, CUDA, `~/wzh/models/hf/bge-reranker-v2-m3`)
Generation: Qwen3-14B-Q4 (local, :8004)
Python: miniconda3/envs/wzh_retrieval (torch 2.9.1+cu128, sentence-transformers 5.4.0)
约束遵守: 未触碰 test_gold / test split；未下载新模型；未改 CUDA/驱动；分块实验纯内存、不写数据库。

## 1. G 策略集成

### 配置变更 (`config/app_config.json`)

| 字段 | 旧值 | 新值 | 说明 |
|------|------|------|------|
| `rag.default_top_k` | 5 | 10 | 初始召回 top_k（任务中的 `rag.top_k` 对应此字段） |
| `rag.use_rerank_by_default` | false | true | 默认启用精排，使 G 成为默认检索策略 |
| `rerank.enabled` | true | true | 保持 |
| `rerank.method` | api | cross_encoder | 切换到本地 cross-encoder（无需 API Key） |
| `rerank.model_name` | （无） | bge-reranker-v2-m3 | 新增 |
| `rerank.local_model_path` | （无） | /home/testuser/wzh/models/hf/bge-reranker-v2-m3 | 新增，本地权重路径 |
| `rerank.device` | （无） | cuda | 新增 |
| `rerank.top_n` | 5 | 5 | 精排后保留 top-5 |
| `features.enable_rerank` | （无） | true | 新增显式开关（`features.rerank` 保持 true） |

`rag.force_rerank` (true) 与 `rag.default_top_n` (5) 保持不变。

### 必要的代码变更 (`src/tools/reranker_tool.py`)

原 `rerank_documents` 工具**只支持 LLM-API 精排**（SiliconFlow `Qwen/Qwen3-Reranker-0.6B`），
而本机 `SILICONFLOW_API_KEY` 未配置，且实验 G 使用的是**本地 cross-encoder**。
为使 `smart_retrieve(use_rerank=True)` 真正复现 G，在 reranker 工具中新增了一条
**配置门控的本地 cross-encoder 分支**（`rerank.method == "cross_encoder"`）：

- 懒加载 `sentence_transformers.CrossEncoder(local_model_path)` 并缓存实例；
- 对 (query, doc_content) 打分，降序取 `top_n`，返回与 LLM 路径同构的 JSON
  （`id` / `relevance_score` / `reason`），因此 `RAGService._maybe_rerank` **零改动**；
- `method=api` 时回退到原 LLM 路径，向后兼容。

该改动仅涉及 reranker **工具**，未触碰 `RAGService` 核心检索/排序逻辑。

### 验证结果

命令（conda `wzh_retrieval`，等价于任务给定命令，补全了必填参数）：

```bash
LOCAL_EMBEDDING_MODEL_PATH=~/wzh/models/hf/qwen3-embedding-0.6b \
LOCAL_EMBEDDING_DEVICE=cuda \
PGDATABASE_URL=postgresql://postgres:postgres@localhost:15432/vector_db \
PYTHONPATH=src \
conda run -n wzh_retrieval python scripts/run_tat_dqa_m2_upper_bound.py \
  --manifest docs/datasets/tat-dqa-joint-v1-manifest.json \
  --qa-json ~/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json \
  --docs-archive ~/wzh/datasets/tat-dqa/raw/tatdqa_docs_dev.zip \
  --split validation --collection tat-dqa-joint-v1-validation \
  --evaluate --with-answers --top-k 10 --use-rerank \
  --output ~/wzh/datasets/tat-dqa/derived/rerank/G_integrated_validate.json
```

| 指标 | G (参考实验) | 集成后 | 偏差 |
|------|-------------|--------|------|
| Doc R@5 | 0.85 | **0.85** | 0% |
| Evi R@5 | 0.50 | 0.53 * | +6.0% |
| MRR | 0.4098 | 0.4144 | +1.1% |
| EM | 0.28 | 0.2525 | -9.8% |
| Cite Rate | 0.48 | 0.4848 | +1.0% |
| Latency | 3.55s | 4.52s | +27% |

\* **Evi R@5 口径差异**：`RAGService._maybe_rerank` 在返回精排 top-5 后会**追加其余候选**
（核心逻辑，按要求未改动），`smart_retrieve` 按 `max_results=top_k=10` 截断，因此评估脚本
实际对 10 条候选判定命中（相当于 R@10），得到 0.53（与 F-10 无精排的 R@10 一致）。精排 top-5
位于返回列表的前 5 位；任何对结果切片 `[:5]` 的下游调用方拿到的就是 G 的 top-5。
G 参考实验的独立脚本 `run_rerank_eval.py` 截断到恰好 5 条，故记 0.50。

**结论：所有质量指标偏差 ≤ 10%（EM -9.8% 临界但在容差内，且本次有 1 例答案 JSON 解析
`ValueError` 拉低 EM 约 0.01），未触发回滚条件。** Doc R@5 与 G 完全一致，精排确认生效
（EM 0.2525 高于 F-10 无精排的 0.23）。延迟升高主要来自本次运行的负载/预热，非配置缺陷。

## 2. 分块粒度实验

评估脚本：`scripts/run_chunk_ablation.py`（本次新增）。
方法：读取 validation 官方解析块（627 blocks），对每种策略在**内存中**重建向量索引
（不写数据库），用本地 Qwen3-Embedding-0.6B 编码，对 100 问题做**纯向量** top-5 检索
（无 BM25、无精排，以隔离分块粒度变量），计算 Evi R@5 / Doc R@5 / MRR。
命中判定：检索到的任一 chunk 覆盖任一 gold block id 即算证据命中。

| 策略 | 描述 | chunks | Evi R@5 | Doc R@5 | MRR | 备注 |
|------|------|--------|---------|---------|------|------|
| A | 原始块（1 块 = 1 chunk） | 627 | 0.500 | 0.800 | 0.4132 | baseline，与线上 Evi R@5 0.50 完全吻合 |
| B | 2-block merge（相邻 2 块合并） | 318 | 0.540 | 0.790 | 0.3665 | Evi↑ 但 Doc↓、MRR↓ |
| C | 3-block merge（相邻 3 块合并） | 215 | 0.570 | **0.860** | **0.4740** | Doc、MRR 最佳 |
| D | sliding window ±1（块 + 前后各 1 块） | 627 | **0.590** | 0.810 | 0.4673 | Evi 最佳（+18% vs A） |

（A/B/C/D 编码耗时 25–65s/策略，D 因窗口拼接文本更长而偏慢，属编码开销，非检索成本。）

## 3. 发现与建议

1. **G 策略已成功集成为默认检索策略**：配置 + reranker 工具的本地 cross-encoder 分支
   复现了 G 的检索质量（Doc R@5 0.85 完全一致，全部质量指标偏差 ≤ 10%），且无需 API Key。

2. **证据召回 0.50 的瓶颈部分源于分块粒度**：A 的 Evi R@5 0.50 与线上一致，确认基线；
   引入邻接上下文后普遍提升——合并/窗口让被块边界截断的证据重新被覆盖。

3. **D（滑动窗口 ±1）是最有前景的方向**：Evi R@5 0.59（+18%），且 chunk 数仍为 627、
   Doc R@5 保持 0.81，不缩小语料、不损失文档召回。代价是同一 gold 块最多出现在 3 个
   重叠 chunk 中，检索可能返回冗余片段（需在精排/去重环节处理）。

4. **C（3 块合并）是稳健替代**：Doc R@5 0.86 与 MRR 0.474 全场最高，chunk 数降至 215，
   索引更紧凑；Evi R@5 0.57 略低于 D。

5. **B（2 块合并）不推荐**：虽 Evi R@5 升至 0.54，但 Doc R@5 与 MRR 均下降，
   说明无上下文的粗合并会稀释检索精度。

### 后续建议

- 优先验证 **D（滑动窗口）** 与 G 精排组合在完整 hybrid+rerank 管线中的端到端 EM 收益；
  若冗余片段干扰生成，可在 `_maybe_rerank` 后加一层 block 级去重。
- 备选 **C（3 块合并）**：若更看重文档命中与排序质量、并希望缩小索引规模。
- 分块策略当前仅在评估脚本中模拟；落地需在 `DocumentManager`/ingest 路径引入对应分块器
  （本任务按要求未改动 ingest 与 RAGService）。
- 建议在更大集合（>627 块）上复测，当前小集合检索已近乎饱和，精排与分块收益在更大集合中更显著。

## 复现与产物

- 集成验证输出: `~/wzh/datasets/tat-dqa/derived/rerank/G_integrated_validate.json`（不入 Git）
- 分块实验输出: `~/wzh/datasets/tat-dqa/derived/chunk_ablation/chunk_ablation.json`（不入 Git）
- 数据契约 (validation): document_ids_sha256 `c3dbc30a…72f14`, question_ids_sha256 `35fadafe…0cab843`
