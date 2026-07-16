# 2026-07-14 Vision Model Smoke Test

## Environment

```text
conda environment: wzh_vision
Python: 3.11.15
PyTorch: 2.13.0+cu130
Torchvision: 0.28.0+cu130
Transformers: 5.7.0
CUDA: 13.0
GPU: NVIDIA GB10, capability 12.1
```

This environment is isolated from `wzh_vllm`, `wzh_retrieval`, and
`wzh_tabular`. It uses PyAV rather than TorchCodec to avoid CUDA-version
coupling during image and video decoding.

`pip check` reports `nvidia-cusparselt-cu13 0.8.1 is not supported on this
platform`. This is the same ARM64 package-metadata warning observed in the
tabular environment. All three CUDA inference runs completed, but the warning
remains a portability risk to track.

## Shared Image

All models processed the official PaddleOCR-VL Chinese newspaper demo image at
1524 x 1368 pixels. The prompt requested OCR text in reading order, and each
run generated at most 256 new tokens.

## Results

| Model | Result | Cold-start elapsed | Peak CUDA allocation | Initial observation |
| --- | --- | ---: | ---: | --- |
| PaddleOCR-VL-1.6 | Passed | 73.842 s | 1.934 GiB | Accurate title, author, and article text; output was truncated by the 256-token smoke limit |
| MiniCPM-V-4.6 | Passed | 20.122 s | 2.909 GiB | Fastest run and preserved Markdown headings, but introduced more Chinese OCR substitutions in later paragraphs |
| Qwen3-VL-8B-Instruct | Passed | 299.215 s | 5.592 GiB | Most complete and fluent extraction, but substantially slower and partly CPU-offloaded during loading |

These values include model loading and one generation. They are environment
smoke measurements, not steady-state latency or quality benchmarks.

## Retrieval Update

`sentence-transformers` in `wzh_retrieval` was upgraded from 5.1.2 to 5.4.0
to use the official Qwen3-Reranker causal-logit integration. After refreshing
the model repository metadata, the fixed Chinese query ranked the correct
document first:

```text
relevant document:  9.697536
unrelated document: -8.606872
unrelated document: -10.399744
```

The existing BGE reranker was rerun after the package upgrade and still ranked
the correct document first with score 0.996852.

## Download Completeness Fix

The original extension allowlist omitted `chat_template.jinja` for
PaddleOCR-VL, MiniCPM-V, and Qwen3-Reranker. Their weights and processors could
load, but inference either failed to build messages or produced invalid equal
rerank scores. The model catalog now includes `*.jinja` and model-card Markdown
for these entries. Existing local directories were refreshed from their
official repositories.

## Next Work

1. Build a small labeled M1 OCR set with clean PDF pages, scans, tables, and
   photographed documents.
2. Separate model-load time from warm inference latency and repeat each run.
3. Measure character error rate, table structure accuracy, reading-order
   accuracy, and downstream M1 field F1.
4. Use PaddleOCR-VL as the first OCR baseline; retain MiniCPM-V as the light
   VLM comparison and Qwen3-VL as the general-purpose quality reference.
