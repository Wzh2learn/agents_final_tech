# 金融对账单智能解析与问答系统

基于 AI 的金融对账单解析与可溯源问答系统：上传对账单，提取结构化数据，并通过自然语言查询来源证据。

> 当前代码状态见 [`memory/STATE.md`](memory/STATE.md)；正式历史指标见 [`memory/CORE.md`](memory/CORE.md)。README 不维护容易过期的测试数和延迟快照。

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 多格式解析 | PDF / TXT / DOCX / XLSX / HTML，含扫描件 OCR 与坐标重建 |
| 智能字段映射 | 表头近义词与可选 LLM 兜底 |
| 勾稽校验 | 市值、币种、日期与错配校验 |
| RAG 问答 | 自然语言查询与来源溯源 |
| 多轮对话 | 连续追问与会话管理 |

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/Wzh2learn/agents_final_tech.git
cd agents_final_tech

# 2. 环境
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 前台启动 (需要 PostgreSQL+PGVector 和模型服务；Ctrl+C 停止)
bash scripts/run.sh

# 4. 访问
# UI:  http://localhost:5050/m1
# API: http://localhost:5050/docs
```

`scripts/run.sh` 完成开发环境检查后会进入统一的前台入口 `serve.sh`。启动过程不会终止已有进程；如果 5050 端口已被占用，它会报错退出。请先明确停止端口所属服务后再重试。

本地运行时契约：`PGDATABASE_URL` 是唯一数据库连接变量，默认数据库为 `vector_db`；Web 端口由 `M1_PORT` 控制，默认 `5050`。示例值统一维护在 `.env.example`。

## Docker 部署

```bash
docker compose up -d
curl http://localhost:5050/health
```

## API 示例

```bash
# 解析对账单
curl -X POST http://localhost:5050/api/m1/parse-file \
  -F "file=@statement.pdf"

# 智能问答
curl -X POST http://localhost:5050/api/m2/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "嘉兴民安的总资产是多少？"}'

# 多轮追问
curl -X POST http://localhost:5050/api/m2/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "其中证券市值呢？", "session_id": "<上轮返回的id>"}'
```

## 项目结构

```
src/
├── biz/            # 业务逻辑 (M1 解析, M2 RAG QA)
├── web/            # FastAPI 路由 + 前端
│   ├── routers/    # API 端点 (m1, m2, pages)
│   ├── static/     # CSS/JS
│   └── templates/  # HTML 模板
└── main.py         # 应用入口

scripts/
├── m1_statement_parser.py   # 对账单解析引擎
├── m1_rag_ingest.py         # RAG 知识库入库
├── m1_rag_qa.py             # RAG 问答测试 (15 queries)
├── m1_benchmark.py          # 性能基准测试
├── qwen_harness_tools.py    # 千问平台工具 CLI
└── run.sh                   # 开发环境检查后委托 serve.sh

serve.sh                     # 所有部署方式共用的服务入口

tests/                       # pytest 测试与契约检查
docs/
├── INDEX.md                 # 文档唯一导航入口
├── governance/              # 治理规则与审计证据
├── experiments/             # 只追加实验记录
└── archive/                 # 只读历史
```

## 技术栈

- **后端**: Python 3.12 / FastAPI / uvicorn
- **解析**: 规则引擎 + LLM 兜底 + AI 视觉 OCR
- **检索**: PGVector + BM25 混合检索
- **生成**: Qwen3.6-35B-A3B (llama.cpp)
- **嵌入**: Qwen3-Embedding-0.6B
- **测试**: pytest；正式全量结果以 GB10 留存证据为准

## 文档

- [文档索引](docs/INDEX.md) — 当前、历史、实验与归档的唯一导航入口
- [当前状态](memory/STATE.md) — 当前工程状态与下一步
- [Graph Engineering 设计](docs/17_Graph_Engineering_多层Loop设计.md) — 多层 Loop 设计依据

## 开发

```bash
# 运行测试
PYTHONPATH=src pytest tests/ -v

# 只运行与改动相关的测试；正式全量验证在 GB10 执行
PYTHONPATH=src python3 -m pytest tests/test_runtime_contract.py -q
```

## License

Internal use only.
