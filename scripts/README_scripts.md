# OpenCode / MCP

初始化现有 PostgreSQL/PGVector 知识库：

```bash
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
python scripts/init_knowledge_backend.py
```

通过 stdio 启动只读 MCP 适配层：

```bash
export JINRONG_MCP_PYTHON="$HOME/miniconda3/envs/wzh_vllm/bin/python"
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
bash scripts/start_mcp_server.sh
```

数据库密码和模型/API Token 只通过开发机环境变量提供，不提交到 Git。

# scripts 目录说明

建议后续由 Codex 生成以下脚本。

## 1. check_gpu.sh

用途：

- 检查 GPU、CUDA、驱动、内存、磁盘、Python、Docker。

## 2. setup_env.sh

用途：

- 创建 Python 环境；
- 安装基础依赖；
- 不建议自动安装 CUDA/驱动。

## 3. start_vllm.sh

用途：

- 启动 vLLM OpenAI-compatible API；
- 模型名从环境变量读取。

## 4. start_sglang.sh

用途：

- 启动 SGLang 服务；
- 用于后续对比。

## 5. start_llamacpp.sh

用途：

- 启动 llama.cpp server；
- GGUF 模型路径从环境变量读取。

## 6. benchmark_model.py

用途：

- 调用 OpenAI-compatible API；
- 记录首 token 延迟、总耗时、tokens/s、错误信息。

## 6.1 benchmark_openai_models.py

用途：

- 对多个本地 OpenAI-compatible 模型运行同一份 M1/M2 基线题集；
- 输出每题原始回答 `raw_results.jsonl`、可用 Excel 打开的 `summary.csv` 和运行元数据；
- 自动检查 JSON 合法性、必填字段和基础关键词命中。

使用方式：

```bash
~/miniconda3/bin/conda run --no-capture-output -n wzh_vllm \
  python scripts/benchmark_openai_models.py \
  --target 'qwen3-4b|http://127.0.0.1:8002/v1|Qwen3-4B-Q4_K_M.gguf' \
  --target 'qwen3-8b|http://127.0.0.1:8003/v1|Qwen3-8B-Q4_K_M.gguf' \
  --target 'qwen3.6-35b|http://127.0.0.1:8001/v1|Qwen3.6-35B-A3B-Q4_K_M.gguf' \
  --disable-thinking
```

## 6.2 smoke_test_retrieval_model.py

用途：

- 在不启动 HTTP 服务的情况下，加载本地 embedding 或 reranker；
- 对固定中文 query/document 样例输出相似度或重排序结果；
- 用于在接入项目 RAG 链路前确认模型权重和运行时依赖可用。

```bash
~/miniconda3/bin/conda run --no-capture-output -n wzh_vllm \
  python scripts/smoke_test_retrieval_model.py \
  --model-path ~/wzh/models/hf/bge-m3 \
  --kind embedding
```

## 6.3 check_vision_model_runtime.py

用途：

- 检查本地 OCR/VLM 的 Transformers 配置和 processor 是否可加载；
- 不加载完整权重，不占用 GPU 用于生成；
- 在准备真实文档评测集前发现依赖或自定义代码兼容性问题。

```bash
~/miniconda3/bin/conda run --no-capture-output -n wzh_retrieval \
  python scripts/check_vision_model_runtime.py \
  --model-path ~/wzh/models/hf/paddleocr-vl-1.6
```

## 6.4 smoke_test_tabular_model.py

用途：

- 在脱敏的小样本准入分类数据上验证 TabPFN 本地执行链路；
- 输出预测类别、概率和总耗时；
- 仅作为环境与模型加载 smoke test，不作为业务效果结论。

```bash
~/miniconda3/bin/conda run --no-capture-output -n wzh_tabular \
  python scripts/smoke_test_tabular_model.py \
  --model tabpfn --device cuda --model-version v2
```

Run the same sample with TabFM:

```bash
~/miniconda3/bin/conda run --no-capture-output -n wzh_tabular \
  python scripts/smoke_test_tabular_model.py \
  --model tabfm --device cuda
```

`v2` supports direct checkpoint download. TabPFN `v2.5`, `v2.6`, and `v3`
require accepting the corresponding gated-model terms on Hugging Face and
authenticating the development machine.

## 6.5 smoke_test_vision_model.py

用途：

- 使用同一张本地图片测试 PaddleOCR-VL、MiniCPM-V 或 Qwen3-VL；
- 输出识别文本、冷启动总耗时和 PyTorch 峰值 CUDA 内存；
- 用于正式 OCR 数据集评测前确认权重、模板和 GPU 推理链路。

```bash
~/miniconda3/bin/conda run --no-capture-output -n wzh_vision \
  python scripts/smoke_test_vision_model.py \
  --model-path ~/wzh/models/hf/paddleocr-vl-1.6 \
  --image /path/to/document.png \
  --kind paddleocr
```

## 7. run_rag_eval.py

用途：

- 批量运行 RAG 问答测试集；
- 输出来源命中率、回答可追溯率、延迟。

## 8. run_rule_extract_eval.py

用途：

- 批量运行规则抽取测试；
- 输出 JSON 合法率、Pydantic 校验通过率、人工审核修改率。
