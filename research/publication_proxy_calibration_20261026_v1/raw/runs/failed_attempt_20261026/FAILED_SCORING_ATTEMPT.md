# Preserved Failed Scoring Attempt

The first calibration process generated all 36 primary calls plus four
preregistered bounded retries (40 calls total), then stopped during
post-generation semantic scoring. No calibration result or analysis was
written. The preserved partial ledger contains 40 complete model attempts.

- Raw partial: `P2_GENERATIONS.partial_40.jsonl`
- Raw SHA256: `fca487c420409a389059aefe169562ca28f58246df0b6157b6c51b7258132488`
- Rows: 40
- Final status: `STOPPED_BEFORE_RESULT`
- Scientific meaning: none; this is an engineering interface failure, not
  evidence for or against proxy information value.

Failure location and preserved traceback:

```text
Traceback (most recent call last):
  File "/home/testuser/wzh/publication_proxy_calibration_worktree_20261026/research/publication_proxy_calibration_20261026_v1/raw/runner.py", line 345, in <module>
    raise SystemExit(main())
  File "/home/testuser/wzh/publication_proxy_calibration_worktree_20261026/research/publication_proxy_calibration_20261026_v1/raw/runner.py", line 339, in main
    payload = {"dry-run": write_zero_output_dry_run, "preflight": formal_preflight, "calibrate": calibrate}[args.mode]()
  File "/home/testuser/wzh/publication_proxy_calibration_worktree_20261026/research/publication_proxy_calibration_20261026_v1/raw/runner.py", line 247, in calibrate
    semantic = semantic_result(parsed, reference, bool(scoring["required_evidence_visible"]))
  File "/home/testuser/wzh/publication_proxy_calibration_worktree_20261026/research/publication_proxy_calibration_20261026_v1/raw/semantic_matcher.py", line 135, in semantic_result
    observed = _normalize_candidate_refs(response)
  File "/home/testuser/wzh/publication_proxy_calibration_worktree_20261026/research/publication_proxy_calibration_20261026_v1/raw/semantic_matcher.py", line 58, in _normalize_candidate_refs
    row, column = value[6:].split(":", 1)
ValueError: not enough values to unpack (expected 2, got 1)
```

The repair only normalizes the already accepted `TABLE:<column>` interface
form to the frozen historical column form. It does not alter model outputs,
frozen references, or scoring decisions.
