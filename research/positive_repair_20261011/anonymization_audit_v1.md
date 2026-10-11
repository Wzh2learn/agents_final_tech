# Double-Anonymous Scrub Audit v1

> date: 2026-10-11 | venue: SANER 2027 RENE (full double-anonymous) | artifact: paper/saner_rene_manuscript_v1.md

## Scan result (grep of the manuscript)
| Pattern | Hits |
|---|---|
| BUPT / wzh6520 / Wzh2learn / @bupt | 0 |
| JinRongAgents / github.com / testuser / GB10 / jinrong-dev / 王中华 | 0 |
| "Affiliation" / "Author" heading / acknowledg | 0 |
| non-ASCII (CJK) characters | 0 |
| :8004 (local judge port) | 3 |

Verdict: no author, affiliation, acknowledgment, repository-URL, host, or CJK leakage. The manuscript has no author block (correct for submission).

## Reviewed and retained (not identity-revealing)
- Relative internal artifact paths (for example scripts/m1_statement_parser.py, data/research/drift_v0/..., config/eval_checkpoint_trees.json). These are repository-relative paths, not URLs, and are the reproducibility handles. Keep, but the final package must pair them with a Data Availability statement that points to an ANONYMIZED repository (per SANER Open Science guidance).
- "127.0.0.1:8004" and ":8004 judge": a local serving address for the judge model, a reproducibility detail, not an identity signal. Retained.

## Required at camera-ready (owner)
- Restore author names/affiliations and acknowledgments.
- Ensure no self-citation is in the first person (checked: references are third person).
- Data Availability statement with an anonymized repository link.

## Blocking dependencies
- H1 (author list/order) and H2 (patent/submission clearance) remain owner decisions; they do not block the anonymized draft but block registration/submission and any public anonymous artifact release.