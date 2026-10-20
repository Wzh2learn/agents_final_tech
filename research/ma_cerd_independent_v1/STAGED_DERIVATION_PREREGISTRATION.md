# Staged Derivation Experiment

Status: `FROZEN_BEFORE_REQUESTS`
Evidence identity: `INDEPENDENT_MACERD_DEVELOPMENT`

Use the same 15 family-disjoint MA-CERD contracts as the matched-feedback
experiment. Remove priors and derive in three stages:

1. relation: 15 requests;
2. node classification: one request per actual plan node;
3. acceptable decisions: 15 requests.

Revision note: an input audit after the first 90 requests found node counts of
4, 6 and 9 rather than the assumed fixed 4. The actual frozen total is 104
requests. Completed requests remain valid and are not repeated; only missing
keys are resumed.

Each stage receives the same compact task evidence and explicit enums. Stage 2
classifies one node at a time as `impact` or `preserved`. Stage 3 receives the
fresh relation and node classifications, but no gold labels.

Primary metrics:

- relation accuracy;
- node classification accuracy and impact/preserved F1;
- handling exact match;
- end-to-end exact match.

Compare against the previous monolithic fresh-derivation V2 result. Hard caps:
118 requests and 220,000 tokens. Zero retries, one pinned model, temperature
0, `max_tokens=256`.
