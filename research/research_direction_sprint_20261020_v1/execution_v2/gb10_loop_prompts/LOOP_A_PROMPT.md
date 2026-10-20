# GB10 Loop A Verification Task

Task ID: `gb10-finrank-c3-verify-20261020-a`

You are Loop A on GB10. Work only under:

`/home/testuser/wzh/projects/agents_final_tech/research/research_direction_sprint_20261020_v1/execution_v2/`

Perform a deterministic independent recomputation of the C3/B0 V4 and open
research evidence. Do not send model requests, run judge/training, modify raw
results, change frozen references, or edit existing reports.

Required checks:

1. Verify `finrank_dev/BUNDLE_C3_B0_V4_FIX1.json` against its listed artifact
   hashes.
2. Run `python3 -B finrank_dev/verify_c3.py` and confirm 13/13.
3. Run `python3 -B finrank_dev/verify_c2_historical.py` and confirm 5/5 with
   its source-snapshot limitation.
4. Run the open-probe and real-trace-feedback unit tests.
5. Recompute B0 V4 counts directly from
   `results/B0_V4_MINIFIED_JSON/B0_RESULT.json`: 5/7 strict success, plan
   sufficient 7/7, consume sufficient 6/7.
6. Verify raw pair counts, zero crashes/retries, and ledger totals
   56/192 requests and 458,650/2,000,000 tokens.
7. Verify `ESD_006` remains sufficient-evidence `UNKNOWN`, and `ESD_012`
   remains `finish_reason=length` with truncated JSON.

Write only:

- `GB10_LOOP_A_VERIFICATION.json`
- `GB10_LOOP_A_RETURN.md`

Record Python version, commands, exit codes, hashes, and any discrepancy.
GB10 is authoritative; do not call a mismatch a scientific result.
