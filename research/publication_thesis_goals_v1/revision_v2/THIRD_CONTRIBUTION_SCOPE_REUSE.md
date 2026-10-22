# Third Contribution Qualification: Evidence Reuse Under Changed Conditions

Date: 2026-10-22, Asia/Shanghai

Status: `QUALIFIED_FOR_BOUNDED_DEVELOPMENT`

## Question

When prior behavioral evidence is collected for one input regime, can it be
reused after the input regime changes while the candidate and dependency remain
fixed? When must transparent scope metadata trigger revalidation?

## Corrected Temporal Comparison

The earlier probe incorrectly treated “candidate differs from parent” as
“dependency changed since evidence collection.” The corrected probe preserves
the actual temporal condition:

- candidate code and dependency are unchanged between observations;
- evidence first covers 24 real repository fixtures;
- the new observation uses three short byte inputs;
- only the input regime changes.

The same gold and alias candidates pass the fixture comparison but differ from
the parent on the short-input regime. Thus their earlier PASS is not valid for
the new regime.

| Policy | Correct | False transfer | Abstain | Unnecessary revalidation |
|---|---:|---:|---:|---:|
| Never revalidate | 3/5 | 2 | 0 | 0 |
| Dependency-change only | 3/5 | 2 | 0 | 0 |
| Exact input reuse only | 0/5 | 0 | 5 | 0 |
| Dependency + input-regime scope | 5/5 | 0 | 0 | 3 |
| Always revalidate | 5/5 | 0 | 0 | 3 |

Dependency-only invalidation misses both transfers because dependency identity
has not changed. Adding the input-regime component makes the scope fingerprint
identify the changed evidence condition and trigger revalidation.

## Qualification Judgment

The candidate is qualified for bounded development as a **transparent
scope-aware evidence invalidation** problem. The current probe supports the
mechanism and provides a falsifiable comparison, but it does not yet establish
a thesis contribution or a learned policy.

Next evidence needed:

1. a second natural module with the same dependency fixed and another input
   distribution change;
2. comparison against cost, coverage and abstention baselines;
3. a clear rule for scope granularity so broad fingerprints do not degenerate
   into always-revalidate;
4. independent outcome or repair decisions showing that avoiding false transfer
   improves a real task, not only an evidence-status label.
