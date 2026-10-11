# Shared Term Sheet — SOURCE_LOCAL_RESPONSE v1

> frozen: 2026-10-11 | closes audit-v1 GLOBAL condition (undefined shared term) | applies to PR-EXP-03/01/04/07

## Definition
`SOURCE_LOCAL_RESPONSE`: a response that is a pure function of the mutation target's own local state (the exact tokens/cells/structure the mutation wrote), computable without observing any state beyond the mutation point.

## Attribution rule
A repair's gain is "source-local-only" (and therefore NOT counted as a repair positive) unless the experiment's frozen operational test passes. Global minimum requirements: (i) duplicate-catch analysis (new catches must not be duplicates of the baseline channel's catches); (ii) the experiment's specificity/no-op arms must not fire for the new channel; (iii) no constant-1-style trivial rule may attain the gain.

## Per-experiment operational tests (frozen)
- PR-EXP-03: pass = (i) all new structural catches unique vs both baseline oracles at frozen rules; (ii) no-op/identity and value-only arms return 0 for the structural oracle; (iii) constant-1 rule documented to fail specificity.
- PR-EXP-04: source-locality is the failure mode under test; fingerprint-bound NULL branch + direct-codebook control + responsive-leaf overlap report operationalize it.
- PR-EXP-07: `full <= direct` binding NULL rule; "robust" additionally requires the non-direct subset to clear chance (frozen margin), so a direct/source-local-concentrated gain cannot be narrated as robust.
- PR-EXP-01: claim object restricted to SYNTHETIC_NULL_SUPPORT_REPAIR; source-local language not used.