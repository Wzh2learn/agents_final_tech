# Q3 exploratory adjudication result and B5 candidate addendum (2026-10-04)

> Status: user-confirmed result summary | Raw outputs and hashes: pending seal | Model calls: 0 in this record
> Authority: GB10 is the only execution/validation environment; this file records the user-confirmed result and the next contract.
> Scope: exploratory learnability evidence only. This is not Stage D closure, not DATA_GO, not RQ2 confirmation, and not training evidence.

## 1. Provenance correction

The user clarified that the Q3 review was performed by **three independent experts**, corresponding to R1, R2, and ADJ. Their outputs are accepted as the source of the summary below.

The raw R1/R2/ADJ outputs, adjudication ledger, and Q3 gold files are not yet present in this repository update. Before these numbers are treated as fully artifact-closed evidence, seal and hash:

- R1 output;
- R2 output;
- ADJ adjudication output;
- final Q3 label ledger;
- the visibility/gold-isolation receipt;
- the package manifest and dataset revision binding.

Until that sealing is complete, this file is an append-only status record of a user-confirmed result summary, not a substitute for the raw evidence bundle.

## 2. Reported exploratory result

| Item | Reported result |
|---|---:|
| Adjudicated Q3 labels | 146 / 146 |
| R1/R2 exact agreement | 119 / 146 = 81.51% |
| Action Cohen's kappa | approximately 0.727 |
| Both reviewers chose `map_to` | 41 |
| Target exact agreement among those 41 | 41 / 41 |
| Disagreements | 27 |
| Disagreement locus | action boundary, not target identity |
| Final `map_to` labels | 52 |
| Final `skip` labels | 58 |
| Final `hold` labels | 36 |

Arithmetic checks: `52 + 58 + 36 = 146`; `119 + 27 = 146`. These checks validate the reported summary only; they do not replace raw-output verification.

## 3. Evidence boundary

The result remains:

- exploratory learnability evidence;
- a labelability and ontology signal for the 146 Valentine source columns;
- not evidence that checkpoint filtering improves a student;
- not evidence for Stage D, Stage R persistent benefit, or RQ4;
- not a reason to change `RQ2 NOT_IDENTIFIED`;
- not a reason to lift `DATA_NO_GO`.

The 146 columns come from 10 lineage/table-pair clusters. Statistical summaries must therefore use table-pair or lineage-cluster uncertainty where applicable; `n=146` must not be treated as 146 independent experimental units.

## 4. B5 candidate: typed-decision baseline

Register a new exploratory candidate, without changing the frozen B0-B4 set:

```text
B5: Jev-like typed-decision baseline, PROPOSED_EXPLORATORY / NOT_RUN
```

The name must not imply that the closed-source Jev system was run. Candidate implementations mentioned by the user are `open-alternative-jev` and `jevos-v2`; both remain unverified dependencies. Before any install or execution, record source, licence, provenance, version/commit, dependency surface, and whether the implementation supports the required typed output. The `jevos-v2` yes/no limitation is not a valid substitute for the three-way action task.

### 4.1 Input contract

B5 sees exactly the same visible input class as the Q3 reviewers:

```text
source_header + canonical headers + LABEL semantics
```

It must not read or infer from:

```text
ground_truth.json
source-side correspondence gold
pipeline mapping
injection map
checkpoint scores
gain / collateral
gate decisions
model predictions
other reviewer outputs
```

### 4.2 Two-stage decision

1. Choose `action` from `map_to / hold / skip`.
2. If and only if `action = map_to`, choose exactly one target from the canonical headers.

Return target as `null` for `skip` and `hold`.

### 4.3 Required exploratory metrics

- action macro-F1;
- target exact match;
- harmful-map rate;
- hold/coverage;
- worst table-pair or family;
- calibration (ECE/Brier, optional but preferred);
- latency;
- token use;
- GPU/CPU cost.

The denominator for harmful-map, coverage, and target exact must be frozen before evaluation. Cost must separate one-off setup/training, per-sample inference, verification/gate cost, and amortized cost if reported.

### 4.4 Evaluation discipline

- A zero-shot run must freeze prompt, model/config, canonical reference, and output parser before the single evaluation pass.
- Any tuning or calibration must use a group-aware split by table/lineage UID.
- Never tune a threshold on all 146 rows and report the same rows as evaluation.
- Report cluster-level uncertainty for the 10 lineage/table-pair clusters.
- Keep all results exploratory and `paper_result=false` until independent acceptance.

## 5. Scientific question

B5 is a go/no-go probe for the necessity of a specialized student:

- If a general typed-decision baseline already solves action and target selection near the observed ceiling, reassess whether a dedicated 8B checkpoint-filtered student is warranted.
- If B5 is clearly weaker and a later A2 checkpoint-filtered student adds stable residual value under the same risk/coverage contract, that supports the Stage D motivation.
- Either outcome does not identify RQ2 by itself and does not authorize training.

## 6. Next actions

1. Seal and hash the three expert outputs, adjudication ledger, final Q3 labels, and visibility receipt.
2. Preserve the result as exploratory; do not convert it into Stage D or DATA_GO language.
3. Run the existing B0-B4 exploratory probe under its frozen contract.
4. Audit the B5 candidate implementation, licence, provenance, and dependency surface before any local install or run.
5. Only after those checks, decide whether to run B5 as a one-pass zero-shot probe or submit a group-aware tuning protocol.

## 7. Pre-seal receipt

The machine-readable inventory is [docs/datasets/phase1a_q3_seal_receipt_v1.json](../datasets/phase1a_q3_seal_receipt_v1.json). It records PRE_SEAL_INVENTORY_ONLY_BLOCKED_MISSING_RAW_ARTIFACTS: R1 output, R2 output, ADJ output, final label ledger, and visibility/gold-isolation receipt are not present in the accessible local/GB10 search scope. The existing r1/r2/adjudication files are empty input templates, so seal_complete=false. This summary remains user-confirmed and not artifact-closed.
