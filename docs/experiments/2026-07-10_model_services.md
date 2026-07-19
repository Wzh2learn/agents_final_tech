# 2026-07-10 Model Services

## Development Machine

Remote project path:

```bash
~/wzh/projects/agents_final_tech
```

Model storage root:

```bash
~/wzh/models
```

## Running Services

| Port | Model | Framework | Base URL | Notes |
| --- | --- | --- | --- | --- |
| 8001 | Qwen3.6-35B-A3B-Q4_K_M.gguf | stopped | http://127.0.0.1:8001/v1 | Quality-ceiling comparison only |
| 8002 | Qwen3-4B-Q4_K_M.gguf | stopped | http://127.0.0.1:8002/v1 | Lightweight JSON/speed baseline |
| 8003 | Qwen3-8B-Q4_K_M.gguf | stopped | http://127.0.0.1:8003/v1 | Small-model M1/M2 baseline |
| 8004 | Qwen3-14B-Q4_K_M.gguf | llama.cpp server | http://127.0.0.1:8004/v1 | Service active at the time of this 2026-07-10 record |

On 2026-07-10, the Qwen3.6-35B-A3B service on port 8001 was stopped after the
initial baseline. The model file remains available, but the 35B service should
only be restarted for quality-ceiling comparison runs. The development machine
normally keeps one generation model service active for each experiment.

## Downloaded Files

```bash
~/wzh/models/gguf/qwen3-4b/Qwen3-4B-Q4_K_M.gguf
~/wzh/models/gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf
```

The Qwen3-8B file was validated as GGUF:

```text
bytes=5027783488
header=47 47 55 46
```

## Smoke Test

Run from the remote project:

```bash
cd ~/wzh/projects/agents_final_tech
~/miniconda3/bin/conda run --no-capture-output -n wzh_vllm \
  python scripts/openai_smoke_test.py \
  --base-url http://127.0.0.1:8003/v1 \
  --model Qwen3-8B-Q4_K_M.gguf \
  --disable-thinking
```

Expected response shape:

```json
{
  "finish_reason": "stop",
  "content": "{\"status\":\"ok\",\"count\":1}",
  "reasoning_content": null
}
```

## Useful Commands

Download the next GGUF model:

```bash
cd ~/wzh/projects/agents_final_tech
HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 \
  ~/miniconda3/bin/conda run --no-capture-output -n wzh_vllm \
  hf download Qwen/Qwen3-14B-GGUF Qwen3-14B-Q4_K_M.gguf \
  --local-dir ~/wzh/models/gguf/qwen3-14b
```

Start a downloaded GGUF model:

```bash
cd ~/wzh/projects/agents_final_tech
./scripts/start_llamacpp_model.sh \
  ~/wzh/models/gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf \
  8003 \
  ~/wzh/logs/qwen3-8b-8003.log
```

Check a service:

```bash
curl http://127.0.0.1:8003/health
curl http://127.0.0.1:8003/v1/models
```

## Notes

Qwen3 GGUF models may default to thinking mode. For M1 structured output tests,
disable thinking with:

```json
{"chat_template_kwargs": {"enable_thinking": false}}
```

## M1/M2 Baseline Run

The repeatable baseline harness and its desensitized cases are versioned with the
project:

```text
scripts/benchmark_openai_models.py
tests/fixtures/m1_m2_baseline_cases.json
```

On 2026-07-10, the three running llama.cpp services were evaluated with thinking
disabled. The run contains two M1 rule-extraction cases and two M2 evidence-QA
cases per model, for 12 model-case pairs in total.

| Models | Automatic pass rate | Result directory on development machine |
| --- | --- | --- |
| Qwen3-4B, Qwen3-8B, Qwen3.6-35B-A3B | 12 / 12 | `docs/experiments/results/20260710_112815/` |

The Qwen3-14B Q4_K_M model was downloaded, started on port 8004, and evaluated
with the same four cases. The control-group baseline is now:

| Model | Cases passed | Result directory on development machine |
| --- | --- | --- |
| Qwen3-4B-Q4_K_M | 4 / 4 | `docs/experiments/results/20260710_112815/` |
| Qwen3-8B-Q4_K_M | 4 / 4 | `docs/experiments/results/20260710_112815/` |
| Qwen3.6-35B-A3B-Q4_K_M | 4 / 4 | `docs/experiments/results/20260710_112815/` |
| Qwen3-14B-Q4_K_M | 4 / 4 | `docs/experiments/results/20260710_114735/` |

The four cases are only a service and format baseline. They do not establish a
semantic quality ranking; the next comparison must use an annotated M1/M2 set.

The automatic checks cover JSON syntax, required output fields, basic evidence
citation, and refusal when evidence is insufficient. They are a service and
format baseline, not a substitute for a real annotated business dataset or
human semantic review.

Run the same benchmark after adding a model service:

```bash
cd ~/wzh/projects/agents_final_tech
~/miniconda3/bin/conda run --no-capture-output -n wzh_vllm \
  python scripts/benchmark_openai_models.py \
  --target 'qwen3-4b|http://127.0.0.1:8002/v1|Qwen3-4B-Q4_K_M.gguf' \
  --target 'qwen3-8b|http://127.0.0.1:8003/v1|Qwen3-8B-Q4_K_M.gguf' \
  --target 'qwen3.6-35b|http://127.0.0.1:8001/v1|Qwen3.6-35B-A3B-Q4_K_M.gguf' \
  --disable-thinking
```

## M2 Retrieval Model Preparation

The first retrieval batch was downloaded through `hf-mirror.com` and checked
with `scripts/smoke_test_retrieval_model.py`. These are local, offline model
loads rather than long-running HTTP services.

| Model | Local directory | Smoke-test result | Runtime |
| --- | --- | --- | --- |
| Qwen3-Embedding-0.6B | `~/wzh/models/hf/qwen3-embedding-0.6b` | 1024-dimensional embedding; relevant loan-age document ranked first | `wzh_retrieval` |
| BGE-M3 | `~/wzh/models/hf/bge-m3` | 1024-dimensional embedding; relevant loan-age document ranked first | `wzh_vllm` |
| bge-reranker-v2-m3 | `~/wzh/models/hf/bge-reranker-v2-m3` | Relevant loan-age document ranked first with a clear score gap | `wzh_vllm` |

`wzh_retrieval` is a conda clone of `wzh_vllm`. It upgrades Transformers to
4.57.6 because the original 4.45.2 package cannot recognize the `qwen3` model
architecture. The serving environment was not changed.

Both environments currently emit a PyTorch warning that the GB10 CUDA
capability is 12.1 while the installed PyTorch build declares support through
12.0. The smoke tests completed successfully, but CUDA/PyTorch compatibility
must be treated as a deployment-risk item and measured again before production
serving or throughput comparison.

## OCR and Vision-Language Preparation

| Model | Local directory | Current status | Runtime decision |
| --- | --- | --- | --- |
| PaddleOCR-VL-1.6 | `~/wzh/models/hf/paddleocr-vl-1.6` | Downloaded; `PaddleOCRVLForConditionalGeneration` config and `PaddleOCRVLProcessor` load successfully | Use `wzh_retrieval` for the first image/PDF smoke test |
| MiniCPM-V-4.6 | `~/wzh/models/hf/minicpm-v-4.6` | Downloaded; current Transformers 4.57.6 does not recognize `minicpmv4_6` | Do not change existing environments in place; assess a dedicated vision environment or GGUF/llama.cpp route |

The MiniCPM-V-4.6 official model card requires `transformers[torch] >= 5.7.0`
for its direct Transformers route and cautions that newer Torch/CUDA packages
can introduce CUDA compatibility issues. This dependency jump is intentionally
kept separate from the retrieval and serving environments.

## Tabular Research Environment

The development machine now has a separate `wzh_tabular` conda environment with
Python 3.11.15. It is reserved for TabFM, TabPFN, XGBoost, and LightGBM
experiments and does not contain the project-serving dependencies.

The environment now contains TabPFN 8.0.8, editable TabFM 1.0.1, and PyTorch
2.13.0+cu130. PyTorch reports CUDA 13.0, detects the NVIDIA GB10, and reports
compute capability 12.1 without the warning seen in the older environments.
TabPFN v2 and TabFM 1.0.0 PyTorch both completed GPU smoke tests using the same
eight-row synthetic credit-rule dataset. These runs validate loading and local
inference only; the dataset is too small for a quality comparison.

TabPFN v2 supports direct checkpoint download. Versions v2.5, v2.6, and v3 use
gated Hugging Face repositories and require accepting their terms and providing
an authenticated read token. The installed TabPFN license also adds an
attribution requirement for externally distributed products; internal
benchmarking is exempt.

`pip check` still reports `nvidia-cusparselt-cu13` as unsupported on the
platform even though the installed CUDA stack completes inference. Treat this
as package-metadata risk until the vendor publishes a clean ARM64 dependency
set.

## Additional Candidate Downloads

The optional public-model batch was downloaded after the first text,
retrieval, OCR, and tabular baselines:

| Model | Local directory | Approximate size | Status |
| --- | --- | --- | --- |
| MiniCPM5-1B | `~/wzh/models/hf/minicpm5-1b` | 2.1 GB | Complete; runtime smoke test pending |
| Qwen3-Reranker-0.6B | `~/wzh/models/hf/qwen3-reranker-0.6b` | 1.2 GB | Complete; rerank smoke test pending |
| Qwen3-VL-8B-Instruct | `~/wzh/models/hf/qwen3-vl-8b-instruct` | 17 GB | Complete; vision runtime smoke test pending |

TabPFN v3 is not downloaded yet. Its Hugging Face repository is gated and must
be accepted by the user account before authenticating the development machine.
