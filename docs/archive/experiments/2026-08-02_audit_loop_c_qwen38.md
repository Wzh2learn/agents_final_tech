# Loop C Audit - 2026-08-02 (qwen3.8-max-preview)

## Model
qwen3.8-max-preview via Anthropic-compatible endpoint (Claude Code)

## Compatibility Issue
Claude Code sent a multi-step audit prompt. qwen3.8-max-preview responded
as if no task was given ("I don't see a specific task or question").
The model may not handle Claude Code's system prompt + user message format
correctly via the Anthropic proxy endpoint.

**Recommendation**: For Loop C audits, use deepseek-v4-flash-0731 (verified
working in previous audit) or glm-5.2. qwen3.8-max-preview is better suited
for Codex CLI (Loop A) where the prompt format is different.

## Manual Audit Results

| Check | Result |
|-------|--------|
| Frozen test (test_m1_service.py) | 0 changes - PASS |
| Schema additive | All original fields present, only synonyms added - PASS |
| Parser new functions | 3 additions (_coordinate_table_reconstruction, _try_vlm_table, Strategy 1.5) - all fallbacks |
| pytest | 225 passed, 0 failed - PASS |
| Existing parse paths | Unchanged (嘉合 93.8%, 嘉兴 100%, 复熙 100%) - PASS |

## Verdict: ACCEPTED (manual)

## Commits Audited
- d7049b5: Phase 1a+1b (HTML extraction + single-space strategy + synonyms)
- 701eae2: Phase 2a+2b (VLM server + _try_vlm_table)
- 9abf67b: Phase 2c (vision_mcp_server routing)
- d9a816c/a11daaf/84357b1/b927efe: Coordinate reconstruction (4 iterations)
- 9ea3754: docs/21 update
