# M2 and MCP verification — 2026-07-19

## Verified

- `PGDATABASE_URL` was present without reading or recording its value.
- The local Qwen3-14B health endpoint on port 8004 was reachable.
- Focused unit tests passed: 12 tests covering the M2 fixture/evaluator,
  stability-run sanitization, and MCP server contract.
- Both evaluation scripts passed dry-run validation.
- A clean sequence of 20 read-only OpenCode/MCP collection-list checks completed.
  The sanitized result is stored in `docs/experiments/results/2026-07-19_mcp_opencode_stability_clean/`.
  All 20 checks timed out at the 30-second limit; pass count: 0/20. The result
  stores only run number, elapsed time, status, and output SHA-256 digest.

## M2 baseline blocker

The committed M2 fixture contains synthetic document labels only. No separate
approved mapping from those labels to stable RAG source IDs was supplied, so a
real baseline was not run and no metrics were fabricated. The evaluator now
requires that local mapping with an explicit approval flag and never writes it
to reports.

## Next action

Restore a responsive OpenCode/Qwen3-14B completion path, then rerun the same
20 isolated checks. After an owner supplies an approved local label-to-source
mapping, run the M2 evaluator and complete human answer-quality review.
