# M2 RAG 集成：M1 解析结果入库 PGVector + 端到端 QA 验证

- 日期: 2026-07-31
- 执行: Loop A (执行层) · Task #6
- 状态: **完成 — M1→M2 闭环打通，QA 命中 3/3**
- 关联: docs/13_M1_M2联合数据闭环计划.md · scripts/m1_statement_parser.py · src/biz/rag_service.py

---

## 1. 目标

证明 M1 对账单解析结果可以走既有 RAG 管线入库，并被 RAG QA 检索命中，
从而打通 **M1(结构化解析) → M2(知识库问答)** 闭环。不新建向量库、不绕过
`RAGService`、不改动任何冻结文件。

## 2. 环境

| 组件 | 值 |
|------|----|
| PGVector | docker `pgvector_15432`，:15432，库 `vector_db`，`vector` 扩展已装 |
| Embedding | 本地 `Qwen3-Embedding-0.6B`（`~/wzh/models/hf/qwen3-embedding-0.6b`，1024 维） |
| Embedding 设备 | **CPU**（GB10 aarch64 上 triton 的 CUDA JIT gcc 编译失败，CPU 对少量 chunk 足够快：加载 1.8s，9 条批量 0.3s） |
| 入库路径 | `RAGService.ingest_parsed_blocks` → `get_vector_store().add_documents` |
| 检索路径 | `RAGService.smart_retrieve`（向量 + BM25 混合，`use_rerank=False`） |
| 集合 | 新建 `m1_parsed_statements` |

入库前既有集合：`knowledge_base`(0 条)、`tat-dqa-joint-v1-validation`(627 条，冻结，未触碰)。

## 3. 数据安全边界（关键设计决策）

仓库红线：真实甲方样本「绝不入库」「输出全部脱敏」（见 m1_statement_parser.py
docstring 与 AGENTS.md）。但本任务要求把解析结果写入向量库。二者协调如下：

- 样本只在内存中解析；写入 PGVector 前，对**每条标准化记录**调用解析器自带的
  `desensitize_record` 脱敏。脱敏规则：字段名/表名/schema 名**保留**，值打码
  （证件/账号保首4尾4，名称保首2尾3，金额保整数前4位+小数）。
- `header_meta` 在解析器内已脱敏，直接复用。
- 因此向量库中**不存在任何原始客户值**；落库 chunk 形如
  `样本: xxx / 表: table_1 (资金资产汇总) / 字段: 资产总值=2216****.90, ...`。
- 检索之所以仍能命中，是因为查询的语义锚点（字段名/表名，如「资产总值」「证券持仓」
  「基金名称」）不被脱敏，而样本名通过 metadata `sample_id` 精确匹配。

脚本 `scripts/m1_rag_ingest.py` 直接 `import m1_statement_parser` 复用其解析与脱敏
函数，不复制逻辑、不改解析器。

## 4. 入库结果

只入库 5 个 `sample_*` 甲方对账单（排除 `mapping_xinxizha_xlsx.xlsx` 参考表，
其 673 行持仓会淹没小规模闭环演示）。逐记录一个 chunk + 表头区 KV 一个 chunk。

| 样本 | 类型 | 分组 | chunk 数 | 需OCR |
|------|------|------|---------|-------|
| sample_20260506_233222LU.pdf | pdf | 2 | 2 | 是 |
| sample_boshi_chuantong.pdf | pdf | 2 | 3 | 否 |
| sample_fuxi_hunhe25_20231101.txt | txt | 3 | 8 | 否 |
| sample_jiaxing_minan_20231031.pdf | pdf | 3 | 4 | 否 |
| sample_xinhua.docx | docx | 0 | 0 | 是 |
| **合计** | | | **17** | |

- `sample_xinhua.docx` 产出 0 chunk：image-only DOCX，OCR(vision-8004) 出来的表是
  「项目/内容」「阶段/我方工作」等非对账单版式，schema 命中 0、标准化记录全空，
  被「跳过全空记录」逻辑过滤。属 M1 解析覆盖问题，非 M2 集成问题。
- 每条 chunk metadata 含 `sample_id / kind / table_name / matched_schema /
  standard_fields / source / document_id / block_id`（满足任务对 metadata 的要求）。
- 入库后 PGVector：`m1_parsed_statements` = 17 embeddings。

## 5. QA 验证结果（smart_retrieve, top_k=5, 向量+BM25）

判定「相关」= top-k 中存在「期望样本 且 chunk 文本含期望字段/表关键词」。

| # | 查询 | 期望样本 | Top-1 命中 | 相关 |
|---|------|---------|-----------|------|
| 1 | 复熙混合25号的资产总值是多少？ | sample_fuxi_hunhe25 | `table_1 (资金资产汇总)` 含 `资产总值=2216****.90`（top1-3 全是该表） | ✅ |
| 2 | 嘉兴民安有哪些证券持仓？ | sample_jiaxing_minan | `p0_table_3 (证券持仓明细)` 含 证券代码/证券名称/持仓数量（top1-2） | ✅ |
| 3 | 博时传统产品的基金名称是什么？ | sample_boshi_chuantong | `表头信息` 含 `基金名称=博时****混合A`（top1） | ✅ |

**RELEVANT 3/3**（任务门槛 ≥ 2/3）。三条查询的正确 chunk 均排在第 1 位。

脱敏示例（Top-1 chunk，值已打码，可安全引用）：
- Q1: `字段: 资金余额=0.00, 资产总值=2216****.90, 证券市值=2216****.90, 币种=人民币, 资产市值=0.00`
- Q2: `字段: 证券代码=60****57, 证券名称=永****源, 在途数量=0, 持仓数量=2929****.00, ...`
- Q3: `字段: 客户姓名=新华****统产品, 资产账号=0042****0128, 基金名称=博时****混合A, 基金代码=00****22, ...`

## 6. 诚实观察与局限

1. **值被脱敏，精确数值不可直接问答**。闭环证明的是「检索能定位到正确的
   样本/表/字段 chunk」，而非「返回明文数值」。若未来需要明文数值问答，须由
   Loop D 单独授权解除脱敏边界（本任务无权解除）。
2. **M1 解析瑕疵（非 M2 问题，如实记录）**：
   - fuxi `table_1` 的 r1/r2 出现 币种=`美`/`港`/`币` 等错位碎片（TXT 列对齐伪影），
     干净行为 r0（币种=人民币）。
   - jiaxing `p0_table_3:r1` 缺 证券代码/证券名称（仅数值列）。
   这些是 M1 表头映射/列对齐的既有质量问题，不影响本次 M2 集成验证，留给后续 M1 迭代。
3. **CPU embedding**：triton CUDA JIT 在 GB10 aarch64 编译失败，改用 CPU；
   17 条 chunk 场景下无性能问题。大规模入库需修复 triton 或换用 SiliconFlow API。
4. **xinhua 0 chunk**：image-only 非对账单版式，M1 未覆盖。

## 7. 验证

- 合约测试：`pytest tests/test_m1_service.py` → **18 passed**（冻结合约未破坏）。
- 全量测试：75 passed, 12 failed。12 个失败均为**既有、与本改动无关**：
  `test_core_service / test_e2e_browser / test_hmm_memory / test_websocket`
  报 "async def functions not natively supported"（缺 pytest-asyncio 插件），
  `test_web_integration` 需 live FastAPI 服务（集成测试）。本改动仅新增一个脚本，
  未改任何 src/ 或 tests/。
- 冻结哈希校验（md5sum 与 frozen_hashes.txt 一致）：
  - `tests/test_m1_service.py` = `faa7565a2b83b5b593389000b7ed72d7` ✅
  - `~/wzh/m1_samples/m1_table_schema.json` = `73d4f46e20e8eeb03532f4b4a8e55c0d` ✅
- 未触碰：`~/wzh/m1_samples/`、`frozen_hashes.txt`、`docs/experiments/` 既有文件、
  RAGService 核心逻辑、TAT-DQA 任何文件。

## 8. 复现

```bash
cd ~/wzh/projects/agents_final_tech
# 入库（解析 5 样本 -> 脱敏 -> 写 m1_parsed_statements；含 OCR 约 2-3 分钟）
./venv/bin/python scripts/m1_rag_ingest.py ingest
# QA 验证（秒级）
./venv/bin/python scripts/m1_rag_ingest.py verify --top-k 5
# 或一次完成
./venv/bin/python scripts/m1_rag_ingest.py all
```

环境变量（脚本内已设默认，可被外部覆盖）：
`LOCAL_EMBEDDING_MODEL_PATH` / `LOCAL_EMBEDDING_DEVICE=cpu` / `PGDATABASE_URL`。

## 9. 变更文件

- 新增 `scripts/m1_rag_ingest.py`（ingest / verify / all 三子命令）
- 新增 `docs/experiments/2026-07-31_m2_rag_integration.md`（本报告）
- 副作用：PGVector 新建集合 `m1_parsed_statements`（17 条脱敏 chunk）
