> 状态: 完成 | 更新: 2026-08-12 | 取代/被取代: 无

# dify 甲方规则 docx 术语挖掘 (S3②, Q2 同款确定性流程)

## 输入
dify/ 5 份甲方业务规则 docx (七月 Dify 原型遗留; 本机 gitignored, 已 scp 至 GB10 同名目录):
估值数据催收 / 完整性监控与一键估值 / 电子对账 / 管理人估值进度查询 / 自定义对账。
性质判定: **估值工作流业务规则文档**, 非对账单字段映射表。

## 方法 (无 LLM)
scripts/mine_dify_rule_terms.py: docx 表格+段落 → CJK 术语抽取 (去停用词) →
与 config/m1_table_schema.json 214 词表确定性比对 (精确/双向子串 len>=3/碰撞检查)。

## 结果
- covered=4: 资金账号/产品名称/账号/名称 (schema 已含)
- candidates=28: 多为自由文本碎片; 真实可用 3 个
- unknown=978: 工作流词汇 (交易数据/内部金额/外部金额/估值表状态/账套编号…)

## 补词 (3, 均证券持仓明细表, 无碰撞)
| 新 synonym | standard | 依据 |
|---|---|---|
| 交易日 | 交易日期 | 子串+语义唯一 |
| 下层基金净值 | 基金净值 | FOF 底层净值变体 |
| 手续费支出 | 手续费 | 支出项变体 |

## 验证
scenario1 回归门禁 15 pass/0 warn (补词后复跑); schema 相关 pytest 138 passed。
**诚实 delta=0** (现存语料无新词命中) — 价值=未来估值表类文档到达时的映射强化,
与 Q2 别名资产同逻辑。

## 复用
甲方若提供真实字段规则表 → 放入 dify/ 重跑本脚本 → 按 candidate 清单补词 → 门禁。
报告 JSON: logs/graph/dify_rule_terms_report.json (不入 git)。
