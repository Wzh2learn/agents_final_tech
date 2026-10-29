# Exposed Partridge migration: offline feasibility qualification

Date: 2026-10-29. Ruling: `REAL_SOURCE_REPLAY_PASSED_SKILL_METHOD_NOT_QUALIFIED`.

## Case and provenance

The upstream [remix/partridge commit 09e89d9](https://github.com/remix/partridge/commit/09e89d98b5a00db44394204d2f3e70c220b51764) actually replaces `chardet` with `cchardet`; the project's [release history](https://partridge.readthedocs.io/en/stable/history.html) describes the change and notes detectors can differ in output. The checked-out source contains an MIT license. Parent is `daefcbe6a03e92a0bfc0c2433279b9fd3d179f6c`; child is `09e89d98b5a00db44394204d2f3e70c220b51764` (2018-10-30, known historic data, not uncontaminated test data). Source and dependency licenses of related components must be reviewed separately before redistribution.

The project's previous qualification work uses two local compatibility modifications in each checked-out test suite (`tests/test_parsers.py` and `tests/test_readers.py`, 5 insertions and 5 deletions). We did not undo these patches or claim unmodified upstream tests. We copied both working trees to a new isolated evidence directory before testing. No hidden test or new model was used.

## Offline results, freshly run on GB10

Existing Python 3.11 environment; `PYTHONDONTWRITEBYTECODE=1`, `pytest -q -p no:cacheprovider --disable-warnings tests` run inside each copied working tree:

| Upstream role | Tests | Warning count | Time reported by pytest |
|---|---:|---:|---:|
| parent | 42 passed | 626 | 3.31s |
| child | 42 passed | 626 | 3.05s |

The warnings are reported counts; their individual nature was not audited. The test pass is conditional on the previous compatibility patches and the existing environment. It supports only that this test suite passes both snapshots, not that both meet the new dependency objective.

Read-only [`qualify_partridge_static.py`](qualify_partridge_static.py) inspects AST import, manifest literals, and package version on the copied snapshots. The detector target `cchardet` was chosen from the already-known public child commit; it is not blind, independently discovered, or a general verifier:

| Snapshot | `__version__` source literal | Direct detector import | Manifest literal | Target check |
|---|---|---|---|
| parent | `0.11.0` | `chardet` | `chardet` | false |
| child | `0.11.0` | `cchardet` | `cchardet` | true |

An invalidation rule based **only** on the package's `__version__` value cannot distinguish this pair; they are commits with an unchanged version field, not evidence that two tagged production releases have the same version. The direct known-target AST check distinguishes the two files, but it is weaker than the previously validated alias-aware baseline and can fail on aliases, helpers or semantically equivalent changes. Commit hashes, actual import/manifest checks and source-diff rules are stronger obvious alternatives that were not beaten here. Prior six-object `6/6` results remain historical: this fresh run did not independently replay all six objects or evaluate retry policies.

The original source trees contain no `SKILL.md` file discovered by the read-only search. A historical dated skill that a real agent used before this update was not located, and no ordinary-retry, fixed-skill or model-based candidate was run. Consequently there is no defensible paired skill-effect or method comparison in this qualification; adding a new invented old skill would be a synthetic development probe. We have not shown a residual after strong rules. The candidate requires an independently sourced task family plus time-stamped applicable skill/contract and held-out evaluation; this old and exposed pair is an infrastructure fixture only.

## Reproduction and accounting

- GB10 evidence directory: `/home/testuser/wzh/research_evidence/agent_frontier_20261029/partridge_qualification_DwLIQkRZ/`; contains the copied checkouts, unchanged previous test compatibility patches, two raw pytest logs, static script variants and JSON outputs. No production services were touched.
- Stored result: [partridge_static_qualification_v2.json](partridge_static_qualification_v2.json). Source and manifest hashes appear in the JSON; `qualify_partridge_static.py <evidence_directory>` replays the static checks.
- Existing environment executable: `/home/testuser/wzh/protected_research_20261021_v1/external_sources/g2_real_migrations_v2/env_gold311/bin/python`.
- Model, judge, training and external paid API calls: **0**. CPU pytest wall times as above, and two small local AST runs. Files are development evidence, not a new benchmark or claim of publication readiness.
