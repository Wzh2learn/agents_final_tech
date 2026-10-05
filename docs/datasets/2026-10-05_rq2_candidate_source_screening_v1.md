# RQ2 candidate source metadata screening v1（2026-10-05）

> Status: `METADATA_ONLY_SCREENING / NO_DOWNLOAD / RQ2_NOT_IDENTIFIED`
> Scope: the 10 sources already recorded in `paper-public-source-registry-v1.json`
> Boundary: no new repository, revision, data body, licence interpretation, model call, or download was used

## 1. Screening question

A confirmatory RQ2 source must make the following evidence co-recoverable within one namespaced lineage UID:

1. **checkpoint evidence** available before action generation and traceable to source, generator, step/time, and hashes;
2. **action/target semantics** for `map_to`, `hold`, and `skip`, including a canonical target for `map_to`;
3. **correctness** from an independent label/adjudication chain that can define correct, incorrect, and harmful actions;
4. **independence capacity** sufficient for role-separated proposal/dev, gate-validation, and sealed evaluation without treating a source namespace as a row-level cluster.

This screening uses only the metadata fields and checked revisions in the registry. It does not infer missing files or label semantics.

Evidence bindings:

- registry: `docs/datasets/paper-public-source-registry-v1.json`, SHA-256 `53fb2acb004925a71c75a1a2d7e86e64ada92eb606eb785370a59c2b0a045a58`;
- RQ2 acquisition card: `docs/datasets/2026-10-04_rq2_identification_and_acquisition_card.md`, SHA-256 `05f345518658ce48de95b5887f94dea3ba64df2047381ff176180348ce094347`;
- Route V exact annex: `docs/datasets/2026-10-05_valentine_route_v_exact_annex_v1.json`, SHA-256 `00e781a6917f7334a1ffcaa9b11d7c2fe1e8edc9415c449f7458ffbed9b6de17`.

## 2. Registry-wide result

| Dataset | Checkpoint evidence | Action/target fit | Correctness fit | Independence / role fit | Metadata verdict |
|---|---|---|---|---|---|
| `tatqa` | Not an audited same-sample checkpoint bridge in the registry | Adapter and Q3 review required | Historical exposure audit still required | `HISTORICAL_ONLY_UNTIL_EXPOSURE_AUDIT` | Reject for confirmatory RQ2 |
| `finqa` | Gold programs / process supervision are available | Programs are explicitly not `map_to/hold/skip` labels | Program gold is not independent Q3 action correctness | Separate `finqa_financial_reports` namespace; usable for process supervision | Process-only; reject as direct bridge |
| `convfinqa` | Conversational process extension | Same non-action program semantics | No independent action correctness chain | Same FinQA namespace and explicitly not an independent test | Reject as independent bridge |
| `multihiertt` | Programs and supporting facts need an adapter | No native `map_to/hold/skip` target contract | Independent action correctness absent | External/long-process stress role only | Adapter-heavy; reject without new task definition |
| `valentine_nyc` | `_full/_result/_trajectory` are not accepted checkpoint evidence without semantic audit | Gold matches support `map_to` only; `skip/hold` require Q3 | Corrected Q3 exists for 10 pairs but has visibility exceptions | 10 eligible pairs at fixed revision; target 40, gap 30 | Exploratory only; reject as confirmatory bridge |
| `hitab` | Hierarchical-table stress material | QA/NLG labels need adapter; no pair action ontology | No independent action correctness chain | Hierarchy external stress only | Reject as direct bridge |
| `gittables` | Natural header proposal pool | No pairwise gold without adapter | No pairwise correctness | Proposal/pretraining pool; namespace is not row-level clusters | Reject as direct bridge |
| `sherlock_viznet` | Semantic-column baseline/pretraining | Type labels are not pairwise match labels | No pairwise action correctness | Semantic columns cannot serve as independent pair clusters | Reject as direct bridge |
| `hybridqa` | Broad external process stress | QA labels need adapter | QA correctness is not action correctness | Shared Wikipedia hybrid namespace | Reject as direct bridge |
| `ottqa` | Retrieval-heavy external stress | QA labels need adapter | QA correctness is not action correctness | Shared Wikipedia hybrid namespace | Reject as direct bridge |

**Result:** `0/10` registry candidates currently provide a direct, auditable same-sample bridge satisfying all four requirements. This is a registry-scoped result, not a claim that no suitable public source exists anywhere.

## 3. Route V-specific consequence

Route V is still the only candidate within the currently approved source/revision/task family. However, the official tree at revision `5d5163f04da304985bd51a476ccf7653de3979c3` contains exactly 10 eligible pair directories and no eligible new pair directories. The approved target is at least 40 independent pair clusters, so the acquisition gap remains **30 clusters**.

The current Route V materials can support exploratory labelability and simple-baseline analysis. They cannot support confirmatory RQ2 because:

- the accepted checkpoint bridge remains incomplete;
- `proposal_train.dev=0` under frozen bucketing;
- Q3 visibility exceptions remain;
- cluster and power requirements are not met.

## 4. Candidate routes requiring new approval

No route below is selected or approved by this report.

1. **New official source annex**: identify a repository/revision with native same-sample checkpoint, action/target, correctness, and at least enough independent clusters; provide exact paths, hashes, owner, licence scope, and permitted uses before download.
2. **Adapter route**: define a new action ontology and independent review contract for a process-rich source such as FinQA or MultiHiertt. This requires a new task definition, licence annex, schema/adapter receipt, Q3 chain, split analysis, and power receipt. It must remain separate from Valentine.
3. **Exploratory-only retention**: keep Route V at 10 pairs for exploratory evidence and formally retain `DATA_NO_GO / RQ2 NOT_IDENTIFIED` until new evidence is approved and delivered.

## 5. Boundary conclusion

The current metadata screen does not identify a confirmatory RQ2 source. Therefore `RQ2_NOT_IDENTIFIED` and `DATA_NO_GO` remain authoritative. No source is added, downloaded, reinterpreted, or promoted by this report. Any new source, revision, task definition, schema adapter, or licence scope requires a new exact annex and separate user approval.
