# 过夜任务：M1 LLM-based 规则抽取原型

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
上一轮 M1 基线实验发现：
- 确定性中文正则基线在英文 TAT-DQA 上抽取规则数 = 0（符合预期）
- OCR 非瓶颈（数字 PDF，字符重叠 99.9%）
- 需要语言/领域适配的抽取方法

本轮目标：用本地 Qwen3-14B (:8004) 做 LLM-based 规则/结构化信息抽取原型，
验证 LLM 能否从 TAT-DQA 英文财务文档中抽取出有意义的结构化条目。

## 约束

- 不得触碰 test_gold / test split
- 不得下载新模型（Qwen3-14B 已在 :8004 运行）
- 不得修改 CUDA、驱动
- 不得修改 src/biz/m1_service.py（这是独立原型脚本）
- 结果写入 docs/experiments/2026-07-28_m1_llm_extraction.md
- 不要 push
- 每个 LLM 调用设置 60s 超时，总实验不超过 30 分钟

## 执行步骤

### Phase 0: 验证 LLM 服务可用

```bash
curl -s http://127.0.0.1:8004/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data'][0]['id'])"
```

### Phase 1: 编写 LLM 抽取脚本

创建 `scripts/m1_llm_extract_prototype.py`，功能：
1. 从 TAT-DQA dev split 取 5 份文档的文本（从 tatdqa_docs_dev.zip 内存读取）
2. 对每份文档，构造 prompt 让 LLM 抽取结构化信息：
   - 公司名、报告期、关键财务指标（收入、利润、资产等）
   - 风险因素（如果有）
   - 会计政策变更（如果有）
3. 调用 http://127.0.0.1:8004/v1/chat/completions
4. 解析 LLM 输出为 JSON 结构
5. 记录：抽取字段数、JSON 解析成功率、延迟、token 用量

Prompt 模板（英文，因为语料是英文）：
```
You are a financial document analyst. Extract structured information from the following text.
Return a JSON object with these fields:
- company_name: string
- reporting_period: string
- key_metrics: array of {name, value, unit}
- risk_factors: array of strings (max 3)
- accounting_changes: array of strings (empty if none)

If a field cannot be determined, use null. Return ONLY valid JSON, no explanation.

Document text (truncated to 3000 chars):
{ text[:3000] }
```

### Phase 2: 运行抽取

对 5 份文档逐一调用，记录结果。
参数：temperature=0, max_tokens=1024, timeout=60s。

### Phase 3: 评估

对每份文档的抽取结果评估：
- JSON 解析是否成功
- company_name 是否与文档 uid 对应的公司名匹配（从 PDF 文件名推断）
- key_metrics 数量是否 > 0
- 总延迟和 token 用量

### Phase 4: 结果汇总

写入 `docs/experiments/2026-07-28_m1_llm_extraction.md`：

```markdown
# M1 LLM-based 规则抽取原型

日期: 2026-07-28
模型: Qwen3-14B-Q4 (local, :8004, 16K context)
数据: TAT-DQA dev split 前 5 份文档
方法: Zero-shot structured extraction via chat completions

## 结果表

| 文档 | 公司 | JSON 成功 | 指标数 | 风险因素 | 延迟 | tokens |
|------|------|----------|--------|---------|------|--------|
| ... | ... | ... | ... | ... | ... | ... |

## 样例输出

（展示 1 份文档的完整抽取 JSON）

## 发现

- LLM 抽取 vs 确定性基线对比
- 结构化输出的可靠性
- 延迟是否可接受（对比 M2 的 3.5s/query）

## 对 M1/M2 闭环的启示

（LLM 抽取能否作为 M1 的可行路径？成本/质量权衡）
```

### Phase 5: 提交

```bash
git add docs/experiments/2026-07-28_m1_llm_extraction.md scripts/m1_llm_extract_prototype.py
git commit -m "exp: M1 LLM-based extraction prototype on TAT-DQA dev

Zero-shot structured extraction with local Qwen3-14B.
5 dev docs, no test_gold, no downloads, no m1_service.py changes."
```

## 停止条件

- LLM 服务不可用 -> BLOCKED
- 连续 3 次调用超时 -> 停止，记录原因
- JSON 解析全部失败 -> 记录并尝试调整 prompt 后重试一次
- 全部完成 -> 正常结束

## 不要做的事

- 不要下载新模型
- 不要 push
- 不要碰 test split
- 不要修改 m1_service.py
- 不要启动额外的模型服务
