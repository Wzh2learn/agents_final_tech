# D-A 裁定证据附件：当前 corpus 的 canonical 参考可行性（零模型实测，2026-09-24）

> 状态: 决策支持件（Loop D，只读实测于 GB10 production 数据）| 零模型调用 | 服务决策包 D-A
> 目的: 把 D-A 的三个选项从「独立性风险」层面降到「可行性」层面，用实测重叠度说话。

## 1 实测（GB10 production，只读）

| 量 | 值 |
|---|---|
| `config/m1_table_schema.json` 的 standard 字段数 | 70（中文甲方对账单字段） |
| drift_v0 观测表头去重数 | 1 542（英文 TAT-QA 派生表头） |
| 二者交集 | **0** |
| injection_map 是否含 canonical 字段 | 否（键集 = col/injected/original/row/seed_component/source_key/type/uid/variant） |
| drift canonical 词汇是否存在于仓内 | 不存在；唯一可得词汇 = 归一化原表头自 canonical（冻结 t2 口径） |

## 2 结论

1. **选项 2（管线映射配置作复核参考）不可行**，而非仅独立性存疑：配置描述甲方对账单 schema，
   与当前 corpus 表头交集为 0，无法对任何样本给出 canonical 判定。该选项自决策包撤回，附本实测。
2. **自 canonical 作复核参考不独立**：map_to 判定将退化为对表头归一化的确认，与可见性口径同义反复，
   不满足「label_ledger 独立复核」要求。
3. **可行路径仅剩两条**：
   - (1) 用户提供官方 TAT-QA schema 摘录（论文/网站表结构节，作为带出处的只读参考件入仓）；
     裁定后 R1/R2 以两个独立载体据此判 map_to/skip/hold，装配器→派生→合同链已端到端测通；
   - (3) 将当前 corpus 的 label 复核延后到 P1-future 包（FinQA schema 草案已审计备妥），
     当前 corpus 的 Phase 1a 维持停门。
4. 本件不改变任何门、不授权任何下载、不产生任何标签。
