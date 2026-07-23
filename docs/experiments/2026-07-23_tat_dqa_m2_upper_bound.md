# 2026-07-23 TAT-DQA M2 Parsed-JSON Upper Bound

## Scope

This baseline measures M2 on the frozen `joint-v1` validation split while
bypassing OCR and PDF parsing. It uses the official converted block JSON, so it
is an M2 parsed-input upper bound, not an M1 or end-to-end result. The test split
remains sealed.

- Dataset: TAT-DQA, CC BY 4.0
- Split: validation only
- Documents/questions: 20/100
- Parsed blocks: 627
- Collection: `tat-dqa-joint-v1-validation`
- Embedding: local Qwen3-Embedding-0.6B, 1024 dimensions
- Generator: Qwen3-14B Q4 through the validated OpenAI-compatible endpoint
- Retrieval: existing `RAGService`, hybrid path, top 5, rerank disabled

The collection was populated through `RAGService.ingest_parsed_blocks`; no
second vector database or direct evaluation-only database query was introduced.
Original JSON, questions, answers, model output, indexes, and per-case reports
remain under `~/wzh/datasets/tat-dqa/` and are not committed.

## Results

| Metric | Validation result |
| --- | ---: |
| Document Recall@5 | 0.81 |
| Evidence-block Recall@5 | 0.50 |
| Evidence MRR | 0.4132 |
| Answer exact match | 0.24 |
| Correct evidence citation rate | 0.48 |
| Mean retrieval latency | 0.08 s |
| Mean retrieval + answer latency | 3.079 s |
| Structured-answer errors | 0 / 100 |

Answer exact match by official type was 0.4048 for span, 0 for multi-span,
0.3636 for count, and 0.0938 for arithmetic. Fifty cases missed the gold
evidence block in the first five results. Of the 50 cases with a gold evidence
hit, 32 still produced an incorrect answer and 18 produced an exact match.

These results establish the untuned validation baseline. They show two separate
bottlenecks: block retrieval is insufficient, and generation remains weak on
multi-span and arithmetic questions even when evidence is available.

## Reproduction

Provide `PGDATABASE_URL` through the controlled development-machine environment
and set the local model path outside Git:

```bash
export LOCAL_EMBEDDING_MODEL_PATH=~/wzh/models/hf/qwen3-embedding-0.6b
export LOCAL_EMBEDDING_DEVICE=cuda
export PYTHONPATH="$PWD/src"

~/miniconda3/envs/wzh_retrieval/bin/python \
  scripts/run_tat_dqa_m2_upper_bound.py \
  --manifest docs/datasets/tat-dqa-joint-v1-manifest.json \
  --qa-json ~/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json \
  --docs-archive ~/wzh/datasets/tat-dqa/raw/tatdqa_docs_dev.zip \
  --split validation \
  --collection tat-dqa-joint-v1-validation \
  --evaluate --with-answers \
  --output ~/wzh/datasets/tat-dqa/derived/m2-validation-answer-full100.json
```

Focused verification completed with `13 passed, 4 deprecation warnings`. The
older retrieval environment also emits a PyTorch capability warning for GB10
12.1 versus a build declaring support through 12.0; CUDA inference completed,
but this remains a runtime risk to remove before throughput claims.

## Next Controlled Comparisons

1. Keep this manifest, collection, generator, and evaluator fixed.
2. Compare vector-only, BM25-only, hybrid, and local reranker variants.
3. Address count/multi-span evidence misses before tuning the generator.
4. Compare official JSON against traditional PDF extraction and Vision MCP/OCR.
5. Use validation for choices; do not run test answers until the protocol is frozen.
