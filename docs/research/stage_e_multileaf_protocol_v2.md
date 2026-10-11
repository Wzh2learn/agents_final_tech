# Stage E Multi-Leaf Protocol v2

Status: `DESIGN_ONLY_NOT_AUTHORIZED`

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

This protocol extends the frozen single-responsive-leaf evidence without changing any frozen Stage E number, threshold, denominator, equivalence definition, or claim boundary. It is a future experiment design, not a result and not authorization for Phase 2, Stage R, E-D-R, model calls, judge calls, training, or production access.

> **2026-10-09 supersession note:** `stage_e_multileaf_preregistration_v1.md` is the active three-stage Stage M/R/N contract. The H2 matched-FPR primary and `90/111 versus 90/111` below are retained only as historical/sensitivity evidence. The clean-only reanalysis marks empirical matched-FPR equality `NOT_IDENTIFIABLE`; the active multi-leaf primary is stage-level localization and visibility-signature separability.

## 1. Source record before conclusions

The pre-conclusion source register is [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json); the frozen-input receipt is [`source_data_receipt.json`](../../research/stage_e_stage_d_20261009/source_data_receipt.json).

| Record | Revision / licence / schema evidence | Exact blocker |
|---|---|---|
| Frozen Stage E artifacts | Seven named JSON hashes are recorded in the source receipt; join key is `(uid, col)`; bootstrap cluster is table UID | No second independent implementation or external corpus is present |
| Existing multi-leaf design | [`2026-10-08_stage_e_inquiry_and_experiment_design_v1.md`](2026-10-08_stage_e_inquiry_and_experiment_design_v1.md), section 9 | Status remains design-only |
| NIST AI RMF Core and Playbook | Official URLs, page revisions, NIST licensing statement, and Core/Playbook wording are recorded in the source audit | They provide governance framing only, not this protocol's threshold or formula |
| External candidate audits | Reused fixed-revision reports are listed in the source audit | No inspected source proves an executable responsive multi-leaf matrix |

`FACT`: all cited source identities, revisions, licence status, schema evidence, and blockers are recorded before the design conclusions below.

## 2. Research question and hypotheses

**Research question.** When operating points are fixed by clean calibration and at least two preregistered scored leaves respond to the same injected input, does a hierarchical protocol produce a reproducible matched-FPR detection difference over a flat protocol?

| ID | Preregistered prediction | Failure interpretation |
|---|---|---|
| H1 | At least two responsive leaves occur in the frozen injection × leaf matrix before any score inspection | Fewer than two: `STOP_BEFORE_ANALYSIS` |
| H2 | Historical/sensitivity only: matched-FPR hierarchical-minus-flat detection difference | Superseded for the active three-stage experiment; empirical equality is `NOT_IDENTIFIED` |
| H3 | Visibility, detection, and harmfulness remain separate constructs | Any substitution invalidates the run |

`VALUE`: H2 is chosen because it tests a localization-capable mechanism at a fixed false-positive operating point rather than converting raw detection or visibility into a localization claim.

## 3. Constructs and denominators

| Construct | Independent measurement | Frozen reference |
|---|---|---|
| Checkpoint visibility | `visible_frozen` under the absorption-based frozen rule | `96/118` visible; `22/118` blind |
| OCR negative-observability control | family denominator 13 | `0/13` visible |
| End-to-end detection | protocol-positive injections | `112/118` |
| Flat detection at frozen/raw operating point | protocol-positive injections | `85/118` |
| Hierarchical detection at frozen/raw operating point | protocol-positive injections | `13/118` |
| Matched-FPR evaluation | harmful `H ∪ HI` denominator | historical/sensitivity `90/111` versus `90/111`, CI `[0,0]`; not the active primary |
| Table-level calibration | table denominator | 95 tables; 88 matched-FPR table clusters |

`FACT`: these values are immutable reference values, not new outcomes of the future protocol.

`FACT`: table-level detection remains on 95 tables, injection-level visibility and detection remain on 118 injections, harmful matched-FPR remains on 111, and family rates retain their own family denominators. They are never merged into one partition.

## 4. Leaf matrix

The future matrix must contain, before any result inspection:

```text
row:    injection_uid × table_uid × origin_cluster
column: preregistered leaf_id × leaf_version
cell:   raw_score, threshold_flag, calibration_role, evidence_hash
```

Required leaves include:

1. flat score leaf;
2. hierarchical score leaf;
3. end-to-end signal leaf;
4. at least one changed parser/table leaf if a valid second dataflow becomes available.

`INFERENCE`: the current single-leaf evidence cannot support a localization claim. Adding planned columns is not enough; H1 is evaluated only when the pre-score matrix shows at least two cells that change with the injected input while table/UID membership stays fixed.

`UNVERIFIED`: no inspected external artifact supplies a ready same-sample, UID-disjoint responsive leaf matrix.

## 5. Split, calibration, and isolation

1. Use table or actual table-origin/lineage cluster as the independent unit.
2. Before any score, visibility, detection, or outcome inspection, apply a hash-bound rule to assign entire clusters to `calibration`, `evaluation`, or `sensitivity`.
3. Keep every injection from a table and every table from an origin in exactly one role.
4. Prohibit same UID/origin across roles.
5. Prohibit split stratification by injected label, visibility, detection, harmfulness, or sealed result.
6. Calibrate flat and hierarchical operating points only on clean calibration records.
7. Freeze scores, thresholds, leaf definitions, family definitions, and code hashes before evaluation.

`FACT`: the existing 95 tables and 118 injections stay unchanged. A future synthetic protocol namespace may add mapping metadata but may not rewrite the corpus.

## 6. Metrics and statistical analysis

### Primary

```text
Delta_primary =
  TPR_hierarchical_at_matched_clean_FPR
  - TPR_flat_at_matched_clean_FPR
```

- Report raw numerators and denominators before percentages.
- Estimate uncertainty with a paired table-cluster bootstrap.
- Keep all injections from a sampled table together.
- Report point estimate, 95% interval, responsive-leaf count, and per-cluster contributions.
- Do not treat 118 injections as independent Bernoulli units.

### Secondary

- injection visibility and blindness overall and by family;
- threshold-conditioned visibility at every preregistered gamma;
- `VD`, `VU`, `BD`, and `BU` cells for each leaf/protocol;
- `P(D|V)`, `P(D|B)`, and blindness among misses;
- raw and matched-FPR detection on their correct denominators;
- trace/hash reproducibility and threshold stability;
- family-wise OCR and prefix sensitivity as predefined controls.

`FACT`: OCR `0/13` remains a table-clustered structural observation. No naive independent-Bernoulli confidence statement is permitted.

## 7. Baselines and controls

| Class | Controls |
|---|---|
| Frozen references | `96/118`, `0/13`, `112/118`, `85/118`, `13/118`, `[0,0]` |
| Protocol controls | flat, hierarchical, end-to-end, greedy/Hungarian |
| Weight controls | equal, expert, random, greedy, PSO, minimax |
| Negative controls | OCR family and frozen prefix-noise family |

`FACT`: PSO and greedy mean performance is a frozen null result; optimizer naming cannot select a winning protocol.

`FACT`: the literal family-range predicate failed at `gamma=0.7` and `gamma=0.9`; that failure remains preserved and is not silently repaired.

## 8. Stop and decision rules

Stop before analysis if any of the following holds:

- fewer than two responsive leaves;
- fewer than two non-empty cluster roles or insufficient preregistered clusters;
- split, UID, origin, or calibration leakage;
- threshold/family/leaf changes after score inspection;
- frozen artifact or claim-boundary modification;
- harmfulness or visibility is substituted for detection;
- target/ground-truth access;
- model, judge, training, GPU, database, service, credential, paid API, Phase 2, Stage R, or E-D-R action;
- required source revision, licence, schema, or provenance remains unproved;
- the analysis script or frozen-anchor check fails.

`VALUE`: if H2 is not supported, the correct conclusion is `NOT_IDENTIFIED`, not threshold repair, family expansion, or a changed denominator.

## 9. Execution state

| Action | State |
|---|---|
| Protocol design | Complete |
| Matrix/threshold/split fixture | Not constructed |
| Gold-free smoke | Not run |
| Responsive-leaf adjudication | Not run |
| Confirmatory matched-FPR comparison | Not run |
| Model/judge/training/service/database | 0 |
| Phase 2 / Stage R / E-D-R | Not started |

`FACT`: this document does not authorize execution. Future work requires a separate task card, static feasibility review, source/revision/licence/schema closure, and explicit authorization.
