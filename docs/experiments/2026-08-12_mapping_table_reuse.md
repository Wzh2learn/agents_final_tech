# 甲方映射表价值再挖掘（Q2）

> 日期: 2026-08-12 | 原则: 确定性优先, LLM 不参与; 门禁不过即回滚
> 源数据: 信息映射表 xlsx (673 数据行 × 6 列: 基金名称/证券代码/证券名称/交易市场/持仓/发行公司)

## 产出资产
- `config/product_aliases.json` — 确定性别名表: products=56 (基金名称 + NFKC 归一化键 + 持仓证券代码表) / securities=234 (代码→名称/发行公司/市场/持有者数) / issuers=61 (机构名变体)
- `scripts/build_product_aliases.py` — 重建工具 (xlsx 更新后一键重跑, 原子写)
- `src/biz/m2_service.py` — resolve_product_query(): 产品名解析三级链 **精确 → 别名表确定性解析 → LIKE 启发式兜底**
- `tests/test_m2_product_aliases.py` — 12 新测试 (归一化/三态解析/三级链 mock/缺文件降级/真实文件形状)

## ① 产品别名确定化 — delta 报告
- 测试: 新增 12 + compare 存量 33 = **45 passed** (test_m2_compare_fuzzy/test_m2_compare 零回归)
- 活体验证 (进程内直连生产 PG, 不经 :5050, 未重启): resolve("MM-A一号") → `alias-exact` ✓; resolve("嘉兴民安") → `unchanged` → LIKE → chunks=6 持仓行=2 ✓ (与 08-09 修复口径一致)
- **诚实 delta: 当前语料命中变化 = 0** — xlsx 56 个基金名称 (MM-A/MR-A/MY-A 系列) 与 RAG 现存 4 个 product_name 无交集。机制已通电并测试, 价值在甲方后续语料 (多期对账单/新产品) 进来时确定性生效
- **生效条件**: 代码在下次 :5050 重启窗口载入 (与延迟 a+b 合并)

## ② 字段规则差集扫描 — 结果: 0 缺口
xlsx 6 个列名逐一对照 config/m1_table_schema.json synonyms:
基金名称→产品名称 ✓ / 证券代码 ✓ / 证券名称 ✓ / 交易市场 ✓ / 持仓→持仓数量 ✓ (synonym 已含"持仓") / 发行公司→基金公司 ✓
**差集为空, 无需 schema 变更**; 回归门禁 --quick 复跑 12 pass/0 warn 确认零扰动。
机构名变体 (61 个发行公司) 属"值"而非"列名", 不进 schema synonyms, 已作为 issuers 清单入别名表, 供未来实体消歧 (如 QA 问"嘉合基金的产品"时做发行公司→产品反查)。

## 后续触发点（台账）
- 甲方多期数据进来后: 重跑 build_product_aliases.py, compare 链自动受益
- issuers 反查接入 M2 QA = 待甲方反馈是否需要"按发行公司聚合"类问题
