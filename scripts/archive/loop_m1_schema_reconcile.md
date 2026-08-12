# 任务：M1 扩 schema + 勾稽校验（救回 KV 报告体 + 抓静默错配）

## 背景
GB10，项目 `~/wzh/projects/agents_final_tech`。上一轮 m1-statement 纯规则对规整网格表
命中 78-90%，但 (a) boshi 这类"基金名称：x / 净值：x"逐基金 KV 报告体命中 0；(b) 存在泛化
synonym 静默错配（持仓数量←在途数量/配号数量，语义不等价却 unmapped 看不到）。本轮用
**扩 schema + 算术勾稽校验**两处纯规则改进，零模型、零 OCR。

样本 `~/wzh/m1_samples/`（项目外，不入库，报告脱敏）。schema 在同目录 `m1_table_schema.json`。

## 约束
- 样本与 schema 都在 `~/wzh/m1_samples/`，**不进 Git**；报告脱敏；schema 改动以 diff 形式贴进报告。
- 不下载模型/数据集；不调 :8004；不改 src/biz/m1_service.py；不 push；不碰 TAT-DQA / test split。
- 只改 `scripts/m1_statement_parser.py` 与 `~/wzh/m1_samples/m1_table_schema.json`。

## Phase 1 扩 schema（编辑 ~/wzh/m1_samples/m1_table_schema.json，记录 diff）
- `证券持仓明细.fields`：增 `产品名称`(synonyms 基金名称/产品全称/账户名称)；`成本价.synonyms += 参考成本`；`持仓数量.synonyms += 股份余额`。
- 新增第三张表 `资金资产汇总`(grid)：字段 资金余额/资金可用/资产市值/总资产/资产总值/合计金额，各带近义词（资产总值/资产总额/基金资产总额 等）。
- `header_meta_fields += ` 客户姓名/制表/开始日期/结束日期/基金名称/基金代码/基金份额净值/基金资产总额。

## Phase 2 勾稽校验（在 m1_statement_parser.py 加 reconcile(records, header_kv, schema)）
对每样本输出 `{sample, check, expected, actual, pass, note}`：
- 市值勾稽：若同时存在明细"市值"列与汇总"合计金额/资产总值"，比较 |sum(市值)-合计| <= max(0.01, 0.005*合计)。
- 币种一致：明细"币种"列去重应=1，且与表头区币种一致（若有）。
- 日期格式：对账/统计日期匹配 YYYYMMDD 或 YYYY年MM月DD日 等。
- 静默错配嫌疑：映射成功但勾稽失败的样本/列单列（这是把"不可见错配"变"可证伪"的核心）。

## Phase 3 重跑 6 样本，对比扩 schema 前后
表1 命中率前后对比（每样本 headline 表）；表2 勾稽校验结果（每样本每 check）；
列出被勾稽抓出的错配/异常，以及 unmapped 列的变化（哪些因扩 schema 救回、哪些仍 unmapped）。

## Phase 4 报告
`docs/experiments/$(date +%F)_m1_schema_reconcile.md`：扩 schema diff + 前后命中率表 +
勾稽通过率表 + 抓到的错配清单 + 对"列对齐覆盖率/错配率/未知表头冷启动"三个北极星指标的贡献。脱敏。

## Phase 5 提交（不 push）
`git add scripts/m1_statement_parser.py docs/experiments/*_m1_schema_reconcile.md`
commit 信息注明 schema 在项目外、报告含 diff、已脱敏。

## 停止条件
schema JSON 解析失败→回滚该次编辑并记录；勾稽函数异常→try/except 记 mismatch=ERROR 继续；
全完成→正常结束。不要 push、不要碰 TAT-DQA、不要起模型。
