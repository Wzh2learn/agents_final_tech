# NtripBrowser Behavioral Probe

Date: 2026-10-21, Asia/Shanghai

Status: `BOUNDED_BEHAVIORAL_CASE_COMPLETE`

## Result

| Arm | Hidden tests | Target structure | Hybrid result | Tokens |
|---|---:|---:|---:|---:|
| BASE | 7/7 | fail | fail | 4,224 |
| PROSE_CHANGE_FACTS | 7/7 | pass | pass | 4,176 |
| STRUCTURED_CHANGE_FACTS | 7/7 | pass | pass | 4,212 |

All three generated modules passed the seven deterministic hidden tests. BASE
nevertheless failed the intended migration: it called `chardet.detect` without
importing `chardet`, caught the resulting error, and fell back to UTF-8. The
mocked UTF-8 fixtures therefore passed despite a missing detector.

PROSE and STRUCTURED both imported `cchardet`, called `cchardet.detect`, removed
`chardet`, and passed the same tests.

## Scientific Interpretation

The main result is **not** that prose or structured facts are superior. Both
explicit-change arms succeeded on this one task.

The result is that behavioral tests alone can produce a false positive for a
dependency-migration contract. The intended change requires both:

1. hidden behavioral tests for preserved observable behavior; and
2. a structural dependency/API contract for the requested external change.

BASE passing tests while violating the migration is direct evidence for this
oracle-design issue in this case.

## Scope

- One real PyMigBench commit and one module.
- One deterministic model/configuration sample per arm.
- Seven local/mocked tests; live-network tests remain excluded.
- No claim about general migration capability or representation superiority.

Raw requests, responses, candidate snapshots and JUnit files are under `raw/`.

## Source-Level Context

A zero-model audit of 36 PyMigBench candidate commits found 33 auditable
records: 20 changed dependency manifests, 19 named the target dependency in
those manifest diffs, and 13 were code-only with no manifest contract. The
qualified NtripBrowser task is one of those code-only records. This supports
treating dependency installation and target-library identity as an explicit
task contract rather than assuming the commit's tests expose it.
