# Repository Guidelines

## Project Structure

`src/` uses a layered FastAPI architecture: `web/` contains routes, templates, and static assets; `biz/` owns application services; `agents/` contains the in-app LangGraph agent; `tools/` implements retrieval and document functions; `storage/` manages PostgreSQL/PGVector, memory, and files. Read-only OpenCode adapters live in `src/mcp_server/`, `src/vision_mcp_server/`, and `src/tabular_mcp_server/`. Put tests in `tests/`, operational and experiment commands in `scripts/`, model manifests in `models/`, and plans/results in `docs/`.

Read `HANDOFF.md` and `docs/13_M1_M2联合数据闭环计划.md` for the current GB10 state,
approved public dataset, split policy, and immediate work before starting a new Codex CLI session.

## Current Architecture Boundary

The existing Web application and `RAGService` remain the source of truth for documents, collections, retrieval, and traceability. `opencode.json` connects the GB10 OpenAI-compatible Qwen3-14B service to three isolated local MCP servers. The implemented surface is read-only:

- `knowledge_search`
- `knowledge_list_collections`
- `knowledge_get_source`
- `vision_ocr_extract`
- `tabular_classify`

Qwen3-14B has been service-validated on this path, and the formal read-only
20-call OpenCode/MCP stability run passed. This does not imply a service is
currently running. Formal M2 business metrics remain blocked on an
owner-approved label-to-source mapping and human annotations. Vision and
tabular protocol/synthetic chain checks have passed, but M1 OCR quality,
tabular business metrics, and full multi-agent orchestration remain unfinished.
Do not create a second vector store or bypass `RAGService` with ad hoc database
queries.

As of 2026-07-28, the M1 display workbench is **complete and verified**:
`src/biz/m1_service.py`, `src/web/routers/m1.py`, `src/web/templates/m1.html`,
`src/web/static/m1.css`, `src/web/static/m1.js`, and `tests/test_m1_service.py`
(18 tests passing on both Windows and Linux aarch64). It is a deterministic
text-rule baseline for demonstrating the M1 -> M2 handoff flow, not an
OCR/VLM result or a production API. The GB10 dev machine has pulled this code
and verified tests pass.

## GB10 Dev Machine (2026-07-28)

Codex CLI 0.145.0 is configured with Token Plan:
- Default model: `qwen3.8-max-preview` (direct, Responses API)
- Chat-only models (`glm-5.2`, `deepseek-v4-pro`) via local proxy on `:8100`
  (`scripts/responses2chat_proxy.py`)
- tmux sessions for autonomous experiment loops
- venv at `~/wzh/projects/agents_final_tech/venv` (pytest + pydantic)
- PostgreSQL/PGVector Docker container on `:15432`
- Qwen3.6-35B-A3B llama-server on `:8004` (64K context, MoE 3B active)

Use `--dangerously-bypass-approvals-and-sandbox` for Codex CLI exec on GB10
(bubblewrap user namespaces unavailable).

## Development Commands

Use Python 3.11 and install `requirements.txt`. On Windows:

```powershell
.\venv\Scripts\python.exe scripts\verify_config.py
.\venv\Scripts\python.exe src\main.py -m http -p 5000
$env:PYTHONPATH="src"; .\venv\Scripts\python.exe -m pytest tests -v
```

On the GB10 Linux machine, provide the required local environment variables
without recording their values, then initialize and test the MCP path with:

```bash
python scripts/init_knowledge_backend.py
python scripts/smoke_test_mcp_server.py
opencode mcp list
```

## Style and Testing

Follow PEP 8, four-space indentation, type annotations, and `snake_case`/`PascalCase` naming. Keep route handlers thin and business logic in `src/biz/`. Tests use `pytest`; name files `test_*.py` and add focused coverage for service, retrieval, MCP contract, and API changes. Commands requiring live PostgreSQL, GB10 models, or cloud credentials must be identified as integration tests.

## Changes and Security

Use short, imperative commits scoped to one concern. PRs should state behavior, verification commands, configuration impact, and screenshots for UI changes. Never commit `.env`, credentials, server addresses, model weights, generated datasets, logs, or local databases. Preserve the read-only MCP boundary unless a reviewed task explicitly introduces a write operation.
## Current Work Mainline & Frozen Items (2026-07-28, user-confirmed)

These are boundaries the next agent must respect or it will redo frozen work or
mis-report status:

- **Mainline / north star = client counterparty-statement M1** (table parse +
  header synonym mapping + arithmetic reconciliation + statement workbench +
  OpenCode skill multi-agent). New work and remote Codex loops prioritize this.
- **TAT-DQA experiments are FROZEN** (paused, not deleted; numbers kept as a
  research baseline). Do NOT open new TAT-DQA retrieval / ablation / llm-batch
  loops or pile on volume. Resume the general methodology only in a later
  research phase, after the client-facing M1 is solid.
- The integrated G retrieval strategy (top_k=10 + bge-reranker-v2-m3 -> top-5,
  TAT-DQA EM 0.28) is the live M2 retrieval default, but it is orthogonal to the
  client M1; report the two separately, never conflate.
- **Multi-agent automatic delegation is NOT verified end-to-end.** Config +
  samples + engine are present (opencode.json agents/permissions), but no
  OpenCode auto-delegation run has completed; docs and reports must say
  "ready to activate", never "verified".
  - 2026-07-29 update: with the model on 64K context, **explicitly-instructed
    two-hop delegation IS verified** (`coordinator -> m1-extraction ->
    evidence-verifier`, exit 0 / 58s; verifier verdict matches the deterministic
    parser ground truth). See docs/experiments/2026-07-29_m1_verify_and_mcp.md.
    This does NOT cover neutral-prompt auto-delegation, which stays unverified.
- Real client samples live in `~/wzh/m1_samples/` on GB10 (outside the repo,
  never committed; reports desensitized). `scripts/loop_*.md` are consumed
  remote-loop task prompts, kept as audit archive.
- Remote Codex CLI exec needs `--dangerously-bypass-approvals-and-sandbox`
  (bubblewrap user namespaces unavailable on GB10).


## Qoder CLI Recon (2026-07-29, recon only, no switch)

Qoder CLI 1.1.7 isolated-installed at `~/.local/qoder` on GB10. Protocol analysis
confirms full OpenAI chat-completions compatibility with llama-server :8004 (direct,
no proxy needed) and responses2chat :8100 (forward path). Config via
`~/.qoder/settings.json` providers field (reverse-engineered from bundle).

**Hard gate**: Qoder requires account auth (PAT or browser OAuth) even for external
providers. Phase 2 connectivity test BLOCKED-auth. User must register + provide PAT
before any Qoder loop can execute.

Coexistence with Codex CLI: zero conflict (separate binaries, config dirs, auth).
All existing assets (AGENTS.md, SKILL.md, loop prompts, supervisors, proxy) are
tool-agnostic and reusable under Qoder with only the invocation shell changed
(`codex exec` -> `qodercli -p --dangerously-skip-permissions`).

Migration decision: pending user PAT + Phase 2实测. See docs/16 and
docs/experiments/2026-07-29_qoder_recon.md for full report.

## Codex CLI model switching on GB10 (2026-07-30)

Codex CLI on GB10 reads ~/.codex/config.toml with two Token Plan providers:
- Token_Plan (direct Responses API) -> qwen3.8-max-preview (default).
- Token_Plan_Chat (local responses2chat proxy :8100, Responses->Chat) -> glm-5.2, deepseek-v4-pro.
  glm/deepseek only speak Chat Completions on Qwen Token Plan; the proxy translates.
Switch helper: bash scripts/switch_codex_model.sh [qwen|glm|deepseek]
For glm/deepseek it also ensures the :8100 proxy is up. Verified 2026-07-30:
codex exec end-to-end with glm-5.2 via the proxy returns a valid response.
Manual equivalent (edit the two top-level lines of ~/.codex/config.toml):
  model = "glm-5.2"                  # or qwen3.8-max-preview / deepseek-v4-pro
  model_provider = "Token_Plan_Chat" # or Token_Plan for qwen
then ensure the proxy is running for the *_Chat provider:
  bash ~/start_proxy.sh   # fallback: nohup python3 ~/.local/bin/responses2chat_proxy.py &

## M1 Parser Terminal State (2026-07-31, 8h autonomous loop)

The M1 counterparty-statement parser (`scripts/m1_statement_parser.py`) achieved
**100% parse rate** on all 5 real client samples after 8 rounds of Loop A:

| Capability | Status |
|------------|--------|
| Text statement parse (TXT/XLSX) | 100% (rule mapping) |
| Text-layer PDF parse | 100% (grid + borderless fallback) |
| Image-only PDF/DOCX parse | 100% (OCR fallback, vision-8004 parallel) |
| LLM fallback (unmapped cols) | Connected, jiaxing unmapped 0 |
| Silent mismatch detection | Fixed, disposition field added |
| Market-value reconciliation | All PASS |
| RAG ingest + QA | 3/3 correct (PGVector m1_parsed_statements) |
| Reconcile disposition | real_pass / skipped / fail |
| OCR parallelization | 200s -> 74s (2.7x) |

PaddleOCR-VL remains broken (transformers version incompatibility); vision-8004
fallback handles all OCR needs. 72B model NOT replacing主力 (degenerate on
structured extraction).

## Graph Engineering Running Mode (2026-07-31)

Four-layer loop architecture per `docs/17_Graph_Engineering_多层Loop设计.md`:

| Layer | Role | Tool | Status |
|-------|------|------|--------|
| Loop D | Strategic oversight | Local Codex desktop | Active |
| Loop A | Execution | Remote Codex CLI via tmux | Standby (dispatched per task) |
| Loop B | Independent verification | graph-loop-b tmux daemon, 30min cycle | Running |
| Loop C | Quality audit | Claude Code + glm-5.2 | 12h freq (after 3x ACCEPTED) |

**AoE session management note**: AoE `send` does not work with `codex exec`
(one-shot binary; respawn re-runs original command). Loop A tasks are dispatched
via tmux direct launch:
```bash
tmux new-session -d -s loop-a-taskN "cd $PROJ && source ~/.bashrc && \
  cat scripts/graph/loop_a_exec_constraints.md /tmp/task.md | \
  codex exec --dangerously-bypass-approvals-and-sandbox 2>&1 | \
  tee -a logs/graph/loop_a.log"
```

Frozen nodes (Loop B verifies every 30min): `tests/test_m1_service.py`,
`~/wzh/m1_samples/m1_table_schema.json`, `scripts/graph/frozen_hashes.txt`.
L5 git pre-commit hook blocks commits touching frozen paths.

## M2 RAG QA Endpoint (2026-07-31)

The M2 RAG QA endpoint is live at :5050/api/m2/ask:
- POST { question: ..., top_k: 3} -> {answer: ..., sources: [...], model: ...}
- Uses PGVector collection m1_parsed_statements (17 embeddings, 4/5 samples)
- Embedding + generation via :8004 (Qwen3.6-35B-A3B)
- QA test suite: scripts/m1_rag_qa.py (15 queries, 100% correct)
- UI panel integrated into :5050/m1 page

## Qwen Harness Tools (2026-07-31)

scripts/qwen_harness_tools.py provides CLI access to Qwen platform tools:
- web_search: internet search via Responses API
- code_interpreter: cloud sandbox code execution
- web_extractor: web page content extraction (requires web_search in same request)
- Model: qwen3.8-max-preview, enable_thinking=true, timeout 120s
- Used by Loop A (execution) and Loop C (audit) for external verification

## Graph Engineering Loop Status (2026-07-31)

- Loop B: daemon running (30min cycle, all PASS)
- Loop C: 12h frequency (4x consecutive ACCEPTED), Claude Code + glm-5.2
- Loop A: standby (tmux direct launch per task)
- Loop D: strategic layer (user + main thread)
- Frozen nodes: tests/test_m1_service.py, ~/wzh/m1_samples/, scripts/graph/frozen_hashes.txt
- xinhua 0/11 schema hit: CLOSED (operational doc, not financial statement)

## 8h Delivery Loop (2026-08-01)

System upgraded from  runnable to deliverable:
- docs/19: Client-facing capability document (business perspective)
- docs/20: Deployment guide with Docker Compose
- Multi-turn M2 conversation (session_id + chat UI + context injection)
- 98+ tests (18 frozen + 17 edge + 20 multiturn + 53 unit)
- Demo screenshot sequence: docs/experiments/2026-08-01_demo_sequence/ (11 images)
- Docker: docker-compose.yml + Dockerfile + scripts/run.sh

### Test Inventory (2026-08-01)
| File | Count | Status |
|------|-------|--------|
| test_m1_service.py (frozen) | 18 | PASS |
| test_m1_edge_cases.py | 17 | PASS |
| test_m2_multiturn.py | 20 | PASS |
| test_m1_parser.py | ~15 | PASS |
| test_m1_reconcile.py | ~12 | PASS |
| test_m1_ocr_fallback.py | ~8 | PASS |
| test_m2_rag.py | ~8 | PASS |
| **Total** | **98+** | |
