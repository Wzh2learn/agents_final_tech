# 过夜任务：检索策略单变量对照实验

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
M2 validation 上限已完成（官方解析 JSON，20 文档，100 问题）：
- 文档 Recall@5 = 0.81
- 证据块 Recall@5 = 0.50
- 证据 MRR = 0.4132
- 答案 EM = 0.24
- 正确引用率 = 0.48
- 平均端到端延迟 = 3.079s

现在要做的是：在相同 validation 集上，逐一切换检索策略，对比指标差异。

## 约束（硬性）

- 不得触碰 test_gold / test split 的任何数据
- 不得下载新模型或新数据集
- 不得修改 CUDA、驱动、系统网络
- 不得修改 `src/biz/rag_service.py` 的核心逻辑（只通过配置切换策略）
- 如果某个服务不可用，记录并跳过，不要无限重试
- 所有结果写入 `docs/experiments/2026-07-28_retrieval_ablation.md`
- 原始 PDF、模型输出、日志不进 Git；只提交聚合指标和实验记录

## 执行步骤

### Phase 0: 环境验证（只读）

```bash
cd ~/wzh/projects/agents_final_tech
source venv/bin/activate

# 检查数据库
docker ps --filter "name=pgvector" --format "{{.Names}} {{.Status}}"

# 检查模型服务
curl -s http://127.0.0.1:8004/v1/models | head -5

# 检查 FastAPI 应用
curl -s http://localhost:5000/api/status | head -5

# 检查 embedding 可用性
python3 -c "
import sys; sys.path.insert(0, 'src')
from tools.vector_store import get_vector_store
vs = get_vector_store()
print('Vector store OK:', type(vs))
"
```

如果任何关键服务不可用，在实验记录中标注 `BLOCKED: <原因>` 并停止对应阶段。

### Phase 1: 确认基线可复现

运行已有的上限脚本，确认结果与 HANDOFF 记录一致：

```bash
python3 scripts/run_tat_dqa_m2_upper_bound.py --split validation --limit 20
```

记录输出指标。如果与 HANDOFF 偏差 > 5%，标注异常并检查原因。

### Phase 2: 单变量对照

在 `config/app_config.json` 中切换 `rag.strategies` 配置，逐一运行：

| 实验编号 | 变量 | 配置 |
|---------|------|------|
| A | 纯向量 | 所有问题类型 -> vector |
| B | 纯 BM25 | 所有问题类型 -> bm25 |
| C | 混合（默认） | 保持现有 7 类映射 |
| D | 混合 + Rerank 关闭 | features.enable_rerank = false |
| E | 混合 + Rerank 开启 | features.enable_rerank = true |
| F | Top-K 变化 | rag.top_k = 3 vs 5 vs 10 |

每组实验：
1. 用 python3 脚本修改配置（不用手动编辑）
2. 运行 eval 脚本
3. 记录指标到实验文件
4. 恢复配置到默认值

### Phase 3: 结果汇总

在 `docs/experiments/2026-07-28_retrieval_ablation.md` 中写入：

```markdown
# 检索策略单变量对照实验

日期: 2026-07-28
数据集: TAT-DQA joint-v1 validation (20 docs, 100 questions)
Embedding: Qwen3-Embedding-0.6B (SiliconFlow)
Generation: Qwen3-14B-Q4 (local, :8004)

## 结果表

| 实验 | 策略 | Doc R@5 | Evi R@5 | MRR | EM | Cite Rate | Latency |
|------|------|---------|---------|-----|-----|-----------|---------| 
| baseline | hybrid (default) | ... | ... | ... | ... | ... | ... |
| A | vector only | ... | ... | ... | ... | ... | ... |
| B | bm25 only | ... | ... | ... | ... | ... | ... |
| D | hybrid no-rerank | ... | ... | ... | ... | ... | ... |
| E | hybrid + rerank | ... | ... | ... | ... | ... | ... |
| F-3 | hybrid top_k=3 | ... | ... | ... | ... | ... | ... |
| F-10 | hybrid top_k=10 | ... | ... | ... | ... | ... | ... |

## 发现

（由执行者填写关键发现）

## 阻塞与异常

（记录任何跳过或异常）
```

### Phase 4: 提交

```bash
git add docs/experiments/2026-07-28_retrieval_ablation.md
git commit -m "exp: retrieval strategy ablation on TAT-DQA validation

Single-variable comparison: vector/bm25/hybrid/rerank/top-k
on frozen joint-v1 validation (20 docs, 100 questions).
No test_gold data touched. No model or dataset downloads."
```

不要 push（等本机确认后统一推）。

## 停止条件

- 所有 Phase 完成 -> 正常结束
- Phase 0 发现关键服务不可用且无法恢复 -> 记录 BLOCKED 后停止
- 单个实验超时（> 10 分钟）-> 跳过该实验，记录 TIMEOUT
- 连续 3 个实验失败 -> 停止，记录原因

## 不要做的事

- 不要启动 LoRA/QLoRA 微调
- 不要下载 PubTables-1M、FinTabNet、FinQA 等候选数据集
- 不要尝试多 Agent 编排
- 不要修改 test split 数据
- 不要 push 到远程仓库
- 不要修改 .env 或提交凭证
