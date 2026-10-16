# execution_v1 - TQ-3 authorized developmental run

> Authorized by `../run_card/RUN_AUTHORIZATION_20261016_v1.md` (G1-G5).
> One developmental run only; hard budgets: 40 generation attempts / 400000 tokens / 90 min.

## Files
- `tq3_runner.py`   - main runner (`--plan`, `--check-pins`, `--run`, `--resume RUN_ID`)
- `tq3_analyze.py`  - post-run scoring/aggregation (`python3 tq3_analyze.py <run_id>`)
- `tq3_point_checks.py` - offline point checks; writes `tests/point_checks_<host>_<ts>.json`
- `tests/`          - point-check records
- `run_console.log` - created on GB10 when the run is launched

## Run (on GB10, from tq3_execution_prep_v1/)
    python3 execution_v1/tq3_point_checks.py
    python3 execution_v1/tq3_runner.py --check-pins
    python3 execution_v1/tq3_runner.py --plan
    python3 execution_v1/tq3_runner.py --run

Outputs land in `../runs/<run_id>/` (ledgers, raw responses, decisions, scoring,
RESULTS.json, SUMMARY.md, RUN_MANIFEST.json). Run outputs are NOT committed to git.

## Notes
- C = same-model, independent-context verification (not answer-blind; not an
  independent model). B = same-source check (full actor output visible). A = simple
  deterministic rule baseline (no model calls).
- Ledger entries are fsynced BEFORE every generation request; ledger counts are
  never reset. Crash resume: `--resume <run_id>` continues unexecuted items only.
- No content retries; infrastructure retries <= 4; request serial, timeout 120 s.
