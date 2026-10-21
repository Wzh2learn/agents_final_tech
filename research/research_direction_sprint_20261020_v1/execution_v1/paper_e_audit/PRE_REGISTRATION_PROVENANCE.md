# Pre-Registration and Output Provenance

`PRE_REGISTRATION.json` remains unchanged as the historical freeze record.
It binds audit code SHA-256:

`CE0DEFDA5F32645FE67E8292CB2D0DF26045B99B20AE3FF4CE19D164BDE771C8`

## V1: Preregistered Wrong-Identity Application

- Status: preregistered question and thresholds; source-identity
  implementation invalid for FinRank's contamination identity.
- Audit code SHA-256: `CE0DEFDA5F32645FE67E8292CB2D0DF26045B99B20AE3FF4CE19D164BDE771C8`
- Result SHA-256: `586148D55116B092E5764EA07C13C522060B20323A969A84AE7BB8D6D5A8FD4F`
- Record rows SHA-256: `16A90B703BA836A26CCEF233124DD98A05DF4ECBA479FBBC4E4611A2FAF5F8D2`
- Files: `outputs/APPLICATION_RESULTS_v1_raw_text_overlap.json` and
  `outputs/APPLICATION_RECORDS_v1_raw_text_overlap.jsonl`.

V1 used raw exact text overlap and reported 293 hard-negative occurrences
across 220 records. FinRank's canonical contamination identity uses trimmed
text / `text_sha1` and `hn_taxonomy.json`.

## V2: Post-Hoc Identity-Corrected Reanalysis

- Status: post-hoc deterministic identity correction and reanalysis; not a
  complete frozen application.
- Audit code SHA-256: `1A2E0AFDF3DB12ED78DA72CB9F980F82D938AD0C7153BF20B25A906B675FE8BF`
- Result SHA-256: `FB4A4CF0066C2482867752BB9B6E92CBF02783BD333635F9A99244B4924A81BD`
- Record rows SHA-256: `278DC785171001FDF38D03482A7FC52558858C87857512377DD46384C1E506E0`
- Files: `outputs/APPLICATION_RESULTS.json` and
  `outputs/APPLICATION_RECORDS.jsonl`.

V2 separately reports raw exact, trimmed, SHA-1 and official-taxonomy identity.
The canonical result is 442 hard-negative occurrences across 305 records.

## Invariants and Limits

The preregistered questions and thresholds remain frozen. V1 and V2 have
identical TF-IDF/BM25 hard/random pairwise metrics, tie-policy variants,
hardness gaps, in-record tie sensitivities and global tie-order deltas. Because
v2 used changed code after the source-identity error was visible, those
identical tie values must be described as preregistered questions with a
post-hoc corrected implementation, not as results of a wholly frozen
application. No raw result was overwritten or edited.
