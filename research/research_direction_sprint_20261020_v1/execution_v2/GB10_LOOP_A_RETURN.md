# GB10 Loop A Verification Return

Task: `gb10-finrank-c3-verify-20261020-a`

Status: `PASS`

Runtime: Python `3.12.3`, Linux `aarch64`

Scope: read-only deterministic recomputation under
`research/research_direction_sprint_20261020_v1/execution_v2/`.
No model request, judge, training run, raw-result edit, frozen-reference edit,
or existing-report edit was made.

## Required checks

| Check | Result | Exit |
|---|---:|---:|
| `BUNDLE_C3_B0_V4_FIX1.json` artifact hashes | `14/14` match | `0` |
| `python3 -B finrank_dev/verify_c3.py` | `13/13 PASS` | `0` |
| `python3 -B finrank_dev/verify_c2_historical.py` | `5/5`, reproducibility limitation retained | `0` |
| Open-probe unit tests | `4/4 OK` | `0` |
| Real-trace-feedback unit tests | `5/5 OK` | `0` |
| Direct B0 V4/raw/ledger recomputation | `23/23` checks | `0` |

## Direct recomputation

- Strict success: `5/7`.
- Plan sufficient: `7/7`.
- Consume sufficient: `6/7`.
- Raw pairs: `56/56`; crashes: `0`; retries: `0`.
- Ledger: `56/192` requests and `458,650/2,000,000` accounting tokens.
- `ESD_006`: evidence sufficient, consume answer `UNKNOWN`, non-success.
- `ESD_012`: `finish_reason=length`, `completion_tokens=256`, and the content
  fails strict JSON parsing with no closing JSON delimiter.

## C2 limitation

The C2 historical verifier returned `5/5` with status
`HISTORICAL_EVIDENCE_VERIFIED_WITH_REPRODUCIBILITY_LIMITATION`:

- `source_snapshot`: `MISSING`
- `current_source_state`: `DRIFTED_INTO_C3`
- `available_frozen_identity`: `BUNDLE_C2_B0_V3.json artifact hash manifest only`
- Claim boundary: historical fixture/result/raw/ledger evidence is verified,
  but the C2 source tree is not reproducible from current files.

## Hashes

- Bundle: `7bb3564cc8a30bac8d81f158232d68c8e3fbdf59247edbc5cd963c47deb893e7`
- B0 V4 result: `74ea8cd3e69096aee41d4b187b0956b40b6774a01fdd17d8699ec569abf5dd88`
- Ledger: `5a4915bd9918e747de17bc5de4eea023146b7b234f97a985e6af02039029dc13`
- ESD_012 raw response: `1baac28afdb9989a16ad9d78891f07393d1098a63f2dad4443d64fdeef9bb662`

The two verifier scripts were run in a temporary byte-identical hard-link
mirror so their report writes could not alter existing reports. Their exact
outputs and exit codes are recorded in `GB10_LOOP_A_VERIFICATION.json`;
the original `C3_VERIFICATION.json` and `C2_VERIFICATION.json` hashes were
unchanged before and after execution.

## Discrepancy record

No source, artifact, count, ledger, or evidence-boundary discrepancy was
found. The retained C2 source-snapshot limitation is a known reproducibility
boundary, not a newly discovered mismatch and not a scientific result.
