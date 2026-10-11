# FinQA v2 Six-Gate Status v1

> Status: `SUPERSEDED_SNAPSHOT` | Superseded for current state by [`finqa_v2_gate_reconciliation_v2.md`](finqa_v2_gate_reconciliation_v2.md) | As of: 2026-10-10 | Historical read-only reconciliation; no FinQA v2 experiment run

## 1. Current decision

FinQA v2 remains blocked for formal execution. The candidate IDs and lexical evidence-to-argument join are frozen as feasibility artifacts, and the independent observation scorer passes its prototype contract, but split roles and pre-result scorer/preregistration freezes are incomplete.

`FORMAL_FINFQA_V2_GO = NO`

This document does not authorize adapter execution, evaluator calls, threshold changes, predictor changes, mutation changes, or post-result sample selection.

## 2. Six-gate status

| Gate | Current status | Evidence and boundary |
|---|---|---|
| `SOURCE_GO` | `PASS_SOURCE_IDENTITY_AND_HASHES` | The causal-join audit and candidate manifest bind the approved train/dev files by byte count and SHA-256. |
| `ID_GO` | `PASS_CANDIDATE_IDS_FROZEN_NOT_EXECUTION` | The manifest freezes 24 report clusters and 72 candidate injections for each of E/P/N, with disjoint report clusters and outcome-blind SHA-256 ranking. |
| `JOIN_GO` | `PASS_RESOLVER_AND_CANDIDATES_NOT_FORMAL` | The audit identifies a lexical unique-evidence join, and resolver v2 returns the argument only for a unique numeric-evidence match. This is not native pipeline provenance or semantic evidence-use proof. |
| `SPLIT_GO` | `BLOCKED_SPLIT_ROLE_NOT_FROZEN` | Train/dev/test, sealed, gate and evaluation roles are not frozen in the current manifest. |
| `SCORER_GO` | `PROTOTYPE_PASS_NOT_FROZEN` | Scorer v2 measures paired checkpoint observation reproduction, imports no shared FinQA fault adapter or Stage E aggregation, and passes 5/5 targeted tests. Exact artifact linkage and a pre-result freeze are still required. |
| `PREREG_GO` | `BLOCKED_PENDING_SPLIT_GO_AND_SCORER_FREEZE` | The preregistration cannot freeze until split roles, exact paired artifacts, scorer linkage and validation hashes are complete. |

Overall gate: `SECOND_FLOW_BLOCKED`.

## 3. Frozen feasibility evidence

### Source and join

- Records: `7134`
- Report clusters: `768`
- Rows with literal program arguments: `6836`
- Rows with at least one unique evidence join: `6794`
- Multi-step rows with unique join: `2851`
- Clusters with unique join: `766`
- Multi-step clusters with unique join: `627`
- Unique evidence-join events: `15368`

The join test is: a numeric literal program-argument token occurs in exactly one `qa.gold_inds` evidence text; the resolver must return that evidence when present and remain unresolved when it is removed. Counts establish constructibility only.

### Candidate sample

| Stage | Selected clusters | Selected injections | Eligible clusters after stage disjointness |
|---|---:|---:|---:|
| E | 24 | 72 | 594 |
| P | 24 | 72 | 526 |
| N | 24 | 72 | 553 |

Selection seed: `20261015`. Selection rule: ascending SHA-256 rank, stages consume disjoint report clusters, and no evaluator output is read.

### Independent scorer boundary

The measurement object is **paired clean/mutant checkpoint observation reproduction** with five observation fields: `evidence_required_hit`, `operator_consistency`, `argument_consistency`, `step_result_consistency`, and `answer_consistency`.

`semantic_correctness_claim = false`

Static import inspection found only standard-library imports (`hashlib`, `json`, `re`, and `typing`) and no shared FinQA fault adapter, existing step scorer, or Stage E aggregation. Targeted tests: `5 passed`.

### Resolver contract boundary

Resolver v2 is a deterministic lexical uniqueness test. It canonicalizes numeric tokens, rejects ambiguous evidence and nonnumeric arguments, and fails closed when no evidence contains the argument. Targeted tests: `3 passed`.

It does not establish that a model used the evidence semantically or that native pipeline provenance exists.

## 4. Required freezes before formal execution

1. Freeze exact train/dev/test, sealed, gate and evaluation roles without outcome inspection.
2. Bind exact sample IDs, operations and paired clean/mutant artifacts to the split roles.
3. Freeze the independent scorer artifact contract and validate its hash before evaluator output exists.
4. Freeze the preregistered primary endpoint, predictor set, thresholds, mutation rules and failure handling.
5. Re-run source/hash and document validators; any failure remains a blocker.

Until all five conditions pass: `NO_FORMAL_FINFQA_V2_RUN`.

## 5. Input bindings

| Input | SHA-256 |
|---|---|
| `research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json` | `280c563c5e701cf81f75d85664f6880f8133723693ddbc63a641db804a909ca7` |
| `research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json` | `71e6e2c4e2f59721644098cae20e1b850692edd20e0c138f87f27bedd4f25b77` |
| `research/finqa_independent_observation_scorer_v2.py` | `b48ed17c4aae2a1d70312e9c93c113d0e45b60d2429e83627162e78337d667e5` |
| `tests/test_finqa_independent_observation_scorer_v2.py` | `2146f847f4da0dab7295e615420eefbf55bc45167c5ce62360908153589db7d1` |
| `research/finqa_evidence_argument_resolver_v2.py` | `f60812f77695cb9d5a153a7986f1043e45043a08ec7b9bcf8c0c4be6d4b7201f` |
| `tests/test_finqa_evidence_argument_resolver_v2.py` | `ac51401a55f8e1ff5eb153f9cabf9dc17824a0be114eb931aed27dfc6544912e` |

## 6. Negative evidence

Mechanism generalization remains `MECHANISM_GENERALIZATION_NOT_IDENTIFIED`. This status does not claim natural-failure localization, semantic process correctness, hierarchy localization, or formal-pilot readiness.
