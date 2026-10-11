# Stage E Paper Upgrade Plan v1

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 拆分 Paper E 与 Paper D；不改变 current canonical manuscript

## 1. Paper route

**Paper E, near term:** *Visibility Is Not Detection* + quantified observation boundaries + multi-stage/multi-leaf validation.

**Paper D, longer term:** *Evaluation-Guided Distillation* / *Process-Evidence-Guided Data Selection*.

`VALUE`: do not merge Stage D into Paper E before a real C4-C2 result exists.

## 1.1 Contribution versions

VERSION A, currently supported:

1. Separate visibility, detection and equivalence-dependent harmfulness as distinct constructs.
2. Quantify observation boundaries with per-family VR, micro VR, worst-family VR and visibility-conditioned detection.
3. Audit protocol identifiability: flat/hierarchical affine-rank equivalence in the single-responsive-leaf setting, with clean-only matched-FPR equality not identifiable.

VERSION B, requires multi-leaf:

1. Keep the three Version A contributions.
2. Add multi-stage checkpoint visibility signatures across M/R/N.
3. Add evidence that checkpoint signatures contain stage-localizing information; do not attribute localization to the hierarchy itself.

Future-only: transfer to a second dataflow and Stage D distillation remain outside Paper E until their own evidence gates pass.

## 2. Stage E upgrade order

1. Replace headline metric sprawl with per-family VR, micro VR, worst-family VR and `P(D|V=1)`.
2. Move BR/macro to secondary and `P(D|V=0)` to diagnostic.
3. Move operational HBR to appendix; semantic HBR remains future.
4. Report OCR as two estimands with separate intervals.
5. Split structural affine equivalence from empirical matched-FPR equality.
6. Add multi-leaf preregistration as the next experiment, not a current result.

## 3. Framing

Academic anchor: NIST asks whether metrics and TEVV are appropriate/effective. Our narrower question is whether the evaluation protocol observes the controlled failures it is supposed to assess.

Industry motivation: one short ITIL/ITSM paragraph on service lifecycle, continual improvement, oversight, risk and accountability. No method claim, certification or ITIL attribution beyond official page wording.

## 4. Introduction logic

1. Long-horizon AI services require process and measurement validity.
2. Final correctness can hide invisible failure modes.
3. Separate visibility, detection and harmfulness.
4. Controlled injections expose observation boundaries.
5. Quantify family/overall/worst-case visibility and conditional protocol use.
6. Repair matched-FPR interpretation through clean-only identification analysis.
7. Use multi-leaf design to test whether stage localization becomes measurable.

## 5. Remaining top evidence gaps

1. Multi-leaf stage localization result with adequate clusters and independent responsive leaves.
2. Independent second scorer/second dataflow reproduction.
3. Licence-cleared same-sample process/outcome source and powered C4-C2 result.

## 6. Gate recommendation

- Stage E quantification: `GO` for paper upgrade, with corrected matched-FPR wording.
- Matched-FPR corrected analysis: `NO-GO` for empirical equality claim; `GO` for structural affine result and blocker report.
- Multi-leaf formal experiment: `READY_TO_EXECUTE_NEEDS_USER_APPROVAL`; M/R/N sample freeze and predictor are complete, but formal scoring is not authorized.
- PRM reference smoke: `GO` for metadata/static reference use, `NO-GO` for training.
- Stage D formal training: `NO-GO`; PRM reference validation and Agent Distillation adapter smoke may proceed as non-commercial academic work.
