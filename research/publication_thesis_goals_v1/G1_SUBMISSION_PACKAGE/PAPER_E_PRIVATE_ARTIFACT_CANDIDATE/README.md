# Paper E Private Artifact Candidate

Status: `PRIVATE_REPRODUCTION_CANDIDATE_NOT_PUBLICLY_RELEASED`

This package reproduces two paper-facing deterministic surfaces from
versioned inputs:

1. the source-table UID clustered sensitivity analysis for the staged evaluator;
2. the full-precision arithmetic, three-decimal display rounding and direction
   checks for the FinRank tie-policy table.

It does not contain credentials, private data, internal AI review records, the
historical preregistration/fixtures/application rows, or a claim that the
package is a public archive. Those historical materials remain in the project
evidence store for author-approved release. The full-precision extract records
the exact source artifact hash for the historical application.

## Run

```sh
python3 reproduce.py --write-receipt REPRODUCTION_RECEIPT.json
```

The script uses only the Python standard library. A successful receipt records
the input hashes, recomputed values and environment. The original raw response,
historical application and post-hoc correction records remain outside this
minimal candidate and are not overwritten.

## Evidence Identity

- Staged analysis: post-hoc deterministic reanalysis of frozen row-level results.
- FinRank table: deterministic recomputation of released compact values; the
  identity counts remain post-hoc v2 corrections.
- No model, judge or training call is required to reproduce this candidate.
