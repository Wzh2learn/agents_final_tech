# M1 Next Iteration: Schema 扩展 + Parser 升级 + 工作台改造

**日期**: 2026-07-29
**状态**: 完成
**前序**: Phase 1 (evidence-verifier bash allow) 已完成; two-hop BLOCKED (16K context)

---

## Phase 2: Schema + Parser

### 2.1 Schema 变更 (`~/wzh/m1_samples/m1_table_schema.json`, 项目外)

- 新增 kv 布局表 `表头信息` (layout: "kv")，14 个字段，替代旧 `header_meta_fields` 硬编码
- 新增 catch-all 表 `_unattributed` (layout: "kv")，含 风险等级/到期时间
- 扩展 synonyms:
  - 对账日期 ← 对账期间/打印日期/起止日期/开始日期/结束日期
  - 合计金额 ← 总资产/净资产/资产市值/参考市值
  - 产品名称 ← 姓名/客户姓名
  - 基金份额净值 ← 份额净值
- 新增字段: 交易规费/其他费用/过户费/财汇局征费/清算金额/登记机构/确认份额/确认日期/确认金额/资金余额/配号/摘要/成交价格

### 2.2 Parser 变更 (`scripts/m1_statement_parser.py`)

- `Schema.load()`: 优先从 kv 布局表构建 `header_meta_fields`，无 kv 表时 fallback 旧 dict
- `extract_header_meta()`: 使用 schema 驱动的 kv 字段列表
- 新增 `scan_unattributed_kv()`: 对文档剩余文本做 `_unattributed` 表 kv 扫描
- `process_sample()`: 合并 header_meta + _unattributed kv

### 2.3 Unmapped 验证

| 指标 | 变更前 | 变更后 |
|------|--------|--------|
| 去重 unmapped 列 | 18 | 5 |
| 总出现次数 | ~25 | 5 |

剩余 5 个 unmapped:
- `普通账户对账单` — PDF 表标题误识别为列头（parser 表格检测边界问题）
- `备注` / `财汇局征费` / `配号` — 出现在 `证券持仓明细` 匹配表但字段定义在 `交易对账单`（跨表复用问题）
- `证券市值` — 与 `资产市值` synonym 冲突（资金资产汇总表内优先级竞争）

---

## Phase 3: M1 页面改造

### 变更文件

| 文件 | 变更 |
|------|------|
| `src/web/templates/m1.html` | 标题改为"M1 对账单解析工作台"；四面板→三面板（标准化表格/KV表数据/复核面板） |
| `src/web/static/m1.js` | 全部重写：文件上传→`/api/m1/parse-file`；三面板渲染；Sample 生成演示 TXT |
| `src/web/static/m1.css` | 全部重写：三栏 grid 布局、表格卡片、KV 表、勾稽条目、确认按钮样式 |
| `src/web/routers/m1.py` | 新增 `POST /api/m1/parse-file`（multipart 上传→parser→结构化 JSON）；保留旧 3 个端点 |

### 三面板设计

1. **标准化表格**: 每张检测到的表显示 schema 匹配、映射关系、前 10 行标准化记录
2. **KV 表数据**: 表头区 + _unattributed 键值对（脱敏）
3. **复核面板**: unmapped 列清单 + 勾稽校验结果（PASS/FAIL）+ 确认按钮

保留: stage rail、metric grid、M2 载荷 Copy/Download 按钮。

### 约束遵守

- `src/biz/m1_service.py` 未修改
- 样本/schema 在项目外，不进 Git
- 旧 `/api/m1/sample`、`/extract`、`/review` 端点保持兼容

---

## 验证

- `tests/test_m1_service.py`: 18/18 PASSED
- Router import: 4 routes OK (`/sample`, `/extract`, `/review`, `/parse-file`)
- Parser unmapped: 18 → 5（72% 减少）

## 后续

- 剩余 5 个 unmapped 需要: (a) 证券持仓明细表补充 备注/财汇局征费/配号 字段; (b) 资金资产汇总 证券市值 synonym 去重; (c) PDF 表标题误检需 parser 表格检测逻辑优化
- Phase 3 UI 需要实际浏览器验证（当前仅代码级验证）
- Multi-agent auto-delegation 仍为 "ready to activate"，未验证
