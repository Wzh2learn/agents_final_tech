# Third Contribution Qualification: Evidence Reuse Under Changed Conditions

Date: 2026-10-22, Asia/Shanghai

Status: `TRANSPARENT_INVALIDATION_CONTINUE / SCOPE_METHOD_PAUSED`

## Question

When prior behavioral evidence was produced under one dependency and input
regime, when may it be reused after conditions change, and when must it be
revalidated?

## Low-Cost Probe

The probe reuses real module executions already collected on GB10:

- 24 repository fixtures provide the original behavior regime;
- three short byte inputs provide a second observable regime;
- five overlapping candidates include natural parent/migration commits and
  manual controls.

Global reuse of the real-fixture result makes two false transfers: the natural
migration commit and alias control pass the fixture regime but differ from the
parent under the short-input regime.

| Policy | Correct | False transfer | Abstain | Unnecessary revalidation |
|---|---:|---:|---:|---:|
| Never revalidate | 3/5 | 2 | 0 | 0 |
| Dependency change only | 5/5 | 0 | 0 | 2 |
| Exact input reuse only | 0/5 | 0 | 5 | 0 |
| Dependency + input-regime scope | 5/5 | 0 | 0 | 3 |
| Always revalidate | 5/5 | 0 | 0 | 3 |

## Qualification Judgment

The broader problem is qualified for bounded development: evidence can fail to
transfer across observable regimes, and transparent invalidation prevents the
false transfer. However, the **scope fingerprint adds no identified increment**
over dependency-change invalidation on the current cases. It creates one extra
unnecessary revalidation.

The next qualifying case must change the input regime while keeping dependency
identity fixed. Without such an orthogonal case, do not develop a learned
evidence-expiry or scope-prediction method. The current defensible contribution
is a measurement boundary plus a simple dependency-invalidation rule, not a
third validated method.
