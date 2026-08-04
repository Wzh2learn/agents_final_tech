# M2 and MCP verification — 2026-07-19

## Verified

- The formal read-only OpenCode/MCP stability run completed successfully: 20/20
  passed (`all_passed: true`). Elapsed time ranged from 22.133 to 79.839 seconds,
  with a 35.899-second average. The local sanitized result JSON remains
  gitignored.
- `PGDATABASE_URL` was present without reading or recording its value.
- Qwen3-14B completed the historical service checks used by this verification;
  no current runtime state is implied.
- Focused tests passed: 19 tests covering the M2 fixture/evaluator,
  stability-run sanitization/lifecycle regression, and MCP server contract,
  with 6 deprecation warnings.
- Both evaluation scripts passed dry-run validation.
- A clean sequence of 20 read-only OpenCode/MCP collection-list checks completed.
  The sanitized result is stored in `docs/experiments/results/2026-07-19_mcp_opencode_stability_clean/`.
  All 20 checks timed out at the 30-second limit; pass count: 0/20. The result
  stores only run number, elapsed time, status, and output SHA-256 digest.
  This is a resolved, superseded diagnostic result from before the
  process-lifecycle fix; the formal 20/20 result above is the current status.

## M2 baseline blocker

The committed M2 fixture contains synthetic document labels only. No separate
approved mapping from those labels to stable RAG source IDs was supplied, so a
real baseline was not run and no metrics were fabricated. The evaluator now
requires that local mapping with an explicit approval flag and never writes it
to reports.

## Next action

Once an owner-approved local label-to-source mapping is supplied, run the
documented M2 evaluator and complete human answer-quality review.

## Resolved/superseded diagnostics

- `run_mcp_opencode_stability.py --dry-run` now validates without an output
  directory; live runs still require one.
- A direct Qwen3-14B completion completed successfully in 4.684 seconds.
- The MCP protocol smoke completed successfully in 22.939 seconds when run
  with the documented MCP Python environment.
- One isolated OpenCode/MCP probe returned a nonzero status in 18.000 seconds,
  without timing out and without the success marker. This is a superseded
  diagnostic result; the successful formal 20/20 run above is the current
  status.

## OpenCode JSON-event follow-up

- The stability runner now invokes OpenCode with `--format json` and records a
  pass only when `jinrong-rag_knowledge_list_collections` reaches a successful
  tool state. It does not inspect or persist model reply text.
- MCP startup allowance is 120 seconds to accommodate the local service's
  cold-start path. This is an OpenCode/MCP execution configuration change only;
  it does not alter model, database, network, or authentication settings.
- The post-change single JSON probe still reached an expected tool error. The
  raw error was inspected locally and reduced only to a database-schema
  compatibility category. No further attempts were run, and no private
  database details were recorded.

## Process-lifecycle follow-up

- The stability runner now directs combined OpenCode output to an anonymous
  temporary file, waits on the OpenCode parent, and then terminates only the
  attempt's own process group. This prevents inherited MCP output descriptors
  from making a completed parent appear to time out. Raw output is never
  persisted; the runner retains only status, elapsed time, and SHA-256.
- Focused tests passed, including a regression case where a child retains an
  inherited output descriptor after its parent exits. The dry-run and Python
  compile checks also passed.
- One read-only JSON-format OpenCode/MCP probe passed in 40.170 seconds with
  the expected collection-list tool event in a completed state. Its sanitized,
  Git-ignored summary is under
  `docs/experiments/results/2026-07-19_mcp_opencode_stability_lifecycle_probe/`.
  This probe predates and is superseded by the successful formal 20/20 run.
