# FinQA v2 Gate Reconciliation v2

> Status: `CANONICAL_RECONCILIATION_NOT_FORMAL_GO` | Evidence class: `SECONDARY` | As of: 2026-10-10 | No FinQA v2 experiment, model call, training run, or source-artifact rewrite

## 1. Canonical decision

`FORMAL_FINFQA_V2_GO = NO`

This namespace supersedes conflicting gate-table presentations. It reconciles presentation only; it does not change gate evidence, sample IDs, mutation rules, predictors, thresholds, or frozen source JSON.

## 2. Canonical six-gate table

| Gate | Canonical status | Boundary |
|---|---|---|
| `SOURCE_GO` | `PASS_SOURCE_IDENTITY_AND_HASHES` | Source byte counts and SHA-256 identities are bound; this is not authorization to execute. |
| `ID_GO` | `PASS_CANDIDATE_IDS_FROZEN_NOT_EXECUTION` | E/P/N candidate IDs are frozen without evaluator-output inspection. |
| `JOIN_GO` | `PASS_RESOLVER_AND_CANDIDATES_NOT_FORMAL` | The lexical unique-evidence join is constructible; it is not native provenance or semantic evidence use. |
| `SPLIT_GO` | `BLOCKED_SPLIT_ROLE_NOT_FROZEN` | Train/dev/test, sealed, gate, and evaluation roles remain unfrozen. |
| `SCORER_GO` | `PROTOTYPE_PASS_NOT_FROZEN` | The paired checkpoint observation-reproduction scorer passes its prototype contract but lacks exact artifact linkage and a pre-result freeze. |
| `PREREG_GO` | `BLOCKED_PENDING_SPLIT_GO_AND_SCORER_FREEZE` | Preregistration remains blocked by split and scorer freezes. |

Overall: `SECOND_FLOW_BLOCKED`.

## 3. Stale snapshots and preserved hashes

| Artifact | SHA-256 | Classification | Reason |
|---|---|---|---|
| `research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json` | `280c563c5e701cf81f75d85664f6880f8133723693ddbc63a641db804a909ca7` | `STALE_STAGE_SCOPED` | Predates candidate-ID freeze and contains the `JOING_GO` typo in `PREREG_GO`. |
| `docs/research/finqa_v2_causal_join_audit_v1.md` | `5f821f91619a70d9835d3ea5614ea55e41c89b8c57f967e184004cfd29d10388` | `STALE_DERIVED` | Mirrors the stage-scoped audit snapshot. |
| `research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json` | `71e6e2c4e2f59721644098cae20e1b850692edd20e0c138f87f27bedd4f25b77` | `STALE_INCOMPLETE` | Omits `SCORER_GO` and omits `SOURCE_GO` from its gate table. |
| `docs/research/finqa_v2_candidate_sample_manifest_v1.md` | `5171ee51030e1b6d15991b563ffc524c67e2176c3b0d67f5f52c2a927ae051fe` | `STALE_DERIVED` | Mirrors the incomplete manifest snapshot. |
| `research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_receipt.json` | `09d3e0ed3b4d226ec001ead3da9e2527eee5abb5e4afa0886772611812db49ee` | `STALE_PRE_RECONCILIATION` | Contains a six-gate snapshot but predates this canonical namespace. |
| `docs/research/finqa_v2_gate_status_v1.md` | `273a08c4c6930225e1c93d93c0db7e3c35641f8060b00e53b2c27cf35b476cf5` | `STALE_PRE_RECONCILIATION` | Values agree with the canonical table, but the document predates explicit supersession. |

All listed files remain byte-for-byte unchanged. The machine-readable companion records the same hashes and observed snapshots.

## 4. Numeric accounting boundary

The causal audit reports `627` multi-step clusters with a unique join; the later candidate manifest reports `594` E-stage clusters eligible after stage disjointness. The relationship between those counts is `NOT_YET_RESOLVED`. This reconciliation does not invent an eligibility-chain explanation.

## 5. Evidence boundary

The canonical table closes presentation disagreement only. It does not establish semantic process correctness, hierarchy localization, natural-failure localization, mechanism generalization, or formal FinQA v2 readiness.
