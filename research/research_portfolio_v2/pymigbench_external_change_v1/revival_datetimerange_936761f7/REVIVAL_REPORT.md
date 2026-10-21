# DatetimeRange PyMigBench Revival

Date: 2026-10-21, Asia/Shanghai

Status: `ZERO_TASK_ENVIRONMENT_CONTRACT_INSUFFICIENT`

## Target

- Source: PyMigBench `dataproperty -> typepy`
- Repository: `thombashi/datetimerange`
- Parent: `10659da2b1812cbec4d218b71582f73029c62fb7`
- Gold: `936761f779c4f7dc8c2d4c03c47b6e7b6e978a89`
- Target tests: `test/test_datetimerange.py`
- Model calls: `0`
- Failed-environment retries: `0`

The parent and gold snapshots were taken with `git archive`. Separate Python
venvs installed only the requirements declared by each revision, followed by
the declared test requirements. Each test command ran once.

## Observed Results

| Snapshot | Environment | Exit | Result | Interpretation |
|---|---|---:|---|---|
| parent | parent declared requirements | 2 | collection error | `DataProperty==1.1.1` lacks `NOT_STRICT_TYPE_MAPPING` used by the parent source. The version floor is not a reproducible environment contract. |
| gold | gold declared requirements | 1 | 160 passed, 8 failed | Gold behavior is not reproducible under the declared requirements plus Python 3.12/UTC. Four failures require `tzdata`; four expose timezone-sensitive epoch conversion. |
| parent | gold declared requirements | 2 | collection error | The source dependency is absent as intended, but this cannot be labeled F2P because gold itself does not pass. |

No F2P or P2P set is valid. The gold run is preserved in full rather than
reduced to a failure count. It shows substantial test discovery and execution,
but `gold_all_tests_pass=false`.

## Why This Is Not Rescued

Installing `tzdata`, pinning historical transitive versions, or changing the
system timezone would change the environment after observing failures. That
would be a retry and would risk manufacturing a green oracle. The current
revision's requirements do not specify these conditions.

## Minimum Next Gate

A future PyMigBench task is eligible only if its freeze includes:

1. exact Python and OS timezone/data contract;
2. exact direct and transitive package lock;
3. one predeclared test command;
4. gold `all_tests_pass=true` before model calls;
5. parent/gold classification computed from the same frozen evaluation
   environment;
6. structural target-library checks separated from behavioral tests.

This is an environment qualification result, not evidence against the
PyMigBench source or the migration hypothesis.

## Evidence

- Commands, versions and JUnit: `evidence/logs/`
- Machine receipt: `REVIVAL_RECEIPT.json`
- Candidate boundary: `TASK_CANDIDATE.json`
- Protected GB10 cache:
  `~/wzh/protected_research_20261021_v1/external_sources/pymigbench_task_repos/revive_datetimerange_936761f7`
