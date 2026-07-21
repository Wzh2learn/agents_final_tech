# OpenCode / MCP

初始化现有 PostgreSQL/PGVector 知识库（先在受控终端配置环境变量，勿记录其值）：

```bash
python scripts/init_knowledge_backend.py
```

通过 stdio 启动只读 MCP 适配层：

```bash
bash scripts/start_mcp_server.sh
```

数据库密码和模型/API Token 只通过开发机环境变量提供，不提交到 Git。

截至 2026-07-21，只读 OpenCode/MCP 稳定性脚本的正式验收为 20/20 通过；这不
表示任何服务当前运行。`run_m2_rag_eval.py` 的 20 条夹具是合成脱敏数据，真实
运行必须先取得负责人批准的本地标签—来源映射和人工答案质量标注。

# scripts 目录说明

建议后续由 Codex 生成以下脚本。

## OpenCode + GB10

在开发机的 VS Code Remote-SSH 终端中运行 OpenCode：

```bash
cd ~/wzh/projects/agents_final_tech
# Configure required local environment variables outside this document.
bash scripts/run_opencode_gb10.sh
```

执行一次性任务时：

```bash
bash scripts/run_opencode_gb10.sh run --pure --auto --model gb10/qwen3-14b 'Reply with exactly OK.'
```

脚本默认设置 `OPENCODE_DISABLE_MODELS_FETCH=1`，避免开发机无法访问
`models.dev` 时 OpenCode 启动等待网络；`JINRONG_MCP_PYTHON` 默认复用
`wzh_vllm` 环境。OpenCode 应在 VS Code Remote-SSH 的交互式终端中运行。

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

## 6.6 Vision MCP server

`start_vision_mcp_server.sh` 仅启动独立的只读 stdio MCP；它不需要
`PGDATABASE_URL`，也不会在启动时导入视觉模型依赖。MCP 服务本身使用
`JINRONG_MCP_PYTHON`（默认 `~/miniconda3/envs/wzh_vllm/bin/python`）；重型视觉推理子进程才使用
`JINRONG_VISION_PYTHON`（默认 `~/miniconda3/envs/wzh_vision/bin/python`）。模型目录只由服务端固定映射
选择，可由各模型对应的本地环境变量覆盖；调用者只能传受控根目录中的图片路径。

```bash
bash scripts/start_vision_mcp_server.sh
python scripts/smoke_test_vision_mcp_server.py
```

第二条命令默认只验证工具发现，不运行推理。只有显式提供已批准图片时才调用 OCR：

```bash
python scripts/smoke_test_vision_mcp_server.py path/to/approved-image.png --model paddleocr
```

这是 2026-07-21 提交的实现说明，不是 OCR 质量指标或持续运行状态证明。真实推理的
原始文本、图片路径和日志均不得提交。

## 7. run_rag_eval.py

用途：

- 批量运行 RAG 问答测试集；
- 输出来源命中率、回答可追溯率、延迟。

## 8. run_rule_extract_eval.py

用途：

- 批量运行规则抽取测试；
- 输出 JSON 合法率、Pydantic 校验通过率、人工审核修改率。
