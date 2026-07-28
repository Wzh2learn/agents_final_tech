# 任务：集成 G 策略 + 分块粒度实验

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
上一轮 rerank 实验确认 G（top_k=10 + bge-reranker-v2-m3 → top-5）是最优策略：
- Doc R@5: 0.85, EM: 0.28, 延迟 3.55s（与 baseline 持平）
- 证据块召回 0.50 是主要瓶颈（分块粒度问题）

本轮两个目标：
1. 将 G 策略写入项目配置作为默认检索策略
2. 实验分块粒度对证据块召回的影响

## 约束

- 不得触碰 test_gold / test split
- 不得下载新模型
- 不得修改 CUDA、驱动
- 结果写入 docs/experiments/2026-07-28_chunking_and_integration.md
- 不要 push
- 修改配置和代码前先 git stash 或确认 worktree 干净

## Phase 1: 集成 G 策略到默认配置

修改 `config/app_config.json`：
- `rag.top_k`: 5 -> 10（初始召回）
- `rerank.enabled`: true
- `rerank.model_name`: 指向本地 bge-reranker-v2-m3 路径
- `rerank.top_n`: 5（精排后保留）
- `features.enable_rerank`: true

注意：不要改 RAGService 核心代码逻辑，只改配置。
如果 rerank 配置需要新增字段（如 local_model_path），可以加。

验证：修改后运行一次 eval 确认指标与实验 G 一致。

```bash
cd ~/wzh/projects/agents_final_tech
source venv/bin/activate
python3 scripts/run_tat_dqa_m2_upper_bound.py --split validation --limit 20 --top-k 10 --use-rerank
```

## Phase 2: 分块粒度实验

当前分块：父块 2000 字符 / 子块 500 字符。
证据块召回 0.50 的可能原因：
- 子块太小，证据跨块被截断
- 子块太大，检索精度下降

实验设计（在 eval 脚本中独立实现，不改 RAGService）：

创建 `scripts/run_chunk_ablation.py`：
1. 读取 validation 集的官方解析块（627 blocks）
2. 模拟不同分块策略对检索的影响：
   - 策略 A：原始块（不合并，当前状态）
   - 策略 B：相邻块合并（2 块合并为一个 chunk）
   - 策略 C：相邻块合并（3 块合并）
   - 策略 D：滑动窗口（块 + 前后各 1 块作为上下文）
3. 对每种策略，重新构建向量索引（内存中，不写数据库）
4. 运行 100 问题检索，计算 Evi R@5

注意：这需要 embedding 模型。使用 conda 环境 wzh_retrieval：
```bash
conda run -n wzh_retrieval python3 scripts/run_chunk_ablation.py
```

如果 embedding 不可用或超时，记录 BLOCKED 并跳过。

## Phase 3: 结果汇总

写入 `docs/experiments/2026-07-28_chunking_and_integration.md`：

```markdown
# G 策略集成 + 分块粒度实验

日期: 2026-07-28

## 1. G 策略集成

配置变更：（列出具体改了什么）
验证结果：（指标是否与实验 G 一致）

## 2. 分块粒度实验

| 策略 | 描述 | Evi R@5 | Doc R@5 | 备注 |
|------|------|---------|---------|------|
| A | 原始块 | 0.50 | 0.85 | baseline |
| B | 2-block merge | ? | ? | |
| C | 3-block merge | ? | ? | |
| D | sliding window ±1 | ? | ? | |

## 3. 发现与建议
```

## Phase 4: 提交

```bash
git add config/app_config.json docs/experiments/2026-07-28_chunking_and_integration.md scripts/run_chunk_ablation.py
git commit -m "feat: integrate G strategy (top_k=10+rerank->5) as default + chunk ablation

Config update: rag.top_k=10, rerank enabled with local bge-reranker-v2-m3.
Chunk granularity experiment: original/2-merge/3-merge/sliding-window.
No test_gold touched, no downloads."
```

## 停止条件

- Phase 1 验证指标偏差 > 10% -> 回滚配置，记录异常
- Phase 2 embedding 不可用 -> BLOCKED，只提交 Phase 1
- 全部完成 -> 正常结束
