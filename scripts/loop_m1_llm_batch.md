# 任务：M1 LLM 批量抽取（全 274 份 dev 文档）

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
上一轮 M1 LLM 原型实验（5 份文档）确认：
- Zero-shot 结构化抽取在英文财务文档上可行（4/5 公司名正确）
- Qwen3-14B 延迟可接受，JSON 解析有 fallback
- 脚本：scripts/m1_llm_extract_prototype.py

本轮目标：扩大到全 274 份 dev 文档，产出完整的 M1 结构化抽取数据集。

## 约束

- 不得触碰 test_gold / test split
- 不得下载新模型（Qwen3-14B 在 :8004）
- 不得修改 src/biz/m1_service.py
- 结果写入 docs/experiments/2026-07-28_m1_llm_batch.md
- 不要 push
- 总时间预算：60 分钟（274 docs × ~13s/doc ≈ 60min）
- 每 50 份文档保存一次中间结果到 /tmp/m1_batch_checkpoint.json

## Phase 0: 验证环境

```bash
cd ~/wzh/projects/agents_final_tech
curl -s http://127.0.0.1:8004/v1/models | head -3
ls ~/wzh/datasets/tat-dqa/raw/tatdqa_docs_dev.zip
```

## Phase 1: 扩展批量脚本

基于 `scripts/m1_llm_extract_prototype.py` 创建 `scripts/m1_llm_batch_extract.py`：
- 处理全 274 份 dev 文档
- 每 50 份保存 checkpoint（断点续传）
- 记录每份文档：uid, company_name, metrics_count, json_success, latency, tokens
- 超时 60s/文档，连续 5 次超时则停止
- 总时间 guard：60 分钟
- 输出汇总 JSON 到 /tmp/m1_batch_results.json

## Phase 2: 运行批量抽取

```bash
python3 scripts/m1_llm_batch_extract.py --limit 274 --checkpoint /tmp/m1_batch_checkpoint.json
```

如果中途超时停止，记录已完成的数量和部分结果。

## Phase 3: 统计分析

对全量结果计算：
- JSON 解析成功率
- 公司名抽取率（非 null）
- 平均 key_metrics 数量
- 平均延迟和 token 用量
- 失败文档列表和原因分类

## Phase 4: 结果汇总

写入 `docs/experiments/2026-07-28_m1_llm_batch.md`：

```markdown
# M1 LLM 批量抽取（全 dev split）

日期: 2026-07-28
模型: Qwen3-14B-Q4 (local, :8004)
数据: TAT-DQA dev split 全 274 份文档

## 汇总统计

| 指标 | 值 |
|------|-----|
| 总文档数 | 274 |
| 成功处理 | ? |
| JSON 解析成功率 | ?% |
| 公司名抽取率 | ?% |
| 平均 metrics 数 | ? |
| 平均延迟 | ?s |
| 总 token 用量 | ? |

## 失败分析

（分类：超时、JSON 解析失败、空输出等）

## 样例输出

（展示 2-3 份代表性文档的抽取 JSON）

## 对 M1/M2 闭环的结论

- LLM 抽取作为 M1 路径的可行性评估
- 成本估算（token/文档 × 274）
- 与确定性基线的互补关系
- 下一步：是否需要 SFT 提升结构化输出质量
```

## Phase 5: 提交

```bash
git add docs/experiments/2026-07-28_m1_llm_batch.md scripts/m1_llm_batch_extract.py
git commit -m "exp: M1 LLM batch extraction on full TAT-DQA dev (274 docs)

Zero-shot structured extraction with local Qwen3-14B.
Full dev split, checkpoint every 50 docs, 60min budget.
No test_gold, no downloads, no m1_service.py changes."
```

## 停止条件

- 60 分钟时间到 -> 保存已有结果，提交部分报告
- 连续 5 次超时 -> 停止，记录原因
- LLM 服务不可用 -> BLOCKED
- 全部完成 -> 正常结束

## 不要做的事

- 不要下载新模型
- 不要 push
- 不要碰 test split
- 不要修改 m1_service.py
- 不要启动额外模型服务
