# Stage D DATA_NO_GO boundary and future requirements（2026-10-05）

> Status: `DATA_NO_GO / RQ2_NOT_IDENTIFIED`
> Stage D necessity: `PILOT_ONLY`
> Goal: `ACTIVE`; this is a valid boundary result, not a failed experiment to be made green by rerunning.

## 1. Formal conclusion

The current evidence does not identify a confirmatory RQ2 effect and does not authorize Stage D training.

The evidence is stronger than the earlier “no bridge” state but still insufficient for confirmation:

1. Q3 provides corrected action/target/correctness labels for 146 Valentine columns.
2. The gold-free process adapter provides checkpoint/action events for the same 10 pair/lineage clusters.
3. Therefore an exploratory same-sample linkage can be constructed.
4. However, the data have only 10 independent clusters, `proposal_train.dev=0`, Q3 visibility is not strict three-field-only, R2/ADJ lack separate signed visibility receipts, and the mandatory split sensitivity is unstable.
5. The Stage D necessity gate is `PILOT_ONLY`; B4 cannot be declared sufficient and a dedicated student cannot be declared necessary.

Accordingly, `DATA_NO_GO` and `RQ2 NOT_IDENTIFIED` remain authoritative.

## 2. Gate-by-gate status

| Gate | Status | Evidence / missing condition |
|---|---|---|
| SOURCE_GO | PARTIAL | D-C sources are downloaded and hashed; no approved source currently supplies enough independent same-sample clusters for confirmatory RQ2. |
| LABEL_GO | EXPLORATORY_ONLY | Corrected Q3 ledger is sealed, but visibility exceptions prevent treating it as strict confirmatory blind review. |
| SPLIT_GO | BLOCKED | Valentine has 10 clusters and `proposal_train.dev=0`; G-A/G-B remain unapproved, so it cannot carry gate/sealed. |
| POWER_GO | BLOCKED | No real development-side variance, MDE, minimum UID/family coverage, or signed power receipt. |
| BASELINE_GO | PILOT_ONLY | B4 is the baseline to beat; risk admissibility is not stable across the mandatory salted sensitivity. |
| MODEL_GO | ARTIFACT_READY_NOT_AUTHORIZED | Qwen3-4B/Qwen3-8B revisions, tokenizer/licence and manifests are validated on GB10. Formal execution still waits for scientific gates, stable residual, and the conditional training window. |
| SAFETY_GO | DESIGN_READY_NOT_RUN | GB10 thresholds and isolation rules exist, but no training/replay execution has been authorized. |

## 3. What would change the conclusion

### 3.1 Data source

One of the following must be approved and delivered:

1. Valentine Route V expansion to at least 40 independent table-pair/origin clusters with exact official paths, revision, bytes, hashes, and licence scope; or
2. another source that natively supplies the same sample with checkpoint evidence, action/target semantics, correctness, and enough independent origin clusters.

FinQA and Valentine must remain separate namespaces. FinQA cannot be forced into `map_to/hold/skip` semantics. TAT-DQA remains frozen; historical TAT-QA remains non-confirmatory.

### 3.2 Labels and visibility

For confirmatory use:

1. corrected final label ledger;
2. independent R1/R2/ADJ outputs and adjudication;
3. separate signed visibility receipts for every reviewer;
4. a strict visibility contract that prevents gold, pipeline mapping, injection maps, lineage grouping, and cross-reviewer output leakage, or a preregistered disclosure that explicitly accepts lineage visibility as a limitation;
5. artifact hashes bound to the exact input package.

### 3.3 Split

The accepted source must produce non-empty `proposal_train.train`, `proposal_train.dev`, `gate_validation`, and `sealed_test` under the approved role policy, without changing frozen bucketing merely to force non-empty layers.

All columns/events/rules derived from one lineage UID must remain in one layer.

### 3.4 Power and analysis

Before Stage D:

1. measure development-side paired variance;
2. calculate MDE and achieved power under the approved `alpha=0.05`, `target_power=0.80`, and non-inferiority margins `0.02`;
3. approve `minimum_uid_by_action` and `minimum_uid_by_role_family`;
4. sign and hash-bind the power receipt;
5. use cluster bootstrap with seeds `[42,43,44]`, treating seed dispersion separately and never as proof of power.

The 250–500 UID target applies to the H3a under-power remedy; it is not an automatic RQ2 sample-size promise.

### 3.5 Baseline necessity

B4 must be the comparator. Stage D becomes worth considering only if a stable residual remains after Q3/B0-B4 and the risk-constrained coverage result is stable across the mandatory sensitivities. `PILOT_ONLY` does not authorize A0-A2.

### 3.6 Model and safety

The model artifact side is ready, but only after SOURCE/LABEL/SPLIT/POWER/BASELINE gates pass and necessity is established:

1. revalidate the already-bound model/revision/tokenizer/template immediately before execution;
2. freeze training configuration and seeds;
3. sign MODEL_GO and SAFETY_GO;
4. run in an isolated worktree/output directory with resource monitoring and stop conditions.

## 4. Non-actions

This boundary report does not download data, install B5, dispatch a model, start Phase 2, start 4B/8B training, alter frozen criteria, or authorize external release.
