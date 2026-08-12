# 任务：M1 真实对账单解析原型（表头近义词映射）

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
甲方提供了真实对账单样本和"解析表规则"配置，M1 的真实业务是：
**把各家格式不统一的对账单/报表，通过表头近义词映射，解析成标准化结构。**

样本在 `~/wzh/m1_samples/`（项目外，绝不进 Git）：
- `sample_fuxi_hunhe25_20231101.txt` — 财信证券对账单（GBK 文本，表头区+币种汇总+股票明细+尾部汇总）
- `sample_20260506_233222LU.pdf` — PDF 对账单
- `sample_boshi_chuantong.pdf` — 博时传统产品 PDF
- `sample_jiaxing_minan_20231031.pdf` — 嘉兴民安普通账户对账单 PDF
- `sample_xinhua.docx` — 新华 docx 对账单
- `mapping_xinxizha_xlsx.xlsx` — 组合证券持仓映射表（674 行 6 列）
- `m1_table_schema.json` — 解析表规则配置（表名/布局/表头区关键词/标准字段→近义词）
- `ui_parse_rule_table.png` — 甲方 UI 截图：解析表规则配置界面
- `ui_extraction_result.png` — 甲方 UI 截图：解析结果+数据分析界面

## M1 真实业务理解（务必先读）

1. 输入是格式各异的对账单（PDF/Excel/TXT/DOCX），每家券商/基金的表头列名不统一。
2. `m1_table_schema.json` 定义了"标准字段 → 近义词列表"。例如标准字段"产品名称"
   在源文档里可能叫"基金名称/账户名称/产品全称/证券简称/客户名称"。
3. M1 引擎要做：解析文档表格 → 识别表头 → 用近义词把源列名映射到标准字段 →
   提取行数据 → 输出标准化记录。映射不上的列标 `unmapped`（对应 UI 的"新增字段"）。
4. 表头信息区（非表格列的键值对，如客户名称/账号/证件号）也要提取。
5. 目标输出对照 `ui_extraction_result.png`：标准化表（产品/对账日期/券商/托管行/
   合计金额/明细行）+ 可在此基础上做 M2 数据分析问答。

## 约束（硬性）

- `~/wzh/m1_samples/` 是甲方真实业务数据，**绝不进 Git**，绝不复制到项目目录。
  原型代码只通过绝对路径 `~/wzh/m1_samples/` 读取。
- 实验报告和 commit 里的样例**必须脱敏**：客户名/账号/证件号/金额用掩码
  （如 `复熙****25号`、`2000****8295`、`2216****.90`）。不得贴完整真实值。
- 不得下载新模型。本轮**优先纯规则解析**（表头近义词匹配），LLM 仅作为
  复杂表格的最后兜底，且若用 LLM 须限流（避免与正在跑的 m1-batch 抢 :8004）。
- 不得修改 src/biz/m1_service.py（那是旧的中文规则基线，保留不动）。
  新原型放在 `src/biz/m1_statement_parser/` 新包，或 `scripts/m1_statement_*.py`。
- 不要 push。不要碰 test split。

## Phase 0: 环境与样本探查

```bash
cd ~/wzh/projects/agents_final_tech
ls -la ~/wzh/m1_samples/
cat ~/wzh/m1_samples/m1_table_schema.json | python3 -m json.tool | head -30

# 检查解析库（系统 python 有 PyMuPDF；venv 可能需要装 openpyxl/python-docx）
python3 -c "import fitz; print('PyMuPDF', fitz.__doc__[:30])" 2>/dev/null || echo "no fitz in system"
./venv/bin/python -c "import openpyxl; print('openpyxl ok')" 2>/dev/null || echo "need openpyxl"
./venv/bin/python -c "import docx; print('python-docx ok')" 2>/dev/null || echo "need python-docx"
```

缺库就在 venv 装（openpyxl、python-docx 是纯 Python，允许装；PyMuPDF 若 venv 没有
可用系统 python 解析 PDF，或装 pymupdf）。**不得装模型/数据集。**

用 TXT 样本（GBK）手工确认结构：表头区键值对 + `---` 分隔的表格 + 尾部汇总。

## Phase 1: 实现解析原型

创建 `scripts/m1_statement_parser.py`（单文件原型，stdlib + 上述库），含：

1. `parse_txt(path)`：编码探测(gbk/utf-8)；按行切分；识别表头区键值对
   （`客户名称:xxx` 模式）；识别 `---`/`===` 分隔线之间的表格（首行表头+数据行）。
2. `parse_pdf(path)`：PyMuPDF `page.find_tables()` 提取表格 + `get_text()` 提取表头区。
3. `parse_xlsx(path)`：openpyxl 读首个非空 sheet 为表格。
4. `parse_docx(path)`：python-docx 读 `document.tables` + 段落键值对。
5. `map_headers(source_headers, schema_table)`：对每个源列名，在 schema 的 synonyms
   里做匹配（精确 → 去空格包含 → 编辑距离≤2 fallback），返回
   `{standard_field: source_column}` 和 `unmapped` 列表。
6. `normalize(rows, mapping)`：按映射把每行转成标准化 dict（标准字段名）。
7. `extract_header_meta(text, schema)`：用 header_meta_fields 的正则/键名提取表头区键值对。

主流程：对 `~/wzh/m1_samples/` 每个 sample_*.{txt,pdf,xlsx,docx} 跑解析+映射+标准化，
打印脱敏后的结果摘要。

## Phase 2: 跑全部样本并评估

对每份样本记录：
- 文档类型、是否成功解析出表格、表格行列数
- 表头列数、映射命中数、命中率、unmapped 列名
- 表头区键值对提取数
- 标准化记录样例（**脱敏**）

## Phase 3: 结果汇总

写入 `docs/experiments/2026-07-28_m1_statement_parser.md`：

```markdown
# M1 真实对账单解析原型（表头近义词映射）

日期: 2026-07-28
样本: ~/wzh/m1_samples/（甲方真实对账单，未入库，报告已脱敏）
方法: 文档解析 + 表头近义词映射（纯规则，无模型）

## 解析结果表

| 样本 | 类型 | 表格 | 表头列 | 映射命中 | 命中率 | unmapped | 表头KV |
|------|------|------|--------|---------|--------|----------|--------|
| fuxi_hunhe25 | txt | ? | ? | ? | ?% | ? | ? |
| ... | ... | ... | ... | ... | ... | ... | ... |

## 标准化输出样例（脱敏）

（每类文档贴 1 条脱敏后的标准记录 JSON）

## 映射规则覆盖度分析

（哪些标准字段总能命中，哪些文档需要扩 synonyms）

## 发现与下一步

- 纯规则映射的覆盖率与局限
- 是否需要 LLM 兜底复杂/无表头表格
- 与 M2 数据分析问答的衔接点
```

## Phase 4: 提交（仅代码+脱敏报告）

```bash
# 确认没有把样本带进项目
git status --short | grep -i m1_samples && echo "ERROR: samples leaked!" || echo "clean"
git add scripts/m1_statement_parser.py docs/experiments/2026-07-28_m1_statement_parser.md
git commit -m "feat: M1 statement parser prototype (header synonym mapping)

Real counterparty statements (PDF/TXT/DOCX/XLSX) parsed via table extraction
+ header synonym mapping to standardized schema. Pure-rule, no model.
Samples stay in ~/wzh/m1_samples (not committed); report is desensitized."
```

## 停止条件

- 所有解析库都装不上 -> 用能用的子集，记录 BLOCKED 项
- 某样本解析崩溃 -> try/except 记录错误，继续其余样本
- 全部完成 -> 正常结束

## 不要做的事

- 不要把 ~/wzh/m1_samples 复制进项目或 commit
- 不要在报告里贴完整真实客户名/账号/金额
- 不要下载模型/数据集
- 不要 push
- 不要改 m1_service.py
- 不要密集调 :8004（m1-batch 正在用）
