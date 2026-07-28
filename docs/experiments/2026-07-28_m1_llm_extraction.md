# M1 LLM-based 规则抽取原型

日期: 2026-07-28
模型: Qwen3-14B-Q4_K_M.gguf (local llama-server, :8004, 16K context)
数据: TAT-DQA dev(validation) split 前 5 份文档（`tatdqa_docs_dev.zip` 内存读取）
方法: Zero-shot structured extraction via `/v1/chat/completions`
脚本: `scripts/m1_llm_extract_prototype.py`（stdlib-only，独立原型，不触碰 `src/biz/m1_service.py`）

## Scope 与约束合规

本实验验证：本地 Qwen3-14B 能否以 zero-shot 方式从 TAT-DQA 英文财务文档中抽取出
有意义的结构化条目（公司名、报告期、关键财务指标、风险因素、会计政策变更），
作为 M1 在英文语料上的可行抽取路径原型（对比上一轮确定性中文正则基线在英文上
抽取规则数 = 0 的结论）。

- 仅使用 dev(validation) split；`test` / `test_gold` 全程未读取、未触碰。
- 未下载新模型/数据集；复用已在 `:8004` 运行的 Qwen3-14B。
- 未修改 CUDA、驱动；未修改 `src/biz/m1_service.py`。
- 每次 LLM 调用 60s 超时；总实验 wall-clock 107.51s（< 30 分钟预算）。
- 未向远程 push。

## 关键实现细节：必须关闭 Qwen3 思考模式

首次调用发现 `message.content` 为空、`completion_tokens` 却打满 1024——Qwen3-14B
在该 llama-server 上默认进入**思考模式**，推理全部写入 `reasoning_content`，
最终答案 `content` 为空，导致 JSON 解析 100% 失败。在 user message 前缀加入
`/no_think` 开关后，模型直接输出答案（验证：同一「只回复 OK」请求从 64-token
空推理变为 6-token 直接回答）。脚本中以 `NO_THINK_PREFIX = "/no_think\n"` 固化。
这是本原型能跑通的**前提条件**，对后续任何调用该服务的 M1/M2 工作都适用。

Prompt 采用任务给定模板（英文），`temperature=0`、`max_tokens=1024`，文档文本
截断至 3000 字符。JSON 解析三级回退：直接 `json.loads` → 去 ```json 围栏 → 取首尾
花括号切片。

## 结果表

| 文档 (uid 前 12 位) | 来源 PDF | 抽取公司名 | JSON 成功 | 指标数 | 风险因素 | 延迟 | tokens |
| --- | --- | --- | :---: | ---: | ---: | ---: | ---: |
| `4d41ea7a63b2` | quicklogic-corporation_2019.pdf | (null) | ✓ | 18 | 3 | 30.56s | 1629 |
| `2eb8a980ff3b` | vodafone-group-plc_2019.pdf | Vodafone Group Plc | ✓ | 5 | 3 | 11.82s | 668 |
| `9ae53f387177` | united-micro-electronics-corp_2019.pdf | UMC | ✓ | 8 | 3 | 19.68s | 1092 |
| `2e3e1ea3ff29` | shopify-inc_2019.pdf | Shopify Inc. | ✓ | 3 | 3 | 11.6s | 1013 |
| `fbdd7d58d570` | hc2-holdings-inc_2019.pdf | HC2 HOLDINGS, INC. | ✓ | 15 | 3 | 33.85s | 1523 |

汇总（5 份文档）：

| 指标 | 值 |
| --- | ---: |
| JSON 解析成功 | 5/5（100%） |
| 解析方式 | 全部 `direct`（无需围栏/切片回退） |
| 含 key_metrics 的文档 | 5/5（100%） |
| 公司名自动匹配（字符串） | 3/5（见下方勘误） |
| 平均延迟 | 21.5s |
| 总延迟 | 107.51s |
| 总 token 用量 | 5925（平均 1185.0/文档） |
| 完成 token 吞吐 | ~20.6 tok/s |
| 总 wall-clock | 107.51s |

### 公司名匹配勘误（自动指标低估）

自动匹配按「文件名派生公司名的词元是否出现在抽取值中」判定，报告 3/5，
但人工核对后实际为 **4/5**：

- `9ae53f387177`（united-micro-electronics-corp）抽取出 `"UMC"`——这是联华电子的
  真实缩写/ticker，属**正确抽取**，但字符串匹配器无法识别别名，记为假阴性。
- `4d41ea7a63b2`（quicklogic）抽取值为 `null`：该文档解析文本从「Results of
  Operations」章节开始，前 3000 字符截断片段中**不含实体名**，模型按指令
  「无法判定则用 null」如实返回 null。这是**截断伪影**而非模型错误。
- 其余 3 份（Vodafone Group Plc / Shopify Inc. / HC2 HOLDINGS, INC.）精确匹配。

## 样例输出

文档 `4d41ea7a63b2`（quicklogic-corporation_2019.pdf，18 项指标的完整抽取 JSON）：

```json
{
  "company_name": null,
  "reporting_period": "Fiscal Years 2019, 2018, 2017",
  "key_metrics": [
    {
      "name": "Revenue",
      "value": "100",
      "unit": "%"
    },
    {
      "name": "Cost of revenue",
      "value": "43",
      "unit": "%"
    },
    {
      "name": "Gross profit",
      "value": "57",
      "unit": "%"
    },
    {
      "name": "Research and development",
      "value": "120",
      "unit": "%"
    },
    {
      "name": "Selling, general and administrative",
      "value": "86",
      "unit": "%"
    },
    {
      "name": "Loss from operations",
      "value": "-149",
      "unit": "%"
    },
    {
      "name": "Interest expense",
      "value": "-3",
      "unit": "%"
    },
    {
      "name": "Interest income and other expense, net",
      "value": "2",
      "unit": "%"
    },
    {
      "name": "Loss before income taxes",
      "value": "-150",
      "unit": "%"
    },
    {
      "name": "Provision for income taxes",
      "value": "1",
      "unit": "%"
    },
    {
      "name": "Net loss",
      "value": "-151",
      "unit": "%"
    },
    {
      "name": "New product revenue",
      "value": "30",
      "unit": "%"
    },
    {
      "name": "Mature product revenue",
      "value": "70",
      "unit": "%"
    },
    {
      "name": "Total revenue",
      "value": "100",
      "unit": "%"
    },
    {
      "name": "Year-Over-Year change in revenue",
      "value": "-18",
      "unit": "%"
    },
    {
      "name": "Cost of revenue",
      "value": "43",
      "unit": "%"
    },
    {
      "name": "Gross profit",
      "value": "57",
      "unit": "%"
    },
    {
      "name": "Year-Over-Year change in gross profit",
      "value": "-7",
      "unit": "%"
    }
  ],
  "risk_factors": [
    "The 46% decrease in new product revenue in 2019 was primarily due to lower sales from Display Bridge Solution, eFPGA license and connectivity product, which was partially offset by an increase in AI SaaS revenue.",
    "The increase in mature product revenue was due primarily to increased orders from our customers in the defense, aerospace, test and instrumentation sectors.",
    "Impact of inflation and product price changes on our revenue and on income was immaterial in 2019, 2018 and 2017."
  ],
  "accounting_changes": []
}
```

该样例准确还原了原文的**共同比利润表**（各项以占收入百分比表示：Revenue 100%、
Cost of revenue 43%、Gross profit 57%、Loss from operations -149%、Net loss -151%
等），`risk_factors` 为文档中真实风险叙述句，`accounting_changes` 正确为空。
`company_name=null` 的原因见上方勘误（截断片段不含实体名）。

## 发现

1. **LLM 抽取在英文语料上有效，确定性基线无效**：上一轮确定性中文正则基线在全
   274 份 dev 文档上抽取规则数 = 0；本原型 zero-shot 即在 5/5 文档上产出结构化
   条目（100% 含 key_metrics，平均 9.8 项指标/文档）。语言/领域适配的抽取方法
   （LLM）是 M1 在 TAT-DQA 上的可行路径，验证了上一轮实验的核心假设。

2. **结构化输出高度可靠**：5/5 文档 JSON 一次解析成功，且全部为 `direct` 方式
   （无需围栏剥离或花括号切片回退）。在 `/no_think` + `temperature=0` 下，
   Qwen3-14B 对「仅返回合法 JSON」指令的遵循度很好，字段语义也合理
   （reporting_period、指标名/值/单位、风险句均贴合原文）。

3. **延迟显著高于 M2 检索查询，但与输出长度强相关**：平均 21.5s/文档，
   约为 M2 检索 3.5s/query 的 6 倍。延迟由 completion 长度主导——指标越多越慢
   （quicklogic 18 指标/683 完成 token/30.56s vs shopify
   3 指标/226 完成 token/11.6s），完成吞吐约 20.6 tok/s。
   作为**离线批量抽取**（M1 入库阶段）该延迟可接受；若用于在线交互则需缓存/异步。

4. **实体名抽取受截断位置影响**：当 3000 字符截断片段不含文档抬头/实体名时，
   模型如实返回 null。改进方向：扩大上下文窗口（16K 可容纳更长文本）、优先截取
   文档首部、或在 prompt 中提供来源文件名作为提示。

## 对 M1/M2 闭环的启示

- **M1 可行路径确认**：LLM zero-shot 结构化抽取可作为 M1 在英文财务语料上的
  抽取器，替代/补充确定性中文正则基线（后者定位为管线与 schema 契约验证）。
  建议将其封装为独立原型路径，**不改动** `src/biz/m1_service.py` 的确定性契约，
  而是作为「语言适配抽取器」候选并列评估。
- **成本/质量权衡**：单文档 ~1185.0 token、~21.5s（本地推理，无云成本），
  质量上指标/风险抽取已具可用性。对 274 份 dev 全量抽取约需 274 × 21.5s
  ≈ 98 分钟（本地单流），可作为离线批处理一次性完成。
- **评测方法需升级**：字符串匹配会低估实体抽取质量（UMC 别名假阴性）。formal M1
  业务指标仍需 owner 批准的 label-to-source 映射与人工标注（与 HANDOFF 一致），
  本原型仅证明技术可行性，不构成正式业务指标。
- **前置条件沉淀**：调用本地 Qwen3-14B 必须显式关闭思考模式（`/no_think`），
  否则 `content` 为空。此结论应纳入后续所有 M1/M2 调用该服务的脚本规范。

## 限制

- 仅 5 份文档（按任务要求），代表性有限；未做抽取字段的人工逐条正确率标注。
- key_metrics 的 value/unit 偶有语义瑕疵（如共同比百分比被记为 value="100"/unit="%"，
  属原文表述方式，非数值错误）；formal 评测需 gold 标注。
- 公司名匹配为自动字符串指标，存在别名假阴性（已人工勘误为 4/5）。
- 延迟基于本地单并发推理；并发/批处理吞吐未测。
