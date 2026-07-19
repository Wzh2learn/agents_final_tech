# Development Handoff

## Snapshot

This handoff reflects the repository and GB10 integration state on 2026-07-19.
The repository extends the existing JinRongAgents FastAPI/LangGraph application
with a loosely coupled OpenCode and local-model experiment path for:

- M1: document parsing and structured business-rule extraction;
- M2: evidence-grounded knowledge-base question answering.

The existing `RAGService`, PostgreSQL/PGVector data, source metadata, APIs, and
Web pages remain the source of truth. Do not create a second vector database.

## Completed

- Qwen3 4B, 8B, 14B, and Qwen3.6-35B-A3B GGUF service/format baselines.
- Qwen3-14B llama.cpp service configured at `127.0.0.1:8004` with a 16K context.
- Read-only MCP tools: `knowledge_search`, `knowledge_list_collections`, and
  `knowledge_get_source`.
- OpenCode provider, MCP permissions, and logical M1/M2/verifier subagents in
  `opencode.json`.
- Protocol smoke test and one end-to-end OpenCode tool call returning the
  `knowledge_base` collection.
- Retrieval, vision, and tabular model downloads/smoke tests documented under
  `docs/experiments/`.

## Immediate Work

1. Pull the latest `main` branch on the GB10 machine.
2. Verify PostgreSQL/PGVector, Qwen3-14B, OpenCode, and MCP after the latest
   machine/network state change.
3. Run 20 consecutive read-only MCP/OpenCode tasks and save the raw results.
4. Build the first M2 annotated set: start with 20 questions, then expand toward
   100. Include answerable, unanswerable, boundary, and conflicting cases.
5. Establish the Qwen3-14B M2 baseline with Recall@5, source hit rate, refusal
   rate, answer quality, and latency.
6. Only after the baseline is reproducible, compare BGE-M3/Qwen3-Embedding and
   BGE/Qwen3 rerankers one variable at a time.

Do not start LoRA/QLoRA, full multi-agent orchestration, or more model downloads
before the M2 dataset and baseline are stable.

## GB10 Runtime

Remote repository:

```bash
~/wzh/projects/agents_final_tech
```

Expected environments:

- `wzh_vllm`: project serving, llama.cpp support, MCP runtime;
- `wzh_retrieval`: Qwen/BGE retrieval experiments;
- `wzh_vision`: PaddleOCR-VL, MiniCPM-V, Qwen3-VL;
- `wzh_tabular`: TabFM, TabPFN, XGBoost, LightGBM.

Required shell variables:

```bash
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
export JINRONG_MCP_PYTHON="$HOME/miniconda3/envs/wzh_vllm/bin/python"
```

Start or verify the 14B/OpenCode path:

```bash
cd ~/wzh/projects/agents_final_tech
bash scripts/start_llamacpp_model.sh \
  ~/wzh/models/gguf/qwen3-14b/Qwen3-14B-Q4_K_M.gguf \
  8004 /tmp/qwen3-14b-8004.log 16384
curl -s http://127.0.0.1:8004/health
python scripts/smoke_test_mcp_server.py
bash scripts/run_opencode_gb10.sh mcp list
```

Model services are not assumed to survive a reboot. Check before restarting and
keep only one large generation model active.

## Guardrails

- Read `AGENTS.md`, `docs/AGENTS.md`, and this file before editing.
- Preserve unrelated working-tree changes and inspect remote stashes before use.
- Never commit `.env`, credentials, tokens, machine addresses, model weights,
  local databases, logs, or private business data.
- A legacy Anthropic token was redacted on 2026-07-19. Treat the historical
  value as compromised and rotate/revoke it; do not copy it from Git history.
- Ask before CUDA/driver/system-network changes or stopping another user's
  process.
- Put reproducible scripts in `scripts/` and sanitized result summaries in
  `docs/experiments/`.
