# 金融对账单智能解析与问答系统

基于 AI 的金融对账单智能解析与问答系统：上传对账单，秒级提取结构化数据，自然语言追问即得答案。

[![Tests](https://img.shields.io/badge/tests-164%20passed-brightgreen)]()
[![Parse Rate](https://img.shields.io/badge/parse%20rate-100%25-blue)]()
[![RAG QA](https://img.shields.io/badge/RAG%20QA-15%2F15-blue)]()

---

## 核心能力

| 能力 | 说明 | 指标 |
|------|------|------|
| 多格式解析 | PDF / TXT / DOCX，含扫描件 OCR | 5/5 = 100% |
| 智能字段映射 | 表头近义词 + LLM 兜底 | 60+ 同义词 |
| 勾稽校验 | 市值/币种/日期/错配 4 项自动校验 | real_pass/skipped 标注 |
| RAG 问答 | 自然语言查询 + 答案溯源 | 15/15 = 100%, 295ms |
| 多轮对话 | 连续追问，上下文感知检索 | session 管理 |

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/Wzh2learn/agents_final_tech.git
cd agents_final_tech

# 2. 环境
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 启动 (需要 PostgreSQL+PGVector 和模型服务)
bash scripts/run.sh

# 4. 访问
# UI:  http://localhost:5050/m1
# API: http://localhost:5050/docs
```

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
└── run.sh                   # 一键启动

tests/                       # 164 tests (0 failures)
docs/
├── 19_系统能力说明书.md      # 甲方演示文档
├── 20_部署指南.md            # 部署文档
└── experiments/             # 实验报告 + 截图
```

## 技术栈

- **后端**: Python 3.12 / FastAPI / uvicorn
- **解析**: 规则引擎 + LLM 兜底 + AI 视觉 OCR
- **检索**: PGVector + BM25 混合检索
- **生成**: Qwen3.6-35B-A3B (llama.cpp)
- **嵌入**: Qwen3-Embedding-0.6B
- **测试**: pytest (164 passed, 13 skipped)

## 性能

| 路径 | 延迟 |
|------|------|
| 非 OCR 解析 | <2.1s |
| OCR 解析 | 27-70s |
| M2 问答 | 295ms |
| 多轮追问 | ~300ms |

## 文档

- [系统能力说明书](docs/19_系统能力说明书.md) — 面向甲方/老师
- [部署指南](docs/20_部署指南.md) — 环境 + Docker + FAQ
- [Graph Engineering 设计](docs/17_Graph_Engineering_多层Loop设计.md) — 开发过程

## 开发

```bash
# 运行测试
PYTHONPATH=src pytest tests/ -v

# 运行 RAG QA 验证
python scripts/m1_rag_qa.py

# 运行性能基准
python scripts/m1_benchmark.py
```

## License

Internal use only.
