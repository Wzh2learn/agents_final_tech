# FinQA v2 Causal Evidence-to-Argument Join Audit v1

> Status: `JOIN_CANDIDATE_IDENTIFIED_NOT_FROZEN` | Read-only feasibility audit | No FinQA adapter or formal experiment

## 1. Counts

| Quantity | Count |
|---|---:|
| Records | 7134 |
| Report clusters | 768 |
| Rows with literal program arguments | 6836 |
| Rows with at least one unique evidence join | 6794 |
| Multi-step rows with unique join | 2851 |
| Clusters with unique join | 766 |
| Multi-step clusters with unique join | 627 |
| Literal argument events | 15840 |
| Unique evidence-join events | 15368 |

## 2. Join definition

A candidate causal join exists when a numeric literal program argument token occurs in exactly one `qa.gold_inds` evidence text. The future resolver contract must return that argument with the evidence present and return `UNRESOLVED` after removing that evidence.

This is a lexical, deterministic join candidate. It is not native pipeline provenance; the resolver semantics and exact sample manifest still need to be frozen.

## 3. Six-gate status

| Gate | Status |
|---|---|
| SOURCE_GO | `PASS_SOURCE_IDENTITY_AND_HASHES` |
| ID_GO | `BLOCKED_EXACT_SAMPLE_IDS_NOT_FROZEN` |
| JOIN_GO | `PASS_CANDIDATE_NOT_FROZEN` |
| SPLIT_GO | `BLOCKED_ROLE_SCOPE_NOT_FROZEN` |
| SCORER_GO | `BLOCKED_INDEPENDENT_SCORER_NOT_LINKED_TO_EXACT_IDS` |
| PREREG_GO | `BLOCKED_PENDING_JOING_GO_ID_GO_SPLIT_GO_SCORER_GO` |

## 4. Decision

`SECOND_FLOW_BLOCKED` until the causal resolver, exact IDs, role/split scope and independent scorer are frozen. Do not treat the numeric-token count as proof of semantic evidence use.
