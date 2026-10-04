# RQ2 SOURCE / LABEL / SPLIT / POWER application v1（2026-10-05）

> Status: `PENDING_USER_APPROVAL / NO_DOWNLOAD / NO_SCHEMA_CHANGE`
> Purpose: exact application card for the next RQ2 data decision; this card does not authorize acquisition or training.

## 1. SOURCE

| Field | Application |
|---|---|
| Candidate route | Valentine Route V, kept separate from FinQA |
| Official source | `https://github.com/delftdata/valentine` |
| Revision | `5d5163f04da304985bd51a476ccf7653de3979c3` |
| Unit | one independent NYC table-pair directory = one lineage/origin cluster |
| Target | at least 40 independent pair clusters including existing 10 |
| Minimal per-pair files | `source_table.csv`, `target_table.csv`, `ground_truth.json` |
| Optional process files | `_full.json`, `_result.json`, `_trajectory.json` require separate semantic and visibility approval |
| Exclusions | FinQA test/private, PDF, other datasets, other Valentine directories, private data, unlisted files |
| Licence | D-B covers only `training / tuning / evaluation / rule_acceptance`; every new directory needs owner, licence, covered hashes, permitted uses |
| Current decision | G-C is not approved; no download is authorized |

## 2. LABEL

| Field | Application |
|---|---|
| Existing evidence | corrected Q3 ledger `51/58/37`, sealed raw R1/R2/ADJ package |
| Existing exceptions | R1 saw `lineage_root_id` / table grouping; R2/ADJ lack independent signed visibility receipts |
| Required for confirmatory use | three independent outputs, adjudication, final ledger, per-reviewer visibility receipts, package manifest/hash binding |
| Forbidden to reviewers | `ground_truth.json`, source gold, pipeline mapping, injection map, other reviewer outputs, final Q3 gold |
| Invalid references | Option A primary quarantine of turn 12/13/31; Option B whole-pair sensitivity remains mandatory |
| Current decision | exploratory label evidence only; `LABEL_GO` is not passed for confirmatory RQ2 |

## 3. SPLIT

| Field | Application |
|---|---|
| Unit | namespaced lineage UID / independence cluster |
| Layers | `proposal_train.train`, `proposal_train.dev`, `gate_validation`, `sealed_test`; `future_replay` may be empty with `LONGITUDINAL_EVIDENCE_UNAVAILABLE` |
| Current Valentine state | 10 clusters, `proposal_train.dev=0`, K=10 |
| Required | all four non-empty under approved role policy; no cluster or derived event crosses layers |
| Hash rule | reuse `research/phase1a_split_assign.py`; do not alter frozen bucketing to force non-empty layers |
| Current decision | `SPLIT_GO=BLOCKED`; G-A/G-B remain unapproved |

## 4. POWER

| Field | Application |
|---|---|
| Design starts | `significance_level=0.05`, `target_power=0.80`, `risk_limit=0.10`, `delta_quality=delta_harm=delta_retention=0.02`, `minimum_cost_reduction=0.10`, `seed_list=[42,43,44]` |
| Unit | lineage UID / independence cluster |
| Required | real proposal/train variance, MDE, achieved power, minimum UID by action and family, signed power receipt |
| Interval | paired seed×UID cluster bootstrap; seed dispersion separate |
| H3a note | the 250–500 UID target is the H3a under-power remedy, not an automatic RQ2 sample-size promise |
| Current decision | `POWER_GO=BLOCKED`; no power claim is available |

## 5. Decision request

User approval is required for each of the following before any acquisition or execution:

1. Route V target of at least 40 independent pair clusters;
2. exact new pair directory list and file-level scope;
3. licence/provenance annex for each new directory;
4. confirmatory label visibility policy;
5. split acceptance after the source is delivered;
6. power receipt and minimum UID/family values;
7. MODEL_GO / TRAINING_GO only after the previous gates and the necessity memo pass.

Until then: `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, no new download, no schema/licence expansion, no model or training.
