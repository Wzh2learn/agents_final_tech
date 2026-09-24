# label_ledger 独立复核流程模板（R1/R2/裁决载体与可见性边界，2026-09-24）

> 状态: 流程模板件（Loop D）| 服务决策包 D-A 裁定后的 label 复核启动 | 零模型调用
> 关系: 装配器（research/phase1a_label_ledger_assemble.py）机械强制载体互异与生成者排除；
> 本件把「独立性」在流程层编码：每个载体能看到什么、不能看到什么、裁决记录长什么样。

## 1 载体与可见性边界（独立性操作定义）

| 载体 | 允许看到 | 禁止看到 |
|---|---|---|
| R1（独立复核载体 1） | 源表原表头（source_tables）、D-A 裁定后的 canonical 参考摘录、LABEL_FIELDS 语义说明 | R2 的判定、裁决内容、管线映射结果（m1 map_headers 输出）、injection_map、任何可见性/检出数字 |
| R2（独立复核载体 2） | 同 R1 | 同 R1（另加：R1 的判定） |
| 裁决载体 | R1 与 R2 的分歧行、源表原表头、canonical 参考摘录 | 管线映射结果、injection_map、任何可见性/检出数字 |
| 生成者（规则派生脚本，若采用） | 其派生输入 | 不得担任 R1/R2/裁决（装配器强制） |

理由：管线映射结果与 injection_map 携带系统自身行为与扰动真值；复核载体若可见，
map_to/skip/hold 判定退化为对系统行为的确认而非独立正确性判断（D-A 附件 §2 第 2 条同理）。

## 2 R1 / R2 判定提示模板（占位符于启动时替换）

```text
你是独立复核载体 {CARRIER_ID}。仅依据以下材料对每个 (sample, col) 给出唯一判定：
- 源表原表头清单（附 sample_id 与 uid）；
- canonical 参考摘录：{REFERENCE_EXCERPT_PATH}（sha256 {REFERENCE_SHA256}）；
- 判定语义：map_to = 该列应映射到参考摘录中的某 canonical 字段（给出 target）；
  skip = 该列应被跳过（无对应 canonical 字段）；hold = 信息不足需人工保留。
禁止参考任何管线输出、注入信息或其他载体的判定。
输出 JSON：{"reviewer_id": "{CARRIER_ID}", "template_version": "label-review-v1",
"judgments": [{"sample_id":..., "uid":..., "col":..., "action":..., "target":...}]}
```

## 3 裁决记录模板（仅分歧行）

```json
{"adjudicator_id": "ADJ", "entries": [
  {"sample_id": "...", "col": 0, "action": "...", "target": null,
   "rationale_ref": "<裁决依据出处：参考摘录节号或源表行号>"}
]}
```

裁决必须给出 rationale_ref（装配器对分歧行强制非空）；裁决选择即 gold。

## 4 启动检查单（D-A 裁定后）

1. 参考摘录件入仓并登记 INDEX（带出处与 sha256）；
2. R1/R2/裁决载体按 §1 边界装配输入（脚本生成输入包并记录 sha）；
3. 两判定 + 裁决过装配器 → labels.jsonl；再过派生运行器与合同（组合测试已端到端测通）；
4. 独立 Loop C 审计复核记录（载体边界是否被遵守、裁决 rationale 是否可追溯）；
5. 全程零管线输出可见性留痕：输入包生成脚本只读 source_tables 与参考摘录。
