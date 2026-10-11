# Stage E Narrative After Advisor Feedback v1

Status: narrative clarification only; the canonical manuscript and frozen evidence are not edited by this deliverable.

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

## 1. Feedback and source record

The pre-conclusion source register is [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json). Project feedback is read from [`paper/teacher_review_note_v2.md`](../../paper/teacher_review_note_v2.md) and [`paper/teacher_review_readiness_v2.md`](../../paper/teacher_review_readiness_v2.md).

`FACT`: the canonical Stage E manuscript is [`paper/teacher_review_draft_v1.md`](../../paper/teacher_review_draft_v1.md); this document does not modify it.

The feedback items addressed narratively are:

1. visibility must not be called detection;
2. OCR `0/13` must retain its direction and definition-dependent harm boundary;
3. raw hierarchical and flat detection cannot be compared without their operating points;
4. matched-FPR evidence does not prove localization;
5. multi-leaf responsiveness and a changed second dataflow remain separate unresolved evidence priorities;
6. harmfulness definitions remain unresolved and cannot be selected retrospectively;
7. future evidence must not be converted into present results.

## 2. Revised one-sentence thesis

**Revised narrative.**

`VALUE`: A long-horizon document evaluator can silently absorb defect types that its intermediate checkpoint does not represent; once visibility, detection, and operational harmfulness are reported as separate constructs at explicit operating points, the apparent hierarchy advantage in raw detection collapses to a matched-FPR null on the frozen corpus.

This wording preserves the project's central distinction:

- `INFERENCE`: **visibility** is evidence that an intermediate representation changed;
- `INFERENCE`: **detection** is a protocol decision;
- `INFERENCE`: **harmfulness** is an operational consequence class under a stated criterion/equivalence path.

## 3. Result narrative with frozen boundaries

| Narrative beat | Frozen evidence | Allowed claim |
|---|---|---|
| Observable region | `96/118` visible, `22/118` blind | The absorption-based checkpoint records a change for 96 injections |
| Family dependence | alias `43/47`, date `15/17`, mixed `20/20`, OCR `0/13`, prefix `13/16`, unit `5/5` | Visibility is defect-family dependent |
| Negative control | OCR `0/13` | Character-similar header perturbations are unrepresented by the tested checkpoint; whether that equals operational harm depends on the equivalence path |
| End-to-end protocol | `112/118` detected | End-to-end positives are not checkpoint visibility |
| Flat raw protocol | `85/118` detected | Raw flat positives are not proof of superior sensitivity |
| Hierarchical raw protocol | `13/118` detected | Raw hierarchical positives are not proof of inferiority without operating-point calibration |
| Matched-FPR | harmful `90/111` versus `90/111`, CI `[0,0]` | Current corpus shows a null TPR difference after clean calibration |
| Threshold curve | `85,45,29,13,13` of 118 across gamma `0.2,0.3,0.5,0.7,0.9` | Threshold-conditioned visibility is distinct from `visible_frozen` |
| Weight search | PSO and greedy equal mean performance at large cost ratio | Informative null, not a headline contribution |

`FACT`: none of these values changes.

## 4. What the paper can claim

### FACT / VALUE boundary

`FACT`: the frozen corpus contains 95 tables and 118 injections and produces the recorded visibility, detection, threshold, family, and matched-FPR values.

`INFERENCE`: the results show that evaluator observability and protocol detection are not interchangeable on this corpus.

`VALUE`: the strongest contribution is a measurement-discipline result: an evaluator can have a stable blind family while a downstream protocol still reports positives from other signals.

`VALUE`: matched-FPR equality is an informative null that narrows the protocol claim rather than a reason to retune or hide the hierarchy result.

## 5. What the paper cannot claim

| Prohibited conclusion | Reason |
|---|---|
| “The hierarchy detects 13/118 while flat detects 85/118, so flat is superior” | Raw operating points are not matched |
| “Visibility is detection” | Different predicates and information sources |
| “All 22 blind cases are harmful misses” | Semantic harmfulness-conditional blindness is `UNVERIFIED` |
| “OCR proves a 0% population blindness rate” | 13 clustered injections are not a population Bernoulli sample |
| “Matched-FPR proves hierarchical localization superiority” | Difference is `[0,0]`; localization is not established |
| “A second scorer/dataflow confirms the result” | Deferred evidence has no result |
| “Stage D/R/E-D-R validates the paper” | No such execution occurred |
| “NIST or ITIL certifies the result” | Governance sources do not validate project metrics |

## 6. Advisor decisions left open

`UNVERIFIED`: the next evidence priority remains multi-leaf/multi-stage injection versus a changed second dataflow.

`UNVERIFIED`: canonical equivalence, reader-referent equivalence, or parallel harmfulness constructs have not been selected as a new primary definition.

`VALUE`: neither open decision may be resolved by rewriting existing Stage E evidence; both require future source/protocol decisions and, where applicable, separate authorization.

## 7. Revised conclusion paragraph

`VALUE`: Stage E demonstrates a bounded observability problem rather than a universal pipeline failure: under the frozen absorption rule, 96 of 118 injections are visible but the OCR-like family remains wholly unrepresented, while protocol detection changes sharply with structure and operating point. At matched harmful false-positive rate, the flat and hierarchical protocols are indistinguishable on this corpus. The defensible contribution is therefore construct separation and transparent negative evidence, not a claim of broad localization, external validity, or completed Evaluate–Distill–Evolve validation.

## 8. Execution boundary

`FACT`: this narrative change runs no model, judge, training, GPU, database, production service, credential, Phase 2, Stage R, or E-D-R action and changes no frozen hash, schema, test, manuscript, claim manifest, `STATE.md`, `THREADS.md`, `docs/33*`, or `docs/34*`.
