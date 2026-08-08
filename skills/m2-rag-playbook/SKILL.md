---
name: m2-rag-playbook
description: M2 RAG 问答失败模式手册（检索为空/数值缺失/多轮追问/脱敏掩码/跨文档聚合的对策与验证）。m2-qa agent 或任何经 jinrong-rag knowledge_search 回答对账单问题的 agent 必读；答案质量回归、sources 为空、出现编造内容时使用。
---

# M2 RAG Playbook（失败模式 → 对策 → 验证）

> 状态: 活跃（2026-08-09 P3 沉淀）| 配套契约: skills/agent-prompt-contracts（四条已验证 prompt 契约）
> 配套 eval: bash scripts/run_eval.sh（M2 确定性检验 16 题 + AI judge 四维）

## 失败模式 1：检索为空 / 命中文档不对

- 症状: knowledge_search 返回 0 条，或 top 结果与问题实体不符
- 对策:
  1. **首查必须 verbatim**：用用户完整原句检索，保留每个字段词（资产总值/币种/市值/总资产），禁止把查询缩短成实体名（verbatim 首查是已验证契约，缩短是 14/15→15/15 修复的关键）
  2. 仍为空 → 一次定向补查：实体名 + 字段关键词（只补查一次，不循环）
  3. 两次都空 → 明确拒答（见拒答规范），禁止编造
- 验证: eval fixture 的 source_required 检查 + judge faithfulness ≥4

## 失败模式 2：数值字段缺失（文档有该字段但 top-k 没带出）

- 症状: 检索到正确样本但缺所问字段值
- 对策: 一次定向补查（实体 + 字段名），命中后引用该 chunk 的 样本/表/字段 三元组
- 验证: exact_numeric check（千分位容差，脱敏掩码 * 为通配）

## 失败模式 3：多轮追问（"其中...占多少" / "它的..." / "呢？"）

- 症状: 裸追问缺实体上下文，检索漂移到错误文档
- 对策: 检索前把追问改写为含实体的独立查询（"其中证券市值占多少" → "嘉兴民安的证券市值"）；:5050 直连路已有 conversation-aware retrieval，agent 路必须自己在查询里带上历史实体
- 验证: eval adv_multiturn 题（judge 检索用全部 turns 拼接模拟改写结果）

## 失败模式 4：脱敏掩码补全幻觉（P2 发现, 系统性风险）

- 症状: chunk 值为 `博时****混合A`，答案却输出完整名称（如"博时新策略混合A"）——用训练知识补全脱敏位
- 对策: **检索值带 * 掩码时，答案必须原样输出掩码形式**；禁止补全、猜测、还原任何被 * 替代的内容。脱敏是合规要求，补全即数据泄漏。
- 验证: judge faithfulness 维度；q03/q07 为回归哨兵

## 失败模式 5：跨文档聚合（"一共几份" / "哪些样本有 X"）

- 症状: 计数/枚举受 top_k 截断（嘉合 8 份只能检回 ~5）
- 对策: 答案限定"检索范围内"措辞，不声称完备计数；如用户需要精确计数，说明受检索窗口限制
- 验证: eval adv_cross_doc（契约只校验来源检索命中，计数局限已文档化）

## 拒答规范

- 无证据时: `sources: []` + 答案明说"根据现有对账单数据，未找到相关信息"
- 禁止: 用模糊相关文档硬凑答案；对库外实体（不存在的基金/产品）编造持仓

## 输出契约（机器解析, 不可省略）

m2-qa 的最终回复必须是单个 JSON: `{"answer": "...", "sources": [{"sample_id","table_name","field"}]}`。
sources 在有证据时不得为空；sample_id/table/field 用检索 chunk 原值。

## 验证方式（改动本 playbook 或 m2-qa prompt 后必跑）

```bash
bash scripts/run_eval.sh   # M2 确定性 16/16 + judge 均分对比 docs/experiments/2026-08-08_eval_baseline.md
```
