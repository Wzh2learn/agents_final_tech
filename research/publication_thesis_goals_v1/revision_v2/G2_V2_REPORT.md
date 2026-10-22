# G2 V2 Report: Actual-Module Consumption Qualification

Date: 2026-10-22, Asia/Shanghai

Status: `METHOD_INCREMENT_NOT_IDENTIFIED_STOP_CURRENT_MECHANISM`

## What Was Fixed

The earlier v2 verifier compared outputs from a fixed third sample and therefore
accepted code that called the detector but ignored its result. The replacement
`g2_contract_verifier_v3.py` now:

- executes the complete actual `partridge/utilities.py`, preserving module
  imports, aliases, helpers and state;
- binds the exact module and `setup.py` hashes;
- applies two paired interventions to the same `b"AB"` input with legal target
  results `latin-1` and `utf-16-le`;
- calls consumption only when the downstream output follows the target-result
  contract across the pair;
- separates `VALID`, `INVALID` and `UNRESOLVED`;
- keeps reference adjudication separate from predictions and records execution
  failures as unresolved rather than invalid.

The audit counterexample is now rejected because it calls `UniversalDetector`
but returns input-dependent hard-coded values. A cache with no target evidence
is `UNRESOLVED`, not silently invalid.

## Real Repository Binding

All evidence channels in `G3_REAL_ACTION_RESULTS_V2_COMPACT.json` execute the same
actual worktree module:

- natural parent commit `daefcbe...`;
- natural migration commit `09e89d9...`;
- source-fallback and alias controls;
- the exact audit counterexample;
- one natural Qwen3.6 model output.

The model candidate differs from the upstream migration only by
`line = bytearray(line)`. It passes the repository tests and the independent
24-fixture behavior comparison. Its reference is based on the gold diff and
independent execution, not on the verifier's own prediction.

## Strong Comparison

| Evidence policy | Correct | False accept | False reject | Unresolved |
|---|---:|---:|---:|---:|
| Repository tests only | 4/6 | 2 | 0 | 0 |
| Alias-aware static + repository tests | 6/6 | 0 | 0 | 0 |
| Alias-aware static + independent behavior | 6/6 | 0 | 0 | 0 |
| Paired consumption + independent behavior | 6/6 | 0 | 0 | 0 |
| Combined short-circuit | 6/6 | 0 | 0 | 0 |

The paired causal criterion is now technically valid: it rejects the old
counterexample and accepts aliases/helpers from the actual module. However, a
strong alias-aware static contract plus ordinary repository tests already
solves every current object. The natural model output also supplies no new
failure mechanism.

## Decision

Stop expansion of the current dependency-consumption method. Preserve the
negative necessity result:

> On the Partridge panel, causal target-result intervention is reproducible
> but has no identified accuracy increment over strong static and behavioral
> controls.

Do not generate more model candidates or migrate additional repositories for
this mechanism until an independent task exhibits a failure that the simpler
strong baseline cannot classify. The behavior-test blind spot remains a real
measurement finding, but it does not by itself establish a new method.
