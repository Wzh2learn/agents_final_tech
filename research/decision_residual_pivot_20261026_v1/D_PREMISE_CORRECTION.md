# D Premise Correction And Execution Gate

Goal ID: `DECISION_RESIDUAL_PILOT_20261026`
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority commit: `19ddd7feffe90779f021304345ce894550c92816`
Authority identity:

- Git blob: `5c3f970db754b0ce712161373c74fa34c36d42d0`
- Canonical GB10 LF SHA-256: `327fb04ae18ff6e057338f28686389d183c24a797e22c325e8557cbea58f0cbe`
- Windows raw SHA-256: `e4c53572a01e1d0b6a86e7377948a8e2416dd3d9ffbcce43f2a40d715d4b7ef2`
  (noncanonical line-ending view; not the authority digest)

## Decision

Keep `STOP_CURRENT_R_E_IMPLEMENTATION`. Do not resume old R/E, confirmation or
second seed. The correction below narrows the interpretation of those results;
it does not reopen the candidate.

## Independently Verified Corrections

1. **Effective parent continuation was not satisfied.**
   `B2_TRAIN_RUN.py` loads `ordinary_parent`, adds `b2_child`, then calls
   `model.set_adapter("b2_child")` before training. Installed PEFT 0.21.2 states
   that only one adapter is active at a time. A fresh CPU counterexample produced
   parent `[[2,2]]`, child/base `[[0,0]]`, with the parent hash unchanged.
   Therefore preserved parent weights do not prove ordinary-parent forward
   computation. R/E are child-only continuation experiments.

2. **Generation responsibility also needs separation.**
   N activates `ordinary_parent`; R/E load and activate a child adapter. File
   presence and hash consistency do not prove equivalent parent composition.
   Future candidates must compute canonicalization, SHA-256 and integrity
   metadata in tools. Models choose semantic facts or bounded actions.

3. **The learning denominator is small and repeated.**
   There are 5 qualified set-binding corrections across 3 source families.
   Each arm presents 39 correction rows and 217 no-op/unresolved rows for 256
   rows, while only 36 unique trajectories and 12 source tasks exist. The
   asymmetric pad weights the five correction identities as `11/7/7/7/7`;
   `39` is presentation count, not 39 independent corrections. Loss is
   computed over all non-padding prompt-plus-target tokens. These are disclosed
   confounds, not proven causes.

4. **The target is a set-binding proxy, not full semantic correctness.**
   Training references may legally contain correct program, direction and unit
   labels. The old experiment intentionally preserved O direction and excluded
   unit/operator changes. Three of five eligible targets are sign-reversed
   relative to the audit reference. They cannot be called answer-correct
   repairs.

5. **Output layers remain separate.**
   O/N are strict whole JSON. Repaired R/E are 36/36 embedded JSON and 36/36
   `MAX_NEW_TOKENS`. E fails first on keys/schema; hash requirements are an
   additional contract burden but are not proven to be the sole cause. Installed
   TRL contains automatic EOS handling, so missing explicit EOS is not a
   verified root cause.

## Metric Correction

- O 27/36, N 26/36, R 25/36 and E 0/36 are `SET_BINDING_SET_ACCURACY` counts on
  36 exposed development trajectories.
- They are not answer-correctness counts.
- R-N has an unmatched configuration and an interval crossing zero. The valid
  conclusion is `NO_GAIN_OBSERVED_IN_THIS_CONFIGURATION`, not a clean causal
  rejection of full revision.
- E is an implementation/representation failure. It does not disprove local
  editing or feedback learning in general.

## Pre-Probe Gate

A new probe is allowed only if a candidate has:

1. Natural decision input and a full semantic reference.
2. At least one deployable action whose value is not already supplied by a
   strong simple baseline.
3. Observable deployment inputs and bounded legal tools.
4. A falsifier showing when the candidate is unnecessary.
5. No old R/E panel renaming, artificial masking presented as natural missing
   evidence, hidden gold in actor input, or oracle arm reported as deployable.

The probe is a development qualification only. It cannot establish a method,
new-source generalization, or thesis contribution.
