# Model Experiment Catalog

Model weights are stored on the development machine under `~/wzh/models` and
must not be committed to Git.

## Status convention — 2026-07-19

“Downloaded” means local files were obtained; “smoke-tested” means a limited
load/inference or format check passed; “service-validated” means a historical
local API path was exercised. None of these labels means a service is running
now or establishes M1/M2 business quality. Qwen3-14B is service-validated for
the OpenCode/MCP path. M1 has no numeric baseline; formal M2 metrics remain
blocked on approved source mapping and human annotations.

## First Batch

| Priority | Model | Format | Purpose |
| --- | --- | --- | --- |
| P0 | Qwen3-4B Q4_K_M | GGUF | Lightweight latency and structured-output baseline |
| P0 | Qwen3-8B Q4_K_M | GGUF | General M1/M2 baseline |
| P1 | Qwen3-14B | Safetensors or GGUF | Main quality/cost candidate |
| Existing | Qwen3.5-35B-A3B Q4_K_M | GGUF | Large MoE comparison |
| Existing | Qwen3.6-35B-A3B Q4_K_M | GGUF | Downloaded comparison candidate; historical baseline only |

## Role B Candidate Pool

| Priority | Model | Type | Purpose |
| --- | --- | --- | --- |
| P0 | Qwen3-8B GGUF | Text LLM | Main small-model M1/M2 baseline |
| P1 | MiniCPM5-1B | Text LLM | Ultra-light local assistant, tool-use, and rule QA boundary test |
| P1 | PaddleOCR-VL-1.6 | OCR/VLM | PDF, table, seal, formula, and layout parsing |
| P1 | MiniCPM-V 4.6 | VLM | Lightweight OCR/document QA comparison |
| P1 | Qwen3-Embedding-0.6B | Embedding | Lightweight retrieval baseline |
| P1 | BGE-M3 | Embedding | Dense/sparse/multi-vector retrieval baseline |
| P1 | bge-reranker-v2-m3 | Rerank | Lightweight rerank baseline |
| P1 | TabFM | Tabular FM | Zero-shot tabular classification/regression research track |
| P1 | TabPFN | Tabular FM | Mature tabular foundation model baseline |

Additional candidate downloads completed on the development machine:

| Model | Local directory | Download status |
| --- | --- | --- |
| MiniCPM5-1B | `~/wzh/models/hf/minicpm5-1b` | Complete |
| Qwen3-Reranker-0.6B | `~/wzh/models/hf/qwen3-reranker-0.6b` | Complete |
| Qwen3-VL-8B-Instruct | `~/wzh/models/hf/qwen3-vl-8b-instruct` | Complete |
| TabPFN v3 | TabPFN model cache | Pending gated-model acceptance and Hugging Face login |

Later batches cover DeepSeek-R1-Distill-Qwen, GLM/ERNIE/Baichuan/InternLM/Yi
comparison, Qwen3-VL, Qwen3-Reranker, OCR-specific variants, and lightweight
fine-tuning experiments after the text-model benchmark harness is ready.

TabFM and TabPFN should use a separate Python 3.11 experiment environment. Do
not install them directly into the reused `wzh_vllm` serving environment until
their dependency impact is checked.

The development machine now has an isolated `wzh_tabular` conda environment
with Python 3.11.15 for TabFM, TabPFN, XGBoost, and LightGBM experiments.
TabPFN 8.0.8, editable TabFM 1.0.1, and PyTorch 2.13.0+cu130 are installed.
PyTorch detects the GB10 and CUDA capability 12.1, and both TabPFN v2 and TabFM
1.0.0 have completed local GPU smoke tests. TabPFN v2.5/v2.6/v3 remain gated
and require license acceptance plus Hugging Face authentication.

`Qwen3-Embedding-0.6B` requires a newer Transformers release than the current
`wzh_vllm` environment provides. Use the cloned `wzh_retrieval` conda
environment for Qwen retrieval experiments; keep `wzh_vllm` unchanged for
llama.cpp and existing project-serving work. BGE-M3 and bge-reranker-v2-m3
have passed their first local smoke tests in `wzh_vllm`.

PaddleOCR-VL-1.6 has passed a configuration and processor check in
`wzh_retrieval`. MiniCPM-V-4.6 weights are downloaded, but its official
Transformers path requires version 5.7.0 or newer. Do not upgrade the existing
environments' Torch stack in place; evaluate a dedicated vision environment or
the official GGUF/llama.cpp route first.

## Mirror Download

Run in the reused `wzh_vllm` environment:

```bash
conda activate wzh_vllm
python scripts/download_hf_model.py Qwen/Qwen3-4B-GGUF \
  --include "Qwen3-4B-Q4_K_M.gguf" \
  --target ~/wzh/models/gguf/qwen3-4b
```

Override the mirror when needed:

```bash
HF_ENDPOINT=https://hf-mirror.com python scripts/download_hf_model.py ...
```
